import csv
import io
from flask import render_template, request, redirect, url_for, flash, Response
from flask_login import login_required, current_user
from . import inventory_bp
from .models import (
    get_active_session, create_inventory_session, get_session,
    get_status_summary, count_accessions, reconcile_inventory,
    get_scanned_in_session, cancel_inventory_session,
    upsert_inventory_record, get_accession_status, mark_copy_damaged,
    mark_copy_lost, update_session_scan, get_session_export_rows, get_scan_history,
    count_scan_history
)
from app.cataloging.models import get_accession_by_number
from app.circulation.models import get_active_loan_by_accession
from app.auth.decorators import librarian_required
from app.auth.models import log_activity


VALID_STATES = ['available', 'borrowed', 'lost', 'damaged', 'missing']


@inventory_bp.route('/librarian/inventory')
@login_required
@librarian_required
def inventory_page():
    session_id = request.args.get('session_id', type=int)
    session = get_session(session_id) if session_id else get_active_session(current_user.id)

    status_summary = get_status_summary()
    status_counts = {state: count for state, count in status_summary}

    status_filter = request.args.get('status')
    if status_filter not in VALID_STATES:
        status_filter = None

    page = request.args.get('page', 1, type=int)
    if page < 1:
        page = 1

    scan_rows = get_scan_history(page=page, per_page=10, status_filter=status_filter)
    total_scans = count_scan_history(status_filter=status_filter)
    total_pages = max(1, (total_scans + 9) // 10)

    return render_template(
        'inventory/inventory.html',
        session=session,
        status_counts=status_counts,
        scan_rows=scan_rows,
        current_status=status_filter,
        current_page=page,
        total_pages=total_pages
    )


@inventory_bp.route('/librarian/inventory/session/start', methods=['POST'])
@login_required
@librarian_required
def start_session():
    existing = get_active_session(current_user.id)
    if existing:
        flash('You already have an active session. Resume it instead.', 'error')
        return redirect(url_for('inventory.inventory_page', session_id=existing[0]))

    total_books = count_accessions()
    new_session = create_inventory_session(current_user.id, total_books)
    session_id = new_session[0]
    log_activity(current_user.id, f'inventory:start_session:{session_id}')
    flash('Inventory session started.', 'success')
    return redirect(url_for('inventory.inventory_page', session_id=session_id))


@inventory_bp.route('/librarian/inventory/session/<int:session_id>/complete', methods=['POST'])
@login_required
@librarian_required
def complete_session(session_id):
    session = get_session(session_id)
    if not session or session[1] != int(current_user.id):
        flash('Session not found.', 'error')
        return redirect(url_for('inventory.inventory_page'))

    if session[4] != 'active':
        flash('This session is not active.', 'error')
        return redirect(url_for('inventory.inventory_page'))

    scanned_rows = get_scanned_in_session(session_id)
    scanned_ids = {r[0] for r in scanned_rows}
    discrepancies = reconcile_inventory(session_id, scanned_ids)

    log_activity(current_user.id, f'inventory:complete_session:{session_id}')
    flash(f'Session completed — {len(discrepancies)} discrepancies found.', 'success')
    return redirect(url_for('inventory.inventory_page', session_id=session_id))


@inventory_bp.route('/librarian/inventory/session/<int:session_id>/cancel', methods=['POST'])
@login_required
@librarian_required
def cancel_session(session_id):
    session = get_session(session_id)
    if not session or session[1] != int(current_user.id):
        flash('Session not found.', 'error')
        return redirect(url_for('inventory.inventory_page'))

    if session[4] != 'active':
        flash('This session is not active.', 'error')
        return redirect(url_for('inventory.inventory_page'))

    cancel_inventory_session(session_id)
    log_activity(current_user.id, f'inventory:cancel_session:{session_id}')
    flash('Session cancelled.', 'success')
    return redirect(url_for('inventory.inventory_page'))

@inventory_bp.route('/librarian/inventory/scan', methods=['POST'])
@login_required
@librarian_required
def scan_accession():
    accession_number = request.form.get('accession_number', '').strip()
    session_id = request.form.get('session_id', type=int)

    if not accession_number:
        flash('Accession number is required.', 'error')
        return redirect(url_for('inventory.inventory_page', session_id=session_id))

    accession = get_accession_by_number(accession_number)
    if not accession:
        flash('Accession not found.', 'error')
        return redirect(url_for('inventory.inventory_page', session_id=session_id))

    accession_id = accession[0]
    active_loan = get_active_loan_by_accession(accession_id)
    state = 'borrowed' if active_loan else 'available'
    inventory_type = 'annual_physical' if session_id else 'realtime_scan'

    if session_id:
        update_session_scan(session_id, accession_id)

    upsert_inventory_record(accession_id, state, inventory_type, current_user.id, session_id=session_id)

    log_activity(current_user.id, f'inventory:scan:{accession_id}')
    flash(f'Scanned {accession_number} — {state}.', 'success')
    return redirect(url_for('inventory.inventory_page', session_id=session_id))


@inventory_bp.route('/librarian/inventory/check', methods=['POST'])
@login_required
@librarian_required
def check_accession():
    accession_number = request.form.get('accession_number', '').strip()
    session_id = request.form.get('session_id', type=int)

    accession = get_accession_by_number(accession_number)
    if not accession:
        flash('Accession not found.', 'error')
        return redirect(url_for('inventory.inventory_page', session_id=session_id))

    status = get_accession_status(accession[0])
    state_text = status[2] if status[2] else 'never scanned'
    flash(f'{status[0]} — {status[1]}: currently {state_text}.', 'info')
    return redirect(url_for('inventory.inventory_page', session_id=session_id))


@inventory_bp.route('/librarian/inventory/accession/<int:accession_id>/damage', methods=['POST'])
@login_required
@librarian_required
def damage_accession(accession_id):
    notes = request.form.get('notes', '').strip() or None
    session_id = request.form.get('session_id', type=int)

    if session_id:
        session = get_session(session_id)
        if not session or session[1] != int(current_user.id):
            flash('Session not found.', 'error')
            return redirect(url_for('inventory.inventory_page'))

    mark_copy_damaged(accession_id, notes, session_id=session_id)
    log_activity(current_user.id, f'inventory:mark_damaged:{accession_id}')
    flash('Marked as damaged.', 'success')
    return redirect(url_for('inventory.inventory_page', session_id=session_id))


@inventory_bp.route('/librarian/inventory/accession/<int:accession_id>/lost', methods=['POST'])
@login_required
@librarian_required
def lost_accession(accession_id):
    session_id = request.form.get('session_id', type=int)

    if session_id:
        session = get_session(session_id)
        if not session or session[1] != int(current_user.id):
            flash('Session not found.', 'error')
            return redirect(url_for('inventory.inventory_page'))

    mark_copy_lost(accession_id, session_id=session_id)
    log_activity(current_user.id, f'inventory:mark_lost:{accession_id}')
    flash('Marked as lost.', 'success')
    return redirect(url_for('inventory.inventory_page', session_id=session_id))



@inventory_bp.route('/librarian/inventory/session/<int:session_id>/export')
@login_required
@librarian_required
def export_session(session_id):
    session = get_session(session_id)
    if not session or session[1] != int(current_user.id):
        flash('Session not found.', 'error')
        return redirect(url_for('inventory.inventory_page'))

    rows = get_session_export_rows(session_id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Accession Number', 'Title', 'Status', 'Last Checked', 'Notes'])
    for row in rows:
        writer.writerow(row)

    log_activity(current_user.id, f'inventory:export_session:{session_id}')
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=inventory_session_{session_id}.csv'}
    )