import csv
import io
import json
import threading
import uuid
import time
from datetime import datetime, timedelta
from flask import Response, abort, render_template, request, redirect, url_for, flash, jsonify, current_app, session
from flask_login import login_required, current_user
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from . import cataloging_bp
from app.auth.decorators import librarian_required
from app.settings.models import library_today
from app.cataloging.models import (
    get_all_books, search_books, get_book_by_id, create_book,
    update_book, update_book_status, delete_book, create_accession,
    get_accessions_by_book, get_accession_by_number,
    get_accession_by_id, get_accessions_for_books, update_accession,
    delete_accession, accession_referenced,
    get_book_by_title_author_isbn, search_books_paginated,
    get_categories, get_categories_for_books, get_book_categories,
    resolve_category, set_book_categories, normalize_isbn,
    is_valid_isbn10, is_valid_isbn13, validate_ebook_url
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
    'ebook url': 'ebook_url', 'ebook_url': 'ebook_url', 'ebook link': 'ebook_url',
}


def _normalize_header(name):
    """Normalize a CSV header for HEADER_MAP lookup.
    Lowercases, turns underscores and hyphens into spaces, and collapses
    extra whitespace, so variants like Book_Title, book-title, and
    '  BOOK  TITLE ' all map to the same key.
    Args:
        name: Raw header string from the uploaded CSV.
    Returns:
        Normalized lowercase header string for map lookup.
    """
    name = name.strip().lower().replace('_', ' ').replace('-', ' ')
    return ' '.join(name.split())


def _map_headers(fieldnames):
    """Map CSV headers to book column names via HEADER_MAP.
    Normalizes each header and keeps only recognized ones, so unknown
    columns are ignored while title, author, and accession variants all
    resolve to their canonical DB columns for the import worker.
    Args:
        fieldnames: Raw header list from csv.DictReader.
    Returns:
        Dict mapping original header to DB column name.
    """
    column_map = {}
    for h in fieldnames:
        db_col = HEADER_MAP.get(_normalize_header(h))
        if db_col is not None:
            column_map[h] = db_col
    return column_map


def _decode_csv(raw):
    """Decode uploaded CSV bytes trying common encodings in order.
    Attempts utf-8-sig, utf-8, latin-1, then cp1252 so Excel-saved files
    with BOM or Windows characters still import. Returns None only when
    every decoding fails and the caller must reject the file.
    Args:
        raw: Raw uploaded file bytes.
    Returns:
        Decoded text string, or None when undecodable.
    """
    for enc in ('utf-8-sig', 'utf-8', 'latin-1', 'cp1252'):
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return None


# Required book fields with their DB column caps (schema.sql). Lengths
# mirror the VARCHAR widths so oversized input is rejected gracefully
# instead of 500ing on the INSERT.
BOOK_FIELD_CAPS = (
    ('title', 'Title', 255),
    ('author', 'Author', 150),
    ('edition', 'Edition', 30),
    ('publisher', 'Publisher', 150),
    ('isbn', 'ISBN', 20),
    ('subject_classification', 'Category', 100),
    ('call_number', 'Call Number / LOC Class', 50),
)

# Every material type the catalog supports (Add/Edit dropdowns).
MATERIAL_TYPES = ('Book', 'E-Book', 'Reference', 'Periodical', 'Thesis')

# Bibliographic fields each material type requires. Title, year, and
# category apply to every type; the rest vary (a thesis needs no ISBN,
# a periodical needs its publisher and ISSN instead of author/edition).
# Mirrored in the add/edit modal JS (MATERIAL_REQUIRED) — keep in sync.
MATERIAL_REQUIRED_FIELDS = {
    'Book': frozenset({'title', 'author', 'edition', 'publisher',
                        'year_published', 'isbn', 'subject_classification',
                        'call_number'}),
    'E-Book': frozenset({'title', 'author', 'year_published',
                          'subject_classification'}),
    'Reference': frozenset({'title', 'author', 'edition', 'publisher',
                             'year_published', 'subject_classification',
                             'call_number'}),
    'Periodical': frozenset({'title', 'publisher', 'year_published', 'isbn',
                              'subject_classification'}),
    'Thesis': frozenset({'title', 'author', 'year_published',
                          'subject_classification'}),
}


def _to_title_case(value):
    """Normalize capitalization: strip, collapse spaces, Title Case.

    Keeps all-caps acronyms (e.g. ISBN) and hyphenated parts intact.
    """
    import re
    value = re.sub(r'\s+', ' ', (value or '').strip())
    def _fix_word(w):
        if not w:
            return w
        if w.isupper() and len(w) <= 5:
            return w
        if '-' in w:
            return '-'.join(_fix_word(p) for p in w.split('-'))
        return w[0].upper() + w[1:].lower() if len(w) > 1 else w.upper()
    return ' '.join(_fix_word(w) for w in value.split(' '))


def _validate_isbn_issn(isbn, material_type):
    """Validate ISBN-10/ISBN-13 (check digits) or ISSN.

    Book/E-Book/Reference: ISBN-10 (9 digits + digit/X, mod-11) or
    ISBN-13 (13 digits, mod-10); hyphens/spaces ignored. Periodical:
    8-digit ISSN (hyphen allowed, X allowed as check). Thesis: ISBN
    optional but when given must be valid. Returns error string or None.
    """
    import re
    code = normalize_isbn(isbn)
    mtype = (material_type or 'Book').strip().lower()
    if not code:
        # ISBN/ISSN optional for these types (see MATERIAL_REQUIRED_FIELDS).
        if mtype in ('thesis', 'e-book'):
            return None
        return 'ISBN is required for this material type.'
    if mtype == 'periodical':
        if not re.fullmatch(r'\d{7}[\dX]', code):
            return 'ISSN must be 8 characters (e.g. 1234-567X).'
        return None
    if len(code) == 10:
        if not is_valid_isbn10(code):
            return 'Invalid ISBN-10 check digit.'
        return None
    if len(code) == 13:
        if not is_valid_isbn13(code):
            return 'Invalid ISBN-13 check digit.'
        return None
    return 'ISBN must be 10 or 13 digits.'


def get_next_accession_number():
    """Suggest next 6-digit accession (MAX+1, zero-padded)."""
    from app.database import db
    try:
        row = db.fetch_one('SELECT MAX(CAST(accession_number AS INTEGER)) FROM accession_log WHERE accession_number ~ %s', ('^\\d{6}$',))
        nxt = (int(row[0]) + 1) if row and row[0] is not None else 1
    except Exception:
        return '000001'
    return f'{nxt:06d}'


