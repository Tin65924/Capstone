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


def return_book(circulation_id, fine_amount=0):
    return db.execute(
        'UPDATE circulation_records SET transaction_status = %s, return_date = %s, fine_amount = %s WHERE circulation_id = %s',
        ('returned', date.today(), fine_amount, circulation_id)
    )


def get_active_loans_by_borrower(borrower_id):
    return db.fetch_all(
        "SELECT * FROM circulation_records WHERE borrower_id = %s AND transaction_status = 'active'",
        (borrower_id,)
    )


def get_active_loan_by_accession(accession_id):
    return db.fetch_one(
        "SELECT * FROM circulation_records WHERE accession_id = %s AND transaction_status = 'active'",
        (accession_id,)
    )


def count_active_loans(borrower_id):
    row = db.fetch_one(
        "SELECT COUNT(*) FROM circulation_records WHERE borrower_id = %s AND transaction_status = 'active'",
        (borrower_id,)
    )
    return row[0] if row else 0


def calculate_fine(circulation_id, overdue_rate=10.0):
    record = db.fetch_one(
        'SELECT due_date, return_date FROM circulation_records WHERE circulation_id = %s',
        (circulation_id,)
    )
    if not record:
        return 0
    due_date, return_date = record
    returned = return_date if return_date else date.today()
    overdue_days = (returned - due_date).days
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
        "SELECT * FROM circulation_records WHERE transaction_status = 'overdue'"
    )


def get_due_within_days(days=2):
    from datetime import timedelta
    target = date.today() + timedelta(days=days)
    return db.fetch_all(
        "SELECT * FROM circulation_records WHERE due_date = %s AND transaction_status = 'active'",
        (target,)
    )
