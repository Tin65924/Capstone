import io
from datetime import date, datetime

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
    'top_books': 'Top Borrowed Books',
    'high_demand': 'Likely High-Demand Titles',
    'by_user_type': 'Borrowings by User Type',
    'collection_by_category': 'Collection by Category',
    'copies_by_status': 'Copies by Status',
    'recent_circulation': 'Recent Circulation Activity',
    'recent_collection': 'Recent Collection Status',
    'circulation_summary': 'Circulation Summary',
}

DASHBOARD_DESCRIPTIONS = {
    'trend_borrowings': 'Daily borrow counts in the selected period.',
    'trend_overdue': 'Daily overdue counts in the selected period.',
    'top_categories': 'Borrows grouped by subject classification.',
    'top_books': 'Most borrowed books with authors.',
    'high_demand': 'Active loans ranked by current demand.',
    'by_user_type': 'Borrows grouped by account role.',
    'collection_by_category': 'Active titles grouped by subject classification.',
    'copies_by_status': 'Physical copies grouped by availability status.',
    'recent_circulation': 'Latest circulation transactions.',
    'recent_collection': 'Latest accessioned copies with status.',
    'circulation_summary': 'Headline circulation totals for the period.',
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


def compute_dashboard(start_date, end_date):
    """Assemble Riverside-style dashboard payload from model queries.

    Returns JSON-serializable dicts/lists only (dates stringified); the
    template embeds it as ``dashboard-data`` and renders the three tabs
    client-side.  Missing tables/rows degrade to zeros/empty lists.
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
    available = max(total_copies - borrowed - overdue - lost_damaged - maintenance, 0)

    by_category = _pair(_safe(models.collection_by_category, start_date, end_date))
    by_user_type = _pair(_safe(models.borrowings_by_user_type, start_date, end_date))
    by_program = _pair(_safe(models.books_borrowed_per_program, start_date, end_date))
    trend = _pair(_safe(models.borrowings_trend, start_date, end_date))
    overdue_t = _pair(_safe(models.overdue_trend, start_date, end_date))
    top_cats = _pair(_safe(models.top_borrowed_categories, start_date, end_date))
    top_books = _triple(_safe(models.top_borrowed_books_detailed, start_date, end_date))
    high_demand = _triple(_safe(models.high_demand_titles, start_date, end_date))
    overview = _safe(models.circulation_overview, start_date, end_date)
    if not overview:
        overview = (0, 0, 0, 0.0, 0.0, 0)
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
        'usage': {
            'total': overview[0],
            'unique_borrowers': overview[1],
            'avg_per_borrower': round(overview[0] / overview[1], 2) if overview[1] else 0.0,
            'overdue': overview[2],
            'return_rate': overview[4],
            'active_departments': len(by_program),
            'by_department': by_program,
            'trend': trend,
            'top_books': top_books,
            'by_user_type': by_user_type,
            'recent': recent_circ,
        },
    }


@analytics_bp.route('/librarian/analytics')
@login_required
@librarian_required
def analytics_page():
    preset = request.args.get('preset', 'all')
    from_str = request.args.get('from', '').strip()
    to_str = request.args.get('to', '').strip()
    # Normalize: semester/year presets ignore stale custom dates in the URL;
    # invalid presets fall back to no bounds (same as kpi_json/export_report).
    preset, from_str, to_str = _normalize_range(preset, from_str, to_str)
    start_date, end_date = resolve_dates(preset, from_str, to_str)
    dashboard = compute_dashboard(start_date, end_date)
    period_label = _format_period(start_date, end_date, preset, from_str, to_str)
    return render_template(
        'analytics/analytics.html',
        preset=preset,
        from_date=from_str,
        to_date=to_str,
        period_label=period_label,
        dashboard=dashboard,
        period_label=_format_period(start_date, end_date, preset, from_str, to_str),
    )


@analytics_bp.route('/librarian/analytics/dashboard')
@login_required
@librarian_required
def dashboard_json():
    """Return the Riverside dashboard payload for the requested range."""
    preset = request.args.get('preset', 'all')
    from_str = request.args.get('from', '').strip()
    to_str = request.args.get('to', '').strip()
    preset, from_str, to_str = _normalize_range(preset, from_str, to_str)
    start_date, end_date = resolve_dates(preset, from_str, to_str)
    return jsonify(compute_dashboard(start_date, end_date))


CHART_NAMES = frozenset({
    'collection_by_category',
    'copies_by_status',
    'borrowings_by_department',
    'borrowings_by_user_type',
    'borrowings_trend',
    'overdue_trend',
    'top_categories',
    'top_books',
    'high_demand',
})


def _clean_list(values, limit=50):
    """Strip blanks from a repeated query param, capped against abuse."""
    return [v.strip() for v in (values or []) if v and v.strip()][:limit]


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
    if name == 'collection_by_category':
        q = args.get('q', '').strip()[:100]
        return models.collection_by_category(start_date, end_date, q or None)
    if name == 'copies_by_status':
        return models.copies_by_status_summary(start_date, end_date)
    if name == 'borrowings_by_department':
        return models.books_borrowed_per_program(
            start_date, end_date, _clean_list(args.getlist('department')))
    if name == 'borrowings_by_user_type':
        return models.borrowings_by_user_type(
            start_date, end_date, _clean_list(args.getlist('role')))
    if name == 'borrowings_trend':
        return models.borrowings_trend(start_date, end_date)
    if name == 'overdue_trend':
        return models.overdue_trend(start_date, end_date)
    if name == 'top_categories':
        return models.top_borrowed_categories(start_date, end_date)
    if name == 'top_books':
        return models.top_borrowed_books_detailed(start_date, end_date)
    if name == 'high_demand':
        return models.high_demand_titles(start_date, end_date)
    raise ValueError('Unknown chart: %s' % name)


def _echo_chart_filters(args):
    echoed = {}
    departments = _clean_list(args.getlist('department'))
    roles = _clean_list(args.getlist('role'))
    q = args.get('q', '').strip()[:100]
    if departments:
        echoed['departments'] = departments
    if roles:
        echoed['roles'] = roles
    if q:
        echoed['q'] = q
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
        return [('Date', 'TXN', 'User', 'Role', 'Title', 'Author', 'Action', 'Due', 'Status')] + \
            [tuple(r) for r in (kpi_data or [])]
    if kpi_type == 'recent_collection':
        return [('Accession', 'Title', 'Category', 'Inventory State', 'Loan', 'Borrower', 'Due')] + \
            [tuple(r) for r in (kpi_data or [])]
    if kpi_type == 'circulation_summary':
        return [('Metric', 'Value')] + [(r[0], r[1]) for r in (kpi_data or [])]
    raise ValueError('Unknown KPI type: %s' % kpi_type)


def _run_kpi(kpi_type, start_date, end_date):
    if kpi_type == 'utilization_rate':
        return models.utilization_rate(start_date, end_date)
    if kpi_type == 'books_borrowed_per_program':
        return models.books_borrowed_per_program(start_date, end_date)
    if kpi_type == 'most_borrowed_titles':
        return models.most_borrowed_titles(start_date, end_date)
    if kpi_type == 'underutilized_titles':
        return models.underutilized_titles(start_date, end_date)
    if kpi_type == 'trend_borrowings':
        return models.borrowings_trend(start_date, end_date)
    if kpi_type == 'trend_overdue':
        return models.overdue_trend(start_date, end_date)
    if kpi_type == 'top_categories':
        return models.top_borrowed_categories(start_date, end_date)
    if kpi_type == 'top_books':
        return models.top_borrowed_books_detailed(start_date, end_date)
    if kpi_type == 'high_demand':
        return models.high_demand_titles(start_date, end_date)
    if kpi_type == 'by_user_type':
        return models.borrowings_by_user_type(start_date, end_date)
    if kpi_type == 'collection_by_category':
        return models.collection_by_category(start_date, end_date)
    if kpi_type == 'copies_by_status':
        return models.copies_by_status_summary(start_date, end_date)
    if kpi_type == 'recent_circulation':
        return models.recent_circulation()
    if kpi_type == 'recent_collection':
        return models.recent_collection_status()
    if kpi_type == 'circulation_summary':
        t, b, o, avg, rate, new = models.circulation_overview(start_date, end_date)
        return [['Total borrowings', t], ['Active borrowers', b], ['Overdue items', o],
                ['Avg. loan duration (days)', avg], ['On-time return rate (%)', rate],
                ['New additions', new]]
    raise ValueError('Unknown KPI type: %s' % kpi_type)


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


def _pdf_bytes(sections, *, preset='all', start_date=None, end_date=None,
               from_str='', to_str=''):
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
        [Paragraph(period_label, s_meta_value),
         Paragraph(now.strftime('%B %d, %Y  •  %I:%M %p'), s_meta_value),
         Paragraph(f"{gen_name}<br/><font color=\"#64748b\" size=\"7\">{gen_role}</font>" if gen_role else gen_name, s_meta_value)],
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
                f'<font color="#334155"><b>PERIOD</b></font>  <font color="#64748b">{period_label}</font>'
                f'&nbsp;&nbsp;&nbsp;<font color="#334155"><b>ROWS</b></font>  '
                f'<font color="#64748b">{(len(kpi_data) if isinstance(kpi_data, list) else 1) if kpi_data is not None else 0}</font>',
                ParagraphStyle('RPeriod', parent=s_cell, fontSize=7, leading=9))]],
            colWidths=[doc.width], hAlign='LEFT'))
        story.append(Spacer(1, 6))

        # Render table / metric
        rows = _as_2d_rows(kt, kpi_data)

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
                header_cells.append(Paragraph(str(c), style))

            body = []
            for r in rows[1:]:
                cells = []
                for j, val in enumerate(r):
                    st = aligns[j] if j < len(aligns) else s_cell
                    cells.append(Paragraph(str(val), st))
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
    for kt in kpi_types:
        kpi_data = _run_kpi(kt, start_date, end_date)
        models.save_report_snapshot(
            kt,
            {'preset': preset, 'from': from_str, 'to': to_str},
            _jsonable(kpi_data),
            current_user.id,
        )
        sections.append((kt, kpi_data))

    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    label = 'all' if export_all else kpi_type
    filename = f'{label}_{stamp}.pdf'

    body = _pdf_bytes(
        sections,
        preset=preset, start_date=start_date, end_date=end_date,
        from_str=from_str, to_str=to_str,
    )
    return Response(
        body,
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )