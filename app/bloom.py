"""Bloom filter used for real-time existence hints on text input fields.

A Bloom filter is probabilistic: ``value in bf`` returning True means the
value is *likely* present (there can be false positives); returning False
means the value is definitely absent (no false negatives). It is only a
pre-filter — routes still validate and dedup against the database before
completing any search or insert.

The hashing scheme (FNV-1a with two seeds + double hashing) is mirrored
exactly in ``app/static/js/autosuggest.js`` so the client can evaluate the
same filter offline.
"""

import base64
import math

SEED_A = 0x9747B28C
SEED_B = 0x5BF03635
FNV_OFFSET = 0x811C9DC5
FNV_PRIME = 0x01000193

FP_RATE = 0.01
MIN_BITS = 64


def _fnv1a_32(value, seed):
    """32-bit FNV-1a hash over UTF-8 bytes, seeded via the offset basis."""
    h = (FNV_OFFSET ^ seed) & 0xFFFFFFFF
    for byte in value.encode('utf-8'):
        h ^= byte
        h = (h * FNV_PRIME) & 0xFFFFFFFF
    return h


def normalize(value):
    """Normalize an input value the same way the client does."""
    return value.strip().lower()


def optimal_params(num_items, fp_rate=FP_RATE):
    """Return ``(m, k)`` — bit array length (byte-aligned) and hash count."""
    if num_items <= 0:
        return MIN_BITS, 1
    m = int(math.ceil(-num_items * math.log(fp_rate) / (math.log(2) ** 2)))
    m = max(MIN_BITS, (m + 7) & ~7)
    k = max(1, int(round((m / num_items) * math.log(2))))
    return m, k


class BloomFilter:
    def __init__(self, num_items, fp_rate=FP_RATE):
        self.m, self.k = optimal_params(num_items, fp_rate)
        self._bytes = bytearray(self.m // 8)

    @classmethod
    def from_payload(cls, m, k, bits):
        obj = cls.__new__(cls)
        obj.m = m
        obj.k = k
        obj._bytes = bytearray(base64.b64decode(bits))
        return obj

    def _indexes(self, value):
        text = normalize(value)
        h1 = _fnv1a_32(text, SEED_A)
        h2 = _fnv1a_32(text, SEED_B)
        if h2 == 0:
            h2 = 1
        return tuple((h1 + i * h2) % self.m for i in range(self.k))

    def add(self, value):
        for idx in self._indexes(value):
            self._bytes[idx >> 3] |= 1 << (7 - (idx & 7))

    def __contains__(self, value):
        for idx in self._indexes(value):
            if not (self._bytes[idx >> 3] & (1 << (7 - (idx & 7)))):
                return False
        return True

    def to_payload(self):
        return {
            'm': self.m,
            'k': self.k,
            'bits': base64.b64encode(bytes(self._bytes)).decode('ascii'),
        }
