from datetime import date
from app.database import db


def mark_copy_present(accession_id, checked_by=None):
    """Mark a scanned copy as available on the shelf via realtime scan.

    Thin wrapper over upsert_inventory_record with state 'available'
    and inventory_type 'realtime_scan', used when a single barcode is
    checked outside a full session.

    Args:
        accession_id: Copy primary key that was scanned.
        checked_by: Staff user_id who scanned, or None.

    Returns:
        Rowcount from the upsert.
    """
    return upsert_inventory_record(accession_id, 'available', 'realtime_scan', checked_by)


def mark_copy_missing(accession_id, checked_by=None):
    """Mark a copy as missing via realtime scan when it cannot be found.

    Thin wrapper over upsert_inventory_record with state 'missing' and
    inventory_type 'realtime_scan'. Missing copies block lending until
    reconciled or found.

    Args:
        accession_id: Copy primary key reported missing.
        checked_by: Staff user_id who reported it, or None.

    Returns:
        Rowcount from the upsert.
    """
    return upsert_inventory_record(accession_id, 'missing', 'realtime_scan', checked_by)


def mark_copy_damaged(accession_id, notes=None, session_id=None, checked_by=None):
    """Flag a copy as damaged with an optional condition note.

    Records inventory_state 'damaged' via upsert_inventory_record,
    using inventory_type 'annual_physical' when part of a session and
    'realtime_scan' otherwise. The note shows wherever the copy
    condition is displayed.

    Args:
        accession_id: Copy primary key.
        notes: Damage description, or None.
        session_id: Owning inventory session, or None for ad-hoc scans.
        checked_by: Staff user_id who flagged it, or None.

    Returns:
        Rowcount from the upsert.
    """
    inventory_type = 'annual_physical' if session_id else 'realtime_scan'
    return upsert_inventory_record(accession_id, 'damaged', inventory_type, checked_by, session_id=session_id, notes=notes)


def mark_copy_lost(accession_id, notes=None, session_id=None, checked_by=None):
    """Flag a copy as lost, with an optional reason note.

    Records inventory_state 'lost' via upsert_inventory_record, using
    'annual_physical' inside a session and 'realtime_scan' otherwise.
    Lost copies are excluded from lending until recovered. The note is
    shown wherever the copy condition is displayed.

    Args:
        accession_id: Copy primary key.
        notes: Loss reason, or None.
        session_id: Owning inventory session, or None for ad-hoc scans.
        checked_by: Staff user_id who flagged it, or None.

    Returns:
        Rowcount from the upsert.
    """
    inventory_type = 'annual_physical' if session_id else 'realtime_scan'
    return upsert_inventory_record(accession_id, 'lost', inventory_type, checked_by, session_id=session_id, notes=notes)


def upsert_inventory_record(accession_id, state, inventory_type, checked_by, session_id=None, notes=None):
    """Create or overwrite a copy's inventory_status row with new state.

    The single write path behind every mark_*/scan/reconcile flow:
    when a row exists for the accession it is UPDATED (state,
    checked_by, last_checked_date, session_id, notes), otherwise a new
    row is INSERTED with the given inventory_type.

    Args:
        accession_id: Copy primary key.
        state: New inventory_state ('available', 'borrowed', 'missing',
            'damaged', 'lost').
        inventory_type: 'realtime_scan' or 'annual_physical'.
        checked_by: Staff user_id performing the check, or None.
        session_id: Owning session for physical counts, or None.
        notes: Condition note, or None.

    Returns:
        Rowcount from the UPDATE or INSERT.
    """
    existing = db.fetch_one(
        'SELECT inventory_id FROM inventory_status WHERE accession_id = %s',
        (accession_id,)
    )
    if existing:
        return db.execute(
            'UPDATE inventory_status SET inventory_state = %s, checked_by = %s, last_checked_date = %s, session_id = %s, notes = %s WHERE accession_id = %s',
            (state, checked_by, date.today(), session_id, notes, accession_id)
        )
    return db.execute(
        'INSERT INTO inventory_status (accession_id, inventory_state, inventory_type, checked_by, last_checked_date, session_id, notes) VALUES (%s, %s, %s, %s, %s, %s, %s)',
        (accession_id, state, inventory_type, checked_by, date.today(), session_id, notes)
    )


