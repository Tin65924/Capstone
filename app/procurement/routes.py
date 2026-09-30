from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import procurement_bp
from .models import get_procurement_items, get_procurement_by_id, update_procurement_status, VALID_STATUSES
from app.auth.decorators import librarian_required
from app.auth.models import log_activity


@procurement_bp.route('/librarian/procurement')
@login_required
@librarian_required
def procurement_dashboard():
    items = get_procurement_items() or []
    return render_template('procurement/procurement.html', items=items)


@procurement_bp.route('/librarian/procurement/<int:procurement_id>/update-status', methods=['POST'])
@login_required
@librarian_required
def update_status(procurement_id):
    new_status = request.form.get('order_status')
    if new_status not in VALID_STATUSES:
        flash('Invalid status.', 'error')
        return redirect(url_for('procurement.procurement_dashboard'))

    if not get_procurement_by_id(procurement_id):
        flash('Procurement record not found.', 'error')
        return redirect(url_for('procurement.procurement_dashboard'))

    update_procurement_status(procurement_id, new_status, updated_by=current_user.id)
    log_activity(current_user.id, f'procurement:update_status:{procurement_id}')
    flash('Status updated.', 'success')
    return redirect(url_for('procurement.procurement_dashboard'))