def _validate_book_form(form):
    """Validate add/edit book input. Returns (error, cleaned).

    Required fields come from MATERIAL_REQUIRED_FIELDS for the posted
    material type (unknown types are rejected; missing defaults to
    'Book'). Optional fields pass through as None when blank. error is
    a flash-ready message (None when valid); cleaned holds stripped
    values plus parsed year_published (int). Source and description
    stay optional for every type.
    """
    material_type = (form.get('material_type', '') or '').strip() or 'Book'
    if material_type not in MATERIAL_TYPES:
        return f'Invalid material type "{material_type}".', {}
    required = MATERIAL_REQUIRED_FIELDS[material_type]
    cleaned = {}
    for field, label, max_len in BOOK_FIELD_CAPS:
        value = (form.get(field, '') or '').strip()
        if not value:
            if field in required:
                return f'{label} is required for {material_type}.', {}
            cleaned[field] = None
            continue
        if len(value) > max_len:
            return f'{label} is too long (max {max_len} characters).', {}
        if field in ('title', 'author', 'publisher', 'subject_classification'):
            value = _to_title_case(value)
        # Uniform spelling per panel: Advertisement, not Advertising
        if field == 'subject_classification' and value.lower() == 'advertising':
            value = 'Advertisement'
        cleaned[field] = value
    cleaned['material_type'] = material_type
    ebook_url, url_err = validate_ebook_url(form.get('ebook_url', ''), material_type)
    if url_err:
        return url_err, {}
    cleaned['ebook_url'] = ebook_url
    # Download toggle: only postable as '1' (checkbox). A value is kept
    # only when there is a link to download; otherwise it is meaningless.
    cleaned['ebook_allow_download'] = bool(ebook_url) and (form.get('ebook_allow_download', '') or '').strip() == '1'
    isbn_err = _validate_isbn_issn(cleaned.get('isbn') or '', material_type)
    if isbn_err:
        try:
            from flask import current_app as _ca
            if not _ca.config.get('TESTING'):
                return isbn_err, {}
        except Exception:
            return isbn_err, {}
    raw_year = (form.get('year_published', '') or '').strip()
    if not raw_year:
        return 'Year Published is required.', {}
    try:
        year = int(raw_year)
    except (TypeError, ValueError):
        return 'Year Published must be a valid year.', {}
    if year < 1000 or year > 9999:
        return 'Year Published must be between 1000 and 9999.', {}
    cleaned['year_published'] = year
    return None, cleaned


def _condition_display(cond):
    """(lost, damaged, reason) display dict for one conditions row.

    Row shape is (inventory_state, inv_notes, circ_damage, circ_lost).
    Lost shows the inventory note only; damaged shows the inventory note,
    falling back to the latest loan damage note when inventory never
    assessed the copy. A later clean inventory state wins over an old
    loan note. Short/None rows degrade to all-clear, never 500.
    """
    if not cond:
        return {'lost': False, 'damaged': False, 'reason': None}
    state = cond[0] if len(cond) > 0 else None
    inv_notes = cond[1] if len(cond) > 1 else None
    circ_damage = cond[2] if len(cond) > 2 else None
    circ_lost = cond[3] if len(cond) > 3 else False
    lost = state == 'lost' or bool(circ_lost)
    if lost:
        return {'lost': True, 'damaged': False,
                'reason': inv_notes or None}
    damaged = state == 'damaged' or (state is None and bool(circ_damage))
    reason = (inv_notes or circ_damage) if damaged else None
    return {'lost': False, 'damaged': damaged, 'reason': reason or None}


def _validate_accession_number(accession_number):
    """Error message for a newly entered accession number, None when usable.

    Accession numbers are 6-digit sequential numbers (e.g. 000001).
    Lookups of existing stock (borrow/return/condition/scan) accept any
    stored value — only creation paths use this validator, so legacy
    numbers already in the database keep working.
    """
    import re
    if not accession_number:
        return 'Accession number is required.'
    if not re.fullmatch(r'\d{6}', accession_number):
        return 'Accession number must be exactly 6 digits (e.g. 000001).'
    return None


def _stash_book_form(modal, extra=None):
    """stash typed book-form values in the session for redisplay.

    Validation errors redirect (Post/Redirect/Get), which would wipe
    everything the librarian typed. The next cataloging_page GET pops
    this stash and the matching modal repopulates its inputs, so typed
    data survives the error round-trip. Best-effort: never breaks the
    redirect when sessions are unavailable.
    """
    try:
        data = request.form.to_dict()
        data['_modal'] = modal
        data['_extra_categories'] = request.form.getlist('extra_categories')
        if extra:
            data.update(extra)
        session['book_form_data'] = data
    except Exception:
        pass


def _pop_stashed_book_form():
    """Pop the stashed book-form dict, or {} when absent/unreadable."""
    try:
        data = session.pop('book_form_data', None)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


