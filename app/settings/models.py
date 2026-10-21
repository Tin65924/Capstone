from flask import current_app
from calendar import monthrange
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
    """Return the current wall-clock time in Philippine Time (Asia/Manila).

    Uses a fixed UTC+8 offset (no DST in the Philippines) instead of a
    tzdata zone, so Windows and Render hosts without zoneinfo data still
    gate correctly. Render servers run on UTC, so naive ``datetime.now``
    would read ~8 hours behind the library and wrongly block borrowing.

    Returns:
        Timezone-aware datetime stamped with the PHT fixed offset.
    """
    return datetime.now(PHT)


def library_today():
    """Return today's calendar date in Philippine Time.

    Derives from :func:`library_now` (not the server-local date), so a
    UTC-hosted request just after midnight Manila time still counts as
    the new day. Used for due-date math and same-day circulation rules
    that must follow the library wall clock.

    Returns:
        A date object for the current Manila calendar day.
    """
    return library_now().date()


def _env_default(name, fallback):
    """Resolve a string default honoring an environment override.

    Reads ``os.getenv(name)`` and coerces it through ``int`` so the
    ``BACKUP_*`` tunables (day/hour/keep) can be set per-deploy without
    code changes. A missing or non-numeric variable falls back to the
    provided default instead of raising at import time.

    Args:
        name: Environment variable name to read.
        fallback: Default value used when the variable is unset or
            unparseable.

    Returns:
        String form of the integer value (env value or fallback).
    """
    try:
        return str(int(os.getenv(name, fallback)))
    except (TypeError, ValueError):
        return str(fallback)


# Open-day controls: weekday checkboxes on Library Hours. Checked means
# the library is open that day; an unchecked day blocks all borrowing.
# Stored as a comma-joined string (e.g. 'Monday,Tuesday,...') so the
# settings table needs no schema change. Default is Mon–Sat, matching the
# historical 'Sunday,holiday' reservation closure.
WEEKDAYS = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
            'Saturday', 'Sunday')
DEFAULT_OPEN_DAYS = ('Monday,Tuesday,Wednesday,Thursday,Friday,Saturday')


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
     ['OVERNIGHT_DUE_DAYS_STUDENT', 'OVERNIGHT_DUE_DAYS_FACULTY']),
    ('fines', 'Fine Settings', 'payments',
     'Overdue fines and grace periods.',
     ['OVERDUE_FINE_PER_DAY', 'OVERDUE_GRACE_DAYS']),
    ('reservations', 'Reservation Settings', 'bookmark',
     'Pickup windows and due-date reminders. Reservations close claim hours before closing time; after cutoff pickup is next open day.',
     ['RESERVATION_CLAIM_HOURS', 'DUE_SOON_NOTIFY_DAYS']),
    ('operations', 'Library Operations Schedule', 'calendar_month',
     'Days the library is open. Unchecked days allow no borrowing and no reservations.',
     ['LIBRARY_OPEN_DAYS', 'LIBRARY_MONTH_DAYS']),
    ('collection', 'Collection Thresholds', 'inventory_2',
     'Low-stock alert threshold for reports.',
     ['LOW_STOCK_THRESHOLD']),
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
    'LIBRARY_OPEN_DAYS', 'LIBRARY_MONTH_DAYS',
    'OVERNIGHT_DUE_DAYS_STUDENT', 'OVERNIGHT_DUE_DAYS_FACULTY',
    'OVERDUE_FINE_PER_DAY', 'OVERDUE_GRACE_DAYS',
    'RESERVATION_CLAIM_HOURS',
    'DUE_SOON_NOTIFY_DAYS',
    'LOW_STOCK_THRESHOLD',
})


