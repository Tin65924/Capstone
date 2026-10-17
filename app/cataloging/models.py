from app.database import db


def normalize_isbn(value):
    """Canonical ISBN form: hyphens/spaces stripped, uppercased.

    Stored values and dedup lookups both go through this so
    '978-0-306-40615-7' and '9780306406157' are the same book.
    """
    return (value or '').strip().replace('-', '').replace(' ', '').upper()


def is_valid_isbn10(code):
    """ISBN-10 checksum: 9 digits + digit/X, weighted mod-11."""
    if len(code) != 10 or not code[:9].isdigit():
        return False
    if not (code[9].isdigit() or code[9] == 'X'):
        return False
    total = sum(((10 if ch == 'X' else int(ch)) * (10 - i))
                for i, ch in enumerate(code))
    return total % 11 == 0


def is_valid_isbn13(code):
    """ISBN-13 checksum: 13 digits, alternating 1/3 weights mod-10."""
    if len(code) != 13 or not code.isdigit():
        return False
    total = sum(int(ch) * (1 if i % 2 == 0 else 3)
                for i, ch in enumerate(code))
    return total % 10 == 0


def clean_ebook_url(value):
    """Trimmed e-book link, or None when blank."""
    value = (value or '').strip()
    return value or None


def validate_ebook_url(value, material_type):
    """Validate an e-book link, returning (cleaned, error).

    Blank is allowed except for E-Book titles, which need their access
    link. Non-blank values must be embeddable Google links — a Drive
    file (/file/d/<id>, open?id=, uc?id=) or a Google Docs document
    (/document/d/<id>) — within the column width. Everything else,
    publisher URLs included, is rejected as invalid. Used by the book
    form and bulk import alike.
    """
    cleaned = clean_ebook_url(value)
    if not cleaned:
        if (material_type or '').strip() == 'E-Book':
            return None, 'E-Book link is required for E-Book.'
        return None, None
    if len(cleaned) > 500:
        return None, 'E-Book link is too long (max 500 characters).'
    try:
        from urllib.parse import urlparse
        parsed = urlparse(cleaned)
    except Exception:
        return None, 'E-Book link must be a valid http(s) URL.'
    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
        return None, 'E-Book link must be a valid http(s) URL.'
    kind, _ = ebook_link_info(cleaned)
    if kind not in ('drive', 'docs'):
        return None, 'E-Book link must be a Google Drive or Google Docs link.'
    return cleaned, None


def ebook_link_info(url):
    """Classify an e-book link for access buttons.

    Returns (kind, doc_id): kind 'drive' with the Drive file id when
    the URL points at a previewable Drive file (/file/d/<id>, open?id=,
    uc?id=); kind 'docs' with the document id for Google Docs
    /document/d/<id> links; kind 'external' for anything else
    (including Drive folders and Docs URLs without a document id,
    which cannot embed a preview); (None, None) when blank. Validation
    rejects the 'external' kind — only Drive and Docs links are
    accepted.
    """
    url = (url or '').strip()
    if not url:
        return None, None
    try:
        from urllib.parse import urlparse, parse_qs
        import re
        parsed = urlparse(url)
        host = (parsed.hostname or '').lower()
        if 'drive.google.com' in host:
            match = re.search(r'/file/d/([-\w]+)', parsed.path)
            if match:
                return 'drive', match.group(1)
            query_id = parse_qs(parsed.query).get('id', [None])[0]
            if query_id and '/folders/' not in parsed.path:
                return 'drive', query_id
            return 'external', None
        if 'docs.google.com' in host:
            match = re.search(r'/document/d/([-\w]+)', url)
            if match:
                return 'docs', match.group(1)
            return 'external', None
        return 'external', None
    except Exception:
        return 'external', None


def drive_preview_url(file_id):
    """Embeddable preview URL for a Drive file id."""
    return 'https://drive.google.com/file/d/%s/preview' % file_id


def docs_preview_url(url):
    """Embeddable /preview URL for a Google Docs document link.

    Accepts any variant of a /document/d/<id> URL (edit, view,
    export, mobilebasic, or an explicit /preview) and returns the
    /preview form, so staff never need to hand-craft the embed URL.
    Empty string when the URL is not a recognized document link.
    """
    import re
    match = re.search(r'/document/d/([-\w]+)', url or '')
    if not match:
        return ''
    return 'https://docs.google.com/document/d/%s/preview' % match.group(1)


def _isbn_search_text(value):
    """Strip hyphens/spaces from a search term for the ISBN column.

    Stored ISBNs are normalized (no hyphens), so the isbn arm of a
    search must compare de-hyphenated too. Unlike normalize_isbn this
    preserves case — ILIKE is already case-insensitive, and keeping
    the original case avoids noise in the other search arms.
    """
    return (value or '').replace('-', '').replace(' ', '')


def _is_missing_relation(exc):
    """True for missing-table/column errors (unmigrated database).

    Lets read paths degrade instead of 500ing when a deploy serving
    new code hits a database whose startup migration has not applied
    yet (e.g. Render serving traffic mid-restart). Only Postgres
    undefined-table/column codes qualify — every other DB error still
    propagates.
    """
    if getattr(exc, 'pgcode', '') in ('42P01', '42703'):
        return True
    try:
        from psycopg2 import errors as _pg_errors
        return isinstance(exc, (_pg_errors.UndefinedTable,
                                _pg_errors.UndefinedColumn))
    except Exception:
        return False


def _warn_schema_mismatch(what):
    try:
        from flask import current_app
        current_app.logger.warning(
            'cataloging: %s missing from database (migration not applied); '
            'degrading gracefully', what)
    except Exception:
        pass


# book_catalog columns introduced by later migrations (categories FK,
# e-book link, audit stamps). Write paths include them when the database
# has them and drop any the database reports missing, so a deploy serving
# new code against a not-yet-migrated database degrades instead of
# 500ing on the INSERT/UPDATE (the write-path twin of the read gate
# below, which keeps those same columns out of SELECTs).
_OPTIONAL_BOOK_COLUMNS = ('category_id', 'ebook_url', 'updated_at', 'updated_by')


def _missing_column_name(exc):
    """Column named by an UndefinedColumn error, or None.

    Postgres phrases it ``column "ebook_url" of relation ...``; pulling
    the name out lets a write retry without exactly the column the
    schema lacks instead of dropping every optional column at once.
    """
    import re
    match = re.search(r'column "([^"]+)"', str(exc))
    return match.group(1) if match else None


def _execute_book_write(build, optional_columns=_OPTIONAL_BOOK_COLUMNS):
    """Run a book_catalog write, retrying without any missing optional column.

    ``build(available)`` returns ``(sql, params)`` built for the current
    set of usable optional columns. When the statement raises an
    UndefinedColumn naming one of them, that column is dropped and
    ``build`` is retried; an unmigrated database therefore loses only the
    columns it lacks instead of failing the request. ``db.execute`` rolls
    the failed statement back, so retrying is safe. Any other error
    propagates unchanged.

    Args:
        build: Callable taking the set of currently usable optional
            column names and returning ``(sql, params)``.
        optional_columns: Names safe to drop when the database lacks them.

    Returns:
        Whatever ``db.execute`` returns for the successful statement.
    """
    available = set(optional_columns)
    while True:
        sql, params = build(available)
        try:
            return db.execute(sql, params)
        except Exception as e:
            if not _is_missing_relation(e):
                raise
            missing = _missing_column_name(e)
            if missing in available:
                _warn_schema_mismatch('book_catalog.%s' % missing)
                available.discard(missing)
                continue
            raise


