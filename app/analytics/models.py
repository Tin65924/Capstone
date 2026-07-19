from app.database import db


def books_borrowed_per_program():
    return db.fetch_all(
        '''SELECT b.department, COUNT(c.circulation_id) as total
           FROM circulation_records c
           JOIN borrowers b ON c.borrower_id = b.borrower_id
           GROUP BY b.department ORDER BY total DESC'''
    )


def utilization_rate():
    total = db.fetch_one("SELECT COUNT(*) FROM book_catalog WHERE catalog_status = 'active'")
    borrowed = db.fetch_one(
        "SELECT COUNT(DISTINCT book_id) FROM circulation_records WHERE transaction_status = 'active'"
    )
    t = total[0] if total and total[0] > 0 else 1
    b = borrowed[0] if borrowed else 0
    return round(b / t * 100, 2)


def most_borrowed_titles(limit=10):
    return db.fetch_all(
        '''SELECT bc.title, COUNT(c.circulation_id) as borrow_count
           FROM book_catalog bc
           JOIN circulation_records c ON bc.book_id = c.book_id
           GROUP BY bc.book_id, bc.title ORDER BY borrow_count DESC LIMIT %s''',
        (limit,)
    )


def underutilized_titles():
    return db.fetch_all(
        '''SELECT bc.title FROM book_catalog bc
           LEFT JOIN circulation_records c ON bc.book_id = c.book_id
           GROUP BY bc.book_id, bc.title HAVING COUNT(c.circulation_id) = 0'''
    )
