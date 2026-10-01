from app.database import db
from app.auth.models import get_pending_users
from app.circulation.models import (
    get_circulation_stats,
    get_reservations_grouped,
)
from app.procurement.models import get_procurement_items


def get_dashboard_stats():
    titles = db.fetch_one(
        "SELECT COUNT(*) FROM book_catalog WHERE catalog_status = 'active'"
    )
    accessions = db.fetch_one(
        '''SELECT COUNT(*) FROM accession_log a
           JOIN book_catalog b ON a.book_id = b.book_id
           WHERE b.catalog_status = 'active' '''
    )
    active_loans = db.fetch_one(
        "SELECT COUNT(*) FROM circulation_records WHERE transaction_type = 'borrow' AND transaction_status IN ('active', 'overdue')"
    )
    open_requests = db.fetch_one(
        "SELECT COUNT(*) FROM request_records WHERE request_status IN ('pending_review', 'approved')"
    )
    overdue = db.fetch_one(
        "SELECT COUNT(*) FROM circulation_records WHERE transaction_type = 'borrow' AND transaction_status IN ('active', 'overdue') AND due_date < CURRENT_DATE"
    )
    total_titles = titles[0] if titles else 0
    total_accessions = accessions[0] if accessions else 0
    return {
        'total_collection': total_titles,
        'total_titles': total_titles,
        'total_accessions': total_accessions,
        'active_loans': active_loans[0] if active_loans else 0,
        'open_requests': open_requests[0] if open_requests else 0,
        'overdue_items': overdue[0] if overdue else 0,
        'reservations_waiting': count_waiting_reservations(),
        'procurement_open': count_open_procurement(),
    }


def count_waiting_reservations():
    """Reservations still needing librarian action (waiting + allocated)."""
    total = 0
    for row in get_reservations_grouped() or []:
        try:
            total += int(row[4] or 0) + int(row[5] or 0)
        except (IndexError, TypeError, ValueError):
            continue
    return total


def count_open_procurement():
    """Procurement items not yet delivered (for ordering + ordered)."""
    return len(get_procurement_items('for_ordering') or []) + \
        len(get_procurement_items('ordered') or [])


def get_attention_summary():
    """Action-needed counts for the dashboard attention panel."""
    circ = get_circulation_stats()
    return {
        'overdue_items': circ.get('overdue_items', 0),
        'due_soon': circ.get('due_in_days', 0),
        'pending_users': len(get_pending_users() or []),
        'waiting_reservations': count_waiting_reservations(),
    }


def get_admin_overview_stats():
    """Governance-focused counts for the admin System Overview.

    Unlike get_dashboard_stats (circulation-focused for librarians),
    this answers: how many accounts exist, who is waiting for approval,
    and how is staff distributed. Backup health is rendered separately
    from backup_log so this stays cheap to mock and test.
    """
    from app.auth.models import (
        count_active_users_by_role,
        count_pending_users,
        count_total_users,
    )

    total = count_total_users()
    pending = count_pending_users()
    by_role_rows = count_active_users_by_role() or []
    by_role = {}
    for row in by_role_rows:
        try:
            by_role[row[0]] = int(row[1] or 0)
        except (IndexError, TypeError, ValueError):
            continue
    collection = db.fetch_one(
        "SELECT COUNT(*) FROM book_catalog WHERE catalog_status = 'active'"
    )
    accessions = db.fetch_one(
        '''SELECT COUNT(*) FROM accession_log a
           JOIN book_catalog b ON a.book_id = b.book_id
           WHERE b.catalog_status = 'active' '''
    )
    total_titles = collection[0] if collection else 0
    total_accessions = accessions[0] if accessions else 0
    return {
        'total_users': total,
        'pending_users': pending,
        'active_librarians': by_role.get('Librarian', 0),
        'active_faculty': by_role.get('Faculty', 0),
        'active_students': by_role.get('Student', 0),
        'active_admins': by_role.get('Admin', 0),
        'total_collection': total_titles,
        'total_titles': total_titles,
        'total_accessions': total_accessions,
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
    return [(row[0], row[1]) for row in rows or []]