# Explicit book_catalog projection in the positional contract order every
# caller indexes by (book[6] subject, book[9] material, book[11] status,
# book[15] category_id, book[16] ebook_url). Selecting columns by name
# instead of SELECT * keeps those indices correct on every database:
# ALTER TABLE migrations append new columns in deployment-dependent order,
# so ebook_url is not reliably the 17th physical column.
BOOK_COLUMNS = (
    'book_id, title, author, edition, publisher, year_published, '
    'subject_classification, call_number, isbn, material_type, description, '
    'catalog_status, date_added, updated_at, updated_by, category_id, ebook_url'
)


def _book_select(fetch, build):
    """Run a book_catalog read with the explicit canonical column list.

    ``build(cols)`` returns ``(sql, params)`` using ``cols`` as the
    projection. If that statement hits a missing column/table (a database
    that has not run the migration adding category_id/ebook_url/audit
    columns), the same query is retried with ``SELECT *`` so reads still
    degrade instead of 500ing.

    Args:
        fetch: ``db.fetch_one`` or ``db.fetch_all``.
        build: Callable taking the projection string and returning
            ``(sql, params)``.

    Returns:
        Whatever ``fetch`` returns.
    """
    try:
        return fetch(*build(BOOK_COLUMNS))
    except Exception as e:
        if not _is_missing_relation(e):
            raise
        _warn_schema_mismatch('book_catalog columns')
        return fetch(*build('*'))


# Multi-category schema gate: book_categories/categories may not exist
# when a deploy serving new code hits a not-yet-migrated database
# (startup migration still pending or failed). Probing every call would
# waste a round trip, so the outcome is cached briefly — migrant
# databases converge within the TTL without a restart.
_MULTI_CAT_TTL = 60
_multi_cat_state = {'ok': None, 'at': 0.0}


def multi_cat_available():
    """True when the multi-category tables exist (cached 60s).

    A cheap SELECT 1 against book_categories; a missing table/column
    error means unmigrated (False). Any other outcome — rows, empty,
    or a non-schema error — fails open to True so real problems still
    surface from the actual query instead of being masked here.
    """
    import time
    now = time.monotonic()
    state = _multi_cat_state
    if state['ok'] is not None and now - state['at'] < _MULTI_CAT_TTL:
        return state['ok']
    try:
        db.fetch_one('SELECT 1 FROM book_categories LIMIT 1')
        ok = True
    except Exception as e:
        ok = not _is_missing_relation(e)
    state['ok'] = ok
    state['at'] = now
    return ok


def create_book(title, author, edition, publisher, year_published, subject_classification,
                call_number, isbn, material_type, description, category_id=None,
                ebook_url=None):
    """Insert a new book title into the catalog as active and return its id.

    Creates one row in book_catalog with catalog_status='active' holding
    the bibliographic metadata. Physical copies are added separately via
    create_accession; a title with no accessions simply shows zero
    available copies.

    Args:
        title: Book title (required).
        author: Author name(s) (required).
        edition: Edition string, or None.
        publisher: Publisher name, or None.
        year_published: Publication year integer, or None.
        subject_classification: Category/subject label for filtering.
        call_number: Shelf call number, or None.
        isbn: ISBN string, or None (duplicates allowed across editions).
        material_type: e.g. 'Book' or 'E-Book'.
        description: Summary/blurb, or None.
        category_id: FK into categories, or None to auto-resolve from
            subject_classification (case-insensitive match or create).
        ebook_url: E-book access link (Drive/publisher), or None.

    Returns:
        New book_id integer, or None if the INSERT returned nothing.
    """
    if category_id is None:
        category_id, _ = resolve_category(subject_classification)
    isbn = normalize_isbn(isbn) or None
    ebook_url = clean_ebook_url(ebook_url)

    def build(available):
        columns = [
            ('title', title), ('author', author), ('edition', edition),
            ('publisher', publisher), ('year_published', year_published),
            ('subject_classification', subject_classification),
            ('call_number', call_number), ('isbn', isbn),
            ('material_type', material_type), ('description', description),
            ('catalog_status', 'active'),
        ]
        if 'category_id' in available:
            columns.append(('category_id', category_id))
        if 'ebook_url' in available:
            columns.append(('ebook_url', ebook_url))
        names = ', '.join(name for name, _ in columns)
        placeholders = ', '.join(['%s'] * len(columns))
        return ('INSERT INTO book_catalog (' + names + ') VALUES ('
                + placeholders + ') RETURNING book_id',
                tuple(value for _, value in columns))

    rows = _execute_book_write(build)
    return rows[0][0] if rows else None


DISTINCT_ORDER = 'title, author, COALESCE(isbn, \'\')'

# Trailing column appended by the cataloging-page list queries; a book can
# have multiple accessions, so they are comma-joined.
ACCESSION_SUBQUERY = (
    "(SELECT COALESCE(string_agg(accession_number, ', ' ORDER BY accession_id), '') "
    "FROM accession_log WHERE accession_log.book_id = book_catalog.book_id)"
)

# Comma-joined secondary category names for export rows. Appended BEFORE
# accession_numbers so the joined accessions stay last (callers use [-1]).
EXTRA_CATEGORIES_SUBQUERY = (
    "(SELECT COALESCE(string_agg(c.name, ', ' ORDER BY c.name), '') "
    "FROM book_categories bc JOIN categories c ON c.category_id = bc.category_id "
    "WHERE bc.book_id = book_catalog.book_id)"
)

