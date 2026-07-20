import secrets
from flask import render_template, redirect, url_for, request, flash, session, abort, current_app
from flask_login import login_user, logout_user, login_required, current_user
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from google_auth_oauthlib.flow import Flow
from . import auth_bp
from .models import (
    get_user_by_email, get_user_by_oauth_sub, create_user,
    create_pending_user, create_borrower, get_roles, get_role_by_name,
    log_activity, get_all_users, get_pending_users,
    approve_user, update_user_role, toggle_user_status, get_admin_count
)
from .user import User
from .decorators import librarian_required, admin_required


ALLOWED_DOMAIN = 'mcst.edu.ph'
SESSION_OAUTH_KEY = '_google_oauth_data'


def _allowed_email(email):
    return email.lower().endswith(f'@{ALLOWED_DOMAIN}')


def _build_flow(redirect_uri=None):
    if not redirect_uri:
        redirect_uri = url_for('auth.google_callback', _external=True)
    return Flow.from_client_config(
        {
            'web': {
                'client_id': current_app.config['GOOGLE_OAUTH_CLIENT_ID'],
                'client_secret': current_app.config['GOOGLE_OAUTH_CLIENT_SECRET'],
                'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                'token_uri': 'https://oauth2.googleapis.com/token',
            }
        },
        scopes=[
            'openid',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile',
        ],
        redirect_uri=redirect_uri,
    )


@auth_bp.route('/login', methods=['GET'])
def login():
    return render_template('auth/login.html')


@auth_bp.route('/login/google')
def google_login():
    next_page = request.args.get('next')
    if next_page:
        session['next'] = next_page

    try:
        flow = _build_flow()
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='select_account',
        )
        session['_oauth_state'] = state
        return redirect(authorization_url)
    except Exception as e:
        current_app.logger.error('Failed to initiate Google OAuth: %s', str(e))
        flash('Unable to connect to Google. Please try again.', 'error')
        return redirect(url_for('auth.login'))


@auth_bp.route('/login/google/callback')
def google_callback():
    state = session.pop('_oauth_state', None)
    if not state:
        flash('Invalid OAuth state. Please try again.', 'error')
        return redirect(url_for('auth.login'))

    expected_redirect = url_for('auth.google_callback', _external=True)
    flow = _build_flow(expected_redirect)

    try:
        flow.fetch_token(authorization_response=request.url)
    except Exception as e:
        current_app.logger.error('Token exchange failed: %s', str(e))
        flash(f'Authentication failed: {e}', 'error')
        return redirect(url_for('auth.login'))

    credentials = flow.credentials
    if not credentials or not credentials.id_token:
        flash('No identity token received.', 'error')
        return redirect(url_for('auth.login'))

    try:
        id_info = id_token.verify_oauth2_token(
            credentials.id_token,
            google_requests.Request(),
            current_app.config['GOOGLE_OAUTH_CLIENT_ID'],
            clock_skew_in_seconds=30,
        )
    except ValueError as e:
        current_app.logger.error('ID token verification failed: %s', str(e))
        flash(f'Authentication failed: {e}', 'error')
        return redirect(url_for('auth.login'))

    if id_info.get('iss') not in ('accounts.google.com', 'https://accounts.google.com'):
        flash('Invalid token issuer.', 'error')
        return redirect(url_for('auth.login'))

    email = id_info.get('email')
    if not email:
        flash('No email address provided by Google.', 'error')
        return redirect(url_for('auth.login'))

    if not _allowed_email(email):
        flash(f'Only @{ALLOWED_DOMAIN} email addresses are allowed.', 'error')
        return redirect(url_for('auth.login'))

    oauth_sub = id_info.get('sub')
    full_name = id_info.get('name', email.split('@')[0])

    existing_user = get_user_by_oauth_sub(oauth_sub)
    if existing_user:
        user = User(*existing_user)
        login_user(user)
        log_activity(user.id, 'login', None)
        next_page = session.pop('next', url_for('main.dashboard'))
        return redirect(next_page)

    existing_email = get_user_by_email(email)
    if existing_email:
        flash('This email is already registered. Contact the librarian if you need access.', 'error')
        return redirect(url_for('auth.login'))

    # First-ever user auto-creates as Admin, skip role selection
    if get_admin_count() == 0:
        user_id = create_user(email, oauth_sub, full_name, get_role_by_name('Admin')[0])
        if user_id:
            create_borrower(user_id, '', '')
            user = User(user_id, email, 'Admin', full_name)
            login_user(user)
            log_activity(user_id, 'first_login')
            flash('Welcome! You are the first admin.', 'success')
            return redirect(url_for('main.dashboard'))
        flash('Failed to create admin account.', 'error')
        return redirect(url_for('auth.login'))

    session[SESSION_OAUTH_KEY] = {
        'email': email,
        'oauth_sub': oauth_sub,
        'full_name': full_name,
    }
    return redirect(url_for('auth.role_select'))


