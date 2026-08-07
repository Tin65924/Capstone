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