def search_books(query, field=None):
    """Search the catalog with an ILIKE match, de-duplicated by title.

    Returns DISTINCT ON (title, author, isbn) rows so duplicate edition
    rows collapse to one hit. When field is one of title/author/isbn/
    category only that column is matched; otherwise title, author, isbn,
    and subject_classification are all searched. Only the sanitized
    field name selects the column — the user query always travels as a
    bound %pattern% parameter.

    Args:
        query: Substring to wrap in %...% for ILIKE matching.
        field: Optional column scope ('title', 'author', 'isbn',
            'category'), or None for all columns.

    Returns:
        List of book_catalog row tuples matching the query.
    """
    pattern = f'%{query}%'
    # Stored ISBNs are normalized (no hyphens); strip them from the
    # query so hyphenated searches still match.
    isbn_pattern = f'%{_isbn_search_text(query)}%'
    if field == 'title':
        return _book_select(db.fetch_all, lambda cols: (
            f'SELECT DISTINCT ON ({DISTINCT_ORDER}) {cols} FROM book_catalog '
            f'WHERE title ILIKE %s ORDER BY {DISTINCT_ORDER}', (pattern,)))
    elif field == 'author':
        return _book_select(db.fetch_all, lambda cols: (
            f'SELECT DISTINCT ON ({DISTINCT_ORDER}) {cols} FROM book_catalog '
            f'WHERE author ILIKE %s ORDER BY {DISTINCT_ORDER}', (pattern,)))
    elif field == 'isbn':
        return _book_select(db.fetch_all, lambda cols: (
            f'SELECT DISTINCT ON ({DISTINCT_ORDER}) {cols} FROM book_catalog '
            f'WHERE isbn ILIKE %s ORDER BY {DISTINCT_ORDER}', (isbn_pattern,)))
    elif field == 'category':
        return _book_select(db.fetch_all, lambda cols: (
            f'SELECT DISTINCT ON ({DISTINCT_ORDER}) {cols} FROM book_catalog '
            f'WHERE subject_classification ILIKE %s ORDER BY {DISTINCT_ORDER}',
            (pattern,)))
    return _book_select(db.fetch_all, lambda cols: (
        f'SELECT DISTINCT ON ({DISTINCT_ORDER}) {cols} FROM book_catalog '
        f'WHERE title ILIKE %s OR author ILIKE %s OR isbn ILIKE %s '
        f'OR subject_classification ILIKE %s ORDER BY {DISTINCT_ORDER}',
        (pattern, pattern, isbn_pattern, pattern)))


def get_book_by_id(book_id):
    """Fetch one catalog row by primary key regardless of status.

    Used by edit, archive-check, detail, and history views that must see
    archived books too (public search filters those out separately).

    Args:
        book_id: Primary key of book_catalog.

    Returns:
        Full book_catalog row tuple, or None if not found.
    """
    return _book_select(db.fetch_one, lambda cols: (
        f'SELECT {cols} FROM book_catalog WHERE book_id = %s', (book_id,)))


def get_book_by_title_author_isbn(title, author, isbn):
    """Find a duplicate title by exact title/author/ISBN match.

    Guards the add-book flow against double entry: when isbn is given
    it must match exactly, otherwise the match requires isbn IS NULL so
    an ISBN-less row never collides with an ISBN-bearing one. The ISBN
    is normalized first so hyphenated and bare forms match the same row.

    Args:
        title: Exact title to match.
        author: Exact author to match.
        isbn: Exact ISBN to match, or falsy to match NULL-ISBN rows.

    Returns:
        1-tuple (book_id,) of the duplicate, or None if unique.
    """
    isbn = normalize_isbn(isbn) or None
    if isbn:
        return db.fetch_one(
            'SELECT book_id FROM book_catalog WHERE title = %s AND author = %s AND isbn = %s',
            (title, author, isbn)
        )
    return db.fetch_one(
        'SELECT book_id FROM book_catalog WHERE title = %s AND author = %s AND isbn IS NULL',
        (title, author)
    )


def suggest_book_values(field, prefix, limit=8):
    """Suggest distinct column values by prefix for form autocomplete.

    Powers the add/edit-book autosuggest inputs: depending on field,
    returns distinct titles, authors, publishers, subjects, ISBNs, or
    (for 'search') the union of title/author/subject/isbn matches.
    Matching is ILIKE prefix%, ordered alphabetically.

    Args:
        field: One of 'title', 'author', 'publisher', 'subject',
            'isbn', or 'search' for the combined catalog box.
        prefix: Typed prefix to match.
        limit: Maximum suggestions to return.

    Returns:
        List of 1-tuples (value,) with distinct matches.
    """
    pattern = f'{prefix}%'
    isbn_pattern = f'{_isbn_search_text(prefix)}%'
    if field == 'title':
        return db.fetch_all(
            'SELECT DISTINCT title FROM book_catalog WHERE title ILIKE %s ORDER BY title LIMIT %s',
            (pattern, limit)
        )
    if field == 'author':
        return db.fetch_all(
            'SELECT DISTINCT author FROM book_catalog WHERE author ILIKE %s ORDER BY author LIMIT %s',
            (pattern, limit)
        )
    if field == 'publisher':
        return db.fetch_all(
            "SELECT DISTINCT publisher FROM book_catalog WHERE publisher IS NOT NULL AND publisher != '' "
            "AND publisher ILIKE %s ORDER BY publisher LIMIT %s",
            (pattern, limit)
        )
    if field == 'subject':
        return db.fetch_all(
            "SELECT DISTINCT subject_classification FROM book_catalog WHERE subject_classification IS NOT NULL "
            "AND subject_classification != '' AND subject_classification ILIKE %s "
            "ORDER BY subject_classification LIMIT %s",
            (pattern, limit)
        )
    if field == 'isbn':
        return db.fetch_all(
            "SELECT DISTINCT isbn FROM book_catalog WHERE isbn IS NOT NULL AND isbn != '' "
            "AND isbn ILIKE %s ORDER BY isbn LIMIT %s",
            (isbn_pattern, limit)
        )
    # 'search' — the catalog search box matches any of these columns
    return db.fetch_all(
        "SELECT DISTINCT value FROM ("
        "SELECT title AS value FROM book_catalog WHERE title ILIKE %s "
        "UNION SELECT author FROM book_catalog WHERE author ILIKE %s "
        "UNION SELECT subject_classification FROM book_catalog WHERE subject_classification IS NOT NULL "
        "AND subject_classification != '' AND subject_classification ILIKE %s "
        "UNION SELECT isbn FROM book_catalog WHERE isbn IS NOT NULL AND isbn != '' AND isbn ILIKE %s"
        ") s WHERE value IS NOT NULL AND value != '' ORDER BY value LIMIT %s",
        (pattern, pattern, pattern, isbn_pattern, limit)
    )


def suggest_books_rich(prefix, limit=8):
    """Title/author pairs for the analytics-style suggestion dropdown.

    Returns [(title, author)] for active books whose title or author
    matches the prefix — the same two-line row style as the Book
    Analytics picker (bold title, author at right).
    """
    pattern = f'{prefix}%'
    return db.fetch_all(
        'SELECT DISTINCT title, author FROM book_catalog '
        "WHERE catalog_status = 'active' AND (title ILIKE %s OR author ILIKE %s) "
        'ORDER BY title LIMIT %s',
        (pattern, pattern, limit)
    )


def get_all_books():
    """Active books only — archived books surface solely via get_books_by_status('archived').

    Full list (with per-book accession numbers) for exports. Page views
    must use get_all_books_paginated() instead so 4.5k+ rows are never
    materialized per request. The extra-categories column is omitted on
    unmigrated databases.
    """
    extra = f', {EXTRA_CATEGORIES_SUBQUERY} AS extra_categories' if multi_cat_available() else ''
    return _book_select(db.fetch_all, lambda cols: (
        f"SELECT DISTINCT ON ({DISTINCT_ORDER}) {cols}{extra}, {ACCESSION_SUBQUERY} AS accession_numbers "
        f"FROM book_catalog WHERE catalog_status = 'active' ORDER BY {DISTINCT_ORDER}",
        ()))


