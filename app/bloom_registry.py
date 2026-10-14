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
    """Build the composite book dedup key shared with the client.

    Lowercases and strips each component and joins them with the
    unit-separator character, exactly mirroring ``autosuggest.js`` and
    the server dedup rule in ``get_book_by_title_author_isbn`` (blank
    ISBN matches books with no ISBN). Any change here must be mirrored
    client-side or hints silently stop matching.

    Args:
        title: Book title string.
        author: Book author string.
        isbn: ISBN string, or '' when unknown.

    Returns:
        Composite ``title SEP author SEP isbn`` key string.
    """
    return f'{title.strip().lower()}{SEP}{author.strip().lower()}{SEP}{(isbn or "").strip().lower()}'


def category_key(name):
    """Normalize a category name into its filter key, matching the client.

    Strips surrounding whitespace and lowercases so ``" Fiction "``
    and ``"fiction"`` share one bit pattern on both server and browser.
    Used when building and querying the ``category_record`` filter for
    the analytics category known-value check.

    Args:
        name: Raw subject_classification string, possibly None.

    Returns:
        Normalized lowercase key string ('' when input was None).
    """
    return (name or '').strip().lower()


class BloomRegistry:
    def __init__(self):
        """Create an empty lazy registry that builds filters on demand.

        Initializes the thread lock, the filter and payload caches, and
        the dirty flag (True so the first :meth:`get_payloads` call
        builds from the database). No database access happens here; the
        build is deferred until the payloads are actually needed.

        Args:
            None: Takes no arguments.
        """
        self._lock = threading.Lock()
        self._filters = {}
        self._payloads = {}
        self._dirty = True

    def mark_dirty(self):
        """Flag cached filters stale so the next read rebuilds them.

        Called after any write that changes the underlying sets (new
        book cataloged, borrower id_number added, category created).
        Only flips a boolean under no extra I/O; the expensive rebuild
        happens lazily inside :meth:`get_payloads`.

        Args:
            None: Takes no arguments.
        """
        self._dirty = True

    def _build(self):
        """Query the database and build all three Bloom filters fresh.

        Pulls distinct book triples, borrower id_numbers, and subject
        classifications (skipping NULL/blank rows), sizes one
        :class:`BloomFilter` per set, and inserts every normalized key.
        An empty table still yields a minimal one-item filter so later
        ``add``/``in`` calls never divide by zero. Runs outside the
        caller lock; the caller swaps the result in atomically.

        Returns:
            Dict mapping ``book_record``/``student_record``/
            ``category_record`` to their built BloomFilter instances.
        """
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
        """Return JSON-serializable payloads for every filter, rebuilding if stale.

        Takes the registry lock, rebuilds via :meth:`_build` when the
        dirty flag is set or no payloads exist yet, serializes each
        filter with ``to_payload``, clears the dirty flag, and returns a
        copy so callers cannot mutate the cache. Thread-safe: concurrent
        readers block on the lock while one rebuild runs.

        Returns:
            Dict mapping filter name to its ``{'m', 'k', 'bits'}``
            payload dict.
        """
        with self._lock:
            if self._dirty or not self._payloads:
                self._filters = self._build()
                self._payloads = {
                    name: bf.to_payload() for name, bf in self._filters.items()
                }
                self._dirty = False
            return dict(self._payloads)


bloom_registry = BloomRegistry()
