from datetime import date
from app.database import db


def get_procurement_items(status=None):
    if status:
        return db.fetch_all(
            'SELECT * FROM procurement_log WHERE order_status = %s ORDER BY order_date DESC',
            (status,)
        )
    return db.fetch_all(
        '''SELECT p.*, rr.book_title, rr.author
           FROM procurement_log p
           JOIN request_records rr ON p.request_id = rr.request_id
           ORDER BY p.order_date DESC'''
    )


def create_procurement(request_id):
    return db.execute(
        'INSERT INTO procurement_log (request_id, order_status, order_date) VALUES (%s, %s, %s)',
        (request_id, 'for_ordering', date.today())
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
