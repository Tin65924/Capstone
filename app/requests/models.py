from app.database import db


def create_request(requester_id, book_title, author=None):
    matched_book_id = check_existing_in_collection(book_title)
    status = 'existing_in_collection' if matched_book_id else 'pending_review'

    rows = db.execute(
        '''INSERT INTO request_records (requester_id, book_title, author, request_status, matched_book_id)
           VALUES (%s, %s, %s, %s, %s)
           RETURNING request_id''',
        (requester_id, book_title, author, status, matched_book_id)
    )
    return rows[0][0]

def get_borrower_by_user(user_id):
    row = db.fetch_one(
        'SELECT borrower_id FROM borrowers WHERE user_id = %s',
        (user_id,)
    )
    return row[0] if row else None

def get_requests(status=None):
    if status:
        return db.fetch_all(
            'SELECT * FROM request_records WHERE request_status = %s ORDER BY request_date DESC',
            (status,)
        )
    return db.fetch_all('SELECT * FROM request_records ORDER BY request_date DESC')

def get_requests_with_details(status=None):
    base_query = '''
        SELECT r.request_id, r.requester_id, r.book_title, r.author,
               r.matched_book_id, r.request_status, r.request_date,
               r.reviewed_by, r.review_date, r.remarks,
               u.full_name, ro.role_name, b.department
        FROM request_records r
        JOIN borrowers b ON b.borrower_id = r.requester_id
        JOIN user_accounts u ON u.user_id = b.user_id
        JOIN roles ro ON ro.role_id = u.role_id
    '''
    if status:
        return db.fetch_all(base_query + ' WHERE r.request_status = %s ORDER BY r.request_date DESC', (status,))
    return db.fetch_all(base_query + ' ORDER BY r.request_date DESC', ())

def get_request_by_id(request_id):
    return db.fetch_one(
        'SELECT * FROM request_records WHERE request_id = %s',
        (request_id,)
    )


def update_request_status(request_id, status, reviewer_id=None, remarks=None):
    if reviewer_id:
        return db.execute(
            'UPDATE request_records SET request_status = %s, reviewed_by = %s, review_date = NOW(), remarks = %s WHERE request_id = %s',
            (status, reviewer_id, remarks, request_id)
        )
    return db.execute(
        'UPDATE request_records SET request_status = %s, remarks = %s WHERE request_id = %s',
        (status, remarks, request_id)
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
    return row[0] if row else None