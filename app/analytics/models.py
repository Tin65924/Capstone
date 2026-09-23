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


def _normalize_departments(departments):
    if departments is None:
        return []
    if isinstance(departments, str):
        departments = [departments]
    return [d.strip() for d in departments if d and d.strip()]


def _department_clause(departments, b_alias='b', r_alias='r'):
    """Return (clause, params) matching the program_label expression.

    program_label = COALESCE(NULLIF(department, ''),
        CASE WHEN role IN ('Admin','Librarian') THEN role ELSE 'No program' END).
    Caller must have joined borrowers AS b_alias, user_accounts, roles AS r_alias.
    Returns (None, []) when no departments given.
    """
    depts = _normalize_departments(departments)
    if not depts:
        return None, []
    conds = []
    params = []
    for d in depts:
        if d in ('Admin', 'Librarian'):
            conds.append(
                "(NULLIF({b}.department, '') IS NULL AND {r}.role_name = %s)".format(
                    b=b_alias, r=r_alias))
            params.append(d)
        elif d == 'No program':
            conds.append(
                "(NULLIF({b}.department, '') IS NULL AND "
                "{r}.role_name NOT IN ('Admin', 'Librarian'))".format(
                    b=b_alias, r=r_alias))
        else:
            conds.append("{b}.department = %s".format(b=b_alias))
            params.append(d)
    if len(conds) == 1:
        return conds[0], params
    return '(' + ' OR '.join(conds) + ')', params


