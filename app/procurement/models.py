from datetime import date
from app.database import db


# Canonical row shape (contract — explicit columns, never SELECT *):
# (procurement_id, request_id, order_status, order_date, date_received,
#  book_id, remarks, updated_at, updated_by, book_title, author).
# Explicit lists immunize readers against physical column drift (audit
# columns were ALTER-added on older databases).
_PROC_COLS = (
    'p.procurement_id, p.request_id, p.order_status, p.order_date, '
    'p.date_received, p.book_id, p.remarks, p.updated_at, p.updated_by, '
    'rr.book_title, rr.author'
)


def get_procurement_items(status=None):
    if status:
        return db.fetch_all(
            f'''SELECT {_PROC_COLS}
                FROM procurement_log p
                JOIN request_records rr ON p.request_id = rr.request_id
                WHERE p.order_status = %s ORDER BY p.order_date DESC''',
            (status,)
        )
    return db.fetch_all(
        f'''SELECT {_PROC_COLS}
           FROM procurement_log p
           JOIN request_records rr ON p.request_id = rr.request_id
           ORDER BY p.order_date DESC'''
    )


def get_procurement_by_id(procurement_id):
    rows = db.fetch_all(
        f'''SELECT {_PROC_COLS}
           FROM procurement_log p
           JOIN request_records rr ON p.request_id = rr.request_id
           WHERE p.procurement_id = %s''',
        (procurement_id,)
    )
    return rows[0] if rows else None


def create_procurement(request_id):
    return db.execute(
        '''INSERT INTO procurement_log (request_id, order_status, order_date)
           SELECT %s, %s, %s
           WHERE NOT EXISTS (SELECT 1 FROM procurement_log WHERE request_id = %s)''',
        (request_id, 'for_ordering', date.today(), request_id)
    )


def update_procurement_status(procurement_id, order_status, remarks=None, date_received=None, book_id=None, updated_by=None):
    if date_received:
        return db.execute(
            'UPDATE procurement_log SET order_status = %s, remarks = %s, date_received = %s, book_id = %s, updated_at = NOW(), updated_by = %s WHERE procurement_id = %s',
            (order_status, remarks, date_received, book_id, updated_by, procurement_id)
        )
    return db.execute(
        'UPDATE procurement_log SET order_status = %s, remarks = %s, updated_at = NOW(), updated_by = %s WHERE procurement_id = %s',
        (order_status, remarks, updated_by, procurement_id)
    )


VALID_STATUSES = ['for_ordering', 'ordered', 'delivered', 'cancelled', 'out_of_stock', 'procured']
