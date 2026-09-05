from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
import re
from . import settings_bp
from .models import SETTING_DEFS, get_settings_dict, update_setting, sync_settings_to_config
from app.auth.decorators import librarian_required
from app.auth.models import log_activity


@settings_bp.route('/librarian/settings')
@login_required
@librarian_required
def settings_page():
    try:
        values = get_settings_dict()
    except Exception:
        values = {}
        flash('Library settings table is not available yet.', 'error')
    return render_template('settings/settings.html', defs=SETTING_DEFS, values=values)


@settings_bp.route('/librarian/settings/update', methods=['POST'])
@login_required
@librarian_required
def update_settings():
    errors = []
    updated = 0
    for key, (label, kind, _desc) in SETTING_DEFS.items():
        raw = request.form.get(key, '').strip()
        if raw == '':
            continue
        try:
            if kind == 'float':
                value = float(raw)
                if value < 0:
                    raise ValueError('must be >= 0')
            else:
                # Strict integers: reject decimals like "2.5" instead of truncating.
                if not re.fullmatch(r'\d+', raw):
                    raise ValueError('must be a whole number')
                value = int(raw)
                if 'LIMIT' in key and value == 0:
                    raise ValueError('must be at least 1')
        except ValueError:
            errors.append(f'{label}: invalid value "{raw}".')
            continue
        update_setting(key, value, current_user.id)
        updated += 1
    try:
        sync_settings_to_config(current_app)
    except Exception:
        pass
    if updated:
        log_activity(current_user.id, f'settings:update:{updated}')
    if errors:
        for err in errors:
            flash(err, 'error')
        if updated:
            flash(f'{updated} setting(s) updated.', 'success')
    elif updated:
        flash(f'{updated} setting(s) updated.', 'success')
    else:
        flash('No changes submitted.', 'info')
    return redirect(url_for('settings.settings_page'))
