from datetime import date, datetime
from app.database import db
from app.settings.models import library_today


# Due dates carry hours: every new loan is due at library closing time
# (5:00 PM) on its due date. Overdue and fine policy stay calendar-day
# based (date parts), so this changes display precision, not lending rules.
DUE_END_HOUR = 17
DUE_END_MINUTE = 0


def end_of_day(day, hour=DUE_END_HOUR, minute=DUE_END_MINUTE):
    """Datetime at the given hour on the given date (library closing by
    default; accepts date or datetime)."""
    if isinstance(day, datetime):
        day = day.date()
    return datetime(day.year, day.month, day.day, hour, minute)


def coerce_due_day(value):
    """Due value (date/datetime/ISO string) as a date, or None.

    Central coercion so TIMESTAMP dues, legacy DATE rows, and short mock
    tuples all compare safely. Never raises.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            pass
        try:
            return datetime.strptime(value[:10], '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return None
    if hasattr(value, 'timetuple'):
        try:
            return date(value.year, value.month, value.day)
        except Exception:
            return None
    return None


def format_due(value):
    """Human due display with hours: 'Aug 05, 2026 · 05:00 PM'.

    Legacy midnight rows (which never had hours) and plain dates render
    date-only; None renders as an em dash; garbage passes through as
    text instead of 500ing. Registered as the `duefmt` Jinja filter.
    """
    if value is None:
        return '—'
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            try:
                value = datetime.strptime(value[:10], '%Y-%m-%d')
            except (ValueError, TypeError):
                return value
    if isinstance(value, datetime):
        if value.hour == 0 and value.minute == 0 and value.second == 0:
            return value.strftime('%b %d, %Y')
        return value.strftime('%b %d, %Y · %I:%M %p')
    if isinstance(value, date):
        return value.strftime('%b %d, %Y')
    return str(value)


def borrow_book(book_id, accession_id, borrower_id, processed_by, borrow_type, due_date=None):
    return db.execute(
        '''INSERT INTO circulation_records
           (book_id, accession_id, borrower_id, processed_by, borrow_type, transaction_type,
            borrow_date, due_date, transaction_status)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)''',
        (book_id, accession_id, borrower_id, processed_by, borrow_type, 'borrow',
         library_today(), due_date, 'active')
    )


def return_book(circulation_id, fine_amount=0, damage_notes=None, lost_flag=False, updated_by=None):
    return db.execute(
        '''UPDATE circulation_records
           SET transaction_status = %s, return_date = %s, fine_amount = %s,
               damage_notes = %s, lost_flag = %s,
               updated_at = NOW(), updated_by = %s
           WHERE circulation_id = %s
             AND transaction_status IN ('active', 'overdue')''',
        ('returned', library_today(), fine_amount, damage_notes, lost_flag, updated_by, circulation_id)
    )


def is_accession_lost(accession_id):
    """True when a copy is marked lost via either channel.

    Lost can be recorded on the loan itself (circulation lost_flag, set
    when a missing copy is reported while on loan) or standalone on the
    copy (inventory_state 'lost', e.g. found missing from the shelf).
    Either one blocks borrowing. Single-row shape is preserved so
    existing callers and mocks keep working.
    """
    row = db.fetch_one(
        '''SELECT COALESCE((
              SELECT c.lost_flag FROM circulation_records c
              WHERE c.accession_id = %s
              ORDER BY c.circulation_id DESC LIMIT 1
          ), FALSE)
          OR COALESCE((
              SELECT ist.inventory_state FROM inventory_status ist
              WHERE ist.accession_id = %s
          ), '') = 'lost' ''',
        (accession_id, accession_id)
    )
    return bool(row and row[0])


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
    # Application-level guard plus DB-level partial unique indexes
    # (uq_active_loan_per_book_borrower, uq_active_loan_per_accession,
    # uq_active_reservation_per_book_borrower in schema.sql): a lost race
    # surfaces as a unique violation, which routes turn into a friendly
    # "refresh and try again" instead of a duplicate loan.
    return db.fetch_one(
        "SELECT * FROM circulation_records WHERE book_id = %s AND borrower_id = %s AND transaction_status IN ('active', 'overdue')",
        (book_id, borrower_id)
    )


def get_active_loan_accession_ids_by_book(book_id):
    rows = db.fetch_all(
        "SELECT accession_id FROM circulation_records WHERE book_id = %s AND transaction_status IN ('active', 'overdue')",
        (book_id,)
    ) or []
    return {row[0] for row in rows}


def get_active_loan_borrower_user_ids_by_book(book_id):
    rows = db.fetch_all(
        '''SELECT c.accession_id, u.user_id
           FROM circulation_records c
           JOIN borrowers br ON c.borrower_id = br.borrower_id
           JOIN user_accounts u ON br.user_id = u.user_id
           WHERE c.book_id = %s AND c.transaction_status IN ('active', 'overdue')''',
        (book_id,)
    ) or []
    return {row[0]: row[1] for row in rows}


def count_allocated_reservations(book_id):
    row = db.fetch_one(
        "SELECT COUNT(*) FROM reservation_queue WHERE book_id = %s AND reservation_status = 'allocated'",
        (book_id,)
    )
    return row[0] if row else 0


def has_active_overnight_loan(book_id):
    row = db.fetch_one(
        """SELECT 1 FROM circulation_records
           WHERE book_id = %s AND borrow_type = 'overnight'
             AND transaction_status IN ('active', 'overdue')
           LIMIT 1""",
        (book_id,)
    )
    return row is not None


def is_book_blocked_for_daily(book_id):
    """A book borrowed as Overnight that is already allocated is
    Not Available for Daily Circulation.

    Returns True when the book has at least one active/overdue
    overnight loan AND at least one allocated reservation.
    """
    try:
        row = db.fetch_one(
            """SELECT 1 WHERE
                   EXISTS (SELECT 1 FROM circulation_records
                           WHERE book_id = %s AND borrow_type = 'overnight'
                             AND transaction_status IN ('active', 'overdue'))
               AND EXISTS (SELECT 1 FROM reservation_queue
                           WHERE book_id = %s AND reservation_status = 'allocated')""",
            (book_id, book_id)
        )
    except Exception:
        return False
    # Real query returns (1,) when blocked, None otherwise. Any other
    # shape is a stale mock (e.g. a book/accession tuple reused as
    # fetch_one return_value) — treat it as not blocked.
    return row is not None and len(row) == 1 and row[0] == 1


def get_available_accession_by_book(book_id):
    return db.fetch_one(
        '''SELECT a.* FROM accession_log a
           WHERE a.book_id = %s
             AND NOT EXISTS (
                 SELECT 1 FROM circulation_records c
                 WHERE c.accession_id = a.accession_id
                   AND c.transaction_status IN ('active', 'overdue')
             )
             AND NOT (
                   EXISTS (SELECT 1 FROM circulation_records c2
                           WHERE c2.book_id = a.book_id AND c2.borrow_type = 'overnight'
                             AND c2.transaction_status IN ('active', 'overdue'))
               AND EXISTS (SELECT 1 FROM reservation_queue r
                           WHERE r.book_id = a.book_id AND r.reservation_status = 'allocated')
             )
              AND COALESCE((
                    SELECT c3.lost_flag FROM circulation_records c3
                    WHERE c3.accession_id = a.accession_id
                    ORDER BY c3.circulation_id DESC LIMIT 1
                ), FALSE) = FALSE
              AND COALESCE((
                    SELECT ist.inventory_state FROM inventory_status ist
                    WHERE ist.accession_id = a.accession_id
                ), '') != 'lost'
            ORDER BY a.accession_id
            LIMIT 1''',
        (book_id,)
    )


def count_available_accessions(book_id):
    """Copies of a book that are free to lend: no active/overdue loan and
    not marked lost. Mirrors the availability WHERE logic of
    get_available_accession_by_book (minus the daily-block clause, which
    is a lending policy, not physical availability)."""
    row = db.fetch_one(
        '''SELECT COUNT(*) FROM accession_log a
           WHERE a.book_id = %s
             AND NOT EXISTS (
                 SELECT 1 FROM circulation_records c
                 WHERE c.accession_id = a.accession_id
                   AND c.transaction_status IN ('active', 'overdue')
             )
              AND COALESCE((
                    SELECT c3.lost_flag FROM circulation_records c3
                    WHERE c3.accession_id = a.accession_id
                    ORDER BY c3.circulation_id DESC LIMIT 1
                ), FALSE) = FALSE
              AND COALESCE((
                    SELECT ist.inventory_state FROM inventory_status ist
                    WHERE ist.accession_id = a.accession_id
                ), '') != 'lost' ''',
        (book_id,)
    )
    return row[0] if row else 0


def count_active_loans(borrower_id):
    row = db.fetch_one(
        "SELECT COUNT(*) FROM circulation_records WHERE borrower_id = %s AND transaction_status IN ('active', 'overdue')",
        (borrower_id,)
    )
    return row[0] if row else 0


def calculate_fine(circulation_id, overdue_rate=5.0, grace_days=0):
    """Overdue fine for a loan. Only overnight borrows accrue fines
    (₱5/day by default); daily/in-library loans never do."""
    record = db.fetch_one(
        'SELECT due_date, return_date, borrow_type FROM circulation_records WHERE circulation_id = %s',
        (circulation_id,)
    )
    if not record:
        return 0
    due_date, return_date, borrow_type = record
    if borrow_type != 'overnight':
        return 0
    if not due_date:
        return 0
    # Calendar-day policy: compare date parts so TIMESTAMP dues (end of
    # day) and legacy DATE rows fine identically. psycopg2 may return
    # date or datetime; be defensive against ISO strings too.
    due_day = coerce_due_day(due_date)
    if due_day is None:
        return 0
    returned_day = coerce_due_day(return_date) if return_date else library_today()
    if returned_day is None:
        return 0
    try:
        overdue_days = (returned_day - due_day).days - (grace_days or 0)
    except TypeError:
        return 0
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
              WHERE transaction_status IN ('active', 'overdue') AND due_date::date < CURRENT_DATE'''
    )


def get_due_within_days(days=2):
    from datetime import timedelta
    target = library_today() + timedelta(days=days)
    return db.fetch_all(
        "SELECT * FROM circulation_records WHERE due_date::date = (%s)::date AND transaction_status = 'active'",
        (target,)
    )


def get_due_soon_detail(days=2):
    return db.fetch_all(
        '''SELECT c.circulation_id, c.due_date, u.full_name
           FROM circulation_records c
           JOIN borrowers br ON c.borrower_id = br.borrower_id
           JOIN user_accounts u ON br.user_id = u.user_id
           WHERE c.transaction_status = 'active'
              AND c.due_date::date BETWEEN CURRENT_DATE AND CURRENT_DATE + %s
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
            WHERE c.transaction_status IN ('active', 'overdue') AND c.due_date::date < CURRENT_DATE
           ORDER BY c.due_date'''
    )


def get_circulation_stats():
    active = db.fetch_one(
        "SELECT COUNT(*) FROM circulation_records WHERE transaction_status IN ('active', 'overdue')"
    )
    overdue = db.fetch_one(
        "SELECT COUNT(*) FROM circulation_records WHERE transaction_status IN ('active', 'overdue') AND due_date::date < CURRENT_DATE"
    )
    due_soon = db.fetch_one(
        "SELECT COUNT(*) FROM circulation_records WHERE transaction_status = 'active' AND due_date::date BETWEEN CURRENT_DATE AND CURRENT_DATE + 2"
    )
    return {
        'active_loans': active[0] if active else 0,
        'overdue_items': overdue[0] if overdue else 0,
        'due_in_days': due_soon[0] if due_soon else 0,
    }


def get_active_loans():
    return db.fetch_all(
        '''SELECT c.circulation_id, c.borrow_date, c.due_date, c.borrow_type, c.transaction_status,
                  u.full_name, u.user_id, b.title, a.accession_number, br.borrower_id,
                  br.id_number, r.role_name
           FROM circulation_records c
           JOIN borrowers br ON c.borrower_id = br.borrower_id
           JOIN user_accounts u ON br.user_id = u.user_id
           JOIN roles r ON u.role_id = r.role_id
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


def mark_notification_read(notification_id, borrower_id, updated_by=None):
    return db.execute(
        'UPDATE notification_log SET is_read = TRUE, updated_at = NOW(), updated_by = %s WHERE notification_id = %s AND recipient_id = %s',
        (updated_by, notification_id, borrower_id)
    )


def mark_all_notifications_read(borrower_id, updated_by=None):
    return db.execute(
        'UPDATE notification_log SET is_read = TRUE, updated_at = NOW(), updated_by = %s WHERE recipient_id = %s AND COALESCE(is_read, FALSE) = FALSE',
        (updated_by, borrower_id)
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
    # Active-only: finished (claimed/expired) reservations are auto-removed
    # from user-facing history. Staff use get_full_reservation_history_by_borrower.
    return db.fetch_all(
        '''SELECT r.reservation_id, r.queue_position, r.reservation_status, r.request_date, r.claim_deadline,
                  b.title, b.author
           FROM reservation_queue r
           JOIN book_catalog b ON r.book_id = b.book_id
           WHERE r.borrower_id = %s AND r.reservation_status IN ('waiting', 'allocated')
           ORDER BY r.request_date DESC''',
        (borrower_id,)
    )


def get_full_reservation_history_by_borrower(borrower_id):
    return db.fetch_all(
        '''SELECT r.reservation_id, r.queue_position, r.reservation_status, r.request_date, r.claim_deadline,
                  b.title, b.author
           FROM reservation_queue r
           JOIN book_catalog b ON r.book_id = b.book_id
           WHERE r.borrower_id = %s
           ORDER BY r.request_date DESC''',
        (borrower_id,)
    )


def expire_overdue_reservations():
    return db.execute(
        """UPDATE reservation_queue SET reservation_status = 'expired', updated_at = NOW()
           WHERE reservation_status = 'allocated'
             AND claim_deadline IS NOT NULL
             AND claim_deadline < NOW()"""
    )


def get_borrowers_for_history(search=None, limit=100):
    base_query = (
        '''SELECT u.user_id, u.full_name, u.email, r.role_name,
                  b.borrower_id, b.id_number, b.department
           FROM user_accounts u
           JOIN roles r ON u.role_id = r.role_id
           JOIN borrowers b ON b.user_id = u.user_id'''
    )
    params = []
    if search:
        base_query += ' WHERE u.full_name ILIKE %s OR u.email ILIKE %s OR b.id_number ILIKE %s'
        like = f'%{search}%'
        params.extend([like, like, like])
    base_query += ' ORDER BY u.full_name ASC LIMIT %s'
    params.append(limit)
    return db.fetch_all(base_query, tuple(params))


def get_fines_by_borrower(borrower_id):
    """Unpaid fines only (fine_paid rows stay in history, not in totals)."""
    return db.fetch_all(
        '''SELECT c.circulation_id, c.borrow_date, c.due_date, c.return_date, c.fine_amount,
                  b.title, a.accession_number
           FROM circulation_records c
           JOIN book_catalog b ON c.book_id = b.book_id
           JOIN accession_log a ON c.accession_id = a.accession_id
           WHERE c.borrower_id = %s AND c.fine_amount > 0 AND c.fine_paid = FALSE
           ORDER BY COALESCE(c.return_date, c.borrow_date) DESC''',
        (borrower_id,)
    )


def get_total_fines(borrower_id):
    row = db.fetch_one(
        'SELECT COALESCE(SUM(fine_amount), 0) FROM circulation_records WHERE borrower_id = %s AND fine_paid = FALSE',
        (borrower_id,)
    )
    return row[0] if row else 0


def get_fine_record(circulation_id):
    """(circulation_id, borrower_id, fine_amount, fine_paid) or None."""
    return db.fetch_one(
        '''SELECT circulation_id, borrower_id, fine_amount, fine_paid
           FROM circulation_records WHERE circulation_id = %s''',
        (circulation_id,)
    )


def mark_fine_paid(circulation_id, updated_by=None):
    db.execute(
        'UPDATE circulation_records SET fine_paid = TRUE, updated_at = NOW(), updated_by = %s WHERE circulation_id = %s',
        (updated_by, circulation_id)
    )


def get_borrower_by_user(user_id):
    # Explicit column order (never SELECT *): older databases have
    # phone_number physically last (added by ALTER TABLE), which would
    # shift borrower_status and break every positional reader.
    return db.fetch_one(
        'SELECT borrower_id, user_id, id_number, department, phone_number,'
        ' borrower_status, updated_at, updated_by'
        ' FROM borrowers WHERE user_id = %s', (user_id,))


def get_borrower_by_id_number(id_number):
    return db.fetch_one(
        'SELECT borrower_id, user_id, id_number, department, phone_number,'
        ' borrower_status, updated_at, updated_by'
        ' FROM borrowers WHERE id_number = %s', (id_number,))


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
    # Active-only: finished (claimed/expired) reservations are auto-removed
    # from user-facing views. Staff use get_full_reservation_history_by_borrower.
    return db.fetch_all(
        '''SELECT r.reservation_id, r.queue_position, r.reservation_status, r.request_date, r.claim_deadline,
                  b.title, b.author
           FROM reservation_queue r
           JOIN book_catalog b ON r.book_id = b.book_id
           WHERE r.borrower_id = %s AND r.reservation_status IN ('waiting', 'allocated')
           ORDER BY r.queue_position''',
        (borrower_id,)
    )


def allocate_reservation(reservation_id, claim_deadline, updated_by=None):
    return db.execute(
        "UPDATE reservation_queue SET reservation_status = 'allocated', claim_deadline = %s, updated_at = NOW(), updated_by = %s WHERE reservation_id = %s",
        (claim_deadline, updated_by, reservation_id)
    )


def claim_reservation(reservation_id, updated_by=None):
    return db.execute(
        "UPDATE reservation_queue SET reservation_status = 'claimed', updated_at = NOW(), updated_by = %s WHERE reservation_id = %s",
        (updated_by, reservation_id)
    )


def expire_reservation(reservation_id, updated_by=None):
    return db.execute(
        "UPDATE reservation_queue SET reservation_status = 'expired', updated_at = NOW(), updated_by = %s WHERE reservation_id = %s",
        (updated_by, reservation_id)
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
