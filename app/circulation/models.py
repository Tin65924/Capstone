from datetime import date, datetime
from app.database import db
from app.settings.models import library_today


# Due dates carry hours: every new loan is due at library closing time
# (5:00 PM) on its due date. Overdue and fine policy stay calendar-day
# based (date parts), so this changes display precision, not lending rules.
DUE_END_HOUR = 17
DUE_END_MINUTE = 0


def end_of_day(day, hour=DUE_END_HOUR, minute=DUE_END_MINUTE):
    """Build a datetime at library closing time on the given day.

    Every new loan is due at closing (5:00 PM default) on its due date.
    Accepts a date or datetime (datetimes are reduced to their date
    first). Overdue and fine policy stay calendar-day based, so this
    only changes display precision, not lending rules.

    Args:
        day: date or datetime whose day the deadline falls on.
        hour: Hour of day for the deadline (default 17).
        minute: Minute of hour for the deadline (default 0).

    Returns:
        Datetime at the given hour/minute on that day.
    """
    if isinstance(day, datetime):
        day = day.date()
    return datetime(day.year, day.month, day.day, hour, minute)


def coerce_due_day(value):
    """Coerce a due value (date/datetime/ISO string) to a date, or None.

    Central coercion so TIMESTAMP dues, legacy DATE rows, and short mock
    tuples all compare safely. Never raises — garbage returns None.

    Args:
        value: date, datetime, ISO string, or duck-typed date-like.

    Returns:
        A date object, or None when the value is empty/unparseable.
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
    """Format a due value for human display with hours when meaningful.

    Renders 'Aug 05, 2026 · 05:00 PM' for datetimes with hours, date-only
    for legacy midnight rows and plain dates, an em dash for None, and
    passes garbage through as text instead of 500ing. Registered as the
    `duefmt` Jinja filter.

    Args:
        value: date, datetime, ISO string, or None.

    Returns:
        Human display string for the due moment.
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
    """Record a new loan of one physical copy to a borrower.

    Inserts into circulation_records with transaction_type='borrow',
    borrow_date=today, the given due date, and status 'active'. The
    route pre-selects a free accession and enforces limits, duplicate
    guards, and the daily-block policy before calling.

    Args:
        book_id: Title FK for the loan.
        accession_id: Exact copy FK being lent.
        borrower_id: Borrowing member's borrower FK.
        processed_by: Staff user_id who processed the desk loan.
        borrow_type: 'daily' (in-library) or 'overnight'.
        due_date: Due datetime (closing time on due day), or None.

    Returns:
        Rowcount from the INSERT.
    """
    return db.execute(
        '''INSERT INTO circulation_records
           (book_id, accession_id, borrower_id, processed_by, borrow_type, transaction_type,
            borrow_date, due_date, transaction_status)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)''',
        (book_id, accession_id, borrower_id, processed_by, borrow_type, 'borrow',
         library_today(), due_date, 'active')
    )


def return_book(circulation_id, fine_amount=0, damage_notes=None, lost_flag=False, updated_by=None):
    """Close an active/overdue loan as returned with fine and condition.

    Updates the loan to transaction_status='returned' with return_date
    today plus the assessed fine, optional damage notes, and lost flag
    (when a missing copy is reported while on loan). Only rows still
    'active'/'overdue' are touched, so double returns affect zero rows.

    Args:
        circulation_id: Loan primary key to close.
        fine_amount: Computed overdue fine to store.
        damage_notes: Condition notes, or None.
        lost_flag: True when the copy is being reported lost on return.
        updated_by: Acting staff user_id for the audit stamp.

    Returns:
        Rowcount from the UPDATE (0 when already returned).
    """
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
    """List a borrower's currently out loans (active + overdue).

    Used for borrow-limit enforcement and the desk "already has this"
    duplicate guard before issuing another copy.

    Args:
        borrower_id: Member's borrower FK.

    Returns:
        List of full circulation_records row tuples still out.
    """
    return db.fetch_all(
        "SELECT * FROM circulation_records WHERE borrower_id = %s AND transaction_status IN ('active', 'overdue')",
        (borrower_id,)
    )


