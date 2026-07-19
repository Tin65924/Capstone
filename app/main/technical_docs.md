# Main Module — Technical Documentation

## Blueprint
`main_bp` — registered at no prefix (`/`, `/dashboard`, `/users`, `/user/*`)

## Endpoints

| Method | Path | Decorators | Description |
|--------|------|------------|-------------|
| GET | `/` | — | Landing page. Calls `get_recent_books(5)`, renders `public/index.html` |
| GET | `/dashboard` | `@login_required` | Student/Faculty → redirect to `/user/profile`. Librarian/Admin → renders `dashboard/dashboard.html` |
| GET | `/users` | `@login_required` | Legacy redirect to `auth.admin_users` (`/admin/users`) |
| GET | `/user/profile` | `@login_required` | Librarian/Admin → redirect to `/dashboard`. Student/Faculty → calls `get_user_by_id(current_user.id)`, renders `users/user_profile.html` |
| GET | `/user/history` | `@login_required` | Renders `users/user_history.html` |

## Route Handler Details

### `index()`
- Calls `get_recent_books(5)` from `cataloging.models` to fetch newest 5 books
- Renders `public/index.html` with `new_arrivals` list
- No authentication required — fully public

### `dashboard()`
- Role check uses `current_user.role` (string comparison)
- `current_user.role in ('Student', 'Faculty')` → redirect to user profile
- Otherwise renders dashboard template (for Librarian/Admin)
- The template expects data from `get_all_books()` / dashboard stats (mocked in tests)

### `user_profile()`
- Role redirect: `current_user.role in ('Librarian', 'Admin')` → dashboard
- Calls `get_user_by_id(current_user.id)` which returns a tuple `(user_id, email, role_name, full_name)` — accesses via tuple indexing in template
- Renders `users/user_profile.html` with `user_data` tuple

### `user_history()`
- Renders static template `users/user_history.html`
- Passes no additional context (template can access `current_user` from Flask-Login)

## Important Technical Notes

- **Role string comparison**: uses `in ('Student', 'Faculty')` and `in ('Librarian', 'Admin')` — case-sensitive
- **`user_data` is a tuple** (not dict): template must use `user_data[0]` (id), `user_data[1]` (email), `user_data[2]` (role), `user_data[3]` (name)
- **`get_user_by_id`** imported locally inside `user_profile()` — lazy import to avoid circular dependency
- **`get_recent_books(limit)`** queries `book_catalog ORDER BY date_added DESC LIMIT %s` — query from cataloging models

## Template Files Referenced
- `public/index.html`
- `dashboard/dashboard.html`
- `users/user_profile.html`
- `users/user_history.html`
- `base.html` (extends)
- `navbar.html` (partial)
- `sidebar.html` (partial)

## Test Coverage
`tests/test_main.py` — 12 tests covering: landing page render/shows arrivals, dashboard redirect/access (all 4 roles + unauthenticated), user profile redirect/access, history access, `/users` redirect to `/admin/users`
