import csv
import json
import threading
import uuid
import time
from datetime import datetime, timedelta
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from . import cataloging_bp
from app.auth.decorators import librarian_required
from app.cataloging.models import (
    get_all_books, search_books, get_book_by_id, create_book,
    update_book, update_book_status, delete_book, create_accession,
    get_accessions_by_book, get_accession_by_number,
    search_books_paginated
)
from app.auth.models import log_activity

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
    'copy number': 'copy_number', 'copy_number': 'copy_number', 'copy': 'copy_number',
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


@cataloging_bp.route('/cataloging')
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

    return render_template('cataloging/cataloging.html', books=books,
                           total=total, search_query=query,
                           search_field=field, status_filter=status_filter,
                           page=page, per_page=per_page)


@cataloging_bp.route('/cataloging/add', methods=['POST'])
@login_required
@librarian_required
def add_book():
    title = request.form.get('title', '').strip()
    author = request.form.get('author', '').strip()
    if not title or not author:
        flash('Title and author are required.', 'error')
        return redirect(url_for('cataloging.cataloging_page'))

    book_id = create_book(
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
    accession_number = request.form.get('accession_number', '').strip()
    if accession_number:
        existing = get_accession_by_number(accession_number)
        if existing:
            flash(f'Accession number {accession_number} already exists.', 'error')
            return redirect(url_for('cataloging.cataloging_page'))
        create_accession(
            accession_number=accession_number,
            book_id=book_id,
            librarian_id=current_user.id,
            source=request.form.get('source', '').strip() or None,
            copy_number=request.form.get('copy_number', type=int) or None,
        )
    log_activity(current_user.id, 'cataloging:add_book')
    flash('Book added to catalog.', 'success')
    return redirect(url_for('cataloging.cataloging_page'))


@cataloging_bp.route('/cataloging/<int:book_id>/edit', methods=['POST'])
@login_required
@librarian_required
def edit_book(book_id):
    book = get_book_by_id(book_id)
    if not book:
        flash('Book not found.', 'error')
        return redirect(url_for('cataloging.cataloging_page'))

    update_book(
        book_id=book_id,
        title=request.form.get('title', '').strip(),
        author=request.form.get('author', '').strip(),
        edition=request.form.get('edition', '').strip() or None,
        publisher=request.form.get('publisher', '').strip() or None,
        year_published=request.form.get('year_published', type=int) or None,
        subject_classification=request.form.get('subject_classification', '').strip() or None,
        call_number=request.form.get('call_number', '').strip() or None,
        isbn=request.form.get('isbn', '').strip() or None,
        material_type=request.form.get('material_type', 'Book'),
        description=request.form.get('description', '').strip() or None,
    )
    accession_number = request.form.get('edit_accession_number', '').strip()
    if accession_number:
        existing = get_accession_by_number(accession_number)
        if existing:
            flash(f'Accession number {accession_number} already exists.', 'error')
        else:
            create_accession(
                accession_number=accession_number,
                book_id=book_id,
                librarian_id=current_user.id,
                source=request.form.get('edit_source', '').strip() or None,
                copy_number=request.form.get('edit_copy_number', type=int) or None,
            )
    log_activity(current_user.id, f'cataloging:edit_book:{book_id}')
    flash('Book updated.', 'success')
    return redirect(url_for('cataloging.cataloging_page'))


@cataloging_bp.route('/cataloging/<int:book_id>/delete', methods=['POST'])
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
    log_activity(current_user.id, f'cataloging:delete_book:{book_id}')
    flash('Book permanently deleted.', 'success')
    return redirect(url_for('cataloging.cataloging_page'))


@cataloging_bp.route('/cataloging/<int:book_id>/status', methods=['POST'])
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


@cataloging_bp.route('/cataloging/<int:book_id>/accession/add', methods=['POST'])
@login_required
@librarian_required
def add_accession(book_id):
    book = get_book_by_id(book_id)
    if not book:
        flash('Book not found.', 'error')
        return redirect(url_for('cataloging.cataloging_page'))

    accession_number = request.form.get('accession_number', '').strip()
    copy_number = request.form.get('copy_number', type=int)
    source = request.form.get('source', '').strip() or None

    if not accession_number:
        flash('Accession number is required.', 'error')
        return redirect(url_for('cataloging.cataloging_page'))

    existing = get_accession_by_number(accession_number)
    if existing:
        flash(f'Accession number {accession_number} already exists.', 'error')
        return redirect(url_for('cataloging.cataloging_page'))

    create_accession(accession_number, book_id, current_user.id, source, copy_number)
    log_activity(current_user.id, f'cataloging:add_accession:{book_id}')
    flash(f'Accession {accession_number} added.', 'success')
    return redirect(url_for('cataloging.cataloging_page'))


@cataloging_bp.route('/cataloging/bulk-import', methods=['POST'])
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


@cataloging_bp.route('/cataloging/bulk-import/status/<job_id>')
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
            if isbn:
                existing_book = db.fetch_one(
                    'SELECT book_id FROM book_catalog WHERE title = %s AND author = %s AND isbn = %s',
                    (title, author, isbn)
                )
            else:
                existing_book = db.fetch_one(
                    'SELECT book_id FROM book_catalog WHERE title = %s AND author = %s AND isbn IS NULL',
                    (title, author)
                )

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
                copy_str = book_data.get('copy_number', '')
                copy_number = int(copy_str) if copy_str and copy_str.isdigit() else None
                source = book_data.get('source', '') or None
                if source:
                    source = source.lower()
                    if source not in ('purchase', 'donation'):
                        source = None
                create_accession(
                    accession_number=accession_number,
                    book_id=book_id,
                    librarian_id=user_id,
                    source=source,
                    copy_number=copy_number,
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
    if query:
        books = search_books(query, field=field if field else None)
    else:
        books = get_all_books()
    return render_template('public/catalog.html', books=books,
                           search_query=query, search_field=field)


@cataloging_bp.route('/book/<int:book_id>')
def book_info(book_id):
    book = get_book_by_id(book_id)
    if not book:
        flash('Book not found.', 'error')
        return redirect(url_for('cataloging.public_catalog'))
    accessions = get_accessions_by_book(book_id)
    from app.auth.models import get_user_by_id
    user_data = get_user_by_id(current_user.id) if current_user.is_authenticated else None
    return render_template('public/bookinfo.html', book=book,
                           accessions=accessions, user_data=user_data)
