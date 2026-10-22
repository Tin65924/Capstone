import json

from app.database import db
from app.settings.models import library_today

# Overdue-lookalike clause shared by the analytics aggregates. due_date
# rows hold naive Asia/Manila (PHT) dates while Postgres CURRENT_DATE
# is UTC on Render, so the comparison binds library_today() (a %s
# placeholder the caller must append to its params tuple).
_OVERDUE_CLAUSE = ("(c.transaction_status = 'overdue'"
                   " OR (c.transaction_status = 'active'"
                   "     AND c.due_date::date < (%s)::date))")


def _cat_pieces(book_alias='b'):
    """Category label/join fragments gated on the migrated schema.

    Returns (label_expr, join_sql, name_expr): the canonical vocabulary
    label (LEFT JOIN categories) when the multi-category tables exist,
    else the legacy free-text subject expression with no join. Keeps
    analytics rendering on databases whose startup migration has not
    applied yet. Any gate failure fails open to the legacy shape.
    """
    try:
        from app.cataloging.models import multi_cat_available
        if multi_cat_available():
            return (
                "COALESCE(NULLIF(ct.name, ''), NULLIF({a}.subject_classification, ''), 'Others')".format(a=book_alias),
                ' LEFT JOIN categories ct ON ct.category_id = {a}.category_id'.format(a=book_alias),
                'COALESCE(ct.name, {a}.subject_classification)'.format(a=book_alias),
            )
    except Exception:
        pass
    return (
        "COALESCE(NULLIF({a}.subject_classification, ''), 'Others')".format(a=book_alias),
        '',
        '{a}.subject_classification'.format(a=book_alias),
    )


def _date_filter(clause_prefix, column):
    """Build WHERE fragments bounding a date column between start and end. It applies the shared date-range and department filters so dashboard, chart, and export views stay consistent, querying live tables on each call.
    
    Args:
        clause_prefix: See implementation for usage.
        column: See implementation for usage.
    
    Returns:
        Query rows or computed payload for the caller (see implementation for shape)."""
    parts, params = [], []
    if clause_prefix.get('start') is not None:
        parts.append('{} >= %s'.format(column))
        params.append(clause_prefix['start'])
    if clause_prefix.get('end') is not None:
        parts.append('{} <= %s'.format(column))
        params.append(clause_prefix['end'])
    return parts, params


def _normalize_departments(departments):
    """Normalize the departments filter into a clean list of names. It applies the shared date-range and department filters so dashboard, chart, and export views stay consistent, querying live tables on each call.
    
    Args:
        departments: Program names to filter by, or None for all programs.
    
    Returns:
        Query rows or computed payload for the caller (see implementation for shape)."""
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
    """Count borrow transactions grouped by program label for the bar chart. It applies the shared date-range and department filters so dashboard, chart, and export views stay consistent, querying live tables on each call.
    
    Args:
        start_date: Start of the date window, or None for open-ended.
        end_date: End of the date window, or None for open-ended.
        departments: Program names to filter by, or None for all programs.
        borrow_type: Optional 'daily' or 'overnight' loan filter.
    
    Returns:
        Query rows or computed payload for the caller (see implementation for shape)."""
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


# Program label shared by the department analytics below: the borrower's
# department, or the staff role / 'No program' fallback for blank ones.
_PROGRAM_LABEL = """COALESCE(NULLIF(b.department, ''),
    CASE WHEN r.role_name IN ('Admin', 'Librarian') THEN r.role_name
         ELSE 'No program' END)"""

# E-book analogue: logged-in readers follow _PROGRAM_LABEL; visitors who
# are not signed in are 'Offline Reader' instead of a made-up program.
_EBOOK_PROGRAM_LABEL = """CASE WHEN e.user_id IS NULL THEN 'Offline Reader'
     ELSE COALESCE(NULLIF(b.department, ''),
         CASE WHEN r.role_name IN ('Admin', 'Librarian') THEN r.role_name
              ELSE 'No program' END) END"""


def _program_joins():
    """Return the shared JOIN fragment linking circulation to borrower, account, and role. It applies the shared date-range and department filters so dashboard, chart, and export views stay consistent, querying live tables on each call.
    
    Args:
        None.
    
    Returns:
        Query rows or computed payload for the caller (see implementation for shape)."""
    return (' JOIN borrowers b ON b.borrower_id = c.borrower_id'
            ' JOIN user_accounts u ON b.user_id = u.user_id'
            ' JOIN roles r ON u.role_id = r.role_id')


def overdue_by_department(start_date=None, end_date=None, departments=None):
    """Overdue loans grouped by department (real split, not a mix reuse)."""
    # Matches circulation/Overview: active-but-past-due counts as overdue
    # because nothing ever flips transaction_status to 'overdue' automatically.
    parts, params = _range_clause('c.borrow_date', start_date, end_date)
    parts.append(_OVERDUE_CLAUSE)
    params.append(library_today())
    clause, cparams = _department_clause(departments, 'b', 'r')
    if clause:
        parts.append(clause)
        params.extend(cparams)
    where = 'WHERE ' + ' AND '.join(parts) if parts else ''
    return db.fetch_all(
        '''SELECT {}, COUNT(c.circulation_id) as total
           FROM circulation_records c{} {} GROUP BY 1 ORDER BY total DESC'''.format(
            _PROGRAM_LABEL, _program_joins(), where),
        tuple(params) if params else None
    )


def borrowers_by_department(start_date=None, end_date=None, departments=None):
    """Distinct active borrowers grouped by department."""
    parts, params = _range_clause('c.borrow_date', start_date, end_date)
    clause, cparams = _department_clause(departments, 'b', 'r')
    if clause:
        parts.append(clause)
        params.extend(cparams)
    where = 'WHERE ' + ' AND '.join(parts) if parts else ''
    return db.fetch_all(
        '''SELECT {}, COUNT(DISTINCT c.borrower_id) as total
           FROM circulation_records c{} {} GROUP BY 1 ORDER BY total DESC'''.format(
            _PROGRAM_LABEL, _program_joins(), where),
        tuple(params) if params else None
    )


def department_summary(start_date=None, end_date=None, departments=None):
    """One row per department: (program, borrowings, borrowers, overdue).

    Powers the Department Leaderboard: every leaderboard column comes
    from this single query.
    """
    parts, params = _range_clause('c.borrow_date', start_date, end_date)
    clause, cparams = _department_clause(departments, 'b', 'r')
    if clause:
        parts.append(clause)
        params.extend(cparams)
    where = 'WHERE ' + ' AND '.join(parts) if parts else ''
    return db.fetch_all(
        '''SELECT {},
                  COUNT(c.circulation_id) as borrowings,
                  COUNT(DISTINCT c.borrower_id) as borrowers,
                   SUM(CASE WHEN c.transaction_status = 'overdue' OR (c.transaction_status = 'active' AND c.due_date::date < (%s)::date)
                           THEN 1 ELSE 0 END) as overdue
           FROM circulation_records c{} {} GROUP BY 1 ORDER BY borrowings DESC'''.format(
            _PROGRAM_LABEL, _program_joins(), where),
        tuple([library_today()] + params)
    )


def utilization_rate(start_date=None, end_date=None):
    """Compute the share of copies currently on loan as a utilization percentage. It applies the shared date-range and department filters so dashboard, chart, and export views stay consistent, querying live tables on each call.
    
    Args:
        start_date: Start of the date window, or None for open-ended.
        end_date: End of the date window, or None for open-ended.
    
    Returns:
        Query rows or computed payload for the caller (see implementation for shape)."""
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
    """List the most borrowed titles by loan count for the top-titles table. It applies the shared date-range and department filters so dashboard, chart, and export views stay consistent, querying live tables on each call.
    
    Args:
        start_date: Start of the date window, or None for open-ended.
        end_date: End of the date window, or None for open-ended.
        limit: Maximum rows to return.
    
    Returns:
        Query rows or computed payload for the caller (see implementation for shape)."""
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


