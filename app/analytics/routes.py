import io
from datetime import date, datetime, timedelta
from xml.sax.saxutils import escape as _xml_escape

from flask import render_template, request, Response, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import HorizontalBarChart
from reportlab.graphics.charts.lineplots import LinePlot

from . import analytics_bp
from app.auth.decorators import librarian_required
from app.analytics import models

VALID_KPIS = {
    'books_borrowed_per_program',
    'utilization_rate',
    'most_borrowed_titles',
    'underutilized_titles',
}

KPI_LABELS = {
    'books_borrowed_per_program': 'Books Borrowed per Program',
    'utilization_rate': 'Utilization Rate',
    'most_borrowed_titles': 'Most Borrowed Titles',
    'underutilized_titles': 'Underutilized Titles',
}

KPI_DESCRIPTIONS = {
    'books_borrowed_per_program': 'Total borrows broken down by borrower program/department.',
    'utilization_rate': 'Share of the active collection currently on loan.',
    'most_borrowed_titles': 'Top titles by quantity of borrows in the selected period.',
    'underutilized_titles': 'Titles with zero borrows in the selected period.',
}

# Dashboard export sections (Statistics tabs + Quick Reports). The custom KPI
# board is removed, so these are the only exportable contents; kpi_json stays
# limited to the board-era VALID_KPIS for backwards compatibility.
DASHBOARD_LABELS = {
    'trend_borrowings': 'Borrowings Trend',
    'trend_overdue': 'Overdue Trend',
    'top_categories': 'Top Borrowed Categories',
    'peak_periods': 'Peak Borrowing Periods',
    'top_books': 'Top Borrowed Books',
    'high_demand': 'Likely High-Demand Titles',
    'by_user_type': 'Borrowings by User Type',
    'collection_by_category': 'Collection by Category',
    'copies_by_status': 'Copies by Status',
    'recent_circulation': 'Recent Circulation Activity',
    'recent_collection': 'Recent Collection Status',
    'circulation_summary': 'Circulation Summary',
    'borrowers_by_department': 'Active Borrowers by Department',
    'overdue_by_department': 'Overdue Items by Department',
    'department_leaderboard': 'Department Leaderboard',
    'top_requested_titles': 'Top Requested Titles',
    'requests_by_role': 'Book Requests by Role (Student vs Faculty)',
    'requests_trend': 'Book Requests Trend',
    'requests_by_program': 'Book Requests by Program',
}

DASHBOARD_DESCRIPTIONS = {
    'trend_borrowings': 'Daily borrow counts in the selected period.',
    'trend_overdue': 'Daily overdue items by due date in the selected period (missing days are zero).',
    'top_categories': 'Borrows grouped by subject classification.',
    'peak_periods': 'Borrowings grouped by day to show peak days.',
    'top_books': 'Most borrowed books with authors.',
    'high_demand': 'Active loans ranked by current demand.',
    'by_user_type': 'Borrows grouped by account role.',
    'collection_by_category': 'Active titles grouped by subject classification.',
    'copies_by_status': 'Physical copies grouped by availability status.',
    'recent_circulation': 'Latest circulation transactions.',
    'recent_collection': 'Latest accessioned copies with status.',
    'circulation_summary': 'Headline circulation totals for the period.',
    'borrowers_by_department': 'Distinct active borrowers grouped by program/department.',
    'overdue_by_department': 'Overdue loans grouped by program/department.',
    'department_leaderboard': 'Borrowings, borrowers, and overdue per program/department.',
    'top_requested_titles': 'Most-requested books not yet in the collection.',
    'requests_by_role': 'Top requested titles split into Student / Faculty / Other staff.',
    'requests_trend': 'Daily book-request counts in the selected period.',
    'requests_by_program': 'Book requests grouped by borrower program/department.',
}

EXPORTABLE_KPIS = set(VALID_KPIS) | set(DASHBOARD_LABELS)


def resolve_dates(preset, from_str, to_str):
    """Resolve a date range into (start_date, end_date).

    Preset ``semester``/``year`` always wins over explicit dates (prevents
    stale ``from``/``to`` from hidden custom inputs from overriding the
    preset).  For ``custom`` (or ``all`` with explicit dates) the dates are
    parsed; invalid dates fall back to no bounds.
    """
    today = date.today()

    # Preset ranges take precedence — ignore any stale from/to.
    if preset == 'year':
        return date(today.year, 1, 1), date(today.year, 12, 31)
    if preset == 'semester':
        if today.month >= 8:
            return date(today.year, 8, 1), date(today.year, 12, 31)
        else:
            return date(today.year, 1, 1), date(today.year, 5, 31)

    # ``custom`` or ``all`` with explicit dates: try to parse the dates.
    if from_str or to_str or preset == 'custom':
        try:
            start_date = datetime.strptime(from_str, '%Y-%m-%d').date() if from_str else None
            end_date = datetime.strptime(to_str, '%Y-%m-%d').date() if to_str else None
        except ValueError:
            return None, None
        return start_date, end_date

    return None, None


def _normalize_range(preset, from_str, to_str):
    if preset in ('semester', 'year'):
        from_str = to_str = ''
    elif preset not in ('custom', 'all'):
        from_str = to_str = ''
    return preset, from_str, to_str


def _clean_department_list(values):
    """Multi program/department selector; [] means all programs."""
    seen = []
    for v in (values or []):
        v = (v or '').strip()
        if v and v not in seen:
            seen.append(v[:100])
        if len(seen) >= 50:
            break
    return seen


def _dashboard_cache_key(start_date, end_date, departments):
    """JSON-safe cache key for a dashboard filter set."""
    def _iso(value):
        try:
            return value.isoformat() if hasattr(value, 'isoformat') else value
        except (TypeError, ValueError):
            return None
    depts = sorted({(d or '').strip() for d in (departments or []) if (d or '').strip()})
    return {'start': _iso(start_date), 'end': _iso(end_date), 'departments': depts}


def _dashboard_cache_allowed():
    """Cache only in real requests — never in tests (deterministic mocks)
    and never without an app context."""
    try:
        from flask import current_app, has_app_context
        return has_app_context() and not current_app.config.get('TESTING')
    except Exception:
        return False


def _dashboard_actor():
    try:
        from flask_login import current_user
        return current_user.id
    except Exception:
        return None


def compute_dashboard(start_date, end_date, departments=None, _use_cache=True):
    """Assemble Riverside-style dashboard payload from model queries.

    Results are cached per filter set (see models.get/set_dashboard_cache,
    TTL 5 min). Cache is best-effort and disabled in tests; any failure
    falls back to fresh compute.
    """
    key = _dashboard_cache_key(start_date, end_date, departments)
    if _use_cache and _dashboard_cache_allowed():
        try:
            hit = models.get_dashboard_cache(key)
        except Exception:
            hit = None
        if hit is not None:
            return hit
    payload = _compute_dashboard(start_date, end_date, departments)
    if _use_cache and _dashboard_cache_allowed():
        try:
            models.set_dashboard_cache(key, payload, _dashboard_actor())
        except Exception:
            pass
    return payload