def books_borrowed_per_program(start_date=None, end_date=None, departments=None,
                                borrow_type=None):
    parts, params = _date_filter({'start': start_date, 'end': end_date}, 'c.borrow_date')
    departments = _normalize_departments(departments)
    if departments:
        pseudo = [d for d in departments if d in ('Admin', 'Librarian', 'No program')]
        normal = [d for d in departments if d not in ('Admin', 'Librarian', 'No program')]
        if pseudo and normal:
            clause, cparams = _department_clause(departments, 'b', 'r')
            parts.append(clause)
            params.extend(cparams)
        elif pseudo:
            clause, cparams = _department_clause(pseudo, 'b', 'r')
            parts.append(clause)
            params.extend(cparams)
        else:
            parts.append('b.department IN ({})'.format(', '.join(['%s'] * len(departments))))
            params.extend(departments)
    if borrow_type:
        parts.append('c.borrow_type = %s')
        params.append(borrow_type)
    where = 'WHERE ' + ' AND '.join(parts) if parts else ''
    return db.fetch_all(
        '''SELECT COALESCE(NULLIF(b.department, ''),
                          CASE WHEN r.role_name IN ('Admin', 'Librarian') THEN r.role_name
                               ELSE 'No program' END) as program_label,
                  COUNT(c.circulation_id) as total
           FROM circulation_records c
           JOIN borrowers b ON c.borrower_id = b.borrower_id
           JOIN user_accounts u ON b.user_id = u.user_id
           JOIN roles r ON u.role_id = r.role_id
           {} GROUP BY COALESCE(NULLIF(b.department, ''),
                                CASE WHEN r.role_name IN ('Admin', 'Librarian') THEN r.role_name
                                     ELSE 'No program' END)
           ORDER BY total DESC'''.format(where),
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


def underutilized_titles(start_date=None, end_date=None, limit=None):
    parts, params = _date_filter({'start': start_date, 'end': end_date}, 'c.borrow_date')
    on_cond = ' AND ' + ' AND '.join(parts) if parts else ''
    limit_clause = ''
    if limit is not None:
        limit_clause = ' LIMIT %s'
        params.append(limit)
    return db.fetch_all(
        '''SELECT bc.title FROM book_catalog bc
           LEFT JOIN circulation_records c ON bc.book_id = c.book_id{}
           GROUP BY bc.book_id, bc.title HAVING COUNT(c.circulation_id) = 0{}'''.format(on_cond, limit_clause),
        tuple(params) if params else None
    )


def save_report_snapshot(report_type, filter_params, kpi_data, generated_by):
    return db.execute(
        '''INSERT INTO analytics_cache (report_type, filter_params, kpi_data, generated_by)
           VALUES (%s, %s, %s, %s)''',
        (report_type, json.dumps(filter_params), json.dumps(kpi_data), generated_by)
    )


# ---------------------------------------------------------------------------
# Riverside-style dashboard queries.
#
# The reference dashboards (Collection Tracking / Library Analytics / Usage
# Analytics) need broader aggregates than the original 4 KPIs.  All queries
# below use only columns that exist in app/schema.sql:
#   - book_catalog (titles, subject_classification, date_added)
#   - accession_log (one row per physical copy)
#   - circulation_records (active/returned/overdue, lost_flag, borrow_date)
#   - reservation_queue (waiting/allocated => reserved)
#   - inventory_status (available/borrowed/lost/damaged/missing)
#   - borrowers (department) + user_accounts/roles (user types)
#
# Approximations (documented, not silent):
#   - "Condition" buckets are derived from inventory_state + lost_flag since
#     there is no condition column: available -> New/Excellent,
#     borrowed -> Very Good, missing -> Good/Fair split, damaged -> Fair,
#     lost -> Poor.
#   - "Under Maintenance" maps to inventory_state = 'missing' (closest
#     existing bucket); there is no maintenance table.
#   - "Peak periods by hour" is served as borrowings by day because
#     borrow_date is a DATE with no time-of-day column.
# ---------------------------------------------------------------------------

def _range_clause(column, start_date, end_date):
    parts, params = [], []
    if start_date is not None:
        parts.append('{} >= %s'.format(column))
        params.append(start_date)
    if end_date is not None:
        parts.append('{} <= %s'.format(column))
        params.append(end_date)
    return parts, params


def count_active_titles():
    row = db.fetch_one(
        "SELECT COUNT(*) FROM book_catalog WHERE catalog_status = 'active'"
    )
    return row[0] if row else 0


def count_total_copies():
    row = db.fetch_one(
        '''SELECT COUNT(*) FROM accession_log a
           JOIN book_catalog b ON a.book_id = b.book_id
           WHERE b.catalog_status = 'active' '''
    )
    return row[0] if row else 0


def count_circulation_status(start_date=None, end_date=None, borrow_type=None):
    """Return [(transaction_status, count)] for active/returned/overdue."""
    parts, params = _range_clause('borrow_date', start_date, end_date)
    if borrow_type:
        parts.append('borrow_type = %s')
        params.append(borrow_type)
    where = 'WHERE ' + ' AND '.join(parts) if parts else ''
    return db.fetch_all(
        '''SELECT transaction_status, COUNT(*)
           FROM circulation_records {} GROUP BY transaction_status'''.format(where),
        tuple(params) if params else None
    )


def count_lost_flagged(start_date=None, end_date=None):
    parts, params = _range_clause('borrow_date', start_date, end_date)
    parts.append('lost_flag = TRUE')
    return db.fetch_one(
        'SELECT COUNT(*) FROM circulation_records WHERE ' + ' AND '.join(parts),
        tuple(params)
    )


def count_reservations():
    row = db.fetch_one(
        """SELECT COUNT(*) FROM reservation_queue
           WHERE reservation_status IN ('waiting', 'allocated')"""
    )
    return row[0] if row else 0


def inventory_state_counts():
    return db.fetch_all(
        'SELECT inventory_state, COUNT(*) FROM inventory_status GROUP BY inventory_state'
    )


def copies_by_status_summary(start_date=None, end_date=None, borrow_type=None):
    """Return [(status, copies)] for the Copies-by-Status chart/export.

    Available = active-catalog copies minus borrowed, overdue, reserved,
    lost/damaged (including lost-flagged loans) and missing (maintenance)
    copies, floored at zero. This matches ``compute_dashboard`` in
    ``app/analytics/routes.py`` so the KPI card and chart agree.
    """
    total = count_total_copies()
    status_rows = count_circulation_status(start_date, end_date, borrow_type) or []
    status = {}
    for r in status_rows:
        try:
            status[str(r[0])] = int(r[1] or 0)
        except (IndexError, TypeError, ValueError):
            continue
    borrowed = status.get('active', 0)
    overdue = status.get('overdue', 0)
    reserved = count_reservations()
    inv_rows = inventory_state_counts() or []
    inv = {}
    for r in inv_rows:
        try:
            inv[str(r[0])] = int(r[1] or 0)
        except (IndexError, TypeError, ValueError):
            continue
    lost_flagged_row = count_lost_flagged(start_date, end_date)
    try:
        lost_flagged = int(lost_flagged_row[0]) if lost_flagged_row else 0
    except (IndexError, TypeError, ValueError):
        lost_flagged = 0
    lost_damaged = inv.get('lost', 0) + inv.get('damaged', 0) + lost_flagged
    maintenance = inv.get('missing', 0)
    available = max(total - borrowed - overdue - reserved - lost_damaged - maintenance, 0)
    return [('Available', available), ('Borrowed', borrowed), ('Reserved', reserved),
            ('Overdue', overdue), ('Lost / Damaged', lost_damaged),
            ('Under Maintenance', maintenance)]


def collection_by_category(start_date=None, end_date=None, categories=None):
    """Return [(category, titles)] grouped by subject_classification.

    categories optionally restricts to the named categories
    (case-insensitive; 'Others' matches blank classifications).
    """
    parts, params = _range_clause('b.date_added', start_date, end_date)
    categories = [c.strip() for c in (categories or []) if c and c.strip()]
    if categories:
        conds = []
        exact = [c for c in categories if c.lower() != 'others']
        if exact:
            conds.append('LOWER(b.subject_classification) IN ({})'.format(
                ', '.join(['%s'] * len(exact))))
            params.extend([c.lower() for c in exact])
        if len(exact) != len(categories):
            conds.append("(b.subject_classification IS NULL OR b.subject_classification = '')")
        parts.append('(' + ' OR '.join(conds) + ')')
    where = 'WHERE b.catalog_status = \'active\'' + (
        ' AND ' + ' AND '.join(parts) if parts else '')
    return db.fetch_all(
        '''SELECT COALESCE(NULLIF(b.subject_classification, ''), 'Others'),
                  COUNT(DISTINCT b.book_id)
           FROM book_catalog b {} GROUP BY 1 ORDER BY 2 DESC'''.format(where),
        tuple(params) if params else None
    )


def borrowings_trend(start_date=None, end_date=None, borrow_type=None,
                     departments=None):
    parts, params = _range_clause('c.borrow_date', start_date, end_date)
    joins = ''
    if borrow_type:
        parts.append('c.borrow_type = %s')
        params.append(borrow_type)
    dept_clause, dept_params = _department_clause(departments, 'br', 'r')
    if dept_clause:
        joins = (' JOIN borrowers br ON br.borrower_id = c.borrower_id'
                 ' JOIN user_accounts u ON br.user_id = u.user_id'
                 ' JOIN roles r ON u.role_id = r.role_id')
        parts.append(dept_clause)
        params.extend(dept_params)
    where = 'WHERE ' + ' AND '.join(parts) if parts else ''
    return db.fetch_all(
        '''SELECT c.borrow_date, COUNT(*)
           FROM circulation_records c{} {} GROUP BY c.borrow_date ORDER BY c.borrow_date'''.format(joins, where),
        tuple(params) if params else None
    )


def overdue_trend(start_date=None, end_date=None, borrow_type=None,
                  departments=None):
    parts, params = _range_clause('c.borrow_date', start_date, end_date)
    joins = ''
    if borrow_type:
        parts.append('c.borrow_type = %s')
        params.append(borrow_type)
    dept_clause, dept_params = _department_clause(departments, 'br', 'r')
    if dept_clause:
        joins = (' JOIN borrowers br ON br.borrower_id = c.borrower_id'
                 ' JOIN user_accounts u ON br.user_id = u.user_id'
                 ' JOIN roles r ON u.role_id = r.role_id')
        parts.append(dept_clause)
        params.extend(dept_params)
    parts.append("c.transaction_status = 'overdue'")
    return db.fetch_all(
        '''SELECT c.borrow_date, COUNT(*) FROM circulation_records c{}
           WHERE {} GROUP BY c.borrow_date ORDER BY c.borrow_date'''.format(joins, ' AND '.join(parts)),
        tuple(params)
    )


def top_borrowed_categories(start_date=None, end_date=None, limit=6, borrow_type=None):
    parts, params = _range_clause('c.borrow_date', start_date, end_date)
    if borrow_type:
        parts.append('c.borrow_type = %s')
        params.append(borrow_type)
    where = 'WHERE ' + ' AND '.join(parts) if parts else ''
    params.append(limit)
    return db.fetch_all(
        '''SELECT COALESCE(NULLIF(b.subject_classification, ''), 'Others'),
                  COUNT(c.circulation_id)
           FROM circulation_records c
           JOIN book_catalog b ON c.book_id = b.book_id
           {} GROUP BY 1 ORDER BY 2 DESC LIMIT %s'''.format(where),
        tuple(params)
    )


def borrowings_by_user_type(start_date=None, end_date=None, roles=None,
                              borrow_type=None, departments=None):
    parts, params = _range_clause('c.borrow_date', start_date, end_date)
    roles = [r.strip() for r in (roles or []) if r and r.strip()]
    if roles:
        parts.append('r.role_name IN ({})'.format(', '.join(['%s'] * len(roles))))
        params.extend(roles)
    if borrow_type:
        parts.append('c.borrow_type = %s')
        params.append(borrow_type)
    dept_clause, dept_params = _department_clause(departments, 'b', 'r')
    if dept_clause:
        parts.append(dept_clause)
        params.extend(dept_params)
    where = 'WHERE ' + ' AND '.join(parts) if parts else ''
    return db.fetch_all(
        '''SELECT r.role_name, COUNT(c.circulation_id)
           FROM circulation_records c
           JOIN borrowers b ON c.borrower_id = b.borrower_id
           JOIN user_accounts u ON b.user_id = u.user_id
           JOIN roles r ON u.role_id = r.role_id
           {} GROUP BY r.role_name ORDER BY 2 DESC'''.format(where),
        tuple(params) if params else None
    )


def circulation_overview(start_date=None, end_date=None, departments=None):
    """Return (total, active_borrowers, overdue, avg_loan_days, return_rate, new_additions).

    Positional tuple; callers index by position per the module tuple contract.
    departments optionally scopes loan aggregates to borrower program(s),
    matching the program_label logic (handles 'No program'/'Admin'/'Librarian').
    New additions always count titles and ignore the department filter.
    """
    dept_clause, dept_params = _department_clause(departments, 'br', 'r')
    joins = ''
    if dept_clause:
        joins = (' JOIN borrowers br ON br.borrower_id = circulation_records.borrower_id'
                 ' JOIN user_accounts u ON br.user_id = u.user_id'
                 ' JOIN roles r ON u.role_id = r.role_id')
    parts, params = _range_clause('borrow_date', start_date, end_date)
    if dept_clause:
        parts.append(dept_clause)
        params.extend(dept_params)
    where = 'WHERE ' + ' AND '.join(parts) if parts else ''
    base = 'FROM circulation_records{} {}'.format(joins, where)
    p = tuple(params) if params else None
    total = db.fetch_one(
        'SELECT COUNT(*) {}'.format(base), p)
    borrowers = db.fetch_one(
        'SELECT COUNT(DISTINCT circulation_records.borrower_id) {}'.format(base), p)

    def _and(cond):
        return (where + ' AND ' + cond) if where else ('WHERE ' + cond)

    overdue = db.fetch_one(
        'SELECT COUNT(*) FROM circulation_records{} {}'.format(
            joins, _and("transaction_status = 'overdue'")),
        p)
    avg_loan = db.fetch_one(
        'SELECT AVG(return_date - borrow_date) FROM circulation_records{} {}'.format(
            joins, _and('return_date IS NOT NULL')),
        p)
    returned = db.fetch_one(
        'SELECT COUNT(*) FROM circulation_records{} {}'.format(
            joins, _and("transaction_status = 'returned'")),
        p)
    # New additions filter on book_catalog.date_added with the same range.
    bparts, bparams = _range_clause('date_added', start_date, end_date)
    bwhere = 'WHERE catalog_status = \'active\'' + (
        ' AND ' + ' AND '.join(bparts) if bparts else '')
    added = db.fetch_one(
        'SELECT COUNT(*) FROM book_catalog {}'.format(bwhere),
        tuple(bparams) if bparams else None)
    t = total[0] if total else 0
    r = returned[0] if returned else 0
    rate = round(r / t * 100, 1) if t else 0.0
    try:
        raw_avg = avg_loan[0] if avg_loan and avg_loan[0] is not None else 0.0
        # DATE - DATE yields int days in Postgres; guard timedelta/Decimal too.
        if hasattr(raw_avg, 'total_seconds'):
            avg_days = raw_avg.total_seconds() / 86400
        else:
            avg_days = float(raw_avg)
    except (TypeError, ValueError):
        avg_days = 0.0
    return (
        t,
        borrowers[0] if borrowers else 0,
        overdue[0] if overdue else 0,
        round(avg_days, 1),
        rate,
        added[0] if added else 0,
    )


def top_borrowed_books_detailed(start_date=None, end_date=None, limit=5,
                                  borrow_type=None, departments=None):
    parts, params = _range_clause('c.borrow_date', start_date, end_date)
    joins = ''
    if borrow_type:
        parts.append('c.borrow_type = %s')
        params.append(borrow_type)
    dept_clause, dept_params = _department_clause(departments, 'br', 'r')
    if dept_clause:
        joins = (' JOIN borrowers br ON c.borrower_id = br.borrower_id'
                 ' JOIN user_accounts u ON br.user_id = u.user_id'
                 ' JOIN roles r ON u.role_id = r.role_id')
        parts.append(dept_clause)
        params.extend(dept_params)
    where = 'WHERE ' + ' AND '.join(parts) if parts else ''
    params.append(limit)
    return db.fetch_all(
        '''SELECT b.title, b.author, COUNT(c.circulation_id)
           FROM book_catalog b
           JOIN circulation_records c ON b.book_id = c.book_id{}
           {} GROUP BY b.book_id, b.title, b.author
           ORDER BY 3 DESC LIMIT %s'''.format(joins, where),
        tuple(params)
    )


def high_demand_titles(start_date=None, end_date=None, limit=5, borrow_type=None):
    """Return [(title, author, current_borrows)] for active loans ranked by demand."""
    parts, params = _range_clause('c.borrow_date', start_date, end_date)
    if borrow_type:
        parts.append('c.borrow_type = %s')
        params.append(borrow_type)
    parts.append("c.transaction_status IN ('active', 'overdue')")
    params.append(limit)
    return db.fetch_all(
        '''SELECT b.title, b.author, COUNT(c.circulation_id)
           FROM book_catalog b
           JOIN circulation_records c ON b.book_id = c.book_id
           WHERE {} GROUP BY b.book_id, b.title, b.author
           ORDER BY 3 DESC LIMIT %s'''.format(' AND '.join(parts)),
        tuple(params)
    )


def borrowings_by_weekday(start_date=None, end_date=None):
    """Return [(weekday_name, count)] Monday-first for staffing forecasts."""
    parts, params = _range_clause('borrow_date', start_date, end_date)
    where = 'WHERE ' + ' AND '.join(parts) if parts else ''
    rows = db.fetch_all(
        '''SELECT EXTRACT(DOW FROM borrow_date)::int AS dow, COUNT(*)
           FROM circulation_records {} GROUP BY dow'''.format(where),
        tuple(params) if params else None,
    )
    names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
             'Saturday', 'Sunday']
    by_dow = {}
    for r in rows or []:
        try:
            by_dow[int(r[0])] = int(r[1] or 0)
        except (IndexError, TypeError, ValueError):
            continue
    # EXTRACT(DOW) is 0=Sunday; rotate Monday-first.
    return [(names[(d + 6) % 7], by_dow.get(d, 0)) for d in (1, 2, 3, 4, 5, 6, 0)]