@auth_bp.route('/login/role-select', methods=['GET', 'POST'])
def role_select():
    oauth_data = session.get(SESSION_OAUTH_KEY)
    if not oauth_data:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        role_name = request.form.get('role')
        id_number = request.form.get('id_number', '').strip()
        department = request.form.get('department', '').strip()

        if role_name not in ('Student', 'Faculty'):
            flash('Please select a valid role.', 'error')
            return render_template('auth/role_select.html')

        role = get_role_by_name(role_name)
        if not role:
            flash('Invalid role selected.', 'error')
            return render_template('auth/role_select.html')

        email = oauth_data['email']
        oauth_sub = oauth_data['oauth_sub']
        full_name = oauth_data['full_name']

        existing = get_user_by_oauth_sub(oauth_sub) or get_user_by_email(email)
        if existing:
            user = User(*existing)
            session.pop(SESSION_OAUTH_KEY, None)
            login_user(user)
            log_activity(user.id, 'login')
            flash('Welcome back!', 'success')
            return redirect(url_for('main.dashboard'))

        if get_admin_count() == 0:
            role_name = 'Admin'
            role = get_role_by_name(role_name)

        if role_name == 'Faculty':
            user_id = create_pending_user(email, oauth_sub, full_name, role[0])
            if user_id:
                create_borrower(user_id, id_number, department)
                session.pop(SESSION_OAUTH_KEY, None)
                flash('Your account requires librarian approval before you can access the system.', 'info')
                return render_template('auth/pending_approval.html', email=email)
            flash('Failed to create account. Please try again.', 'error')
            return render_template('auth/role_select.html')

        user_id = create_user(email, oauth_sub, full_name, role[0])
        if not user_id:
            flash('Failed to create account. Please try again.', 'error')
            return render_template('auth/role_select.html')

        create_borrower(user_id, id_number, department)
        session.pop(SESSION_OAUTH_KEY, None)
        user = User(user_id, email, role_name, full_name)
        login_user(user)
        log_activity(user_id, 'first_login')
        next_page = session.pop('next', url_for('main.dashboard'))
        return redirect(next_page)

    return render_template('auth/role_select.html')


@auth_bp.route('/admin/users')
@login_required
@librarian_required
def admin_users():
    users = get_all_users()
    pending = get_pending_users()
    status_filter = request.args.get('status', '')
    if status_filter:
        users = [u for u in users if u[4] == status_filter]
    total = len(users)
    active = sum(1 for u in users if u[4] == 'active')
    students = sum(1 for u in users if u[3] == 'Student')
    suspended = sum(1 for u in users if u[4] == 'disabled')
    return render_template('users/users.html',
                           users=users, roles=get_roles(),
                           pending=pending, total=total,
                           active=active, students=students,
                           suspended=suspended,
                           status_filter=status_filter)


@auth_bp.route('/admin/users/<int:user_id>/approve', methods=['POST'])
@login_required
@librarian_required
def approve_user_route(user_id):
    approve_user(user_id)
    log_activity(current_user.id, f'approved_user:{user_id}')
    flash('User approved.', 'success')
    return redirect(url_for('auth.admin_users'))


@auth_bp.route('/admin/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status_route(user_id):
    toggle_user_status(user_id)
    log_activity(current_user.id, f'toggled_user_status:{user_id}')
    flash('User status updated.', 'success')
    return redirect(url_for('auth.admin_users'))


@auth_bp.route('/admin/users/<int:user_id>/role', methods=['POST'])
@login_required
@admin_required
def change_user_role(user_id):
    role_id = request.form.get('role_id')
    if role_id:
        update_user_role(user_id, role_id)
        log_activity(current_user.id, f'changed_role:{user_id}_to_{role_id}')
        flash('User role updated.', 'success')
    return redirect(url_for('auth.admin_users'))


@auth_bp.route('/admin/reset-db', methods=['GET', 'POST'])
@login_required
@admin_required
def reset_db():
    from app.database import db as db_instance, run_schema
    conn = db_instance._pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute('DROP SCHEMA public CASCADE; CREATE SCHEMA public;')
        conn.commit()
        run_schema(current_app)
        app.logger.info('Database reset complete.')
    except Exception as e:
        conn.rollback()
        current_app.logger.error('Database reset failed: %s', e)
        flash('Reset failed. Check logs.', 'error')
        return redirect(url_for('auth.admin_users'))
    finally:
        db_instance._pool.putconn(conn)
    logout_user()
    flash('Database reset. Please log in again.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/logout')
@login_required
def logout():
    log_activity(current_user.id, 'logout')
    logout_user()
    return redirect(url_for('auth.login'))