# key -> (label, kind, description). Kinds: int, float, bool, time, days, monthdays.
SETTING_DEFS = {
    'MAX_BORROW_LIMIT_STUDENT': ('Max borrows (Student)', 'int', 'Max active loans for students'),
    'MAX_BORROW_LIMIT_FACULTY': ('Max borrows (Faculty)', 'int', 'Max active loans for faculty'),
    'LIBRARY_OPENING_TIME': ('Opening hour', 'time', 'Daily opening hour (24-hour clock)'),
    'LIBRARY_CLOSING_TIME': ('Closing hour', 'time', 'Daily closing hour (must be after opening)'),
    'LIBRARY_OPEN_DAYS': ('Open days', 'days', 'Checked days are open — borrowing is blocked on unchecked days'),
    'LIBRARY_MONTH_DAYS': ('Open days in month', 'monthdays', 'Per-date overrides for the current month — a checked date is open even when its weekday is not'),
    'OVERNIGHT_DUE_DAYS_STUDENT': ('Overnight due days (Student)', 'int', 'Overnight loan due days for students'),
    'OVERNIGHT_DUE_DAYS_FACULTY': ('Overnight due days (Faculty)', 'int', 'Overnight loan due days for faculty'),
    'OVERDUE_FINE_PER_DAY': ('Overdue fine per day (₱)', 'float', 'Overdue fine in pesos per day'),
    'OVERDUE_GRACE_DAYS': ('Overdue grace days', 'int', 'Grace days before fines accrue'),
    'RESERVATION_CLAIM_HOURS': ('Reservation claim hours', 'float', 'Hours to claim an allocated reservation (2 = 2-hour pickup window)'),
    'LOW_STOCK_THRESHOLD': ('Low-stock threshold', 'int', 'Alert when available copies are at or below this (default 2)'),
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
    'LIBRARY_OPEN_DAYS': DEFAULT_OPEN_DAYS,
    'LIBRARY_MONTH_DAYS': '',
    'OVERNIGHT_DUE_DAYS_STUDENT': '1',
    'OVERNIGHT_DUE_DAYS_FACULTY': '7',
    'OVERDUE_FINE_PER_DAY': '5.0',
    'OVERDUE_GRACE_DAYS': '0',
    'RESERVATION_CLAIM_HOURS': '2',
    'LOW_STOCK_THRESHOLD': '2',
    'DUE_SOON_NOTIFY_DAYS': '2',
    'BACKUP_DAY': _env_default('BACKUP_DAY', 1),
    'BACKUP_HOUR': _env_default('BACKUP_HOUR', 2),
    'BACKUP_KEEP': _env_default('BACKUP_KEEP', 12),
    'BACKUP_RESTORE_ENABLED': '1',
}


def get_all_settings():
    """Fetch every stored library setting row ordered by key.

    Reads ``(setting_key, setting_value, description, updated_at)`` from
    ``library_settings`` in key order for the admin/librarian settings
    pages. Stored values are strings; callers coerce by kind via
    ``SETTING_DEFS``. Raises through to the route on DB failure so the
    page can flash a table-unavailable message.

    Returns:
        List of (setting_key, setting_value, description, updated_at)
        tuples, possibly empty.
    """
    return db.fetch_all(
        'SELECT setting_key, setting_value, description, updated_at FROM library_settings ORDER BY setting_key'
    )


def get_settings_dict():
    """Return effective settings as a key-value dict with defaults applied.

    Starts from a copy of ``DEFAULTS`` so every known key has a value
    even when the table is empty, then overlays stored rows on top.
    Malformed rows are skipped and a total read failure degrades to an
    empty dict (callers fall back to defaults/config). Never raises.

    Returns:
        Dict mapping setting_key to its string value, including
        defaults for keys with no stored row.
    """
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
    """Fetch one setting value with default fallback.

    Queries ``library_settings`` by exact key. A stored non-NULL value
    wins; otherwise the explicit ``default`` argument wins when given;
    otherwise the ``DEFAULTS`` entry for the key (or None for unknown
    keys). Used for single-key reads like the restore toggle where a
    full dict would be wasteful.

    Args:
        key: Setting key string (e.g. ``'BACKUP_KEEP'``).
        default: Explicit fallback when no row and no DEFAULTS entry
            should apply, or None to use DEFAULTS.

    Returns:
        The stored string value, the explicit default, the DEFAULTS
        entry, or None.
    """
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
    """Check whether an admin may restore a backup right now.

    Reads BACKUP_RESTORE_ENABLED (default on). Only explicit off-values
    disable restore; anything else — including an unreadable settings
    table — preserves the historical behavior (restore allowed). The
    fail-open choice keeps disaster recovery reachable even when the
    settings table itself is damaged.

    Args:
        None: Takes no arguments; reads the stored setting internally.

    Returns:
        True when restores are allowed, False only on an explicit
        off-like value (``0``/``false``/``off``/``no``).
    """
    try:
        raw = get_setting('BACKUP_RESTORE_ENABLED', '1')
    except Exception:
        return True
    return str(raw).strip().lower() not in ('0', 'false', 'off', 'no')


def update_setting(key, value, updated_by=None):
    """Upsert one library setting with audit stamps.

    Inserts the key/value row, or on key conflict overwrites the value
    and refreshes ``updated_at``/``updated_by``. Values are stored as
    strings (callers stringify ints/floats/times first); validation
    happens in the routes layer, not here.

    Args:
        key: Setting key string from SETTING_DEFS.
        value: New value to store (stringified by the caller).
        updated_by: Acting staff user_id for the audit stamp.

    Returns:
        Rowcount from the upsert.
    """
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
    """Copy stored library settings into the Flask config type-coerced.

    Reads the effective settings dict and writes each key into
    ``app.config`` by its declared kind: bools become 0/1, times stay
    ``HH:MM`` strings (skipped when invalid), day lists stay
    comma-joined strings and month maps stay ``YYYY-MM:bits`` strings,
    floats/ints are coerced
    numerically. Unparseable values are skipped, never raising, so one
    corrupt row cannot break app startup or a settings save. Borrowing,
    fines, and backup code then read plain ``current_app.config``.

    Args:
        app: Flask application to sync into, defaulting to
            ``current_app``.
    """
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
            elif kind == 'days':
                # Comma-joined weekday names stay a string (may be '' when
                # every day is unchecked — that means closed all week).
                value = str(raw or '').strip()
            elif kind == 'monthdays':
                # 'YYYY-MM:bits' per-date map stays a string ('' = no
                # overrides, weekly pattern applies to every date).
                value = str(raw or '').strip()
            else:
                value = float(raw) if kind == 'float' else int(float(raw))
        except (TypeError, ValueError):
            continue
        app.config[key] = value


def parse_hhmm(raw):
    """Parse an 'HH:MM' 24-hour string into an (hour, minute) tuple.

    Strictly validates with a full-match regex (``00:00``–``23:59``),
    so ``"8:00"``, ``"24:00"``, and ``"08:60"`` all fail. Used by the
    settings forms for opening/closing hours and by the open-hours gate
    before any borrowing is allowed.

    Args:
        raw: Candidate time string, possibly None or padded.

    Returns:
        Tuple (hour, minute) as ints, or None when invalid.
    """
    match = re.fullmatch(r'([01]\d|2[0-3]):([0-5]\d)', (raw or '').strip())
    if not match:
        return None
    return (int(match.group(1)), int(match.group(2)))


def library_hours_from_config(config=None):
    """Resolve the configured (opening, closing) pair, or None if open-all-day.

    Configured (opening, closing) as ((h, m), (h, m)), or None.
    None means unrestricted: the keys are absent (e.g. tests, where
    settings sync is skipped) or fail validation. Borrowing must never
    be blocked by a missing or corrupt setting, so callers fail open.
    Also requires opening < closing; an inverted pair (e.g. 17:00–08:00)
    is treated as unconfigured rather than a midnight-spanning schedule.

    Args:
        config: Optional config mapping to read from (defaults to
            ``current_app.config``).

    Returns:
        Tuple ((open_h, open_m), (close_h, close_m)) when both parse
        and opening precedes closing, else None.
    """
    cfg = config if config is not None else current_app.config
    opening = parse_hhmm(cfg.get('LIBRARY_OPENING_TIME') or '')
    closing = parse_hhmm(cfg.get('LIBRARY_CLOSING_TIME') or '')
    if opening is None or closing is None or not opening < closing:
        return None
    return (opening, closing)


