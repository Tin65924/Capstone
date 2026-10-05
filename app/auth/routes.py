import csv
import io
import secrets
from datetime import datetime

from flask import Response, render_template, redirect, url_for, request, flash, session, abort, current_app, jsonify
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
    log_activity, log_system_event, get_all_users, get_pending_users,
    approve_user, update_user_role, toggle_user_status,
    update_user_details, archive_user, unarchive_user, delete_user, get_admin_count,
    get_user_record, audit_text, get_account_status, get_user_deletion_blocker,
    get_departments, is_valid_department, create_department,
    get_department_by_id, get_department_by_name, delete_department, count_borrowers_in_department,
    update_department_status, DEPT_STATUSES,
    get_profile_by_user, DEPT_TYPES, is_valid_any_department,
    is_valid_id_number, normalize_id_number, ID_NUMBER_EXAMPLES, get_user_by_id_number
)
from .user import User
from .decorators import librarian_required, admin_required


ALLOWED_DOMAIN = 'mcst.edu.ph'
SESSION_OAUTH_KEY = '_google_oauth_data'


def _allowed_email(email):
    return email.lower().endswith(f'@{ALLOWED_DOMAIN}')


def _login_status(user_id):
    """Account status for a returning OAuth user ('active' on any doubt).

    get_user_by_oauth_sub/get_user_by_email carry no status, so sign-in
    must check explicitly — otherwise an archived/disabled user would
    'log in' and then bounce on every page with a generic
    'Please sign in' message that never explains the real reason.
    """
    try:
        record = get_user_record(user_id)
    except Exception:
        return 'active'
    if record and len(record) > 4 and record[4]:
        return record[4]
    return 'active'


def _safe_next_url(fallback_endpoint='main.user_profile'):
    """Pop a validated post-login redirect from the session.

    Only same-origin relative paths (single leading `/`, no scheme or
    host) are honored; anything else (including the `next` values an
    attacker plants via /login?next=...) falls back to `fallback_endpoint`.
    """
    from urllib.parse import urlparse
    fallback = url_for(fallback_endpoint)
    nxt = session.pop('next', fallback)
    if not nxt or not isinstance(nxt, str):
        return fallback
    parsed = urlparse(nxt)
    if parsed.scheme or parsed.netloc:
        return fallback
    # Backslashes are treated as slashes by browsers (open-redirect
    # bypass like /\\evil.com), so reject them outright.
    if '\\' in nxt:
        return fallback
    if not nxt.startswith('/') or nxt.startswith('//'):
        return fallback
    return nxt


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
        log_system_event('system:login_failed:initiate')
        flash('Unable to connect to Google. Please try again.', 'error')
        return redirect(url_for('auth.login'))


