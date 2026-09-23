from datetime import date
from app.database import db


def get_procurement_items(status=None):
    # Both branches return the same shape: procurement_log columns
    # (0 procurement_id, 1 request_id, 2 order_status, ...) then
    # (7 book_title, 8 author) — the template indexes by position.
    if status:
        return db.fetch_all(
            '''SELECT p.*, rr.book_title, rr.author
               FROM procurement_log p
               JOIN request_records rr ON p.request_id = rr.request_id
               WHERE p.order_status = %s ORDER BY p.order_date DESC''',
            (status,)
        )
    return db.fetch_all(
        '''SELECT p.*, rr.book_title, rr.author
           FROM procurement_log p
           JOIN request_records rr ON p.request_id = rr.request_id
           ORDER BY p.order_date DESC'''
    )


def get_procurement_by_id(procurement_id):
    return db.fetch_one(
        'SELECT * FROM procurement_log WHERE procurement_id = %s',
        (procurement_id,)
    )


def create_procurement(request_id):
    return db.execute(
        '''INSERT INTO procurement_log (request_id, order_status, order_date)
           SELECT %s, %s, %s
           WHERE NOT EXISTS (SELECT 1 FROM procurement_log WHERE request_id = %s)''',
        (request_id, 'for_ordering', date.today(), request_id)
    )


def update_procurement_status(procurement_id, order_status, remarks=None, date_received=None, book_id=None):
    if date_received:
        return db.execute(
            'UPDATE procurement_log SET order_status = %s, remarks = %s, date_received = %s, book_id = %s WHERE procurement_id = %s',
            (order_status, remarks, date_received, book_id, procurement_id)
        )
    return db.execute(
        'UPDATE procurement_log SET order_status = %s, remarks = %s WHERE procurement_id = %s',
        (order_status, remarks, procurement_id)
    )


VALID_STATUSES = ['for_ordering', 'ordered', 'delivered', 'cancelled', 'out_of_stock', 'procured']


def clear_supplier_catalog():
    return db.execute('DELETE FROM supplier_catalog')


def add_supplier_item(supplier_name, book_title, author=None, uploaded_by=None):
    return db.execute(
        '''INSERT INTO supplier_catalog (supplier_name, book_title, author, uploaded_by)
           VALUES (%s, %s, %s, %s)''',
        (supplier_name or 'Supplier', book_title, author, uploaded_by)
    )


def get_supplier_catalog(limit=200):
    return db.fetch_all(
        '''SELECT supplier_id, supplier_name, book_title, author, uploaded_at
           FROM supplier_catalog ORDER BY uploaded_at DESC, supplier_id DESC LIMIT %s''',
        (limit,)
    )


def count_supplier_catalog():
    row = db.fetch_one('SELECT COUNT(*) FROM supplier_catalog')
    return row[0] if row else 0


def find_supplier_match(title, author=None, limit=5):
    """Case-insensitive partial match against the uploaded supplier list."""
    title = (title or '').strip()
    if not title:
        return []
    if author and author.strip():
        return db.fetch_all(
            '''SELECT supplier_name, book_title, author FROM supplier_catalog
               WHERE book_title ILIKE %s AND author ILIKE %s
               ORDER BY book_title LIMIT %s''',
            ('%' + title + '%', '%' + author.strip() + '%', limit)
        )
    return db.fetch_all(
        '''SELECT supplier_name, book_title, author FROM supplier_catalog
           WHERE book_title ILIKE %s ORDER BY book_title LIMIT %s''',
        ('%' + title + '%', limit)
    )