def underutilized_titles(start_date=None, end_date=None, limit=10):
    """List titles with the fewest loans to surface underused stock. It applies the shared date-range and department filters so dashboard, chart, and export views stay consistent, querying live tables on each call.
    
    Args:
        start_date: Start of the date window, or None for open-ended.
        end_date: End of the date window, or None for open-ended.
        limit: Maximum rows to return.
    
    Returns:
        Query rows or computed payload for the caller (see implementation for shape)."""
    parts, params = _date_filter({'start': start_date, 'end': end_date}, 'c.borrow_date')
    on_cond = ' AND ' + ' AND '.join(parts) if parts else ''
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 10
    limit = max(1, min(limit, 50))
    params = list(params) + [limit]
    return db.fetch_all(
        '''SELECT bc.title FROM book_catalog bc
           LEFT JOIN circulation_records c ON bc.book_id = c.book_id{}
           GROUP BY bc.book_id, bc.title HAVING COUNT(c.circulation_id) = 0
           ORDER BY bc.title ASC LIMIT %s'''.format(on_cond),
        tuple(params)
    )


# Every report_type ever written to analytics_cache: the four board KPIs
# plus every dashboard export section. Single source of truth for the
# table CHECK (see schema.sql and database.run_schema): any exportable
# KPI missing here fails the INSERT and silently drops its audit
# snapshot. A test asserts routes.EXPORTABLE_KPIS stays a subset.
ANALYTICS_REPORT_TYPES = (
    'books_borrowed_per_program', 'utilization_rate',
    'most_borrowed_titles', 'underutilized_titles',
    'online_resource_usage',
    'trend_borrowings', 'trend_overdue',
    'trend_borrowings_by_program', 'trend_overdue_by_program',
    'top_categories', 'top_categories_by_program',
    'peak_periods', 'top_books', 'top_books_by_program',
    'fines_by_book', 'high_demand', 'by_user_type',
    'collection_by_category', 'copies_by_status',
    'recent_circulation', 'recent_collection',
    'circulation_summary',
    'borrowers_by_department', 'overdue_by_department',
    'department_leaderboard',
    'top_requested_titles', 'requests_by_role',
    'requests_trend', 'requests_by_program',
    'ebook_trend', 'top_ebooks',
)


def save_report_snapshot(report_type, filter_params, kpi_data, generated_by):
    """Persist a generated report payload to the analytics cache for reuse. It applies the shared date-range and department filters so dashboard, chart, and export views stay consistent, querying live tables on each call.
    
    Args:
        report_type: See implementation for usage.
        filter_params: See implementation for usage.
        kpi_data: See implementation for usage.
        generated_by: See implementation for usage.
    
    Returns:
        Query rows or computed payload for the caller (see implementation for shape)."""
    return db.execute(
        '''INSERT INTO analytics_cache (report_type, filter_params, kpi_data, generated_by)
           VALUES (%s, %s, %s, %s)''',
        (report_type, json.dumps(filter_params), json.dumps(kpi_data), generated_by)
    )


# ---------------------------------------------------------------------------
# Riverside dashboard cache (perf batch #4).
#
# compute_dashboard() fans out to ~20 aggregate queries; the analytics page
# and its JSON endpoint both call it per load. Cache the JSON-serializable
# payload in analytics_cache (report_type 'circulation_summary', already in
# the table CHECK) keyed by the exact filter set, with a TTL so dashes stay
# reasonably fresh. Reads/writes are best-effort â€” any failure
# degrades to uncached compute, never a 500. Pruning keeps the table bounded.
# ---------------------------------------------------------------------------

DASHBOARD_CACHE_TYPE = 'circulation_summary'
# Neon adds ~100-200ms round-trip latency per query, so a cold dashboard
# recompute costs ~10s; a longer TTL keeps hits cheap without lying about
# the data beyond what a staff dashboard tolerates.
DASHBOARD_CACHE_TTL_SECONDS = 900


def _cache_fresh(generated_date, ttl_seconds):
    """True when a cache timestamp is within TTL. Unparseable â†’ stale."""
    from datetime import datetime, timedelta
    try:
        if hasattr(generated_date, 'year'):
            stamped = generated_date.replace(tzinfo=None)
        else:
            stamped = datetime.fromisoformat(str(generated_date)[:19])
    except (TypeError, ValueError):
        return False
    try:
        return datetime.now() - stamped < timedelta(seconds=int(ttl_seconds))
    except (TypeError, ValueError):
        return False


def get_dashboard_cache(filter_params, ttl_seconds=DASHBOARD_CACHE_TTL_SECONDS):
    """Freshest cached dashboard payload for filter_params, or None."""
    row = db.fetch_one(
        '''SELECT kpi_data, generated_date FROM analytics_cache
           WHERE report_type = %s AND filter_params = %s::jsonb
           ORDER BY generated_date DESC LIMIT 1''',
        (DASHBOARD_CACHE_TYPE, json.dumps(filter_params))
    )
    if not row:
        return None
    try:
        payload, stamped = row[0], row[1]
    except (IndexError, TypeError):
        return None
    if not _cache_fresh(stamped, ttl_seconds):
        return None
    if isinstance(payload, str):
        try:
            return json.loads(payload)
        except (TypeError, ValueError):
            return None
    return payload


def get_dashboard_cache_stale(filter_params):
    """Cached dashboard payload regardless of TTL, or None.

    Used by routes.compute_dashboard to serve an expired entry instantly
    while it is recomputed in the background (serve-stale-then-refresh);
    filters out nothing except absent or unparseable rows.
    """
    row = db.fetch_one(
        '''SELECT kpi_data, generated_date FROM analytics_cache
           WHERE report_type = %s AND filter_params = %s::jsonb
           ORDER BY generated_date DESC LIMIT 1''',
        (DASHBOARD_CACHE_TYPE, json.dumps(filter_params))
    )
    if not row or len(row) < 2:
        return None
    payload = row[0]
    if not isinstance(payload, (str, dict)):
        return None
    if isinstance(payload, str):
        try:
            return json.loads(payload)
        except (TypeError, ValueError):
            return None
    return payload


def set_dashboard_cache(filter_params, payload, generated_by=None):
    """Store a dashboard payload and prune entries older than a day."""
    db.execute(
        '''DELETE FROM analytics_cache
           WHERE report_type = %s AND generated_date < NOW() - INTERVAL '1 day' ''',
        (DASHBOARD_CACHE_TYPE,)
    )
    return save_report_snapshot(DASHBOARD_CACHE_TYPE, filter_params, payload, generated_by)


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
#     borrowed -> Very Good, damaged -> Fair, lost -> Poor.
#   - "Peak periods by hour" is served as borrowings by day because
#     borrow_date is a DATE with no time-of-day column.
# ---------------------------------------------------------------------------

def _range_clause(column, start_date, end_date):
    """Build WHERE fragments bounding a timestamp column between start and end dates. It applies the shared date-range and department filters so dashboard, chart, and export views stay consistent, querying live tables on each call.
    
    Args:
        column: See implementation for usage.
        start_date: Start of the date window, or None for open-ended.
        end_date: End of the date window, or None for open-ended.
    
    Returns:
        Query rows or computed payload for the caller (see implementation for shape)."""
    parts, params = [], []
    if start_date is not None:
        parts.append('{} >= %s'.format(column))
        params.append(start_date)
    if end_date is not None:
        parts.append('{} <= %s'.format(column))
        params.append(end_date)
    return parts, params


