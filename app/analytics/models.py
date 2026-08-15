import json

from app.database import db


def _date_filter(clause_prefix, column):
    parts, params = [], []
    if clause_prefix.get('start') is not None:
        parts.append('{} >= %s'.format(column))
        params.append(clause_prefix['start'])
    if clause_prefix.get('end') is not None:
        parts.append('{} <= %s'.format(column))
        params.append(clause_prefix['end'])
    return parts, params


def books_borrowed_per_program(start_date=None, end_date=None):
    parts, params = _date_filter({'start': start_date, 'end': end_date}, 'c.borrow_date')
    where = 'WHERE ' + ' AND '.join(parts) if parts else ''
    return db.fetch_all(
        '''SELECT b.department, COUNT(c.circulation_id) as total
           FROM circulation_records c
           JOIN borrowers b ON c.borrower_id = b.borrower_id
           {} GROUP BY b.department ORDER BY total DESC'''.format(where),
        tuple(params) if params else None
    )


def utilization_rate(start_date=None, end_date=None):
    total = db.fetch_one("SELECT COUNT(*) FROM book_catalog WHERE catalog_status = 'active'")
    parts, params = _date_filter({'start': start_date, 'end': end_date}, 'borrow_date')
    where = 'WHERE transaction_status = \'active\'' + (' AND ' + ' AND '.join(parts) if parts else '')
    borrowed = db.fetch_one(
        '''SELECT COUNT(DISTINCT book_id) FROM circulation_records
           {}'''.format(where),
        tuple(params) if params else None
    )
    t = total[0] if total and total[0] > 0 else 1
    b = borrowed[0] if borrowed else 0
    return round(b / t * 100, 2)


def most_borrowed_titles(start_date=None, end_date=None, limit=10):
    parts, params = _date_filter({'start': start_date, 'end': end_date}, 'c.borrow_date')
    where = 'WHERE ' + ' AND '.join(parts) if parts else ''
    params.append(limit)
    return db.fetch_all(
        '''SELECT bc.title, COUNT(c.circulation_id) as borrow_count
           FROM book_catalog bc
           JOIN circulation_records c ON bc.book_id = c.book_id
           {} GROUP BY bc.book_id, bc.title ORDER BY borrow_count DESC LIMIT %s'''.format(where),
        tuple(params)
    )


def underutilized_titles(start_date=None, end_date=None):
    parts, params = _date_filter({'start': start_date, 'end': end_date}, 'c.borrow_date')
    on_cond = ' AND ' + ' AND '.join(parts) if parts else ''
    return db.fetch_all(
        '''SELECT bc.title FROM book_catalog bc
           LEFT JOIN circulation_records c ON bc.book_id = c.book_id{}
           GROUP BY bc.book_id, bc.title HAVING COUNT(c.circulation_id) = 0'''.format(on_cond),
        tuple(params) if params else None
    )


def save_report_snapshot(report_type, filter_params, kpi_data, generated_by):
    return db.execute(
        '''INSERT INTO analytics_cache (report_type, filter_params, kpi_data, generated_by)
           VALUES (%s, %s, %s, %s)''',
        (report_type, json.dumps(filter_params), json.dumps(kpi_data), generated_by)
    )