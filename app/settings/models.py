from flask import current_app
from app.database import db


# key -> (label, kind, description). Kinds: int, float.
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
            value = float(raw) if kind == 'float' else int(float(raw))
        except (TypeError, ValueError):
            continue
        app.config[key] = value
