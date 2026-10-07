from app.database import db
import re


# Canonical ID-number formats per role (strict):
#   Student   0000-00000  e.g. 2024-00123
#   Faculty   000000000  e.g. 123456789
#   Librarian LIB-00000  e.g. LIB-00123
#   Admin     1-10       e.g. 7
ID_NUMBER_PATTERNS = {
    'Student': re.compile(r'^\d{4}-\d{5}$'),
    'Faculty': re.compile(r'^\d{9}$'),
    'Librarian': re.compile(r'^LIB-\d{5}$'),
    'Admin': re.compile(r'^(10|[1-9])$'),
}

ID_NUMBER_EXAMPLES = {
    'Student': '2024-00123 (format: 0000-00000)',
    'Faculty': '123456789 (format: 000000000)',
    'Librarian': 'LIB-00123 (format: LIB-00000)',
    'Admin': '1-10 (e.g. 7)',
}

# Max input lengths per role (exact canonical lengths):
#   Student  0000-00000 = 10, Faculty 000000000 = 9,
#   Librarian LIB-00000 = 9, Admin 1-10 = 2.
ID_NUMBER_MAX_LENGTHS = {
    'Student': 10,
    'Faculty': 9,
    'Librarian': 9,
    'Admin': 2,
}


def normalize_id_number(id_number, role_name=None):
    """Strip whitespace; uppercase the LIB- prefix for librarians."""
    value = (id_number or '').strip()
    if role_name == 'Librarian' or value.upper().startswith('LIB-'):
        return value.upper()
    return value


def is_valid_id_number(id_number, role_name):
    """True when id_number matches the canonical format for role_name."""
    pattern = ID_NUMBER_PATTERNS.get(role_name)
    if not pattern:
        return False
    return bool(pattern.match(normalize_id_number(id_number, role_name)))


def get_user_by_id(user_id):
    return db.fetch_one(
        '''SELECT u.user_id, u.email, r.role_name, u.full_name
           FROM user_accounts u
           JOIN roles r ON u.role_id = r.role_id
           WHERE u.user_id = %s AND u.account_status = 'active' ''',
        (user_id,)
    )


def get_user_by_email(email):
    return db.fetch_one(
        '''SELECT u.user_id, u.email, r.role_name, u.full_name
           FROM user_accounts u
           JOIN roles r ON u.role_id = r.role_id
           WHERE u.email = %s''',
        (email,)
    )


def get_user_by_oauth_sub(oauth_sub):
    return db.fetch_one(
        '''SELECT u.user_id, u.email, r.role_name, u.full_name
           FROM user_accounts u
           JOIN roles r ON u.role_id = r.role_id
           WHERE u.oauth_sub = %s''',
        (oauth_sub,)
    )


def get_user_by_id_number(id_number):
    return db.fetch_one(
        '''SELECT u.user_id, u.email, r.role_name, u.full_name
           FROM user_accounts u
           JOIN borrowers b ON u.user_id = b.user_id
           JOIN roles r ON u.role_id = r.role_id
           WHERE b.id_number = %s''',
        (id_number,)
    )


def get_user_record(user_id):
    """One user row regardless of account status (for audit enrichment).

    Unlike get_user_by_id (active only): (user_id, email, role_name,
    full_name, account_status) or None when the user is gone.
    """
    return db.fetch_one(
        '''SELECT u.user_id, u.email, r.role_name, u.full_name, u.account_status
           FROM user_accounts u
           JOIN roles r ON u.role_id = r.role_id
           WHERE u.user_id = %s''',
        (user_id,)
    )


def audit_text(value, width=60):
    """One-line audit-safe text for embedding in an activity code.

    Collapses whitespace and strips colons (the code separator), then
    truncates — activity is VARCHAR(255) and presenters split on ':'.
    """
    text = ' '.join(str(value or '').split()).replace(':', ' ').strip()
    if len(text) > width:
        text = text[:width - 3] + '...'
    return text


def suggest_programs(prefix, limit=8):
    return db.fetch_all(
        "SELECT DISTINCT department FROM borrowers WHERE department IS NOT NULL "
        "AND department != '' AND department ILIKE %s ORDER BY department LIMIT %s",
        (f'{prefix}%', limit)
    )


def create_user(email, oauth_sub, full_name, role_id):
    row = db.fetch_one(
        '''INSERT INTO user_accounts (email, oauth_sub, full_name, role_id, account_status, created_at)
           VALUES (%s, %s, %s, %s, %s, NOW()) RETURNING user_id''',
        (email, oauth_sub, full_name, role_id, 'active')
    )
    return row[0] if row else None


def create_pending_user(email, oauth_sub, full_name, role_id):
    row = db.fetch_one(
        '''INSERT INTO user_accounts (email, oauth_sub, full_name, role_id, account_status, created_at)
           VALUES (%s, %s, %s, %s, %s, NOW()) RETURNING user_id''',
        (email, oauth_sub, full_name, role_id, 'pending')
    )
    return row[0] if row else None


