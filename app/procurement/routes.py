from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import procurement_bp
from .models import (
    get_procurement_items, get_procurement_by_id,
    update_procurement_status, VALID_STATUSES,
    clear_supplier_catalog, add_supplier_item,
    get_supplier_catalog, count_supplier_catalog,
)
from app.requests.models import update_request_status as sync_request_status
from app.auth.decorators import librarian_required
from app.auth.models import log_activity

# Accepted CSV headers for the supplier book list (lowercased, stripped).
SUPPLIER_HEADERS = {
    'title': 'title', 'book_title': 'title', 'book': 'title',
    'author': 'author', 'author_name': 'author', 'writer': 'author',
    'supplier': 'supplier', 'supplier_name': 'supplier', 'vendor': 'supplier',
}

# Terminal procurement states mirror back onto the request lifecycle:
# a procured book closes its request, while a cancelled order returns the
# request to 'approved' so it can be sourced from another supplier.
PROCUREMENT_TO_REQUEST = {'procured': 'procured', 'cancelled': 'approved'}


@procurement_bp.route('/librarian/procurement')
@login_required
@librarian_required
def procurement_dashboard():
    status = request.args.get('status', '').strip()
    if status not in VALID_STATUSES:
        status = None
    items = get_procurement_items(status)
    return render_template(
        'procurement/procurement.html',
        items=items,
        status=status,
        supplier_items=get_supplier_catalog(),
        supplier_count=count_supplier_catalog(),
    )


@procurement_bp.route('/librarian/procurement/<int:procurement_id>/update-status', methods=['POST'])
@login_required
@librarian_required
def update_status(procurement_id):
    new_status = request.form.get('order_status')
    if new_status not in VALID_STATUSES:
        flash('Invalid status.', 'error')
        return redirect(url_for('procurement.procurement_dashboard'))

    row = get_procurement_by_id(procurement_id)
    if row is None:
        flash('Procurement record not found.', 'error')
        return redirect(url_for('procurement.procurement_dashboard'))

    update_procurement_status(procurement_id, new_status)
    linked_status = PROCUREMENT_TO_REQUEST.get(new_status)
    if linked_status and len(row) > 1 and row[1] is not None:
        sync_request_status(row[1], linked_status, current_user.id)
        flash(f'Status updated. Linked request marked {linked_status}.', 'success')
    else:
        flash('Status updated.', 'success')
    log_activity(current_user.id, f'procurement:update_status:{procurement_id}')
    return redirect(url_for('procurement.procurement_dashboard'))


@procurement_bp.route('/librarian/procurement/supplier-upload', methods=['POST'])
@login_required
@librarian_required
def supplier_upload():
    """Replace the supplier book list from an uploaded CSV.

    Expected headers: title (required), author, supplier (all optional
    except title). Each upload replaces the previous list outright.
    """
    import csv as csv_module

    if 'file' not in request.files:
        flash('No file selected.', 'error')
        return redirect(url_for('procurement.procurement_dashboard'))

    f = request.files['file']
    if not f.filename or not f.filename.lower().endswith('.csv'):
        flash('Please upload a CSV file.', 'error')
        return redirect(url_for('procurement.procurement_dashboard'))

    try:
        content = f.read().decode('utf-8-sig')
    except (UnicodeDecodeError, ValueError):
        flash('Unable to read file. Ensure it is a valid CSV file.', 'error')
        return redirect(url_for('procurement.procurement_dashboard'))

    lines = content.splitlines()
    reader = csv_module.DictReader(lines)
    if not reader.fieldnames:
        flash('CSV file has no headers.', 'error')
        return redirect(url_for('procurement.procurement_dashboard'))

    column_map = {}
    for header in reader.fieldnames:
        mapped = SUPPLIER_HEADERS.get((header or '').strip().lower())
        if mapped and mapped not in column_map.values():
            column_map[header] = mapped
    if 'title' not in column_map.values():
        flash('CSV must contain a "title" column.', 'error')
        return redirect(url_for('procurement.procurement_dashboard'))

    rows = [
        {column_map[k]: (v or '').strip() for k, v in row.items() if k in column_map}
        for row in reader
    ]
    rows = [r for r in rows if r.get('title')]
    if not rows:
        flash('CSV contains no book titles.', 'error')
        return redirect(url_for('procurement.procurement_dashboard'))

    clear_supplier_catalog()
    for row in rows:
        add_supplier_item(
            row.get('supplier') or 'Supplier',
            row['title'],
            row.get('author') or None,
            current_user.id,
        )
    log_activity(current_user.id, f'procurement:supplier_upload:{len(rows)}')
    flash(f'Supplier list updated — {len(rows)} titles.', 'success')
    return redirect(url_for('procurement.procurement_dashboard'))