def library_hours_label(config=None):
    """Format the configured hours as a display label, or None.

    Renders ``'08:00–17:00'`` (en dash) for flash messages and closed
    notices from :func:`library_hours_from_config`. Returns None when
    hours are unrestricted so callers can omit the label rather than
    show a misleading range.

    Args:
        config: Optional config mapping to read from (defaults to
            ``current_app.config``).

    Returns:
        Formatted hours string, or None when unrestricted.
    """
    hours = library_hours_from_config(config)
    if hours is None:
        return None
    (oh, om), (ch, cm) = hours
    return f'{oh:02d}:{om:02d}–{ch:02d}:{cm:02d}'


def _hhmm_ampm(pair):
    """Format an (hour, minute) pair as '5:00 PM' style wall-clock text."""
    hour, minute = pair
    meridiem = 'AM' if hour < 12 else 'PM'
    hour12 = hour % 12 or 12
    return f'{hour12}:{minute:02d} {meridiem}'


def next_open_day(after=None, config=None, max_days=14):
    """First day strictly after ``after`` whose date is open.

    Honors both LIBRARY_OPEN_DAYS and per-date month overrides (it walks
    :func:`is_open_day`). Returns None when nothing opens within
    ``max_days`` (e.g. every day unchecked) or when the input date is
    unusable.
    """
    day = after or library_today()
    try:
        day.strftime('%A')
    except Exception:
        return None
    for i in range(1, max_days + 1):
        candidate = day + timedelta(days=i)
        if is_open_day(candidate, config):
            return candidate
    return None


def library_open_status(config=None, now=None):
    """Public open/closed banner state for the landing page.

    Combines Library Hours (LIBRARY_OPENING_TIME/LIBRARY_CLOSING_TIME)
    with the Operations Schedule (LIBRARY_OPEN_DAYS + LIBRARY_MONTH_DAYS
    per-date overrides) into a display dict:

    ``{'open': bool, 'message': str, 'hours_label': str or None}``

    - open → "Open now" (+ " — closes at 5:00 PM" when hours configured)
    - closed day (unchecked weekday / override) → "Closed today — reopens
      {Weekday, Mon DD} at 8:00 AM"
    - open day before opening → "Closed — opens today at 8:00 AM"
    - open day after closing → "Closed — reopens {next open day} at ..."

    Fail-open semantics follow :func:`is_library_open`: with no hours
    configured, the library counts as always open ("No hour restrictions
    set"). Never raises; corrupt dates degrade to 'Open now'.

    Args:
        config: Optional config mapping (defaults to
            ``current_app.config``).
        now: Datetime to evaluate (defaults to :func:`library_now`).

    Returns:
        Display dict for templates as described above.
    """
    day = now or library_now()
    try:
        day.date().strftime('%A')
    except Exception:
        return {'open': True, 'message': 'Open now',
                'hours_label': 'No hour restrictions set'}
    today = day.date()
    hours = library_hours_from_config(config)
    hours_label = None
    if hours:
        hours_label = f'{_hhmm_ampm(hours[0])} – {_hhmm_ampm(hours[1])}'
    else:
        return {'open': True, 'message': 'Open now',
                'hours_label': 'No hour restrictions set'}
    if is_library_open(day, config):
        return {'open': True,
                'message': f'Open now — closes at {_hhmm_ampm(hours[1])}',
                'hours_label': hours_label}
    opening_label = _hhmm_ampm(hours[0])
    if not is_open_day(today, config):
        nxt = next_open_day(today, config)
        if nxt:
            return {'open': False,
                    'message': (f'Closed today — reopens '
                                f'{nxt.strftime("%A, %b %d")} at {opening_label}'),
                    'hours_label': hours_label}
        return {'open': False, 'message': 'Closed today',
                'hours_label': hours_label}
    current = (day.hour if isinstance(day, datetime) else None,
               day.minute if isinstance(day, datetime) else None)
    if None not in current and current < hours[0]:
        return {'open': False,
                'message': f'Closed — opens today at {opening_label}',
                'hours_label': hours_label}
    nxt = next_open_day(today, config)
    return {'open': False,
            'message': ('Closed — reopens ' +
                        (f'{nxt.strftime("%A, %b %d")} at {opening_label}'
                         if nxt else 'tomorrow')),
            'hours_label': hours_label}


