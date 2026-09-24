from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
import re
from . import settings_bp
from .models import (SETTING_CATEGORIES, SETTING_DEFS, ADMIN_ONLY_KEYS,
                     SETTING_RANGES, get_settings_dict, update_setting,
                     sync_settings_to_config)
from app.auth.decorators import admin_required
from app.auth.models import log_activity


@settings_bp.route('/admin/settings')
@login_required
@admin_required
def settings_page():
    try:
        values = get_settings_dict()
    except Exception:
        values = {}
        flash('Library settings table is not available yet.', 'error')
    # Admins see only admin-only constants; circulation settings live in
    # the database with their defaults and have no UI surface.
    categories = [
        {'id': anchor, 'title': title, 'icon': icon, 'blurb': blurb,
         'fields': [(key, SETTING_DEFS[key]) for key in keys
                    if key in ADMIN_ONLY_KEYS]}
        for anchor, title, icon, blurb, keys in SETTING_CATEGORIES
    ]
    categories = [c for c in categories if c['fields']]
    return render_template('settings/settings.html', defs=SETTING_DEFS,
                           values=values, categories=categories,
                           sidebar='components/admin_sidebar_nav.html')


@settings_bp.route('/librarian/settings')
@login_required
def legacy_settings_redirect():
    """Backward-compat redirect: settings moved to /admin/settings."""
    return redirect(url_for('settings.settings_page'))


@settings_bp.route('/admin/settings/update', methods=['POST'])
@login_required
@admin_required
def update_settings():
    errors = []
    updated = 0
    for key, (label, kind, _desc) in SETTING_DEFS.items():
        if kind == 'bool':
            # Toggle switches submit getlist values (checkbox '1' when
            # on plus a hidden '0' fallback). Absent entirely means the
            # field wasn't rendered — leave the stored value alone.
            raws = [r.strip().lower()
                    for r in request.form.getlist(key)]
            if not raws:
                continue
            if key not in ADMIN_ONLY_KEYS:
                errors.append(f'{label}: not editable here.')
                continue
            try:
                if any(r not in ('1', 'true', 'on', 'yes',
                                 '0', 'false', 'off', 'no') for r in raws):
                    raise ValueError('must be on or off')
                value = (1 if any(r in ('1', 'true', 'on', 'yes')
                                  for r in raws) else 0)
            except ValueError as e:
                errors.append(f'{label}: invalid value ({e}).')
                continue
            update_setting(key, value, current_user.id)
            updated += 1
            continue
        raw = request.form.get(key, '').strip()
        if raw == '':
            continue
        if key not in ADMIN_ONLY_KEYS:
            errors.append(f'{label}: not editable here.')
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
                lo, hi = SETTING_RANGES.get(key, (None, None))
                if lo is not None and value < lo:
                    raise ValueError(f'must be at least {lo}')
                if hi is not None and value > hi:
                    raise ValueError(f'must be at most {hi}')
        except ValueError as e:
            errors.append(f'{label}: invalid value "{raw}" ({e}).')
            continue
        update_setting(key, value, current_user.id)
        updated += 1
    try:
        sync_settings_to_config(current_app)
    except Exception:
        pass
    if updated:
        try:
            from app.backup.scheduler import reschedule
            reschedule(current_app)
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
