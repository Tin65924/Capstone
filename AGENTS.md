# AGENTS.md

Flask 3.1 library management system (MCST LMS). Server-rendered Jinja2 + Tailwind templates, PostgreSQL via raw psycopg2 (no ORM), Google OAuth + Flask-Login auth. Deployed on Render.

- Run the app with `python run.py` from repo root (use the repo venv: `venv\Scripts\python.exe`). Binds `0.0.0.0`, port from `PORT` env (default 5000), `debug=False`.
- Run tests with `venv\Scripts\python.exe -m pytest` from repo root. No Postgres needed — `tests/conftest.py` patches `app.database` before app import and the autouse `mock_db` fixture mocks `db.execute/fetch_one/fetch_all` for every test.
- `app/schema.sql` is the source of truth (idempotent, `IF NOT EXISTS`) and is re-applied at every app start by `app/database.py:run_schema`. Do not edit the schema anywhere else.
- The default branch is `main`.
- `.env` is gitignored; only `GOOGLE_OAUTH_CLIENT_ID`/`GOOGLE_OAUTH_CLIENT_SECRET` are in `.env.example`. Locally you also need `OAUTHLIB_INSECURE_TRANSPORT=1`.

## Branch Names

Use a short branch name of at most three words, separated by hyphens. Do not use slashes or type prefixes such as `feat/` or `fix/`.

Examples: `fix-reset-db`, `wire-circulation`, `local-login`.

## Commits and PR Titles

Use conventional commit-style messages and PR titles: `type(scope): summary`. Scope is optional; the existing history mostly omits it.

Valid types are `feat`, `fix`, `docs`, `chore`, `refactor`, and `test`.

Examples: `fix: correct endpoint name main.profile -> main.user_profile`, `feat: merge accession into add/edit book modals`, `chore: add books_copies_extra.csv`.

## Style Guide

### General

- Keep route handlers thin: validate input, flash feedback, redirect. Put all SQL in the module's `models.py`, not in routes.
- All DB access goes through `from app.database import db`. Use `db.fetch_one()` (single row), `db.fetch_all()` (many rows), `db.execute()` (writes; returns rowcount, or rows if the statement is a SELECT). Always use `%s` placeholders — never build SQL with f-strings.
- Do not open raw psycopg2 connections in routes. Only `setup_db.py`, `auth/routes.py:reset_db`, and `backup/utils.py` touch raw connections.
- Gate access with RBAC decorators from `app/auth/decorators.py`: `librarian_required` (Librarian+Admin), `admin_required` (Admin), `faculty_required` (Faculty+Librarian+Admin). Denied requests redirect to `/user/profile`; don't hand-roll `current_user.role` checks in routes.
- Don't blanket-swallow `db.*` errors. `db.execute` rolls back and re-raises (`app/database.py`), and unexpected exceptions surface to the 500 handler in `app/__init__.py` — a generic page, no traceback (debug is off). Still handle *expected* user-driven failures (duplicate accession, FK violations) explicitly with pre-checks, and keep `try/except` for per-row work in background threads (e.g. the bulk-import worker), which have no request error handler.
- Keep template styling as inline Tailwind classes; shared partials live in `app/templates/components/`.

## Module Development Rules

Every module under `app/` must follow these rules — including the not-yet-wired ones (`requests`, `procurement`, `circulation`, `inventory`, `analytics`, `backup`). If a module breaks one of these, treat it as a bug.

### Package Layout

- Each module is a blueprint package: `__init__.py` defines `X_bp = Blueprint('x', __name__, template_folder='../templates/<name>')` and imports `from . import routes` at the bottom; `routes.py` holds handlers only; `models.py` holds all SQL.
- Register every new blueprint in `create_app()` (`app/__init__.py`) — there is no auto-discovery. Missing registration = 404 for the module's URLs.
- Templates live in `app/templates/<module>/`; shared partials in `app/templates/components/` (navbars, modals, flash messages).

### Route Rules

- Handlers are thin: parse/validate input → flash → redirect. Import data functions from the module's `models.py`; never touch `db` or SQL inside a route.
- Guard order matters: `@login_required` first, then the RBAC decorator. Public endpoints (e.g. `/catalog`, `/book/<id>`) get no guard.
- State-changing actions are `POST` only. After handling, `flash(msg, 'success' | 'error' | 'info')` and `redirect(url_for(...))` — never `render_template` after a POST (Post/Redirect/Get).
- Record the audit trail after every write: `log_activity(current_user.id, '<module>:<action>:<target_id>')`.
- Hard delete is archive-then-delete: read `catalog_status` / `account_status` from the fetched tuple and refuse a DELETE unless it is `'archived'`.

### Model Rules

- Reads use `db.fetch_one()` (single row) and `db.fetch_all()` (many rows); writes use `db.execute()`. Always `%s` placeholders — never f-string SQL (except for already-sanitized identifiers, as `search_books` does).
- Return positional tuples; SELECT column order is the contract. Callers index by position.
- Name functions by action: `get_*` for reads, `create_*` / `update_*` / `delete_*` for writes, `count_*` for aggregates.
- SQL goes in the module's `models.py`, never in routes; shared cross-module queries are imported, not re-written (e.g. `get_user_by_id` from `app.auth.models`).

### Tuple Contract

- Model functions return **positional tuples**, not dicts or ORM objects. The SELECT column order is the contract and callers index by position (e.g. book `book[11]` is `catalog_status`; `get_user_by_id` returns `(user_id, email, role_name, full_name)`). Never reorder SELECT columns without updating every caller.
- Archive-before-delete is enforced in routes, so read the status field from the fetched tuple before issuing a DELETE.

## Testing

- Tests exercise routes against mocked DB returns; no database or network. Set `mock_db['fetch_one']` / `mock_db['fetch_all']` / `mock_db['execute']` return values before hitting the endpoint.
- Logged-in clients are `student_client`, `faculty_client`, `librarian_client`, `admin_client` (user ids 1–4, mocked loader in `conftest.py`).
- Assert on `resp.status_code`, `resp.location`, rendered body bytes, and `mock_db` call args (e.g. that the first `execute` was `INSERT INTO book_catalog`).

## Verification

- No linter, formatter, or typechecker is configured and there is no CI. `venv\Scripts\python.exe -m pytest` is the only check.

## Module Status

- `auth`, `cataloging`, and `main` are fully wired. `requests`, `procurement`, `circulation`, `inventory`, `analytics`, and `backup` are **static-UI only**: their routes render templates with no data and their model functions are never called. Don't assume a module works end-to-end; `dev/PROJECT_STATUS.md` (gitignored, local-only) tracks what's stubbed.
- Bulk CSV import (`cataloging/routes.py`) runs in a background thread and polls an in-memory `_import_jobs` dict — no task queue, jobs are lost on restart. Headers map through `HEADER_MAP`; `title`, `author`, and `accession_number` columns are required.
- `auth/routes.py:reset_db` re-adds the `user_accounts.account_status` CHECK with only `('active','disabled','pending')` — missing `'archived'`, inconsistent with `app/schema.sql`. Fix both together if you touch status values.
- Auth is Google OAuth restricted to `@mcst.edu.ph`; the first-ever login auto-creates an Admin.
- `Project_Tracker_Site/` is a static showcase site (fully gitignored), not app code. `books_seed.csv` / `books_copies_extra.csv` at root are bulk-import fixtures. `backups/` holds `pg_dump` output.