def _count_books(where, args):
    """Count catalog rows for one WHERE fragment for pagination totals.

    Shared helper behind every paginated staff/public listing so the
    total matches exactly the rows the page query can return.

    Args:
        where: WHERE clause string including the WHERE keyword.
        args: Bound parameters for that clause.

    Returns:
        Integer matching-row count (0 when none).
    """
    row = db.fetch_one(f'SELECT COUNT(*) FROM book_catalog {where}', args)
    return row[0] if row else 0


# Staff-page sort options (allowlisted — never built from user input).
# '' is the default title A-Z ordering. Accession sorts use the joined
# accession string (exact for single-copy books); newest is date_added
# with book_id breaking same-day ties.
_CATALOG_SORTS = {
    'title_desc': 'title DESC, author ASC, isbn ASC',
    'accession_asc': 'accession_numbers ASC',
    'accession_desc': 'accession_numbers DESC',
    'newest': 'date_added DESC, book_id DESC',
}


def _catalog_sort_clause(sort_by):
    """ORDER BY fragment for a sort key, or None for the default."""
    return _CATALOG_SORTS.get(sort_by or '')


def _relevance_order(query):
    """(ORDER BY, params) scoring match quality for a public-catalog term.

    Tiers: exact title (0) > title starts-with (1) > title word hit
    (2) > title anywhere (3) > author (4) > isbn (5) > subject (6),
    ties break A-Z by title. NULL columns never match a tier and fall
    through. LIKE wildcards in the term behave as in the search itself
    (unescaped, consistent with _filtered_where). Returns (None, ())
    without a term — relevance means A-Z then.
    """
    term = (query or '').strip()
    if not term:
        return None, ()
    order = (
        'ORDER BY CASE'
        ' WHEN LOWER(title) = LOWER(%s) THEN 0'
        ' WHEN title ILIKE %s THEN 1'
        ' WHEN title ILIKE %s THEN 2'
        ' WHEN title ILIKE %s THEN 3'
        ' WHEN author ILIKE %s THEN 4'
        ' WHEN isbn ILIKE %s THEN 5'
        ' WHEN subject_classification ILIKE %s THEN 6'
        ' ELSE 7 END, title ASC, author ASC'
    )
    params = (term, f'{term}%', f'% {term}%', f'%{term}%',
              f'%{term}%', f'%{term}%', f'%{term}%')
    return order, params


def get_all_books_paginated(page=1, per_page=20, sort_by=None, material_type=None):
    """Paginated active-book listing for the staff page. Same row shape
    as get_all_books; returns (rows, total). An optional material_type
    (exact book type) further narrows the listing."""
    page = max(1, page or 1)
    per_page = max(1, per_page or 20)
    where = "WHERE catalog_status = 'active'"
    args = []
    if material_type:
        where += ' AND material_type = %s'
        args.append(material_type)
    args = tuple(args)
    total = _count_books(where, args)
    order = _catalog_sort_clause(sort_by)
    if order is None:
        rows = _book_select(db.fetch_all, lambda cols: (
            f'SELECT DISTINCT ON ({DISTINCT_ORDER}) {cols}, {ACCESSION_SUBQUERY} AS accession_numbers '
            f'FROM book_catalog {where} ORDER BY {DISTINCT_ORDER} LIMIT %s OFFSET %s',
            args + (per_page, (page - 1) * per_page)))
    else:
        # DISTINCT ON requires the inner ORDER BY to start with the
        # distinct columns, so non-default sorts wrap the deduped page
        # query and re-sort outside (same pattern as the public catalog).
        rows = _book_select(db.fetch_all, lambda cols: (
            f'SELECT * FROM (SELECT DISTINCT ON ({DISTINCT_ORDER}) {cols}, {ACCESSION_SUBQUERY} AS accession_numbers '
            f'FROM book_catalog {where} ORDER BY {DISTINCT_ORDER}) AS sorted_books '
            f'ORDER BY {order} LIMIT %s OFFSET %s',
            args + (per_page, (page - 1) * per_page)))
    return rows, total


def get_books_by_status_paginated(status, page=1, per_page=20, sort_by=None,
                                  material_type=None):
    """Paginated status listing for the staff page. Same row shape as
    get_books_by_status; returns (rows, total). An optional material_type
    (exact book type) further narrows the listing."""
    page = max(1, page or 1)
    per_page = max(1, per_page or 20)
    where = 'WHERE catalog_status = %s'
    args = [status]
    if material_type:
        where += ' AND material_type = %s'
        args.append(material_type)
    args = tuple(args)
    total = _count_books(where, args)
    order = _catalog_sort_clause(sort_by) or 'title'
    rows = _book_select(db.fetch_all, lambda cols: (
        f'SELECT {cols}, {ACCESSION_SUBQUERY} AS accession_numbers FROM book_catalog '
        f'{where} ORDER BY {order} LIMIT %s OFFSET %s',
        args + (per_page, (page - 1) * per_page)))
    return rows, total


COPY_STATUS_FILTERS = ('overdue', 'lost', 'damaged', 'lost_damaged')


def _copy_status_condition(copy_status):
    """EXISTS fragment for a problem-copy listing, or None when unknown.

    'lost_damaged' is kept for older links (e.g. analytics deep-links);
    the tabs use the separate 'lost' and 'damaged' values.
    """
    if copy_status == 'overdue':
        return (
            "EXISTS (SELECT 1 FROM accession_log al "
            "JOIN circulation_records c ON c.accession_id = al.accession_id "
            "WHERE al.book_id = book_catalog.book_id AND c.transaction_status = 'overdue')"
        )
    if copy_status in ('lost', 'lost_damaged'):
        states = "'lost'" if copy_status == 'lost' else "'lost', 'damaged'"
        return (
            "EXISTS (SELECT 1 FROM accession_log al "
            "JOIN inventory_status i ON i.accession_id = al.accession_id "
            f"WHERE al.book_id = book_catalog.book_id AND i.inventory_state IN ({states}))"
        )
    if copy_status == 'damaged':
        return (
            "EXISTS (SELECT 1 FROM accession_log al "
            "JOIN inventory_status i ON i.accession_id = al.accession_id "
            "WHERE al.book_id = book_catalog.book_id AND i.inventory_state = 'damaged')"
        )
    return None


def get_books_by_copy_status(copy_status):
    """Books with at least one copy in a problem state (analytics deep-links).

    Same row shape as get_all_books (book_catalog.* + accession_numbers).
    Archived books are excluded — they only appear under ?status=archived.
    Full list; page views must use get_books_by_copy_status_paginated().
    """
    condition = _copy_status_condition(copy_status)
    if condition is None:
        return []
    return db.fetch_all(
        f'SELECT DISTINCT ON ({DISTINCT_ORDER}) *, {ACCESSION_SUBQUERY} AS accession_numbers '
        f"FROM book_catalog WHERE book_catalog.catalog_status = 'active' AND ({condition}) ORDER BY {DISTINCT_ORDER}")


