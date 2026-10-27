from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import procurement_bp
from .models import get_procurement_items, get_procurement_by_id, update_status_with_request, VALID_STATUSES
from app.auth.decorators import librarian_required
from app.auth.models import log_activity


@procurement_bp.route('/librarian/procurement')
@login_required
@librarian_required
def procurement_dashboard():
    """Render the librarian procurement dashboard with all order rows.

    Loads every procurement item newest-first via
    :func:`models.get_procurement_items` and renders the procurement
    table. No JSON here: this is the server-rendered landing page staff
    use to scan order states before drilling into status updates.

    Returns:
        Rendered ``procurement/procurement.html`` with ``items`` (list
        of procurement tuples, possibly empty).
    """
    items = get_procurement_items() or []
    return render_template('procurement/procurement.html', items=items)


@procurement_bp.route('/librarian/procurement/<int:procurement_id>/update-status', methods=['POST'])
@login_required
@librarian_required
def update_status(procurement_id):
    """Handle the procurement status-update POST for one order row.

    Validates the submitted ``order_status`` against ``VALID_STATUSES``
    and pre-checks that the procurement row exists, flashing an error
    and redirecting on either failure. On success writes the new status,
    records the ``procurement:update_status:<id>`` audit trail, flashes
    success, and redirects back to the dashboard (Post/Redirect/Get).

    Args:
        procurement_id: URL primary key of the procurement_log row.

    Returns:
        A redirect response to ``procurement.procurement_dashboard``.
    """
    new_status = request.form.get('order_status')
    if new_status not in VALID_STATUSES:
        flash('Invalid status.', 'error')
        return redirect(url_for('procurement.procurement_dashboard'))

    procurement = get_procurement_by_id(procurement_id)
    if not procurement:
        flash('Procurement record not found.', 'error')
        return redirect(url_for('procurement.procurement_dashboard'))

    update_status_with_request(procurement_id, procurement[1], new_status, updated_by=current_user.id)
    log_activity(current_user.id, f'procurement:update_status:{procurement_id}')
    flash('Status updated.', 'success')
    return redirect(url_for('procurement.procurement_dashboard'))
