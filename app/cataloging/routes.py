import csv
import io
import json
import threading
import uuid
import time
from datetime import datetime, timedelta
from flask import Response, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from . import cataloging_bp
from app.auth.decorators import librarian_required
from app.cataloging.models import (
    get_all_books, search_books, get_book_by_id, create_book,
    update_book, update_book_status, delete_book, create_accession,
    get_accessions_by_book, get_accession_by_number,
    get_accession_by_id, get_accessions_for_books, update_accession,
    delete_accession, accession_referenced,
    get_book_by_title_author_isbn, search_books_paginated
)
from app.auth.models import log_activity
from app.bloom_registry import bloom_registry

_import_jobs = {}
_import_lock = threading.Lock()
_IMPORT_EXPIRY = timedelta(minutes=10)

HEADER_MAP = {
    'title': 'title', 'book title': 'title', 'book_title': 'title', 'name': 'title',
    'author': 'author', 'authors': 'author', 'creator': 'author', 'author(s)': 'author',
    'isbn': 'isbn', 'isbn-13': 'isbn', 'isbn13': 'isbn', 'isbn 13': 'isbn',
    'edition': 'edition', 'ed': 'edition',
    'publisher': 'publisher', 'publishers': 'publisher',
    'year': 'year_published', 'year published': 'year_published',
    'year_published': 'year_published', 'publication year': 'year_published',
    'publication_year': 'year_published', 'pub year': 'year_published',
    'subject': 'subject_classification', 'subjects': 'subject_classification',
    'subject classification': 'subject_classification',
    'subject_classification': 'subject_classification', 'category': 'subject_classification',
    'call number': 'call_number', 'call_number': 'call_number', 'call no': 'call_number',
    'material type': 'material_type', 'material_type': 'material_type',
    'type': 'material_type', 'material': 'material_type', 'format': 'material_type',
    'description': 'description', 'desc': 'description',
    'accession number': 'accession_number', 'accession_number': 'accession_number',
    'accession': 'accession_number', 'accession no': 'accession_number',
    'source': 'source', 'acquisition source': 'source', 'acquisition_source': 'source',
}


def _normalize_header(name):
    name = name.strip().lower().replace('_', ' ').replace('-', ' ')
    return ' '.join(name.split())


def _map_headers(fieldnames):
    column_map = {}
    for h in fieldnames:
        db_col = HEADER_MAP.get(_normalize_header(h))
        if db_col is not None:
            column_map[h] = db_col
    return column_map


def _decode_csv(raw):
    for enc in ('utf-8-sig', 'utf-8', 'latin-1', 'cp1252'):
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return None


@cataloging_bp.route('/librarian/cataloging')
@login_required
@librarian_required
def cataloging_page():
    query = request.args.get('q', '').strip()
    field = request.args.get('field', '')
    status_filter = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    per_page = 20

    if status_filter:
        from app.cataloging.models import get_books_by_status
        books = get_books_by_status(status_filter)
        total = len(books)
    elif query:
        books, total = search_books_paginated(query, field, page, per_page)
    else:
        books = get_all_books()
        total = len(books)

    accessions_by_book = {}
    if books:
        for row in get_accessions_for_books([book[0] for book in books]):
            accessions_by_book.setdefault(row[2], []).append(row)

    return render_template('cataloging/cataloging.html', books=books,
                           total=total, search_query=query,
                           search_field=field, status_filter=status_filter,
                           page=page, per_page=per_page,
                           accessions_by_book=accessions_by_book)


_BOOK_EXPORT_HEADERS = [
    'Book ID', 'Title', 'Author', 'Edition', 'Publisher', 'Year Published',
    'Subject Classification', 'Call Number', 'ISBN', 'Material Type',
    'Description', 'Status', 'Date Added', 'Accession Numbers',
]


# book_catalog.* is 13 cols (0 book_id … 12 date_added) + accession_numbers at 13
# Both get_all_books() and get_books_by_status() use ACCESSION_SUBQUERY ("...") AS accession_numbers
# Keep _BOOK_EXPORT_HEADERS width in sync with these 14 positions.
_BOOK_COL = {
    'book_id': 0, 'title': 1, 'author': 2, 'edition': 3, 'publisher': 4,
    'year': 5, 'subject': 6, 'call_number': 7, 'isbn': 8, 'material': 9,
    'description': 10, 'status': 11, 'date_added': 12, 'accessions': 13,
}