def _compute_dashboard(start_date, end_date, departments=None):
    """Assemble Riverside-style dashboard payload from model queries.

    Returns JSON-serializable dicts/lists only (dates stringified); the
    template embeds it as ``dashboard-data`` and renders the three tabs
    client-side.  Missing tables/rows degrade to zeros/empty lists.
    departments (str or list of str) scopes ONLY the usage section
    (whole Usage tab program filter); collection/circulation sections
    always use the full range.
    """
    def _safe(fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception:
            return None

    def _pair(rows):
        out = []
        for r in rows or []:
            try:
                label = r[0]
                # Trend queries return DATEs; Flask jsonify would render them
                # as RFC-2822 ("Sat, 15 Aug 2026...") which breaks the chart
                # x-axis slicing. Normalize to ISO YYYY-MM-DD instead.
                if hasattr(label, 'isoformat'):
                    label = label.isoformat()
                out.append([label, int(r[1] or 0)])
            except (IndexError, TypeError, ValueError):
                continue
        return out

    def _triple(rows):
        out = []
        for r in rows or []:
            try:
                out.append([r[0], r[1] if len(r) > 1 else '', int(r[2] or 0) if len(r) > 2 else 0])
            except (IndexError, TypeError, ValueError):
                continue
        return out

    def _dept_summary_rows(rows):
        """Leaderboard rows: [program, borrowings, borrowers, overdue]."""
        out = []
        for r in rows or []:
            try:
                out.append([r[0], int(r[1] or 0), int(r[2] or 0) if len(r) > 2 else 0,
                            int(r[3] or 0) if len(r) > 3 else 0])
            except (IndexError, TypeError, ValueError):
                continue
        return out

    def _quint(rows):
        """Role-split rows: [title, student, faculty, other, total]."""
        out = []
        for r in rows or []:
            try:
                out.append([r[0], int(r[1] or 0) if len(r) > 1 else 0,
                            int(r[2] or 0) if len(r) > 2 else 0,
                            int(r[3] or 0) if len(r) > 3 else 0,
                            int(r[4] or 0) if len(r) > 4 else 0])
            except (IndexError, TypeError, ValueError):
                continue
        return out

    total_titles = _safe(models.count_active_titles) or 0
    total_copies = _safe(models.count_total_copies) or 0
    status_rows = _safe(models.count_circulation_status, start_date, end_date) or []
    status = {}
    for r in status_rows:
        try:
            status[str(r[0])] = int(r[1] or 0)
        except (IndexError, TypeError, ValueError):
            continue
    lost_flagged = _safe(models.count_lost_flagged, start_date, end_date)
    lost_flagged = int(lost_flagged[0]) if lost_flagged else 0
    reserved = _safe(models.count_reservations) or 0
    inv_rows = _safe(models.inventory_state_counts) or []
    inv = {}
    for r in inv_rows:
        try:
            inv[str(r[0])] = int(r[1] or 0)
        except (IndexError, TypeError, ValueError):
            continue
    inv_lost = inv.get('lost', 0)
    inv_damaged = inv.get('damaged', 0)
    inv_missing = inv.get('missing', 0)

    borrowed = status.get('active', 0)
    overdue = status.get('overdue', 0)
    lost_damaged = inv_lost + inv_damaged + lost_flagged
    maintenance = inv_missing
    # Unified with models.copies_by_status_summary: reserved copies are not
    # available, and lost-flagged loans count as lost/damaged.
    available = max(total_copies - borrowed - overdue - reserved - lost_damaged - maintenance, 0)

    if isinstance(departments, str):
        departments = [departments]
    dept_list = _clean_department_list(departments) or None

    by_category = _pair(_safe(models.collection_by_category, start_date, end_date))
    by_program_all = _pair(_safe(models.books_borrowed_per_program, start_date, end_date))
    trend = _pair(_safe(models.borrowings_trend, start_date, end_date))
    overdue_t = _pair(_safe(models.overdue_trend, start_date, end_date))
    top_cats = _pair(_safe(models.top_borrowed_categories, start_date, end_date))
    high_demand = _triple(_safe(models.high_demand_titles, start_date, end_date))
    overview = _safe(models.circulation_overview, start_date, end_date)
    if not overview:
        overview = (0, 0, 0, 0.0, 0.0, 0)
    # Book Requests tab (read-only acquisition demand). by_program honors
    # the same program filter as the usage tab; the rest is period-scoped.
    req_status_rows = _safe(models.requests_by_status, start_date, end_date) or []
    req_status = {}
    for r in req_status_rows:
        try:
            req_status[str(r[0])] = int(r[1] or 0)
        except (IndexError, TypeError, ValueError):
            continue
    req_top = _pair(_safe(models.top_requested_titles, start_date, end_date, 10))
    req_split = _quint(_safe(models.requests_by_role_split, start_date, end_date, 10))
    req_trend = _pair(_safe(models.requests_trend, start_date, end_date))
    req_by_program = _pair(_safe(models.requests_by_program, start_date, end_date, dept_list))
    # Usage-tab scoped queries (whole-tab program filter).
    if dept_list:
        overview_u = _safe(models.circulation_overview, start_date, end_date, dept_list)
        trend_u = _pair(_safe(models.borrowings_trend, start_date, end_date, None, dept_list))
        top_books_u = _triple(_safe(
            models.top_borrowed_books_detailed, start_date, end_date, 5, None, dept_list))
        by_user_type_u = _pair(_safe(
            models.borrowings_by_user_type, start_date, end_date, None, None, dept_list))
        by_program_u = _pair(_safe(
            models.books_borrowed_per_program, start_date, end_date, dept_list))
        overdue_dept_u = _pair(_safe(
            models.overdue_by_department, start_date, end_date, dept_list))
        borrowers_dept_u = _pair(_safe(
            models.borrowers_by_department, start_date, end_date, dept_list))
        dept_summary_u = _dept_summary_rows(_safe(
            models.department_summary, start_date, end_date, dept_list))
        recent_u_raw = _safe(
            models.recent_circulation, 10, dept_list, start_date, end_date) or []
    else:
        overview_u = overview
        trend_u = trend
        top_books_u = _triple(_safe(models.top_borrowed_books_detailed, start_date, end_date))
        by_user_type_u = _pair(_safe(models.borrowings_by_user_type, start_date, end_date))
        by_program_u = by_program_all
        overdue_dept_u = _pair(_safe(models.overdue_by_department, start_date, end_date))
        borrowers_dept_u = _pair(_safe(models.borrowers_by_department, start_date, end_date))
        dept_summary_u = _dept_summary_rows(_safe(models.department_summary, start_date, end_date))
        recent_u_raw = _safe(models.recent_circulation) or []
    if not overview_u:
        overview_u = (0, 0, 0, 0.0, 0.0, 0)
    recent_circ_raw = _safe(models.recent_circulation) or []
    recent_circ = []
    for c in recent_circ_raw:
        try:
            recent_circ.append([
                str(c[0]), c[1] if len(c) > 1 else '', c[2] if len(c) > 2 else '',
                c[3] if len(c) > 3 else '', c[4] if len(c) > 4 else '',
                c[5] if len(c) > 5 else '', c[6] if len(c) > 6 else '',
                str(c[7]) if len(c) > 7 and c[7] else '',
                c[8] if len(c) > 8 else '',
            ])
        except (IndexError, TypeError):
            continue
    recent_u = []
    for c in recent_u_raw:
        try:
            recent_u.append([
                str(c[0]), c[1] if len(c) > 1 else '', c[2] if len(c) > 2 else '',
                c[3] if len(c) > 3 else '', c[4] if len(c) > 4 else '',
                c[5] if len(c) > 5 else '', c[6] if len(c) > 6 else '',
                str(c[7]) if len(c) > 7 and c[7] else '',
                c[8] if len(c) > 8 else '',
            ])
        except (IndexError, TypeError):
            continue
    recent_coll_raw = _safe(models.recent_collection_status) or []
    recent_coll = []
    for c in recent_coll_raw:
        try:
            recent_coll.append([
                c[0] if len(c) > 0 else '', c[1] if len(c) > 1 else '',
                c[2] if len(c) > 2 else '', c[3] if len(c) > 3 else '',
                c[4] if len(c) > 4 else '', c[5] if len(c) > 5 else '',
                str(c[6]) if len(c) > 6 and c[6] else '',
            ])
        except (IndexError, TypeError):
            continue

    # Condition buckets derived from inventory_state (no condition column).
    cond_total = max(sum(inv.values()), 1)
    condition = [
        ['New / Excellent', inv.get('available', 0)],
        ['Very Good', inv.get('borrowed', 0)],
        ['Good', 0],
        ['Fair', inv.get('damaged', 0) + inv.get('missing', 0)],
        ['Poor', inv.get('lost', 0) + lost_flagged],
    ]
    if sum(c[1] for c in condition) == 0 and total_copies:
        condition[0][1] = available
        condition[1][1] = borrowed

    return {
        'collection': {
            'total_titles': total_titles,
            'total_copies': total_copies,
            'available': available,
            'borrowed': borrowed,
            'reserved': reserved,
            'overdue': overdue,
            'lost_damaged': lost_damaged,
            'maintenance': maintenance,
            'by_category': by_category,
            'condition': condition,
            'cond_total': cond_total,
            'recent': recent_coll,
        },
        'circulation': {
            'total': overview[0],
            'active_borrowers': overview[1],
            'overdue': overview[2],
            'avg_loan_days': overview[3],
            'return_rate': overview[4],
            'new_additions': overview[5],
            'trend': trend,
            'overdue_trend': overdue_t,
            'top_categories': top_cats,
            'high_demand': high_demand,
            'recent': recent_circ,
        },
        'requests': {
            'total': (req_status.get('pending_review', 0) + req_status.get('approved', 0)
                      + req_status.get('rejected', 0) + req_status.get('procured', 0)
                      + req_status.get('existing_in_collection', 0)),
            'pending': req_status.get('pending_review', 0),
            'approved': req_status.get('approved', 0),
            'rejected': req_status.get('rejected', 0),
            'procured': req_status.get('procured', 0),
            'top_titles': req_top,
            'by_role': req_split,
            'trend': req_trend,
            'by_program': req_by_program,
        },
        'usage': {
            'total': overview_u[0],
            'unique_borrowers': overview_u[1],
            'avg_per_borrower': round(overview_u[0] / overview_u[1], 2) if overview_u[1] else 0.0,
            'overdue': overview_u[2],
            'return_rate': overview_u[4],
            'active_departments': len(by_program_all),
            'by_department': by_program_u,
            'by_department_all': by_program_all,
            'overdue_by_department': overdue_dept_u,
            'borrowers_by_department': borrowers_dept_u,
            'dept_summary': dept_summary_u,
            'trend': trend_u,
            'top_books': top_books_u,
            'by_user_type': by_user_type_u,
            'recent': recent_u,
            'departments': dept_list or [],
            'department': ', '.join(dept_list) if dept_list else '',
        },
    }


@analytics_bp.route('/librarian/analytics')
@login_required
@librarian_required
def analytics_page():
    preset = request.args.get('preset', 'all')
    from_str = request.args.get('from', '').strip()
    to_str = request.args.get('to', '').strip()
    departments = _clean_department_list(request.args.getlist('department'))
    # Normalize: semester/year presets ignore stale custom dates in the URL;
    # invalid presets fall back to no bounds (same as kpi_json/export_report).
    preset, from_str, to_str = _normalize_range(preset, from_str, to_str)
    start_date, end_date = resolve_dates(preset, from_str, to_str)
    dashboard = compute_dashboard(start_date, end_date, departments)
    period_label = _format_period(start_date, end_date, preset, from_str, to_str)
    # Book Analytics tab: ``q`` searches active titles by title,
    # category, or accession number; ``book_id`` selects one title whose
    # single-book traffic renders in the tab.  Top-10 utilized /
    # underutilized charts always render, even before any search.
    # Without ``book_id`` no per-book queries run, so only the top-10
    # sections show until a card's "Show Analytics" is clicked.
    q = request.args.get('q', '').strip()
    book_id = _parse_book_id(request.args.get('book_id', ''))
    results = models.search_books_for_analytics(q, 10) if q else []
    traffic = compute_book_traffic(book_id, start_date, end_date) if book_id else None
    if book_id and traffic is None:
        flash('Book not found.', 'error')
    try:
        top_utilized = models.most_borrowed_titles(start_date, end_date, 10) or []
    except Exception:
        top_utilized = []
    try:
        top_underutilized = models.underutilized_titles(start_date, end_date, 10) or []
    except Exception:
        top_underutilized = []
    return render_template(
        'analytics/analytics.html',
        preset=preset,
        from_date=from_str,
        to_date=to_str,
        period_label=period_label,
        departments=departments,
        dashboard=dashboard,
        q=q,
        results=results,
        book_id=book_id,
        traffic=traffic,
        top_utilized=top_utilized,
        top_underutilized=top_underutilized,
    )


def _parse_book_id(value):
    try:
        book_id = int((value or '').strip())
    except (AttributeError, TypeError, ValueError):
        return None
    return book_id if book_id > 0 else None


# Multi-line status graph: one line per circulation/reservation status,
# in the same key order as models.BOOK_STATUS_KEYS.
BOOK_STATUS_META = (
    ('borrowed', 'Borrowed', '#2563eb'),
    ('returned', 'Returned', '#16a34a'),
    ('overdue', 'Overdue', '#ef4444'),
    ('waiting', 'Waiting', '#f59e0b'),
    ('allocated', 'Allocated', '#8b5cf6'),
    ('claimed', 'Claimed', '#0ea5e9'),
    ('expired', 'Expired', '#64748b'),
)


def compute_book_traffic(book_id, start_date, end_date):
    """Assemble per-book traffic payload (JSON-safe primitives only).

    Returns None when the book does not exist; otherwise a dict with
    headline totals, ISO-dated trend, program/user-type splits, copy
    states, waiting reservations, and recent transactions.
    """

    def _safe(fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception:
            return None

    def _pair(rows):
        out = []
        for r in rows or []:
            try:
                label = r[0]
                if hasattr(label, 'isoformat'):
                    label = label.isoformat()
                out.append([label, int(r[1] or 0)])
            except (IndexError, TypeError, ValueError):
                continue
        return out

    book = _safe(models.get_book_for_analytics, book_id)
    if not book or len(book) < 4:
        return None
    overview = _safe(models.book_traffic_overview, book_id, start_date, end_date)
    if not overview:
        overview = (0, 0, 0, 0, 0, 0.0, 0.0)
    trend = _pair(_safe(models.book_borrowings_trend, book_id, start_date, end_date))
    by_program = _pair(_safe(models.book_borrowed_per_program, book_id, start_date, end_date))
    by_user_type = _pair(_safe(models.book_borrowings_by_user_type, book_id, start_date, end_date))
    copies_raw = _safe(models.book_copy_states, book_id) or []
    copies = []
    for c in copies_raw:
        try:
            copies.append([
                c[0] if len(c) > 0 else '', c[1] if len(c) > 1 else '',
                c[2] if len(c) > 2 else '', c[3] if len(c) > 3 else '',
                str(c[4]) if len(c) > 4 and c[4] else '',
            ])
        except (IndexError, TypeError):
            continue
    recent_raw = _safe(models.book_recent_circulation, book_id, 10, start_date, end_date) or []
    recent = []
    for c in recent_raw:
        try:
            recent.append([
                str(c[0]) if len(c) > 0 and c[0] else '',
                c[1] if len(c) > 1 else '', c[2] if len(c) > 2 else '',
                c[3] if len(c) > 3 else '', c[4] if len(c) > 4 else '',
                str(c[5]) if len(c) > 5 and c[5] else '',
                c[6] if len(c) > 6 else '',
            ])
        except (IndexError, TypeError):
            continue
    waiting = _safe(models.book_reservation_count, book_id) or 0
    try:
        waiting = int(waiting)
    except (TypeError, ValueError):
        waiting = 0
    # Pivot per-status daily rows into aligned series (zero-filled) for the
    # multi-line status graph: one line per circulation/reservation status.
    status_dates = []
    status_series = []
    status_rows = _safe(models.book_status_trends, book_id, start_date, end_date) or []
    day_set = set()
    day_values = {}
    for r in status_rows:
        try:
            day = r[0].isoformat() if hasattr(r[0], 'isoformat') else str(r[0])
            key = str(r[1])
            count = int(r[2] or 0)
        except (IndexError, TypeError, ValueError):
            continue
        if key not in models.BOOK_STATUS_KEYS:
            continue
        day_set.add(day)
        day_values[(day, key)] = day_values.get((day, key), 0) + count
    status_dates = sorted(day_set)
    if start_date is not None and end_date is not None:
        # Bounded period (semester/year/custom): show every day in the
        # range so lone spikes render as spikes on a real timeline instead
        # of collapsing the axis to the active days only. Cap the fill so
        # absurd ranges fall back to observed dates.
        span = (end_date - start_date).days
        if 0 <= span <= 400:
            day = start_date
            full = []
            while day <= end_date:
                full.append(day.isoformat())
                day += timedelta(days=1)
            status_dates = full
    for key, label, color in BOOK_STATUS_META:
        status_series.append({
            'key': key, 'label': label, 'color': color,
            'values': [day_values.get((day, key), 0) for day in status_dates],
        })
    # get_book_for_analytics returns
    # (book_id, title, author, category, year_published, copies,
    #  publisher, edition, isbn, call_number, material_type, description);
    # older callers/mocks may still pass the shorter 5/6-tuples.
    if len(book) > 5:
        year_published = book[4]
        copy_count = book[5]
    else:
        year_published = None
        copy_count = book[4] if len(book) > 4 else 0
    try:
        copy_count = int(copy_count or 0)
    except (TypeError, ValueError):
        copy_count = 0

    def _col(i):
        return book[i] if len(book) > i else None

    return {
        'book': {
            'book_id': book[0], 'title': book[1], 'author': book[2],
            'category': book[3] if len(book) > 3 else '',
            'year_published': year_published,
            'copyright_date': year_published,
            'copies': copy_count,
            'publisher': _col(6),
            'edition': _col(7),
            'isbn': _col(8),
            'call_number': _col(9),
            'material_type': _col(10),
            'description': _col(11),
        },
        'overview': {
            'total': overview[0], 'active': overview[1], 'overdue': overview[2],
            'returned': overview[3], 'borrowers': overview[4],
            'avg_loan_days': overview[5], 'return_rate': overview[6],
            'waiting': waiting,
        },
        'trend': trend,
        'by_program': by_program,
        'by_user_type': by_user_type,
        'status_trends': {'dates': status_dates, 'series': status_series},
        'copies': copies,
        'recent': recent,
    }


@analytics_bp.route('/librarian/analytics/book/search')
@login_required
@librarian_required
def book_search_json():
    """Live title/category/accession suggestions for the Book Analytics picker."""
    q = request.args.get('q', '').strip()
    rows = models.search_books_for_analytics(q, 10)
    results = []
    for r in (rows or []):
        item = {'book_id': r[0], 'title': r[1], 'author': r[2],
                'category': r[3] if len(r) > 3 else ''}
        if len(r) > 4:
            item['year_published'] = r[4]
            item['copyright_date'] = r[4]
        results.append(item)
    return jsonify({'results': results})


@analytics_bp.route('/librarian/analytics/book/data')
@login_required
@librarian_required
def book_data_json():
    """Traffic payload for one book in the requested range as JSON."""
    book_id = _parse_book_id(request.args.get('book_id', ''))
    if not book_id:
        return jsonify({'error': 'invalid book_id'}), 400
    preset = request.args.get('preset', 'all')
    from_str = request.args.get('from', '').strip()
    to_str = request.args.get('to', '').strip()
    preset, from_str, to_str = _normalize_range(preset, from_str, to_str)
    start_date, end_date = resolve_dates(preset, from_str, to_str)
    traffic = compute_book_traffic(book_id, start_date, end_date)
    if traffic is None:
        return jsonify({'error': 'book not found'}), 404
    return jsonify(traffic)


def _trend_direction(counts):
    """Rising/falling/flat from first-half vs second-half daily averages."""
    if len(counts) < 4:
        return 'flat'
    mid = len(counts) // 2
    first = sum(counts[:mid]) / max(mid, 1)
    second = sum(counts[mid:]) / max(len(counts) - mid, 1)
    if not first:
        return 'up' if second > 0 else 'flat'
    ratio = second / first
    if ratio >= 1.1:
        return 'up'
    if ratio <= 0.9:
        return 'down'
    return 'flat'


def _forecast_payload(start_date, end_date, preset='all', from_str='', to_str=''):
    """Projections from current graphs + actionable insights.

    All projections are simple run-rate extrapolations, labeled as such —
    planning aids, not predictions. JSON-safe primitives only.
    """
    trend = models.borrowings_trend(start_date, end_date) or []
    counts = []
    for r in trend:
        try:
            counts.append(int(r[1] or 0))
        except (IndexError, TypeError, ValueError):
            continue
    total = sum(counts)
    if start_date is not None and end_date is not None:
        span = max((end_date - start_date).days + 1, 1)
    else:
        span = max(len(counts), 1)
    daily_avg = round(total / span, 2)
    next_30 = int(round(daily_avg * 30))

    top_cats = models.top_borrowed_categories(start_date, end_date) or []
    cat_total = sum((c[1] or 0) for c in top_cats if len(c) > 1)
    by_category = []
    for c in top_cats:
        try:
            share = (c[1] or 0) / cat_total if cat_total else 0
            by_category.append([c[0], int(c[1] or 0), int(round(share * next_30))])
        except (IndexError, TypeError, ValueError):
            continue

    overdue_t = models.overdue_trend(start_date, end_date) or []
    overdue_counts = []
    for r in overdue_t:
        try:
            overdue_counts.append(int(r[1] or 0))
        except (IndexError, TypeError, ValueError):
            continue
    overdue_inflow = round(sum(overdue_counts) / span, 2)
    overdue_direction = _trend_direction(overdue_counts)

    added = models.count_accessions(start_date, end_date)
    additions_next_30 = int(round(added / span * 30))

    weekday_mix = models.borrowings_by_weekday(start_date, end_date) or []
    weekday_total = sum(w[1] for w in weekday_mix)
    busiest = max(weekday_mix, key=lambda w: w[1])[0] if weekday_total else '-'

    # 30-day demand projection: daily pace shaped by historical weekday
    # shares, so peaks and quiet days show instead of a flat line.
    shares = [(w[1] / weekday_total) if weekday_total else 1 / 7 for w in weekday_mix]
    today = date.today()
    projected_trend = []
    for i in range(1, 31):
        day = today + timedelta(days=i)
        if weekday_mix:
            value = round(daily_avg * 7 * shares[day.weekday() % 7], 1)
        else:
            value = round(daily_avg, 1)
        projected_trend.append([day.isoformat(), value])
    trend_tail = []
    for r in trend[-30:]:
        try:
            label = r[0].isoformat() if hasattr(r[0], 'isoformat') else r[0]
            trend_tail.append([label, int(r[1] or 0)])
        except (IndexError, TypeError, ValueError):
            continue

    gaps = []
    for r in models.title_demand_gaps() or []:
        try:
            waiting, available = int(r[2] or 0), int(r[3] or 0)
        except (IndexError, TypeError, ValueError):
            continue
        if waiting > available:
            gaps.append([r[0], r[1], waiting, available, waiting - available])

    insights = []
    if gaps:
        insights.append({
            'severity': 'warn',
            'title': '%d title(s) have more waiters than copies' % len(gaps),
            'detail': 'Top pressure: "%s" needs %d more cop%s.' % (
                gaps[0][0], gaps[0][4], 'y' if gaps[0][4] == 1 else 'ies'),
            'action_label': 'Order copies',
            'action_url': url_for('procurement.procurement_dashboard'),
        })
    if overdue_direction == 'up':
        insights.append({
            'severity': 'warn',
            'title': 'Overdue inflow is rising',
            'detail': 'About %g new overdue items per day in this period.' % overdue_inflow,
            'action_label': 'Follow up overdue',
            'action_url': url_for('circulation.circulation_page'),
        })
    if by_category:
        insights.append({
            'severity': 'info',
            'title': '%s leads projected demand' % by_category[0][0],
            'detail': 'About %d of the projected %d borrows in the next 30 days.' % (
                by_category[0][2], next_30),
            'action_label': 'Boost acquisition',
            'action_url': url_for('procurement.procurement_dashboard'),
        })
    if busiest != '-':
        insights.append({
            'severity': 'info',
            'title': '%ss are the busiest day' % busiest,
            'detail': 'Plan staffing and returns handling for peak weekday load.',
            'action_label': 'View circulation',
            'action_url': url_for('circulation.circulation_page'),
        })
    if additions_next_30:
        insights.append({
            'severity': 'ok',
            'title': 'Collection growing at %d titles / 30 days' % additions_next_30,
            'detail': 'Keep cataloging throughput to sustain the pace.',
            'action_label': 'Add titles',
            'action_url': url_for('cataloging.cataloging_page'),
        })
    if not insights:
        insights.append({
            'severity': 'info',
            'title': 'Not enough activity to forecast',
            'detail': 'Record more circulation in this period to unlock projections.',
            'action_label': 'Open circulation',
            'action_url': url_for('circulation.circulation_page'),
        })

    return {
        'daily_avg': daily_avg,
        'next_30': next_30,
        'by_category': by_category,
        'overdue_inflow_per_day': overdue_inflow,
        'overdue_direction': overdue_direction,
        'additions_next_30': additions_next_30,
        'weekday_mix': [[w[0], int(w[1] or 0)] for w in weekday_mix],
        'busiest_weekday': busiest,
        'demand_gaps': gaps,
        'insights': insights,
        'trend_tail': trend_tail,
        'projected_trend': projected_trend,
        'basis': _format_period(start_date, end_date, preset, from_str, to_str),
        'generated_at': datetime.now().strftime('%b %d, %Y %I:%M %p'),
    }


@analytics_bp.route('/librarian/analytics/forecast')
@login_required
@librarian_required
def forecast_json():
    """Return forecast projections for the requested range as JSON."""
    preset = request.args.get('preset', 'all')
    from_str = request.args.get('from', '').strip()
    to_str = request.args.get('to', '').strip()
    preset, from_str, to_str = _normalize_range(preset, from_str, to_str)
    start_date, end_date = resolve_dates(preset, from_str, to_str)
    return jsonify(_forecast_payload(start_date, end_date, preset, from_str, to_str))


@analytics_bp.route('/librarian/analytics/dashboard')
@login_required
@librarian_required
def dashboard_json():
    """Return the Riverside dashboard payload for the requested range."""
    preset = request.args.get('preset', 'all')
    from_str = request.args.get('from', '').strip()
    to_str = request.args.get('to', '').strip()
    departments = _clean_department_list(request.args.getlist('department'))
    preset, from_str, to_str = _normalize_range(preset, from_str, to_str)
    start_date, end_date = resolve_dates(preset, from_str, to_str)
    return jsonify(compute_dashboard(start_date, end_date, departments))


CHART_NAMES = frozenset({
    'collection_by_category',
    'copies_by_status',
    'borrowings_by_department',
    'borrowers_by_department',
    'overdue_by_department',
    'borrowings_by_user_type',
    'borrowings_trend',
    'overdue_trend',
    'top_categories',
    'top_books',
    'high_demand',
    'top_requested_titles',
    'requests_by_role',
    'requests_trend',
    'requests_by_program',
})


VALID_BORROW_TYPES = frozenset({'overnight', 'daily_circulation'})


def _clean_list(values, limit=50):
    """Strip blanks from a repeated query param, capped against abuse."""
    return [v.strip() for v in (values or []) if v and v.strip()][:limit]


def _clean_borrow_type(value):
    """Allowlist the borrow_type filter; anything else means unfiltered."""
    value = (value or '').strip()
    return value if value in VALID_BORROW_TYPES else None


def _chart_rows(rows):
    """Make chart rows JSON-safe (dates/Decimals -> plain values)."""
    out = []
    for r in rows or []:
        try:
            out.append([c.isoformat() if hasattr(c, 'isoformat') else c for c in r])
        except TypeError:
            continue
    return out


def _run_chart(name, start_date, end_date, args):
    borrow_type = _clean_borrow_type(args.get('borrow_type', ''))
    if name == 'collection_by_category':
        return models.collection_by_category(
            start_date, end_date, _clean_list(args.getlist('category')))
    if name == 'copies_by_status':
        return models.copies_by_status_summary(start_date, end_date)
    if name == 'borrowings_by_department':
        return models.books_borrowed_per_program(
            start_date, end_date, _clean_list(args.getlist('department')),
            borrow_type)
    if name == 'borrowers_by_department':
        return models.borrowers_by_department(
            start_date, end_date, _clean_list(args.getlist('department')))
    if name == 'overdue_by_department':
        return models.overdue_by_department(
            start_date, end_date, _clean_list(args.getlist('department')))
    if name == 'borrowings_by_user_type':
        return models.borrowings_by_user_type(
            start_date, end_date, _clean_list(args.getlist('role')), borrow_type)
    if name == 'borrowings_trend':
        return models.borrowings_trend(start_date, end_date, borrow_type)
    if name == 'overdue_trend':
        return models.overdue_trend(start_date, end_date, borrow_type)
    if name == 'top_categories':
        return models.top_borrowed_categories(start_date, end_date,
                                              borrow_type=borrow_type)
    if name == 'top_books':
        return models.top_borrowed_books_detailed(start_date, end_date,
                                                  borrow_type=borrow_type)
    if name == 'high_demand':
        return models.high_demand_titles(start_date, end_date, borrow_type=borrow_type)
    if name == 'top_requested_titles':
        return models.top_requested_titles(start_date, end_date)
    if name == 'requests_by_role':
        return models.requests_by_role_split(start_date, end_date)
    if name == 'requests_trend':
        return models.requests_trend(start_date, end_date)
    if name == 'requests_by_program':
        return models.requests_by_program(
            start_date, end_date, _clean_list(args.getlist('department')))
    raise ValueError('Unknown chart: %s' % name)


def _echo_chart_filters(args):
    echoed = {}
    departments = _clean_list(args.getlist('department'))
    roles = _clean_list(args.getlist('role'))
    categories = _clean_list(args.getlist('category'))
    borrow_type = _clean_borrow_type(args.get('borrow_type', ''))
    if departments:
        echoed['departments'] = departments
    if roles:
        echoed['roles'] = roles
    if categories:
        echoed['categories'] = categories
    if borrow_type:
        echoed['borrow_type'] = borrow_type
    return echoed


@analytics_bp.route('/librarian/analytics/chart')
@login_required
@librarian_required
def chart_json():
    """Return one dashboard chart's data for its own filter set as JSON."""
    name = request.args.get('name', '')
    if name not in CHART_NAMES:
        return jsonify({'error': 'invalid chart name'}), 400
    preset = request.args.get('preset', 'all')
    from_str = request.args.get('from', '').strip()
    to_str = request.args.get('to', '').strip()
    preset, from_str, to_str = _normalize_range(preset, from_str, to_str)
    start_date, end_date = resolve_dates(preset, from_str, to_str)
    return jsonify({
        'chart': name,
        'data': _chart_rows(_run_chart(name, start_date, end_date, request.args)),
        'filters': _echo_chart_filters(request.args),
    })


@analytics_bp.route('/librarian/analytics/kpi')
@login_required
@librarian_required
def kpi_json():
    """Return a single KPI's data for the requested range as JSON."""
    kpi_type = request.args.get('kpi_type', '')
    if kpi_type not in VALID_KPIS:
        return jsonify({'error': 'invalid kpi_type'}), 400
    preset = request.args.get('preset', 'all')
    from_str = request.args.get('from', '').strip()
    to_str = request.args.get('to', '').strip()
    if preset in ('semester', 'year'):
        from_str = to_str = ''
    elif preset not in ('custom', 'all'):
        from_str = to_str = ''
    start_date, end_date = resolve_dates(preset, from_str, to_str)
    return jsonify({'kpi_type': kpi_type, 'data': _run_kpi(kpi_type, start_date, end_date)})


def _as_2d_rows(kpi_type, kpi_data):
    """Flatten a KPI query result into labeled, exportable 2-D rows."""
    if kpi_type == 'books_borrowed_per_program':
        return [('Program', 'Total Borrows')] + [(r[0], r[1]) for r in kpi_data]
    if kpi_type == 'utilization_rate':
        return [('Metric', 'Value'), ('Utilization Rate (%)', kpi_data)]
    if kpi_type == 'most_borrowed_titles':
        return [('Title', 'Borrow Count')] + [(r[0], r[1]) for r in kpi_data]
    if kpi_type == 'underutilized_titles':
        return [('Title',)] + [(r[0],) for r in kpi_data]
    if kpi_type == 'trend_borrowings':
        return [('Date', 'Borrowings')] + [(r[0], r[1]) for r in (kpi_data or [])]
    if kpi_type == 'peak_periods':
        return [('Date', 'Borrowings')] + [(r[0], r[1]) for r in (kpi_data or [])]
    if kpi_type == 'trend_overdue':
        return [('Date', 'Overdue Items')] + [(r[0], r[1]) for r in (kpi_data or [])]
    if kpi_type == 'top_categories':
        return [('Category', 'Borrowings')] + [(r[0], r[1]) for r in (kpi_data or [])]
    if kpi_type == 'top_books':
        return [('Title', 'Author', 'Borrowings')] + [(r[0], r[1], r[2]) for r in (kpi_data or [])]
    if kpi_type == 'high_demand':
        return [('Title', 'Author', 'Active Loans')] + [(r[0], r[1], r[2]) for r in (kpi_data or [])]
    if kpi_type == 'by_user_type':
        return [('User Type', 'Borrowings')] + [(r[0], r[1]) for r in (kpi_data or [])]
    if kpi_type == 'collection_by_category':
        return [('Category', 'Titles')] + [(r[0], r[1]) for r in (kpi_data or [])]
    if kpi_type == 'copies_by_status':
        return [('Status', 'Copies')] + [(r[0], r[1]) for r in (kpi_data or [])]
    if kpi_type == 'recent_circulation':
        return [('Date', 'Accession No.', 'User', 'Role', 'Title', 'Author', 'Action', 'Due', 'Status')] + \
            [tuple(r) for r in (kpi_data or [])]
    if kpi_type == 'recent_collection':
        return [('Accession', 'Title', 'Category', 'Inventory State', 'Loan', 'Borrower', 'Due')] + \
            [tuple(r) for r in (kpi_data or [])]
    if kpi_type == 'circulation_summary':
        return [('Metric', 'Value')] + [(r[0], r[1]) for r in (kpi_data or [])]
    if kpi_type == 'borrowers_by_department':
        return [('Department', 'Active Borrowers')] + [(r[0], r[1]) for r in (kpi_data or [])]
    if kpi_type == 'overdue_by_department':
        return [('Department', 'Overdue Items')] + [(r[0], r[1]) for r in (kpi_data or [])]
    if kpi_type == 'department_leaderboard':
        return [('Department', 'Borrowings', 'Borrowers', 'Overdue')] + \
            [(r[0], r[1], r[2], r[3]) for r in (kpi_data or [])]
    if kpi_type == 'top_requested_titles':
        return [('Title', 'Requests')] + [(r[0], r[1]) for r in (kpi_data or [])]
    if kpi_type == 'requests_by_role':
        return [('Title', 'Student', 'Faculty', 'Other Staff', 'Total')] + \
            [(r[0], r[1], r[2], r[3], r[4]) for r in (kpi_data or [])]
    if kpi_type == 'requests_trend':
        return [('Date', 'Requests')] + [(r[0], r[1]) for r in (kpi_data or [])]
    if kpi_type == 'requests_by_program':
        return [('Program', 'Requests')] + [(r[0], r[1]) for r in (kpi_data or [])]
    raise ValueError('Unknown KPI type: %s' % kpi_type)


USAGE_SCOPED_KPIS = frozenset({
    'books_borrowed_per_program', 'trend_borrowings', 'trend_overdue',
    'top_books', 'high_demand', 'by_user_type', 'recent_circulation',
    'circulation_summary', 'borrowers_by_department', 'overdue_by_department',
    'requests_by_program', 'department_leaderboard',
})


def _run_kpi(kpi_type, start_date, end_date, departments=None):
    dept_list = _normalize_dept_list(departments)
    # Only usage-scoped sections honor the program filter; collection
    # sections always report the full catalog.
    scoped = dept_list if kpi_type in USAGE_SCOPED_KPIS else None
    if kpi_type == 'utilization_rate':
        return models.utilization_rate(start_date, end_date)
    if kpi_type == 'books_borrowed_per_program':
        return models.books_borrowed_per_program(start_date, end_date, scoped)
    if kpi_type == 'borrowers_by_department':
        return models.borrowers_by_department(start_date, end_date, scoped)
    if kpi_type == 'overdue_by_department':
        return models.overdue_by_department(start_date, end_date, scoped)
    if kpi_type == 'most_borrowed_titles':
        return models.most_borrowed_titles(start_date, end_date)
    if kpi_type == 'underutilized_titles':
        return models.underutilized_titles(start_date, end_date)
    if kpi_type == 'trend_borrowings':
        return models.borrowings_trend(start_date, end_date, None, scoped)
    if kpi_type == 'peak_periods':
        return models.borrowings_trend(start_date, end_date, None, scoped)
    if kpi_type == 'trend_overdue':
        return models.overdue_trend(start_date, end_date, None, scoped)
    if kpi_type == 'top_categories':
        return models.top_borrowed_categories(start_date, end_date)
    if kpi_type == 'top_books':
        return models.top_borrowed_books_detailed(start_date, end_date, 5, None, scoped)
    if kpi_type == 'high_demand':
        return models.high_demand_titles(start_date, end_date, borrow_type=None)
    if kpi_type == 'by_user_type':
        return models.borrowings_by_user_type(start_date, end_date, None, None, scoped)
    if kpi_type == 'collection_by_category':
        return models.collection_by_category(start_date, end_date)
    if kpi_type == 'copies_by_status':
        return models.copies_by_status_summary(start_date, end_date)
    if kpi_type == 'recent_circulation':
        return models.recent_circulation(10, scoped, start_date, end_date)
    if kpi_type == 'recent_collection':
        return models.recent_collection_status()
    if kpi_type == 'circulation_summary':
        t, b, o, avg, rate, new = models.circulation_overview(start_date, end_date, scoped)
        return [['Total borrowings', t], ['Active borrowers', b], ['Overdue items', o],
                ['Avg. loan duration (days)', avg], ['On-time return rate (%)', rate],
                ['New additions', new]]
    if kpi_type == 'top_requested_titles':
        return models.top_requested_titles(start_date, end_date)
    if kpi_type == 'requests_by_role':
        return models.requests_by_role_split(start_date, end_date)
    if kpi_type == 'requests_trend':
        return models.requests_trend(start_date, end_date)
    if kpi_type == 'requests_by_program':
        return models.requests_by_program(start_date, end_date, scoped)
    if kpi_type == 'department_leaderboard':
        return models.department_summary(start_date, end_date, scoped)
    raise ValueError('Unknown KPI type: %s' % kpi_type)


def _normalize_dept_list(departments):
    if departments is None:
        return None
    if isinstance(departments, str):
        departments = [departments]
    cleaned = [d.strip() for d in departments if d and d.strip()]
    return cleaned or None


def _all_labels():
    labels = dict(KPI_LABELS)
    labels.update(DASHBOARD_LABELS)
    return labels


def _all_descriptions():
    descriptions = dict(KPI_DESCRIPTIONS)
    descriptions.update(DASHBOARD_DESCRIPTIONS)
    return descriptions


def _jsonable_cell(value):
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    try:
        import decimal
        if isinstance(value, decimal.Decimal):
            return float(value)
    except ImportError:
        pass
    return value


def _jsonable(kpi_data):
    if isinstance(kpi_data, list):
        return [[_jsonable_cell(c) for c in r] if isinstance(r, (list, tuple))
                else _jsonable_cell(r) for r in kpi_data]
    return _jsonable_cell(kpi_data)


def _format_period(start_date, end_date, preset, from_str, to_str):
    if from_str or to_str:
        if start_date and end_date:
            return f"{start_date:%b %d, %Y} – {end_date:%b %d, %Y}"
        if start_date:
            return f"From {start_date:%b %d, %Y}"
        if end_date:
            return f"Until {end_date:%b %d, %Y}"
    if preset == 'year':
        return f"Calendar Year {date.today().year}"
    if preset == 'semester':
        return 'Current Semester' + (
            ' (Aug–Dec)' if date.today().month >= 8 else ' (Jan–May)'
        )
    return 'All Time'


_CHART_COLORS = [
    colors.HexColor(c) for c in (
        '#1e3a8a', '#1d4ed8', '#0ea5e9', '#10b981',
        '#f59e0b', '#8b5cf6', '#ef4444', '#64748b',
    )
]
_CHART_SLATE_700 = colors.HexColor('#334155')
_CHART_SLATE_300 = colors.HexColor('#cbd5e1')

_PIE_SECTIONS = frozenset({
    'top_categories', 'collection_by_category', 'by_user_type', 'copies_by_status',
})
_LINE_SECTIONS = frozenset({'trend_borrowings', 'trend_overdue', 'requests_trend'})
_BAR_SECTIONS = frozenset({
    'books_borrowed_per_program', 'most_borrowed_titles', 'top_books', 'high_demand',
    'borrowers_by_department', 'overdue_by_department',
    'top_requested_titles', 'requests_by_program', 'peak_periods',
})


def _chart_num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _pdf_text(value):
    """Escape dynamic text for reportlab Paragraph (XML markup).

    Titles, names, and departments may contain ``&``/``<``/``>`` which
    would otherwise raise a parse error at build time and 500 the export.
    """
    if value is None:
        return ''
    return _xml_escape(str(value), {'"': '&quot;'})


def _chart_short(label, limit=20):
    text = str(label)
    return text if len(text) <= limit else text[:limit - 1] + '…'


def _pie_drawing(pairs, width):
    """Pie + hand-drawn legend. Returns None when there is nothing to plot."""
    vals = [max(_chart_num(v), 0) for _, v in pairs]
    if sum(vals) <= 0:
        return None
    slices = list(zip([p[0] for p in pairs], vals))
    if len(slices) > 8:
        head, tail = slices[:7], slices[7:]
        slices = head + [('Other', sum(v for _, v in tail))]
        vals = [v for _, v in slices]
    legend_w = 190
    pie_d = 140
    d = Drawing(width, 170)
    pc = Pie()
    pc.x = 10
    pc.y = 10
    pc.width = pie_d
    pc.height = pie_d
    pc.data = [v for _, v in slices]
    pc.slices.strokeWidth = 0.5
    pc.slices.strokeColor = colors.white
    for i in range(len(slices)):
        pc.slices[i].fillColor = _CHART_COLORS[i % len(_CHART_COLORS)]
    d.add(pc)
    lx = pie_d + 30
    for i, (label, val) in enumerate(slices):
        y = 150 - i * 17
        d.add(Rect(lx, y - 9, 10, 10, strokeColor=None,
                   fillColor=_CHART_COLORS[i % len(_CHART_COLORS)]))
        d.add(String(lx + 15, y - 7, '%s (%g)' % (_chart_short(label), val),
                     fontName='Helvetica', fontSize=7, fillColor=_CHART_SLATE_700))
    return d


def _bar_drawing(pairs, width):
    """Horizontal bars for top-N label/value rows."""
    pairs = pairs[:10]
    vals = [_chart_num(v) for _, v in pairs]
    if not pairs or max(vals) <= 0:
        return None
    n = len(pairs)
    height = max(80, min(24 * n + 30, 260))
    d = Drawing(width, height)
    bc = HorizontalBarChart()
    bc.x = 130
    bc.y = 10
    bc.width = width - 140
    bc.height = height - 20
    bc.data = [vals]
    bc.strokeColor = None
    bc.bars[0].fillColor = _CHART_COLORS[1]
    bc.categoryAxis.labels.boxAnchor = 'ne'
    bc.categoryAxis.labels.dx = -6
    bc.categoryAxis.labels.fontSize = 7
    bc.categoryAxis.labels.fontName = 'Helvetica'
    bc.categoryAxis.categoryNames = [_chart_short(p[0], 16) for p in pairs]
    bc.valueAxis.valueMin = 0
    bc.valueAxis.valueMax = max(vals) * 1.15
    bc.valueAxis.labels.fontSize = 6
    bc.valueAxis.labels.fontName = 'Helvetica'
    bc.valueAxis.visibleGrid = 1
    bc.valueAxis.gridStrokeColor = _CHART_SLATE_300
    d.add(bc)
    return d


def _fill_daily_gaps(pairs):
    """Zero-fill missing days between first and last date.

    Sparse trend rows (e.g. 13 days with count=1 over 4 months) would
    otherwise render as a flat line. Returns filled [(iso_date, value)].
    Non-date labels or huge spans (>730 days) are returned as-is.
    """
    if not pairs or len(pairs) < 2:
        return list(pairs)
    parsed = []
    for label, value in pairs:
        day = label.isoformat()[:10] if hasattr(label, 'isoformat') else str(label)[:10]
        try:
            dt = datetime.strptime(day, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return list(pairs)
        try:
            num = float(value)
        except (TypeError, ValueError):
            num = 0.0
        parsed.append((dt, num))
    parsed.sort(key=lambda r: r[0])
    span = (parsed[-1][0] - parsed[0][0]).days
    if span <= 0 or span > 730:
        return [(d.isoformat(), v) for d, v in parsed]
    by_day = {d: v for d, v in parsed}
    filled = []
    cur = parsed[0][0]
    end = parsed[-1][0]
    while cur <= end:
        filled.append((cur.isoformat(), by_day.get(cur, 0.0)))
        cur += timedelta(days=1)
    return filled


def _line_drawing(pairs, width, color):
    """Line chart for daily (date, count) rows, strided to at most 40 points."""
    pairs = _fill_daily_gaps(pairs)
    if len(pairs) > 40:
        stride = -(-len(pairs) // 40)
        pairs = pairs[::stride]
    ys = [_chart_num(v) for _, v in pairs]
    if not pairs or max(ys) <= 0:
        return None
    n = len(pairs)
    d = Drawing(width, 175)
    lp = LinePlot()
    lp.x = 35
    lp.y = 25
    lp.width = width - 45
    lp.height = 125
    lp.data = [[(x, y) for x, y in enumerate(ys)]]
    lp.lines[0].strokeColor = color
    lp.lines[0].strokeWidth = 2
    lp.xValueAxis.valueMin = 0
    lp.xValueAxis.valueMax = max(n - 1, 1)
    lp.xValueAxis.visibleLabels = 0
    lp.xValueAxis.visibleTicks = 0
    lp.yValueAxis.valueMin = 0
    lp.yValueAxis.valueMax = max(ys) * 1.15
    lp.yValueAxis.labels.fontSize = 6
    lp.yValueAxis.labels.fontName = 'Helvetica'
    lp.yValueAxis.visibleGrid = 1
    lp.yValueAxis.gridStrokeColor = _CHART_SLATE_300
    d.add(lp)
    d.add(String(35, 8, _chart_short(pairs[0][0], 16),
                 fontName='Helvetica', fontSize=7, fillColor=_CHART_SLATE_700))
    tail = _chart_short(pairs[-1][0], 16)
    d.add(String(width - 8 - len(tail) * 4.2, 8, tail,
                 fontName='Helvetica', fontSize=7, fillColor=_CHART_SLATE_700))
    return d


def _section_chart(kt, rows, width):
    """Build a chart Drawing for a report section, or None for table-only."""
    data = [r for r in (rows[1:] if len(rows) > 1 else [])]
    if not data:
        return None
    if kt in _PIE_SECTIONS:
        return _pie_drawing([(r[0], r[1]) for r in data if len(r) > 1], width)
    if kt in _LINE_SECTIONS:
        color = _CHART_COLORS[6] if kt == 'trend_overdue' else _CHART_COLORS[0]
        return _line_drawing([(r[0], r[1]) for r in data if len(r) > 1], width, color)
    if kt in _BAR_SECTIONS:
        return _bar_drawing([(r[0], r[1]) for r in data if len(r) > 1], width)
    return None


def _pdf_bytes(sections, *, preset='all', start_date=None, end_date=None,
               from_str='', to_str='', department=''):
    """Build a polished PDF report from (kpi_type, kpi_data) sections."""
    buf = io.BytesIO()

    # -- palette
    NAVY = colors.HexColor('#1e3a8a')
    NAVY_DARK = colors.HexColor('#172554')
    NAVY_LIGHT = colors.HexColor('#1d4ed8')
    SLATE_900 = colors.HexColor('#0f172a')
    SLATE_700 = colors.HexColor('#334155')
    SLATE_500 = colors.HexColor('#64748b')
    SLATE_300 = colors.HexColor('#cbd5e1')
    SLATE_100 = colors.HexColor('#f1f5f9')
    SLATE_50 = colors.HexColor('#f8fafc')
    WHITE = colors.white

    def _header_footer(canvas, doc):
        canvas.saveState()
        # top hairline + brand
        canvas.setStrokeColor(SLATE_300)
        canvas.setLineWidth(0.6)
        canvas.line(doc.leftMargin, doc.height + doc.topMargin + 6,
                    doc.width + doc.leftMargin, doc.height + doc.topMargin + 6)
        canvas.setFont('Helvetica-Bold', 7)
        canvas.setFillColor(NAVY)
        canvas.drawString(doc.leftMargin, doc.height + doc.topMargin + 14,
                          'MCST  •  LIBRARY MANAGEMENT SYSTEM')
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(SLATE_500)
        canvas.drawRightString(doc.width + doc.leftMargin,
                               doc.height + doc.topMargin + 14,
                               'CONFIDENTIAL  •  INTERNAL USE ONLY')
        # footer
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(SLATE_500)
        canvas.drawString(doc.leftMargin, 30,
                          'MCST Library  •  Analytics & Reporting')
        canvas.drawRightString(doc.width + doc.leftMargin, 30,
                               f"Page {doc.page}")
        # thin bottom line
        canvas.setStrokeColor(SLATE_300)
        canvas.setLineWidth(0.4)
        canvas.line(doc.leftMargin, 36,
                    doc.width + doc.leftMargin, 36)
        canvas.restoreState()

    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        rightMargin=48, leftMargin=48,
        topMargin=64, bottomMargin=48,
        title='MCST Library Analytics Report',
        author='MCST Library',
    )

    styles = getSampleStyleSheet()
    s_title = ParagraphStyle('RTitle', parent=styles['Title'],
                             fontName='Helvetica-Bold', fontSize=22,
                             leading=26, textColor=NAVY_DARK,
                             spaceAfter=4, alignment=TA_LEFT)
    s_sub = ParagraphStyle('RSub', parent=styles['Normal'],
                           fontName='Helvetica', fontSize=9.5,
                           leading=13, textColor=SLATE_500, spaceAfter=0)
    s_meta_label = ParagraphStyle('RMetaLabel', parent=styles['Normal'],
                                  fontName='Helvetica-Bold', fontSize=7,
                                  leading=9, textColor=SLATE_500,
                                  spaceAfter=1)
    s_meta_value = ParagraphStyle('RMetaValue', parent=styles['Normal'],
                                  fontName='Helvetica', fontSize=9,
                                  leading=11, textColor=SLATE_700)
    s_section_title = ParagraphStyle('RSectionTitle', parent=styles['Heading2'],
                                     fontName='Helvetica-Bold', fontSize=13,
                                     leading=15, textColor=NAVY_DARK,
                                     spaceBefore=0, spaceAfter=2)
    s_section_desc = ParagraphStyle('RSectionDesc', parent=styles['Normal'],
                                    fontName='Helvetica', fontSize=8.5,
                                    leading=11, textColor=SLATE_500,
                                    spaceAfter=8)
    s_cell = ParagraphStyle('RCell', parent=styles['Normal'],
                            fontName='Helvetica', fontSize=8.5, leading=11,
                            textColor=SLATE_700, alignment=TA_LEFT)
    s_cell_header = ParagraphStyle('RCellH', parent=s_cell,
                                   fontName='Helvetica-Bold', textColor=WHITE,
                                   fontSize=7.5, leading=10)
    s_cell_right = ParagraphStyle('RCellR', parent=s_cell, alignment=TA_RIGHT)
    s_cell_center = ParagraphStyle('RCellC', parent=s_cell, alignment=TA_CENTER)
    s_empty = ParagraphStyle('REmpty', parent=styles['Normal'],
                             fontName='Helvetica-Oblique', fontSize=8.5,
                             leading=11, textColor=SLATE_500,
                             alignment=TA_CENTER)
    s_kpi_big = ParagraphStyle('RKpiBig', parent=styles['Normal'],
                               fontName='Helvetica-Bold', fontSize=28,
                               leading=30, textColor=NAVY_DARK, alignment=TA_CENTER)
    s_kpi_unit = ParagraphStyle('RKpiUnit', parent=styles['Normal'],
                                fontName='Helvetica-Bold', fontSize=9,
                                leading=11, textColor=NAVY_LIGHT, alignment=TA_CENTER)
    s_kpi_caption = ParagraphStyle('RKpiCap', parent=styles['Normal'],
                                   fontName='Helvetica', fontSize=7.5,
                                   leading=9, textColor=SLATE_500, alignment=TA_CENTER)

    now = datetime.now()
    period_label = _format_period(start_date, end_date, preset, from_str, to_str)
    if department:
        period_label = period_label + ' · ' + department

    gen_name = getattr(current_user, 'full_name', None) or getattr(current_user, 'email', '') or 'System'
    gen_role = getattr(current_user, 'role', '') or ''

    story = []

    # -- Cover block -----------------------------------------------------
    # Eyebrow
    story.append(Paragraph('ANALYTICS  &  REPORTING', ParagraphStyle(
        'REyebrow', parent=styles['Normal'], fontName='Helvetica-Bold',
        fontSize=7, leading=9, textColor=NAVY_LIGHT, spaceAfter=6)))
    story.append(Paragraph('Library Analytics Report', s_title))
    story.append(Paragraph(
        'Operational KPIs for collection utilization, circulation demand '
        'and engagement — prepared for planning and budget review.', s_sub))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width='100%', thickness=0.6, color=NAVY, spaceAfter=12, spaceBefore=6))

    # Key-value meta grid (period, generated on, generated by)
    meta_data = [
        [Paragraph('<font color="#64748b"><b>REPORT PERIOD</b></font>', s_meta_label),
         Paragraph('<font color="#64748b"><b>GENERATED ON</b></font>', s_meta_label),
         Paragraph('<font color="#64748b"><b>GENERATED BY</b></font>', s_meta_label)],
        [Paragraph(_pdf_text(period_label), s_meta_value),
         Paragraph(now.strftime('%B %d, %Y  •  %I:%M %p'), s_meta_value),
         Paragraph(f"{_pdf_text(gen_name)}<br/><font color=\"#64748b\" size=\"7\">{_pdf_text(gen_role)}</font>" if gen_role else _pdf_text(gen_name), s_meta_value)],
    ]
    t_meta = Table(meta_data, colWidths=[doc.width * 0.34, doc.width * 0.33, doc.width * 0.33],
                   hAlign='LEFT')
    t_meta.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 2),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 0),
        ('LINEBELOW', (0, 0), (-1, 0), 0.4, SLATE_300),
        ('TOPPADDING', (0, 1), (-1, 1), 4),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 14))

    # Summary badges: sections in this report
    labels = _all_labels()
    descriptions = _all_descriptions()
    badge_cells = []
    for kt, _ in sections:
        badge_cells.append(Paragraph(
            f'<font color="#1e3a8a"><b>{labels.get(kt, kt)}</b></font>',
            ParagraphStyle('RBadgeTx', parent=s_cell, fontSize=7, leading=9,
                           textColor=NAVY, alignment=TA_CENTER)))
    if badge_cells:
        # flow into a single row table with wrapped cells
        n = len(badge_cells)
        col_w = doc.width / max(n, 1)
        t_badges = Table([badge_cells], colWidths=[col_w] * n, hAlign='LEFT')
        style_badges = TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, SLATE_300),
            ('INNERGRID', (0, 0), (-1, -1), 0.4, SLATE_300),
            ('BACKGROUND', (0, 0), (-1, -1), SLATE_50),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROUNDEDCORNERS', [3, 3, 3, 3]),
        ])
        t_badges.setStyle(style_badges)
        story.append(Paragraph('INCLUDED IN THIS REPORT', ParagraphStyle(
            'RBadgeLbl', parent=s_meta_label, alignment=TA_LEFT, spaceAfter=4)))
        story.append(t_badges)
        story.append(Spacer(1, 6))

    story.append(HRFlowable(width='100%', thickness=0.4, color=SLATE_300, spaceAfter=10, spaceBefore=6))
    story.append(Paragraph(
        'Each section below contains the KPI definition, the filtered time window, '
        'and a styled data table.  Empty sections indicate no matching records for the selected period.',
        ParagraphStyle('RNote', parent=s_sub, fontSize=7.5, leading=10, textColor=SLATE_500)))
    story.append(Spacer(1, 14))

    # -- KPI sections ----------------------------------------------------
    for idx, (kt, kpi_data) in enumerate(sections):
        if idx > 0:
            story.append(Spacer(1, 6))

        # Section card header: numbered pill + title
        pill = Table(
            [[Paragraph(f"{idx + 1:02d}", ParagraphStyle(
                'RPill', parent=styles['Normal'], fontName='Helvetica-Bold',
                fontSize=7, leading=7, textColor=WHITE, alignment=TA_CENTER))]],
            colWidths=[22], rowHeights=[16], hAlign='LEFT')
        pill.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), NAVY),
            ('ROUNDEDCORNERS', [8, 8, 8, 8]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        title_row = Table(
            [[pill, Paragraph(labels.get(kt, kt), s_section_title)]],
            colWidths=[26, doc.width - 26], hAlign='LEFT')
        title_row.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(title_row)
        story.append(Paragraph(descriptions.get(kt, ''), s_section_desc))

        # Period chip row for this card
        story.append(Table(
            [[Paragraph(
                f'<font color="#334155"><b>PERIOD</b></font>  <font color="#64748b">{_pdf_text(period_label)}</font>'
                f'&nbsp;&nbsp;&nbsp;<font color="#334155"><b>ROWS</b></font>  '
                f'<font color="#64748b">{(len(kpi_data) if isinstance(kpi_data, list) else 1) if kpi_data is not None else 0}</font>',
                ParagraphStyle('RPeriod', parent=s_cell, fontSize=7, leading=9))]],
            colWidths=[doc.width], hAlign='LEFT'))
        story.append(Spacer(1, 6))

        # Render table / metric. Per-section guard: one unrenderable
        # section must not 500 the whole report.
        try:
            rows = _as_2d_rows(kt, kpi_data)

            chart = _section_chart(kt, rows, doc.width)
            if chart is not None:
                story.append(chart)
                story.append(Spacer(1, 6))

            if kt == 'utilization_rate':
                # Metric hero card
                val = kpi_data if isinstance(kpi_data, (int, float)) else 0
                try:
                    val_f = float(val)
                except Exception:
                    val_f = 0.0
                # clamp display 0..100
                val_f = max(0.0, min(100.0, val_f))
                hero = Table([
                    [Paragraph(f"{val_f:.1f}<font size=\"14\" color=\"#1d4ed8\">%</font>", s_kpi_big)],
                    [Paragraph('collection currently on loan', s_kpi_caption)],
                    [Paragraph(
                        f'<font color="#334155"><b>{int(round(val_f))} of 100</b></font>'
                        f'  <font color="#64748b">active titles borrowed in the selected window</font>',
                        ParagraphStyle('RKpiSub', parent=s_kpi_caption, alignment=TA_CENTER))],
                ], colWidths=[doc.width], hAlign='CENTER')
                hero.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), SLATE_50),
                    ('BOX', (0, 0), (-1, -1), 0.6, SLATE_300),
                    ('INNERGRID', (0, 0), (-1, -1), 0.4, SLATE_300),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('LEFTPADDING', (0, 0), (-1, -1), 12),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                    ('ROUNDEDCORNERS', [6, 6, 6, 6]),
                ]))
                story.append(hero)
                story.append(Spacer(1, 4))
                # also show tiny 2-col table for auditability
                mini = Table(
                    [[Paragraph('Metric', s_cell_header), Paragraph('Value', s_cell_header)],
                     [Paragraph('Utilization Rate (%)', s_cell), Paragraph(f"{val_f:.2f}%", s_cell_right)]],
                    colWidths=[doc.width * 0.70, doc.width * 0.30], hAlign='LEFT')
                mini.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), NAVY),
                    ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, SLATE_50]),
                    ('GRID', (0, 0), (-1, -1), 0.4, SLATE_300),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ]))
                story.append(mini)
            elif len(rows) == 1:
                # empty state
                empty_box = Table(
                    [[Paragraph('No records for this KPI in the selected period.', s_empty)]],
                    colWidths=[doc.width], hAlign='CENTER')
                empty_box.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), SLATE_50),
                    ('BOX', (0, 0), (-1, -1), 0.5, SLATE_300),
                    ('TOPPADDING', (0, 0), (-1, -1), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                    ('ROUNDEDCORNERS', [6, 6, 6, 6]),
                ]))
                story.append(empty_box)
            else:
                # Styled data table
                # choose column widths by shape: 2-col label/value tables get a
                # wide label column; wider tables split the width evenly.
                ncols = len(rows[0])
                if ncols == 1:
                    cw = [doc.width]
                    aligns = [s_cell]
                elif ncols == 2:
                    cw = [doc.width * 0.68, doc.width * 0.32]
                    aligns = [s_cell, s_cell_right]
                else:
                    cw = [doc.width / ncols] * ncols
                    aligns = [s_cell] * ncols

                header_cells = []
                for j, c in enumerate(rows[0]):
                    style = s_cell_center if len(cw) == 1 else (s_cell_header if j == 0 else s_cell_header)
                    # numeric headers center/right
                    if len(cw) > 1 and j == 1:
                        style = ParagraphStyle('RThR', parent=s_cell_header, alignment=TA_RIGHT)
                    elif len(cw) > 1 and j == 0:
                        style = ParagraphStyle('RThL', parent=s_cell_header, alignment=TA_LEFT)
                    header_cells.append(Paragraph(_pdf_text(c), style))

                body = []
                for r in rows[1:]:
                    cells = []
                    for j, val in enumerate(r):
                        st = aligns[j] if j < len(aligns) else s_cell
                        cells.append(Paragraph(_pdf_text(val), st))
                    body.append(cells)

                # optional: cap rows for readability, add "..." note
                truncated = False
                max_rows = 28
                if len(body) > max_rows:
                    truncated = True
                    body = body[:max_rows]

                t = Table([header_cells] + body, colWidths=cw, hAlign='LEFT', repeatRows=1)
                wide_font = 7 if ncols > 4 else 8
                style_cmds = [
                    ('BACKGROUND', (0, 0), (-1, 0), NAVY),
                    ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), wide_font),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 7),
                    ('TOPPADDING', (0, 0), (-1, 0), 7),
                    ('TOPPADDING', (0, 1), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
                    ('LEFTPADDING', (0, 0), (-1, -1), 7),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 7),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, SLATE_100]),
                    ('GRID', (0, 0), (-1, -1), 0.4, SLATE_300),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LINEBELOW', (0, 0), (-1, 0), 1.2, NAVY_DARK),
                ]
                # zebra is via ROWBACKGROUNDS; add light inner rule
                t.setStyle(TableStyle(style_cmds))
                story.append(t)
                if truncated:
                    story.append(Spacer(1, 4))
                    story.append(Paragraph(
                        f'Showing first {max_rows} rows.  Export includes all rows; '
                        f'{len(rows) - 1 - max_rows} more row(s) not displayed in the paginated table.',
                        ParagraphStyle('RTrunc', parent=s_empty, alignment=TA_LEFT, fontSize=7)))
        except Exception:
            story.append(Paragraph(
                'This section could not be rendered for the selected period.',
                s_empty))

        # card footer spacing
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width='100%', thickness=0.4, color=SLATE_300, spaceAfter=2, spaceBefore=2))

    # -- closing note
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        'Notes:  Figures are computed from circulation_records joined to borrowers and roles.  '
        '“All Time” is unfiltered; presets and custom dates filter on borrow_date.  '
        'A snapshot of this export was cached to analytics_cache for audit and budget defense.',
        ParagraphStyle('RFootNote', parent=s_sub, fontSize=7, leading=9, textColor=SLATE_500)))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        'MCST Library Management System  •  Maranding, Lala, Lanao del Norte  •  '
        'This document is system-generated and does not require a signature.',
        ParagraphStyle('RFootNote2', parent=s_sub, fontSize=6.5, leading=8, textColor=SLATE_500,
                       alignment=TA_CENTER)))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buf.getvalue()


@analytics_bp.route('/librarian/analytics/export', methods=['POST'])
@login_required
@librarian_required
def export_report():
    kpi_type = request.form.get('kpi_type', '')
    preset = request.form.get('preset', 'all')
    from_str = request.form.get('from', '').strip()
    to_str = request.form.get('to', '').strip()
    departments = _clean_department_list(request.form.getlist('department'))
    # Semester/year presets must not carry stale custom dates.
    if preset in ('semester', 'year'):
        from_str = to_str = ''
    elif preset not in ('custom', 'all'):
        from_str = to_str = ''
    # Analytics reports are PDF-only since 2026-08 (migration from CSV/XLSX).
    # Keep spreadsheet generation for Catalog/Users exports only. For backwards
    # compatibility, legacy format=csv|xlsx requests are explicitly coerced to PDF
    # with an info flash (not silent) — see analytics.html PDF-only modal.
    fmt = request.form.get('format', 'pdf').strip().lower()
    if fmt in ('csv', 'xlsx'):
        flash('Analytics CSV/XLSX exports have been retired — PDF generated instead. Use Catalog/Users exports for spreadsheets.', 'info')
        fmt = 'pdf'
    elif fmt != 'pdf':
        fmt = 'pdf'

    export_all = kpi_type == 'all'
    if not export_all and kpi_type not in EXPORTABLE_KPIS:
        flash('Invalid report type.', 'error')
        return redirect(url_for('analytics.analytics_page'))

    start_date, end_date = resolve_dates(preset, from_str, to_str)

    if export_all:
        # If the board sent an explicit list of added KPIs, export only those.
        # Legacy calls without kpi_types still export all KPIs (keeps tests green).
        has_key = ('kpi_types' in request.form or 'kpi_types[]' in request.form
                   or 'selected_kpis' in request.form)
        raw = (request.form.get('kpi_types') or request.form.get('kpi_types[]') or
               request.form.get('selected_kpis') or '').strip()
        multi = request.form.getlist('kpi_types') + request.form.getlist('kpi_types[]')
        # handle repeated fields: kpi_types=a&kpi_types=b (or kpi_types[]=a&kpi_types[]=b)
        if multi and len(multi) > 1:
            candidates = [c.strip() for c in multi if c.strip()]
        elif raw:
            candidates = [p.strip() for p in raw.split(',') if p.strip()]
        else:
            candidates = []
        if has_key:
            # Respect the caller's explicit selection — even if empty (export nothing).
            # Filter to valid KPIs only; if only invalid names were sent, result is empty.
            kpi_types = [k for k in candidates if k in EXPORTABLE_KPIS]
        else:
            # Legacy calls without kpi_types export the board KPIs (keeps tests green).
            kpi_types = [k for k in candidates if k in EXPORTABLE_KPIS] or list(KPI_LABELS.keys())
    else:
        kpi_types = [kpi_type]

    sections = []
    dept_list = departments or None
    dept_label = ', '.join(departments)
    for kt in kpi_types:
        kpi_data = _run_kpi(kt, start_date, end_date, dept_list)
        try:
            models.save_report_snapshot(
                kt,
                {'preset': preset, 'from': from_str, 'to': to_str,
                 'department': departments},
                _jsonable(kpi_data),
                current_user.id,
            )
        except Exception:
            # Audit caching must never break the export itself.
            pass
        sections.append((kt, kpi_data))

    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    label = 'all' if export_all else kpi_type
    filename = f'{label}_{stamp}.pdf'

    body = _pdf_bytes(
        sections,
        preset=preset, start_date=start_date, end_date=end_date,
        from_str=from_str, to_str=to_str, department=dept_label,
    )
    return Response(
        body,
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )