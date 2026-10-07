from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
import re
from . import settings_bp
from .models import (SETTING_CATEGORIES, SETTING_DEFS, ADMIN_ONLY_KEYS,
                     LIBRARIAN_EDITABLE_KEYS,
                     SETTING_RANGES, get_settings_dict, update_setting,
                     sync_settings_to_config, parse_hhmm)
from app.auth.decorators import admin_required, librarian_required
from app.auth.models import log_activity


def _filtered_categories(allowed_keys):
    categories = [
        {'id': anchor, 'title': title, 'icon': icon, 'blurb': blurb,
         'fields': [(key, SETTING_DEFS[key]) for key in keys
                    if key in allowed_keys]}
        for anchor, title, icon, blurb, keys in SETTING_CATEGORIES
    ]
    return [c for c in categories if c['fields']]


def _apply_updates(allowed_keys):
    """Shared validation for both settings forms. Returns (updated, updated_keys, errors)."""
    errors = []
    updated = 0
    updated_keys = []
    pending_times = {}
    for key, (label, kind, _desc) in SETTING_DEFS.items():
        if kind == 'time':
            raw = request.form.get(key, '').strip()
            if raw == '':
                continue
            if key not in allowed_keys:
                errors.append(f'{label}: not editable here.')
                continue
            if parse_hhmm(raw) is None:
                errors.append(
                    f'{label}: invalid value "{raw}" (use HH:MM, 24-hour).')
                continue
            pending_times[key] = raw
            continue
        if kind == 'bool':
            # Toggle switches submit getlist values (checkbox '1' when
            # on plus a hidden '0' fallback). Absent entirely means the
            # field wasn't rendered — leave the stored value alone.
            raws = [r.strip().lower()
                    for r in request.form.getlist(key)]
            if not raws:
                continue
            if key not in allowed_keys:
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
            updated_keys.append(key)
            continue
        raw = request.form.get(key, '').strip()
        if raw == '':
            continue
        if key not in allowed_keys:
            errors.append(f'{label}: not editable here.')
            continue
        try:
            if kind == 'float':
                value = float(raw)
                if value < 0:
                    raise ValueError('must be >= 0')
                if key == 'RESERVATION_CLAIM_HOURS' and value == 0:
                    raise ValueError('must be greater than 0')
                if key == 'OVERDUE_FINE_PER_DAY' and value > 1000:
                    raise ValueError('must be at most 1000')
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
                if key in ('MAX_BORROW_LIMIT_STUDENT', 'MAX_BORROW_LIMIT_FACULTY') and value > 20:
                    raise ValueError('must be at most 20')
                if key in ('OVERNIGHT_DUE_DAYS_STUDENT', 'OVERNIGHT_DUE_DAYS_FACULTY',
                           'DAILY_CIRCULATION_DUE_DAYS', 'OVERDUE_GRACE_DAYS',
                           'RESERVATION_CLAIM_DAYS', 'DUE_SOON_NOTIFY_DAYS') and value > 60:
                    raise ValueError('must be at most 60')
        except ValueError as e:
            errors.append(f'{label}: invalid value "{raw}" ({e}).')
            continue
        update_setting(key, value, current_user.id)
        updated += 1
        updated_keys.append(key)
    if pending_times:
        # Opening must precede closing: resolve each side from the form
        # when submitted, else the stored value, and write nothing unless
        # the pair is coherent (avoids half-saved inverted hours).
        stored = {}
        try:
            stored = get_settings_dict()
        except Exception:
            pass
        open_raw = pending_times.get(
            'LIBRARY_OPENING_TIME', stored.get('LIBRARY_OPENING_TIME', ''))
        close_raw = pending_times.get(
            'LIBRARY_CLOSING_TIME', stored.get('LIBRARY_CLOSING_TIME', ''))
        open_t, close_t = parse_hhmm(open_raw), parse_hhmm(close_raw)
        if open_t is None or close_t is None or not open_t < close_t:
            errors.append(
                'Library hours: opening time must be earlier than closing time.')
        else:
            for key, raw in pending_times.items():
                update_setting(key, raw, current_user.id)
                updated += 1
                updated_keys.append(key)
    return updated, updated_keys, errors


def _finish_update(updated, updated_keys, errors, redirect_endpoint):
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
        detail = f'settings:update:{updated}:{",".join(updated_keys)}'
        log_activity(current_user.id, detail[:255])
    if errors:
        for err in errors:
            flash(err, 'error')
        if updated:
            flash(f'{updated} setting(s) updated.', 'success')
    elif updated:
        flash(f'{updated} setting(s) updated.', 'success')
    else:
        flash('No changes submitted.', 'info')
    return redirect(url_for(redirect_endpoint))


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
    # the database with their defaults and have no UI surface here —
    # librarians edit them at /librarian/settings.
    categories = _filtered_categories(ADMIN_ONLY_KEYS)
    return render_template('settings/settings.html', defs=SETTING_DEFS,
                           values=values, categories=categories,
                           sidebar='components/admin_sidebar_nav.html',
                           form_action=url_for('settings.update_settings'),
                           cancel_url=url_for('main.admin_dashboard'))


@settings_bp.route('/librarian/settings')
@login_required
@librarian_required
def librarian_settings_page():
    """Circulation constants for librarians: due dates, fines, limits, pickup windows."""
    try:
        values = get_settings_dict()
    except Exception:
        values = {}
        flash('Library settings table is not available yet.', 'error')
    categories = _filtered_categories(LIBRARIAN_EDITABLE_KEYS)
    return render_template('settings/settings.html', defs=SETTING_DEFS,
                           values=values, categories=categories,
                           sidebar='components/librarian_sidebar_nav.html',
                           form_action=url_for('settings.update_librarian_settings'),
                           cancel_url=url_for('main.librarian_dashboard'))


@settings_bp.route('/admin/settings/update', methods=['POST'])
@login_required
@admin_required
def update_settings():
    updated, updated_keys, errors = _apply_updates(ADMIN_ONLY_KEYS)
    return _finish_update(updated, updated_keys, errors, 'settings.settings_page')


@settings_bp.route('/librarian/settings/update', methods=['POST'])
@login_required
@librarian_required
def update_librarian_settings():
    updated, updated_keys, errors = _apply_updates(LIBRARIAN_EDITABLE_KEYS)
    return _finish_update(updated, updated_keys, errors, 'settings.librarian_settings_page')
