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
    """Build sidebar category dicts containing only the allowed keys.

    Walks ``SETTING_CATEGORIES`` and keeps, per category, the fields
    whose keys appear in both the category definition and the caller's
    allowlist (admin-only vs librarian-editable). Drops categories left
    with no fields so the template never renders an empty section.

    Args:
        allowed_keys: Set of setting keys the current role may see.

    Returns:
        List of dicts with id, title, icon, blurb, and fields (list of
        (key, (label, kind, description)) tuples).
    """
    categories = [
        {'id': anchor, 'title': title, 'icon': icon, 'blurb': blurb,
         'fields': [(key, SETTING_DEFS[key]) for key in keys
                    if key in allowed_keys]}
        for anchor, title, icon, blurb, keys in SETTING_CATEGORIES
    ]
    return [c for c in categories if c['fields']]


def _apply_updates(allowed_keys):
    """Validate and persist settings form input for one role's allowlist.

    Shared validation for both settings forms. Returns (updated, updated_keys, errors).
    Walks every key in ``SETTING_DEFS`` by kind: times require HH:MM and
    the opening/closing pair is only written when coherent (opening <
    closing); bools parse checkbox+hidden-fallback getlists; day lists
    accept weekday checkboxes in canonical Mon–Sun order (all unchecked
    stores empty = closed every day); month maps accept per-date
    checkboxes as 'YYYY-MM:bits'; floats/ints
    enforce non-negativity, per-key caps (fines, borrow limits, day
    counts), and SETTING_RANGES bounds. Disallowed keys and blank inputs
    are skipped (blanks keep the stored value). Writes each valid key
    immediately via ``update_setting`` with the actor's id.

    Args:
        allowed_keys: Set of setting keys this form may change.

    Returns:
        Tuple (updated, updated_keys, errors) with the count of writes,
        the list of changed keys, and human-readable error strings.
    """
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
        if kind == 'days':
            # Weekday checkboxes submit one value per checked day plus a
            # hidden '' fallback. Absent entirely means the field wasn't
            # rendered — leave the stored value alone. All unchecked
            # stores '' (closed every day); unknown values are rejected.
            from .models import WEEKDAYS
            raws = [(r or '').strip() for r in request.form.getlist(key)]
            if not raws:
                continue
            if key not in allowed_keys:
                errors.append(f'{label}: not editable here.')
                continue
            picked = []
            bad = []
            for r in raws:
                if not r:
                    continue
                name = r.capitalize()
                if name not in WEEKDAYS:
                    bad.append(r)
                elif name not in picked:
                    picked.append(name)
            if bad:
                errors.append(
                    f'{label}: unknown day(s) {", ".join(bad)}.')
                continue
            picked.sort(key=WEEKDAYS.index)
            update_setting(key, ','.join(picked), current_user.id)
            updated += 1
            updated_keys.append(key)
            continue
        if kind == 'monthdays':
            # Per-date checkboxes submit 'YYYY-MM-DD' per checked date
            # plus a hidden '' fallback. Absent entirely means the field
            # wasn't rendered — leave the stored value alone. All dates
            # must belong to one real month with valid day numbers; the
            # map stores as 'YYYY-MM:bits' (one 0/1 per calendar date).
            from calendar import monthrange as _monthrange
            raws = [(r or '').strip() for r in request.form.getlist(key)]
            if not raws:
                continue
            if key not in allowed_keys:
                errors.append(f'{label}: not editable here.')
                continue
            months = set()
            checked = set()
            bad = []
            for r in raws:
                if not r:
                    continue
                match = re.fullmatch(
                    r'(\d{4})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])', r)
                if not match:
                    bad.append(r)
                    continue
                months.add(r[:7])
                checked.add(int(r[8:10]))
            if bad:
                errors.append(
                    f'{label}: unknown date(s) {", ".join(bad)}.')
                continue
            if not months:
                # Every date unchecked: only the hidden fallbacks
                # submitted. The grid always posts its month alongside,
                # so store all-closed for that month.
                hint = (request.form.get('open_month') or '').strip()
                if not re.fullmatch(r'\d{4}-(?:0[1-9]|1[0-2])', hint):
                    errors.append(
                        f'{label}: dates must all belong to one month.')
                    continue
                ym = hint
                day_count = _monthrange(int(ym[:4]), int(ym[5:7]))[1]
                update_setting(key, f'{ym}:{"0" * day_count}',
                               current_user.id)
                updated += 1
                updated_keys.append(key)
                continue
            if len(months) != 1:
                errors.append(
                    f'{label}: dates must all belong to one month.')
                continue
            ym = next(iter(months))
            day_count = _monthrange(int(ym[:4]), int(ym[5:7]))[1]
            if any(d < 1 or d > day_count for d in checked):
                errors.append(
                    f'{label}: {ym} has {day_count} days.')
                continue
            bits = ''.join('1' if d in checked else '0'
                           for d in range(1, day_count + 1))
            update_setting(key, f'{ym}:{bits}', current_user.id)
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
                           'OVERDUE_GRACE_DAYS',
                           'DUE_SOON_NOTIFY_DAYS') and value > 60:
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
    """Sync config, reschedule backups, audit, flash, and redirect.

    Re-syncs ``app.config`` from the database and re-applies the backup
    cron schedule (both best-effort so a sync failure never breaks the
    save), records a truncated ``settings:update:<n>:<keys>`` audit row
    when anything changed, flashes per-field errors plus a success or
    no-changes note, and redirects to the caller's settings page
    (Post/Redirect/Get).

    Args:
        updated: Count of settings written.
        updated_keys: List of changed setting keys for the audit row.
        errors: List of validation error strings to flash.
        redirect_endpoint: Flask endpoint name to redirect back to.

    Returns:
        A redirect response to ``redirect_endpoint``.
    """
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
    """Render the admin-only backup schedule settings page.

    Loads effective settings (flashing an error when the table is
    unavailable) and shows only ``ADMIN_ONLY_KEYS`` categories with the
    admin sidebar. Circulation constants stay database-backed but have
    no UI surface here; librarians edit them at /librarian/settings.

    Returns:
        Rendered ``settings/settings.html`` with defs, values,
        categories, sidebar, form action, and cancel URL.
    """
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
    """Render the librarian circulation-constants page.

    Circulation constants for librarians: due dates, fines, limits, pickup windows.
    Loads effective settings (flashing when the table is unavailable) and
    shows only ``LIBRARIAN_EDITABLE_KEYS`` categories with the librarian
    sidebar, so librarians can tune due dates, fines, borrow limits, and
    pickup windows without touching backup/admin-only settings.

    Returns:
        Rendered ``settings/settings.html`` scoped to the librarian
        allowlist with the librarian sidebar and form action.
    """
    try:
        values = get_settings_dict()
    except Exception:
        values = {}
        flash('Library settings table is not available yet.', 'error')
    categories = _filtered_categories(LIBRARIAN_EDITABLE_KEYS)
    try:
        from app.settings.models import library_today, month_grid
        _today = library_today()
        month_days = month_grid(_today.year, _today.month, values)
        month_label = _today.strftime('%B %Y')
        month_ym = _today.strftime('%Y-%m')
    except Exception:
        month_days = []
        month_label = ''
        month_ym = ''
    return render_template('settings/settings.html', defs=SETTING_DEFS,
                           values=values, categories=categories,
                           month_days=month_days, month_label=month_label,
                           month_ym=month_ym,
                           sidebar='components/librarian_sidebar_nav.html',
                           form_action=url_for('settings.update_librarian_settings'),
                           cancel_url=url_for('main.librarian_dashboard'))


@settings_bp.route('/admin/settings/update', methods=['POST'])
@login_required
@admin_required
def update_settings():
    """Handle the admin backup-schedule settings POST.

    Delegates validation and persistence to :func:`_apply_updates` with
    the admin allowlist, then finishes via :func:`_finish_update` back
    to the admin settings page. Thin route: all SQL lives in models.

    Returns:
        A redirect response to ``settings.settings_page``.
    """
    updated, updated_keys, errors = _apply_updates(ADMIN_ONLY_KEYS)
    return _finish_update(updated, updated_keys, errors, 'settings.settings_page')


@settings_bp.route('/librarian/settings/update', methods=['POST'])
@login_required
@librarian_required
def update_librarian_settings():
    """Handle the librarian circulation-constants settings POST.

    Delegates validation and persistence to :func:`_apply_updates` with
    the librarian allowlist, then finishes via :func:`_finish_update`
    back to the librarian settings page. Thin route: all SQL lives in
    models.

    Returns:
        A redirect response to ``settings.librarian_settings_page``.
    """
    updated, updated_keys, errors = _apply_updates(LIBRARIAN_EDITABLE_KEYS)
    return _finish_update(updated, updated_keys, errors, 'settings.librarian_settings_page')