def get_books_by_copy_status_paginated(copy_status, page=1, per_page=20, sort_by=None,
                                       material_type=None):
    """Paginated problem-copy listing for the staff page. Same row shape
    as get_books_by_copy_status; returns (rows, total). Unknown filters
    return ([], 0), mirroring get_books_by_copy_status."""
    condition = _copy_status_condition(copy_status)
    if condition is None:
        return [], 0
    page = max(1, page or 1)
    per_page = max(1, per_page or 20)
    where = f"WHERE book_catalog.catalog_status = 'active' AND ({condition})"
    args = []
    if material_type:
        where += ' AND material_type = %s'
        args.append(material_type)
    args = tuple(args)
    total = _count_books(where, args)
    order = _catalog_sort_clause(sort_by)
    if order is None:
        rows = db.fetch_all(
            f'SELECT DISTINCT ON ({DISTINCT_ORDER}) *, {ACCESSION_SUBQUERY} AS accession_numbers '
            f'FROM book_catalog {where} ORDER BY {DISTINCT_ORDER} LIMIT %s OFFSET %s',
            args + (per_page, (page - 1) * per_page)
        )
    else:
        rows = db.fetch_all(
            f'SELECT * FROM (SELECT DISTINCT ON ({DISTINCT_ORDER}) *, {ACCESSION_SUBQUERY} AS accession_numbers '
            f'FROM book_catalog {where} ORDER BY {DISTINCT_ORDER}) AS sorted_books '
            f'ORDER BY {order} LIMIT %s OFFSET %s',
            args + (per_page, (page - 1) * per_page)
        )
    return rows, total


def get_distinct_categories():
    """List every non-empty subject classification A-Z for filter options.

    Unions the primary free-text subjects with secondary vocabulary
    names actually linked to a book, so the sidebar never misses a
    category that only exists as an extra link. Falls back to the
    legacy text-only list when the vocabulary tables are missing
    (unmigrated database).

    Returns:
        List of 1-tuples (category,) ordered alphabetically.
    """
    try:
        return db.fetch_all(
            'SELECT subject_classification FROM book_catalog WHERE subject_classification IS NOT NULL AND subject_classification != \'\' '
            'UNION SELECT c.name FROM categories c WHERE EXISTS '
            '(SELECT 1 FROM book_categories bc WHERE bc.category_id = c.category_id) '
            'ORDER BY 1'
        )
    except Exception as e:
        if not _is_missing_relation(e):
            raise
        _warn_schema_mismatch('categories')
        return db.fetch_all(
            'SELECT DISTINCT subject_classification FROM book_catalog WHERE subject_classification IS NOT NULL AND subject_classification != \'\' ORDER BY subject_classification'
        )


def get_categories():
    """List the controlled category vocabulary A-Z for form dropdowns.

    Returns:
        List of (category_id, name) tuples ordered case-insensitively.
    """
    return db.fetch_all(
        'SELECT category_id, name FROM categories ORDER BY LOWER(name), name'
    ) or []


def resolve_category(name):
    """Resolve a subject label to (category_id, canonical_name).

    Matches case-insensitively against the vocabulary so 'computer
    science' reuses 'Computer Science'; creates the entry when absent
    so cataloging converges on one spelling per category. Blank input
    resolves to (None, None). Tolerates short rows and rowcount ints
    (mock/test shapes) and re-reads after a lost insert race instead
    of failing.

    Args:
        name: Raw subject label from a form or CSV row.

    Returns:
        Tuple (category_id or None, canonical name or None).
    """
    clean = (name or '').strip()
    if not clean:
        return None, None
    try:
        for attempt in ('select', 'insert', 'select'):
            if attempt == 'insert':
                inserted = db.execute(
                    'INSERT INTO categories (name) VALUES (%s) '
                    'ON CONFLICT (name) DO NOTHING RETURNING category_id, name',
                    (clean,)
                )
                if isinstance(inserted, (list, tuple)) and inserted:
                    first = inserted[0]
                    if isinstance(first, (list, tuple)) and len(first) > 0:
                        return first[0], (first[1] if len(first) > 1 else clean)
            else:
                row = db.fetch_one(
                    'SELECT category_id, name FROM categories WHERE LOWER(name) = LOWER(%s)',
                    (clean,)
                )
                if isinstance(row, (list, tuple)) and len(row) > 0:
                    return row[0], (row[1] if len(row) > 1 else clean)
    except Exception as e:
        if not _is_missing_relation(e):
            raise
        # Unmigrated database (no categories table yet): keep the
        # entered spelling and leave the FK unset; the startup backfill
        # links such rows once the migration applies.
        _warn_schema_mismatch('categories')
    return None, clean


def get_book_categories(book_id):
    """List a title's secondary categories as [(category_id, name)] A-Z.

    The primary category stays on book_catalog.category_id; this covers
    only the extra links in book_categories. Returns [] for unknown or
    link-less titles.
    """
    try:
        book_id = int(book_id)
    except (TypeError, ValueError):
        return []
    return db.fetch_all(
        '''SELECT c.category_id, c.name FROM categories c
           JOIN book_categories bc ON bc.category_id = c.category_id
           JOIN book_catalog b ON b.book_id = bc.book_id
           WHERE bc.book_id = %s
             AND bc.category_id IS DISTINCT FROM b.category_id
           ORDER BY LOWER(c.name), c.name''',
        (book_id,)
    ) or []


def get_categories_for_books(book_ids):
    """Batch-fetch secondary categories as {book_id: [(id, name)]}.

    Empty input short-circuits to {} without hitting the DB.
    """
    ids = []
    for bid in book_ids or []:
        try:
            ids.append(int(bid))
        except (TypeError, ValueError):
            continue
    if not ids:
        return {}
    rows = db.fetch_all(
        '''SELECT bc.book_id, c.category_id, c.name FROM categories c
           JOIN book_categories bc ON bc.category_id = c.category_id
           JOIN book_catalog b ON b.book_id = bc.book_id
           WHERE bc.book_id = ANY(%s)
             AND bc.category_id IS DISTINCT FROM b.category_id
           ORDER BY LOWER(c.name), c.name''',
        (ids,)
    ) or []
    out = {}
    for row in rows:
        try:
            out.setdefault(row[0], []).append((row[1], row[2]))
        except (IndexError, TypeError):
            continue
    return out


def set_book_categories(book_id, category_ids):
    """Replace a title's secondary category links.

    Deletes existing links, then inserts one row per id that names a
    real category (unknown ids are skipped by the SELECT, never a FK
    violation). The primary book_catalog.category_id is untouched.

    Args:
        book_id: Target title's primary key.
        category_ids: Iterable of candidate category ids (anything
            int-coercible; junk is ignored).
    """
    try:
        book_id = int(book_id)
    except (TypeError, ValueError):
        return
    ids = []
    for cid in category_ids or []:
        try:
            cid = int(cid)
        except (TypeError, ValueError):
            continue
        if cid not in ids:
            ids.append(cid)
    db.execute('DELETE FROM book_categories WHERE book_id = %s', (book_id,))
    if not ids:
        return
    db.execute(
        '''INSERT INTO book_categories (book_id, category_id)
           SELECT %s, category_id FROM categories
           WHERE category_id = ANY(%s)
             AND category_id IS DISTINCT FROM
                 (SELECT category_id FROM book_catalog WHERE book_id = %s)
           ON CONFLICT DO NOTHING''',
        (book_id, ids, book_id)
    )


