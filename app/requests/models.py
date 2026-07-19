from app.database import db


def create_request(requester_id, book_title, author=None):
    return db.execute(
        '''INSERT INTO request_records (requester_id, book_title, author, request_status)
           VALUES (%s, %s, %s, %s)''',
        (requester_id, book_title, author, 'pending_review')
    )


def get_requests(status=None):
    if status:
        return db.fetch_all(
            'SELECT * FROM request_records WHERE request_status = %s ORDER BY request_date DESC',
            (status,)
        )
    return db.fetch_all('SELECT * FROM request_records ORDER BY request_date DESC')


def get_request_by_id(request_id):
    return db.fetch_one(
        'SELECT * FROM request_records WHERE request_id = %s',
        (request_id,)
    )


def update_request_status(request_id, status, reviewer_id=None):
    if reviewer_id:
        return db.execute(
            'UPDATE request_records SET request_status = %s, reviewed_by = %s, review_date = NOW() WHERE request_id = %s',
            (status, reviewer_id, request_id)
        )
    return db.execute(
        'UPDATE request_records SET request_status = %s WHERE request_id = %s',
        (status, request_id)
    )


def get_demand_count(book_title):
    row = db.fetch_one(
        'SELECT COUNT(*) FROM request_records WHERE book_title = %s',
        (book_title,)
    )
    return row[0] if row else 0


def get_demand_by_role():
    return db.fetch_all(
        '''SELECT rr.book_title, r.role_name, COUNT(*) AS count
           FROM request_records rr
           JOIN borrowers b ON rr.requester_id = b.borrower_id
           JOIN user_accounts u ON b.user_id = u.user_id
           JOIN roles r ON u.role_id = r.role_id
           WHERE rr.request_status IN ('pending_review', 'approved')
           GROUP BY rr.book_title, r.role_name'''
    )


def check_duplicate_request(requester_id, book_title):
    row = db.fetch_one(
        'SELECT request_id FROM request_records WHERE requester_id = %s AND book_title = %s',
        (requester_id, book_title)
    )
    return row is not None


def check_existing_in_collection(book_title):
    row = db.fetch_one(
        'SELECT book_id FROM book_catalog WHERE title = %s',
        (book_title,)
    )
    return row is not None