def create_borrower(user_id, id_number, department=None):
    return db.execute(
        'INSERT INTO borrowers (user_id, id_number, department) VALUES (%s, %s, %s)',
        (user_id, id_number, department)
    )


def delete_signup_user(user_id):
    """Remove a just-created account when its borrower insert fails.

    Keeps a failed signup from leaving an orphan user row (no borrower):
    the borrower INSERT already rolled back, so only the user row remains.
    """
    return db.execute(
        'DELETE FROM user_accounts WHERE user_id = %s',
        (user_id,)
    )


def get_roles():
    return db.fetch_all('SELECT role_id, role_name FROM roles ORDER BY role_id')


def get_role_by_name(role_name):
    return db.fetch_one(
        'SELECT role_id, role_name FROM roles WHERE role_name = %s',
        (role_name,)
    )


def log_activity(user_id, activity, session_token=None):
    db.execute(
        'INSERT INTO audit_trail (user_id, activity, session_token) VALUES (%s, %s, %s)',
        (user_id, activity, session_token)
    )


def log_system_event(activity):
    """Record something the application did on its own (no actor).

    Stored with a NULL user_id so it surfaces under the System tab of
    the admin Audit Logs. Activity should be a short namespaced string,
    e.g. 'system:scheduled_backup:completed:<filename>'.
    """
    db.execute(
        'INSERT INTO audit_trail (user_id, activity, session_token) VALUES (%s, %s, %s)',
        (None, activity, None)
    )


def get_all_users():
    return db.fetch_all(
        '''SELECT u.user_id, u.email, u.full_name, r.role_name, u.account_status,
                  u.created_at, b.id_number, b.department
           FROM user_accounts u
           JOIN roles r ON u.role_id = r.role_id
           LEFT JOIN borrowers b ON u.user_id = b.user_id
           ORDER BY u.created_at DESC'''
    )


def get_pending_users():
    return db.fetch_all(
        '''SELECT u.user_id, u.email, u.full_name, r.role_name, u.created_at,
                  b.id_number, b.department
           FROM user_accounts u
           JOIN roles r ON u.role_id = r.role_id
           LEFT JOIN borrowers b ON u.user_id = b.user_id
           WHERE u.account_status = 'pending'
           ORDER BY u.created_at ASC'''
    )


def count_total_users():
    row = db.fetch_one('SELECT COUNT(*) FROM user_accounts')
    return row[0] if row else 0


def count_pending_users():
    row = db.fetch_one(
        "SELECT COUNT(*) FROM user_accounts WHERE account_status = 'pending'"
    )
    return row[0] if row else 0


def count_active_users_by_role():
    """Active user counts keyed by role name.

    Returns a list of (role_name, count) tuples.
    """
    return db.fetch_all(
        '''SELECT r.role_name, COUNT(*)
            FROM user_accounts u
            JOIN roles r ON u.role_id = r.role_id
            WHERE u.account_status = 'active'
            GROUP BY r.role_name'''
    )


# Audit trail contract:
#   (log_id, full_name, email, role_name, activity, log_timestamp)
#
# Tab filters are a fixed whitelist (never user input): the caller passes
# one of 'all', 'staff', 'members', 'system' and only the matching fragment
# is interpolated. Activity text always stays a bound %s parameter.
_TAB_FILTERS = {
    'staff': "r.role_name IN ('Admin', 'Librarian')",
    'members': "r.role_name IN ('Student', 'Faculty')",
    'system': "a.user_id IS NULL",
}

AUDIT_TABS = ('all', 'staff', 'members', 'system')

# Day-to-day operational noise stays out of the admin audit views —
# borrowing/returning (circulation:) and book requests (requests:) already
# have dedicated pages (user history, circulation, requests). The audit
# trail keeps governance and technical events only.
OPERATIONAL_PREFIXES = ('circulation:', 'requests:')


def get_audit_logs(limit=50, search=None, tab='all'):
    """Newest-first audit trail rows for the admin Audit Logs page.

    LIKE patterns travel as bound parameters, never inline: a literal %
    inside the SQL string breaks psycopg2 placeholder parsing.
    """
    clauses = ['(a.activity NOT LIKE %s AND a.activity NOT LIKE %s)']
    params = ['circulation:%', 'requests:%']
    if tab in _TAB_FILTERS:
        clauses.append(_TAB_FILTERS[tab])
    if search:
        clauses.append('a.activity ILIKE %s')
        params.append(f'%{search}%')
    where = f"WHERE {' AND '.join(clauses)}"
    params.append(limit)
    return db.fetch_all(
        f'''SELECT a.log_id, u.full_name, u.email, r.role_name,
                   a.activity, a.log_timestamp
            FROM audit_trail a
            LEFT JOIN user_accounts u ON a.user_id = u.user_id
            LEFT JOIN roles r ON u.role_id = r.role_id
            {where}
            ORDER BY a.log_timestamp DESC
            LIMIT %s''',
        tuple(params)
    )