def get_active_loan_by_accession(accession_id):
    """Fetch the live loan holding one copy, if any.

    Returns the single circulation row with status active/overdue for
    the accession, used to block double-lending a copy and to resolve
    which loan a return scan closes.

    Args:
        accession_id: Copy primary key to check.

    Returns:
        Full circulation_records row tuple, or None when the copy is
        on the shelf.
    """
    return db.fetch_one(
        "SELECT * FROM circulation_records WHERE accession_id = %s AND transaction_status IN ('active', 'overdue')",
        (accession_id,)
    )


def get_active_loan_by_book_and_borrower(book_id, borrower_id):
    """Fetch a borrower's live loan for one title, if any.

    Application-level guard plus DB-level partial unique indexes
    (uq_active_loan_per_book_borrower, uq_active_loan_per_accession,
    uq_active_reservation_per_book_borrower in schema.sql): a lost race
    surfaces as a unique violation, which routes turn into a friendly
    "refresh and try again" instead of a duplicate loan.

    Args:
        book_id: Title FK.
        borrower_id: Member FK.

    Returns:
        Full circulation_records row tuple, or None when the member
        holds no live copy of the title.
    """
    return db.fetch_one(
        "SELECT * FROM circulation_records WHERE book_id = %s AND borrower_id = %s AND transaction_status IN ('active', 'overdue')",
        (book_id, borrower_id)
    )


def get_active_loan_accession_ids_by_book(book_id):
    """Return the set of copy ids of a title that are currently lent out.

    Used to compute availability and to exclude on-loan copies from the
    lendable picker without fetching full loan rows.

    Args:
        book_id: Title FK.

    Returns:
        Set of accession_id integers with active/overdue loans.
    """
    rows = db.fetch_all(
        "SELECT accession_id FROM circulation_records WHERE book_id = %s AND transaction_status IN ('active', 'overdue')",
        (book_id,)
    ) or []
    return {row[0] for row in rows}


def get_active_loan_borrower_user_ids_by_book(book_id):
    """Map each lent-out copy of a title to its holder's user_id.

    Joins live loans through borrowers to user_accounts so desk views
    can name who holds each copy without extra queries.

    Args:
        book_id: Title FK.

    Returns:
        Dict {accession_id: user_id} for live loans of the title.
    """
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
    """Count allocated (ready-to-claim) reservations for a title.

    Feeds the daily-block check and desk availability messaging: when an
    overnight loan plus an allocation coexist, the title is not
    available for daily circulation.

    Args:
        book_id: Title FK.

    Returns:
        Integer count of 'allocated' reservations.
    """
    row = db.fetch_one(
        "SELECT COUNT(*) FROM reservation_queue WHERE book_id = %s AND reservation_status = 'allocated'",
        (book_id,)
    )
    return row[0] if row else 0


def has_active_overnight_loan(book_id):
    """Check whether a title has any live overnight loan.

    One half of the daily-block condition; combined with an allocated
    reservation it makes the title unavailable for daily borrowing.

    Args:
        book_id: Title FK.

    Returns:
        True when at least one active/overdue overnight loan exists.
    """
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
    """Pick the first lendable copy of a title for a new loan.

    Selects the lowest accession_id with no active/overdue loan, not
    flagged lost on either channel, and not caught by the daily-block
    (overnight-out plus allocated reservation). Returns one full
    accession_log row for borrow_book to lend.

    Args:
        book_id: Title FK.

    Returns:
        Full accession_log row tuple, or None when no copy is lendable.
    """
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
    """Count a borrower's currently out loans for limit enforcement.

    Counts active + overdue rows; routes compare this against the
    per-role borrow cap before issuing another copy.

    Args:
        borrower_id: Member's borrower FK.

    Returns:
        Integer live-loan count.
    """
    row = db.fetch_one(
        "SELECT COUNT(*) FROM circulation_records WHERE borrower_id = %s AND transaction_status IN ('active', 'overdue')",
        (borrower_id,)
    )
    return row[0] if row else 0


def calculate_fine(circulation_id, overdue_rate=5.0, grace_days=0):
    """Compute the overdue fine owed for one loan.

    Only overnight borrows accrue fines (₱5/day by default);
    daily/in-library loans never do. Compares calendar date parts (via
    coerce_due_day) so TIMESTAMP dues at end-of-day and legacy DATE rows
    fine identically. Uses return_date when set, otherwise today. Never
    raises on bad data — returns 0.

    Args:
        circulation_id: Loan primary key to assess.
        overdue_rate: Pesos per overdue day.
        grace_days: Free days subtracted from the overdue count.

    Returns:
        Fine amount (float/int), 0 when not overnight or not overdue.
    """
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
    """Count all-time loans for one title for popularity displays.

    Simple COUNT(*) over circulation_records used by detail widgets and
    analytics fallbacks.

    Args:
        book_id: Title FK.

    Returns:
        Integer total loan count.
    """
    row = db.fetch_one(
        'SELECT COUNT(*) FROM circulation_records WHERE book_id = %s',
        (book_id,)
    )
    return row[0] if row else 0


