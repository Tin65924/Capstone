from app.database import db


def create_book(title, author, edition, publisher, year_published, subject_classification,
                call_number, isbn, material_type, description):
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
    return db.fetch_one('SELECT * FROM book_catalog WHERE book_id = %s', (book_id,))


def get_book_by_title_author_isbn(title, author, isbn):
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
    """Distinct existing values matching a prefix for autosuggestions."""
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


def get_all_books():
    return db.fetch_all(
        f'SELECT DISTINCT ON ({DISTINCT_ORDER}) *, {ACCESSION_SUBQUERY} AS accession_numbers FROM book_catalog ORDER BY {DISTINCT_ORDER}')


def get_distinct_categories():
    return db.fetch_all(
        'SELECT DISTINCT subject_classification FROM book_catalog WHERE subject_classification IS NOT NULL AND subject_classification != \'\' ORDER BY subject_classification'
    )


def search_books_filtered(query, field=None, year_from=None, year_to=None, sort_by=None,
                          category=None, material_type=None, availability=None):
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
        conditions.append('year_published >= %s')
        args.append(int(year_from))
    if year_to:
        conditions.append('year_published <= %s')
        args.append(int(year_to))
    if category:
        conditions.append('subject_classification = %s')
        args.append(category)
    if material_type:
        if material_type == 'ebook':
            conditions.append('material_type = %s')
            args.append('E-Book')
        elif material_type == 'physical':
            conditions.append('material_type IS NULL OR material_type != %s')
            args.append('E-Book')
    AVAILABLE_COPY_EXISTS = (
        "EXISTS (SELECT 1 FROM accession_log al WHERE al.book_id = book_catalog.book_id "
        "AND NOT EXISTS (SELECT 1 FROM circulation_records c WHERE c.accession_id = al.accession_id "
        "AND c.transaction_status IN ('active', 'overdue')))"
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

    if sort_by == 'title':
        order = 'ORDER BY title ASC'
    elif sort_by == 'year_desc':
        order = 'ORDER BY year_published DESC NULLS LAST, title ASC'
    else:
        order = f'ORDER BY {DISTINCT_ORDER}'

    base = f'SELECT DISTINCT ON ({DISTINCT_ORDER}) book_catalog.*, {availability_col}, {available_count_col} FROM book_catalog {where} ORDER BY {DISTINCT_ORDER}'
    if sort_by in ('title', 'year_desc'):
        return db.fetch_all(
            f'SELECT * FROM ({base}) AS deduped {order}',
            tuple(args)
        )
    return db.fetch_all(base, tuple(args))


def get_recent_books(limit=5):
    return db.fetch_all(
        f'SELECT DISTINCT ON ({DISTINCT_ORDER}) * FROM book_catalog ORDER BY {DISTINCT_ORDER}, date_added DESC LIMIT %s',
        (limit,)
    )


def create_accession(accession_number, book_id, librarian_id, source=None):
    return db.execute(
        '''INSERT INTO accession_log (accession_number, book_id, librarian_id, source)
           VALUES (%s, %s, %s, %s)''',
        (accession_number, book_id, librarian_id, source)
    )


def get_accessions_by_book(book_id):
    return db.fetch_all(
        'SELECT * FROM accession_log WHERE book_id = %s ORDER BY accession_id',
        (book_id,)
    )


def get_accession_by_number(accession_number):
    return db.fetch_one(
        'SELECT * FROM accession_log WHERE accession_number = %s',
        (accession_number,)
    )


def get_accession_by_id(accession_id):
    return db.fetch_one(
        'SELECT * FROM accession_log WHERE accession_id = %s',
        (accession_id,)
    )


def get_accessions_for_books(book_ids):
    if not book_ids:
        return []
    return db.fetch_all(
        'SELECT accession_id, accession_number, book_id, source, date_accessioned '
        'FROM accession_log WHERE book_id = ANY(%s) ORDER BY accession_id',
        (book_ids,)
    )


def update_accession(accession_id, accession_number, source):
    return db.execute(
        'UPDATE accession_log SET accession_number=%s, source=%s WHERE accession_id=%s',
        (accession_number, source, accession_id)
    )


def delete_accession(accession_id):
    db.execute('DELETE FROM accession_log WHERE accession_id = %s', (accession_id,))


def accession_referenced(accession_id):
    row = db.fetch_one(
        '''SELECT 1 WHERE EXISTS (SELECT 1 FROM circulation_records WHERE accession_id = %s)
              OR EXISTS (SELECT 1 FROM inventory_status WHERE accession_id = %s)''',
        (accession_id, accession_id)
    )
    return row is not None


def add_favorite(user_id, book_id):
    return db.execute(
        'INSERT INTO user_favorites (user_id, book_id) VALUES (%s, %s) ON CONFLICT DO NOTHING',
        (user_id, book_id)
    )


def remove_favorite(user_id, book_id):
    return db.execute(
        'DELETE FROM user_favorites WHERE user_id = %s AND book_id = %s',
        (user_id, book_id)
    )


def get_user_favorites(user_id):
    return db.fetch_all(
        '''SELECT b.* FROM book_catalog b
           JOIN user_favorites f ON b.book_id = f.book_id
           WHERE f.user_id = %s ORDER BY f.created_at DESC''',
        (user_id,)
    )


def update_book(book_id, title, author, edition, publisher, year_published,
                subject_classification, call_number, isbn, material_type, description):
    return db.execute(
        '''UPDATE book_catalog SET title=%s, author=%s, edition=%s, publisher=%s,
           year_published=%s, subject_classification=%s, call_number=%s,
           isbn=%s, material_type=%s, description=%s
           WHERE book_id=%s''',
        (title, author, edition, publisher, year_published,
         subject_classification, call_number, isbn, material_type, description, book_id)
    )


def get_books_by_status(status):
    return db.fetch_all(
        f'SELECT *, {ACCESSION_SUBQUERY} AS accession_numbers FROM book_catalog WHERE catalog_status = %s ORDER BY title',
        (status,)
    )


def delete_book(book_id):
    db.execute('DELETE FROM book_catalog WHERE book_id = %s', (book_id,))


def update_book_status(book_id, status):
    return db.execute(
        'UPDATE book_catalog SET catalog_status=%s WHERE book_id=%s',
        (status, book_id)
    )


def search_books_paginated(query, field, page, per_page):
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

    count_row = db.fetch_one(
        f'SELECT COUNT(*) FROM (SELECT DISTINCT ON ({DISTINCT_ORDER}) 1 FROM book_catalog {where}) sub', args
    )
    total = count_row[0] if count_row else 0

    rows = db.fetch_all(
        f'''SELECT DISTINCT ON ({DISTINCT_ORDER}) *, {ACCESSION_SUBQUERY} AS accession_numbers FROM book_catalog {where} ORDER BY {DISTINCT_ORDER}, date_added DESC LIMIT %s OFFSET %s''',
        args + (per_page, offset)
    )
    return rows, total