def describe_activity(actor, activity):
    """Human sentence for an audit row, e.g. 'Staff1 edited book #42'.

    Pure presenter — the stored code is unchanged (still rendered small
    next to the sentence). Both legacy codes and newer enriched codes
    (with embedded names / before~>after detail) are understood;
    unknown codes fall back to the raw string.
    """
    import re
    who = actor or 'System'
    code = activity or ''

    m = re.match(r'^(approved_user|toggled_user_status|archived_user|'
                 r'unarchived_user|deleted_user|edited_user):(\d+)(?::(.+))?$',
                 code)
    if m:
        verbs = {'approved_user': 'approved',
                 'toggled_user_status': 'changed the status of',
                 'archived_user': 'archived',
                 'unarchived_user': 'restored',
                 'deleted_user': 'permanently deleted',
                 'edited_user': 'edited the details of'}
        target = m.group(3) or f'#{m.group(2)}'
        if m.group(3):
            target = f'{m.group(3)} (#{m.group(2)})'
        return f'{who} {verbs[m.group(1)]} user {target}'

    m = re.match(r'^changed_role:(\d+)_to_(\d+)(?::(.+))?$', code)
    if m:
        target = f'{m.group(3)} (#{m.group(1)})' if m.group(3) \
            else f'user #{m.group(1)}'
        return (f'{who} changed the role of {target} '
                f'(to role #{m.group(2)})')
    m = re.match(r'^changed_role:(\d+):(.+?)~>(.+?)(?::(.+))?$', code)
    if m:
        target = m.group(4) or f'#{m.group(1)}'
        if m.group(4):
            target = f'{m.group(4)} (#{m.group(1)})'
        return (f'{who} changed the role of user {target} '
                f'from {m.group(2)} to {m.group(3)}')

    m = re.match(r'^cataloging:edit_book:(\d+)(?::title:(.+)~>(.+))?$', code)
    if m:
        if m.group(2) is not None:
            return (f"{who} edited the title of book #{m.group(1)} "
                    f"from '{m.group(2)}' to '{m.group(3)}'")
        return f'{who} edited book #{m.group(1)}'
    m = re.match(r'^cataloging:(add_book|add_book_duplicate|add_copy|'
                 r'add_accession|delete_book|edit_accession|'
                 r'delete_accession)(?::(\d+))?$', code)
    if m:
        verbs = {'add_book': 'added a new book',
                 'add_book_duplicate': 'added a duplicate of book',
                 'add_copy': 'added a copy of book',
                 'add_accession': 'accessioned a copy of book',
                 'delete_book': 'deleted book',
                 'edit_accession': 'edited copy',
                 'delete_accession': 'deleted copy'}
        target = f' #{m.group(2)}' if m.group(2) else ''
        return f'{who} {verbs[m.group(1)]}{target}'
    m = re.match(r'^cataloging:toggle_status:(\d+):(.+)$', code)
    if m:
        verb = 'archived' if m.group(2) == 'archived' else 'activated'
        return f'{who} {verb} book #{m.group(1)}'
    m = re.match(r'^cataloging:bulk_import:(\d+)_success_(\d+)_errors$', code)
    if m:
        return (f'{who} bulk-imported {m.group(1)} book(s) '
                f'with {m.group(2)} error(s)')
    m = re.match(r'^cataloging:export_books:([^:]+):(\d+)$', code)
    if m:
        return f'{who} exported {m.group(2)} book(s) ({m.group(1)})'

    m = re.match(r'^users:export:([^:]+):(\d+)$', code)
    if m:
        return f'{who} exported {m.group(2)} user(s) ({m.group(1)})'
    m = re.match(r'^added_department:([^:]+):(.+)$', code)
    if m:
        return f'{who} added {m.group(1)} "{m.group(2)}"'
    m = re.match(r'^deleted_department:(\d+)$', code)
    if m:
        return f'{who} deleted department #{m.group(1)}'
    m = re.match(r'^department_status:(\d+):(active|inactive)$', code)
    if m:
        verb = 'activated' if m.group(2) == 'active' else 'deactivated'
        return f'{who} {verb} department #{m.group(1)}'

    m = re.match(r'^settings:update:(\d+)(?::(.+))?$', code)
    if m:
        keys = f" ({m.group(2)})" if m.group(2) else ''
        return f'{who} updated {m.group(1)} library setting(s){keys}'

    m = re.match(r'^backup:(created|restored|deleted):(.+)$', code)
    if m:
        verbs = {'created': 'created backup',
                 'restored': 'restored the database from',
                 'deleted': 'deleted backup'}
        return f'{who} {verbs[m.group(1)]} {m.group(2)}'
    if code == 'backup:failed:manual':
        return f"{who}'s manual backup failed"
    m = re.match(r'^backup:restore_(failed|aborted):(.+)$', code)
    if m:
        why = ('failed' if m.group(1) == 'failed'
               else 'was aborted (no safety snapshot)')
        return f"{who}'s restore from {m.group(2)} {why}"

    if code in ('login',):
        return f'{who} signed in'
    if code == 'first_login':
        return f'{who} signed in for the first time'
    if code == 'logout':
        return f'{who} signed out'
    if code == 'profile:update':
        return f'{who} updated their profile'
    m = re.match(r'^notifications:read:(\d+)$', code)
    if m:
        return f'{who} read notification #{m.group(1)}'
    if code == 'notifications:read_all':
        return f'{who} marked all notifications as read'

    m = re.match(r'^inventory:(start_session|complete_session|'
                 r'cancel_session|export_session):(\d+)$', code)
    if m:
        verbs = {'start_session': 'started inventory session',
                 'complete_session': 'completed inventory session',
                 'cancel_session': 'cancelled inventory session',
                 'export_session': 'exported inventory session'}
        return f'{who} {verbs[m.group(1)]} #{m.group(2)}'
    m = re.match(r'^inventory:(scan|mark_damaged|mark_lost):(\d+)$', code)
    if m:
        verbs = {'scan': 'scanned copy',
                 'mark_damaged': 'marked copy',
                 'mark_lost': 'marked copy'}
        suffix = {'scan': '', 'mark_damaged': ' as damaged',
                  'mark_lost': ' as lost'}[m.group(1)]
        return f'{who} {verbs[m.group(1)]} #{m.group(2)}{suffix}'
    m = re.match(r'^procurement:update_status:(\d+)$', code)
    if m:
        return f'{who} updated procurement request #{m.group(1)}'
    m = re.match(r'^circulation:([^:]+):(\d+)$', code)
    if m:
        verbs = {'borrow': 'borrowed copy', 'return': 'returned loan',
                 'allocate_reservation': 'allocated reservation',
                 'claim_reservation': 'claimed reservation',
                 'expire_reservation': 'expired reservation',
                 'user_borrow_request': 'requested book',
                 'user_borrow': 'borrowed book', 'user_reserve': 'reserved book',
                 'user_return': 'returned loan', 'fine_paid': 'paid fine',
                 'mark_lost': 'marked copy', 'mark_damaged': 'marked copy'}
        verb = verbs.get(m.group(1), m.group(1).replace('_', ' '))
        suffix = {'mark_lost': ' as lost',
                  'mark_damaged': ' as damaged'}.get(m.group(1), '')
        return f'{who} {verb} #{m.group(2)}{suffix}'
    m = re.match(r'^requests:([^:]+):(\d+)$', code)
    if m:
        return f'{who} {m.group(1).replace("_", " ")} request #{m.group(2)}'

    m = re.match(r'^system:login_failed:(.+)$', code)
    if m:
        reasons = {'initiate': 'could not reach Google',
                   'invalid_state': 'invalid session state',
                   'token_exchange': 'identity provider error',
                   'no_id_token': 'missing identity token',
                   'verify': 'token verification failed',
                   'issuer': 'untrusted token issuer',
                   'email': 'no email address provided',
                   'domain': 'non-library email domain'}
        why = reasons.get(m.group(1), m.group(1).replace('_', ' '))
        return f'A sign-in attempt failed ({why})'
    m = re.match(r'^system:scheduled_backup:completed:(.+)$', code)
    if m:
        return f'Scheduled backup completed ({m.group(1)})'
    if code == 'system:scheduled_backup:failed':
        return 'Scheduled backup failed'
    m = re.match(r'^system:error:500:(.+)$', code)
    if m:
        return f'Server error (500) on {m.group(1)}'
    m = re.match(r'^system:auth_required:(.+)$', code)
    if m:
        return f'Someone tried to open {m.group(1)} without signing in'
    m = re.match(r'^security:denied:(.+)$', code)
    if m:
        return f'{who} was denied access to {m.group(1)}'

    return code