def get_borrowing_by_program(program):
    """Count loans by members of one program/department name.

    Joins circulation to borrowers and filters on the department
    string; feeds per-program borrowing breakdowns.

    Args:
        program: Exact department/program name.

    Returns:
        List of 1-tuples (count,) (single aggregate row).
    """
    return db.fetch_all(
        '''SELECT COUNT(*) FROM circulation_records c
           JOIN borrowers b ON c.borrower_id = b.borrower_id
           WHERE b.department = %s''',
        (program,)
    )


def get_overdue_loans():
    """List every loan past its due date still marked out.

    Selects active/overdue rows whose due_date::date is before today;
    the desk overdue tab and reminder jobs consume this.

    Returns:
        List of full circulation_records row tuples overdue.
    """
    return db.fetch_all(
        '''SELECT * FROM circulation_records
              WHERE transaction_status IN ('active', 'overdue') AND due_date::date < CURRENT_DATE'''
    )


def get_due_within_days(days=2):
    """List active loans due exactly on the target day for reminders.

    Computes target = library_today() + days and selects active rows
    with that due date; used to send due-soon notifications.

    Args:
        days: Days ahead to look (default 2).

    Returns:
        List of full circulation_records row tuples due that day.
    """
    from datetime import timedelta
    target = library_today() + timedelta(days=days)
    return db.fetch_all(
        "SELECT * FROM circulation_records WHERE due_date::date = (%s)::date AND transaction_status = 'active'",
        (target,)
    )


def get_due_soon_detail(days=2):
    """List active loans due in the next N days with borrower names.

    Joins to borrowers and user_accounts to produce (circulation_id,
    due_date, full_name) rows ordered by due date for the desk due-soon
    panel and reminder messages.

    Args:
        days: Lookahead window in days.

    Returns:
        List of (circulation_id, due_date, full_name) tuples.
    """
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
    """List overdue loans enriched with borrower, title, and barcode.

    Returns (circulation_id, due_date, full_name, title,
    accession_number) ordered by due date for the desk overdue table
    and overdue notice content.

    Returns:
        List of 5-tuple detail rows for overdue loans.
    """
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
    """Compute desk headline counts: out, overdue, and due-soon totals.

    Runs three bounded COUNT(*) queries (active/overdue, overdue by
    date, active due within 2 days) for the circulation dashboard
    cards.

    Returns:
        Dict with active_loans, overdue_items, and due_in_days counts.
    """
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
    """List every live loan with borrower, title, and copy details.

    Joins circulation through borrowers, users, roles, catalog, and
    accessions to produce the desk's main out-loans table ordered by
    due date.

    Returns:
        List of (circulation_id, borrow_date, due_date, borrow_type,
        transaction_status, full_name, user_id, title,
        accession_number, borrower_id, id_number, role_name) tuples.
    """
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
    """List recent borrow/return activity newest-first for the desk feed.

    Joins to borrower, title, and accession to show who moved what,
    ordered by return-or-borrow date then id.

    Args:
        limit: Maximum transactions to return.

    Returns:
        List of (transaction_type, borrow_date, return_date, due_date,
        transaction_status, fine_amount, full_name, title,
        accession_number) tuples.
    """
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
    """List one member's live loans with title and barcode by due date.

    Desk-facing per-borrower view returning (circulation_id,
    borrow_date, due_date, borrow_type, transaction_status, title,
    accession_number) for active/overdue rows only.

    Args:
        borrower_id: Member's borrower FK.

    Returns:
        List of 7-tuple loan rows ordered by due date.
    """
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
    """List the logged-in user's live loans for their borrowing page.

    Resolves user_id through borrowers to live circulation rows with
    title, author, and barcode, ordered by due date.

    Args:
        user_id: Owner's user_accounts primary key.

    Returns:
        List of (circulation_id, borrow_date, due_date, borrow_type,
        transaction_status, title, author, accession_number) tuples.
    """
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
    """Fetch one live loan owned by a user for self-service actions.

    Verifies the loan id belongs to the user's borrower row and is
    still active/overdue, preventing users from returning each other's
    loans. Returns the narrow row the return route needs.

    Args:
        circulation_id: Loan primary key.
        user_id: Requesting user's user_accounts id.

    Returns:
        Tuple (circulation_id, book_id, borrower_id, due_date,
        transaction_status, borrow_type) or None.
    """
    return db.fetch_one(
        '''SELECT c.circulation_id, c.book_id, c.borrower_id, c.due_date, c.transaction_status, c.borrow_type
           FROM circulation_records c
           JOIN borrowers br ON c.borrower_id = br.borrower_id
           WHERE c.circulation_id = %s AND br.user_id = %s
             AND c.transaction_status IN ('active', 'overdue')''',
        (circulation_id, user_id)
    )


