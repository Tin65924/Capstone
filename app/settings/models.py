from flask import current_app
from datetime import datetime, date, timedelta, timezone
from app.database import db
import os
import re


# Library wall-clock: Asia/Manila (UTC+8, no DST). Render servers run on
# UTC, so datetime.now()/date.today() are ~8h behind the Philippines —
# 1:33 PM in the library reads as 5:33 AM UTC and looks "closed".
# Fixed offset avoids a tzdata dependency on Windows/Render.
PHT = timezone(timedelta(hours=8), name='PHT')


def library_now():
    """Current wall-clock time in the library (Philippine time)."""
    return datetime.now(PHT)


def library_today():
    """Current calendar date in the library (Philippine time)."""
    return library_now().date()


def _env_default(name, fallback):
    """String default honoring an env override (BACKUP_* live in env today)."""
    try:
        return str(int(os.getenv(name, fallback)))
    except (TypeError, ValueError):
        return str(fallback)


# Sidebar categories: (anchor id, title, icon, blurb, setting keys).
# Every key in SETTING_DEFS must appear in exactly one category.
SETTING_CATEGORIES = [
    ('book', 'Book Settings', 'menu_book',
     'How many books each role may hold at once.',
     ['MAX_BORROW_LIMIT_STUDENT', 'MAX_BORROW_LIMIT_FACULTY']),
    ('hours', 'Library Hours', 'schedule',
     'Daily opening and closing hours. Borrowing is blocked outside open hours.',
     ['LIBRARY_OPENING_TIME', 'LIBRARY_CLOSING_TIME']),
    ('due-dates', 'Due Date Settings', 'event',
     'Loan periods for overnight and in-library use.',
     ['OVERNIGHT_DUE_DAYS_STUDENT', 'OVERNIGHT_DUE_DAYS_FACULTY',
      'DAILY_CIRCULATION_DUE_DAYS']),
    ('fines', 'Fine Settings', 'payments',
     'Overdue fines and grace periods.',
     ['OVERDUE_FINE_PER_DAY', 'OVERDUE_GRACE_DAYS']),
    ('reservations', 'Reservation Settings', 'bookmark',
     'Pickup windows and due-date reminders.',
     ['RESERVATION_CLAIM_HOURS', 'RESERVATION_CLAIM_DAYS', 'DUE_SOON_NOTIFY_DAYS']),
    ('backup-schedule', 'Backup Schedule', 'settings_backup_restore',
     'Automatic monthly backups and retention. Admin only.',
     ['BACKUP_DAY', 'BACKUP_HOUR', 'BACKUP_KEEP', 'BACKUP_RESTORE_ENABLED']),
]


# Keys only admins may view or edit. Librarians get the circulation
# categories; admins get exactly these.
ADMIN_ONLY_KEYS = frozenset({'BACKUP_DAY', 'BACKUP_HOUR', 'BACKUP_KEEP',
                             'BACKUP_RESTORE_ENABLED'})

# Keys librarians may view/edit on /librarian/settings. This is the
# complement of ADMIN_ONLY_KEYS: every circulation constant lives here so
# librarians can tune due dates, fines, borrow limits, and pickup windows
# without touching backup/admin-only settings.
LIBRARIAN_EDITABLE_KEYS = frozenset({
    'MAX_BORROW_LIMIT_STUDENT', 'MAX_BORROW_LIMIT_FACULTY',
    'LIBRARY_OPENING_TIME', 'LIBRARY_CLOSING_TIME',
    'OVERNIGHT_DUE_DAYS_STUDENT', 'OVERNIGHT_DUE_DAYS_FACULTY',
    'DAILY_CIRCULATION_DUE_DAYS',
    'OVERDUE_FINE_PER_DAY', 'OVERDUE_GRACE_DAYS',
    'RESERVATION_CLAIM_HOURS', 'RESERVATION_CLAIM_DAYS',
    'DUE_SOON_NOTIFY_DAYS',
})


