"""In-memory Bloom filters used as a pre-filter for duplicate-record checks.

The filters hold composite "record keys":
- ``book_record``: ``title SEP author SEP isbn`` for every book, mirroring the
  dedup rule in :func:`app.cataloging.models.get_book_by_title_author_isbn`
  (blank ISBN matches books with no ISBN).
- ``student_record``: each borrower ``id_number``.
- ``category_record``: each distinct ``subject_classification`` (powers the
  analytics category filter's known-value check).

They are built lazily from the database and rebuilt the next time a relevant
write calls :func:`BloomRegistry.mark_dirty`. A ``False`` result from a filter
means the record is definitely new, so the client skips the confirming DB
query; a ``True`` result only means "maybe exists" and is confirmed against
the database before any message is shown.
"""

import threading

from app.database import db
from app.bloom import BloomFilter

SEP = '\x1f'


def record_key(title, author, isbn=''):
    """Composite key for a book record; must match the client (autosuggest.js)."""
    return f'{title.strip().lower()}{SEP}{author.strip().lower()}{SEP}{(isbn or "").strip().lower()}'


def category_key(name):
    """Normalized key for a collection category; must match the client."""
    return (name or '').strip().lower()


class BloomRegistry:
    def __init__(self):
        self._lock = threading.Lock()
        self._filters = {}
        self._payloads = {}
        self._dirty = True

    def mark_dirty(self):
        self._dirty = True

    def _build(self):
        filters = {}

        book_rows = db.fetch_all(
            "SELECT DISTINCT title, author, COALESCE(isbn, '') FROM book_catalog "
            "WHERE title IS NOT NULL AND title != '' "
            "AND author IS NOT NULL AND author != ''"
        )
        book_bf = BloomFilter(len(book_rows) or 1)
        for title, author, isbn in book_rows:
            book_bf.add(record_key(title, author, isbn))
        filters['book_record'] = book_bf

        id_rows = db.fetch_all(
            "SELECT DISTINCT id_number FROM borrowers "
            "WHERE id_number IS NOT NULL AND id_number != ''"
        )
        student_bf = BloomFilter(len(id_rows) or 1)
        for (id_number,) in id_rows:
            student_bf.add(id_number.strip().lower())
        filters['student_record'] = student_bf

        cat_rows = db.fetch_all(
            "SELECT DISTINCT subject_classification FROM book_catalog "
            "WHERE subject_classification IS NOT NULL AND subject_classification != ''"
        )
        cat_bf = BloomFilter(len(cat_rows) or 1)
        for (name,) in cat_rows:
            cat_bf.add(category_key(name))
        filters['category_record'] = cat_bf

        return filters

    def get_payloads(self):
        with self._lock:
            if self._dirty or not self._payloads:
                self._filters = self._build()
                self._payloads = {
                    name: bf.to_payload() for name, bf in self._filters.items()
                }
                self._dirty = False
            return dict(self._payloads)


bloom_registry = BloomRegistry()