def get_user_loan_history(user_id):
    """List a user's full borrowing history newest-first.

    Includes returned loans (unlike the active-only views) with title,
    author, barcode, fine, and status for the user history page,
    ordered by return-or-borrow date.

    Args:
        user_id: Owner's user_accounts primary key.

    Returns:
        List of (circulation_id, borrow_date, due_date, return_date,
        borrow_type, transaction_status, fine_amount, title, author,
        accession_number) tuples.
    """
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
    """List a member's notifications newest-first with read flags.

    Selects (notification_id, message, notif_type, related_reference,
    date_sent, is_read) for the recipient, coalescing NULL is_read to
    FALSE for legacy rows. An optional LIMIT powers the navbar preview.

    Args:
        borrower_id: Notification recipient's borrower FK.
        limit: Optional maximum rows to return.

    Returns:
        List of 6-tuple notification rows.
    """
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
    """Count a member's unread notifications for the badge counter.

    Counts rows where is_read is FALSE/NULL for the recipient.

    Args:
        borrower_id: Notification recipient's borrower FK.

    Returns:
        Integer unread count.
    """
    row = db.fetch_one(
        '''SELECT COUNT(*) FROM notification_log
           WHERE recipient_id = %s AND COALESCE(is_read, FALSE) = FALSE''',
        (borrower_id,)
    )
    return row[0] if row else 0


def get_notification_by_id(notification_id, borrower_id):
    """Fetch one notification owned by a borrower for the read action.

    Scoping by both notification_id and recipient_id prevents users
    from reading each other's notifications.

    Args:
        notification_id: Notification primary key.
        borrower_id: Expected recipient's borrower FK.

    Returns:
        6-tuple notification row, or None if not owned/found.
    """
    return db.fetch_one(
        '''SELECT notification_id, message, notif_type, related_reference, date_sent,
                  COALESCE(is_read, FALSE) AS is_read
           FROM notification_log
           WHERE notification_id = %s AND recipient_id = %s''',
        (notification_id, borrower_id)
    )


def mark_notification_read(notification_id, borrower_id, updated_by=None):
    """Mark one notification as read for its owner.

    Sets is_read=TRUE plus audit stamps, scoped to the recipient so one
    user can never mark another's notification.

    Args:
        notification_id: Notification primary key.
        borrower_id: Expected recipient's borrower FK.
        updated_by: Acting user_id for the audit stamp.

    Returns:
        Rowcount from the UPDATE.
    """
    return db.execute(
        'UPDATE notification_log SET is_read = TRUE, updated_at = NOW(), updated_by = %s WHERE notification_id = %s AND recipient_id = %s',
        (updated_by, notification_id, borrower_id)
    )


def mark_all_notifications_read(borrower_id, updated_by=None):
    """Mark every unread notification of a borrower as read.

    Bulk-sets is_read=TRUE where it is still FALSE/NULL for the
    recipient, powering the "mark all read" button.

    Args:
        borrower_id: Recipient's borrower FK.
        updated_by: Acting user_id for the audit stamp.

    Returns:
        Rowcount (number of notifications marked).
    """
    return db.execute(
        'UPDATE notification_log SET is_read = TRUE, updated_at = NOW(), updated_by = %s WHERE recipient_id = %s AND COALESCE(is_read, FALSE) = FALSE',
        (updated_by, borrower_id)
    )


