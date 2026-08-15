import csv
import io
from datetime import date, datetime

from flask import render_template, request, Response, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

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


def resolve_dates(preset, from_str, to_str):
    """Resolve a date range into (start_date, end_date).

    Explicit ``from``/``to`` dates win; otherwise the preset applies
    (``all`` -> no bounds, ``semester`` -> current academic semester,
    ``year`` -> current calendar year).
    """
    today = date.today()
    start_date = end_date = None

    if from_str or to_str:
        try:
            start_date = datetime.strptime(from_str, '%Y-%m-%d').date() if from_str else None
            end_date = datetime.strptime(to_str, '%Y-%m-%d').date() if to_str else None
        except ValueError:
            start_date = end_date = None
        return start_date, end_date

    if preset == 'year':
        start_date = date(today.year, 1, 1)
        end_date = date(today.year, 12, 31)
    elif preset == 'semester':
        if today.month >= 8:
            start_date = date(today.year, 8, 1)
            end_date = date(today.year, 12, 31)
        else:
            start_date = date(today.year, 1, 1)
            end_date = date(today.year, 5, 31)
    return start_date, end_date


def compute_all_kpis(start_date, end_date):
    return {
        'books_borrowed_per_program': models.books_borrowed_per_program(start_date, end_date),
        'utilization_rate': models.utilization_rate(start_date, end_date),
        'most_borrowed_titles': models.most_borrowed_titles(start_date, end_date),
        'underutilized_titles': models.underutilized_titles(start_date, end_date),
    }


@analytics_bp.route('/librarian/analytics')
@login_required
@librarian_required
def analytics_page():
    preset = request.args.get('preset', 'all')
    from_str = request.args.get('from', '').strip()
    to_str = request.args.get('to', '').strip()
    start_date, end_date = resolve_dates(preset, from_str, to_str)
    kpi_data = compute_all_kpis(start_date, end_date)
    return render_template(
        'analytics/analytics.html',
        kpi_data=kpi_data,
        kpi_labels=KPI_LABELS,
        kpi_descriptions=KPI_DESCRIPTIONS,
        preset=preset,
        from_date=from_str,
        to_date=to_str,
    )


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
    raise ValueError('Unknown KPI type: %s' % kpi_type)


def _pdf_bytes(sections):
    """Build a PDF report from (kpi_type, kpi_data) sections."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
                            rightMargin=54, leftMargin=54,
                            topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ReportTitle', parent=styles['Title'], fontSize=18, spaceAfter=6)
    subtitle_style = ParagraphStyle(
        'ReportSubtitle', parent=styles['Normal'], fontSize=10,
        textColor=colors.grey, spaceAfter=18)
    section_style = ParagraphStyle(
        'ReportSection', parent=styles['Heading2'], fontSize=14,
        spaceBefore=14, spaceAfter=8)
    cell_style = ParagraphStyle(
        'ReportCell', parent=styles['Normal'], fontSize=9, leading=12)

    now = datetime.now().strftime('%B %d, %Y')
    story = [
        Paragraph('MCST Library - Analytics Report', title_style),
        Paragraph('Generated on {}'.format(now), subtitle_style),
    ]

    for i, (kt, kpi_data) in enumerate(sections):
        if i > 0:
            story.append(Spacer(1, 18))
        story.append(Paragraph(KPI_LABELS[kt], section_style))

        rows = _as_2d_rows(kt, kpi_data)
        if len(rows) == 1:
            story.append(Paragraph('No data for this KPI.', cell_style))
            continue

        header = [Paragraph(str(c), cell_style) for c in rows[0]]
        data = [[Paragraph(str(c), cell_style) for c in row] for row in rows[1:]]
        table = Table([header] + data, hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f1f5f9')]),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cbd5e1')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(table)

    doc.build(story)
    return buf.getvalue()


@analytics_bp.route('/librarian/analytics/export', methods=['POST'])
@login_required
@librarian_required
def export_report():
    kpi_type = request.form.get('kpi_type', '')
    fmt = request.form.get('format', 'csv')
    preset = request.form.get('preset', 'all')
    from_str = request.form.get('from', '').strip()
    to_str = request.form.get('to', '').strip()

    export_all = kpi_type == 'all'
    if not export_all and kpi_type not in VALID_KPIS:
        flash('Invalid report type.', 'error')
        return redirect(url_for('analytics.analytics_page'))
    if fmt not in ('csv', 'xlsx', 'pdf'):
        fmt = 'csv'

    start_date, end_date = resolve_dates(preset, from_str, to_str)

    if export_all:
        kpi_types = list(KPI_LABELS.keys())
    else:
        kpi_types = [kpi_type]

    sections = []
    for kt in kpi_types:
        kpi_data = _run_kpi(kt, start_date, end_date)
        models.save_report_snapshot(
            kt,
            {'preset': preset, 'from': from_str, 'to': to_str},
            [list(r) for r in kpi_data] if isinstance(kpi_data, list) else kpi_data,
            current_user.id,
        )
        sections.append((kt, kpi_data))

    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    label = 'all' if export_all else kpi_type
    filename = '{}_{}.{}'.format(label, stamp, fmt)

    if fmt == 'pdf':
        body = _pdf_bytes(sections)
        mimetype = 'application/pdf'
    elif fmt == 'xlsx':
        wb = Workbook()
        wb.remove(wb.active)
        for kt, kpi_data in sections:
            ws = wb.create_sheet(title=(KPI_LABELS[kt][:31] or kt))
            for row in _as_2d_rows(kt, kpi_data):
                ws.append(row)
        buf = io.BytesIO()
        wb.save(buf)
        body = buf.getvalue()
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    else:
        buf = io.StringIO()
        writer = csv.writer(buf)
        for i, (kt, kpi_data) in enumerate(sections):
            if i > 0:
                buf.write('\n')
            writer.writerow([KPI_LABELS[kt]])
            writer.writerows(_as_2d_rows(kt, kpi_data))
        body = buf.getvalue().encode('utf-8-sig')
        mimetype = 'text/csv'

    return Response(
        body,
        mimetype=mimetype,
        headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
    )