def reconcile_inventory(session_id, scanned_accessions, checked_by=None):
    """Reconcile a finished physical count against the full collection.

    Compares every accession against the scanned set: copies already
    marked damaged/lost are skipped; scanned copies become 'available'
    (or 'borrowed' when a live loan exists); on-loan-but-unscanned
    copies become 'borrowed'; everything else becomes 'missing' and is
    collected as a discrepancy. Then closes the session as 'completed'
    with the scanned count and today's date.

    Args:
        session_id: Inventory session being closed.
        scanned_accessions: Iterable of scanned accession_id values.
        checked_by: Staff user_id closing the session, or None.

    Returns:
        List of dicts {accession_id, accession, issue} for each newly
        missing copy.
    """
    all_copies = db.fetch_all(
        '''SELECT al.accession_id, al.accession_number, ist.inventory_state
           FROM accession_log al
           LEFT JOIN inventory_status ist ON ist.accession_id = al.accession_id'''
    )
    scanned_set = set(scanned_accessions)
    discrepancies = []
    for acc_id, acc_num, current_state in all_copies:
        if current_state in ('damaged', 'lost'):
            continue

        active_loan = db.fetch_one(
            "SELECT circulation_id FROM circulation_records WHERE accession_id = %s AND transaction_status = 'active'",
            (acc_id,)
        )
        if acc_id in scanned_set:
            state = 'borrowed' if active_loan else 'available'
            upsert_inventory_record(acc_id, state, 'annual_physical', checked_by, session_id=session_id)
        elif active_loan:
            upsert_inventory_record(acc_id, 'borrowed', 'annual_physical', checked_by, session_id=session_id)
        else:
            upsert_inventory_record(acc_id, 'missing', 'annual_physical', checked_by, session_id=session_id)
            discrepancies.append({'accession_id': acc_id, 'accession': acc_num, 'issue': 'Missing'})

    db.execute(
        'UPDATE inventory_sessions SET scanned_count = %s, session_status = %s, ended_at = %s, updated_at = NOW(), updated_by = %s WHERE session_id = %s',
        (len(scanned_accessions), 'completed', date.today(), checked_by, session_id)
    )
    return discrepancies


def get_status_summary():
    """Count inventory rows grouped by state for dashboard widgets.

    Returns one row per inventory_state present (e.g. available,
    borrowed, missing, damaged, lost) with its copy count.

    Returns:
        List of (inventory_state, count) tuples.
    """
    return db.fetch_all(
        'SELECT inventory_state, COUNT(*) FROM inventory_status GROUP BY inventory_state'
    )


def create_inventory_session(librarian_id, total_books):
    """Open a new annual-physical inventory session and return its id.

    Inserts into inventory_sessions with scanned_count 0, status
    'active', and started_at today. The librarian should have no other
    active session (routes enforce one-at-a-time).

    Args:
        librarian_id: Staff user_id running the count.
        total_books: Total copies expected at session start.

    Returns:
        1-tuple (session_id,) of the new session, or None on failure.
    """
    return db.fetch_one(
        '''INSERT INTO inventory_sessions (librarian_id, total_books, scanned_count, session_status, started_at)
           VALUES (%s, %s, %s, %s, %s) RETURNING session_id''',
        (librarian_id, total_books, 0, 'active', date.today())
    )


def get_session(session_id):
    """Fetch one inventory session by primary key regardless of status.

    Used to render session progress, validate scan targets, and guard
    complete/cancel/export actions.

    Args:
        session_id: Inventory session primary key.

    Returns:
        Full inventory_sessions row tuple, or None if not found.
    """
    return db.fetch_one(
        'SELECT * FROM inventory_sessions WHERE session_id = %s',
        (session_id,)
    )


