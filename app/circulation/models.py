from datetime import date
from app.database import db


def borrow_book(book_id, accession_id, borrower_id, processed_by, borrow_type, due_date=None):
    return db.execute(
        '''INSERT INTO circulation_records
           (book_id, accession_id, borrower_id, processed_by, borrow_type, transaction_type,
            borrow_date, due_date, transaction_status)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)''',
        (book_id, accession_id, borrower_id, processed_by, borrow_type, 'borrow',
         date.today(), due_date, 'active')
    )


def return_book(circulation_id, fine_amount=0, damage_notes=None, lost_flag=False):
    return db.execute(
        '''UPDATE circulation_records
           SET transaction_status = %s, return_date = %s, fine_amount = %s,
               damage_notes = %s, lost_flag = %s
           WHERE circulation_id = %s''',
        ('returned', date.today(), fine_amount, damage_notes, lost_flag, circulation_id)
    )


def get_active_loans_by_borrower(borrower_id):
    return db.fetch_all(
        "SELECT * FROM circulation_records WHERE borrower_id = %s AND transaction_status IN ('active', 'overdue')",
        (borrower_id,)
    )


def get_active_loan_by_accession(accession_id):
    return db.fetch_one(
        "SELECT * FROM circulation_records WHERE accession_id = %s AND transaction_status IN ('active', 'overdue')",
        (accession_id,)
    )


def get_active_loan_by_book_and_borrower(book_id, borrower_id):
    # NOTE: application-level guard only. Concurrent POSTs can both pass this
    # check and INSERT different accessions of the same book (no partial unique
    # index on (book_id, borrower_id) WHERE active/overdue). Accepted for
    # capstone scope; a DB-level constraint would close the race.
    return db.fetch_one(
        "SELECT * FROM circulation_records WHERE book_id = %s AND borrower_id = %s AND transaction_status IN ('active', 'overdue')",
        (book_id, borrower_id)
    )


def get_active_loan_accession_ids_by_book(book_id):
    rows = db.fetch_all(
        "SELECT accession_id FROM circulation_records WHERE book_id = %s AND transaction_status IN ('active', 'overdue')",
        (book_id,)
    )
    return {row[0] for row in rows}


def get_active_loan_borrower_user_ids_by_book(book_id):
    rows = db.fetch_all(
        '''SELECT c.accession_id, u.user_id
           FROM circulation_records c
           JOIN borrowers br ON c.borrower_id = br.borrower_id
           JOIN user_accounts u ON br.user_id = u.user_id
           WHERE c.book_id = %s AND c.transaction_status IN ('active', 'overdue')''',
        (book_id,)
    )
    return {row[0]: row[1] for row in rows}


def get_available_accession_by_book(book_id):
    return db.fetch_one(
        '''SELECT a.* FROM accession_log a
           WHERE a.book_id = %s
             AND NOT EXISTS (
                 SELECT 1 FROM circulation_records c
                 WHERE c.accession_id = a.accession_id
                   AND c.transaction_status IN ('active', 'overdue')
             )
           ORDER BY a.accession_id
           LIMIT 1''',
        (book_id,)
    )


def count_active_loans(borrower_id):
    row = db.fetch_one(
        "SELECT COUNT(*) FROM circulation_records WHERE borrower_id = %s AND transaction_status IN ('active', 'overdue')",
        (borrower_id,)
    )
    return row[0] if row else 0


def calculate_fine(circulation_id, overdue_rate=10.0, grace_days=0):
    record = db.fetch_one(
        'SELECT due_date, return_date FROM circulation_records WHERE circulation_id = %s',
        (circulation_id,)
    )
    if not record:
        return 0
    due_date, return_date = record
    returned = return_date if return_date else date.today()
    overdue_days = (returned - due_date).days - (grace_days or 0)
    return max(0, overdue_days * overdue_rate)


def get_borrowing_frequency(book_id):
    row = db.fetch_one(
        'SELECT COUNT(*) FROM circulation_records WHERE book_id = %s',
        (book_id,)
    )
    return row[0] if row else 0


def get_borrowing_by_program(program):
    return db.fetch_all(
        '''SELECT COUNT(*) FROM circulation_records c
           JOIN borrowers b ON c.borrower_id = b.borrower_id
           WHERE b.department = %s''',
        (program,)
    )


def get_overdue_loans():
    return db.fetch_all(
        '''SELECT * FROM circulation_records
           WHERE transaction_status IN ('active', 'overdue') AND due_date < CURRENT_DATE'''
    )


def get_due_within_days(days=2):
    from datetime import timedelta
    target = date.today() + timedelta(days=days)
    return db.fetch_all(
        "SELECT * FROM circulation_records WHERE due_date = %s AND transaction_status = 'active'",
        (target,)
    )


def get_due_soon_detail(days=2):
    return db.fetch_all(
        '''SELECT c.circulation_id, c.due_date, u.full_name
           FROM circulation_records c
           JOIN borrowers br ON c.borrower_id = br.borrower_id
           JOIN user_accounts u ON br.user_id = u.user_id
           WHERE c.transaction_status = 'active'
             AND c.due_date BETWEEN CURRENT_DATE AND CURRENT_DATE + %s
           ORDER BY c.due_date''',
        (days,)
    )


def get_overdue_loans_detail():
    return db.fetch_all(
        '''SELECT c.circulation_id, c.due_date,
                  u.full_name, b.title, a.accession_number
           FROM circulation_records c
           JOIN borrowers br ON c.borrower_id = br.borrower_id
           JOIN user_accounts u ON br.user_id = u.user_id
           JOIN book_catalog b ON c.book_id = b.book_id
           JOIN accession_log a ON c.accession_id = a.accession_id
           WHERE c.transaction_status IN ('active', 'overdue') AND c.due_date < CURRENT_DATE
           ORDER BY c.due_date'''
    )


def get_circulation_stats():
    active = db.fetch_one(
        "SELECT COUNT(*) FROM circulation_records WHERE transaction_status IN ('active', 'overdue')"
    )
    overdue = db.fetch_one(
        "SELECT COUNT(*) FROM circulation_records WHERE transaction_status IN ('active', 'overdue') AND due_date < CURRENT_DATE"
    )
    due_soon = db.fetch_one(
        "SELECT COUNT(*) FROM circulation_records WHERE transaction_status = 'active' AND due_date BETWEEN CURRENT_DATE AND CURRENT_DATE + 2"
    )
    return {
        'active_loans': active[0] if active else 0,
        'overdue_items': overdue[0] if overdue else 0,
        'due_in_days': due_soon[0] if due_soon else 0,
    }


def get_active_loans():
    return db.fetch_all(
        '''SELECT c.circulation_id, c.borrow_date, c.due_date, c.borrow_type, c.transaction_status,
                  u.full_name, u.user_id, b.title, a.accession_number, br.borrower_id
           FROM circulation_records c
           JOIN borrowers br ON c.borrower_id = br.borrower_id
           JOIN user_accounts u ON br.user_id = u.user_id
           JOIN book_catalog b ON c.book_id = b.book_id
           JOIN accession_log a ON c.accession_id = a.accession_id
           WHERE c.transaction_status IN ('active', 'overdue')
           ORDER BY c.due_date'''
    )


def get_recent_transactions(limit=10):
    return db.fetch_all(
        '''SELECT c.transaction_type, c.borrow_date, c.return_date, c.due_date, c.transaction_status,
                  c.fine_amount, u.full_name, b.title, a.accession_number
           FROM circulation_records c
           JOIN borrowers br ON c.borrower_id = br.borrower_id
           JOIN user_accounts u ON br.user_id = u.user_id
           JOIN book_catalog b ON c.book_id = b.book_id
           JOIN accession_log a ON c.accession_id = a.accession_id
           ORDER BY COALESCE(c.return_date, c.borrow_date) DESC, c.circulation_id DESC
           LIMIT %s''',
        (limit,)
    )


def get_loans_by_borrower(borrower_id):
    return db.fetch_all(
        '''SELECT c.circulation_id, c.borrow_date, c.due_date, c.borrow_type, c.transaction_status,
                  b.title, a.accession_number
           FROM circulation_records c
           JOIN book_catalog b ON c.book_id = b.book_id
           JOIN accession_log a ON c.accession_id = a.accession_id
           WHERE c.borrower_id = %s AND c.transaction_status IN ('active', 'overdue')
           ORDER BY c.due_date''',
        (borrower_id,)
    )


def get_user_active_loans(user_id):
    return db.fetch_all(
        '''SELECT c.circulation_id, c.borrow_date, c.due_date, c.borrow_type, c.transaction_status,
                  b.title, b.author, a.accession_number
           FROM circulation_records c
           JOIN borrowers br ON c.borrower_id = br.borrower_id
           JOIN book_catalog b ON c.book_id = b.book_id
           JOIN accession_log a ON c.accession_id = a.accession_id
           WHERE br.user_id = %s AND c.transaction_status IN ('active', 'overdue')
           ORDER BY c.due_date''',
        (user_id,)
    )


def get_active_loan_by_id_and_user(circulation_id, user_id):
    return db.fetch_one(
        '''SELECT c.circulation_id, c.book_id, c.borrower_id, c.due_date, c.transaction_status, c.borrow_type
           FROM circulation_records c
           JOIN borrowers br ON c.borrower_id = br.borrower_id
           WHERE c.circulation_id = %s AND br.user_id = %s
             AND c.transaction_status IN ('active', 'overdue')''',
        (circulation_id, user_id)
    )


def get_user_loan_history(user_id):
    return db.fetch_all(
        '''SELECT c.circulation_id, c.borrow_date, c.due_date, c.return_date, c.borrow_type,
                  c.transaction_status, c.fine_amount, b.title, b.author, a.accession_number
           FROM circulation_records c
           JOIN borrowers br ON c.borrower_id = br.borrower_id
           JOIN book_catalog b ON c.book_id = b.book_id
           JOIN accession_log a ON c.accession_id = a.accession_id
           WHERE br.user_id = %s
           ORDER BY COALESCE(c.return_date, c.borrow_date) DESC, c.circulation_id DESC''',
        (user_id,)
    )


def get_notifications_by_borrower(borrower_id, limit=None):
    query = (
        '''SELECT notification_id, message, notif_type, related_reference, date_sent,
                  COALESCE(is_read, FALSE) AS is_read
           FROM notification_log
           WHERE recipient_id = %s
           ORDER BY date_sent DESC'''
    )
    params = [borrower_id]
    if limit:
        query += ' LIMIT %s'
        params.append(limit)
    return db.fetch_all(query, tuple(params))


def count_unread_notifications(borrower_id):
    row = db.fetch_one(
        '''SELECT COUNT(*) FROM notification_log
           WHERE recipient_id = %s AND COALESCE(is_read, FALSE) = FALSE''',
        (borrower_id,)
    )
    return row[0] if row else 0


def get_notification_by_id(notification_id, borrower_id):
    return db.fetch_one(
        '''SELECT notification_id, message, notif_type, related_reference, date_sent,
                  COALESCE(is_read, FALSE) AS is_read
           FROM notification_log
           WHERE notification_id = %s AND recipient_id = %s''',
        (notification_id, borrower_id)
    )


def mark_notification_read(notification_id, borrower_id):
    return db.execute(
        'UPDATE notification_log SET is_read = TRUE WHERE notification_id = %s AND recipient_id = %s',
        (notification_id, borrower_id)
    )


def mark_all_notifications_read(borrower_id):
    return db.execute(
        'UPDATE notification_log SET is_read = TRUE WHERE recipient_id = %s AND COALESCE(is_read, FALSE) = FALSE',
        (borrower_id,)
    )


def notification_exists(recipient_id, notif_type, related_reference):
    row = db.fetch_one(
        '''SELECT notification_id FROM notification_log
           WHERE recipient_id = %s AND notif_type = %s AND related_reference = %s
             AND DATE(date_sent) = CURRENT_DATE''',
        (recipient_id, notif_type, related_reference)
    )
    return bool(row)


def get_reservation_history_by_borrower(borrower_id):
    return db.fetch_all(
        '''SELECT r.reservation_id, r.queue_position, r.reservation_status, r.request_date, r.claim_deadline,
                  b.title, b.author
           FROM reservation_queue r
           JOIN book_catalog b ON r.book_id = b.book_id
           WHERE r.borrower_id = %s
           ORDER BY r.request_date DESC''',
        (borrower_id,)
    )


def get_fines_by_borrower(borrower_id):
    return db.fetch_all(
        '''SELECT c.circulation_id, c.borrow_date, c.due_date, c.return_date, c.fine_amount,
                  b.title, a.accession_number
           FROM circulation_records c
           JOIN book_catalog b ON c.book_id = b.book_id
           JOIN accession_log a ON c.accession_id = a.accession_id
           WHERE c.borrower_id = %s AND c.fine_amount > 0
           ORDER BY COALESCE(c.return_date, c.borrow_date) DESC''',
        (borrower_id,)
    )


def get_total_fines(borrower_id):
    row = db.fetch_one(
        'SELECT COALESCE(SUM(fine_amount), 0) FROM circulation_records WHERE borrower_id = %s',
        (borrower_id,)
    )
    return row[0] if row else 0


def get_borrower_by_user(user_id):
    return db.fetch_one('SELECT * FROM borrowers WHERE user_id = %s', (user_id,))