# key -> (label, kind, description). Kinds: int, float, bool, time.
SETTING_DEFS = {
    'MAX_BORROW_LIMIT_STUDENT': ('Max borrows (Student)', 'int', 'Max active loans for students'),
    'MAX_BORROW_LIMIT_FACULTY': ('Max borrows (Faculty)', 'int', 'Max active loans for faculty'),
    'LIBRARY_OPENING_TIME': ('Opening hour', 'time', 'Daily opening hour (24-hour clock)'),
    'LIBRARY_CLOSING_TIME': ('Closing hour', 'time', 'Daily closing hour (must be after opening)'),
    'OVERNIGHT_DUE_DAYS_STUDENT': ('Overnight due days (Student)', 'int', 'Overnight loan due days for students'),
    'OVERNIGHT_DUE_DAYS_FACULTY': ('Overnight due days (Faculty)', 'int', 'Overnight loan due days for faculty'),
    'DAILY_CIRCULATION_DUE_DAYS': ('Daily circulation due days', 'int', 'Daily circulation due days (0 = same day)'),
    'OVERDUE_FINE_PER_DAY': ('Overdue fine per day (₱)', 'float', 'Overdue fine in pesos per day'),
    'OVERDUE_GRACE_DAYS': ('Overdue grace days', 'int', 'Grace days before fines accrue'),
    'RESERVATION_CLAIM_DAYS': ('Reservation claim days (legacy)', 'int', 'Days to claim an allocated reservation (used only when claim hours is empty)'),
    'RESERVATION_CLAIM_HOURS': ('Reservation claim hours', 'float', 'Hours to claim an allocated reservation (2 = 2-hour pickup window)'),
    'DUE_SOON_NOTIFY_DAYS': ('Due-soon reminder days', 'int', 'Days before due date to send due-soon reminders'),
    'BACKUP_DAY': ('Auto-backup day of month', 'int', 'Day of month for the automatic backup (1-28)'),
    'BACKUP_HOUR': ('Auto-backup hour (0-23)', 'int', 'Hour of day for the automatic backup'),
    'BACKUP_KEEP': ('Backups to retain', 'int', 'Newest backups kept; older ones are deleted'),
    'BACKUP_RESTORE_ENABLED': ('Allow backup restore', 'bool', 'When off, the Restore action on Backup & Recovery is disabled'),
}

# key -> (min, max) inclusive bounds; None means unbounded. Enforced on
# update — out-of-range values are rejected, never clamped silently.
SETTING_RANGES = {
    'BACKUP_DAY': (1, 28),
    'BACKUP_HOUR': (0, 23),
    'BACKUP_KEEP': (1, None),
}

DEFAULTS = {
    'MAX_BORROW_LIMIT_STUDENT': '3',
    'MAX_BORROW_LIMIT_FACULTY': '5',
    'LIBRARY_OPENING_TIME': '08:00',
    'LIBRARY_CLOSING_TIME': '17:00',
    'OVERNIGHT_DUE_DAYS_STUDENT': '1',
    'OVERNIGHT_DUE_DAYS_FACULTY': '7',
    'DAILY_CIRCULATION_DUE_DAYS': '0',
    'OVERDUE_FINE_PER_DAY': '5.0',
    'OVERDUE_GRACE_DAYS': '0',
    'RESERVATION_CLAIM_DAYS': '2',
    'RESERVATION_CLAIM_HOURS': '2',
    'DUE_SOON_NOTIFY_DAYS': '2',
    'BACKUP_DAY': _env_default('BACKUP_DAY', 1),
    'BACKUP_HOUR': _env_default('BACKUP_HOUR', 2),
    'BACKUP_KEEP': _env_default('BACKUP_KEEP', 12),
    'BACKUP_RESTORE_ENABLED': '1',
}


def get_all_settings():
    return db.fetch_all(
        'SELECT setting_key, setting_value, description, updated_at FROM library_settings ORDER BY setting_key'
    )


def get_settings_dict():
    try:
        rows = get_all_settings() or []
    except Exception:
        return {}
    data = dict(DEFAULTS)
    for row in rows:
        try:
            data[row[0]] = row[1]
        except (IndexError, TypeError):
            continue
    return data


