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
    """List procurement rows newest-first, optionally filtered by status.

    Joins ``procurement_log`` to ``request_records`` so each row carries
    the requested title and author alongside the order state. Powers the
    librarian procurement dashboard table and its status filter chips.

    Args:
        status: Optional ``order_status`` to filter by (e.g.
            ``'ordered'``), or None for every row.

    Returns:
        List of 11-tuples (procurement_id, request_id, order_status,
        order_date, date_received, book_id, remarks, updated_at,
        updated_by, book_title, author) ordered by order_date DESC.
    """
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
    """Fetch one procurement row by primary key with request details.

    Joins ``procurement_log`` to ``request_records`` for the title and
    author context the status-update form shows. Used as the existence
    pre-check before any status write so missing ids flash a friendly
    message instead of silently updating zero rows.

    Args:
        procurement_id: Primary key of the procurement_log row.

    Returns:
        11-tuple (procurement_id, request_id, order_status, order_date,
        date_received, book_id, remarks, updated_at, updated_by,
        book_title, author), or None when the id does not exist.
    """
    rows = db.fetch_all(
        f'''SELECT {_PROC_COLS}
           FROM procurement_log p
           JOIN request_records rr ON p.request_id = rr.request_id
           WHERE p.procurement_id = %s''',
        (procurement_id,)
    )
    return rows[0] if rows else None


def create_procurement(request_id):
    """Create the procurement row for an approved book request, once only.

    Inserts with ``order_status='for_ordering'`` and today's order date,
    guarded by a ``NOT EXISTS`` clause so double-approval clicks or bulk
    retries never create duplicate procurement rows for the same request.
    Called from the request approve flows after the request flips to
    ``approved``.

    Args:
        request_id: FK into request_records that was just approved.

    Returns:
        Rowcount from the conditional INSERT (1 on first creation,
        0 when a row already existed).
    """
    return db.execute(
        '''INSERT INTO procurement_log (request_id, order_status, order_date)
           SELECT %s, %s, %s
           WHERE NOT EXISTS (SELECT 1 FROM procurement_log WHERE request_id = %s)''',
        (request_id, 'for_ordering', date.today(), request_id)
    )


def update_procurement_status(procurement_id, order_status, remarks=None, date_received=None, book_id=None, updated_by=None):
    """Advance a procurement order to a new status with audit stamps.

    Writes the new ``order_status`` plus remarks and audit columns on
    every call. When ``date_received`` is given the receipt date and the
    linked catalog ``book_id`` are stored too (the delivered path); the
    plain path only touches status, remarks, and audit stamps. Callers
    must validate ``order_status`` against ``VALID_STATUSES`` first.

    Args:
        procurement_id: Target procurement_log row.
        order_status: New status string from VALID_STATUSES.
        remarks: Optional staff note about the order.
        date_received: Optional receipt date for delivered orders.
        book_id: Optional catalog FK once the title is cataloged.
        updated_by: Acting staff user_id for the audit stamp.

    Returns:
        Rowcount from the UPDATE.
    """
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
