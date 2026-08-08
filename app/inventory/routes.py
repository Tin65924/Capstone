from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import inventory_bp
from .models import (
    get_active_session, create_inventory_session, get_session,
    get_status_summary, count_accessions, reconcile_inventory,
    get_scanned_in_session, cancel_inventory_session
)
from app.auth.decorators import librarian_required
from app.auth.models import log_activity


@inventory_bp.route('/librarian/inventory')
@login_required
@librarian_required
def inventory_page():
    session_id = request.args.get('session_id', type=int)
    session = get_session(session_id) if session_id else get_active_session(current_user.id)
    status_summary = get_status_summary()
    return render_template('inventory/inventory.html', session=session, status_summary=status_summary)


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
    if not session or session[1] != current_user.id:
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
    return redirect(url_for('inventory.inventory_page'))


@inventory_bp.route('/librarian/inventory/session/<int:session_id>/cancel', methods=['POST'])
@login_required
@librarian_required
def cancel_session(session_id):
    session = get_session(session_id)
    if not session or session[1] != current_user.id:
        flash('Session not found.', 'error')
        return redirect(url_for('inventory.inventory_page'))

    if session[4] != 'active':
        flash('This session is not active.', 'error')
        return redirect(url_for('inventory.inventory_page'))

    cancel_inventory_session(session_id)
    log_activity(current_user.id, f'inventory:cancel_session:{session_id}')
    flash('Session cancelled.', 'success')
    return redirect(url_for('inventory.inventory_page'))