def title_demand_gaps(limit=8):
    """Return [(title, author, waiting, available)] for pressured titles.

    waiting = reservations waiting/allocated; available = copies with no
    active loan. Ordered by waiters descending.
    """
    return db.fetch_all(
        '''SELECT b.title, b.author,
                  COUNT(DISTINCT CASE WHEN r.reservation_status IN ('waiting', 'allocated')
                                      THEN r.reservation_id END) AS waiting,
                  COUNT(DISTINCT a.accession_id)
                  - COUNT(DISTINCT CASE WHEN c.transaction_status IN ('active', 'overdue')
                                        THEN c.accession_id END) AS available
           FROM book_catalog b
           LEFT JOIN accession_log a ON a.book_id = b.book_id
           LEFT JOIN circulation_records c ON c.accession_id = a.accession_id
                AND c.transaction_status IN ('active', 'overdue')
           LEFT JOIN reservation_queue r ON r.book_id = b.book_id
           WHERE b.catalog_status = 'active'
           GROUP BY b.book_id, b.title, b.author
           HAVING COUNT(DISTINCT CASE WHEN r.reservation_status IN ('waiting', 'allocated')
                                      THEN r.reservation_id END) > 0
           ORDER BY waiting DESC LIMIT %s''',
        (limit,),
    )


