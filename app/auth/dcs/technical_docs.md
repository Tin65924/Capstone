# Authentication Module — Technical Documentation

## Blueprint
`auth_bp` — registered at no prefix (`/login`, `/logout`, `/admin/users`)

## Endpoints

| Method | Path | Decorators | Description |
|--------|------|------------|-------------|
| GET | `/login` | — | Renders `auth/login.html` |
| GET | `/login/google` | — | Initiate OAuth: builds `Flow`, stores `_oauth_state` in session, redirects to Google |
| GET | `/login/google/callback` | — | OAuth callback: verifies state, exchanges code, verifies ID token, logs in or redirects to role-select |
| GET | `/login/role-select` | — | Renders `auth/role_select.html` if session has `_google_oauth_data` |
| POST | `/login/role-select` | — | Creates user record, assigns role, logs in or shows pending |
| GET | `/logout` | `@login_required` | Calls `logout_user()`, logs activity, redirects to `/login` |
| GET | `/admin/users` | `@login_required @librarian_required` | Lists all users, pending users, role counts |
| POST | `/admin/users/<id>/approve` | `@login_required @librarian_required` | Sets `account_status='active'` |
| POST | `/admin/users/<id>/toggle-status` | `@login_required @admin_required` | Toggles `account_status` active/disabled |
| POST | `/admin/users/<id>/role` | `@login_required @admin_required` | Changes `role_id` |

## Route Handler Details

### `google_login()`
- Calls `_build_flow()` (wraps `Flow.from_client_config`)
- Sets `session['_oauth_state']` = CSRF state from `flow.authorization_url()`
- On exception: logs error, flashes failure message, redirects to `/login`

### `google_callback()`
- Pops `session['_oauth_state']` — rejects if missing
- Calls `_build_flow()` with `_external=True` redirect URI
- Calls `flow.fetch_token(authorization_response=request.url)`
- Verifies ID token via `id_token.verify_oauth2_token()` with 30s clock skew
- Checks `id_info['iss']` ∈ `('accounts.google.com', 'https://accounts.google.com')`
- Enforces `@mcst.edu.ph` domain via `_allowed_email()`
- Looks up user by `oauth_sub` → if found, `login_user()`, redirect
- Looks up by email → if found, flash "already registered", redirect
- If `get_admin_count() == 0`: creates user as Admin (role_id=4), auto-login, redirect dashboard
- Otherwise: stores `{email, oauth_sub, full_name}` in `session['_google_oauth_data']`, redirects to `/login/role-select`

### `role_select()` (POST)
- Reads `oauth_data` from `session['_google_oauth_data']`
- Validates `role_name` in `('Student', 'Faculty')`
- Calls `get_role_by_name(role_name)` — uses `role[0]` for role_id
- Checks for existing user by `oauth_sub` or email
- **Faculty**: calls `create_pending_user()` (status=disabled), renders pending_approval
- **Student**: calls `create_user()` (status=active), creates borrower, `login_user()`, redirects dashboard

### `approve_user_route()`
- Calls `approve_user(user_id)` → `UPDATE account_status = 'active'`

### `toggle_user_status_route()`
- Calls `toggle_user_status(user_id)` → reads current status, flips it

### `change_user_role()`
- Reads `role_id` from form, calls `update_user_role()`

## Model Functions

| Function | SQL | Returns | Notes |
|----------|-----|---------|-------|
| `get_user_by_id(uid)` | `SELECT u.user_id, u.email, r.role_name, u.full_name FROM user_accounts u JOIN roles r ON u.role_id = r.role_id WHERE u.user_id=%s AND u.account_status='active'` | `(id, email, role, name)` or `None` | Used by Flask-Login `load_user` |
| `get_user_by_email(email)` | Same SELECT without status filter | `(id, email, role, name)` or `None` | |
| `get_user_by_oauth_sub(sub)` | Same SELECT with `u.oauth_sub=%s` | tuple or `None` | |
| `create_user(...)` | `INSERT ... RETURNING user_id` | `int` or `None` | Status=`active` |
| `create_pending_user(...)` | Same INSERT with status=`disabled` | `int` or `None` | |
| `create_borrower(uid, id_num, dept)` | `INSERT INTO borrowers ...` | `None` (execute) | |
| `get_role_by_name(name)` | `SELECT role_id, role_name FROM roles WHERE role_name=%s` | `(id, name)` or `None` | Role names are case-sensitive: `'Student'`, `'Faculty'`, `'Librarian'`, `'Admin'` |
| `get_admin_count()` | `SELECT COUNT(*) FROM user_accounts u JOIN roles r ... WHERE r.role_name='Admin' AND u.account_status='active'` | `int` | |
| `get_all_users()` | 8-column JOIN with borrowers | list of tuples | `u[0]=id, u[1]=email, u[2]=name, u[3]=role, u[4]=status, u[5]=created_at, u[6]=id_number, u[7]=dept` |
| `get_pending_users()` | Same JOIN with `status='disabled'` | list of 7-element tuples | `p[4]` = `created_at` (datetime) |
| `log_activity(uid, activity, token)` | `INSERT INTO audit_trail ...` | `None` | |

## Important Technical Notes

- **`load_user` in `app/extensions.py`**: calls `User(*get_user_by_id(user_id))` — the tuple unpacking means `get_user_by_id` MUST return exactly `(id, email, role_name, full_name)` or `None`
- **Role names are case-sensitive strings**: `'Student'`, `'Faculty'`, `'Librarian'`, `'Admin'` — checked in decorators and templates with `==`, never `in`
- **`SESSION_OAUTH_KEY`** = `'_google_oauth_data'` (module-level constant)
- **`current_user`** is a `LocalProxy` — use `current_user.id` (str) and `current_user.role` (str)
- **First-user bootstrap**: if `get_admin_count() == 0`, the first registrant bypasses role-select and is created as Admin

## Decorators (`app/auth/decorators.py`)

| Decorator | Allows | Implementation |
|-----------|--------|----------------|
| `@login_required` | Any authenticated user | Flask-Login, redirects to `/login?next=...` |
| `@librarian_required` | Librarian, Admin | Aborts 403 if role not in `('Librarian', 'Admin')` |
| `admin_required` | Admin only | Aborts 403 if role != `'Admin'` |

## Template Files Referenced
- `auth/login.html`
- `auth/role_select.html`
- `auth/pending_approval.html`
- `users/users.html`

## Test Coverage
`tests/test_auth.py` — 24 tests covering: login page render, Google OAuth redirect/callback/exception, domain blocking, first-user admin, role selection (Student/Faculty/invalid), logout, user management RBAC (librarian/admin approval, toggle-status, role change)
