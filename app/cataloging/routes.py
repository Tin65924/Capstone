import csv
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import cataloging_bp
from app.auth.decorators import librarian_required
from app.cataloging.models import (
    get_all_books, search_books, get_book_by_id, create_book,
    update_book, update_book_status, create_accession,
    get_accessions_by_book, get_accession_by_number,
    search_books_paginated
)
from app.auth.models import log_activity

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
    page = request.args.get('page', 1, type=int)
    per_page = 20

    if query:
        books, total = search_books_paginated(query, field, page, per_page)
    else:
        books = get_all_books()
        total = len(books)

    return render_template('cataloging/cataloging.html', books=books,
                           total=total, search_query=query,
                           search_field=field, page=page, per_page=per_page)


@cataloging_bp.route('/cataloging/add', methods=['POST'])
@login_required
@librarian_required
def add_book():
    title = request.form.get('title', '').strip()
    author = request.form.get('author', '').strip()
    if not title or not author:
        flash('Title and author are required.', 'error')
        return redirect(url_for('cataloging.cataloging_page'))

    create_book(
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
    log_activity(current_user.id, f'cataloging:edit_book:{book_id}')
    flash('Book updated.', 'success')
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
        flash('No file selected.', 'error')
        return redirect(url_for('cataloging.cataloging_page'))

    f = request.files['file']
    if f.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('cataloging.cataloging_page'))

    if not f.filename.lower().endswith('.csv'):
        flash('Please upload a CSV file.', 'error')
        return redirect(url_for('cataloging.cataloging_page'))

    raw = f.read()
    if len(raw) > 10 * 1024 * 1024:
        flash('File too large. Maximum size is 10MB.', 'error')
        return redirect(url_for('cataloging.cataloging_page'))

    content = _decode_csv(raw)
    if content is None:
        flash('Unable to read file. Please ensure it is a valid CSV file.', 'error')
        return redirect(url_for('cataloging.cataloging_page'))

    lines = content.splitlines()
    if not lines:
        flash('CSV file is empty.', 'error')
        return redirect(url_for('cataloging.cataloging_page'))

    reader = csv.DictReader(lines)
    if not reader.fieldnames:
        flash('CSV file has no headers.', 'error')
        return redirect(url_for('cataloging.cataloging_page'))

    column_map = _map_headers(reader.fieldnames)
    mapped_columns = set(column_map.values())
    if 'title' not in mapped_columns or 'author' not in mapped_columns:
        flash('CSV must contain at least "title" and "author" columns.', 'error')
        return redirect(url_for('cataloging.cataloging_page'))

    imported = 0
    errors = []
    for i, row in enumerate(reader, start=2):
        book_data = {}
        for csv_col, db_col in column_map.items():
            if db_col:
                book_data[db_col] = (row.get(csv_col) or '').strip()

        title = book_data.get('title', '')
        author = book_data.get('author', '')

        if not title or not author:
            errors.append(f'Row {i}: missing title or author')
            continue

        year_str = book_data.get('year_published', '')
        year = int(year_str) if year_str and year_str.isdigit() else None

        try:
            create_book(
                title=title,
                author=author,
                edition=book_data.get('edition') or None,
                publisher=book_data.get('publisher') or None,
                year_published=year,
                subject_classification=book_data.get('subject_classification') or None,
                call_number=book_data.get('call_number') or None,
                isbn=book_data.get('isbn') or None,
                material_type=book_data.get('material_type', 'Book') or 'Book',
                description=book_data.get('description') or None,
            )
            imported += 1
        except Exception as e:
            errors.append(f'Row {i}: {e}')

    log_activity(current_user.id,
                 f'cataloging:bulk_import:{imported}_success_{len(errors)}_errors')

    if imported:
        flash(f'Successfully imported {imported} book(s).', 'success')
    for err in errors[:10]:
        flash(err, 'error')
    if len(errors) > 10:
        flash(f'... and {len(errors) - 10} more error(s).', 'error')

    return redirect(url_for('cataloging.cataloging_page'))


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
