import re
from difflib import SequenceMatcher
from app.database import db

ABBREVIATIONS = {
    'intro': 'introduction',
    'prog': 'programming',
    'comp': 'computer',
    'sci': 'science',
    'admin': 'administration',
}

def normalize_title(title):
    title = title.lower()
    title = re.sub(r'[^\w\s]', '', title)
    words = [ABBREVIATIONS.get(w, w) for w in title.split()]
    return ' '.join(words)

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

PER_PAGE = 50

def get_requests_with_details(status=None, search=None, page=1):
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
    conditions = []
    params = []

    if status:
        conditions.append('r.request_status = %s')
        params.append(status)

    if search:
        conditions.append('r.book_title ILIKE %s')
        params.append(f'%{search}%')

    if conditions:
        base_query += ' WHERE ' + ' AND '.join(conditions)

    base_query += ' ORDER BY r.request_date DESC LIMIT %s OFFSET %s'
    params.append(PER_PAGE)
    params.append((page - 1) * PER_PAGE)

    return db.fetch_all(base_query, tuple(params))


def count_requests(status=None, search=None):
    base_query = 'SELECT COUNT(*) FROM request_records r'
    conditions = []
    params = []

    if status:
        conditions.append('r.request_status = %s')
        params.append(status)

    if search:
        conditions.append('r.book_title ILIKE %s')
        params.append(f'%{search}%')

    if conditions:
        base_query += ' WHERE ' + ' AND '.join(conditions)

    row = db.fetch_one(base_query, tuple(params))
    return row[0] if row else 0

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

def get_requests_by_borrower(borrower_id):
    return db.fetch_all(
        'SELECT request_id, book_title, author, request_status, request_date, remarks FROM request_records WHERE requester_id = %s ORDER BY request_date DESC',
        (borrower_id,)
    )

def check_duplicate_request(requester_id, book_title):
    normalized = normalize_title(book_title)
    rows = db.fetch_all(
        'SELECT book_title FROM request_records WHERE requester_id = %s',
        (requester_id,)
    )

    for (title,) in rows:
        existing_normalized = normalize_title(title)
        if existing_normalized == normalized or SequenceMatcher(None, existing_normalized, normalized).ratio() >= 0.85:
            return True

    return False


def check_existing_in_collection(book_title):
    normalized = normalize_title(book_title)

    exact = db.fetch_one(
        'SELECT book_id FROM book_catalog WHERE LOWER(title) = LOWER(%s)',
        (book_title,)
    )
    if exact:
        return exact[0]

    first_word = normalized.split(' ')[0] if normalized else ''
    candidates = db.fetch_all(
        "SELECT book_id, title FROM book_catalog WHERE LOWER(title) LIKE LOWER(%s)",
        (first_word + '%',)
    )
    for book_id, title in candidates:
        if SequenceMatcher(None, normalize_title(title), normalized).ratio() >= 0.85:
            return book_id

    return None