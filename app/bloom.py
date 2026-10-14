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
    """Compute a seeded 32-bit FNV-1a hash over the UTF-8 bytes of a value.

    XORs the seed into the FNV offset basis first so the two filter
    hashes (SEED_A / SEED_B) are independent streams from one function.
    This is the raw hash primitive behind the double-hashing scheme:
    index_i = (h1 + i*h2) mod m. Must stay byte-identical to the
    JavaScript twin in ``autosuggest.js`` or client hints diverge.

    Args:
        value: Normalized string to hash (already lowercased/stripped).
        seed: Integer seed XORed into the offset basis.

    Returns:
        Unsigned 32-bit integer hash digest.
    """
    h = (FNV_OFFSET ^ seed) & 0xFFFFFFFF
    for byte in value.encode('utf-8'):
        h ^= byte
        h = (h * FNV_PRIME) & 0xFFFFFFFF
    return h


def normalize(value):
    """Normalize a raw input value exactly the way the client does.

    Strips surrounding whitespace and lowercases, so ``"  Intro "`` and
    ``"intro"`` hash to the same indexes on both server and browser.
    Every :meth:`BloomFilter.add` and ``in`` check funnels through here;
    skipping it would cause systematic false negatives between the two
    implementations.

    Args:
        value: Raw user-typed string.

    Returns:
        Stripped, lowercased string ready for hashing.
    """
    return value.strip().lower()


def optimal_params(num_items, fp_rate=FP_RATE):
    """Derive optimal Bloom filter size and hash count for an item count.

    Applies the classic formulas ``m = -n*ln(p)/ln(2)^2`` bits and
    ``k = (m/n)*ln(2)`` hashes, then rounds ``m`` up to a whole byte
    (minimum ``MIN_BITS``) so the bit array always fits ``m // 8`` bytes.
    More items mean a larger array; a stricter false-positive rate means
    more bits per item and more hashes.

    Args:
        num_items: Expected number of distinct items to store.
        fp_rate: Target false-positive probability (default FP_RATE).

    Returns:
        Tuple (m, k) where m is the byte-aligned bit length and k is
        the number of hash functions (indexes per item).
    """
    if num_items <= 0:
        return MIN_BITS, 1
    m = int(math.ceil(-num_items * math.log(fp_rate) / (math.log(2) ** 2)))
    m = max(MIN_BITS, (m + 7) & ~7)
    k = max(1, int(round((m / num_items) * math.log(2))))
    return m, k


class BloomFilter:
    def __init__(self, num_items, fp_rate=FP_RATE):
        """Size a fresh empty filter for the expected item count.

        Calls :func:`optimal_params` to pick the bit length and hash
        count, then allocates a zeroed bytearray of ``m // 8`` bytes.
        A larger ``num_items`` estimate lowers the eventual false-positive
        rate at the cost of a bigger payload shipped to the browser.

        Args:
            num_items: Expected distinct items the filter will hold.
            fp_rate: Target false-positive probability.
        """
        self.m, self.k = optimal_params(num_items, fp_rate)
        self._bytes = bytearray(self.m // 8)

    @classmethod
    def from_payload(cls, m, k, bits):
        """Rebuild a filter from its serialized payload without rehashing.

        Decodes the base64 bit string back into a bytearray and attaches
        the stored ``m``/``k`` parameters, so the browser-sent or cached
        payload behaves identically to the original. Used when
        rehydrating filters shipped via :meth:`to_payload`.

        Args:
            m: Bit array length of the original filter.
            k: Hash count of the original filter.
            bits: Base64-encoded bit array string.

        Returns:
            A BloomFilter instance with the decoded bit array.
        """
        obj = cls.__new__(cls)
        obj.m = m
        obj.k = k
        obj._bytes = bytearray(base64.b64decode(bits))
        return obj

    def _indexes(self, value):
        """Compute the k bit indexes for a value via double hashing.

        Normalizes the value, hashes it twice with the two FNV seeds
        (h1, h2), then emits ``(h1 + i*h2) % m`` for ``i`` in ``0..k-1``.
        The ``h2 == 0`` guard avoids collapsing all k probes onto one
        bit. Both :meth:`add` and :meth:`__contains__` use exactly this
        sequence, mirroring the client implementation.

        Args:
            value: Raw input string to locate in the bit array.

        Returns:
            Tuple of k integer indexes in ``range(m)``.
        """
        text = normalize(value)
        h1 = _fnv1a_32(text, SEED_A)
        h2 = _fnv1a_32(text, SEED_B)
        if h2 == 0:
            h2 = 1
        return tuple((h1 + i * h2) % self.m for i in range(self.k))

    def add(self, value):
        """Insert a value by setting its k bits in the array.

        Hashes the normalized value to k indexes and sets each bit
        (big-endian bit order within each byte, matching the client).
        Adding twice is idempotent. The filter never stores the value
        itself, only these bits, which is what makes it compact and
        probabilistic.

        Args:
            value: Raw input string to insert.
        """
        for idx in self._indexes(value):
            self._bytes[idx >> 3] |= 1 << (7 - (idx & 7))

    def __contains__(self, value):
        """Test probable membership: False means definitely absent.

        Checks all k bits for the normalized value. A single unset bit
        proves absence (no false negatives); all-set means present or a
        hash collision (false positive possible). Callers must confirm
        positive hints against the database before acting on them.

        Args:
            value: Raw input string to test.

        Returns:
            True when the value is possibly present, False when it is
            definitely not present.
        """
        for idx in self._indexes(value):
            if not (self._bytes[idx >> 3] & (1 << (7 - (idx & 7)))):
                return False
        return True

    def to_payload(self):
        """Serialize the filter for shipment to the browser as JSON.

        Base64-encodes the raw bit array (bytes are not JSON-safe) and
        bundles it with ``m`` and ``k`` so the client can evaluate the
        identical double-hashing scheme offline. Reversible with
        :meth:`from_payload`.

        Returns:
            Dict with ``m`` (bit length), ``k`` (hash count), and
            ``bits`` (base64 bit array string).
        """
        return {
            'm': self.m,
            'k': self.k,
            'bits': base64.b64encode(bytes(self._bytes)).decode('ascii'),
        }