def is_library_open(now=None, config=None):
    """Check whether borrowing is allowed at a given moment.

    True when borrowing is allowed right now. Open boundary inclusive,
    closing exclusive (at exactly 17:00 the library is closed). The day
    itself must also be checked in LIBRARY_OPEN_DAYS — an unchecked day
    blocks borrowing all day. Philippine wall-clock time, so a
    UTC-hosted server (e.g. Render) still gates on Manila hours.
    Unconfigured hours/days mean open (fail open), and a timestamp
    without clock fields also fails open rather than blocking
    circulation on bad input.

    Args:
        now: Datetime to test (defaults to :func:`library_now`).
        config: Optional config mapping for hours (defaults to
            ``current_app.config``).

    Returns:
        True when the library counts as open, False when closed.
    """
    hours = library_hours_from_config(config)
    if hours is None:
        return True
    now = now or library_now()
    try:
        current = (now.hour, now.minute)
    except (AttributeError, TypeError):
        return True
    if current < hours[0] or current >= hours[1]:
        return False
    try:
        day = now.date() if isinstance(now, datetime) else now
    except (AttributeError, TypeError):
        day = None
    return is_open_day(day, config)


def get_closing_time(config=None):
    """Resolve the closing time used for due-date timestamps.

    (hour, minute) for due timestamps; (17, 0) when unconfigured.
    Closing alone is meaningful (unlike the open/close pair needed for
    the open-hours gate), so only the closing value is consulted.
    Overnight loans stamp their due moment at this wall-clock time on
    the due date, keeping returns aligned with the desk schedule.

    Args:
        config: Optional config mapping to read from (defaults to
            ``current_app.config``).

    Returns:
        Tuple (hour, minute) of the configured close, or (17, 0).
    """
    cfg = config if config is not None else current_app.config
    parsed = parse_hhmm(cfg.get('LIBRARY_CLOSING_TIME') or '')
    return parsed or (17, 0)


def get_reservation_cutoff(config=None):
    """Daily reservation cutoff as (hour, minute), derived from hours.

    Closing time minus reservation claim hours: a 17:00 close with a
    2-hour claim window closes reservations at 15:00. Bookings at/after
    cutoff are served the next open day.
    """
    cfg = config if config is not None else current_app.config
    close = parse_hhmm(cfg.get('LIBRARY_CLOSING_TIME') or '') or (17, 0)
    try:
        claim_hours = float(cfg.get('RESERVATION_CLAIM_HOURS') or 2)
    except (TypeError, ValueError):
        claim_hours = 2.0
    total = close[0] * 60 + close[1] - max(0.0, claim_hours) * 60
    return max(0, int(total)) // 60, max(0, int(total)) % 60


def is_after_reservation_cutoff(now=None, config=None):
    """True when now is at/after the daily reservation cutoff (closing
    time minus the claim hours)."""
    now = now or library_now()
    cutoff = get_reservation_cutoff(config)
    try:
        return (now.hour, now.minute) >= cutoff
    except (AttributeError, TypeError):
        return False


def get_closed_days(config=None):
    """Closed weekday names (lowercase) derived from the open days.

    A weekday with its box unchecked counts as closed. Unconfigured
    open days mean no closures (fail open), matching the old behavior
    where an absent closed-days list closed nothing.
    """
    days = get_open_days(config)
    if days is None:
        return set()
    return {d.lower() for d in WEEKDAYS if d not in days}


def is_closed_day(day=None, config=None):
    """True for closed days — no reservations allowed.

    A date counts as closed exactly when borrowing is disallowed that
    day (unchecked weekday, or a per-date month override closing it),
    so reservation blocking always agrees with the Operations open-days
    grid. Callers pass the target pickup date so post-3PM next-day
    rollover can skip closed days.
    """
    day = day or library_today()
    try:
        day.strftime('%A')
    except Exception:
        return False
    return not is_open_day(day, config)