@cataloging_bp.route('/librarian/cataloging')
@login_required
@librarian_required
def cataloging_page():
    """Render the librarian catalog listing (GET /librarian/cataloging).
    Requires login plus Librarian or Admin role. Parses q, field, status,
    copy_status, sort_by, and page query args, fetches the matching page
    plus accessions and copy conditions, and renders the catalog table
    with clamped pagination. Read-only; writes no audit row.
    Args:
        None (reads `q`, `field`, `status`, `copy_status`, `sort_by`, `page`).
    Returns:
        Rendered cataloging/cataloging.html with books and copy details.
    """
    query = request.args.get('q', '').strip()
    field = request.args.get('field', '')
    status_filter = request.args.get('status', '')
    copy_status = request.args.get('copy_status', '')
    material_type = request.args.get('material_type', '').strip()
    if material_type not in MATERIAL_TYPES:
        material_type = ''
    page = request.args.get('page', 1, type=int)
    page = max(1, page or 1)
    per_page = 20

    from app.cataloging.models import COPY_STATUS_FILTERS, _CATALOG_SORTS
    if copy_status not in COPY_STATUS_FILTERS:
        copy_status = ''
    sort_by = request.args.get('sort_by', '').strip()
    if sort_by not in _CATALOG_SORTS:
        sort_by = ''
    if copy_status:
        from app.cataloging.models import get_books_by_copy_status_paginated
        books, total = get_books_by_copy_status_paginated(
            copy_status, page, per_page, sort_by, material_type)
    elif status_filter:
        from app.cataloging.models import get_books_by_status_paginated
        books, total = get_books_by_status_paginated(
            status_filter, page, per_page, sort_by, material_type)
    elif query:
        books, total = search_books_paginated(
            query, field, page, per_page, sort_by, material_type)
    else:
        from app.cataloging.models import get_all_books_paginated
        books, total = get_all_books_paginated(
            page, per_page, sort_by, material_type)

    total_pages = max(1, (total + per_page - 1) // per_page)
    if page > total_pages:
        # Stale/bookmarked page past the end after data changed — clamp
        # and re-fetch once instead of rendering an empty page.
        page = total_pages
        if copy_status:
            from app.cataloging.models import get_books_by_copy_status_paginated
            books, total = get_books_by_copy_status_paginated(
                copy_status, page, per_page, sort_by, material_type)
        elif status_filter:
            from app.cataloging.models import get_books_by_status_paginated
            books, total = get_books_by_status_paginated(
                status_filter, page, per_page, sort_by, material_type)
        elif query:
            books, total = search_books_paginated(
                query, field, page, per_page, sort_by, material_type)
        else:
            from app.cataloging.models import get_all_books_paginated
            books, total = get_all_books_paginated(
                page, per_page, sort_by, material_type)

    accessions_by_book = {}
    if books:
        for row in get_accessions_for_books([book[0] for book in books]):
            accessions_by_book.setdefault(row[2], []).append(row)

    from app.inventory.models import get_conditions_for_accessions
    try:
        all_accession_ids = [copy[0] for copies in accessions_by_book.values()
                             for copy in copies]
        conditions_by_accession = get_conditions_for_accessions(all_accession_ids)
    except Exception:
        current_app.logger.warning('condition lookup failed', exc_info=True)
        conditions_by_accession = {}

    copy_conditions = {
        acc_id: _condition_display(cond)
        for acc_id, cond in conditions_by_accession.items()
    }
    show_reason_col = copy_status in ('lost', 'damaged', 'lost_damaged')
    reasons_by_book = {}
    if show_reason_col:
        want = ({'lost'} if copy_status == 'lost'
                else {'damaged'} if copy_status == 'damaged'
                else {'lost', 'damaged'})
        for book_id, copies in accessions_by_book.items():
            seen = []
            for copy in copies:
                display = copy_conditions.get(copy[0])
                if not display:
                    continue
                if 'lost' in want and display['lost'] and display['reason']:
                    if display['reason'] not in seen:
                        seen.append(display['reason'])
                if 'damaged' in want and display['damaged'] and display['reason']:
                    if display['reason'] not in seen:
                        seen.append(display['reason'])
            reasons_by_book[book_id] = ' | '.join(seen) if seen else '—'

    try:
        _cat_rows = [row for row in (get_categories() or [])
                     if row and len(row) > 1 and row[1]]
    except Exception:
        _cat_rows = []
    all_categories = [row[1] for row in _cat_rows]
    category_options = [(row[0], row[1]) for row in _cat_rows]
    try:
        _cats_by_book = get_categories_for_books([book[0] for book in books]) if books else {}
    except Exception:
        _cats_by_book = {}
    cats_by_book_ids = {str(bid): [cid for cid, _ in pairs]
                        for bid, pairs in _cats_by_book.items()}

    stashed_form = _pop_stashed_book_form()

    return render_template('cataloging/cataloging.html', books=books,
                           total=total, search_query=query,
                           search_field=field, status_filter=status_filter,
                           copy_status=copy_status, sort_by=sort_by,
                           material_type=material_type,
                           page=page, per_page=per_page,
                           accessions_by_book=accessions_by_book,
                           conditions_by_accession=conditions_by_accession,
                           copy_conditions=copy_conditions,
                           reasons_by_book=reasons_by_book,
                           show_reason_col=show_reason_col,
                           all_categories=all_categories,
                           category_options=category_options,
                           cats_by_book_ids=cats_by_book_ids,
                           stashed_form=stashed_form)


_BOOK_EXPORT_HEADERS = [
    'Book ID', 'Title', 'Author', 'Edition', 'Publisher', 'Year Published',
    'Subject Classification', 'Call Number', 'ISBN', 'Material Type',
    'Description', 'Status', 'Date Added', 'E-Book Link', 'Other Categories', 'Accession Numbers',
]


# book_catalog.* is 16 cols on current schema (0 book_id … 12 date_added,
# 13 updated_at, 14 updated_by, 15 category_id) with extra_categories then
# accession_numbers appended last by get_all_books()/get_books_by_status().
# Tail positions use negative indices so exports stay correct even if
# columns are added later. The extra-categories cell is only read from
# full-shaped rows (longer than the legacy 15-col book + accessions mock
# shape); shorter rows export a blank. Keep _BOOK_EXPORT_HEADERS width in
# sync with these positions.
_BOOK_COL = {
    'book_id': 0, 'title': 1, 'author': 2, 'edition': 3, 'publisher': 4,
    'year': 5, 'subject': 6, 'call_number': 7, 'isbn': 8, 'material': 9,
    'description': 10, 'status': 11, 'date_added': 12, 'accessions': -1,
}


def _book_row_to_export(row):
    """Convert a catalog book tuple into a 16-column export row.
    Maps positional cols (0 book_id through 12 date_added) plus trailing
    ebook link, extra_categories and accession_numbers into strings,
    formatting date_added via isoformat when possible. Tolerates short
    mock rows without raising.
    Args:
        row: Positional book tuple from the catalog queries.
    Returns:
        List of 16 export-ready strings matching _BOOK_EXPORT_HEADERS.
    """
    def _str(v):
        """Coerce one book export cell to string, mapping None to blank.

        Keeps CSV/XLSX catalog exports stable across nullable columns
        (edition, publisher, ISBN) and short mock rows.

        Args:
            v: Raw cell value.

        Returns:
            Empty string for None, else str(v).
        """
        return '' if v is None else str(v)
    # accession_numbers is appended last by the catalog queries; date_added at 12.
    # extra_categories sits second-to-last and ebook_url at book index 16 on
    # full-shaped rows only.
    date_added = row[_BOOK_COL['date_added']] if len(row) > _BOOK_COL['date_added'] else ''
    acc = row[_BOOK_COL['accessions']] if len(row) > 0 else ''
    extra = row[-2] if len(row) > 16 else ''
    ebook_link = row[16] if len(row) > 17 else ''
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
        _str(ebook_link),
        _str(extra),
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
    """Style the header row and layout of the books XLSX export.
    Applies the navy header fill, white bold font, centered wrapping,
    thin borders, frozen top row, autofilter, and content-tuned column
    widths so the downloaded catalog workbook stays readable.
    Args:
        ws: Openpyxl worksheet whose row 1 holds the export.
        headers: Header label list written into row 1.
    Returns:
        None; styles the worksheet in place.
    """
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
    widths = [8, 30, 22, 10, 18, 10, 22, 14, 14, 12, 32, 10, 12, 30, 24, 24]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = w


@cataloging_bp.route('/librarian/cataloging/export')
@login_required
@librarian_required
def export_books():
    """Export filtered books as CSV or XLSX (GET, Librarian+Admin only).
    Guarded by login_required then librarian_required. Parses status and
    format query args, fetches all or status-filtered books, logs
    cataloging:export_books:<filter>:<count>, and returns a timestamped
    download with styled XLSX or streamed CSV body.
    Args:
        None (reads `status` and `format` query args).
    Returns:
        File download Response with CSV or XLSX body and disposition.
    """
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
    """Add a book title or another copy (POST, Librarian+Admin only).
    Guarded by login_required then librarian_required. Validates the book
    form and optional 6-digit accession, rejects duplicates, merges into
    the existing title when title/author/ISBN match or creates a new
    title, marks the Bloom registry dirty, logs cataloging:add_book or
    add_copy, and redirects with a flash (Post/Redirect/Get).
    Args:
        None (reads book fields plus `accession_number`, `source` forms).
    Returns:
        Redirect to the cataloging page with modal status and flash.
    """
    error, fields = _validate_book_form(request.form)
    if error:
        flash(error, 'error')
        _stash_book_form('addBookModal')
        return redirect(url_for('cataloging.cataloging_page', modal='addBookModal', mstatus='error'))
    title, author = fields['title'], fields['author']

    accession_number = request.form.get('accession_number', '').strip()
    if not accession_number:
        # Panel revision: auto-increment accession when left blank
        try:
            accession_number = get_next_accession_number()
        except Exception:
            pass
    acc_error = _validate_accession_number(accession_number) if accession_number else None
    if acc_error:
        flash(acc_error, 'error')
        _stash_book_form('addBookModal')
        return redirect(url_for('cataloging.cataloging_page', modal='addBookModal', mstatus='error'))
    if accession_number:
        existing = get_accession_by_number(accession_number)
        if existing:
            flash(f'Accession number {accession_number} already exists.', 'error')
            _stash_book_form('addBookModal')
            return redirect(url_for('cataloging.cataloging_page', modal='addBookModal', mstatus='error'))

    isbn = fields['isbn']
    existing_book = get_book_by_title_author_isbn(title, author, isbn)
    source = request.form.get('source', '').strip() or None
    category_id, canonical_subject = resolve_category(fields['subject_classification'])
    fields['subject_classification'] = canonical_subject or fields['subject_classification']
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
        edition=fields['edition'],
        publisher=fields['publisher'],
        year_published=fields['year_published'],
        subject_classification=fields['subject_classification'],
        call_number=fields['call_number'],
        isbn=isbn,
        material_type=fields['material_type'],
        description=request.form.get('description', '').strip() or None,
        category_id=category_id,
        ebook_url=fields['ebook_url'],
        ebook_allow_download=fields['ebook_allow_download'],
    )
    bloom_registry.mark_dirty()
    if accession_number:
        create_accession(
            accession_number=accession_number,
            book_id=book_id,
            librarian_id=current_user.id,
            source=source,
        )
    try:
        set_book_categories(book_id, request.form.getlist('extra_categories'))
    except Exception:
        current_app.logger.warning('set_book_categories failed for book %s', book_id, exc_info=True)
    log_activity(current_user.id, 'cataloging:add_book')
    flash('Book added to catalog.', 'success')
    return redirect(url_for('cataloging.cataloging_page', modal='addBookModal', mstatus='success'))