def get_distinct_material_types():
    """Book types that have at least one active catalogued item.

    Returns [(material_type, count), ...] ordered A-Z. Types with zero
    active books never appear, so the catalog sidebar and landing-page
    buttons only offer types that actually return results.
    """
    return db.fetch_all(
        "SELECT material_type, COUNT(*) FROM book_catalog "
        "WHERE catalog_status = 'active' "
        "AND material_type IS NOT NULL AND material_type != '' "
        'GROUP BY material_type ORDER BY material_type'
    )


def _filtered_where(query, field=None, year_from=None, year_to=None,
                    category=None, material_type=None, availability=None):
    """Shared WHERE builder for the public-catalog filtered search.

    Returns (where_clause, args). Sort does not affect row selection,
    so it stays with the callers.
    """
    conditions = ["catalog_status = 'active'"]
    args = []
    pattern = f'%{query}%' if query else None
    isbn_pattern = f'%{_isbn_search_text(query)}%' if query else None

    if query:
        if field == 'title':
            conditions.append('title ILIKE %s')
            args.append(pattern)
        elif field == 'author':
            conditions.append('author ILIKE %s')
            args.append(pattern)
        elif field == 'isbn':
            conditions.append('isbn ILIKE %s')
            args.append(isbn_pattern)
        elif field == 'category':
            conditions.append('subject_classification ILIKE %s')
            args.append(pattern)
        else:
            conditions.append('(title ILIKE %s OR author ILIKE %s OR isbn ILIKE %s OR subject_classification ILIKE %s)')
            args.extend([pattern, pattern, isbn_pattern, pattern])

    if year_from:
        try:
            args.append(int(year_from))
        except (TypeError, ValueError):
            pass
        else:
            conditions.append('year_published >= %s')
    if year_to:
        try:
            args.append(int(year_to))
        except (TypeError, ValueError):
            pass
        else:
            conditions.append('year_published <= %s')
    if category:
        if multi_cat_available():
            # Parens are load-bearing (see material_type above): the
            # secondary-categories EXISTS is OR-ed with the primary match.
            conditions.append(
                '(subject_classification = %s OR EXISTS '
                '(SELECT 1 FROM book_categories bc JOIN categories c '
                'ON c.category_id = bc.category_id '
                'WHERE bc.book_id = book_catalog.book_id AND c.name = %s))')
            args.append(category)
            args.append(category)
        else:
            conditions.append('subject_classification = %s')
            args.append(category)
    if material_type:
        if material_type == 'ebook' or material_type == 'E-Book':
            conditions.append('material_type = %s')
            args.append('E-Book')
        elif material_type == 'physical':
            # Parens are load-bearing: without them AND binds tighter than
            # OR, so a combined category + physical filter would match every
            # non-ebook row regardless of category.
            conditions.append('(material_type IS NULL OR material_type != %s)')
            args.append('E-Book')
        else:
            # Exact book-type match (Book, Reference, Periodical, Thesis).
            # Unknown values match zero rows — never 500.
            conditions.append('material_type = %s')
            args.append(material_type)
    DAILY_BLOCKED = (
        "(EXISTS (SELECT 1 FROM circulation_records c2 WHERE c2.book_id = book_catalog.book_id "
        "AND c2.borrow_type = 'overnight' AND c2.transaction_status IN ('active', 'overdue')) "
        "AND EXISTS (SELECT 1 FROM reservation_queue r WHERE r.book_id = book_catalog.book_id "
        "AND r.reservation_status = 'allocated'))"
    )
    AVAILABLE_COPY_EXISTS = (
        "EXISTS (SELECT 1 FROM accession_log al WHERE al.book_id = book_catalog.book_id "
        "AND NOT EXISTS (SELECT 1 FROM circulation_records c WHERE c.accession_id = al.accession_id "
        "AND c.transaction_status IN ('active', 'overdue')))"
        f" AND NOT {DAILY_BLOCKED}"
    )

    if availability == 'available':
        conditions.append(AVAILABLE_COPY_EXISTS)
    elif availability == 'borrowed':
        conditions.append(f'NOT {AVAILABLE_COPY_EXISTS}')

    where = 'WHERE ' + ' AND '.join(conditions)

    availability_col = f"CASE WHEN {AVAILABLE_COPY_EXISTS} THEN 'available' ELSE 'borrowed' END AS availability"

    available_count_col = (
        "(SELECT COUNT(*) FROM accession_log al WHERE al.book_id = book_catalog.book_id "
        "AND NOT EXISTS (SELECT 1 FROM circulation_records c WHERE c.accession_id = al.accession_id "
        "AND c.transaction_status IN ('active', 'overdue'))) AS available_count"
    )
    return where, tuple(args), availability_col, available_count_col


def search_books_filtered(query, field=None, year_from=None, year_to=None, sort_by=None,
                          category=None, material_type=None, availability=None,
                          page=1, per_page=50):
    """Filtered public-catalog search, paginated in SQL.

    Returns (rows, total): only the requested page is materialized — the
    per-row availability subqueries run for `per_page` rows instead of
    every match. Row shape is unchanged (book_catalog.* + availability +
    available_count), so callers and templates are unaffected.
    """
    page = max(1, page or 1)
    per_page = max(1, per_page or 50)
    where, args, availability_col, available_count_col = _filtered_where(
        query, field, year_from, year_to, category, material_type, availability)

    count_row = db.fetch_one(
        f'SELECT COUNT(*) FROM (SELECT DISTINCT ON ({DISTINCT_ORDER}) 1 FROM book_catalog {where}) sub',
        args
    )
    total = count_row[0] if count_row else 0

    if sort_by == 'title':
        order = 'ORDER BY title ASC'
    elif sort_by == 'year_desc':
        order = 'ORDER BY year_published DESC NULLS LAST, title ASC'
    else:
        order = f'ORDER BY {DISTINCT_ORDER}'

    offset = (page - 1) * per_page
    relevance_order, relevance_params = _relevance_order(query)

    def build(cols):
        base = (f'SELECT DISTINCT ON ({DISTINCT_ORDER}) {cols}, {availability_col}, {available_count_col} '
                f'FROM book_catalog {where} ORDER BY {DISTINCT_ORDER}')
        if sort_by in ('title', 'year_desc'):
            return (f'SELECT * FROM ({base}) AS deduped {order} LIMIT %s OFFSET %s',
                    args + (per_page, offset))
        if relevance_order is not None:
            return (f'SELECT * FROM ({base}) AS deduped {relevance_order} LIMIT %s OFFSET %s',
                    args + relevance_params + (per_page, offset))
        return (f'{base} LIMIT %s OFFSET %s', args + (per_page, offset))

    return _book_select(db.fetch_all, build), total