def count_active_titles():
    """Count active catalog titles for headline KPI cards. It applies the shared date-range and department filters so dashboard, chart, and export views stay consistent, querying live tables on each call.
    
    Args:
        None.
    
    Returns:
        Query rows or computed payload for the caller (see implementation for shape)."""
    row = db.fetch_one(
        "SELECT COUNT(*) FROM book_catalog WHERE catalog_status = 'active'"
    )
    return row[0] if row else 0


def count_total_copies():
    """Count all physical copies for headline KPI cards. It applies the shared date-range and department filters so dashboard, chart, and export views stay consistent, querying live tables on each call.
    
    Args:
        None.
    
    Returns:
        Query rows or computed payload for the caller (see implementation for shape)."""
    row = db.fetch_one(
        '''SELECT COUNT(*) FROM accession_log a
           JOIN book_catalog b ON a.book_id = b.book_id
           WHERE b.catalog_status = 'active' '''
    )
    return row[0] if row else 0


def count_circulation_status(start_date=None, end_date=None, borrow_type=None):
    """Return [(transaction_status, count)] for active/returned/overdue.

    Active-but-past-due counts as 'overdue' (nothing ever flips the status
    automatically; circulation/Overview uses the same rule), so 'active'
    means still out but not yet due and the two buckets stay exclusive.
    """
    parts, params = _range_clause('borrow_date', start_date, end_date)
    if borrow_type:
        parts.append('borrow_type = %s')
        params.append(borrow_type)
    # The overdue CASE (and its PHT cutoff placeholder) sits in the
    # SELECT list, before any WHERE fragment, so its param goes first.
    where = 'WHERE ' + ' AND '.join(parts) if parts else ''
    return db.fetch_all(
        '''SELECT CASE WHEN transaction_status = 'overdue' OR (transaction_status = 'active'
                          AND due_date::date < (%s)::date)
                       THEN 'overdue' ELSE transaction_status END, COUNT(*)
           FROM circulation_records {} GROUP BY 1'''.format(where),
        tuple([library_today()] + params)
    )


def count_lost_flagged(start_date=None, end_date=None):
    """Count copies flagged lost via loan or inventory channels. It applies the shared date-range and department filters so dashboard, chart, and export views stay consistent, querying live tables on each call.
    
    Args:
        start_date: Start of the date window, or None for open-ended.
        end_date: End of the date window, or None for open-ended.
    
    Returns:
        Query rows or computed payload for the caller (see implementation for shape)."""
    parts, params = _range_clause('borrow_date', start_date, end_date)
    parts.append('lost_flag = TRUE')
    return db.fetch_one(
        'SELECT COUNT(*) FROM circulation_records WHERE ' + ' AND '.join(parts),
        tuple(params)
    )


def count_reservations():
    """Count reservation rows for headline KPI cards. It applies the shared date-range and department filters so dashboard, chart, and export views stay consistent, querying live tables on each call.
    
    Args:
        None.
    
    Returns:
        Query rows or computed payload for the caller (see implementation for shape)."""
    row = db.fetch_one(
        """SELECT COUNT(*) FROM reservation_queue
           WHERE reservation_status IN ('waiting', 'allocated')"""
    )
    return row[0] if row else 0


def inventory_state_counts():
    """Count inventory rows grouped by state for the condition breakdown. It applies the shared date-range and department filters so dashboard, chart, and export views stay consistent, querying live tables on each call.
    
    Args:
        None.
    
    Returns:
        Query rows or computed payload for the caller (see implementation for shape)."""
    return db.fetch_all(
        'SELECT inventory_state, COUNT(*) FROM inventory_status GROUP BY inventory_state'
    )