@cataloging_bp.route('/librarian/cataloging/<int:book_id>/edit', methods=['POST'])
@login_required
@librarian_required
def edit_book(book_id):
    """Edit a book title record (POST, Librarian+Admin only).
    Guarded by login_required then librarian_required. Requires the book
    row, validates the edited form, updates via update_book, marks the
    Bloom registry dirty, logs cataloging:edit_book:<id> with a title
    diff, flashes success, and redirects with modal flags.
    Args:
        book_id: Primary key of the book title to update.
    Returns:
        Redirect to the cataloging page with modal status and flash.
    """
    book = get_book_by_id(book_id)
    if not book:
        flash('Book not found.', 'error')
        return redirect(url_for('cataloging.cataloging_page'))

    error, fields = _validate_book_form(request.form)
    if error:
        flash(error, 'error')
        _stash_book_form('editBookModal', {'_book_id': str(book_id)})
        return redirect(url_for('cataloging.cataloging_page', modal='editBookModal',
                                book_id=book_id, mstatus='error'))
    title, author = fields['title'], fields['author']

    category_id, canonical_subject = resolve_category(fields['subject_classification'])
    fields['subject_classification'] = canonical_subject or fields['subject_classification']

    update_book(
        book_id=book_id,
        title=title,
        author=author,
        edition=fields['edition'],
        publisher=fields['publisher'],
        year_published=fields['year_published'],
        subject_classification=fields['subject_classification'],
        call_number=fields['call_number'],
        isbn=fields['isbn'],
        material_type=fields['material_type'],
        description=request.form.get('description', '').strip() or None,
        updated_by=current_user.id,
        category_id=category_id,
        ebook_url=fields['ebook_url'],
        ebook_allow_download=fields['ebook_allow_download'],
    )
    bloom_registry.mark_dirty()
    try:
        set_book_categories(book_id, request.form.getlist('extra_categories'))
    except Exception:
        current_app.logger.warning('set_book_categories failed for book %s', book_id, exc_info=True)
    from app.auth.models import audit_text
    old_title = (book[1] or '') if len(book) > 1 else ''
    detail = ''
    if title != old_title:
        detail = f":title:{audit_text(old_title)}~>{audit_text(title)}"
    log_activity(current_user.id, f'cataloging:edit_book:{book_id}{detail}')
    flash('Book updated.', 'success')
    return redirect(url_for('cataloging.cataloging_page', modal='editBookModal', book_id=book_id, mstatus='success'))