def count_accessions(start_date=None, end_date=None):
    parts, params = _range_clause('date_accessioned', start_date, end_date)
    where = 'WHERE ' + ' AND '.join(parts) if parts else ''
    row = db.fetch_one(
        'SELECT COUNT(*) FROM accession_log {}'.format(where),
        tuple(params) if params else None,
    )
    return row[0] if row else 0


def recent_circulation(limit=10, departments=None, start_date=None, end_date=None):
    parts, params = _range_clause('c.borrow_date', start_date, end_date)
    dept_clause, dept_params = _department_clause(departments, 'br', 'r')
    if dept_clause:
        parts.append(dept_clause)
        params.extend(dept_params)
    where = 'WHERE ' + ' AND '.join(parts) if parts else ''
    params.append(limit)
    return db.fetch_all(
        '''SELECT c.borrow_date, c.circulation_id, u.full_name, r.role_name,
                  b.title, b.author, c.transaction_type, c.due_date, c.transaction_status
           FROM circulation_records c
           JOIN book_catalog b ON c.book_id = b.book_id
           JOIN borrowers br ON c.borrower_id = br.borrower_id
           JOIN user_accounts u ON br.user_id = u.user_id
           JOIN roles r ON u.role_id = r.role_id
           {} ORDER BY c.borrow_date DESC LIMIT %s'''.format(where),
        tuple(params)
    )


def recent_collection_status(limit=10):
    return db.fetch_all(
        '''SELECT a.accession_number, b.title,
                  COALESCE(NULLIF(b.subject_classification, ''), 'Others'),
                  COALESCE(i.inventory_state, 'available'),
                  c.transaction_status, u.full_name, c.due_date
           FROM accession_log a
           JOIN book_catalog b ON a.book_id = b.book_id
           LEFT JOIN inventory_status i ON i.accession_id = a.accession_id
           LEFT JOIN circulation_records c ON c.accession_id = a.accession_id
               AND c.transaction_status IN ('active', 'overdue')
           LEFT JOIN borrowers br ON c.borrower_id = br.borrower_id
           LEFT JOIN user_accounts u ON br.user_id = u.user_id
           WHERE b.catalog_status = 'active'
           ORDER BY a.accession_id DESC LIMIT %s''',
        (limit,)
    )