def get_recent_books(limit=5):
    """Fetch the most recently added titles for dashboard widgets.

    Orders distinct titles by date_added DESC (duplicates collapsed by
    DISTINCT ON) so the dashboard "new arrivals" strip shows fresh
    catalog additions.

    Args:
        limit: Maximum titles to return.

    Returns:
        List of book_catalog row tuples, newest first.
    """
    return _book_select(db.fetch_all, lambda cols: (
        f'SELECT DISTINCT ON ({DISTINCT_ORDER}) {cols} FROM book_catalog '
        f'ORDER BY {DISTINCT_ORDER}, date_added DESC LIMIT %s',
        (limit,)))


def create_accession(accession_number, book_id, librarian_id, source=None):
    """Add one physical copy of a book to the accession log.

    Inserts into accession_log linking the copy (accession_number, which
    must be unique) to its title and the processing librarian. Source
    records acquisition origin ('purchase', 'donation', 'others').

    Args:
        accession_number: Unique copy barcode/number string.
        book_id: FK into book_catalog for the title.
        librarian_id: Acting staff user_id recorded as processor.
        source: Acquisition source label, or None.

    Returns:
        Rowcount from the INSERT.
    """
    return db.execute(
        '''INSERT INTO accession_log (accession_number, book_id, librarian_id, source)
           VALUES (%s, %s, %s, %s)''',
        (accession_number, book_id, librarian_id, source)
    )


def get_accessions_by_book(book_id):
    """List every copy of one title in accession_id order.

    Used by the book detail/edit modals to show all barcodes, sources,
    and per-copy actions for a title. Returns [] (never None) so
    templates can iterate directly.

    Args:
        book_id: FK into book_catalog.

    Returns:
        List of full accession_log row tuples for the title.
    """
    return db.fetch_all(
        'SELECT * FROM accession_log WHERE book_id = %s ORDER BY accession_id',
        (book_id,)
    ) or []


def get_accession_by_number(accession_number):
    """Fetch one copy by its exact accession number string.

    Used to detect duplicate barcodes before insert and to resolve
    scans/returns typed by number.

    Args:
        accession_number: Exact copy number to look up.

    Returns:
        Full accession_log row tuple, or None if not found.
    """
    return db.fetch_one(
        'SELECT * FROM accession_log WHERE accession_number = %s',
        (accession_number,)
    )


def get_accession_by_id(accession_id):
    """Fetch one copy by its primary key.

    Used by edit/delete-copy and circulation flows that carry the
    numeric accession_id rather than the barcode string.

    Args:
        accession_id: Primary key of accession_log.

    Returns:
        Full accession_log row tuple, or None if not found.
    """
    return db.fetch_one(
        'SELECT * FROM accession_log WHERE accession_id = %s',
        (accession_id,)
    )


def get_accessions_for_books(book_ids):
    """Batch-fetch copy rows for many titles for list-page rendering.

    Avoids N+1 queries on catalog tables by pulling (accession_id,
    accession_number, book_id, source, date_accessioned) for all given
    titles in one ANY(%s) query, ordered by accession_id. Empty input
    short-circuits to [] without hitting the DB.

    Args:
        book_ids: Iterable of book_catalog primary keys.

    Returns:
        List of 5-tuple copy rows (possibly empty).
    """
    if not book_ids:
        return []
    return db.fetch_all(
        'SELECT accession_id, accession_number, book_id, source, date_accessioned '
        'FROM accession_log WHERE book_id = ANY(%s) ORDER BY accession_id',
        (book_ids,)
    ) or []


def update_accession(accession_id, accession_number, source, updated_by=None):
    """Edit a copy's barcode number and acquisition source.

    Updates accession_number (must stay unique — callers pre-check),
    source, and audit stamps for one accession_log row.

    Args:
        accession_id: Target copy's primary key.
        accession_number: New unique barcode string.
        source: New source label ('purchase', 'donation', 'others').
        updated_by: Acting staff user_id for the audit stamp.

    Returns:
        Rowcount from the UPDATE.
    """
    return db.execute(
        'UPDATE accession_log SET accession_number=%s, source=%s, updated_at=NOW(), updated_by=%s WHERE accession_id=%s',
        (accession_number, source, updated_by, accession_id)
    )


def delete_accession(accession_id):
    """Hard-delete one copy row by primary key.

    Callers must first check accession_referenced and refuse when the
    copy has circulation or inventory history, otherwise the DELETE
    would hit a FK violation (500).

    Args:
        accession_id: Target copy's primary key.
    """
    db.execute('DELETE FROM accession_log WHERE accession_id = %s', (accession_id,))


def accession_referenced(accession_id):
    """Check whether a copy has history blocking its deletion.

    Returns True when any circulation_records or inventory_status row
    references the accession_id, meaning delete_accession would violate
    a foreign key. The delete-copy route uses this to show a friendly
    refusal instead of a 500.

    Args:
        accession_id: Copy primary key to safety-check.

    Returns:
        True when the copy is referenced and must be kept.
    """
    row = db.fetch_one(
        '''SELECT 1 WHERE EXISTS (SELECT 1 FROM circulation_records WHERE accession_id = %s)
              OR EXISTS (SELECT 1 FROM inventory_status WHERE accession_id = %s)''',
        (accession_id, accession_id)
    )
    return row is not None


def add_favorite(user_id, book_id):
    """Star a book for a user, ignoring duplicates silently.

    Inserts into user_favorites with ON CONFLICT DO NOTHING so
    re-favoriting is a safe no-op powering the catalog heart toggle.

    Args:
        user_id: Owner of the favorites list.
        book_id: Title to star.

    Returns:
        Rowcount from the INSERT (0 when already favorited).
    """
    return db.execute(
        'INSERT INTO user_favorites (user_id, book_id) VALUES (%s, %s) ON CONFLICT DO NOTHING',
        (user_id, book_id)
    )


def remove_favorite(user_id, book_id):
    """Unstar a book for a user.

    Deletes the single user_favorites row for the pair; removing a
    non-favorite simply affects zero rows.

    Args:
        user_id: Owner of the favorites list.
        book_id: Title to unstar.

    Returns:
        Rowcount from the DELETE.
    """
    return db.execute(
        'DELETE FROM user_favorites WHERE user_id = %s AND book_id = %s',
        (user_id, book_id)
    )


def get_user_favorites(user_id):
    """List a user's starred books newest-first.

    Joins user_favorites to book_catalog so the favorites shelf renders
    full title rows ordered by when they were starred.

    Args:
        user_id: Owner of the favorites list.

    Returns:
        List of book_catalog row tuples the user starred.
    """
    return db.fetch_all(
        '''SELECT b.* FROM book_catalog b
           JOIN user_favorites f ON b.book_id = f.book_id
           WHERE f.user_id = %s ORDER BY f.created_at DESC''',
        (user_id,)
    )


