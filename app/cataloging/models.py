from app.database import db


def create_book(title, author, edition, publisher, year_published, subject_classification,
                call_number, isbn, material_type, description):
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

    Returns:
        New book_id integer, or None if the INSERT returned nothing.
    """
    rows = db.execute(
        '''INSERT INTO book_catalog (title, author, edition, publisher, year_published,
           subject_classification, call_number, isbn, material_type, description, catalog_status)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
           RETURNING book_id''',
        (title, author, edition, publisher, year_published, subject_classification,
         call_number, isbn, material_type, description, 'active')
    )
    return rows[0][0] if rows else None


DISTINCT_ORDER = 'title, author, COALESCE(isbn, \'\')'

# Trailing column appended by the cataloging-page list queries; a book can
# have multiple accessions, so they are comma-joined.
ACCESSION_SUBQUERY = (
    "(SELECT COALESCE(string_agg(accession_number, ', ' ORDER BY accession_id), '') "
    "FROM accession_log WHERE accession_log.book_id = book_catalog.book_id)"
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
    if field == 'title':
        return db.fetch_all(
            f'SELECT DISTINCT ON ({DISTINCT_ORDER}) * FROM book_catalog WHERE title ILIKE %s ORDER BY {DISTINCT_ORDER}',
            (pattern,)
        )
    elif field == 'author':
        return db.fetch_all(
            f'SELECT DISTINCT ON ({DISTINCT_ORDER}) * FROM book_catalog WHERE author ILIKE %s ORDER BY {DISTINCT_ORDER}',
            (pattern,)
        )
    elif field == 'isbn':
        return db.fetch_all(
            f'SELECT DISTINCT ON ({DISTINCT_ORDER}) * FROM book_catalog WHERE isbn ILIKE %s ORDER BY {DISTINCT_ORDER}',
            (pattern,)
        )
    elif field == 'category':
        return db.fetch_all(
            f'SELECT DISTINCT ON ({DISTINCT_ORDER}) * FROM book_catalog WHERE subject_classification ILIKE %s ORDER BY {DISTINCT_ORDER}',
            (pattern,)
        )
    return db.fetch_all(
        f'''SELECT DISTINCT ON ({DISTINCT_ORDER}) * FROM book_catalog
           WHERE title ILIKE %s OR author ILIKE %s OR isbn ILIKE %s
              OR subject_classification ILIKE %s
           ORDER BY {DISTINCT_ORDER}''',
        (pattern, pattern, pattern, pattern)
    )


def get_book_by_id(book_id):
    """Fetch one catalog row by primary key regardless of status.

    Used by edit, archive-check, detail, and history views that must see
    archived books too (public search filters those out separately).

    Args:
        book_id: Primary key of book_catalog.

    Returns:
        Full book_catalog row tuple, or None if not found.
    """
    return db.fetch_one('SELECT * FROM book_catalog WHERE book_id = %s', (book_id,))


def get_book_by_title_author_isbn(title, author, isbn):
    """Find a duplicate title by exact title/author/ISBN match.

    Guards the add-book flow against double entry: when isbn is given
    it must match exactly, otherwise the match requires isbn IS NULL so
    an ISBN-less row never collides with an ISBN-bearing one.

    Args:
        title: Exact title to match.
        author: Exact author to match.
        isbn: Exact ISBN to match, or falsy to match NULL-ISBN rows.

    Returns:
        1-tuple (book_id,) of the duplicate, or None if unique.
    """
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
            (pattern, limit)
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
        (pattern, pattern, pattern, pattern, limit)
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
    materialized per request.
    """
    return db.fetch_all(
        f"SELECT DISTINCT ON ({DISTINCT_ORDER}) *, {ACCESSION_SUBQUERY} AS accession_numbers FROM book_catalog WHERE catalog_status = 'active' ORDER BY {DISTINCT_ORDER}")


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