# Audit analytics: window + cap for the dashboard aggregation below.
AUDIT_STATS_DAYS = 30
AUDIT_STATS_MAX_ROWS = 2000
AUDIT_STATS_DAILY_DAYS = 14

LOGIN_ACTIVITIES = ('login', 'first_login')


def _activity_category(code):
    """Bucket an activity code for the category donut."""
    c = code or ''
    if c in LOGIN_ACTIVITIES:
        return 'Sign-ins'
    if c == 'logout':
        return 'Sign-outs'
    if c.startswith('system:login_failed:'):
        return 'Failed sign-ins'
    if c.startswith('system:error:500:'):
        return 'Server errors'
    if c.startswith('system:auth_required:'):
        return 'Sign-in prompts'
    if c.startswith('security:denied:'):
        return 'Access denials'
    if c.startswith('system:scheduled_backup:'):
        return 'Scheduled backups'
    if c.startswith('backup:'):
        return 'Backups'
    if c.startswith('cataloging:'):
        return 'Cataloging'
    if c.startswith('settings:'):
        return 'Settings'
    if c.startswith('inventory:'):
        return 'Inventory'
    if c.startswith('procurement:'):
        return 'Procurement'
    if c.startswith(('profile:', 'notifications:')):
        return 'Profile & notifications'
    if c.startswith(('approved_user:', 'toggled_user_status:',
                     'archived_user:', 'unarchived_user:', 'deleted_user:',
                      'edited_user:', 'changed_role:', 'added_department:',
                      'deleted_department:', 'department_status:', 'users:export:')):
        return 'User management'
    return 'Other'