def get_active_session(librarian_id):
    """Fetch a librarian's currently open inventory session, if any.

    Selects the 'active' session for the staff member, enforcing the
    one-active-session-at-a-time rule before a new session may start.

    Args:
        librarian_id: Staff user_id who owns the session.

    Returns:
        Full inventory_sessions row tuple, or None when none is open.
    """
    return db.fetch_one(
        "SELECT * FROM inventory_sessions WHERE librarian_id = %s AND session_status = 'active'",
        (librarian_id,)
    )


def update_session_scan(session_id, accession_id, updated_by=None):
    """Record one barcode scan toward a session's progress counter.

    Skips (returns None) when the copy was already scanned in this
    session; otherwise increments inventory_sessions.scanned_count and
    stamps audit fields. The actual copy-state write happens via the
    mark_* path — this only tracks progress.

    Args:
        session_id: Active inventory session being counted.
        accession_id: Scanned copy primary key.
        updated_by: Staff user_id for the audit stamp.

    Returns:
        Rowcount from the counter UPDATE, or None when already
        scanned in this session.
    """
    already_scanned = db.fetch_one(
        'SELECT inventory_id FROM inventory_status WHERE accession_id = %s AND session_id = %s',
        (accession_id, session_id)
    )
    if already_scanned:
        return None
    return db.execute(
        'UPDATE inventory_sessions SET scanned_count = scanned_count + 1, updated_at = NOW(), updated_by = %s WHERE session_id = %s',
        (updated_by, session_id)
    )


def end_session(session_id, updated_by=None):
    """Close an inventory session as completed without reconciliation.

    Sets session_status='completed' with ended_at today plus audit
    stamps. The full physical-count close path uses
    reconcile_inventory instead (which also flips missing copies).

    Args:
        session_id: Session primary key to close.
        updated_by: Staff user_id for the audit stamp.

    Returns:
        Rowcount from the UPDATE.
    """
    return db.execute(
        "UPDATE inventory_sessions SET session_status = 'completed', ended_at = %s, updated_at = NOW(), updated_by = %s WHERE session_id = %s",
        (date.today(), updated_by, session_id)
    )

def get_scanned_in_session(session_id):
    """List copy ids tagged to one inventory session.

    Returns every accession_id whose inventory_status row points at the
    session, used for progress display and export scoping.

    Args:
        session_id: Inventory session primary key.

    Returns:
        List of 1-tuples (accession_id,) scanned in the session.
    """
    return db.fetch_all(
        'SELECT accession_id FROM inventory_status WHERE session_id = %s',
        (session_id,)
    )


def get_scan_history(page=1, per_page=10, status_filter=None):
    """List inventory check rows newest-first with pagination and filter.

    Joins inventory_status through accessions to titles to produce
    (inventory_id, accession_id, accession_number, title,
    inventory_state, last_checked_date, notes) for the scan-history
    table. An optional state filter narrows to one condition.

    Args:
        page: 1-based page number.
        per_page: Rows per page.
        status_filter: Optional inventory_state to filter by.

    Returns:
        List of 7-tuple history rows for the page.
    """
    base_query = '''
        SELECT ist.inventory_id, ist.accession_id, al.accession_number, bc.title, ist.inventory_state,
               ist.last_checked_date, ist.notes
        FROM inventory_status ist
        JOIN accession_log al ON al.accession_id = ist.accession_id
        JOIN book_catalog bc ON bc.book_id = al.book_id
    '''
    conditions = []
    params = []

    if status_filter:
        conditions.append('ist.inventory_state = %s')
        params.append(status_filter)

    if conditions:
        base_query += ' WHERE ' + ' AND '.join(conditions)

    base_query += ' ORDER BY ist.last_checked_date DESC LIMIT %s OFFSET %s'
    params.append(per_page)
    params.append((page - 1) * per_page)

    return db.fetch_all(base_query, tuple(params))


def count_scan_history(status_filter=None):
    """Count inventory check rows for history pagination totals.

    Mirrors get_scan_history's optional state filter so the total
    matches the rows the page query can return.

    Args:
        status_filter: Optional inventory_state to count only.

    Returns:
        Integer matching-row count.
    """
    base_query = 'SELECT COUNT(*) FROM inventory_status ist'
    params = []

    if status_filter:
        base_query += ' WHERE ist.inventory_state = %s'
        params.append(status_filter)

    row = db.fetch_one(base_query, tuple(params))
    return row[0] if row else 0