def get_all_books_paginated(page=1, per_page=20, sort_by=None):
    """Paginated active-book listing for the staff page. Same row shape
    as get_all_books; returns (rows, total)."""
    page = max(1, page or 1)
    per_page = max(1, per_page or 20)
    where = "WHERE catalog_status = 'active'"
    total = _count_books(where, ())
    order = _catalog_sort_clause(sort_by)
    if order is None:
        rows = db.fetch_all(
            f'SELECT DISTINCT ON ({DISTINCT_ORDER}) *, {ACCESSION_SUBQUERY} AS accession_numbers '
            f'FROM book_catalog {where} ORDER BY {DISTINCT_ORDER} LIMIT %s OFFSET %s',
            (per_page, (page - 1) * per_page)
        )
    else:
        # DISTINCT ON requires the inner ORDER BY to start with the
        # distinct columns, so non-default sorts wrap the deduped page
        # query and re-sort outside (same pattern as the public catalog).
        rows = db.fetch_all(
            f'SELECT * FROM (SELECT DISTINCT ON ({DISTINCT_ORDER}) *, {ACCESSION_SUBQUERY} AS accession_numbers '
            f'FROM book_catalog {where} ORDER BY {DISTINCT_ORDER}) AS sorted_books '
            f'ORDER BY {order} LIMIT %s OFFSET %s',
            (per_page, (page - 1) * per_page)
        )
    return rows, total


def get_books_by_status_paginated(status, page=1, per_page=20, sort_by=None):
    """Paginated status listing for the staff page. Same row shape as
    get_books_by_status; returns (rows, total)."""
    page = max(1, page or 1)
    per_page = max(1, per_page or 20)
    where = 'WHERE catalog_status = %s'
    total = _count_books(where, (status,))
    order = _catalog_sort_clause(sort_by) or 'title'
    rows = db.fetch_all(
        f'SELECT *, {ACCESSION_SUBQUERY} AS accession_numbers FROM book_catalog '
        f'{where} ORDER BY {order} LIMIT %s OFFSET %s',
        (status, per_page, (page - 1) * per_page)
    )
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


def get_books_by_copy_status_paginated(copy_status, page=1, per_page=20, sort_by=None):
    """Paginated problem-copy listing for the staff page. Same row shape
    as get_books_by_copy_status; returns (rows, total). Unknown filters
    return ([], 0), mirroring get_books_by_copy_status."""
    condition = _copy_status_condition(copy_status)
    if condition is None:
        return [], 0
    page = max(1, page or 1)
    per_page = max(1, per_page or 20)
    where = f"WHERE book_catalog.catalog_status = 'active' AND ({condition})"
    total = _count_books(where, ())
    order = _catalog_sort_clause(sort_by)
    if order is None:
        rows = db.fetch_all(
            f'SELECT DISTINCT ON ({DISTINCT_ORDER}) *, {ACCESSION_SUBQUERY} AS accession_numbers '
            f'FROM book_catalog {where} ORDER BY {DISTINCT_ORDER} LIMIT %s OFFSET %s',
            (per_page, (page - 1) * per_page)
        )
    else:
        rows = db.fetch_all(
            f'SELECT * FROM (SELECT DISTINCT ON ({DISTINCT_ORDER}) *, {ACCESSION_SUBQUERY} AS accession_numbers '
            f'FROM book_catalog {where} ORDER BY {DISTINCT_ORDER}) AS sorted_books '
            f'ORDER BY {order} LIMIT %s OFFSET %s',
            (per_page, (page - 1) * per_page)
        )
    return rows, total