def get_borrower_by_id_number(id_number):
    return db.fetch_one('SELECT * FROM borrowers WHERE id_number = %s', (id_number,))


def get_borrower_details(borrower_id):
    return db.fetch_one(
        '''SELECT br.borrower_id, br.id_number, br.department, br.borrower_status,
                  u.full_name, u.user_id, r.role_name
           FROM borrowers br
           JOIN user_accounts u ON br.user_id = u.user_id
           JOIN roles r ON u.role_id = r.role_id
           WHERE br.borrower_id = %s''',
        (borrower_id,)
    )


def create_reservation(book_id, borrower_id, queue_position):
    return db.execute(
        '''INSERT INTO reservation_queue
           (book_id, borrower_id, queue_position, reservation_status, request_date)
           VALUES (%s, %s, %s, 'waiting', NOW())''',
        (book_id, borrower_id, queue_position)
    )


def get_next_queue_position(book_id):
    row = db.fetch_one(
        'SELECT COALESCE(MAX(queue_position), 0) + 1 FROM reservation_queue WHERE book_id = %s',
        (book_id,)
    )
    return row[0] if row else 1


def get_active_reservation_by_book_and_borrower(book_id, borrower_id):
    return db.fetch_one(
        "SELECT * FROM reservation_queue WHERE book_id = %s AND borrower_id = %s AND reservation_status IN ('waiting', 'allocated')",
        (book_id, borrower_id)
    )


def get_reservation_by_id(reservation_id):
    return db.fetch_one('SELECT * FROM reservation_queue WHERE reservation_id = %s', (reservation_id,))


def get_reservations_grouped():
    return db.fetch_all(
        '''SELECT r.book_id, b.title, b.author,
                  COUNT(*) AS total,
                  COUNT(*) FILTER (WHERE r.reservation_status = 'waiting') AS waiting,
                  COUNT(*) FILTER (WHERE r.reservation_status = 'allocated') AS allocated,
                  COUNT(*) FILTER (WHERE r.reservation_status = 'claimed') AS claimed,
                  COUNT(*) FILTER (WHERE r.reservation_status = 'expired') AS expired
           FROM reservation_queue r
           JOIN book_catalog b ON r.book_id = b.book_id
           GROUP BY r.book_id, b.title, b.author
           ORDER BY b.title'''
    )


def get_reservations_by_book(book_id):
    return db.fetch_all(
        '''SELECT r.reservation_id, r.queue_position, r.reservation_status, r.request_date, r.claim_deadline,
                  b.title, u.full_name, u.user_id, br.id_number
           FROM reservation_queue r
           JOIN book_catalog b ON r.book_id = b.book_id
           JOIN borrowers br ON r.borrower_id = br.borrower_id
           JOIN user_accounts u ON br.user_id = u.user_id
           WHERE r.book_id = %s
           ORDER BY r.queue_position''',
        (book_id,)
    )

def get_reservations_by_borrower(borrower_id):
    return db.fetch_all(
        '''SELECT r.reservation_id, r.queue_position, r.reservation_status, r.request_date, r.claim_deadline,
                  b.title, b.author
           FROM reservation_queue r
           JOIN book_catalog b ON r.book_id = b.book_id
           WHERE r.borrower_id = %s
           ORDER BY r.queue_position''',
        (borrower_id,)
    )


def allocate_reservation(reservation_id, claim_deadline):
    return db.execute(
        "UPDATE reservation_queue SET reservation_status = 'allocated', claim_deadline = %s WHERE reservation_id = %s",
        (claim_deadline, reservation_id)
    )


def claim_reservation(reservation_id):
    return db.execute(
        "UPDATE reservation_queue SET reservation_status = 'claimed' WHERE reservation_id = %s",
        (reservation_id,)
    )


def expire_reservation(reservation_id):
    return db.execute(
        "UPDATE reservation_queue SET reservation_status = 'expired' WHERE reservation_id = %s",
        (reservation_id,)
    )


def next_in_queue(book_id):
    return db.fetch_one(
        "SELECT * FROM reservation_queue WHERE book_id = %s AND reservation_status = 'waiting' ORDER BY queue_position ASC LIMIT 1",
        (book_id,)
    )


def create_notification(recipient_id, message, notif_type, related_reference=None):
    return db.execute(
        'INSERT INTO notification_log (recipient_id, message, notif_type, related_reference) VALUES (%s, %s, %s, %s)',
        (recipient_id, message, notif_type, related_reference)
    )