@auth_bp.route('/login/google/callback')
def google_callback():
    state = session.pop('_oauth_state', None)
    if not state:
        log_system_event('system:login_failed:invalid_state')
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
        log_system_event('system:login_failed:token_exchange')
        flash(f'Authentication failed: {e}', 'error')
        return redirect(url_for('auth.login'))

    credentials = flow.credentials
    if not credentials or not credentials.id_token:
        log_system_event('system:login_failed:no_id_token')
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
        log_system_event('system:login_failed:verify')
        flash(f'Authentication failed: {e}', 'error')
        return redirect(url_for('auth.login'))

    if id_info.get('iss') not in ('accounts.google.com', 'https://accounts.google.com'):
        log_system_event('system:login_failed:issuer')
        flash('Invalid token issuer.', 'error')
        return redirect(url_for('auth.login'))

    email = id_info.get('email')
    if not email:
        log_system_event('system:login_failed:email')
        flash('No email address provided by Google.', 'error')
        return redirect(url_for('auth.login'))

    if not _allowed_email(email):
        log_system_event('system:login_failed:domain')
        flash(f'Only @{ALLOWED_DOMAIN} email addresses are allowed.', 'error')
        return redirect(url_for('auth.login'))

    oauth_sub = id_info.get('sub')
    full_name = id_info.get('name', email.split('@')[0])

    existing_user = get_user_by_oauth_sub(oauth_sub)
    if existing_user:
        status = _login_status(existing_user[0])
        if status == 'pending':
            flash('Your account is still waiting for librarian approval.', 'info')
            return render_template('auth/pending_approval.html', email=email)
        if status != 'active':
            flash(f'Your account is {status}. Contact the librarian if you need access.', 'error')
            return redirect(url_for('auth.login'))
        user = User(*existing_user)
        login_user(user)
        log_activity(user.id, 'login', None)
        next_page = _safe_next_url()
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

    def _render_register(error=None):
        if error:
            flash(error, 'error')
        return render_template('auth/role_select.html',
                               programs=get_departments('program'),
                               departments=get_departments('department'))

    if request.method == 'POST':
        role_name = request.form.get('role')
        id_number = normalize_id_number(request.form.get('id_number', ''), role_name)
        department = request.form.get('department', '').strip()

        if role_name not in ('Student', 'Faculty'):
            return _render_register('Please select a valid role.')

        if not is_valid_id_number(id_number, role_name):
            example = ID_NUMBER_EXAMPLES.get(role_name, '')
            return _render_register(
                f'Invalid ID number for {role_name}. Use format {example}.'
            )

        if get_user_by_id_number(id_number):
            return _render_register('This ID number is already registered.')

        # Students pick a Program, faculty pick a Department — strictly
        # from the controlled vocabulary so variants can't creep in.
        dept_type = 'program' if role_name == 'Student' else 'department'
        if not department or not is_valid_department(department, dept_type):
            label = 'program' if dept_type == 'program' else 'department'
            return _render_register(
                f'Please select a valid {label} from the list. '
                f'If yours is missing, ask the librarian to add it first.'
            )

        role = get_role_by_name(role_name)
        if not role:
            return _render_register('Invalid role selected.')

        email = oauth_data['email']
        oauth_sub = oauth_data['oauth_sub']
        full_name = oauth_data['full_name']

        existing = get_user_by_oauth_sub(oauth_sub) or get_user_by_email(email)
        if existing:
            status = _login_status(existing[0])
            session.pop(SESSION_OAUTH_KEY, None)
            if status == 'pending':
                flash('Your account is still waiting for librarian approval.', 'info')
                return render_template('auth/pending_approval.html', email=email)
            if status != 'active':
                flash(f'Your account is {status}. Contact the librarian if you need access.', 'error')
                return redirect(url_for('auth.login'))
            user = User(*existing)
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
            return _render_register('Failed to create account. Please try again.')

        user_id = create_user(email, oauth_sub, full_name, role[0])
        if not user_id:
            return _render_register('Failed to create account. Please try again.')

        create_borrower(user_id, id_number, department)
        bloom_registry.mark_dirty()
        session.pop(SESSION_OAUTH_KEY, None)
        user = User(user_id, email, role_name, full_name)
        login_user(user)
        log_activity(user_id, 'first_login')
        next_page = _safe_next_url()
        return redirect(next_page)

    return render_template('auth/role_select.html',
                           programs=get_departments('program'),
                           departments=get_departments('department'))