def get_distinct_categories():
    """List every non-empty subject classification A-Z for filter options.

    Feeds the category dropdown on the staff and public catalog pages.

    Returns:
        List of 1-tuples (subject_classification,) ordered alphabetically.
    """
    return db.fetch_all(
        'SELECT DISTINCT subject_classification FROM book_catalog WHERE subject_classification IS NOT NULL AND subject_classification != \'\' ORDER BY subject_classification'
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

    if query:
        if field == 'title':
            conditions.append('title ILIKE %s')
            args.append(pattern)
        elif field == 'author':
            conditions.append('author ILIKE %s')
            args.append(pattern)
        elif field == 'isbn':
            conditions.append('isbn ILIKE %s')
            args.append(pattern)
        elif field == 'category':
            conditions.append('subject_classification ILIKE %s')
            args.append(pattern)
        else:
            conditions.append('(title ILIKE %s OR author ILIKE %s OR isbn ILIKE %s OR subject_classification ILIKE %s)')
            args.extend([pattern, pattern, pattern, pattern])

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
        conditions.append('subject_classification = %s')
        args.append(category)
    if material_type:
        if material_type == 'ebook':
            conditions.append('material_type = %s')
            args.append('E-Book')
        elif material_type == 'physical':
            # Parens are load-bearing: without them AND binds tighter than
            # OR, so a combined category + physical filter would match every
            # non-ebook row regardless of category.
            conditions.append('(material_type IS NULL OR material_type != %s)')
            args.append('E-Book')
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

    base = f'SELECT DISTINCT ON ({DISTINCT_ORDER}) book_catalog.*, {availability_col}, {available_count_col} FROM book_catalog {where} ORDER BY {DISTINCT_ORDER}'
    offset = (page - 1) * per_page
    if sort_by in ('title', 'year_desc'):
        return db.fetch_all(
            f'SELECT * FROM ({base}) AS deduped {order} LIMIT %s OFFSET %s',
            args + (per_page, offset)
        ), total
    relevance_order, relevance_params = _relevance_order(query)
    if relevance_order is not None:
        return db.fetch_all(
            f'SELECT * FROM ({base}) AS deduped {relevance_order} LIMIT %s OFFSET %s',
            args + relevance_params + (per_page, offset)
        ), total
    return db.fetch_all(
        f'{base} LIMIT %s OFFSET %s',
        args + (per_page, offset)
    ), total


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
    return db.fetch_all(
        f'SELECT DISTINCT ON ({DISTINCT_ORDER}) * FROM book_catalog ORDER BY {DISTINCT_ORDER}, date_added DESC LIMIT %s',
        (limit,)
    )


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
                updated_by=None):
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

    Returns:
        Rowcount from the UPDATE.
    """
    return db.execute(
        '''UPDATE book_catalog SET title=%s, author=%s, edition=%s, publisher=%s,
           year_published=%s, subject_classification=%s, call_number=%s,
           isbn=%s, material_type=%s, description=%s,
           updated_at=NOW(), updated_by=%s
           WHERE book_id=%s''',
        (title, author, edition, publisher, year_published,
         subject_classification, call_number, isbn, material_type, description,
         updated_by, book_id)
    )


def get_books_by_status(status):
    """List all titles with one catalog_status for exports and tab views.

    Returns every book_catalog row with the given status (e.g.
    'archived') plus its comma-joined accession numbers, ordered by
    title. The staff page must use the paginated variant instead for
    large result sets.

    Args:
        status: Required catalog_status value ('active'/'archived').

    Returns:
        List of (book_catalog.* + accession_numbers) row tuples.
    """
    return db.fetch_all(
        f'SELECT *, {ACCESSION_SUBQUERY} AS accession_numbers FROM book_catalog WHERE catalog_status = %s ORDER BY title',
        (status,)
    )


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


def search_books_paginated(query, field, page, per_page, sort_by=None):
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

    if field == 'title':
        where = 'WHERE title ILIKE %s'
        args = (pattern,)
    elif field == 'author':
        where = 'WHERE author ILIKE %s'
        args = (pattern,)
    elif field == 'isbn':
        where = 'WHERE isbn ILIKE %s'
        args = (pattern,)
    elif field == 'accession':
        where = 'WHERE book_id IN (SELECT book_id FROM accession_log WHERE accession_number ILIKE %s)'
        args = (pattern,)
    elif field and query:
        where = 'WHERE %s ILIKE %s'
        args = (field, pattern)
    elif query:
        where = '''WHERE title ILIKE %s OR author ILIKE %s OR isbn ILIKE %s
                      OR subject_classification ILIKE %s
                      OR book_id IN (SELECT book_id FROM accession_log WHERE accession_number ILIKE %s)'''
        args = (pattern, pattern, pattern, pattern, pattern)
    else:
        where = ''
        args = ()

    # Archived books never appear in search — only under ?status=archived.
    if where:
        where += " AND catalog_status = 'active'"
    else:
        where = "WHERE catalog_status = 'active'"

    count_row = db.fetch_one(
        f'SELECT COUNT(*) FROM (SELECT DISTINCT ON ({DISTINCT_ORDER}) 1 FROM book_catalog {where}) sub', args
    )
    total = count_row[0] if count_row else 0

    order = _catalog_sort_clause(sort_by)
    if order is None:
        rows = db.fetch_all(
            f'''SELECT DISTINCT ON ({DISTINCT_ORDER}) *, {ACCESSION_SUBQUERY} AS accession_numbers FROM book_catalog {where} ORDER BY {DISTINCT_ORDER}, date_added DESC LIMIT %s OFFSET %s''',
            args + (per_page, offset)
        )
    else:
        rows = db.fetch_all(
            f'''SELECT * FROM (SELECT DISTINCT ON ({DISTINCT_ORDER}) *, {ACCESSION_SUBQUERY} AS accession_numbers FROM book_catalog {where} ORDER BY {DISTINCT_ORDER}, date_added DESC) AS sorted_books ORDER BY {order} LIMIT %s OFFSET %s''',
            args + (per_page, offset)
        )
    return rows, total