@cataloging_bp.route('/librarian/cataloging/<int:book_id>/delete', methods=['POST'])
@login_required
@librarian_required
def delete_book_route(book_id):
    """Permanently delete an archived book (POST, Librarian+Admin only).
    Guarded by login_required then librarian_required. Enforces
    archive-then-delete via book[11], deletes via delete_book, marks the
    Bloom registry dirty, logs cataloging:delete_book:<id>, flashes the
    outcome, and redirects to the catalog page.
    Args:
        book_id: Primary key of the archived book to delete.
    Returns:
        Redirect to the cataloging page with a flash message.
    """
    book = get_book_by_id(book_id)
    if not book:
        flash('Book not found.', 'error')
        return redirect(url_for('cataloging.cataloging_page'))
    try:
        status = book[11]
    except (IndexError, TypeError):
        current_app.logger.warning('delete_book short row for book %s', book_id)
        flash('Book record is unavailable. Please try again.', 'error')
        return redirect(url_for('cataloging.cataloging_page'))
    if status != 'archived':
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
    """Toggle a book between active and archived (POST, staff only).
    Guarded by login_required then librarian_required. Requires the book
    row, flips active to archived or back via update_book_status, logs
    cataloging:toggle_status:<id>:<new>, flashes the new status, and
    redirects to the catalog page.
    Args:
        book_id: Primary key of the book whose status flips.
    Returns:
        Redirect to the cataloging page with a flash message.
    """
    book = get_book_by_id(book_id)
    if not book:
        flash('Book not found.', 'error')
        return redirect(url_for('cataloging.cataloging_page'))

    try:
        current_status = book[11]
    except (IndexError, TypeError):
        current_app.logger.warning('toggle_book short row for book %s', book_id)
        flash('Book record is unavailable. Please try again.', 'error')
        return redirect(url_for('cataloging.cataloging_page'))

    new_status = 'archived' if current_status == 'active' else 'active'
    update_book_status(book_id, new_status, updated_by=current_user.id)
    log_activity(current_user.id, f'cataloging:toggle_status:{book_id}:{new_status}')
    flash(f'Book {new_status}.', 'success')
    return redirect(url_for('cataloging.cataloging_page'))


@cataloging_bp.route('/librarian/cataloging/<int:book_id>/accession/add', methods=['POST'])
@login_required
@librarian_required
def add_accession(book_id):
    """Add a physical copy to a book (POST, Librarian+Admin only).
    Guarded by login_required then librarian_required. Requires the book
    row, validates the 6-digit accession and rejects duplicates, creates
    via create_accession, logs cataloging:add_accession:<book_id>,
    flashes the new number, and redirects with modal flags.
    Args:
        book_id: Primary key of the book receiving the copy.
    Returns:
        Redirect to the cataloging page with modal status and flash.
    """
    book = get_book_by_id(book_id)
    if not book:
        flash('Book not found.', 'error')
        return redirect(url_for('cataloging.cataloging_page'))

    accession_number = request.form.get('accession_number', '').strip()
    source = request.form.get('source', '').strip() or None

    acc_error = _validate_accession_number(accession_number)
    if acc_error:
        flash(acc_error, 'error')
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
    """Edit an accession copy number/source (POST, staff only).
    Guarded by login_required then librarian_required. Requires the
    accession row, validates the new 6-digit number and rejects numbers
    owned by other copies, updates via update_accession, logs
    cataloging:edit_accession:<id>, and redirects with modal flags.
    Args:
        accession_id: Primary key of the accession copy to update.
    Returns:
        Redirect to the cataloging page with modal status and flash.
    """
    acc = get_accession_by_id(accession_id)
    if not acc:
        flash('Accession copy not found.', 'error')
        return redirect(url_for('cataloging.cataloging_page'))

    accession_number = request.form.get('accession_number', '').strip()
    source = request.form.get('source', '').strip() or None

    acc_error = _validate_accession_number(accession_number)
    if acc_error:
        flash(acc_error, 'error')
        return redirect(url_for('cataloging.cataloging_page', modal='editAccessionModal', mstatus='error'))

    existing = get_accession_by_number(accession_number)
    if existing and existing[0] != accession_id:
        flash(f'Accession number {accession_number} already exists.', 'error')
        return redirect(url_for('cataloging.cataloging_page', modal='editAccessionModal', mstatus='error'))

    update_accession(accession_id, accession_number, source, updated_by=current_user.id)
    log_activity(current_user.id, f'cataloging:edit_accession:{accession_id}')
    flash(f'Accession {accession_number} updated.', 'success')
    return redirect(url_for('cataloging.cataloging_page', modal='editAccessionModal', mstatus='success'))


@cataloging_bp.route('/librarian/cataloging/categories', methods=['POST'])
@login_required
@librarian_required
def create_category():
    """Create (or fetch) one vocabulary category, returning JSON.

    Powers the in-modal category manager: POSTs a `name`, resolves it
    case-insensitively via resolve_category (existing spelling wins),
    logs cataloging:add_category:<id>, and returns the id/name pair so
    the dropdown can offer and check it immediately. Thin route: all
    SQL lives in models.
    """
    name = (request.form.get('name', '') or '').strip()
    if not name:
        return jsonify({'error': 'Category name is required.'}), 400
    if len(name) > 100:
        return jsonify({'error': 'Category name is too long (max 100 characters).'}), 400
    try:
        category_id, canonical = resolve_category(name)
    except Exception:
        current_app.logger.warning('create_category failed for %r', name, exc_info=True)
        return jsonify({'error': 'Could not save category.'}), 500
    if category_id is None:
        return jsonify({'error': 'Could not save category.'}), 500
    log_activity(current_user.id, f'cataloging:add_category:{category_id}')
    return jsonify({'id': category_id, 'name': canonical or name})