def notification_exists(recipient_id, notif_type, related_reference):
    """Check whether the same notification was already sent today.

    Guards reminder jobs against spamming: matches on recipient, type,
    and reference with date_sent = today.

    Args:
        recipient_id: Borrower FK who would receive it.
        notif_type: Notification type string.
        related_reference: Related loan/reservation id string.

    Returns:
        True when today's duplicate already exists.
    """
    row = db.fetch_one(
        '''SELECT notification_id FROM notification_log
           WHERE recipient_id = %s AND notif_type = %s AND related_reference = %s
             AND DATE(date_sent) = CURRENT_DATE''',
        (recipient_id, notif_type, related_reference)
    )
    return bool(row)


def get_reservation_history_by_borrower(borrower_id):
    """List a member's live reservations for user-facing history.

    Active-only: finished (claimed/expired) reservations are hidden
    here (staff use get_full_reservation_history_by_borrower). Returns
    waiting/allocated rows with title/author newest-first.

    Args:
        borrower_id: Member's borrower FK.

    Returns:
        List of (reservation_id, queue_position, reservation_status,
        request_date, claim_deadline, title, author) tuples.
    """
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
    """List every reservation of a member including finished ones.

    Staff/audit view returning all statuses (waiting, allocated,
    claimed, expired) with title/author newest-first.

    Args:
        borrower_id: Member's borrower FK.

    Returns:
        List of (reservation_id, queue_position, reservation_status,
        request_date, claim_deadline, title, author) tuples.
    """
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
    """Expire allocated reservations past their claim deadline.

    Bulk-updates 'allocated' rows with claim_deadline < NOW() to
    'expired' so the copy frees for the next person in queue. Run by
    maintenance/before-listing logic.

    Returns:
        Rowcount (number of reservations expired).
    """
    return db.execute(
        """UPDATE reservation_queue SET reservation_status = 'expired', updated_at = NOW()
           WHERE reservation_status = 'allocated'
             AND claim_deadline IS NOT NULL
             AND claim_deadline < NOW()"""
    )


def get_borrowers_for_history(search=None, limit=100):
    """Search members for the staff history-lookup picker.

    Joins users, roles, and borrowers to show (user_id, full_name,
    email, role_name, borrower_id, id_number, department) ordered by
    name. Optional ILIKE filters name/email/ID; always capped by limit
    to keep the picker fast.

    Args:
        search: Optional substring matched against name/email/ID.
        limit: Maximum borrowers to return.

    Returns:
        List of 7-tuple borrower rows.
    """
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
    """Sum a member's unpaid fine total for badges and pay walls.

    Aggregates fine_amount over unpaid (fine_paid=FALSE) loans.

    Args:
        borrower_id: Member's borrower FK.

    Returns:
        Total fine amount (0 when nothing owed).
    """
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
    """Mark one loan's fine as paid plus audit stamps.

    Sets fine_paid=TRUE so the loan drops out of unpaid totals while
    remaining in history.

    Args:
        circulation_id: Loan primary key whose fine was collected.
        updated_by: Staff user_id who collected payment.
    """
    db.execute(
        'UPDATE circulation_records SET fine_paid = TRUE, updated_at = NOW(), updated_by = %s WHERE circulation_id = %s',
        (updated_by, circulation_id)
    )


def get_borrower_by_user(user_id):
    """Fetch a member's borrower row by login user id.

    Selects explicit columns in fixed order (never SELECT *): older
    databases have phone_number physically last (added by ALTER TABLE),
    which would shift borrower_status and break every positional
    reader.

    Args:
        user_id: user_accounts primary key.

    Returns:
        Tuple (borrower_id, user_id, id_number, department,
        phone_number, borrower_status, updated_at, updated_by) or None.
    """
    return db.fetch_one(
        'SELECT borrower_id, user_id, id_number, department, phone_number,'
        ' borrower_status, updated_at, updated_by'
        ' FROM borrowers WHERE user_id = %s', (user_id,))


def get_borrower_by_id_number(id_number):
    """Fetch a member's borrower row by school ID number.

    Uses the same explicit column order as get_borrower_by_user so
    positional readers stay correct on older databases.

    Args:
        id_number: Canonical school ID string.

    Returns:
        Tuple (borrower_id, user_id, id_number, department,
        phone_number, borrower_status, updated_at, updated_by) or None.
    """
    return db.fetch_one(
        'SELECT borrower_id, user_id, id_number, department, phone_number,'
        ' borrower_status, updated_at, updated_by'
        ' FROM borrowers WHERE id_number = %s', (id_number,))