def _book_row_to_export(row):
    def _str(v):
        return '' if v is None else str(v)
    # accession_numbers is always at 13 when present; date_added at 12
    date_added = row[_BOOK_COL['date_added']] if len(row) > _BOOK_COL['date_added'] else ''
    acc = row[_BOOK_COL['accessions']] if len(row) > _BOOK_COL['accessions'] else ''
    return [
        _str(row[_BOOK_COL['book_id']] if len(row) > _BOOK_COL['book_id'] else ''),
        _str(row[_BOOK_COL['title']] if len(row) > _BOOK_COL['title'] else ''),
        _str(row[_BOOK_COL['author']] if len(row) > _BOOK_COL['author'] else ''),
        _str(row[_BOOK_COL['edition']] if len(row) > _BOOK_COL['edition'] else ''),
        _str(row[_BOOK_COL['publisher']] if len(row) > _BOOK_COL['publisher'] else ''),
        _str(row[_BOOK_COL['year']] if len(row) > _BOOK_COL['year'] else ''),
        _str(row[_BOOK_COL['subject']] if len(row) > _BOOK_COL['subject'] else ''),
        _str(row[_BOOK_COL['call_number']] if len(row) > _BOOK_COL['call_number'] else ''),
        _str(row[_BOOK_COL['isbn']] if len(row) > _BOOK_COL['isbn'] else ''),
        _str(row[_BOOK_COL['material']] if len(row) > _BOOK_COL['material'] else ''),
        _str(row[_BOOK_COL['description']] if len(row) > _BOOK_COL['description'] else ''),
        _str(row[_BOOK_COL['status']] if len(row) > _BOOK_COL['status'] else ''),
        date_added.isoformat() if hasattr(date_added, 'isoformat') else _str(date_added),
        _str(acc),
    ]


