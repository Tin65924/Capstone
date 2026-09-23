from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import resources_bp
from .models import (
    get_resources, get_resource_by_id, create_resource,
    set_resource_active, log_access, count_resources,
)
from app.auth.decorators import librarian_required
from app.auth.models import log_activity


def _valid_url(url):
    cleaned = (url or '').strip()
    lowered = cleaned.lower()
    return cleaned if lowered.startswith(('http://', 'https://')) else None


@resources_bp.route('/librarian/online-resources')
@login_required
@librarian_required
def manage_resources():
    items = get_resources(active_only=False)
    return render_template(
        'resources/manage.html',
        items=items,
        active_count=count_resources(active_only=True),
    )


@resources_bp.route('/librarian/online-resources/add', methods=['POST'])
@login_required
@librarian_required
def add_resource():
    title = request.form.get('title', '').strip()
    url = _valid_url(request.form.get('url', ''))
    provider = request.form.get('provider', '').strip() or None
    description = request.form.get('description', '').strip() or None
    if not title:
        flash('Title is required.', 'error')
        return redirect(url_for('resources.manage_resources'))
    if not url:
        flash('URL must start with http:// or https://.', 'error')
        return redirect(url_for('resources.manage_resources'))
    create_resource(title, url, provider, description, current_user.id)
    log_activity(current_user.id, f'resources:add:{title[:60]}')
    flash('Online resource added.', 'success')
    return redirect(url_for('resources.manage_resources'))


@resources_bp.route('/librarian/online-resources/<int:resource_id>/toggle', methods=['POST'])
@login_required
@librarian_required
def toggle_resource(resource_id):
    row = get_resource_by_id(resource_id)
    if row is None:
        flash('Resource not found.', 'error')
        return redirect(url_for('resources.manage_resources'))
    set_resource_active(resource_id, not row[5])
    log_activity(current_user.id, f'resources:toggle:{resource_id}')
    flash('Resource deactivated.' if row[5] else 'Resource activated.', 'success')
    return redirect(url_for('resources.manage_resources'))


@resources_bp.route('/resources')
@login_required
def browse_resources():
    items = get_resources(active_only=True)
    return render_template('resources/browse.html', items=items)


@resources_bp.route('/resources/<int:resource_id>/visit')
@login_required
def visit_resource(resource_id):
    row = get_resource_by_id(resource_id)
    if row is None or not row[5]:
        flash('Resource is no longer available.', 'error')
        return redirect(url_for('resources.browse_resources'))
    url = _valid_url(row[3] or '')
    if not url:
        flash('Resource link is invalid. The librarian has been notified.', 'error')
        return redirect(url_for('resources.browse_resources'))
    log_access(resource_id, current_user.id)
    return redirect(url)
