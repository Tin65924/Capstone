from app.database import db


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


def approve_user(user_id):
    db.execute(
        'UPDATE user_accounts SET account_status = %s WHERE user_id = %s',
        ('active', user_id)
    )


def update_user_role(user_id, role_id):
    db.execute(
        'UPDATE user_accounts SET role_id = %s WHERE user_id = %s',
        (role_id, user_id)
    )


def update_user_details(user_id, full_name, id_number, department):
    db.execute(
        'UPDATE user_accounts SET full_name = %s WHERE user_id = %s',
        (full_name, user_id)
    )
    db.execute(
        'UPDATE borrowers SET id_number = %s, department = %s WHERE user_id = %s',
        (id_number, department, user_id)
    )


def toggle_user_status(user_id):
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
            'UPDATE user_accounts SET account_status = %s WHERE user_id = %s',
            (new_status, user_id)
        )


def delete_user(user_id):
    db.execute('DELETE FROM user_accounts WHERE user_id = %s', (user_id,))


def archive_user(user_id):
    db.execute(
        'UPDATE user_accounts SET account_status = %s WHERE user_id = %s',
        ('archived', user_id)
    )


def unarchive_user(user_id):
    db.execute(
        'UPDATE user_accounts SET account_status = %s WHERE user_id = %s',
        ('active', user_id)
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
    """Update editable self-service fields. Never touches id_number."""
    db.execute(
        'UPDATE user_accounts SET full_name = %s WHERE user_id = %s',
        (full_name, user_id)
    )
    db.execute(
        'UPDATE borrowers SET phone_number = %s, department = %s WHERE user_id = %s',
        (phone_number, department, user_id)
    )


DEPT_TYPES = ('program', 'department')


def get_departments(dept_type=None):
    """Controlled-vocabulary entries as (department_id, name, dept_type)."""
    if dept_type:
        return db.fetch_all(
            'SELECT department_id, name, dept_type FROM departments '
            'WHERE dept_type = %s ORDER BY name',
            (dept_type,)
        )
    return db.fetch_all(
        'SELECT department_id, name, dept_type FROM departments '
        'ORDER BY dept_type, name'
    )


def is_valid_department(name, dept_type):
    row = db.fetch_one(
        'SELECT 1 FROM departments WHERE name = %s AND dept_type = %s',
        (name, dept_type)
    )
    return row is not None


def is_valid_any_department(name):
    """Staff (Admin/Librarian) may hold either a program or a department."""
    row = db.fetch_one(
        'SELECT 1 FROM departments WHERE name = %s',
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
        'SELECT department_id, name, dept_type FROM departments WHERE department_id = %s',
        (department_id,)
    )


def count_borrowers_in_department(name):
    row = db.fetch_one(
        'SELECT COUNT(*) FROM borrowers WHERE department = %s',
        (name,)
    )
    return row[0] if row else 0


def delete_department(department_id):
    db.execute('DELETE FROM departments WHERE department_id = %s', (department_id,))