def _generate_book_csv(headers, rows):
    """Yield CSV bytes incrementally — keeps large exports scalable."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(headers)
    yield buf.getvalue().encode('utf-8-sig')
    buf.seek(0)
    buf.truncate(0)
    for r in rows:
        writer.writerow(r)
        data = buf.getvalue()
        if data:
            yield data.encode('utf-8') if isinstance(data, str) else data
            buf.seek(0)
            buf.truncate(0)


def _style_xlsx_sheet(ws, headers):
    navy = PatternFill(start_color='1e3a8a', end_color='1e3a8a', fill_type='solid')
    white_font = Font(color='FFFFFF', bold=True, size=9, name='Calibri')
    thin = Side(style='thin', color='cbd5e1')
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    for col, h in enumerate(headers, 1):
        c = ws.cell(row=1, column=col, value=h)
        c.fill = navy
        c.font = white_font
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        c.border = border
    ws.row_dimensions[1].height = 18
    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = ws.dimensions
    # widths tuned for content
    widths = [8, 30, 22, 10, 18, 10, 22, 14, 14, 12, 32, 10, 12, 24]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = w


@cataloging_bp.route('/librarian/cataloging/export')
@login_required
@librarian_required
def export_books():
    status = request.args.get('status', '').strip().lower()
    fmt = request.args.get('format', 'csv').strip().lower()
    if fmt not in ('csv', 'xlsx'):
        fmt = 'csv'
    if status not in ('active', 'archived'):
        status = ''

    from app.cataloging.models import get_books_by_status
    if status:
        books = get_books_by_status(status)
    else:
        books = get_all_books()

    rows = [_book_row_to_export(b) for b in books]
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    suffix = status or 'all'
    filename = f'books_{suffix}_{stamp}.{fmt}'

    if fmt == 'xlsx':
        # Buffered workbook is fine for capstone scale (<10k rows) and keeps styling;
        # for larger scale, switch to write_only with manual style handling.
        wb = Workbook()
        ws = wb.active
        ws.title = 'Books'
        _style_xlsx_sheet(ws, _BOOK_EXPORT_HEADERS)
        for r in rows:
            ws.append(r)
        # style data rows
        thin = Side(style='thin', color='cbd5e1')
        border = Border(left=thin, right=thin, top=thin, bottom=thin)
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, max_col=len(_BOOK_EXPORT_HEADERS)):
            for cell in row:
                cell.font = Font(size=9, name='Calibri')
                cell.alignment = Alignment(vertical='center', wrap_text=True)
                cell.border = border
            ws.row_dimensions[row[0].row].height = 15
        # alternating row fill
        light = PatternFill(start_color='f8fafc', end_color='f8fafc', fill_type='solid')
        for idx, row in enumerate(ws.iter_rows(min_row=2, max_row=ws.max_row, max_col=len(_BOOK_EXPORT_HEADERS)), 2):
            if idx % 2 == 0:
                for cell in row:
                    cell.fill = light
        buf = io.BytesIO()
        wb.save(buf)
        body = buf.getvalue()
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        log_activity(current_user.id, f'cataloging:export_books:{suffix}:{len(rows)}')
        return Response(
            body,
            mimetype=mimetype,
            headers={'Content-Disposition': f'attachment; filename="{filename}"'},
        )
    else:
        log_activity(current_user.id, f'cataloging:export_books:{suffix}:{len(rows)}')
        return Response(
            _generate_book_csv(_BOOK_EXPORT_HEADERS, rows),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'},
        )


@cataloging_bp.route('/librarian/cataloging/add', methods=['POST'])
@login_required
@librarian_required
def add_book():
    title = request.form.get('title', '').strip()
    author = request.form.get('author', '').strip()
    if not title or not author:
        flash('Title and author are required.', 'error')
        return redirect(url_for('cataloging.cataloging_page', modal='addBookModal', mstatus='error'))

    accession_number = request.form.get('accession_number', '').strip()
    if accession_number:
        existing = get_accession_by_number(accession_number)
        if existing:
            flash(f'Accession number {accession_number} already exists.', 'error')
            return redirect(url_for('cataloging.cataloging_page', modal='addBookModal', mstatus='error'))

    isbn = request.form.get('isbn', '').strip() or None
    existing_book = get_book_by_title_author_isbn(title, author, isbn)
    source = request.form.get('source', '').strip() or None
    if existing_book:
        book_id = existing_book[0]
        if accession_number:
            create_accession(accession_number, book_id, current_user.id, source)
            log_activity(current_user.id, f'cataloging:add_copy:{book_id}')
            flash(f'"{title}" already exists; accession {accession_number} added as another copy.', 'success')
        else:
            log_activity(current_user.id, f'cataloging:add_book_duplicate:{book_id}')
            flash(f'"{title}" already exists in the catalog.', 'info')
        return redirect(url_for('cataloging.cataloging_page', modal='addBookModal', mstatus='success'))

    book_id = create_book(
        title=title,
        author=author,
        edition=request.form.get('edition', '').strip() or None,
        publisher=request.form.get('publisher', '').strip() or None,
        year_published=request.form.get('year_published', type=int) or None,
        subject_classification=request.form.get('subject_classification', '').strip() or None,
        call_number=request.form.get('call_number', '').strip() or None,
        isbn=isbn,
        material_type=request.form.get('material_type', 'Book'),
        description=request.form.get('description', '').strip() or None,
    )
    bloom_registry.mark_dirty()
    if accession_number:
        create_accession(
            accession_number=accession_number,
            book_id=book_id,
            librarian_id=current_user.id,
            source=source,
        )
    log_activity(current_user.id, 'cataloging:add_book')
    flash('Book added to catalog.', 'success')
    return redirect(url_for('cataloging.cataloging_page', modal='addBookModal', mstatus='success'))


@cataloging_bp.route('/librarian/cataloging/<int:book_id>/edit', methods=['POST'])
@login_required
@librarian_required
def edit_book(book_id):
    book = get_book_by_id(book_id)
    if not book:
        flash('Book not found.', 'error')
        return redirect(url_for('cataloging.cataloging_page'))

    title = request.form.get('title', '').strip()
    author = request.form.get('author', '').strip()
    if not title or not author:
        flash('Title and author are required.', 'error')
        return redirect(url_for('cataloging.cataloging_page', modal='editBookModal',
                                book_id=book_id, mstatus='error'))

    update_book(
        book_id=book_id,
        title=title,
        author=author,
        edition=request.form.get('edition', '').strip() or None,
        publisher=request.form.get('publisher', '').strip() or None,
        year_published=request.form.get('year_published', type=int) or None,
        subject_classification=request.form.get('subject_classification', '').strip() or None,
        call_number=request.form.get('call_number', '').strip() or None,
        isbn=request.form.get('isbn', '').strip() or None,
        material_type=request.form.get('material_type', 'Book'),
        description=request.form.get('description', '').strip() or None,
    )
    bloom_registry.mark_dirty()
    log_activity(current_user.id, f'cataloging:edit_book:{book_id}')
    flash('Book updated.', 'success')
    return redirect(url_for('cataloging.cataloging_page', modal='editBookModal', book_id=book_id, mstatus='success'))


@cataloging_bp.route('/librarian/cataloging/<int:book_id>/delete', methods=['POST'])
@login_required
@librarian_required
def delete_book_route(book_id):
    book = get_book_by_id(book_id)
    if not book:
        flash('Book not found.', 'error')
        return redirect(url_for('cataloging.cataloging_page'))
    if book[11] != 'archived':
        flash('Book must be archived before deletion.', 'error')
        return redirect(url_for('cataloging.cataloging_page'))
    delete_book(book_id)
    bloom_registry.mark_dirty()
    log_activity(current_user.id, f'cataloging:delete_book:{book_id}')
    flash('Book permanently deleted.', 'success')
    return redirect(url_for('cataloging.cataloging_page'))


@cataloging_bp.route('/librarian/cataloging/<int:book_id>/status', methods=['POST'])
@login_required
@librarian_required
def toggle_book_status(book_id):
    book = get_book_by_id(book_id)
    if not book:
        flash('Book not found.', 'error')
        return redirect(url_for('cataloging.cataloging_page'))

    new_status = 'archived' if book[11] == 'active' else 'active'
    update_book_status(book_id, new_status)
    log_activity(current_user.id, f'cataloging:toggle_status:{book_id}:{new_status}')
    flash(f'Book {new_status}.', 'success')
    return redirect(url_for('cataloging.cataloging_page'))


@cataloging_bp.route('/librarian/cataloging/<int:book_id>/accession/add', methods=['POST'])
@login_required
@librarian_required
def add_accession(book_id):
    book = get_book_by_id(book_id)
    if not book:
        flash('Book not found.', 'error')
        return redirect(url_for('cataloging.cataloging_page'))

    accession_number = request.form.get('accession_number', '').strip()
    source = request.form.get('source', '').strip() or None

    if not accession_number:
        flash('Accession number is required.', 'error')
        return redirect(url_for('cataloging.cataloging_page', modal='addAccessionModal',
                                action=url_for('cataloging.add_accession', book_id=book_id),
                                mstatus='error'))

    existing = get_accession_by_number(accession_number)
    if existing:
        flash(f'Accession number {accession_number} already exists.', 'error')
        return redirect(url_for('cataloging.cataloging_page', modal='addAccessionModal',
                                action=url_for('cataloging.add_accession', book_id=book_id),
                                mstatus='error'))

    create_accession(accession_number, book_id, current_user.id, source)
    log_activity(current_user.id, f'cataloging:add_accession:{book_id}')
    flash(f'Accession {accession_number} added.', 'success')
    return redirect(url_for('cataloging.cataloging_page', modal='addAccessionModal',
                            action=url_for('cataloging.add_accession', book_id=book_id),
                            mstatus='success'))


@cataloging_bp.route('/librarian/cataloging/accession/<int:accession_id>/edit', methods=['POST'])
@login_required
@librarian_required
def edit_accession(accession_id):
    acc = get_accession_by_id(accession_id)
    if not acc:
        flash('Accession copy not found.', 'error')
        return redirect(url_for('cataloging.cataloging_page'))

    accession_number = request.form.get('accession_number', '').strip()
    source = request.form.get('source', '').strip() or None

    if not accession_number:
        flash('Accession number is required.', 'error')
        return redirect(url_for('cataloging.cataloging_page'))

    existing = get_accession_by_number(accession_number)
    if existing and existing[0] != accession_id:
        flash(f'Accession number {accession_number} already exists.', 'error')
        return redirect(url_for('cataloging.cataloging_page'))

    update_accession(accession_id, accession_number, source)
    log_activity(current_user.id, f'cataloging:edit_accession:{accession_id}')
    flash(f'Accession {accession_number} updated.', 'success')
    return redirect(url_for('cataloging.cataloging_page'))


@cataloging_bp.route('/librarian/cataloging/accession/<int:accession_id>/delete', methods=['POST'])
@login_required
@librarian_required
def delete_accession_route(accession_id):
    acc = get_accession_by_id(accession_id)
    if not acc:
        flash('Accession copy not found.', 'error')
        return redirect(url_for('cataloging.cataloging_page'))

    if accession_referenced(accession_id):
        flash(f'Cannot delete accession {acc[1]} — it is referenced by circulation or inventory records.', 'error')
        return redirect(url_for('cataloging.cataloging_page'))

    delete_accession(accession_id)
    log_activity(current_user.id, f'cataloging:delete_accession:{accession_id}')
    flash(f'Accession {acc[1]} deleted.', 'success')
    return redirect(url_for('cataloging.cataloging_page'))


@cataloging_bp.route('/librarian/cataloging/bulk-import', methods=['POST'])
@login_required
@librarian_required
def bulk_import():
    if 'file' not in request.files:
        return jsonify({'error': 'No file selected.'}), 400

    f = request.files['file']
    if f.filename == '':
        return jsonify({'error': 'No file selected.'}), 400

    if not f.filename.lower().endswith('.csv'):
        return jsonify({'error': 'Please upload a CSV file.'}), 400

    raw = f.read()
    if len(raw) > 10 * 1024 * 1024:
        return jsonify({'error': 'File too large. Maximum size is 10MB.'}), 400

    content = _decode_csv(raw)
    if content is None:
        return jsonify({'error': 'Unable to read file. Ensure it is a valid CSV file.'}), 400

    lines = content.splitlines()
    if not lines:
        return jsonify({'error': 'CSV file is empty.'}), 400

    reader = csv.DictReader(lines)
    if not reader.fieldnames:
        return jsonify({'error': 'CSV file has no headers.'}), 400

    column_map = _map_headers(reader.fieldnames)
    mapped = set(column_map.values())
    if 'title' not in mapped or 'author' not in mapped:
        return jsonify({'error': 'CSV must contain at least "title" and "author" columns.'}), 400
    if 'accession_number' not in mapped:
        return jsonify({'error': 'CSV must contain an "accession_number" column.'}), 400

    rows = list(reader)
    job_id = str(uuid.uuid4())
    _import_jobs[job_id] = {
        'status': 'processing',
        'total': len(rows),
        'done': 0,
        'errors': [],
        'message': None,
    }

    app = _get_current_app()
    t = threading.Thread(
        target=_bulk_import_worker,
        args=(app, job_id, rows, column_map, current_user.id),
        daemon=True,
    )
    t.start()

    return jsonify({'job_id': job_id, 'redirect': url_for('cataloging.cataloging_page')})


@cataloging_bp.route('/librarian/cataloging/bulk-import/status/<job_id>')
@login_required
@librarian_required
def bulk_import_status(job_id):
    _cleanup_old_jobs()
    job = _import_jobs.get(job_id)
    if not job:
        return jsonify({'status': 'not_found'}), 404
    return jsonify({
        'status': job['status'],
        'total': job['total'],
        'done': job['done'],
        'message': job.get('message'),
        'errors': job.get('errors', []),
    })


def _get_current_app():
    from flask import current_app
    return current_app._get_current_object()


def _bulk_import_worker(app, job_id, rows, column_map, user_id):
    with app.app_context():
        from app.cataloging.models import create_book, create_accession, get_accession_by_number
        from app.database import db
        from app.auth.models import log_activity
        imported = 0
        errors = []
        total = len(rows)

        for i, row in enumerate(rows, start=2):
            book_data = {}
            for csv_col, db_col in column_map.items():
                if db_col:
                    book_data[db_col] = (row.get(csv_col) or '').strip()

            title = book_data.get('title', '')
            author = book_data.get('author', '')
            accession_number = book_data.get('accession_number', '')
            if not title or not author:
                errors.append(f'Row {i}: missing title or author')
                with _import_lock:
                    _import_jobs[job_id]['done'] = imported + len(errors)
                continue
            if not accession_number:
                errors.append(f'Row {i}: missing accession_number')
                with _import_lock:
                    _import_jobs[job_id]['done'] = imported + len(errors)
                continue

            isbn = book_data.get('isbn', '')
            existing_book = get_book_by_title_author_isbn(title, author, isbn or None)

            existing_acc = get_accession_by_number(accession_number)
            if existing_acc:
                if existing_book and existing_acc[2] == existing_book[0]:
                    imported += 1
                    with _import_lock:
                        _import_jobs[job_id]['done'] = imported + len(errors)
                    continue
                errors.append(f'Row {i}: accession number {accession_number} already exists')
                with _import_lock:
                    _import_jobs[job_id]['done'] = imported + len(errors)
                continue

            if existing_book:
                book_id = existing_book[0]
            else:
                year_str = book_data.get('year_published', '')
                year = int(year_str) if year_str and year_str.isdigit() else None
                book_id = create_book(
                    title=title,
                    author=author,
                    edition=book_data.get('edition') or None,
                    publisher=book_data.get('publisher') or None,
                    year_published=year,
                    subject_classification=book_data.get('subject_classification') or None,
                    call_number=book_data.get('call_number') or None,
                    isbn=isbn or None,
                    material_type=book_data.get('material_type', 'Book') or 'Book',
                    description=book_data.get('description') or None,
                )

            try:
                source = book_data.get('source', '') or None
                if source:
                    source = source.lower()
                    if source not in ('purchase', 'donation', 'others'):
                        source = None
                create_accession(
                    accession_number=accession_number,
                    book_id=book_id,
                    librarian_id=user_id,
                    source=source,
                )
                imported += 1
            except Exception as e:
                errors.append(f'Row {i}: {e}')

            with _import_lock:
                _import_jobs[job_id]['done'] = imported + len(errors)

        try:
            log_activity(user_id,
                         f'cataloging:bulk_import:{imported}_success_{len(errors)}_errors')
        except Exception:
            pass

        bloom_registry.mark_dirty()

        message = f'Successfully imported {imported} book(s).'
        if errors:
            if len(errors) <= 10:
                message += ' ' + ' '.join(errors[:10])
            else:
                message += ' ' + ' '.join(errors[:10]) + f' ... and {len(errors) - 10} more error(s).'

        with _import_lock:
            _import_jobs[job_id].update({
                'status': 'done',
                'done': total,
                'message': message,
                'errors': errors[:10],
            })


def _cleanup_old_jobs():
    cutoff = datetime.now() - _IMPORT_EXPIRY
    stale = [jid for jid, j in _import_jobs.items()
             if j.get('updated_at') and j['updated_at'] < cutoff]
    for jid in stale:
        _import_jobs.pop(jid, None)


@cataloging_bp.route('/catalog')
def public_catalog():
    query = request.args.get('q', '').strip()
    field = request.args.get('field', '')
    year_preset = request.args.get('year_preset', '').strip()
    year_from = request.args.get('year_from', '').strip()
    year_to = request.args.get('year_to', '').strip()
    sort_by = request.args.get('sort_by', '').strip()
    category = request.args.get('category', '').strip()
    material_type = request.args.get('material_type', '').strip()
    availability = request.args.get('availability', '').strip()

    current_year = datetime.now().year
    if year_preset == 'since_this_year':
        year_from = str(current_year)
        year_to = ''
    elif year_preset == 'since_last_year':
        year_from = str(current_year - 1)
        year_to = ''
    elif year_preset == 'since_2023':
        year_from = '2023'
        year_to = ''
    elif year_preset == 'any':
        year_from = ''
        year_to = ''

    from app.cataloging.models import search_books_filtered, get_distinct_categories
    books = search_books_filtered(
        query, field=field if field else None,
        year_from=year_from or None, year_to=year_to or None,
        sort_by=sort_by or None, category=category or None,
        material_type=material_type or None, availability=availability or None
    )
    categories = [row[0] for row in get_distinct_categories()]

    per_page = 50
    total = len(books)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(request.args.get('page', 1, type=int), total_pages))
    start = (page - 1) * per_page
    books = books[start:start + per_page]

    return render_template('public/catalog.html', books=books,
                           search_query=query, search_field=field,
                           year_preset=year_preset,
                           year_from=year_from, year_to=year_to,
                           sort_by=sort_by, category=category,
                           material_type=material_type, availability=availability,
                           current_year=current_year,
                           categories=categories,
                           page=page, total_pages=total_pages, total=total, per_page=per_page)


@cataloging_bp.route('/book/<int:book_id>')
def book_info(book_id):
    book = get_book_by_id(book_id)
    if not book:
        flash('Book not found.', 'error')
        return redirect(url_for('cataloging.public_catalog'))
    accessions = get_accessions_by_book(book_id)
    from app.auth.models import get_user_by_id
    from app.circulation.models import (
        get_active_loan_accession_ids_by_book,
        get_active_loan_borrower_user_ids_by_book,
    )
    borrowed_ids = get_active_loan_accession_ids_by_book(book_id)
    borrower_map = get_active_loan_borrower_user_ids_by_book(book_id)
    accessions_with_status = [
        (acc, acc[0] not in borrowed_ids) for acc in accessions
    ]
    any_available = any(is_available for _, is_available in accessions_with_status)
    user_data = get_user_by_id(current_user.id) if current_user.is_authenticated else None
    return render_template('public/bookinfo.html', book=book,
                           accessions=accessions_with_status, any_available=any_available,
                           borrower_map=borrower_map, user_data=user_data)