def copies_by_status_summary(start_date=None, end_date=None, borrow_type=None):
    """Return [(status, copies)] for the Copies-by-Status chart/export.

    Available = active-catalog copies minus borrowed, overdue, reserved,
    and lost/damaged (including lost-flagged loans and missing)
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
    lost_damaged = inv.get('lost', 0) + inv.get('damaged', 0) + inv.get('missing', 0) + lost_flagged
    available = max(total - borrowed - overdue - reserved - lost_damaged, 0)
    return [('Available', available), ('Borrowed', borrowed), ('Reserved', reserved),
            ('Overdue', overdue), ('Lost / Damaged', lost_damaged)]


def collection_by_category(start_date=None, end_date=None, categories=None):
    """Return [(category, titles)] grouped by canonical category name.

    Groups through the categories vocabulary (LEFT JOIN) with the
    legacy free-text subject as fallback, so case variants of one
    subject collapse to a single row. Unlinked blanks report as
    'Others'. On unmigrated databases the legacy text grouping applies.

    categories optionally restricts to the named categories
    (case-insensitive; 'Others' matches blank classifications).
    """
    parts, params = _range_clause('b.date_added', start_date, end_date)
    label_expr, join_sql, name_expr = _cat_pieces('b')
    categories = [c.strip() for c in (categories or []) if c and c.strip()]
    if categories:
        conds = []
        exact = [c for c in categories if c.lower() != 'others']
        if exact:
            conds.append('LOWER({}) IN ({})'.format(
                name_expr, ', '.join(['%s'] * len(exact))))
            params.extend([c.lower() for c in exact])
        if len(exact) != len(categories):
            conds.append("(b.subject_classification IS NULL OR b.subject_classification = '')")
        parts.append('(' + ' OR '.join(conds) + ')')
    where = 'WHERE b.catalog_status = \'active\'' + (
        ' AND ' + ' AND '.join(parts) if parts else '')
    return db.fetch_all(
        '''SELECT {}, COUNT(DISTINCT b.book_id)
           FROM book_catalog b{} {} GROUP BY 1 ORDER BY 2 DESC'''.format(label_expr, join_sql, where),
        tuple(params) if params else None
    )


def borrowings_trend(start_date=None, end_date=None, borrow_type=None,
                     departments=None):
    """Aggregate borrow counts per day for the trend line chart. It applies the shared date-range and department filters so dashboard, chart, and export views stay consistent, querying live tables on each call.
    
    Args:
        start_date: Start of the date window, or None for open-ended.
        end_date: End of the date window, or None for open-ended.
        borrow_type: Optional 'daily' or 'overnight' loan filter.
        departments: Program names to filter by, or None for all programs.
    
    Returns:
        Query rows or computed payload for the caller (see implementation for shape)."""
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
    """Aggregate overdue counts per day for the overdue trend chart. It applies the shared date-range and department filters so dashboard, chart, and export views stay consistent, querying live tables on each call.
    
    Args:
        start_date: Start of the date window, or None for open-ended.
        end_date: End of the date window, or None for open-ended.
        borrow_type: Optional 'daily' or 'overnight' loan filter.
        departments: Program names to filter by, or None for all programs.
    
    Returns:
        Query rows or computed payload for the caller (see implementation for shape)."""
    # Group by due_date (not borrow_date): "daily overdue counts" means
    # when items became overdue. COALESCE covers legacy rows with NULL due.
    parts, params = _range_clause('COALESCE(c.due_date, c.borrow_date)', start_date, end_date)
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
    # Include active-but-past-due: nothing flips status to 'overdue' automatically,
    # circulation/Overview counts past-due loans even while still 'active'.
    parts.append(_OVERDUE_CLAUSE)
    params.append(library_today())
    return db.fetch_all(
        '''SELECT COALESCE(c.due_date, c.borrow_date)::date, COUNT(*) FROM circulation_records c{}
           WHERE {} GROUP BY 1 ORDER BY 1'''.format(joins, ' AND '.join(parts)),
        tuple(params)
    )


def borrowings_trend_by_program(start_date=None, end_date=None, borrow_type=None,
                                departments=None):
    """Return [(borrow_date, program_label, count)] daily trend split by program.

    Powers the "Borrowings Trend by Program" multi-line graph so every point
    shows which program/department it belongs to. Same program_label logic
    as books_borrowed_per_program (borrower department with Admin/Librarian/
    'No program' fallback for blank departments).
    """
    parts, params = _range_clause('c.borrow_date', start_date, end_date)
    if borrow_type:
        parts.append('c.borrow_type = %s')
        params.append(borrow_type)
    dept_clause, dept_params = _department_clause(departments, 'b', 'r')
    if dept_clause:
        parts.append(dept_clause)
        params.extend(dept_params)
    where = 'WHERE ' + ' AND '.join(parts) if parts else ''
    return db.fetch_all(
        '''SELECT c.borrow_date, {}, COUNT(c.circulation_id)
           FROM circulation_records c{}
           {} GROUP BY c.borrow_date, 2 ORDER BY c.borrow_date, 2'''.format(
            _PROGRAM_LABEL, _program_joins(), where),
        tuple(params) if params else None
    )


def borrowings_by_program_on_date(day, borrow_type=None, departments=None):
    """Return [(program_label, count)] borrowings on one calendar day split by program.

    Powers the Borrowings Trend dot drill-down: clicking a trend point
    shows which programs borrowed on that date. Same program_label logic
    as borrowings_trend_by_program. `day` is 'YYYY-MM-DD'; the ::date
    cast keeps TIMESTAMP and legacy DATE rows comparable.
    """
    parts = ['c.borrow_date::date = %s::date']
    params = [day]
    if borrow_type:
        parts.append('c.borrow_type = %s')
        params.append(borrow_type)
    dept_clause, dept_params = _department_clause(departments, 'b', 'r')
    if dept_clause:
        parts.append(dept_clause)
        params.extend(dept_params)
    return db.fetch_all(
        '''SELECT {}, COUNT(c.circulation_id)
           FROM circulation_records c{}
           WHERE {} GROUP BY 1 ORDER BY 2 DESC'''.format(
            _PROGRAM_LABEL, _program_joins(), ' AND '.join(parts)),
        tuple(params)
    )


def overdue_by_program_on_date(day):
    """Return [(program_label, count)] overdue items for one due date by program.

    Powers the Overdue Trend dot drill-down. Same overdue rule and
    due-date grouping as overdue_trend (active-but-past-due counts).
    """
    return db.fetch_all(
        '''SELECT {}, COUNT(c.circulation_id)
           FROM circulation_records c{}
           WHERE COALESCE(c.due_date, c.borrow_date)::date = %s::date
             AND {}
           GROUP BY 1 ORDER BY 2 DESC'''.format(
            _PROGRAM_LABEL, _program_joins(), _OVERDUE_CLAUSE),
        (day, library_today())
    )


def category_borrowings_by_program(category, start_date=None, end_date=None,
                                   borrow_type=None):
    """Return [(program_label, count)] borrows in one category by program.

    Powers the Top Borrowed Categories drill-down (donut slice / legend
    click). Category matches the card's canonical label expression, so
    'Others' covers blank classifications. Period-scoped like the card.
    """
    label_expr, join_sql, _ = _cat_pieces('bk')
    parts = ["{} = %s".format(label_expr)]
    params = [category]
    range_parts, range_params = _range_clause('c.borrow_date', start_date,
                                             end_date)
    parts.extend(range_parts)
    params.extend(range_params)
    if borrow_type:
        parts.append('c.borrow_type = %s')
        params.append(borrow_type)
    return db.fetch_all(
        '''SELECT {}, COUNT(c.circulation_id)
           FROM circulation_records c
           JOIN book_catalog bk ON c.book_id = bk.book_id{}{}
           WHERE {} GROUP BY 1 ORDER BY 2 DESC'''.format(
            _PROGRAM_LABEL, join_sql, _program_joins(), ' AND '.join(parts)),
        tuple(params)
    )


def fines_by_program_for_title(title, start_date=None, end_date=None):
    """Return [(program_label, total_fines, fine_count)] for one title by program.

    Powers the Books with Most Fines row drill-down. Same window and
    fine_amount > 0 rule as fines_by_book.
    """
    parts = ['bk.title = %s', 'c.fine_amount > 0']
    params = [title]
    range_parts, range_params = _range_clause('c.borrow_date', start_date,
                                             end_date)
    parts.extend(range_parts)
    params.extend(range_params)
    return db.fetch_all(
        '''SELECT {}, SUM(c.fine_amount), COUNT(c.circulation_id)
           FROM circulation_records c
           JOIN book_catalog bk ON c.book_id = bk.book_id{}
           WHERE {} GROUP BY 1 ORDER BY 2 DESC'''.format(
            _PROGRAM_LABEL, _program_joins(), ' AND '.join(parts)),
        tuple(params)
    )


def _request_program_joins():
    """Return the shared JOIN fragment linking requests to borrower, account, and role. It applies the shared date-range and department filters so dashboard, chart, and export views stay consistent, querying live tables on each call.
    
    Args:
        None.
    
    Returns:
        Query rows or computed payload for the caller (see implementation for shape)."""
    return (' JOIN borrowers b ON b.borrower_id = rr.requester_id'
            ' JOIN user_accounts u ON b.user_id = u.user_id'
            ' JOIN roles r ON u.role_id = r.role_id')


def requests_by_program_on_date(day):
    """Return [(program_label, count)] book requests for one day by program.

    Powers the Requests Over Time dot drill-down. Same pending +
    rejected scope as requests_trend so denied demand stays visible.
    """
    return db.fetch_all(
        '''SELECT {}, COUNT(rr.request_id)
           FROM request_records rr{}
           WHERE rr.request_date::date = %s::date
             AND rr.request_status IN ('pending_review', 'rejected')
           GROUP BY 1 ORDER BY 2 DESC'''.format(
            _PROGRAM_LABEL, _request_program_joins()),
        (day,)
    )


def requests_for_title_by_program(title, start_date=None, end_date=None):
    """Return [(program_label, count)] pending requests for one title by program.

    Powers the Student vs Faculty demand row drill-down (per-title
    program split). Same pending-only scope as top_requested_titles.
    """
    parts = ['rr.book_title = %s', "rr.request_status = 'pending_review'"]
    params = [title]
    range_parts, range_params = _range_clause('rr.request_date', start_date,
                                             end_date)
    parts.extend(range_parts)
    params.extend(range_params)
    return db.fetch_all(
        '''SELECT {}, COUNT(rr.request_id)
           FROM request_records rr{}
           WHERE {} GROUP BY 1 ORDER BY 2 DESC'''.format(
            _PROGRAM_LABEL, _request_program_joins(), ' AND '.join(parts)),
        tuple(params)
    )


def overdue_trend_by_program(start_date=None, end_date=None, borrow_type=None,
                             departments=None):
    """Return [(due_date, program_label, count)] overdue trend split by program."""
    parts, params = _range_clause('COALESCE(c.due_date, c.borrow_date)', start_date, end_date)
    if borrow_type:
        parts.append('c.borrow_type = %s')
        params.append(borrow_type)
    # Borrowers are aliased 'b' by _program_joins(); passing 'br' here
    # made every department-scoped overdue trend fail with
    # "missing FROM-clause entry for table br" (silently swallowed).
    dept_clause, dept_params = _department_clause(departments, 'b', 'r')
    if dept_clause:
        parts.append(dept_clause)
        params.extend(dept_params)
    parts.append(_OVERDUE_CLAUSE)
    params.append(library_today())
    return db.fetch_all(
        '''SELECT COALESCE(c.due_date, c.borrow_date)::date, {}, COUNT(c.circulation_id)
           FROM circulation_records c{}
           WHERE {} GROUP BY 1, 2 ORDER BY 1, 2'''.format(
            _PROGRAM_LABEL, _program_joins(), ' AND '.join(parts)),
        tuple(params)
    )


def top_books_program_breakdown(start_date=None, end_date=None, limit=20,
                                borrow_type=None, departments=None):
    """Return [(title, program_label, count)] top-book borrows split by program.

    Single query (no N+1): top titles crossed with the borrowing program so
    the "Top Borrowed Books" graph can label which program each borrow came
    from. Ordered by borrows descending.
    """
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 20
    limit = max(1, min(limit, 100))
    parts, params = _range_clause('c.borrow_date', start_date, end_date)
    if borrow_type:
        parts.append('c.borrow_type = %s')
        params.append(borrow_type)
    # Borrowers are aliased 'b' by _program_joins(); book_catalog takes
    # 'bk' so the two never collide (duplicate 'b' 500s on Postgres).
    dept_clause, dept_params = _department_clause(departments, 'b', 'r')
    if dept_clause:
        parts.append(dept_clause)
        params.extend(dept_params)
    where = 'WHERE ' + ' AND '.join(parts) if parts else ''
    params.append(limit)
    return db.fetch_all(
        '''SELECT bk.title, {}, COUNT(c.circulation_id)
           FROM circulation_records c
           JOIN book_catalog bk ON c.book_id = bk.book_id{} {} GROUP BY bk.title, 2
           ORDER BY 3 DESC LIMIT %s'''.format(_PROGRAM_LABEL, _program_joins(), where),
        tuple(params)
    )


def top_categories_by_program(start_date=None, end_date=None, limit=20,
                              borrow_type=None):
    """Return [(category, program_label, count)] borrows split by program."""
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 20
    limit = max(1, min(limit, 100))
    parts, params = _range_clause('c.borrow_date', start_date, end_date)
    if borrow_type:
        parts.append('c.borrow_type = %s')
        params.append(borrow_type)
    where = 'WHERE ' + ' AND '.join(parts) if parts else ''
    params.append(limit)
    label_expr, join_sql, _ = _cat_pieces('bk')
    return db.fetch_all(
        '''SELECT {},
                  {}, COUNT(c.circulation_id)
           FROM circulation_records c
           JOIN book_catalog bk ON c.book_id = bk.book_id{}{} {} GROUP BY 1, 2
           ORDER BY 3 DESC LIMIT %s'''.format(label_expr, _PROGRAM_LABEL, join_sql, _program_joins(), where),
        tuple(params)
    )


def fines_by_book(start_date=None, end_date=None, limit=10):
    """Return [(title, author, total_fines, fine_count)] highest-fine books first.

    Sums circulation_records.fine_amount per active-catalog title in the
    selected borrow_date window. Only rows with fine_amount > 0 count, so
    the "Books with Most Fines" table answers which book incurred the most
    fines. Amounts come back as Decimal/float; callers coerce for display.
    """
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 10
    limit = max(1, min(limit, 50))
    parts, params = _range_clause('c.borrow_date', start_date, end_date)
    parts.append('c.fine_amount > 0')
    where = 'WHERE ' + ' AND '.join(parts)
    params.append(limit)
    return db.fetch_all(
        '''SELECT b.title, b.author, SUM(c.fine_amount), COUNT(c.circulation_id)
           FROM circulation_records c
           JOIN book_catalog b ON c.book_id = b.book_id
           {} GROUP BY b.book_id, b.title, b.author
           ORDER BY SUM(c.fine_amount) DESC, COUNT(c.circulation_id) DESC
           LIMIT %s'''.format(where),
        tuple(params)
    )


def top_borrowed_categories(start_date=None, end_date=None, limit=6, borrow_type=None):
    """List top subject classifications by borrow volume for the pie chart. It applies the shared date-range and department filters so dashboard, chart, and export views stay consistent, querying live tables on each call.
    
    Args:
        start_date: Start of the date window, or None for open-ended.
        end_date: End of the date window, or None for open-ended.
        limit: Maximum rows to return.
        borrow_type: Optional 'daily' or 'overnight' loan filter.
    
    Returns:
        Query rows or computed payload for the caller (see implementation for shape)."""
    parts, params = _range_clause('c.borrow_date', start_date, end_date)
    if borrow_type:
        parts.append('c.borrow_type = %s')
        params.append(borrow_type)
    where = 'WHERE ' + ' AND '.join(parts) if parts else ''
    params.append(limit)
    label_expr, join_sql, _ = _cat_pieces('b')
    return db.fetch_all(
        '''SELECT {},
                  COUNT(c.circulation_id)
           FROM circulation_records c
           JOIN book_catalog b ON c.book_id = b.book_id{}
           {} GROUP BY 1 ORDER BY 2 DESC LIMIT %s'''.format(label_expr, join_sql, where),
        tuple(params)
    )


def borrowings_by_user_type(start_date=None, end_date=None, roles=None,
                              borrow_type=None, departments=None):
    """Count borrows grouped by role name for the user-type split. It applies the shared date-range and department filters so dashboard, chart, and export views stay consistent, querying live tables on each call.
    
    Args:
        start_date: Start of the date window, or None for open-ended.
        end_date: End of the date window, or None for open-ended.
        roles: See implementation for usage.
        borrow_type: Optional 'daily' or 'overnight' loan filter.
        departments: Program names to filter by, or None for all programs.
    
    Returns:
        Query rows or computed payload for the caller (see implementation for shape)."""
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
        """Perform the  and analytics operation. It applies the shared date-range and department filters so dashboard, chart, and export views stay consistent, querying live tables on each call.
        
        Args:
            cond: See implementation for usage.
        
        Returns:
            Query rows or computed payload for the caller (see implementation for shape)."""
        return (where + ' AND ' + cond) if where else ('WHERE ' + cond)

    overdue = db.fetch_one(
        'SELECT COUNT(*) FROM circulation_records{} {}'.format(
            joins, _and("(transaction_status = 'overdue' OR (transaction_status = 'active'"
                        " AND due_date::date < (%s)::date))")),
        (p + (library_today(),)) if p else (library_today(),))
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
    """List top titles with author and counts for the detailed top-books table. It applies the shared date-range and department filters so dashboard, chart, and export views stay consistent, querying live tables on each call.
    
    Args:
        start_date: Start of the date window, or None for open-ended.
        end_date: End of the date window, or None for open-ended.
        limit: Maximum rows to return.
        borrow_type: Optional 'daily' or 'overnight' loan filter.
        departments: Program names to filter by, or None for all programs.
    
    Returns:
        Query rows or computed payload for the caller (see implementation for shape)."""
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
    """Perform the count accessions analytics operation. It applies the shared date-range and department filters so dashboard, chart, and export views stay consistent, querying live tables on each call.
    
    Args:
        start_date: Start of the date window, or None for open-ended.
        end_date: End of the date window, or None for open-ended.
    
    Returns:
        Query rows or computed payload for the caller (see implementation for shape)."""
    parts, params = _range_clause('date_accessioned', start_date, end_date)
    where = 'WHERE ' + ' AND '.join(parts) if parts else ''
    row = db.fetch_one(
        'SELECT COUNT(*) FROM accession_log {}'.format(where),
        tuple(params) if params else None,
    )
    return row[0] if row else 0


def recent_circulation(limit=10, departments=None, start_date=None, end_date=None):
    """Perform the recent circulation analytics operation. It applies the shared date-range and department filters so dashboard, chart, and export views stay consistent, querying live tables on each call.
    
    Args:
        limit: Maximum rows to return.
        departments: Program names to filter by, or None for all programs.
        start_date: Start of the date window, or None for open-ended.
        end_date: End of the date window, or None for open-ended.
    
    Returns:
        Query rows or computed payload for the caller (see implementation for shape)."""
    parts, params = _range_clause('c.borrow_date', start_date, end_date)
    dept_clause, dept_params = _department_clause(departments, 'br', 'r')
    if dept_clause:
        parts.append(dept_clause)
        params.extend(dept_params)
    where = 'WHERE ' + ' AND '.join(parts) if parts else ''
    params.append(limit)
    return db.fetch_all(
        '''SELECT c.borrow_date, a.accession_number, u.full_name, r.role_name,
                   b.title, b.author, c.transaction_type, c.due_date, c.transaction_status
            FROM circulation_records c
            JOIN accession_log a ON a.accession_id = c.accession_id
            JOIN book_catalog b ON c.book_id = b.book_id
           JOIN borrowers br ON c.borrower_id = br.borrower_id
           JOIN user_accounts u ON br.user_id = u.user_id
           JOIN roles r ON u.role_id = r.role_id
           {} ORDER BY c.borrow_date DESC LIMIT %s'''.format(where),
        tuple(params)
    )


def recent_collection_status(limit=10):
    """Perform the recent collection status analytics operation. It applies the shared date-range and department filters so dashboard, chart, and export views stay consistent, querying live tables on each call.
    
    Args:
        limit: Maximum rows to return.
    
    Returns:
        Query rows or computed payload for the caller (see implementation for shape)."""
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


# ---------------------------------------------------------------------------
# Book Analytics (per-title traffic).
#
# One page shows the traffic of a specific book: headline totals, daily
# trend, breakdowns by program/user-type, copy states, and recent
# transactions.  All functions filter on book_catalog.book_id with %s
# placeholders and return positional tuples (SELECT order is the contract).
# ---------------------------------------------------------------------------

def search_books_for_analytics(query, limit=10):
    """Return [(book_id, title, author, category, year_published)].

    Matches book title, category (subject_classification), or accession
    number (via accession_log), plus author/ISBN for convenience.

    Only active titles; empty/blank queries return [] so the Book Analytics
    page shows nothing until the librarian searches or picks a book.
    """
    query = (query or '').strip()
    if not query:
        return []
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 10
    limit = max(1, min(limit, 50))
    pattern = '%' + query + '%'
    return db.fetch_all(
        '''SELECT DISTINCT b.book_id, b.title, b.author,
                  COALESCE(NULLIF(b.subject_classification, ''), 'Others'),
                  b.year_published
           FROM book_catalog b
           LEFT JOIN accession_log a ON a.book_id = b.book_id
           WHERE b.catalog_status = 'active'
             AND (b.title ILIKE %s OR b.author ILIKE %s OR b.isbn ILIKE %s
                  OR b.subject_classification ILIKE %s
                  OR a.accession_number ILIKE %s)
           ORDER BY b.title ASC LIMIT %s''',
        (pattern, pattern, pattern, pattern, pattern, limit)
    )


def get_book_for_analytics(book_id):
    """Return full catalog details for one active title.

    Positional tuple (contract â€” new columns are appended, never reordered):
    (book_id, title, author, category, year, copies,
     publisher, edition, isbn, call_number, material_type, description).

    ``year`` is ``year_published`` (the copyright date shown on book cards).
    """
    try:
        book_id = int(book_id)
    except (TypeError, ValueError):
        return None
    return db.fetch_one(
        '''SELECT b.book_id, b.title, b.author,
                  COALESCE(NULLIF(b.subject_classification, ''), 'Others'),
                  b.year_published,
                  (SELECT COUNT(*) FROM accession_log a WHERE a.book_id = b.book_id),
                  b.publisher, b.edition, b.isbn, b.call_number,
                  b.material_type, b.description
           FROM book_catalog b
           WHERE b.book_id = %s AND b.catalog_status = 'active' ''',
        (book_id,)
    )


def book_traffic_overview(book_id, start_date=None, end_date=None):
    """Return (total, active, overdue, returned, borrowers, avg_days, return_rate).

    Positional tuple; scoped to one book_id with an optional borrow_date
    range.  New-accession counts are intentionally excluded here.
    """
    try:
        book_id = int(book_id)
    except (TypeError, ValueError):
        return (0, 0, 0, 0, 0, 0.0, 0.0)
    parts, params = _range_clause('borrow_date', start_date, end_date)
    parts = ['book_id = %s'] + parts
    params = [book_id] + params
    where = 'WHERE ' + ' AND '.join(parts)
    p = tuple(params)

    def _and(cond):
        """Perform the  and analytics operation. It applies the shared date-range and department filters so dashboard, chart, and export views stay consistent, querying live tables on each call.
        
        Args:
            cond: See implementation for usage.
        
        Returns:
            Query rows or computed payload for the caller (see implementation for shape)."""
        return where + ' AND ' + cond

    total = db.fetch_one(
        'SELECT COUNT(*) FROM circulation_records {}'.format(where), p)
    active = db.fetch_one(
        'SELECT COUNT(*) FROM circulation_records {}'.format(
            _and("transaction_status = 'active'")), p)
    overdue = db.fetch_one(
        'SELECT COUNT(*) FROM circulation_records {}'.format(
            _and("(transaction_status = 'overdue' OR (transaction_status = 'active'"
                 " AND due_date::date < (%s)::date))")), p + (library_today(),))
    returned = db.fetch_one(
        'SELECT COUNT(*) FROM circulation_records {}'.format(
            _and("transaction_status = 'returned'")), p)
    borrowers = db.fetch_one(
        'SELECT COUNT(DISTINCT borrower_id) FROM circulation_records {}'.format(where), p)
    avg_loan = db.fetch_one(
        'SELECT AVG(return_date - borrow_date) FROM circulation_records {}'.format(
            _and('return_date IS NOT NULL')), p)
    t = total[0] if total else 0
    r = returned[0] if returned else 0
    rate = round(r / t * 100, 1) if t else 0.0
    try:
        raw_avg = avg_loan[0] if avg_loan and avg_loan[0] is not None else 0.0
        if hasattr(raw_avg, 'total_seconds'):
            avg_days = raw_avg.total_seconds() / 86400
        else:
            avg_days = float(raw_avg)
    except (TypeError, ValueError):
        avg_days = 0.0
    return (
        t,
        active[0] if active else 0,
        overdue[0] if overdue else 0,
        r,
        borrowers[0] if borrowers else 0,
        round(avg_days, 1),
        rate,
    )


def book_borrowings_trend(book_id, start_date=None, end_date=None):
    """Return [(borrow_date, count)] daily trend for one book."""
    try:
        book_id = int(book_id)
    except (TypeError, ValueError):
        return []
    parts, params = _range_clause('c.borrow_date', start_date, end_date)
    parts = ['c.book_id = %s'] + parts
    params = [book_id] + params
    return db.fetch_all(
        '''SELECT c.borrow_date, COUNT(*)
           FROM circulation_records c
           WHERE {} GROUP BY c.borrow_date ORDER BY c.borrow_date'''.format(
            ' AND '.join(parts)),
        tuple(params)
    )


def book_borrowed_per_program(book_id, start_date=None, end_date=None):
    """Return [(program, borrows)] for one book (program_label logic)."""
    try:
        book_id = int(book_id)
    except (TypeError, ValueError):
        return []
    parts, params = _range_clause('c.borrow_date', start_date, end_date)
    parts = ['c.book_id = %s'] + parts
    params = [book_id] + params
    return db.fetch_all(
        '''SELECT {}, COUNT(c.circulation_id) as total
           FROM circulation_records c{} WHERE {} GROUP BY 1 ORDER BY total DESC'''.format(
            _PROGRAM_LABEL, _program_joins(), ' AND '.join(parts)),
        tuple(params)
    )


def book_borrowings_by_user_type(book_id, start_date=None, end_date=None):
    """Return [(role_name, borrows)] for one book."""
    try:
        book_id = int(book_id)
    except (TypeError, ValueError):
        return []
    parts, params = _range_clause('c.borrow_date', start_date, end_date)
    parts = ['c.book_id = %s'] + parts
    params = [book_id] + params
    return db.fetch_all(
        '''SELECT r.role_name, COUNT(c.circulation_id)
           FROM circulation_records c
           JOIN borrowers b ON c.borrower_id = b.borrower_id
           JOIN user_accounts u ON b.user_id = u.user_id
           JOIN roles r ON u.role_id = r.role_id
           WHERE {} GROUP BY r.role_name ORDER BY 2 DESC'''.format(' AND '.join(parts)),
        tuple(params)
    )


def book_recent_circulation(book_id, limit=10, start_date=None, end_date=None):
    """Return recent [(date, accession_number, user, role, action, due, status)] for one book."""
    try:
        book_id = int(book_id)
    except (TypeError, ValueError):
        return []
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 10
    limit = max(1, min(limit, 50))
    parts, params = _range_clause('c.borrow_date', start_date, end_date)
    parts = ['c.book_id = %s'] + parts
    params = [book_id] + params
    params.append(limit)
    return db.fetch_all(
        '''SELECT c.borrow_date, a.accession_number, u.full_name, r.role_name,
                   c.transaction_type, c.due_date, c.transaction_status
            FROM circulation_records c
            JOIN accession_log a ON a.accession_id = c.accession_id
            JOIN borrowers br ON c.borrower_id = br.borrower_id
            JOIN user_accounts u ON br.user_id = u.user_id
            JOIN roles r ON u.role_id = r.role_id
            WHERE {} ORDER BY c.borrow_date DESC LIMIT %s'''.format(' AND '.join(parts)),
        tuple(params)
    )


def book_copy_states(book_id):
    """Return [(accession_number, inventory_state, loan, borrower, due)] per copy."""
    try:
        book_id = int(book_id)
    except (TypeError, ValueError):
        return []
    return db.fetch_all(
        '''SELECT a.accession_number,
                  COALESCE(i.inventory_state, 'available'),
                  c.transaction_status, u.full_name, c.due_date
           FROM accession_log a
           LEFT JOIN inventory_status i ON i.accession_id = a.accession_id
           LEFT JOIN circulation_records c ON c.accession_id = a.accession_id
               AND c.transaction_status IN ('active', 'overdue')
           LEFT JOIN borrowers br ON c.borrower_id = br.borrower_id
           LEFT JOIN user_accounts u ON br.user_id = u.user_id
           WHERE a.book_id = %s
           ORDER BY a.accession_number ASC''',
        (book_id,)
    )


def book_reservation_count(book_id):
    """Return waiting/allocated reservation count for one book."""
    try:
        book_id = int(book_id)
    except (TypeError, ValueError):
        return 0
    row = db.fetch_one(
        """SELECT COUNT(*) FROM reservation_queue
           WHERE book_id = %s AND reservation_status IN ('waiting', 'allocated')""",
        (book_id,)
    )
    return row[0] if row else 0


# Status keys for the per-book multi-line trend (circulation actions +
# reservation-queue states, mirroring Reservation Management).
BOOK_STATUS_KEYS = (
    'borrowed', 'returned', 'overdue',
    'waiting', 'allocated', 'claimed', 'expired',
)


def book_status_trends(book_id, start_date=None, end_date=None):
    """Return [(day, status, count)] daily per-status traffic for one book.

    Circulation rows: borrowed groups borrow_date where
    transaction_type = 'borrow'; returned groups return_date where
    transaction_status = 'returned' (returns are an UPDATE of the loan
    row, so no transaction_type = 'return' row ever exists); overdue
    groups borrow_date for overdue/active-past-due loans. Reservation
    rows group request_date by queue state (waiting, allocated,
    claimed, expired â€” the Reservation Management states).
    Reservation rows are dated by request_date (the only per-row date on
    reservation_queue), so claimed/expired lines show when the request was
    made, not when it changed state.
    """
    try:
        book_id = int(book_id)
    except (TypeError, ValueError):
        return []
    cparts, cparams = _range_clause('c.borrow_date', start_date, end_date)
    cparts = ['c.book_id = %s'] + cparts
    cparams = [book_id] + cparams
    cwhere = ' AND '.join(cparts)
    # Returned loans are dated by return_date: the borrow row is UPDATED
    # to transaction_status = 'returned' (transaction_type stays
    # 'borrow'), so filtering borrow_date by transaction_type = 'return'
    # would always return zero rows.
    rtn_parts, rtn_params = _range_clause('c.return_date::date', start_date, end_date)
    rtn_parts = ['c.book_id = %s', "c.transaction_status = 'returned'"] + rtn_parts
    rtn_params = [book_id] + rtn_params
    rtn_where = ' AND '.join(rtn_parts)
    rparts, rparams = _range_clause('r.request_date::date', start_date, end_date)
    rparts = ['r.book_id = %s'] + rparts
    rparams = [book_id] + rparams
    rwhere = ' AND '.join(rparts)
    return db.fetch_all(
        '''SELECT c.borrow_date AS day, 'borrowed' AS status, COUNT(*)
           FROM circulation_records c WHERE {} AND c.transaction_type = 'borrow'
           GROUP BY day
           UNION ALL
           SELECT c.return_date::date AS day, 'returned' AS status, COUNT(*)
           FROM circulation_records c WHERE {} AND c.return_date IS NOT NULL
           GROUP BY day
            UNION ALL
            SELECT c.borrow_date AS day, 'overdue' AS status, COUNT(*)
            FROM circulation_records c WHERE {} AND {}
            GROUP BY day
           UNION ALL
           SELECT r.request_date::date AS day, r.reservation_status AS status, COUNT(*)
           FROM reservation_queue r WHERE {}
           GROUP BY day, r.reservation_status
           ORDER BY day'''.format(cwhere, rtn_where, cwhere, _OVERDUE_CLAUSE, rwhere),
        tuple(cparams + rtn_params + cparams
              + [library_today()] + rparams)
    )


def top_requested_titles(start_date=None, end_date=None, limit=10):
    """Return [(book_title, request_count)] most-requested books first.

    Pending-only: counts rows with request_status = 'pending_review'.
    """
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 10
    parts, params = _range_clause('rr.request_date', start_date, end_date)
    parts.append("rr.request_status = 'pending_review'")
    where = 'WHERE ' + ' AND '.join(parts) if parts else ''
    return db.fetch_all(
        '''SELECT rr.book_title, COUNT(*) AS total
           FROM request_records rr {}
           GROUP BY rr.book_title ORDER BY total DESC, rr.book_title ASC
           LIMIT %s'''.format(where),
        tuple(params + [limit])
    )


def requests_by_role_split(start_date=None, end_date=None, limit=10):
    """Return [(book_title, student, faculty, other, total)] for top titles.

    One row per requested title with the Student / Faculty / Other-staff
    split, so the Analytics tab can render a stacked demand bar per title.
    Pending-only: counts rows with request_status = 'pending_review'.
    """
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 10
    parts, params = _range_clause('rr.request_date', start_date, end_date)
    parts.append("rr.request_status = 'pending_review'")
    where = 'WHERE ' + ' AND '.join(parts) if parts else ''
    return db.fetch_all(
        '''SELECT rr.book_title,
                  COUNT(*) FILTER (WHERE r.role_name = 'Student') AS student,
                  COUNT(*) FILTER (WHERE r.role_name = 'Faculty') AS faculty,
                  COUNT(*) FILTER (WHERE r.role_name NOT IN ('Student', 'Faculty')) AS other,
                  COUNT(*) AS total
           FROM request_records rr
           JOIN borrowers b ON rr.requester_id = b.borrower_id
           JOIN user_accounts u ON b.user_id = u.user_id
           JOIN roles r ON u.role_id = r.role_id
           {} GROUP BY rr.book_title ORDER BY total DESC, rr.book_title ASC
           LIMIT %s'''.format(where),
        tuple(params + [limit])
    )


def requests_trend(start_date=None, end_date=None):
    """Return [(day, request_count)] daily book-request volume.

    Includes pending_review + rejected so denied demand stays visible
    over time.
    """
    parts, params = _range_clause('rr.request_date', start_date, end_date)
    parts.append("rr.request_status IN ('pending_review', 'rejected')")
    where = 'WHERE ' + ' AND '.join(parts) if parts else ''
    return db.fetch_all(
        '''SELECT rr.request_date::date AS day, COUNT(*)
           FROM request_records rr {} GROUP BY day ORDER BY day'''.format(where),
        tuple(params) if params else None
    )


def requests_by_program(start_date=None, end_date=None, departments=None):
    """Return [(program_label, request_count)] using the shared program label.

    program_label matches books_borrowed_per_program: the borrower's
    department, falling back to Admin/Librarian role or 'No program'.
    Pending-only: counts rows with request_status = 'pending_review'.
    """
    parts, params = _range_clause('rr.request_date', start_date, end_date)
    parts.append("rr.request_status = 'pending_review'")
    dept_clause, dept_params = _department_clause(departments, 'b', 'r')
    if dept_clause:
        parts.append(dept_clause)
        params.extend(dept_params)
    where = 'WHERE ' + ' AND '.join(parts) if parts else ''
    return db.fetch_all(
        '''SELECT COALESCE(NULLIF(b.department, ''),
                          CASE WHEN r.role_name IN ('Admin', 'Librarian') THEN r.role_name
                               ELSE 'No program' END) as program_label,
                  COUNT(rr.request_id) as total
           FROM request_records rr
           JOIN borrowers b ON rr.requester_id = b.borrower_id
           JOIN user_accounts u ON b.user_id = u.user_id
           JOIN roles r ON u.role_id = r.role_id
           {} GROUP BY program_label ORDER BY total DESC'''.format(where),
        tuple(params) if params else None
    )


def requests_by_status(start_date=None, end_date=None):
    """Return [(request_status, count)] headline counts for KPI cards."""
    parts, params = _range_clause('rr.request_date', start_date, end_date)
    where = 'WHERE ' + ' AND '.join(parts) if parts else ''
    return db.fetch_all(
        '''SELECT rr.request_status, COUNT(*)
           FROM request_records rr {} GROUP BY rr.request_status'''.format(where),
        tuple(params) if params else None
    )


# ebook_access_log.accessed_at is a UTC DEFAULT NOW() timestamp. Convert it
# to the library's Manila wall clock before day-bucketing or range-filtering
# so the trend charts and the recent table agree with Philippine dates.
_EBOOK_MANILA_DAY = "(e.accessed_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Manila')::date"
_EBOOK_MANILA_DAY_BARE = "(accessed_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Manila')::date"


def ebook_access_trend(start_date=None, end_date=None):
    """Return [(day, program_label, count)] daily e-book activity by program.

    Grouped by accessed day and the reader's program (borrower department,
    staff role, or the shared 'No program' fallback). Activity by visitors
    who are not signed in is labelled 'Offline Reader'. Powers the E-Book
    Reads & Downloads Trend multi-line graph on the Library tab.
    """
    parts, params = _range_clause(_EBOOK_MANILA_DAY, start_date, end_date)
    where = 'WHERE ' + ' AND '.join(parts) if parts else ''
    return db.fetch_all(
        '''SELECT (e.accessed_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Manila')::date AS day,
                  {} AS series_label,
                  COUNT(*) AS total
           FROM ebook_access_log e
           LEFT JOIN user_accounts u ON u.user_id = e.user_id
           LEFT JOIN borrowers b ON b.user_id = u.user_id
           LEFT JOIN roles r ON r.role_id = u.role_id
           {} GROUP BY day, 2 ORDER BY day, 2'''.format(
            _EBOOK_PROGRAM_LABEL, where),
        tuple(params) if params else None
    )


def ebook_access_by_program_on_date(day):
    """Return [(program_label, count)] e-book access split for one day.

    Drill-down for the E-Book Reads & Downloads Trend dots: clicking a
    trend point shows which reader program accessed e-books on that
    date. Not-signed-in activity is labelled 'Offline Reader'. `day` is
    'YYYY-MM-DD'; the ::date cast keeps TIMESTAMP rows comparable.
    """
    return db.fetch_all(
        '''SELECT {} AS program_label, COUNT(*) AS total
           FROM ebook_access_log e
           LEFT JOIN user_accounts u ON u.user_id = e.user_id
           LEFT JOIN borrowers b ON b.user_id = u.user_id
           LEFT JOIN roles r ON r.role_id = u.role_id
           WHERE (e.accessed_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Manila')::date = %s::date
           GROUP BY 1 ORDER BY total DESC, 1'''.format(_EBOOK_PROGRAM_LABEL),
        (day,)
    )


def top_ebooks(start_date=None, end_date=None, limit=8):
    """Return [(title, author, reads, downloads, total)] top e-books first.

    One row per e-book title with the read and download split, ordered
    by combined activity within the selected period.
    """
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 8
    parts, params = _range_clause(_EBOOK_MANILA_DAY, start_date, end_date)
    where = 'WHERE ' + ' AND '.join(parts) if parts else ''
    return db.fetch_all(
        '''SELECT b.title, b.author,
                  COUNT(*) FILTER (WHERE e.access_kind = 'read') AS reads,
                  COUNT(*) FILTER (WHERE e.access_kind = 'download') AS downloads,
                  COUNT(*) AS total
           FROM ebook_access_log e
           JOIN book_catalog b ON e.book_id = b.book_id
           {} GROUP BY b.book_id, b.title, b.author
           ORDER BY total DESC, b.title ASC
           LIMIT %s'''.format(where),
        tuple(params + [limit])
    )


def book_ebook_accesses(book_id, start_date=None, end_date=None):
    """Return (reads, downloads, total) for one book within the period.

    Summing both event kinds for the Resource Analytics per-book view;
    a missing book_id yields the zero row instead of raising.
    """
    try:
        book_id = int(book_id)
    except (TypeError, ValueError):
        return (0, 0, 0)
    parts, params = _range_clause(_EBOOK_MANILA_DAY_BARE, start_date, end_date)
    parts.insert(0, 'book_id = %s')
    params = [book_id] + params
    where = 'WHERE ' + ' AND '.join(parts)
    row = db.fetch_one(
        '''SELECT COUNT(*) FILTER (WHERE access_kind = 'read') AS reads,
                  COUNT(*) FILTER (WHERE access_kind = 'download') AS downloads,
                  COUNT(*) AS total
           FROM ebook_access_log {}'''.format(where),
        tuple(params), 
    )
    if not row:
        return (0, 0, 0)
    try:
        return (int(row[0] or 0), int(row[1] or 0), int(row[2] or 0))
    except (IndexError, TypeError, ValueError):
        return (0, 0, 0)


def book_ebook_recent(book_id, limit=10, start_date=None, end_date=None):
    """Return [(time, kind, user_name)] newest e-book events for one book.

    Powers the Resource Analytics recent table; anonymous events join
    to no user and render as 'Anonymous'. Bad ids produce an empty list
    without querying.
    """
    try:
        book_id = int(book_id)
        limit = int(limit)
    except (TypeError, ValueError):
        return []
    parts, params = _range_clause(_EBOOK_MANILA_DAY, start_date, end_date)
    where = 'WHERE e.book_id = %s' + (' AND ' + ' AND '.join(parts) if parts else '')
    params = [book_id] + params
    return db.fetch_all(
        '''SELECT e.accessed_at, e.access_kind,
                  COALESCE(u.full_name, 'Anonymous') AS reader
           FROM ebook_access_log e
           LEFT JOIN user_accounts u ON e.user_id = u.user_id
           {} ORDER BY e.accessed_at DESC LIMIT %s'''.format(where),
        tuple(params + [limit])
    )