def _as_date(value):
    """Best-effort date from a datetime or DB string; None if unparseable."""
    from datetime import date
    try:
        if hasattr(value, 'date'):
            return value.date()
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def _sortable_ts(value):
    """Naive datetime for ordering mixed date/datetime/string stamps.

    Raw log_timestamp values are naive datetimes in practice, but a mix
    of dates, datetimes, and strings would crash every comparison, so
    normalize once and compare only normalized values.
    """
    from datetime import date, datetime
    try:
        if isinstance(value, datetime):
            return value.replace(tzinfo=None)
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time())
        return datetime.fromisoformat(str(value)[:19])
    except (TypeError, ValueError):
        return None


def get_audit_stats(days=AUDIT_STATS_DAYS, limit=AUDIT_STATS_MAX_ROWS,
                    today=None):
    """Aggregate login/error/category/role stats for the Audit Logs page.

    One bounded query (same operational exclusions as get_audit_logs),
    everything else in Python. All values JSON-serializable for tojson.
    `today` is injectable for tests.
    """
    from collections import Counter
    from datetime import date, datetime, timedelta
    today = today or date.today()
    cutoff = datetime.combine(today - timedelta(days=days - 1),
                              datetime.min.time())
    rows = db.fetch_all(
        '''SELECT a.activity, a.log_timestamp, a.user_id, u.full_name,
                  r.role_name
           FROM audit_trail a
           LEFT JOIN user_accounts u ON a.user_id = u.user_id
           LEFT JOIN roles r ON u.role_id = r.role_id
           WHERE a.log_timestamp >= %s
             AND a.activity NOT LIKE %s AND a.activity NOT LIKE %s
           ORDER BY a.log_timestamp DESC
           LIMIT %s''',
        (cutoff, 'circulation:%', 'requests:%', limit)
    ) or []

    day_list = [today - timedelta(days=i)
                for i in reversed(range(AUDIT_STATS_DAILY_DAYS))]
    day_index = {d: i for i, d in enumerate(day_list)}
    logins_per_day = [0] * len(day_list)
    errors_per_day = [0] * len(day_list)
    logins_today = 0
    logins_7d = 0
    failed_logins = 0
    denials = 0
    server_errors = 0
    categories = Counter()
    logins_by_role = Counter()
    error_paths = Counter()
    # uid -> [last_login, last_logout, name, role]
    sessions = {}

    for row in rows:
        try:
            activity, ts, uid, name, role = row[0], row[1], row[2], row[3], row[4]
        except (IndexError, TypeError):
            continue
        day = _as_date(ts)
        sts = _sortable_ts(ts)
        code = activity if isinstance(activity, str) else ''
        categories[_activity_category(code)] += 1
        if code in LOGIN_ACTIVITIES:
            logins_by_role[role or 'Unknown'] += 1
            if day is not None:
                if day in day_index:
                    logins_per_day[day_index[day]] += 1
                if day == today:
                    logins_today += 1
                if (today - day).days < 7:
                    logins_7d += 1
            if uid is not None:
                slot = sessions.setdefault(uid, [None, None, name, role])
                slot[2] = slot[2] or name
                slot[3] = slot[3] or role
                if sts is not None and (slot[0] is None or sts > slot[0]):
                    slot[0] = sts
        elif code == 'logout' and uid is not None:
            slot = sessions.setdefault(uid, [None, None, name, role])
            if slot[1] is None or (sts is not None and sts > slot[1]):
                slot[1] = sts if sts is not None else slot[1]
        if code.startswith('system:login_failed:'):
            failed_logins += 1
            if day in day_index:
                errors_per_day[day_index[day]] += 1
        elif code.startswith('system:error:500:'):
            server_errors += 1
            parts = code.split(':', 3)
            error_paths[parts[3] if len(parts) > 3 else code] += 1
            if day in day_index:
                errors_per_day[day_index[day]] += 1
        elif code.startswith('security:denied:'):
            denials += 1

    active = [(uid, s[2], s[3], s[0]) for uid, s in sessions.items()
              if s[0] is not None and (s[1] is None or s[0] > s[1])]
    active.sort(key=lambda t: t[3], reverse=True)
    active_users = [[(n or 'Someone'), (r or 'Unknown')] for _, n, r, _ in active[:5]]

    labels = [d.strftime('%b %d') for d in day_list]
    return {
        'window_days': days,
        'total_events': len(rows),
        'logins_today': logins_today,
        'logins_7d': logins_7d,
        'active_now': len(active),
        'active_users': active_users,
        'failed_logins': failed_logins,
        'denials': denials,
        'server_errors': server_errors,
        'logins_per_day': [[labels[i], logins_per_day[i]]
                           for i in range(len(day_list))],
        'errors_per_day': [[labels[i], errors_per_day[i]]
                           for i in range(len(day_list))],
        'by_category': [[label, count]
                        for label, count in categories.most_common(8)],
        'logins_by_role': sorted(logins_by_role.items()),
        'top_error_paths': [[path, count]
                            for path, count in error_paths.most_common(5)],
    }