def update_book(book_id, title, author, edition, publisher, year_published,
                subject_classification, call_number, isbn, material_type, description,
                updated_by=None, category_id=None, ebook_url=None):
    """Overwrite a title's bibliographic metadata plus audit stamps.

    Updates all editable book_catalog columns for one book_id and
    stamps updated_at/updated_by. Copies (accessions) are untouched —
    they are managed via the accession functions.

    Args:
        book_id: Target title's primary key.
        title: New title. author: New author. edition: New edition.
        publisher: New publisher. year_published: New year.
        subject_classification: New category. call_number: New call no.
        isbn: New ISBN. material_type: New type. description: New blurb.
        updated_by: Acting staff user_id for the audit stamp.
        category_id: FK into categories, or None to auto-resolve from
            subject_classification (case-insensitive match or create).

    Returns:
        Rowcount from the UPDATE.
    """
    if category_id is None:
        category_id, _ = resolve_category(subject_classification)
    isbn = normalize_isbn(isbn) or None
    ebook_url = clean_ebook_url(ebook_url)

    def build(available):
        assigns = [
            'title=%s', 'author=%s', 'edition=%s', 'publisher=%s',
            'year_published=%s', 'subject_classification=%s', 'call_number=%s',
            'isbn=%s', 'material_type=%s', 'description=%s',
        ]
        params = [title, author, edition, publisher, year_published,
                  subject_classification, call_number, isbn, material_type,
                  description]
        if 'category_id' in available:
            assigns.append('category_id=%s')
            params.append(category_id)
        if 'ebook_url' in available:
            assigns.append('ebook_url=%s')
            params.append(ebook_url)
        if 'updated_at' in available:
            assigns.append('updated_at=NOW()')
        if 'updated_by' in available:
            assigns.append('updated_by=%s')
            params.append(updated_by)
        params.append(book_id)
        return ('UPDATE book_catalog SET ' + ', '.join(assigns)
                + ' WHERE book_id=%s', tuple(params))

    return _execute_book_write(build)


def get_books_by_status(status):
    """List all titles with one catalog_status for exports and tab views.

    Returns every book_catalog row with the given status (e.g.
    'archived') plus its comma-joined accession numbers, ordered by
    title. The staff page must use the paginated variant instead for
    large result sets.

    Args:
        status: Required catalog_status value ('active'/'archived').

    Returns:
        List of (book_catalog.* + extra_categories + accession_numbers)
        row tuples. The extra-categories column is omitted on unmigrated
        databases.
    """
    extra = f', {EXTRA_CATEGORIES_SUBQUERY} AS extra_categories' if multi_cat_available() else ''
    return _book_select(db.fetch_all, lambda cols: (
        f'SELECT {cols}{extra}, {ACCESSION_SUBQUERY} AS accession_numbers '
        f'FROM book_catalog WHERE catalog_status = %s ORDER BY title',
        (status,)))


def delete_book(book_id):
    """Hard-delete one title row by primary key.

    Callers must enforce archive-before-delete (refuse unless
    catalog_status='archived') and ensure its accessions are already
    cleared, otherwise the DELETE hits FK or policy violations.

    Args:
        book_id: Target title's primary key.
    """
    db.execute('DELETE FROM book_catalog WHERE book_id = %s', (book_id,))


def update_book_status(book_id, status, updated_by=None):
    """Flip a title between active and archived plus audit stamps.

    Implements the archive-before-delete workflow: archiving hides the
    title from search and exports while preserving history; activating
    restores it.

    Args:
        book_id: Target title's primary key.
        status: New catalog_status ('active' or 'archived').
        updated_by: Acting staff user_id for the audit stamp.

    Returns:
        Rowcount from the UPDATE.
    """
    return db.execute(
        'UPDATE book_catalog SET catalog_status=%s, updated_at=NOW(), updated_by=%s WHERE book_id=%s',
        (status, updated_by, book_id)
    )


def search_books_paginated(query, field, page, per_page, sort_by=None,
                           material_type=None):
    """Search active titles with staff-page pagination and sorting.

    Builds an ILIKE WHERE for the field scope (title/author/isbn/
    accession, or all columns plus accession numbers when unscoped),
    always restricted to catalog_status='active' so archived books only
    appear under ?status=archived. Returns the requested page plus the
    total distinct-title count; non-default sorts wrap the deduped
    query and re-sort outside because DISTINCT ON requires its own
    inner ordering.

    Args:
        query: Search substring (empty means list all active).
        field: Column scope or 'accession' for barcode search.
        page: 1-based page number.
        per_page: Rows per page.
        sort_by: Allowlisted sort key, or None for title A-Z.

    Returns:
        Tuple (rows, total) where rows are (book_catalog.* +
        accession_numbers) tuples for the page.
    """
    offset = (page - 1) * per_page
    pattern = f'%{query}%'
    isbn_pattern = f'%{_isbn_search_text(query)}%'

    if field == 'title':
        where = 'WHERE title ILIKE %s'
        args = (pattern,)
    elif field == 'author':
        where = 'WHERE author ILIKE %s'
        args = (pattern,)
    elif field == 'isbn':
        where = 'WHERE isbn ILIKE %s'
        args = (isbn_pattern,)
    elif field == 'accession':
        where = 'WHERE book_id IN (SELECT book_id FROM accession_log WHERE accession_number ILIKE %s)'
        args = (pattern,)
    elif field and query:
        where = 'WHERE %s ILIKE %s'
        args = (field, pattern)
    elif query:
        # Parens keep the trailing AND filters (status, material type)
        # applying to the whole term instead of only the last OR arm.
        where = '''WHERE (title ILIKE %s OR author ILIKE %s OR isbn ILIKE %s
                      OR subject_classification ILIKE %s
                      OR book_id IN (SELECT book_id FROM accession_log WHERE accession_number ILIKE %s))'''
        args = (pattern, pattern, isbn_pattern, pattern, pattern)
    else:
        where = ''
        args = ()

    # Archived books never appear in search — only under ?status=archived.
    if where:
        where += " AND catalog_status = 'active'"
    else:
        where = "WHERE catalog_status = 'active'"

    if material_type:
        where += ' AND material_type = %s'
        args = args + (material_type,)

    count_row = db.fetch_one(
        f'SELECT COUNT(*) FROM (SELECT DISTINCT ON ({DISTINCT_ORDER}) 1 FROM book_catalog {where}) sub', args
    )
    total = count_row[0] if count_row else 0

    order = _catalog_sort_clause(sort_by)
    if order is None:
        rows = _book_select(db.fetch_all, lambda cols: (
            f'SELECT DISTINCT ON ({DISTINCT_ORDER}) {cols}, {ACCESSION_SUBQUERY} AS accession_numbers '
            f'FROM book_catalog {where} ORDER BY {DISTINCT_ORDER}, date_added DESC LIMIT %s OFFSET %s',
            args + (per_page, offset)))
    else:
        rows = _book_select(db.fetch_all, lambda cols: (
            f'SELECT * FROM (SELECT DISTINCT ON ({DISTINCT_ORDER}) {cols}, {ACCESSION_SUBQUERY} AS accession_numbers '
            f'FROM book_catalog {where} ORDER BY {DISTINCT_ORDER}, date_added DESC) AS sorted_books '
            f'ORDER BY {order} LIMIT %s OFFSET %s',
            args + (per_page, offset)))
    return rows, total