def get_borrower_details(borrower_id):
    """Fetch one borrower's identity plus account and role names.

    Joins borrowers to users and roles for desk displays that need the
    member's name, role, department, and status together.

    Args:
        borrower_id: Borrower primary key.

    Returns:
        Tuple (borrower_id, id_number, department, borrower_status,
        full_name, user_id, role_name) or None.
    """
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
    """Place a member in line for a title as a waiting reservation.

    Inserts into reservation_queue with status 'waiting',
    request_date=NOW(), and the caller-computed queue position
    (from get_next_queue_position). Duplicate active guards and the
    unique index prevent the same member holding two live slots.

    Args:
        book_id: Title FK being reserved.
        borrower_id: Member's borrower FK.
        queue_position: 1-based position at the back of the queue.

    Returns:
        Rowcount from the INSERT.
    """
    return db.execute(
        '''INSERT INTO reservation_queue
           (book_id, borrower_id, queue_position, reservation_status, request_date)
           VALUES (%s, %s, %s, 'waiting', NOW())''',
        (book_id, borrower_id, queue_position)
    )


def get_next_queue_position(book_id):
    """Compute the next back-of-queue position number for a title.

    Returns MAX(queue_position)+1 over all rows for the book (or 1 when
    empty) so new reservations append fairly.

    Args:
        book_id: Title FK.

    Returns:
        Integer next queue position (>= 1).
    """
    row = db.fetch_one(
        'SELECT COALESCE(MAX(queue_position), 0) + 1 FROM reservation_queue WHERE book_id = %s',
        (book_id,)
    )
    return row[0] if row else 1


def get_active_reservation_by_book_and_borrower(book_id, borrower_id):
    """Fetch a member's live reservation slot for a title, if any.

    Matches waiting/allocated rows only, used as the duplicate-reserve
    guard before create_reservation.

    Args:
        book_id: Title FK.
        borrower_id: Member's borrower FK.

    Returns:
        Full reservation_queue row tuple, or None when no live slot.
    """
    return db.fetch_one(
        "SELECT * FROM reservation_queue WHERE book_id = %s AND borrower_id = %s AND reservation_status IN ('waiting', 'allocated')",
        (book_id, borrower_id)
    )


def get_reservation_by_id(reservation_id):
    """Fetch one reservation row by primary key regardless of status.

    Used by allocate/claim/expire actions to confirm the row exists and
    read its current status before transitioning it.

    Args:
        reservation_id: Reservation primary key.

    Returns:
        Full reservation_queue row tuple, or None if not found.
    """
    return db.fetch_one('SELECT * FROM reservation_queue WHERE reservation_id = %s', (reservation_id,))


def get_reservations_grouped():
    """Summarize reservation queues per title for the staff overview.

    Groups by book with total plus per-status FILTER counts
    (waiting/allocated/claimed/expired) ordered by title, so staff see
    demand and readiness at a glance.

    Returns:
        List of (book_id, title, author, total, waiting, allocated,
        claimed, expired) tuples.
    """
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
    """List every reservation slot for one title in queue order.

    Joins to catalog, borrowers, and users to show who waits where
    (reservation_id, position, status, dates, title, name, user_id,
    id_number, borrow_type) for staff queue management. borrow_type is
    the loan type the slot claims into: the claimed loan's actual type
    when one matches the claim date, otherwise 'overnight' — the type
    every reservation claim is created as.

    Args:
        book_id: Title FK.

    Returns:
        List of 10-tuple reservation rows ordered by queue_position.
    """
    return db.fetch_all(
        '''SELECT r.reservation_id, r.queue_position, r.reservation_status, r.request_date, r.claim_deadline,
                  b.title, u.full_name, u.user_id, br.id_number,
                  COALESCE(loan.borrow_type, 'overnight') AS borrow_type
           FROM reservation_queue r
           JOIN book_catalog b ON r.book_id = b.book_id
           JOIN borrowers br ON r.borrower_id = br.borrower_id
           JOIN user_accounts u ON br.user_id = u.user_id
           LEFT JOIN LATERAL (
               SELECT c.borrow_type
               FROM circulation_records c
               WHERE c.book_id = r.book_id AND c.borrower_id = r.borrower_id
                 AND c.transaction_type = 'borrow'
                 AND DATE(r.updated_at) = c.borrow_date
               ORDER BY c.borrow_date DESC
               LIMIT 1
           ) loan ON TRUE
           WHERE r.book_id = %s
           ORDER BY r.queue_position''',
        (book_id,)
    )

