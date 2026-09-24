from flask import current_app
from app.database import db
import os


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
    ('due-dates', 'Due Date Settings', 'event',
     'Loan periods for overnight and in-library use.',
     ['OVERNIGHT_DUE_DAYS_STUDENT', 'OVERNIGHT_DUE_DAYS_FACULTY',
      'DAILY_CIRCULATION_DUE_DAYS']),
    ('fines', 'Fine Settings', 'payments',
     'Overdue fines and grace periods.',
     ['OVERDUE_FINE_PER_DAY', 'OVERDUE_GRACE_DAYS']),
    ('reservations', 'Reservation Settings', 'bookmark',
     'Pickup windows and due-date reminders.',
     ['RESERVATION_CLAIM_DAYS', 'DUE_SOON_NOTIFY_DAYS']),
    ('backup-schedule', 'Backup Schedule', 'settings_backup_restore',
     'Automatic monthly backups and retention. Admin only.',
     ['BACKUP_DAY', 'BACKUP_HOUR', 'BACKUP_KEEP', 'BACKUP_RESTORE_ENABLED']),
]


# Keys only admins may view or edit. Librarians get the circulation
# categories; admins get exactly these.
ADMIN_ONLY_KEYS = frozenset({'BACKUP_DAY', 'BACKUP_HOUR', 'BACKUP_KEEP',
                             'BACKUP_RESTORE_ENABLED'})


# key -> (label, kind, description). Kinds: int, float, bool.
SETTING_DEFS = {
    'MAX_BORROW_LIMIT_STUDENT': ('Max borrows (Student)', 'int', 'Max active loans for students'),
    'MAX_BORROW_LIMIT_FACULTY': ('Max borrows (Faculty)', 'int', 'Max active loans for faculty'),
    'OVERNIGHT_DUE_DAYS_STUDENT': ('Overnight due days (Student)', 'int', 'Overnight loan due days for students'),
    'OVERNIGHT_DUE_DAYS_FACULTY': ('Overnight due days (Faculty)', 'int', 'Overnight loan due days for faculty'),
    'DAILY_CIRCULATION_DUE_DAYS': ('Daily circulation due days', 'int', 'Daily circulation due days (0 = same day)'),
    'OVERDUE_FINE_PER_DAY': ('Overdue fine per day (₱)', 'float', 'Overdue fine in pesos per day'),
    'OVERDUE_GRACE_DAYS': ('Overdue grace days', 'int', 'Grace days before fines accrue'),
    'RESERVATION_CLAIM_DAYS': ('Reservation claim days', 'int', 'Days to claim an allocated reservation'),
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
    'OVERNIGHT_DUE_DAYS_STUDENT': '2',
    'OVERNIGHT_DUE_DAYS_FACULTY': '30',
    'DAILY_CIRCULATION_DUE_DAYS': '0',
    'OVERDUE_FINE_PER_DAY': '5.0',
    'OVERDUE_GRACE_DAYS': '0',
    'RESERVATION_CLAIM_DAYS': '2',
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
            else:
                value = float(raw) if kind == 'float' else int(float(raw))
        except (TypeError, ValueError):
            continue
        app.config[key] = value
