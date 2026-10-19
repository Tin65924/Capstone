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
    count_scan_history, get_sessions
)
from app.cataloging.models import get_accession_by_number, get_accession_by_id
from app.circulation.models import get_active_loan_by_accession
from app.auth.decorators import librarian_required
from app.auth.models import log_activity


VALID_STATES = ['available', 'borrowed', 'lost', 'damaged', 'missing']


@inventory_bp.route('/librarian/inventory')
@login_required
@librarian_required
def inventory_page():
    """Render the librarian inventory dashboard with session and history.

    GET guarded by login + Librarian/Admin. Loads the requested or
    active session (ignored when malformed), status counts for the
    condition cards, one page of scan history optionally filtered by
    VALID_STATES, and the newest inventory sessions for the shared
    "Past Sessions" list (every session is visible to every librarian).
    Renders inventory/inventory.html; never writes.

    Returns:
        Rendered inventory dashboard template response.
    """
    session_id = request.args.get('session_id', type=int)
    session = get_session(session_id) if session_id else get_active_session()
    if session is not None and len(session) < 6:
        session = None

    status_summary = get_status_summary() or []
    status_counts = {}
    for _row in status_summary:
        try:
            _state, _count = _row[0], _row[1] if len(_row) > 1 else 0
            status_counts[_state] = int(_count or 0)
        except (IndexError, TypeError, ValueError):
            continue

    status_filter = request.args.get('status')
    if status_filter not in VALID_STATES:
        status_filter = None

    page = request.args.get('page', 1, type=int)
    if page < 1:
        page = 1

    scan_rows = get_scan_history(page=page, per_page=10, status_filter=status_filter) or []
    total_scans = count_scan_history(status_filter=status_filter) or 0
    total_pages = max(1, (total_scans + 9) // 10)

    sessions = get_sessions(limit=20)
    sessions = [s for s in (sessions or []) if s and len(s) >= 7]

    return render_template(
        'inventory/inventory.html',
        session=session,
        status_counts=status_counts,
        scan_rows=scan_rows,
        current_status=status_filter,
        current_page=page,
        total_pages=total_pages,
        sessions=sessions
    )


@inventory_bp.route('/librarian/inventory/session/start', methods=['POST'])
@login_required
@librarian_required
def start_session():
    """Open a new annual-physical inventory session.

    POST guarded by login + Librarian/Admin. Sessions are shared, so it
    refuses with an error flash while any session is already active (one
    inventory at a time); otherwise counts all accessions as the
    baseline, creates the session, logs inventory:start_session:<id>,
    flashes success, and redirects to the inventory page for the new
    session.

    Returns:
        Redirect to the inventory page (existing or new session).
    """
    existing = get_active_session()
    if existing:
        flash('A session is already active. Resume it instead.', 'error')
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
    """Close an active session by reconciling scans against the collection.

    POST guarded by login + Librarian/Admin. Verifies the session exists,
    is active; collects scanned ids,
    runs reconcile_inventory (marking unscanned available copies
    missing), logs inventory:complete_session:<id>, flashes the
    discrepancy count, and redirects back to the session view.

    Args:
        session_id: Inventory session to reconcile and close.

    Returns:
        Redirect to the inventory page for the session.
    """
    session = get_session(session_id)
    if not session or len(session) < 6:
        flash('Session not found.', 'error')
        return redirect(url_for('inventory.inventory_page'))

    if session[4] != 'active':
        flash('This session is not active.', 'error')
        return redirect(url_for('inventory.inventory_page'))

    scanned_rows = get_scanned_in_session(session_id) or []
    scanned_ids = {r[0] for r in scanned_rows}
    discrepancies = reconcile_inventory(session_id, scanned_ids, checked_by=current_user.id)

    log_activity(current_user.id, f'inventory:complete_session:{session_id}')
    flash(f'Session completed — {len(discrepancies)} discrepancies found.', 'success')
    return redirect(url_for('inventory.inventory_page', session_id=session_id))


@inventory_bp.route('/librarian/inventory/session/<int:session_id>/cancel', methods=['POST'])
@login_required
@librarian_required
def cancel_session(session_id):
    """Abort an active inventory session without reconciliation.

    POST guarded by login + Librarian/Admin. Verifies ownership and
    active status, marks the session cancelled via
    cancel_inventory_session, logs inventory:cancel_session:<id>,
    flashes success, and redirects to the inventory landing page.
    Already-recorded copy states are kept.

    Args:
        session_id: Active session to cancel.

    Returns:
        Redirect to the inventory page.
    """
    session = get_session(session_id)
    if not session or len(session) < 6:
        flash('Session not found.', 'error')
        return redirect(url_for('inventory.inventory_page'))

    if session[4] != 'active':
        flash('This session is not active.', 'error')
        return redirect(url_for('inventory.inventory_page'))

    cancel_inventory_session(session_id, updated_by=current_user.id)
    log_activity(current_user.id, f'inventory:cancel_session:{session_id}')
    flash('Session cancelled.', 'success')
    return redirect(url_for('inventory.inventory_page'))

@inventory_bp.route('/librarian/inventory/scan', methods=['POST'])
@login_required
@librarian_required
def scan_accession():
    """Record one barcode scan as available or borrowed.

    POST guarded by login + Librarian/Admin. Validates the session when
    given, requires an accession number, resolves it to a copy, derives
    state (borrowed when a live loan exists, else available), bumps the
    session counter, upserts the inventory row, logs inventory:scan:<id>,
    flashes the result, and redirects back preserving session_id.

    Returns:
        Redirect to the inventory page for the session (or landing).
    """
    accession_number = request.form.get('accession_number', '').strip()
    session_id = request.form.get('session_id', type=int)

    if session_id:
        session = get_session(session_id)
        if not session or len(session) < 6 or session[4] != 'active':
            flash('Session not found or not active.', 'error')
            return redirect(url_for('inventory.inventory_page'))

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
        update_session_scan(session_id, accession_id, updated_by=current_user.id)

    upsert_inventory_record(accession_id, state, inventory_type, current_user.id, session_id=session_id)

    log_activity(current_user.id, f'inventory:scan:{accession_id}')
    flash(f'Scanned {accession_number} — {state}.', 'success')
    return redirect(url_for('inventory.inventory_page', session_id=session_id))


@inventory_bp.route('/librarian/inventory/check', methods=['POST'])
@login_required
@librarian_required
def check_accession():
    """Look up and flash one copy's current condition without writing.

    POST guarded by login + Librarian/Admin. Resolves the barcode via
    get_accession_by_number and get_accession_status, then flashes an
    info line like '<number> — <title>: currently <state>' ('never
    scanned' when no row exists). Read-only; redirects back.

    Returns:
        Redirect to the inventory page preserving session_id.
    """
    accession_number = request.form.get('accession_number', '').strip()
    session_id = request.form.get('session_id', type=int)

    accession = get_accession_by_number(accession_number)
    if not accession:
        flash('Accession not found.', 'error')
        return redirect(url_for('inventory.inventory_page', session_id=session_id))

    status = get_accession_status(accession[0])
    if not status or len(status) < 3:
        flash('Accession status unavailable.', 'error')
        return redirect(url_for('inventory.inventory_page', session_id=session_id))
    state_text = status[2] if status[2] else 'never scanned'
    flash(f'{status[0]} — {status[1]}: currently {state_text}.', 'info')
    return redirect(url_for('inventory.inventory_page', session_id=session_id))


@inventory_bp.route('/librarian/inventory/accession/<int:accession_id>/damage', methods=['POST'])
@login_required
@librarian_required
def damage_accession(accession_id):
    """Flag one copy as damaged with a required reason note.

    POST guarded by login + Librarian/Admin. Verifies the copy exists,
    requires a non-empty note (max 255 chars), optionally validates the
    session, records via mark_copy_damaged, logs
    inventory:mark_damaged:<id>, flashes success, and redirects back.

    Args:
        accession_id: Copy to mark damaged.

    Returns:
        Redirect to the inventory page preserving session_id.
    """
    notes = request.form.get('notes', '').strip() or None
    session_id = request.form.get('session_id', type=int)

    if not get_accession_by_id(accession_id):
        flash('Accession copy not found.', 'error')
        return redirect(url_for('inventory.inventory_page'))

    if not notes:
        flash('A reason is required to mark a copy as damaged.', 'error')
        return redirect(url_for('inventory.inventory_page'))
    if len(notes) > 255:
        flash('Damage reason is too long (max 255 characters).', 'error')
        return redirect(url_for('inventory.inventory_page'))

    if session_id:
        session = get_session(session_id)
        if not session or len(session) < 6:
            flash('Session not found.', 'error')
            return redirect(url_for('inventory.inventory_page'))

    mark_copy_damaged(accession_id, notes, session_id=session_id, checked_by=current_user.id)
    log_activity(current_user.id, f'inventory:mark_damaged:{accession_id}')
    flash('Marked as damaged.', 'success')
    return redirect(url_for('inventory.inventory_page', session_id=session_id))


@inventory_bp.route('/librarian/inventory/accession/<int:accession_id>/lost', methods=['POST'])
@login_required
@librarian_required
def lost_accession(accession_id):
    """Flag one copy as lost with a required reason note.

    POST guarded by login + Librarian/Admin. Verifies the copy exists,
    requires a non-empty note (max 255 chars), optionally validates the
    session, records via mark_copy_lost, logs inventory:mark_lost:<id>,
    flashes success, and redirects back. Lost copies leave the
    lendable pool until recovered.

    Args:
        accession_id: Copy to mark lost.

    Returns:
        Redirect to the inventory page preserving session_id.
    """
    session_id = request.form.get('session_id', type=int)
    notes = request.form.get('notes', '').strip() or None

    if not get_accession_by_id(accession_id):
        flash('Accession copy not found.', 'error')
        return redirect(url_for('inventory.inventory_page'))

    if not notes:
        flash('A reason is required to mark a copy as lost.', 'error')
        return redirect(url_for('inventory.inventory_page'))
    if len(notes) > 255:
        flash('Note is too long (max 255 characters).', 'error')
        return redirect(url_for('inventory.inventory_page'))

    if session_id:
        session = get_session(session_id)
        if not session or len(session) < 6:
            flash('Session not found.', 'error')
            return redirect(url_for('inventory.inventory_page'))

    mark_copy_lost(accession_id, notes, session_id=session_id, checked_by=current_user.id)
    log_activity(current_user.id, f'inventory:mark_lost:{accession_id}')
    flash('Marked as lost.', 'success')
    return redirect(url_for('inventory.inventory_page', session_id=session_id))



@inventory_bp.route('/librarian/inventory/session/<int:session_id>/export')
@login_required
@librarian_required
def export_session(session_id):
    """Download a completed session's rows as CSV.

    GET guarded by login + Librarian/Admin. Verifies ownership and that
    the session is completed (active sessions are refused), streams
    get_session_export_rows as a CSV download named
    inventory_session_<id>.csv, and logs
    inventory:export_session:<id>.

    Args:
        session_id: Completed session to export.

    Returns:
        CSV download response, or a redirect with an error flash.
    """
    session = get_session(session_id)
    if not session or len(session) < 6:
        flash('Session not found.', 'error')
        return redirect(url_for('inventory.inventory_page'))

    if session[4] != 'completed':
        flash('Only completed sessions can be exported.', 'error')
        return redirect(url_for('inventory.inventory_page', session_id=session_id))

    rows = get_session_export_rows(session_id) or []

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