def get_setting(key, default=None):
    row = db.fetch_one(
        'SELECT setting_value FROM library_settings WHERE setting_key = %s',
        (key,)
    )
    if row and row[0] is not None:
        return row[0]
    if default is not None:
        return default
    return DEFAULTS.get(key)


def is_restore_enabled():
    """Whether an admin may restore a backup.

    Reads BACKUP_RESTORE_ENABLED (default on). Only explicit off-values
    disable restore; anything else — including an unreadable settings
    table — preserves the historical behavior (restore allowed).
    """
    try:
        raw = get_setting('BACKUP_RESTORE_ENABLED', '1')
    except Exception:
        return True
    return str(raw).strip().lower() not in ('0', 'false', 'off', 'no')


def update_setting(key, value, updated_by=None):
    return db.execute(
        '''INSERT INTO library_settings (setting_key, setting_value, updated_at, updated_by)
           VALUES (%s, %s, NOW(), %s)
           ON CONFLICT (setting_key) DO UPDATE
           SET setting_value = EXCLUDED.setting_value,
               updated_at = NOW(),
               updated_by = EXCLUDED.updated_by''',
        (key, str(value), updated_by)
    )


def sync_settings_to_config(app=None):
    app = app or current_app
    try:
        data = get_settings_dict()
    except Exception:
        return
    for key, raw in data.items():
        kind = SETTING_DEFS.get(key, (key, 'int', ''))[1]
        try:
            if kind == 'bool':
                value = (1 if str(raw).strip().lower()
                         in ('1', 'true', 'on', 'yes') else 0)
            elif kind == 'time':
                value = str(raw).strip() if parse_hhmm(raw) else None
                if value is None:
                    continue
            else:
                value = float(raw) if kind == 'float' else int(float(raw))
        except (TypeError, ValueError):
            continue
        app.config[key] = value


def parse_hhmm(raw):
    """'HH:MM' 24-hour string as (hour, minute), or None when invalid."""
    match = re.fullmatch(r'([01]\d|2[0-3]):([0-5]\d)', (raw or '').strip())
    if not match:
        return None
    return (int(match.group(1)), int(match.group(2)))


def library_hours_from_config(config=None):
    """Configured (opening, closing) as ((h, m), (h, m)), or None.

    None means unrestricted: the keys are absent (e.g. tests, where
    settings sync is skipped) or fail validation. Borrowing must never
    be blocked by a missing or corrupt setting, so callers fail open.
    """
    cfg = config if config is not None else current_app.config
    opening = parse_hhmm(cfg.get('LIBRARY_OPENING_TIME') or '')
    closing = parse_hhmm(cfg.get('LIBRARY_CLOSING_TIME') or '')
    if opening is None or closing is None or not opening < closing:
        return None
    return (opening, closing)


def library_hours_label(config=None):
    """'08:00–17:00' for messages, or None when unrestricted."""
    hours = library_hours_from_config(config)
    if hours is None:
        return None
    (oh, om), (ch, cm) = hours
    return f'{oh:02d}:{om:02d}–{ch:02d}:{cm:02d}'


def is_library_open(now=None, config=None):
    """True when borrowing is allowed right now.

    Open boundary inclusive, closing exclusive (at exactly 17:00 the
    library is closed). Philippine wall-clock time, so a UTC-hosted
    server (e.g. Render) still gates on Manila hours. Unconfigured
    → True (fail open).
    """
    hours = library_hours_from_config(config)
    if hours is None:
        return True
    now = now or library_now()
    try:
        current = (now.hour, now.minute)
    except (AttributeError, TypeError):
        return True
    return hours[0] <= current < hours[1]


def get_closing_time(config=None):
    """(hour, minute) for due timestamps; (17, 0) when unconfigured.

    Closing alone is meaningful (unlike the open/close pair needed for
    the open-hours gate), so only the closing value is consulted.
    """
    cfg = config if config is not None else current_app.config
    parsed = parse_hhmm(cfg.get('LIBRARY_CLOSING_TIME') or '')
    return parsed or (17, 0)