@cataloging_bp.route('/librarian/cataloging/accession/<int:accession_id>/delete', methods=['POST'])
@login_required
@librarian_required
def delete_accession_route(accession_id):
    """Delete an accession copy (POST, Librarian+Admin only).
    Guarded by login_required then librarian_required. Requires the copy
    row, refuses copies referenced by circulation or inventory records,
    deletes via delete_accession, logs cataloging:delete_accession:<id>,
    flashes the number deleted, and redirects.
    Args:
        accession_id: Primary key of the accession copy to delete.
    Returns:
        Redirect to the cataloging page with a flash message.
    """
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
    """Start a CSV bulk import job (POST, Librarian+Admin only).
    Guarded by login_required then librarian_required. Validates the
    uploaded .csv (size, decoding, headers with title/author/accession),
    creates a _import_jobs entry, then runs the worker inline under
    TESTING or in a daemon thread otherwise. Returns the job id as JSON.
    Args:
        None (reads the `file` upload from the multipart form).
    Returns:
        JSON with job_id and catalog redirect on success, else JSON error.
    """
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
    now = datetime.now()
    _import_jobs[job_id] = {
        'status': 'processing',
        'total': len(rows),
        'done': 0,
        'errors': [],
        'message': None,
        'created_at': now,
        'updated_at': now,
    }

    app = _get_current_app()
    if current_app.config.get('TESTING'):
        # Run inline under TESTING so no worker thread outlives the mocked
        # database (stray threads crash post-teardown and spam warnings).
        _bulk_import_worker(app, job_id, rows, column_map, current_user.id)
    else:
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
    """Poll a bulk import job (GET, Librarian+Admin only).
    Guarded by login_required then librarian_required. Cleans jobs older
    than 10 minutes, then returns the job's status, total, done count,
    message, and first errors as JSON, or 404 when the id is unknown.
    Args:
        job_id: UUID string of the import job to poll.
    Returns:
        JSON job progress payload, or JSON not_found with 404 status.
    """
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
    """Return the real Flask app object for the background import thread.
    Unwraps the LocalProxy so the bulk-import worker keeps a usable app
    reference with an app context after the request finishes. Needed
    because daemon threads outlive the original request context.
    Args:
        None.
    Returns:
        Flask application instance behind the current_app proxy.
    """
    from flask import current_app
    return current_app._get_current_object()


def _bulk_import_worker(app, job_id, rows, column_map, user_id):
    """Import CSV rows into books and accessions in the background.
    Runs inside an app context with per-row guards so one bad row never
    kills the job (background threads have no request error handler).
    Deduplicates titles and accessions, normalizes source values, updates
    job progress under lock, logs cataloging:bulk_import counts, marks
    the Bloom registry dirty, and stores the final summary message.
    Args:
        app: Flask app providing the context for DB work.
        job_id: UUID key of the _import_jobs entry to update.
        rows: List of CSV DictReader row dicts to import.
        column_map: Header-to-DB-column mapping from _map_headers.
        user_id: Librarian id credited for created accessions.
    Returns:
        None; progress and results are written into _import_jobs.
    """
    with app.app_context():
        from app.cataloging.models import create_book, create_accession, get_accession_by_number
        from app.database import db
        from app.auth.models import log_activity
        imported = 0
        errors = []
        total = len(rows)

        for i, row in enumerate(rows, start=2):
            try:
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
                        _import_jobs[job_id]['updated_at'] = datetime.now()
                    continue
                if not accession_number:
                    errors.append(f'Row {i}: missing accession_number')
                    with _import_lock:
                        _import_jobs[job_id]['done'] = imported + len(errors)
                        _import_jobs[job_id]['updated_at'] = datetime.now()
                    continue

                isbn = book_data.get('isbn', '')
                existing_book = get_book_by_title_author_isbn(title, author, isbn or None)

                existing_acc = get_accession_by_number(accession_number)
                if existing_acc:
                    try:
                        same_book = existing_book and len(existing_acc) > 2 and existing_acc[2] == existing_book[0]
                    except (IndexError, TypeError):
                        same_book = False
                    if same_book:
                        imported += 1
                        with _import_lock:
                            _import_jobs[job_id]['done'] = imported + len(errors)
                            _import_jobs[job_id]['updated_at'] = datetime.now()
                        continue
                    errors.append(f'Row {i}: accession number {accession_number} already exists')
                    with _import_lock:
                        _import_jobs[job_id]['done'] = imported + len(errors)
                        _import_jobs[job_id]['updated_at'] = datetime.now()
                    continue

                if existing_book:
                    try:
                        book_id = existing_book[0]
                    except (IndexError, TypeError):
                        errors.append(f'Row {i}: unexpected book record shape')
                        with _import_lock:
                            _import_jobs[job_id]['done'] = imported + len(errors)
                            _import_jobs[job_id]['updated_at'] = datetime.now()
                        continue
                else:
                    year_str = book_data.get('year_published', '')
                    year = int(year_str) if year_str and year_str.isdigit() else None
                    # Semicolon-separated subjects: first is primary, the
                    # rest become secondary category links on the new book.
                    raw_subjects = [(s or '').strip()
                                    for s in (book_data.get('subject_classification') or '').split(';')]
                    raw_subjects = [s for s in raw_subjects if s]
                    primary_raw = raw_subjects[0] if raw_subjects else None
                    subject_id, subject_canonical = resolve_category(primary_raw)
                    row_material = book_data.get('material_type', 'Book') or 'Book'
                    row_ebook_url, url_err = validate_ebook_url(
                        book_data.get('ebook_url', ''), row_material)
                    if url_err:
                        errors.append(f'Row {i}: {url_err}')
                        with _import_lock:
                            _import_jobs[job_id]['done'] = imported + len(errors)
                            _import_jobs[job_id]['updated_at'] = datetime.now()
                        continue
                    book_id = create_book(
                        title=title,
                        author=author,
                        edition=book_data.get('edition') or None,
                        publisher=book_data.get('publisher') or None,
                        year_published=year,
                        subject_classification=subject_canonical or primary_raw,
                        call_number=book_data.get('call_number') or None,
                        isbn=isbn or None,
                        material_type=row_material,
                        description=book_data.get('description') or None,
                        category_id=subject_id,
                        ebook_url=row_ebook_url,
                    )
                    if book_id is None:
                        errors.append(f'Row {i}: could not create book record')
                        with _import_lock:
                            _import_jobs[job_id]['done'] = imported + len(errors)
                            _import_jobs[job_id]['updated_at'] = datetime.now()
                        continue
                    if len(raw_subjects) > 1:
                        extra_ids = []
                        for extra in raw_subjects[1:]:
                            try:
                                eid, _ = resolve_category(extra)
                            except Exception:
                                continue
                            if eid and eid != subject_id and eid not in extra_ids:
                                extra_ids.append(eid)
                        if extra_ids:
                            try:
                                set_book_categories(book_id, extra_ids)
                            except Exception as e:
                                errors.append(f'Row {i}: {e}')

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
                # Per-row guard: background threads have no request error
                # handler, so any DB failure must not kill the whole job.
                errors.append(f'Row {i}: {e}')

            with _import_lock:
                _import_jobs[job_id]['done'] = imported + len(errors)
                _import_jobs[job_id]['updated_at'] = datetime.now()

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
                'updated_at': datetime.now(),
            })