def approve_user(user_id, updated_by=None):
    db.execute(
        'UPDATE user_accounts SET account_status = %s, updated_at = NOW(), updated_by = %s WHERE user_id = %s',
        ('active', updated_by, user_id)
    )


def update_user_role(user_id, role_id, updated_by=None):
    db.execute(
        'UPDATE user_accounts SET role_id = %s, updated_at = NOW(), updated_by = %s WHERE user_id = %s',
        (role_id, updated_by, user_id)
    )


def update_user_details(user_id, full_name, id_number, department, updated_by=None):
    db.execute(
        'UPDATE user_accounts SET full_name = %s, updated_at = NOW(), updated_by = %s WHERE user_id = %s',
        (full_name, updated_by, user_id)
    )
    db.execute(
        'UPDATE borrowers SET id_number = %s, department = %s, updated_at = NOW(), updated_by = %s WHERE user_id = %s',
        (id_number, department, updated_by, user_id)
    )


def toggle_user_status(user_id, updated_by=None):
    cur = db.fetch_one(
        'SELECT account_status FROM user_accounts WHERE user_id = %s',
        (user_id,)
    )
    if cur:
        if cur[0] == 'active':
            new_status = 'disabled'
        elif cur[0] == 'disabled':
            new_status = 'active'
        else:
            return
        db.execute(
            'UPDATE user_accounts SET account_status = %s, updated_at = NOW(), updated_by = %s WHERE user_id = %s',
            (new_status, updated_by, user_id)
        )


def delete_user(user_id):
    """Permanently remove an archived account without tripping FKs.

    Plain ``DELETE FROM user_accounts`` 500s on any real account because
    dependent rows reference it: ``borrowers.user_id`` (every member has
    one), ``audit_trail.user_id``, ``user_favorites.user_id``, plus every
    nullable ``updated_by``/``checked_by``/``reviewed_by``/``generated_by``
    column. Those are safe to NULL/cascade away.

    Business history that must survive (active loans, live reservations,
    pending requests, staff action history on NOT NULL columns) is NOT
    deleted here — check :func:`get_user_deletion_blocker` first; the
    route refuses with a friendly message instead of hitting a FK
    violation (500).
    """
    borrower = db.fetch_one(
        'SELECT borrower_id FROM borrowers WHERE user_id = %s',
        (user_id,)
    )
    borrower_id = borrower[0] if borrower else None
    if borrower_id is not None:
        db.execute(
            'DELETE FROM notification_log WHERE recipient_id = %s',
            (borrower_id,)
        )
        # Active waiting/allocated reservations are blocked by the
        # pre-check; whatever remains here is terminal and safe to clear.
        db.execute(
            'DELETE FROM reservation_queue WHERE borrower_id = %s',
            (borrower_id,)
        )
        req_rows = db.fetch_all(
            'SELECT request_id FROM request_records WHERE requester_id = %s',
            (borrower_id,)
        ) or []
        for req in req_rows:
            try:
                request_id = req[0]
            except (IndexError, TypeError):
                continue
            db.execute(
                'DELETE FROM procurement_log WHERE request_id = %s',
                (request_id,)
            )
        db.execute(
            'DELETE FROM request_records WHERE requester_id = %s',
            (borrower_id,)
        )
        # Active/overdue loans are blocked by the pre-check; remaining
        # returned rows are cleared so the borrower row can go.
        db.execute(
            'DELETE FROM circulation_records WHERE borrower_id = %s',
            (borrower_id,)
        )
    db.execute('DELETE FROM user_favorites WHERE user_id = %s', (user_id,))
    # Keep the audit history row, just detach the deleted actor.
    db.execute('UPDATE audit_trail SET user_id = NULL WHERE user_id = %s', (user_id,))
    for _table, _column in _NULLABLE_USER_REFS:
        db.execute(
            f'UPDATE {_table} SET {_column} = NULL WHERE {_column} = %s',
            (user_id,)
        )
    db.execute('DELETE FROM borrowers WHERE user_id = %s', (user_id,))
    db.execute('DELETE FROM user_accounts WHERE user_id = %s', (user_id,))


