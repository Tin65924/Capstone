from datetime import date
from app.database import db


def mark_copy_present(accession_id):
    return db.execute(
        "UPDATE inventory_status SET inventory_state = 'available' WHERE accession_id = %s",
        (accession_id,)
    )


def mark_copy_missing(accession_id):
    return db.execute(
        "UPDATE inventory_status SET inventory_state = 'missing' WHERE accession_id = %s",
        (accession_id,)
    )


def mark_copy_damaged(accession_id, notes=None):
    return db.execute(
        "UPDATE book_catalog SET notes = %s WHERE book_id IN (SELECT book_id FROM accession_log WHERE accession_id = %s)",
        (notes, accession_id)
    )


def mark_copy_lost(accession_id):
    return db.execute(
        "UPDATE inventory_status SET inventory_state = 'lost' WHERE accession_id = %s",
        (accession_id,)
    )


def upsert_inventory_record(accession_id, state, inventory_type, checked_by):
    existing = db.fetch_one(
        'SELECT inventory_id FROM inventory_status WHERE accession_id = %s',
        (accession_id,)
    )
    if existing:
        return db.execute(
            'UPDATE inventory_status SET inventory_state = %s, checked_by = %s, last_checked_date = %s WHERE accession_id = %s',
            (state, checked_by, date.today(), accession_id)
        )
    return db.execute(
        'INSERT INTO inventory_status (accession_id, inventory_state, inventory_type, checked_by, last_checked_date) VALUES (%s, %s, %s, %s, %s)',
        (accession_id, state, inventory_type, checked_by, date.today())
    )


def reconcile_inventory(session_id, scanned_accessions):
    all_copies = db.fetch_all(
        'SELECT al.accession_id, al.accession_number FROM accession_log al'
    )
    scanned_set = set(scanned_accessions)
    discrepancies = []
    for acc_id, acc_num in all_copies:
        if acc_num in scanned_set:
            upsert_inventory_record(acc_id, 'available', 'annual_physical', None)
        else:
            active_loan = db.fetch_one(
                "SELECT circulation_id FROM circulation_records WHERE accession_id = %s AND transaction_status = 'active'",
                (acc_id,)
            )
            if not active_loan:
                upsert_inventory_record(acc_id, 'missing', 'annual_physical', None)
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
