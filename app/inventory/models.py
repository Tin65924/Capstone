from datetime import date
from app.database import db


def mark_copy_present(accession_id):
    return upsert_inventory_record(accession_id, 'available', 'realtime_scan', None)


def mark_copy_missing(accession_id):
    return upsert_inventory_record(accession_id, 'missing', 'realtime_scan', None)


def mark_copy_damaged(accession_id, notes=None):
    return upsert_inventory_record(accession_id, 'damaged', 'realtime_scan', None, notes=notes)


def mark_copy_lost(accession_id):
    return upsert_inventory_record(accession_id, 'lost', 'realtime_scan', None)


def upsert_inventory_record(accession_id, state, inventory_type, checked_by, session_id=None, notes=None):
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


def reconcile_inventory(session_id, scanned_accessions):
    all_copies = db.fetch_all(
        'SELECT al.accession_id, al.accession_number FROM accession_log al'
    )
    scanned_set = set(scanned_accessions)
    discrepancies = []
    for acc_id, acc_num in all_copies:
        active_loan = db.fetch_one(
            "SELECT circulation_id FROM circulation_records WHERE accession_id = %s AND transaction_status = 'active'",
            (acc_id,)
        )
        if acc_id in scanned_set:
            state = 'borrowed' if active_loan else 'available'
            upsert_inventory_record(acc_id, state, 'annual_physical', None, session_id=session_id)
        elif active_loan:
            upsert_inventory_record(acc_id, 'borrowed', 'annual_physical', None, session_id=session_id)
        else:
            upsert_inventory_record(acc_id, 'missing', 'annual_physical', None, session_id=session_id)
            discrepancies.append({'accession_id': acc_id, 'accession': acc_num, 'issue': 'Missing'})

    db.execute(
        'UPDATE inventory_sessions SET scanned_count = %s, session_status = %s, ended_at = %s WHERE session_id = %s',
        (len(scanned_accessions), 'completed', date.today(), session_id)
    )
    return discrepancies


def get_status_summary():
    return db.fetch_all(
        'SELECT inventory_state, COUNT(*) FROM inventory_status GROUP BY inventory_state'
    )


def create_inventory_session(librarian_id, total_books):
    return db.fetch_one(
        '''INSERT INTO inventory_sessions (librarian_id, total_books, scanned_count, session_status, started_at)
           VALUES (%s, %s, %s, %s, %s) RETURNING session_id''',
        (librarian_id, total_books, 0, 'active', date.today())
    )


def get_session(session_id):
    return db.fetch_one(
        'SELECT * FROM inventory_sessions WHERE session_id = %s',
        (session_id,)
    )


def get_active_session(librarian_id):
    return db.fetch_one(
        "SELECT * FROM inventory_sessions WHERE librarian_id = %s AND session_status = 'active'",
        (librarian_id,)
    )


def update_session_scan(session_id):
    return db.execute(
        'UPDATE inventory_sessions SET scanned_count = scanned_count + 1 WHERE session_id = %s',
        (session_id,)
    )


def end_session(session_id):
    return db.execute(
        "UPDATE inventory_sessions SET session_status = 'completed', ended_at = %s WHERE session_id = %s",
        (date.today(), session_id)
    )

def get_scanned_in_session(session_id):
    return db.fetch_all(
        'SELECT accession_id FROM inventory_status WHERE session_id = %s',
        (session_id,)
    )


def get_scan_history(page=1, per_page=10, status_filter=None):
    base_query = '''
        SELECT ist.inventory_id, al.accession_number, bc.title, ist.inventory_state,
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
    base_query = 'SELECT COUNT(*) FROM inventory_status ist'
    params = []

    if status_filter:
        base_query += ' WHERE ist.inventory_state = %s'
        params.append(status_filter)

    row = db.fetch_one(base_query, tuple(params))
    return row[0] if row else 0


def get_accession_status(accession_id):
    return db.fetch_one(
        '''SELECT al.accession_number, bc.title, ist.inventory_state, ist.last_checked_date
           FROM accession_log al
           JOIN book_catalog bc ON bc.book_id = al.book_id
           LEFT JOIN inventory_status ist ON ist.accession_id = al.accession_id
           WHERE al.accession_id = %s''',
        (accession_id,)
    )

def count_accessions():
    row = db.fetch_one('SELECT COUNT(*) FROM accession_log')
    return row[0] if row else 0


def cancel_inventory_session(session_id):
    return db.execute(
        "UPDATE inventory_sessions SET session_status = 'cancelled', ended_at = %s WHERE session_id = %s",
        (date.today(), session_id)
    )

def get_session_export_rows(session_id):
    return db.fetch_all(
        '''SELECT al.accession_number, bc.title, ist.inventory_state, ist.last_checked_date, ist.notes
           FROM inventory_status ist
           JOIN accession_log al ON al.accession_id = ist.accession_id
           JOIN book_catalog bc ON bc.book_id = al.book_id
           WHERE ist.session_id = %s
           ORDER BY ist.last_checked_date DESC''',
        (session_id,)
    )