# Every nullable FK column pointing at user_accounts(user_id). Table and
# column names come from this hardcoded list only (never user input), so
# interpolating them is safe — values stay bound %s parameters.
_NULLABLE_USER_REFS = (
    ('user_accounts', 'updated_by'),
    ('borrowers', 'updated_by'),
    ('book_catalog', 'updated_by'),
    ('accession_log', 'updated_by'),
    ('request_records', 'reviewed_by'),
    ('request_records', 'updated_by'),
    ('procurement_log', 'updated_by'),
    ('circulation_records', 'updated_by'),
    ('inventory_status', 'checked_by'),
    ('inventory_sessions', 'updated_by'),
    ('reservation_queue', 'updated_by'),
    ('notification_log', 'updated_by'),
    ('analytics_cache', 'generated_by'),
    ('library_settings', 'updated_by'),
)


def get_account_status(user_id):
    """Raw account_status for archive-before-delete enforcement."""
    return db.fetch_one(
        'SELECT account_status FROM user_accounts WHERE user_id = %s',
        (user_id,)
    )


def get_user_deletion_blocker(user_id):
    """Human-readable reason an archived account cannot be deleted yet.

    Returns e.g. 'active loans' when history on a NOT NULL FK (or live
    operational state) would make the DELETE fail — the route turns this
    into a flash message instead of a 500. Returns None when the account
    is safe for :func:`delete_user` to cascade-clean.

    Existence checks use fetch_all (empty == clear) so the contrived
    single-tuple fetch_one mocks in the test-suite never read as blockers.
    """
    borrower = db.fetch_one(
        'SELECT borrower_id FROM borrowers WHERE user_id = %s',
        (user_id,)
    )
    borrower_id = borrower[0] if borrower else None
    if borrower_id is not None:
        rows = db.fetch_all(
            "SELECT 1 FROM circulation_records WHERE borrower_id = %s "
            "AND transaction_status IN ('active', 'overdue') LIMIT 1",
            (borrower_id,)
        ) or []
        if rows:
            return 'active loans'
        rows = db.fetch_all(
            "SELECT 1 FROM reservation_queue WHERE borrower_id = %s "
            "AND reservation_status IN ('waiting', 'allocated') LIMIT 1",
            (borrower_id,)
        ) or []
        if rows:
            return 'active reservations'
        rows = db.fetch_all(
            "SELECT 1 FROM request_records WHERE requester_id = %s "
            "AND request_status IN ('pending_review', 'approved') LIMIT 1",
            (borrower_id,)
        ) or []
        if rows:
            return 'pending book requests'
    # Staff action history lives on NOT NULL columns that cannot be
    # nulled — deleting would orphan catalog/circulation rows.
    for _table, _column in (
        ('accession_log', 'librarian_id'),
        ('circulation_records', 'processed_by'),
        ('inventory_sessions', 'librarian_id'),
    ):
        rows = db.fetch_all(
            f'SELECT 1 FROM {_table} WHERE {_column} = %s LIMIT 1',
            (user_id,)
        ) or []
        if rows:
            return 'staff action history'
    return None


def archive_user(user_id, updated_by=None):
    db.execute(
        'UPDATE user_accounts SET account_status = %s, updated_at = NOW(), updated_by = %s WHERE user_id = %s',
        ('archived', updated_by, user_id)
    )


def unarchive_user(user_id, updated_by=None):
    db.execute(
        'UPDATE user_accounts SET account_status = %s, updated_at = NOW(), updated_by = %s WHERE user_id = %s',
        ('active', updated_by, user_id)
    )


def get_admin_count():
    row = db.fetch_one(
        '''SELECT COUNT(*) FROM user_accounts u
           JOIN roles r ON u.role_id = r.role_id
           WHERE r.role_name = 'Admin' AND u.account_status = 'active' '''
    )
    return row[0] if row else 0


def get_profile_by_user(user_id):
    """Full self-service profile: user + borrower details incl. phone.

    Returns (user_id, email, role_name, full_name, borrower_id, id_number,
             department, phone_number, borrower_status) or None.
    """
    return db.fetch_one(
        '''SELECT u.user_id, u.email, r.role_name, u.full_name,
                  b.borrower_id, b.id_number, b.department, b.phone_number, b.borrower_status
           FROM user_accounts u
           JOIN roles r ON u.role_id = r.role_id
           LEFT JOIN borrowers b ON u.user_id = b.user_id
           WHERE u.user_id = %s''',
        (user_id,)
    )