def get_accession_status(accession_id):
    """Fetch one copy's barcode, title, and latest inventory condition.

    Joins accession_log to its title and left-joins inventory_status
    (copies never checked return NULL state/date) for scan-lookup and
    condition-badge displays.

    Args:
        accession_id: Copy primary key.

    Returns:
        Tuple (accession_number, title, inventory_state,
        last_checked_date) or None if the copy is gone.
    """
    return db.fetch_one(
        '''SELECT al.accession_number, bc.title, ist.inventory_state, ist.last_checked_date
           FROM accession_log al
           JOIN book_catalog bc ON bc.book_id = al.book_id
           LEFT JOIN inventory_status ist ON ist.accession_id = al.accession_id
           WHERE al.accession_id = %s''',
        (accession_id,)
    )

def count_accessions():
    """Count every physical copy for session setup and dashboard stats.

    Simple COUNT(*) over accession_log used as the total_books baseline
    when opening a session.

    Returns:
        Integer total copy count.
    """
    row = db.fetch_one('SELECT COUNT(*) FROM accession_log')
    return row[0] if row else 0


def get_conditions_for_accessions(accession_ids):
    """Condition per copy for the cataloging table: {accession_id: row}.

    Row is (inventory_state or None, reason or None, loan_damage or None,
    circ_lost bool). Lost = inventory 'lost' OR the latest loan flagged
    lost (legacy return-path data). Damaged = inventory 'damaged', or —
    when inventory never assessed the copy — damage recorded on the
    latest loan. The reason prefers the inventory note and falls back to
    that loan note. Returns {} for empty/None.
    """
    if not accession_ids:
        return {}
    rows = db.fetch_all(
        '''SELECT a.accession_id, ist.inventory_state, ist.notes,
              (SELECT c.damage_notes FROM circulation_records c
               WHERE c.accession_id = a.accession_id
               ORDER BY c.circulation_id DESC LIMIT 1),
              COALESCE((
                  SELECT c.lost_flag FROM circulation_records c
                  WHERE c.accession_id = a.accession_id
                  ORDER BY c.circulation_id DESC LIMIT 1
              ), FALSE)
           FROM accession_log a
           LEFT JOIN inventory_status ist ON ist.accession_id = a.accession_id
           WHERE a.accession_id = ANY(%s)''',
        (list(accession_ids),)
    ) or []
    return {row[0]: row[1:] for row in rows if row}


def cancel_inventory_session(session_id, updated_by=None):
    """Abort an active inventory session as cancelled.

    Sets session_status='cancelled' with ended_at today plus audit
    stamps. Already-recorded copy states are kept; only the session is
    closed without reconciliation.

    Args:
        session_id: Active session primary key to cancel.
        updated_by: Staff user_id for the audit stamp.

    Returns:
        Rowcount from the UPDATE.
    """
    return db.execute(
        "UPDATE inventory_sessions SET session_status = 'cancelled', ended_at = %s, updated_at = NOW(), updated_by = %s WHERE session_id = %s",
        (date.today(), updated_by, session_id)
    )

def get_session_export_rows(session_id):
    """Fetch session rows for CSV/XLSX export newest-check-first.

    Joins session-tagged inventory_status rows to accessions and titles
    to produce (accession_number, title, inventory_state,
    last_checked_date, notes) for the download.

    Args:
        session_id: Inventory session primary key to export.

    Returns:
        List of 5-tuple export rows.
    """
    return db.fetch_all(
        '''SELECT al.accession_number, bc.title, ist.inventory_state, ist.last_checked_date, ist.notes
           FROM inventory_status ist
           JOIN accession_log al ON al.accession_id = ist.accession_id
           JOIN book_catalog bc ON bc.book_id = al.book_id
           WHERE ist.session_id = %s
           ORDER BY ist.last_checked_date DESC''',
        (session_id,)
    )