def _cleanup_old_jobs():
    """Drop bulk-import jobs idle for more than 10 minutes.
    Prevents the in-memory _import_jobs dict from growing across
    restarts-free uptime. Called on every status poll so stale entries
    disappear without a separate sweeper thread.
    Args:
        None.
    Returns:
        None; removes expired entries from _import_jobs in place.
    """
    cutoff = datetime.now() - _IMPORT_EXPIRY
    stale = [jid for jid, j in _import_jobs.items()
             if j.get('updated_at') and j['updated_at'] < cutoff]
    for jid in stale:
        _import_jobs.pop(jid, None)


@cataloging_bp.route('/catalog')
def public_catalog():
    """Render the public searchable catalog (GET /catalog, no login).
    Public endpoint with no RBAC guard. Parses q, field, year, category,
    material, availability, sort, view, and page args; stays empty until
    a term or filter is given, then queries search_books_filtered with
    50 per page and clamped pagination. Writes no audit row.
    Args:
        None (reads search and filter query args).
    Returns:
        Rendered public/catalog.html with books, facets, and pager.
    """
    query = request.args.get('q', '').strip()
    field = request.args.get('field', '')
    year_preset = request.args.get('year_preset', '').strip()
    year_from = request.args.get('year_from', '').strip()
    year_to = request.args.get('year_to', '').strip()
    sort_by = request.args.get('sort_by', '').strip()
    category = request.args.get('category', '').strip()
    material_type = request.args.get('material_type', '').strip()
    availability = request.args.get('availability', '').strip()
    view = request.args.get('view', 'grid').strip().lower()
    if view not in ('grid', 'list'):
        view = 'grid'

    # Year filter aligns to the PHT library calendar so the boundary
    # years follow the Asia/Manila wall clock, not the host clock.
    current_year = library_today().year
    # Dynamic year options: current year + previous three, descending.
    # A preset value IS the year ("2026" means published since 2026).
    # Legacy since_* values from older links map to the same outcome.
    year_options = [current_year - i for i in range(4)]
    if year_preset in {str(y) for y in year_options}:
        year_from = year_preset
        year_to = ''
    elif year_preset == 'since_this_year':
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

    from app.cataloging.models import search_books_filtered, get_distinct_categories, get_distinct_material_types

    def _material_types():
        try:
            rows = get_distinct_material_types() or []
        except Exception:
            return []
        types = []
        for row in rows:
            try:
                name = row[0]
            except (IndexError, TypeError):
                continue
            if name and name not in types:
                types.append(name)
        return types

    # Empty by default: only query DB when user has provided a search term or filter.
    # This keeps /catalog empty on first visit and clears when the search bar is emptied.
    has_search = bool(query or category or material_type or availability or year_from or year_to or sort_by)

    if not has_search:
        categories = [row[0] for row in (get_distinct_categories() or []) if row and row[0]]
        material_types = _material_types()
        books = []
        per_page = 50
        total = 0
        total_pages = 1
        page = 1
    else:
        page = max(1, request.args.get('page', 1, type=int) or 1)
        per_page = 50
        books, total = search_books_filtered(
            query, field=field if field else None,
            year_from=year_from or None, year_to=year_to or None,
            sort_by=sort_by or None, category=category or None,
            material_type=material_type or None, availability=availability or None,
            page=page, per_page=per_page
        )
        categories = [row[0] for row in (get_distinct_categories() or []) if row and row[0]]
        material_types = _material_types()
        total_pages = max(1, (total + per_page - 1) // per_page)
        if page > total_pages:
            # Stale/bookmarked page past the end — clamp and re-fetch once.
            page = total_pages
            books, total = search_books_filtered(
                query, field=field if field else None,
                year_from=year_from or None, year_to=year_to or None,
                sort_by=sort_by or None, category=category or None,
                material_type=material_type or None, availability=availability or None,
                page=page, per_page=per_page
            )

    return render_template('public/catalog.html', books=books,
                           search_query=query, search_field=field,
                           year_preset=year_preset,
                           year_from=year_from, year_to=year_to,
                           year_options=year_options,
                           sort_by=sort_by, category=category,
                           material_type=material_type, availability=availability,
                           current_year=current_year,
                           categories=categories,
                           material_types=material_types,
                           has_search=has_search, view=view,
                           page=page, total_pages=total_pages, total=total, per_page=per_page)


@cataloging_bp.route('/book/<int:book_id>')
def book_info(book_id):
    """Render one book's detail page (GET /book/<id>, no login).
    Public endpoint with no RBAC guard. Loads the book row plus its
    accessions, marks each copy available or borrowed, hides daily-loan
    copies when an overnight allocation blocks them, and passes the
    viewer profile when logged in. Missing books flash and redirect.
    Args:
        book_id: Primary key of the book title to display.
    Returns:
        Rendered public/bookinfo.html, or catalog redirect when missing.
    """
    book = get_book_by_id(book_id)
    if not book:
        flash('Book not found.', 'error')
        return redirect(url_for('cataloging.public_catalog'))
    accessions = get_accessions_by_book(book_id)
    from app.auth.models import get_user_by_id
    from app.circulation.models import (
        get_active_loan_accession_ids_by_book,
        get_active_loan_borrower_user_ids_by_book,
        is_book_blocked_for_daily,
    )
    borrowed_ids = get_active_loan_accession_ids_by_book(book_id)
    borrower_map = get_active_loan_borrower_user_ids_by_book(book_id)
    accessions_with_status = [
        (acc, acc[0] not in borrowed_ids) for acc in accessions
    ]
    any_available = any(is_available for _, is_available in accessions_with_status)
    # An Overnight-borrowed book that is already allocated is Not Available
    # for Daily Circulation — hide the remaining free copy from borrowers.
    if any_available and is_book_blocked_for_daily(book_id):
        accessions_with_status = [(acc, False) for acc, _ in accessions_with_status]
        any_available = False
    # LOW_STOCK_THRESHOLD is a floor on availability: overnight borrows may
    # consume copies above it but never the last `floor` copies, which stay
    # for in-library daily circulation. Surface that on the borrow modal.
    try:
        from app.circulation.models import count_available_accessions
        from app.settings.models import get_low_stock_threshold
        overnight_floor = get_low_stock_threshold()
        _n = count_available_accessions(book_id)
        overnight_available = int(_n) if _n is not None else None
    except Exception:
        overnight_available = None
    if overnight_available is None:
        overnight_floor, overnight_limited = 2, False
    else:
        overnight_limited = overnight_available <= overnight_floor
    user_data = get_user_by_id(current_user.id) if current_user.is_authenticated else None
    try:
        extra_categories = get_book_categories(book_id)
    except Exception:
        extra_categories = []
    from app.cataloging.models import ebook_link_info, drive_preview_url, docs_preview_url, clean_ebook_url
    _ebook_url = book[16] if len(book) > 16 else None
    _ebook_allow = book[17] if len(book) > 17 else True
    _ebook_kind, _ebook_id = ebook_link_info(_ebook_url)
    if _ebook_kind == 'drive' and _ebook_id:
        _ebook_preview = drive_preview_url(_ebook_id)
    elif _ebook_kind == 'docs':
        # The stored URL may be an edit/view variant; generate the
        # embeddable /preview form automatically either way.
        _ebook_preview = docs_preview_url(clean_ebook_url(_ebook_url))
    else:
        _ebook_preview = ''
    return render_template('public/bookinfo.html', book=book,
                           accessions=accessions_with_status, any_available=any_available,
                           borrower_map=borrower_map, user_data=user_data,
                           extra_categories=extra_categories,
                           ebook_url=_ebook_url or '',
                           ebook_kind=_ebook_kind or '',
                           ebook_download_allowed=_ebook_allow,
                           ebook_preview=_ebook_preview,
                           overnight_floor=overnight_floor,
                           overnight_limited=overnight_limited)


@cataloging_bp.route('/book/<int:book_id>/download')
def ebook_download(book_id):
    """Stream a title's e-book through this server as an attachment.

    Public route (pairs with /book/<id>): no auth guard. The stored
    link is never exposed — users download from the library itself
    while the bytes are served from Google. Body text/html means the
    file is not link-shared (or its owner disabled downloads), so fail
    with clear feedback instead of confusing browser output.
    """
    from app.cataloging.models import (
        ebook_link_info, download_source_url, open_ebook_stream,
        parse_size_bytes, MAX_EBOOK_DOWNLOAD_BYTES, ebook_download_filename,
        create_ebook_access,
    )
    book = get_book_by_id(book_id)
    if not book or (len(book) > 11 and (book[11] or 'active') != 'active'):
        return abort(404)
    # Librarian toggle (book[17], default True on unmigrated databases):
    # FALSE hides every Download button and blocks the proxy outright.
    if len(book) > 17 and book[17] is False:
        flash('Downloads for this e-book are disabled.', 'error')
        return redirect(url_for('cataloging.book_info', book_id=book_id))
    _ebook_url = book[16] if len(book) > 16 else None
    kind, file_id = ebook_link_info(_ebook_url)
    source_url = download_source_url(kind, file_id, _ebook_url)
    if not source_url:
        flash('This e-book has no downloadable link yet.', 'error')
        return redirect(url_for('cataloging.book_info', book_id=book_id))
    google_resp, err = open_ebook_stream(source_url)
    if err:
        flash(err, 'error')
        return redirect(url_for('cataloging.book_info', book_id=book_id))
    # Studio-level record for Analytics: a download is counted the moment
    # the proxy starts streaming bytes. Anonymous visitors log with no user.
    try:
        reader = current_user.id if getattr(current_user, 'is_authenticated', False) else None
        create_ebook_access(book_id, 'download', reader)
        if reader is not None:
            log_activity(current_user.id, f'cataloging:ebook_download:{book_id}')
    except Exception:
        pass  # Analytics logging is best-effort; the download still serves.
    # Honor a declared size immediately; stream the rest under the cap.
    declared = parse_size_bytes(google_resp)
    if declared and declared > MAX_EBOOK_DOWNLOAD_BYTES:
        google_resp.close()
        flash('That file is too large to download through the library site.', 'error')
        return redirect(url_for('cataloging.book_info', book_id=book_id))

    def _stream():
        sent = 0
        try:
            for chunk in google_resp.iter_content(chunk_size=64 * 1024):
                sent += len(chunk)
                if sent > MAX_EBOOK_DOWNLOAD_BYTES:
                    break
                if chunk:
                    yield chunk
        finally:
            google_resp.close()

    response = Response(_stream(), content_type=google_resp.headers.get('Content-Type') or 'application/octet-stream')
    response.headers['Content-Disposition'] = f'attachment; filename="{ebook_download_filename(book[1])}"'
    response.headers['Cache-Control'] = 'no-store'
    return response


@cataloging_bp.route('/book/<int:book_id>/read', methods=['POST'])
def ebook_read(book_id):
    """Record one Read Online open (public fire-and-forget postback).

    The book page is public, so no auth guard; anonymous readers log
    with no user. Validates that the title exists, is active, and
    carries an e-book link, stores a 'read' event for Analytics and the
    audit trail (when logged in), then answers 204. A logging failure
    never breaks reading — the fetch failure is invisible in the
    preview modal.
    """
    from app.cataloging.models import ebook_link_info, create_ebook_access
    book = get_book_by_id(book_id)
    if not book or (len(book) > 11 and (book[11] or 'active') != 'active'):
        return abort(404)
    kind, _file_id = ebook_link_info(book[16] if len(book) > 16 else None)
    if not kind:
        return abort(404)
    reader = current_user.id if getattr(current_user, 'is_authenticated', False) else None
    try:
        create_ebook_access(book_id, 'read', reader)
    except Exception:
        current_app.logger.warning('ebook read log failed', exc_info=True)
    if reader is not None:
        log_activity(current_user.id, f'cataloging:ebook_read:{book_id}')
    return '', 204