def get_reservations_by_borrower(borrower_id):
    """List a member's live reservations for user-facing views.

    Active-only: finished (claimed/expired) reservations are hidden
    here (staff use get_full_reservation_history_by_borrower). Returns
    waiting/allocated rows with title/author in queue order.

    Args:
        borrower_id: Member's borrower FK.

    Returns:
        List of (reservation_id, queue_position, reservation_status,
        request_date, claim_deadline, title, author) tuples.
    """
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
    """Mark a waiting reservation as allocated with a claim deadline.

    Moves the slot to 'allocated' and sets claim_deadline (when the
    member must pick up the copy before expire_overdue_reservations
    reaps it), plus audit stamps.

    Args:
        reservation_id: Reservation primary key to allocate.
        claim_deadline: Deadline datetime for pickup.
        updated_by: Staff user_id for the audit stamp.

    Returns:
        Rowcount from the UPDATE.
    """
    return db.execute(
        "UPDATE reservation_queue SET reservation_status = 'allocated', claim_deadline = %s, updated_at = NOW(), updated_by = %s WHERE reservation_id = %s",
        (claim_deadline, updated_by, reservation_id)
    )


def claim_reservation(reservation_id, updated_by=None):
    """Mark an allocated reservation as claimed on pickup.

    Moves the slot to 'claimed' with audit stamps when the member
    collects the held copy (which is then lent via borrow_book).

    Args:
        reservation_id: Allocated reservation primary key.
        updated_by: Staff user_id for the audit stamp.

    Returns:
        Rowcount from the UPDATE.
    """
    return db.execute(
        "UPDATE reservation_queue SET reservation_status = 'claimed', updated_at = NOW(), updated_by = %s WHERE reservation_id = %s",
        (updated_by, reservation_id)
    )


def expire_reservation(reservation_id, updated_by=None):
    """Mark one reservation as expired without waiting for the sweeper.

    Moves the slot to 'expired' with audit stamps, freeing the held
    copy for the next person in queue. Used for manual expiry and
    deadline enforcement.

    Args:
        reservation_id: Reservation primary key to expire.
        updated_by: Staff user_id for the audit stamp, or None.

    Returns:
        Rowcount from the UPDATE.
    """
    return db.execute(
        "UPDATE reservation_queue SET reservation_status = 'expired', updated_at = NOW(), updated_by = %s WHERE reservation_id = %s",
        (updated_by, reservation_id)
    )


def next_in_queue(book_id):
    """Fetch the front waiting reservation for a title to allocate next.

    Returns the lowest queue_position row still 'waiting', which is who
    gets the next freed copy.

    Args:
        book_id: Title FK.

    Returns:
        Full reservation_queue row tuple, or None when nobody waits.
    """
    return db.fetch_one(
        "SELECT * FROM reservation_queue WHERE book_id = %s AND reservation_status = 'waiting' ORDER BY queue_position ASC LIMIT 1",
        (book_id,)
    )


def create_notification(recipient_id, message, notif_type, related_reference=None):
    """Queue one notification message for a borrower.

    Inserts into notification_log with date_sent defaulting to now and
    is_read FALSE; callers pair this with notification_exists to avoid
    same-day duplicates for reminders.

    Args:
        recipient_id: Borrower FK who receives it.
        message: Human-readable notification text.
        notif_type: Type code (borrow, return, overdue_reminder, etc.).
        related_reference: Related loan/reservation id string, or None.

    Returns:
        Rowcount from the INSERT.
    """
    return db.execute(
        'INSERT INTO notification_log (recipient_id, message, notif_type, related_reference) VALUES (%s, %s, %s, %s)',
        (recipient_id, message, notif_type, related_reference)
    )


def is_low_stock(book_id, threshold=2):
    try:
        return (count_available_accessions(book_id) or 0) <= int(threshold)
    except Exception:
        return False


def is_aged_for_weeding(year_published, lifespan_years=10):
    try:
        if not year_published: return False
        from datetime import date as _d
        return (_d.today().year - int(year_published)) >= int(lifespan_years)
    except Exception:
        return False