@auth_bp.route('/librarian/users')
@login_required
@librarian_required
def admin_users():
    users = get_all_users() or []
    pending = get_pending_users() or []
    status_filter = request.args.get('status', '')
    role_filter = request.args.get('role', '')
    scope = (request.args.get('scope', '') or '').strip().lower()
    if scope not in ('', 'staff', 'members', 'all'):
        scope = ''
    is_admin_view = current_user.role == 'Admin'
    # User Management visibility rules:
    # - Librarians see members + fellow librarians (everything except Admin).
    # - Admins default to the same listing; explicit ?scope=staff shows
    #   all staff (Librarian + Faculty + Admin, never students),
    #   ?scope=all shows every account.
    # - The sidebar follows the scope (staff -> admin sidebar,
    #   otherwise librarian sidebar), so entering from the librarian
    #   dashboard never bounces into admin space. Nothing here redirects
    #   to either dashboard; actions return to this same page.
    if not is_admin_view:
        scope = 'members'
    elif not scope:
        scope = 'members'
    if scope == 'staff':
        users = [u for u in users if u[3] in ('Librarian', 'Faculty', 'Admin')]
        pending = [p for p in pending if p[3] in ('Librarian', 'Faculty', 'Admin')]
    elif scope == 'members':
        users = [u for u in users if u[3] in ('Student', 'Faculty', 'Librarian')]
        pending = [p for p in pending if p[3] in ('Student', 'Faculty', 'Librarian')]
    # KPIs reflect the current scope, not the table filters — compute
    # before applying status/role filters so clicking a card doesn't zero
    # the other cards.
    total = len(users)
    active = sum(1 for u in users if u[4] == 'active')
    students = sum(1 for u in users if u[3] == 'Student')
    faculty = sum(1 for u in users if u[3] == 'Faculty')
    inactive = sum(1 for u in users if u[4] == 'disabled')
    archived = sum(1 for u in users if u[4] == 'archived')
    if status_filter:
        users = [u for u in users if u[4] == status_filter]
    if role_filter:
        users = [u for u in users if u[3] == role_filter]
    # Server-side pagination (20/page). KPI counts above stay
    # scope-wide; only the table page is sliced. The pager renders
    # only when there is more than one page.
    page = request.args.get('page', 1, type=int)
    if not page or page < 1:
        page = 1
    per_page = 20
    total_pages = max(1, (len(users) + per_page - 1) // per_page)
    if page > total_pages:
        page = total_pages
    users = users[(page - 1) * per_page:page * per_page]
    # The sidebar follows the view scope (not just the role), so an
    # admin entering from the librarian dashboard stays in librarian
    # space instead of bouncing into admin space.
    sidebar = ('components/admin_sidebar_nav.html' if scope == 'staff'
               else 'components/librarian_sidebar_nav.html')
    # Full vocab (including inactive) drives the management listing so
    # librarians can reactivate entries; dropdowns/options below only
    # receive the active subset — inactive values never appear as options.
    # NOTE: roles are fetched before the vocab to preserve the DB call
    # order the test-suite mocks rely on (users, pending, roles, vocab).
    roles = get_roles()
    programs_all = get_departments('program', include_inactive=True) or []
    departments_all = get_departments('department', include_inactive=True) or []

    def _only_active(rows):
        return [r for r in (rows or [])
                if (r[3] if len(r) > 3 and r[3] else 'active') == 'active']

    return render_template('users/users.html',
                               users=users, roles=roles,
                               pending=pending, total=total,
                               active=active, students=students,
                               faculty=faculty,
                               inactive=inactive, archived=archived,
                           status_filter=status_filter,
                           role_filter=role_filter,
                           scope=scope,
                           current_page=page,
                           total_pages=total_pages,
                           is_staff_view=(scope == 'staff'),
                           is_admin_view=is_admin_view,
                           sidebar=sidebar,
                           programs=_only_active(programs_all),
                           departments=_only_active(departments_all),
                           programs_all=programs_all,
                           departments_all=departments_all)


_USER_EXPORT_HEADERS = [
    'User ID', 'Email', 'Full Name', 'Role', 'Account Status',
    'Created At', 'ID Number', 'Department',
]


# get_all_users() contract: 8 positional cols from auth/models.py:96
# 0 user_id, 1 email, 2 full_name, 3 role_name, 4 account_status, 5 created_at, 6 id_number, 7 department
# Keep in sync with schema.sql account_status CHECK ('active','disabled','pending','archived')
_USER_COL = {'user_id': 0, 'email': 1, 'full_name': 2, 'role': 3, 'status': 4, 'created': 5, 'id_number': 6, 'dept': 7}


def _user_row_to_export(row):
    def _str(v):
        return '' if v is None else str(v)
    # created_at may be datetime, date, or string (mock); handle all
    created = row[_USER_COL['created']] if len(row) > _USER_COL['created'] else None
    if hasattr(created, 'isoformat'):
        try:
            created_s = created.isoformat(sep=' ', timespec='seconds')
        except TypeError:
            created_s = created.isoformat()
    else:
        created_s = _str(created)
    return [
        _str(row[_USER_COL['user_id']] if len(row) > _USER_COL['user_id'] else ''),
        _str(row[_USER_COL['email']] if len(row) > _USER_COL['email'] else ''),
        _str(row[_USER_COL['full_name']] if len(row) > _USER_COL['full_name'] else ''),
        _str(row[_USER_COL['role']] if len(row) > _USER_COL['role'] else ''),
        _str(row[_USER_COL['status']] if len(row) > _USER_COL['status'] else ''),
        created_s,
        _str(row[_USER_COL['id_number']] if len(row) > _USER_COL['id_number'] else ''),
        _str(row[_USER_COL['dept']] if len(row) > _USER_COL['dept'] else ''),
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


def _generate_user_csv(headers, rows):
    """Yield CSV bytes incrementally — scalable for large exports."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(headers)
    yield buf.getvalue().encode('utf-8-sig')
    buf.seek(0)
    buf.truncate(0)
    for r in rows:
        writer.writerow(r)
        data = buf.getvalue()
        if data:
            yield data.encode('utf-8') if isinstance(data, str) else data
            buf.seek(0)
            buf.truncate(0)


@auth_bp.route('/librarian/users/export')
@login_required
@librarian_required
def export_users():
    status = request.args.get('status', '').strip().lower()
    fmt = request.args.get('format', 'csv').strip().lower()
    if fmt not in ('csv', 'xlsx'):
        fmt = 'csv'
    # UI uses Inactive but DB uses disabled — keep mapping symmetric
    # schema.sql: CHECK (account_status IN ('active','disabled','pending','archived'))
    if status == 'inactive':
        status = 'disabled'
    if status not in ('active', 'disabled', 'pending', 'archived'):
        status = ''

    users = get_all_users() or []
    scope = (request.args.get('scope', '') or '').strip().lower()
    if scope not in ('', 'staff', 'members', 'all'):
        scope = ''
    # Same visibility rules as the manage page: librarians see
    # members + fellow librarians (never admins); admins default to
    # the same listing; explicit staff/all honored; staff never leaks
    # students.
    if current_user.role != 'Admin':
        scope = 'members'
    elif not scope:
        scope = 'members'
    if scope == 'staff':
        users = [u for u in users
                 if u[_USER_COL['role']] in ('Librarian', 'Faculty', 'Admin')]
    elif scope == 'members':
        users = [u for u in users
                 if u[_USER_COL['role']] in ('Student', 'Faculty', 'Librarian')]
    if status:
        users = [u for u in users if (u[_USER_COL['status']] or '').lower() == status]
    role = request.args.get('role', '').strip()
    if role:
        users = [u for u in users if u[_USER_COL['role']] == role]

    rows = [_user_row_to_export(u) for u in users]
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    suffix = status or 'all'
    # filename uses UI term inactive for readability
    file_suffix = 'inactive' if suffix == 'disabled' else suffix
    if scope:
        file_suffix = f'{file_suffix}_{scope}'
    if role:
        file_suffix = f'{file_suffix}_{role.lower()}'
    filename = f'users_{file_suffix}_{stamp}.{fmt}'

    if fmt == 'xlsx':
        # For large exports, write_only would be more scalable; current buffered
        # approach is fine for capstone scale (<10k rows) and keeps styling.
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
        log_activity(current_user.id, f'users:export:{file_suffix}:{len(rows)}')
        return Response(
            body,
            mimetype=mimetype,
            headers={'Content-Disposition': f'attachment; filename="{filename}"'},
        )
    else:
        # Stream CSV to avoid holding large exports fully in memory
        log_activity(current_user.id, f'users:export:{file_suffix}:{len(rows)}')
        return Response(
            _generate_user_csv(_USER_EXPORT_HEADERS, rows),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'},
        )


@auth_bp.route('/librarian/users/<int:user_id>/approve', methods=['POST'])
@login_required
@librarian_required
def approve_user_route(user_id):
    user = db.fetch_one(
        '''SELECT u.user_id, u.email, r.role_name, u.full_name
           FROM user_accounts u
           JOIN roles r ON u.role_id = r.role_id
           WHERE u.user_id = %s''',
        (user_id,)
    )
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('auth.admin_users'))
    approve_user(user_id, updated_by=current_user.id)
    log_activity(current_user.id, f'approved_user:{user_id}:{_target_name(user_id)}')
    flash('User approved.', 'success')
    return redirect(url_for('auth.admin_users'))


def _target_name(user_id):
    """Display name of the acted-upon user for audit codes (id fallback).

    Lenient by design: audit enrichment must never break the action on
    an unexpected row shape.
    """
    target = get_user_record(user_id)
    if target and len(target) > 3 and target[3]:
        return audit_text(target[3], 40)
    return f'#{user_id}'


@auth_bp.route('/admin/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status_route(user_id):
    record = get_user_record(user_id)
    if not record:
        flash('User not found.', 'error')
        return redirect(url_for('auth.admin_users'))
    if len(record) > 4 and record[4] not in ('active', 'disabled'):
        flash('Only active or disabled accounts can have their status toggled.', 'info')
        return redirect(url_for('auth.admin_users'))
    toggle_user_status(user_id, updated_by=current_user.id)
    log_activity(current_user.id, f'toggled_user_status:{user_id}:{_target_name(user_id)}')
    flash('User status updated.', 'success')
    return redirect(url_for('auth.admin_users'))


@auth_bp.route('/admin/users/<int:user_id>/archive', methods=['POST'])
@login_required
@admin_required
def archive_user_route(user_id):
    if not get_user_record(user_id):
        flash('User not found.', 'error')
        return redirect(url_for('auth.admin_users'))
    archive_user(user_id, updated_by=current_user.id)
    log_activity(current_user.id, f'archived_user:{user_id}:{_target_name(user_id)}')
    flash('User archived.', 'success')
    return redirect(url_for('auth.admin_users'))


@auth_bp.route('/admin/users/<int:user_id>/unarchive', methods=['POST'])
@login_required
@admin_required
def unarchive_user_route(user_id):
    if not get_user_record(user_id):
        flash('User not found.', 'error')
        return redirect(url_for('auth.admin_users'))
    unarchive_user(user_id, updated_by=current_user.id)
    log_activity(current_user.id, f'unarchived_user:{user_id}:{_target_name(user_id)}')
    flash('User restored.', 'success')
    return redirect(url_for('auth.admin_users'))


@auth_bp.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user_route(user_id):
    # Name first: the row is gone after delete_user().
    target_name = _target_name(user_id)
    user = get_user_record(user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('auth.admin_users'))
    if str(user_id) == str(current_user.id):
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('auth.admin_users'))
    status = get_account_status(user_id)
    status_value = status[0] if status else (user[4] if len(user) > 4 else None)
    if status_value != 'archived':
        flash('User must be archived before deletion.', 'error')
        return redirect(url_for('auth.admin_users'))
    blocker = get_user_deletion_blocker(user_id)
    if blocker:
        flash(f'Cannot delete {target_name} — account has {blocker}.', 'error')
        return redirect(url_for('auth.admin_users'))
    try:
        delete_user(user_id)
    except Exception:
        current_app.logger.exception('Failed to delete user %s', user_id)
        flash('Cannot delete this account — it is still linked to library records.', 'error')
        return redirect(url_for('auth.admin_users'))
    log_activity(current_user.id, f'deleted_user:{user_id}:{target_name}')
    flash('User permanently deleted.', 'success')
    return redirect(url_for('auth.admin_users'))


@auth_bp.route('/admin/users/<int:user_id>/role', methods=['POST'])
@login_required
@admin_required
def change_user_role(user_id):
    role_id = request.form.get('role_id')
    if role_id:
        target = get_user_record(user_id)
        old_role = target[2] if target and len(target) > 2 else None
        new_role = next((r[1] for r in get_roles() or []
                         if len(r) > 1 and str(r[0]) == str(role_id)), None)
        if not target:
            flash('User not found.', 'error')
            return redirect(url_for('auth.admin_users'))
        if new_role is None:
            flash('Invalid role selected.', 'error')
            return redirect(url_for('auth.admin_users'))
        is_self = str(user_id) == str(current_user.id)
        demoting_admin = old_role == 'Admin' and new_role != 'Admin'
        if demoting_admin:
            try:
                admin_count = get_admin_count()
            except Exception:
                admin_count = 2
            if admin_count <= 1:
                if is_self:
                    flash('You are the last admin. Transfer the admin role to another user before changing your own role.', 'error')
                else:
                    flash('This is the last admin account. Assign another admin before changing this role.', 'error')
                return redirect(url_for('auth.admin_users'))
        update_user_role(user_id, role_id, updated_by=current_user.id)
        if old_role and new_role:
            detail = (f':{audit_text(old_role, 30)}~>'
                      f'{audit_text(new_role, 30)}')
        else:
            detail = f'_to_{role_id}'
        if target and len(target) > 3 and target[3]:
            name = audit_text(target[3], 40)
        else:
            name = f'#{user_id}'
        log_activity(current_user.id,
                     f'changed_role:{user_id}{detail}:{name}')
        flash('User role updated.', 'success')
    return redirect(url_for('auth.admin_users'))


@auth_bp.route('/admin/users/<int:user_id>/edit', methods=['POST'])
@login_required
@librarian_required
def edit_user_route(user_id):
    # Librarians may modify student/faculty information only — never
    # staff accounts. Admins may edit anyone.
    if current_user.role != 'Admin':
        profile = get_profile_by_user(user_id)
        role_name = profile[2] if profile and len(profile) > 2 else None
        if role_name not in ('Student', 'Faculty'):
            flash('Librarians can only edit student and faculty accounts.', 'error')
            return redirect(url_for('auth.admin_users'))
    full_name = request.form.get('full_name', '').strip()
    id_number = request.form.get('id_number', '').strip()
    department = request.form.get('department', '').strip()
    if full_name:
        profile = get_profile_by_user(user_id)
        role_name = profile[2] if profile else None
        current_dept = profile[6] if profile else None
        current_id = profile[5] if profile and len(profile) > 5 else None
        has_borrower = bool(profile and len(profile) > 4 and profile[4] is not None)
        if id_number and role_name in ID_NUMBER_EXAMPLES:
            id_number = normalize_id_number(id_number, role_name)
            # Unchanged value (e.g. legacy rows) stays editable; only new
            # values must match the canonical per-role format.
            if id_number != (current_id or ''):
                if not is_valid_id_number(id_number, role_name):
                    flash(f'Invalid ID number for {role_name}. Use format '
                          f'{ID_NUMBER_EXAMPLES[role_name]}.', 'error')
                    return redirect(url_for('auth.admin_users', modal='editModal',
                                            user_id=user_id, mstatus='error'))
                if get_user_by_id_number(id_number):
                    flash('This ID number is already registered.', 'error')
                    return redirect(url_for('auth.admin_users', modal='editModal',
                                            user_id=user_id, mstatus='error'))
        if has_borrower and department != (current_dept or ''):
            if role_name in ('Student', 'Faculty'):
                dept_type = 'program' if role_name == 'Student' else 'department'
                valid = bool(department) and is_valid_department(department, dept_type)
            else:
                # Staff with a borrower record: accept any active vocab entry.
                valid = bool(department) and is_valid_any_department(department)
            if not valid:
                flash('Please select a valid program/department from the list.', 'error')
                return redirect(url_for('auth.admin_users', modal='editModal',
                                        user_id=user_id, mstatus='error'))
        update_user_details(user_id, full_name, id_number or None, department or None,
                            updated_by=current_user.id)
        bloom_registry.mark_dirty()
        log_activity(current_user.id,
                     f'edited_user:{user_id}:{_target_name(user_id)}')
        flash('User details updated.', 'success')
    return redirect(url_for('auth.admin_users', modal='editModal', user_id=user_id, mstatus='success'))


@auth_bp.route('/librarian/departments/add', methods=['POST'])
@login_required
@librarian_required
def add_department_route():
    name = request.form.get('name', '').strip()
    dept_type = request.form.get('dept_type', '').strip()
    wants_json = _wants_json()

    def _fail(message, code):
        if wants_json:
            return jsonify({'error': message}), code
        flash(message, 'error')
        return redirect(url_for('auth.admin_users'))

    if not name:
        return _fail('Program/department name is required.', 400)
    if dept_type not in DEPT_TYPES:
        return _fail('Invalid type. Choose Program or Department.', 400)
    if is_valid_department(name, dept_type):
        return _fail(f'"{name}" already exists.', 409)
    rowcount = create_department(name, dept_type)
    if not rowcount:
        # Lost a race with another insert (ON CONFLICT DO NOTHING).
        return _fail(f'"{name}" already exists.', 409)
    log_activity(current_user.id, f'added_department:{dept_type}:{name}')
    if wants_json:
        row = get_department_by_name(name)
        return jsonify({'added': {'id': row[0], 'name': row[1],
                                  'dept_type': row[2]}})
    flash(f'"{name}" added.', 'success')
    return redirect(url_for('auth.admin_users'))


@auth_bp.route('/admin/departments/<int:department_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_department_route(department_id):
    wants_json = _wants_json()

    def _fail(message, code):
        if wants_json:
            return jsonify({'error': message}), code
        flash(message, 'error')
        return redirect(url_for('auth.admin_users'))

    dept = get_department_by_id(department_id)
    if not dept:
        return _fail('Entry not found.', 404)
    dept_type = dept[2] if len(dept) > 2 else None
    in_use = count_borrowers_in_department(dept[1], dept_type)
    if in_use:
        return _fail(f'Cannot delete "{dept[1]}" — {in_use} borrower(s) still use it.', 409)
    delete_department(department_id)
    log_activity(current_user.id, f'deleted_department:{department_id}')
    if wants_json:
        return jsonify({'deleted': department_id, 'name': dept[1]})
    flash(f'"{dept[1]}" deleted.', 'success')
    return redirect(url_for('auth.admin_users'))


@auth_bp.route('/librarian/departments/<int:department_id>/status', methods=['POST'])
@login_required
@librarian_required
def update_department_status_route(department_id):
    """Switch a program/department between active and inactive.

    Librarian-accessible (Admin included): inactive entries stay in the
    table but disappear from every registration/profile option.
    """
    wants_json = _wants_json()

    def _fail(message, code):
        if wants_json:
            return jsonify({'error': message}), code
        flash(message, 'error')
        return redirect(url_for('auth.admin_users'))

    status = (request.form.get('status') or '').strip().lower()
    if status not in DEPT_STATUSES:
        return _fail('Invalid status. Choose Active or Inactive.', 400)

    dept = get_department_by_id(department_id)
    if not dept:
        return _fail('Entry not found.', 404)
    current = dept[3] if len(dept) > 3 and dept[3] else 'active'
    if current == status:
        if wants_json:
            return jsonify({'updated': department_id, 'name': dept[1], 'status': status})
        flash(f'"{dept[1]}" is already {status}.', 'info')
        return redirect(url_for('auth.admin_users'))

    update_department_status(department_id, status)
    log_activity(current_user.id, f'department_status:{department_id}:{status}')
    if wants_json:
        return jsonify({'updated': department_id, 'name': dept[1], 'status': status})
    flash(f'"{dept[1]}" set to {status}.', 'success')
    return redirect(url_for('auth.admin_users'))


def _wants_json():
    """True when the client asked for JSON (AJAX) instead of PRG redirect."""
    return 'application/json' in (request.headers.get('Accept') or '')


@auth_bp.route('/logout')
@login_required
def logout():
    log_activity(current_user.id, 'logout')
    logout_user()
    return redirect(url_for('auth.login'))
