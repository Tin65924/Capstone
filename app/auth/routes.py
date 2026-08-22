import csv
import io
import os
import secrets
from datetime import datetime

from flask import Response, render_template, redirect, url_for, request, flash, session, abort, current_app
from flask_login import login_user, logout_user, login_required, current_user
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from google_auth_oauthlib.flow import Flow
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from . import auth_bp
from app.database import db
from app.bloom_registry import bloom_registry
from .models import (
    get_user_by_email, get_user_by_oauth_sub, create_user,
    create_pending_user, create_borrower, get_roles, get_role_by_name,
    log_activity, get_all_users, get_pending_users,
    approve_user, update_user_role, toggle_user_status,
    update_user_details, archive_user, unarchive_user, delete_user, get_admin_count, get_user_by_id
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
        verifier = getattr(flow, 'code_verifier', None)
        if isinstance(verifier, str) and verifier:
            session['_oauth_code_verifier'] = verifier
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

    verifier = session.pop('_oauth_code_verifier', None)
    if verifier:
        flow.code_verifier = verifier

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
        next_page = session.pop('next', url_for('main.user_profile'))
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
            return redirect(url_for('main.user_profile'))
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
            return redirect(url_for('main.user_profile'))

        if get_admin_count() == 0:
            role_name = 'Admin'
            role = get_role_by_name(role_name)

        if role_name == 'Faculty':
            user_id = create_pending_user(email, oauth_sub, full_name, role[0])
            if user_id:
                create_borrower(user_id, id_number, department)
                bloom_registry.mark_dirty()
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
        bloom_registry.mark_dirty()
        session.pop(SESSION_OAUTH_KEY, None)
        user = User(user_id, email, role_name, full_name)
        login_user(user)
        log_activity(user_id, 'first_login')
        next_page = session.pop('next', url_for('main.user_profile'))
        return redirect(next_page)

    return render_template('auth/role_select.html')


@auth_bp.route('/librarian/users')
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
    inactive = sum(1 for u in users if u[4] == 'disabled')
    archived = sum(1 for u in users if u[4] == 'archived')
    return render_template('users/users.html',
                           users=users, roles=get_roles(),
                           pending=pending, total=total,
                           active=active, students=students,
                           inactive=inactive, archived=archived,
                           status_filter=status_filter)


_USER_EXPORT_HEADERS = [
    'User ID', 'Email', 'Full Name', 'Role', 'Account Status',
    'Created At', 'ID Number', 'Department',
]


def _user_row_to_export(row):
    def _str(v):
        return '' if v is None else str(v)
    created = row[5]
    created_s = created.isoformat(sep=' ') if hasattr(created, 'isoformat') else _str(created)
    return [
        _str(row[0]), _str(row[1]), _str(row[2]), _str(row[3]), _str(row[4]),
        created_s, _str(row[6]), _str(row[7]),
    ]


def _style_user_xlsx(ws, headers):
    navy = PatternFill(start_color='1e3a8a', end_color='1e3a8a', fill_type='solid')
    white_font = Font(color='FFFFFF', bold=True, size=9, name='Calibri')
    thin = Side(style='thin', color='cbd5e1')
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    for col, h in enumerate(headers, 1):
        c = ws.cell(row=1, column=col, value=h)
        c.fill = navy
        c.font = white_font
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        c.border = border
    ws.row_dimensions[1].height = 18
    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = ws.dimensions
    widths = [10, 28, 24, 12, 14, 18, 14, 22]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = w


@auth_bp.route('/librarian/users/export')
@login_required
@librarian_required
def export_users():
    status = request.args.get('status', '').strip().lower()
    fmt = request.args.get('format', 'csv').strip().lower()
    if fmt not in ('csv', 'xlsx'):
        fmt = 'csv'
    # map Inactive alias to disabled; allow 'all' or '' for no filter
    if status == 'inactive':
        status = 'disabled'
    if status not in ('active', 'disabled', 'pending', 'archived'):
        status = ''

    users = get_all_users()
    if status:
        users = [u for u in users if (u[4] or '').lower() == status]

    rows = [_user_row_to_export(u) for u in users]
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    suffix = status or 'all'
    # normalize suffix for filename: disabled -> inactive is more readable
    file_suffix = 'inactive' if suffix == 'disabled' else suffix
    filename = f'users_{file_suffix}_{stamp}.{fmt}'

    if fmt == 'xlsx':
        wb = Workbook()
        ws = wb.active
        ws.title = 'Users'
        _style_user_xlsx(ws, _USER_EXPORT_HEADERS)
        for r in rows:
            ws.append(r)
        thin = Side(style='thin', color='cbd5e1')
        border = Border(left=thin, right=thin, top=thin, bottom=thin)
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, max_col=len(_USER_EXPORT_HEADERS)):
            for cell in row:
                cell.font = Font(size=9, name='Calibri')
                cell.alignment = Alignment(vertical='center', wrap_text=True)
                cell.border = border
            ws.row_dimensions[row[0].row].height = 15
        light = PatternFill(start_color='f8fafc', end_color='f8fafc', fill_type='solid')
        for idx, row in enumerate(ws.iter_rows(min_row=2, max_row=ws.max_row, max_col=len(_USER_EXPORT_HEADERS)), 2):
            if idx % 2 == 0:
                for cell in row:
                    cell.fill = light
        buf = io.BytesIO()
        wb.save(buf)
        body = buf.getvalue()
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    else:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(_USER_EXPORT_HEADERS)
        writer.writerows(rows)
        body = buf.getvalue().encode('utf-8-sig')
        mimetype = 'text/csv'

    log_activity(current_user.id, f'users:export:{file_suffix}:{len(rows)}')
    return Response(
        body,
        mimetype=mimetype,
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )


