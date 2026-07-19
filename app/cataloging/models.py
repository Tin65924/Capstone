from app.database import db


def create_book(title, author, edition, publisher, year_published, subject_classification,
                call_number, isbn, material_type, description):
    return db.execute(
        '''INSERT INTO book_catalog (title, author, edition, publisher, year_published,
           subject_classification, call_number, isbn, material_type, description, catalog_status)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
        (title, author, edition, publisher, year_published, subject_classification,
         call_number, isbn, material_type, description, 'active')
    )


def search_books(query, field=None):
    pattern = f'%{query}%'
    if field == 'title':
        return db.fetch_all(
            'SELECT * FROM book_catalog WHERE title ILIKE %s ORDER BY title',
            (pattern,)
        )
    elif field == 'author':
        return db.fetch_all(
            'SELECT * FROM book_catalog WHERE author ILIKE %s ORDER BY title',
            (pattern,)
        )
    elif field == 'isbn':
        return db.fetch_all(
            'SELECT * FROM book_catalog WHERE isbn ILIKE %s ORDER BY title',
            (pattern,)
        )
    elif field == 'category':
        return db.fetch_all(
            'SELECT * FROM book_catalog WHERE subject_classification ILIKE %s ORDER BY title',
            (pattern,)
        )
    return db.fetch_all(
        '''SELECT * FROM book_catalog
           WHERE title ILIKE %s OR author ILIKE %s OR isbn ILIKE %s
              OR subject_classification ILIKE %s
           ORDER BY title''',
        (pattern, pattern, pattern, pattern)
    )


def get_book_by_id(book_id):
    return db.fetch_one('SELECT * FROM book_catalog WHERE book_id = %s', (book_id,))


def get_all_books():
    return db.fetch_all('SELECT * FROM book_catalog ORDER BY title')


def get_recent_books(limit=5):
    return db.fetch_all(
        'SELECT * FROM book_catalog ORDER BY date_added DESC LIMIT %s',
        (limit,)
    )


def create_accession(accession_number, book_id, librarian_id, source=None, copy_number=None):
    return db.execute(
        '''INSERT INTO accession_log (accession_number, book_id, librarian_id, source, copy_number)
           VALUES (%s, %s, %s, %s, %s)''',
        (accession_number, book_id, librarian_id, source, copy_number)
    )


def get_accessions_by_book(book_id):
    return db.fetch_all(
        'SELECT * FROM accession_log WHERE book_id = %s ORDER BY copy_number',
        (book_id,)
    )


def get_accession_by_number(accession_number):
    return db.fetch_one(
        'SELECT * FROM accession_log WHERE accession_number = %s',
        (accession_number,)
    )


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
                      OR subject_classification ILIKE %s'''
        args = (pattern, pattern, pattern, pattern)
    else:
        where = ''
        args = ()

    count_row = db.fetch_one(
        f'SELECT COUNT(*) FROM book_catalog {where}', args
    )
    total = count_row[0] if count_row else 0

    rows = db.fetch_all(
        f'''SELECT * FROM book_catalog {where} ORDER BY date_added DESC, title LIMIT %s OFFSET %s''',
        args + (per_page, offset)
    )
    return rows, total
