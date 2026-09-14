from app.database import db


def get_dashboard_stats():
    total = db.fetch_one(
        "SELECT COUNT(*) FROM book_catalog WHERE catalog_status = 'active'"
    )
    active_loans = db.fetch_one(
        "SELECT COUNT(*) FROM circulation_records WHERE transaction_status IN ('active', 'overdue')"
    )
    open_requests = db.fetch_one(
        "SELECT COUNT(*) FROM request_records WHERE request_status IN ('pending_review', 'approved')"
    )
    overdue = db.fetch_one(
        "SELECT COUNT(*) FROM circulation_records WHERE transaction_status IN ('active', 'overdue') AND due_date < CURRENT_DATE"
    )
    return {
        'total_collection': total[0] if total else 0,
        'active_loans': active_loans[0] if active_loans else 0,
        'open_requests': open_requests[0] if open_requests else 0,
        'overdue_items': overdue[0] if overdue else 0,
    }


def get_recent_activity(limit=5):
    return db.fetch_all(
        '''SELECT u.full_name, u.user_id,
                  CASE WHEN c.transaction_type = 'borrow' THEN 'Borrowed' ELSE 'Returned' END AS action,
                  b.title, c.borrow_date, c.return_date, c.due_date
           FROM circulation_records c
           JOIN book_catalog b ON c.book_id = b.book_id
           JOIN borrowers br ON c.borrower_id = br.borrower_id
           JOIN user_accounts u ON br.user_id = u.user_id
           ORDER BY COALESCE(c.return_date, c.borrow_date) DESC
           LIMIT %s''',
        (limit,)
    )


def get_daily_borrows(days=6):
    rows = db.fetch_all(
        '''SELECT DATE(borrow_date) AS d, COUNT(*) AS cnt
           FROM circulation_records
           WHERE transaction_type = 'borrow'
             AND borrow_date >= CURRENT_DATE - INTERVAL '%s days'
           GROUP BY DATE(borrow_date)
           ORDER BY d''',
        (days,)
    )
    return [(row[0], row[1]) for row in rows]