@auth_bp.route('/librarian/users/<int:user_id>/approve', methods=['POST'])
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


@auth_bp.route('/admin/users/<int:user_id>/archive', methods=['POST'])
@login_required
@admin_required
def archive_user_route(user_id):
    archive_user(user_id)
    log_activity(current_user.id, f'archived_user:{user_id}')
    flash('User archived.', 'success')
    return redirect(url_for('auth.admin_users'))


@auth_bp.route('/admin/users/<int:user_id>/unarchive', methods=['POST'])
@login_required
@admin_required
def unarchive_user_route(user_id):
    unarchive_user(user_id)
    log_activity(current_user.id, f'unarchived_user:{user_id}')
    flash('User restored.', 'success')
    return redirect(url_for('auth.admin_users'))


@auth_bp.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user_route(user_id):
    user = get_user_by_id(user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('auth.admin_users'))
    status = db.fetch_one(
        'SELECT account_status FROM user_accounts WHERE user_id = %s',
        (user_id,)
    )
    if status and status[0] != 'archived':
        flash('User must be archived before deletion.', 'error')
        return redirect(url_for('auth.admin_users'))
    delete_user(user_id)
    log_activity(current_user.id, f'deleted_user:{user_id}')
    flash('User permanently deleted.', 'success')
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


@auth_bp.route('/admin/users/<int:user_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_user_route(user_id):
    full_name = request.form.get('full_name', '').strip()
    id_number = request.form.get('id_number', '').strip()
    department = request.form.get('department', '').strip()
    if full_name:
        update_user_details(user_id, full_name, id_number or None, department or None)
        bloom_registry.mark_dirty()
        log_activity(current_user.id, f'edited_user:{user_id}')
        flash('User details updated.', 'success')
    return redirect(url_for('auth.admin_users', modal='editModal', user_id=user_id, mstatus='success'))


@auth_bp.route('/admin/reset-db', methods=['GET', 'POST'])
@login_required
@admin_required
def reset_db():
    import psycopg2
    dsn = current_app.config['DATABASE_URL']
    schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schema.sql')
    conn = psycopg2.connect(dsn)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute('DROP SCHEMA public CASCADE; CREATE SCHEMA public;')
            if os.path.isfile(schema_path):
                with open(schema_path, 'r') as f:
                    cur.execute(f.read())
            cur.execute("""
                ALTER TABLE user_accounts
                DROP CONSTRAINT IF EXISTS user_accounts_account_status_check;
            """)
            cur.execute("""
                ALTER TABLE user_accounts
                ADD CONSTRAINT user_accounts_account_status_check
                CHECK (account_status IN ('active', 'disabled', 'pending'));
            """)
        conn.close()
        current_app.logger.info('Database reset complete.')
    except Exception as e:
        current_app.logger.error('Database reset failed: %s', e)
        flash('Reset failed: ' + str(e), 'error')
        return redirect(url_for('auth.admin_users'))
    logout_user()
    flash('Database reset. Please log in again.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/logout')
@login_required
def logout():
    log_activity(current_user.id, 'logout')
    logout_user()
    return redirect(url_for('auth.login'))