def get_open_days(config=None):
    """Open weekday names from LIBRARY_OPEN_DAYS, or None if unconfigured.

    Parses the comma-joined setting into canonical title-case names
    (``Monday``..``Sunday``); unknown tokens are dropped. Returns None
    when the key is absent (e.g. tests, unsynced config) so callers fail
    open — an explicitly stored empty string means every day is
    unchecked, i.e. an empty set (closed all week), not None.

    Args:
        config: Optional config mapping (defaults to
            ``current_app.config``).

    Returns:
        Set of weekday names, or None when unconfigured.
    """
    cfg = config if config is not None else current_app.config
    if 'LIBRARY_OPEN_DAYS' not in cfg:
        return None
    raw = str(cfg.get('LIBRARY_OPEN_DAYS') or '')
    return {p.strip().capitalize() for p in raw.replace(';', ',').split(',')
            if p.strip()}.intersection(WEEKDAYS)


def get_month_days(config=None):
    """Per-date open map from LIBRARY_MONTH_DAYS, or None.

    Parses the stored ``'YYYY-MM:bits'`` value (one ``0``/``1`` char per
    calendar date, ``1`` = open). Returns None when unconfigured, blank,
    malformed, or when the bit count disagrees with the real days in
    that month — callers then fall back to the weekly pattern. A stale
    month (not the date being tested) is not itself a failure: the
    caller only applies the map when its month matches.

    Args:
        config: Optional config mapping (defaults to
            ``current_app.config``).

    Returns:
        Tuple (ym, bits) with ym ``'YYYY-MM'``, or None.
    """
    cfg = config if config is not None else current_app.config
    raw = str(cfg.get('LIBRARY_MONTH_DAYS') or '').strip()
    if not raw:
        return None
    match = re.fullmatch(r'(\d{4}-(?:0[1-9]|1[0-2])):([01]{28,31})', raw)
    if not match:
        return None
    year, month = int(match.group(1)[:4]), int(match.group(1)[5:7])
    bits = match.group(2)
    if len(bits) != monthrange(year, month)[1]:
        return None
    return match.group(1), bits


def month_grid(year, month, config=None):
    """Effective open state for every date of a real calendar month.

    Returns [{n, weekday, iso, open}] with ``n`` the day of month,
    ``weekday`` the short name (Mon..Sun), ``iso`` the ``YYYY-MM-DD``
    form value, and ``open`` the effective state (per-date override
    wins, else the weekly pattern). Raises ValueError on an impossible
    month so form handlers fail loudly instead of rendering a wrong
    grid.

    Args:
        year: Four-digit year.
        month: Month 1-12.
        config: Optional config mapping (defaults to
            ``current_app.config``).

    Returns:
        List of per-date dicts in calendar order.
    """
    count = monthrange(year, month)[1]
    grid = []
    for day_num in range(1, count + 1):
        day = date(year, month, day_num)
        grid.append({
            'n': day_num,
            'weekday': day.strftime('%a'),
            'iso': day.isoformat(),
            'open': is_open_day(day, config),
        })
    return grid


def is_open_day(day=None, config=None):
    """True when the library is open on a given date.

    A stored per-date override for the date's month wins over the
    weekly pattern (so holidays can close an open weekday and special
    days can open a closed one); otherwise the weekday must be checked
    in LIBRARY_OPEN_DAYS. Unconfigured days fail open; corrupt values
    fail open too. Only an explicitly stored schedule gates.

    Args:
        day: Date to test (defaults to :func:`library_today`).
        config: Optional config mapping (defaults to
            ``current_app.config``).

    Returns:
        True when borrowing is allowed that day, False when closed.
    """
    day = day or library_today()
    try:
        ym = day.strftime('%Y-%m')
        idx = day.day - 1
        name = day.strftime('%A')
    except Exception:
        return True
    month_map = get_month_days(config)
    if month_map is not None and month_map[0] == ym:
        bits = month_map[1]
        if 0 <= idx < len(bits):
            return bits[idx] == '1'
    days = get_open_days(config)
    if days is None:
        return True
    return name in days


def get_low_stock_threshold(config=None):
    """Copies-at-or-below count that triggers low-stock alert (default 2)."""
    cfg = config if config is not None else current_app.config
    try:
        return max(0, int(float(cfg.get('LOW_STOCK_THRESHOLD', 2))))
    except (TypeError, ValueError):
        return 2