def update_own_profile(user_id, full_name, phone_number=None, department=None):
    """Update editable self-service fields. Never touches id_number.

    Best-effort atomicity on the non-transactional db helper: the old
    name is re-applied if the borrower update fails, so a midway DB
    failure cannot leave name updated with phone/department stale.
    """
    old = db.fetch_one(
        'SELECT full_name FROM user_accounts WHERE user_id = %s',
        (user_id,)
    )
    old_name = old[0] if old else None
    db.execute(
        'UPDATE user_accounts SET full_name = %s, updated_at = NOW(), updated_by = %s WHERE user_id = %s',
        (full_name, user_id, user_id)
    )
    try:
        db.execute(
            'UPDATE borrowers SET phone_number = %s, department = %s, updated_at = NOW(), updated_by = %s WHERE user_id = %s',
            (phone_number, department, user_id, user_id)
        )
    except Exception:
        if old_name is not None:
            try:
                db.execute(
                    'UPDATE user_accounts SET full_name = %s, updated_at = NOW(), updated_by = %s WHERE user_id = %s',
                    (old_name, user_id, user_id)
                )
            except Exception:
                pass
        raise


DEPT_TYPES = ('program', 'department')

DEPT_STATUSES = ('active', 'inactive')


def _dept_status(row):
    """Status at index 3 when present; legacy 3-tuple rows count as active."""
    try:
        return row[3] if len(row) > 3 and row[3] else 'active'
    except (IndexError, TypeError):
        return 'active'


def get_departments(dept_type=None, include_inactive=False):
    """Controlled-vocabulary entries as (department_id, name, dept_type, status).

    Default returns active entries only — every registration/profile
    dropdown and option list must never show inactive values. Pass
    include_inactive=True for the management listing so librarians can
    see and reactivate inactive entries.
    """
    status_filter = '' if include_inactive else " AND status = 'active'"
    if dept_type:
        return db.fetch_all(
            'SELECT department_id, name, dept_type, status FROM departments '
            'WHERE dept_type = %s' + status_filter + ' ORDER BY name',
            (dept_type,)
        )
    return db.fetch_all(
        'SELECT department_id, name, dept_type, status FROM departments '
        'WHERE 1 = 1' + status_filter + ' '
        'ORDER BY dept_type, name'
    )


def get_active_departments(dept_type=None):
    """Active entries only (registration/profile/edit options)."""
    return get_departments(dept_type, include_inactive=False)


def is_valid_department(name, dept_type):
    row = db.fetch_one(
        "SELECT 1 FROM departments WHERE name = %s AND dept_type = %s AND status = 'active'",
        (name, dept_type)
    )
    return row is not None


def is_valid_any_department(name):
    """Staff (Admin/Librarian) may hold either a program or a department."""
    row = db.fetch_one(
        "SELECT 1 FROM departments WHERE name = %s AND status = 'active'",
        (name,)
    )
    return row is not None


def create_department(name, dept_type):
    return db.execute(
        'INSERT INTO departments (name, dept_type) VALUES (%s, %s) ON CONFLICT DO NOTHING',
        (name, dept_type)
    )


def get_department_by_id(department_id):
    return db.fetch_one(
        'SELECT department_id, name, dept_type, status FROM departments WHERE department_id = %s',
        (department_id,)
    )


def get_department_by_name(name):
    """Single vocab entry by exact name (for JSON add responses)."""
    return db.fetch_one(
        'SELECT department_id, name, dept_type, status FROM departments WHERE name = %s',
        (name,)
    )


def update_department_status(department_id, status):
    """Switch a program/department between active and inactive."""
    return db.execute(
        'UPDATE departments SET status = %s WHERE department_id = %s',
        (status, department_id)
    )


def count_borrowers_in_department(name, dept_type=None):
    """Borrowers actually bound to a vocab entry.

    Programs are only selectable by Students and departments only by
    Faculty, so a same-named value on the other side (e.g. a student
    program "BA Communication" vs the faculty department of the same
    name) must not block deletion. Unscoped (dept_type=None) keeps the
    legacy all-borrower count.
    """
    if dept_type == 'program':
        row = db.fetch_one(
            'SELECT COUNT(*) FROM borrowers b '
            'JOIN user_accounts u ON u.user_id = b.user_id '
            'JOIN roles r ON r.role_id = u.role_id '
            "WHERE b.department = %s AND r.role_name = 'Student'",
            (name,)
        )
    elif dept_type == 'department':
        row = db.fetch_one(
            'SELECT COUNT(*) FROM borrowers b '
            'JOIN user_accounts u ON u.user_id = b.user_id '
            'JOIN roles r ON r.role_id = u.role_id '
            "WHERE b.department = %s AND r.role_name = 'Faculty'",
            (name,)
        )
    else:
        row = db.fetch_one(
            'SELECT COUNT(*) FROM borrowers WHERE department = %s',
            (name,)
        )
    return row[0] if row else 0


def delete_department(department_id):
    db.execute('DELETE FROM departments WHERE department_id = %s', (department_id,))