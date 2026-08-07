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
| GET | `/api/bloom` | — | Serialized Bloom filters (`book_record`, `student_record`) used as a local pre-filter for duplicate-record checks. Public |
| GET | `/api/suggestions` | — | Autosuggestion values for `book_title`, `book_author`, `book_publisher`, `book_subject`, `book_isbn`, `book_search`, `student_program` (`?field=&q=`). Public |
| GET | `/api/book-exists` | — | Duplicate book check (`?title=&author=&isbn=`), mirrors the `get_book_by_title_author_isbn` dedup rule. Public |
| GET | `/api/student-exists` | — | Duplicate student check (`?id_number=`). Public |

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

### `bloom_filters()`
- Returns `jsonify(bloom_registry.get_payloads())` — composite record filters: `book_record` (`title SEP author SEP isbn` per book, blank ISBN matches null-ISBN books) and `student_record` (borrower `id_number`s)
- Each payload is `{m, k, bits}` where `bits` is base64 of the packed bit array; `app/static/js/autosuggest.js` decodes it and checks membership locally
- Filters are built lazily from the DB on first access and rebuilt after a write calls `bloom_registry.mark_dirty()` (see `app/bloom_registry.py`)
- Preliminary check only — a `False` result skips the confirming DB query, a `True` result is confirmed against `/api/book-exists` / `/api/student-exists`

### `suggestions()`
- Valid `field` values in `SUGGEST_FIELDS`; requires `len(q) >= 2`, returns up to 8 distinct matching values (`ILIKE prefix%`, ordered)
- `student_program` reads `borrowers.department` (`auth.models.suggest_programs`); all book fields read `book_catalog` (`cataloging.models.suggest_book_values`); `book_search` unions title/author/subject/isbn

### `book_exists()` / `student_exists()`
- Thin: require the identifying inputs, delegate to `get_book_by_title_author_isbn` / `get_user_by_id_number`, return `{'exists': bool}`

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

## Autosuggestions & Duplicate Feedback (cross-cutting)
- Server: `app/bloom.py` (BloomFilter, FNV-1a double hashing) + `app/bloom_registry.py` (composite record filters, lazy build, `mark_dirty()` on writes); suggestion/exists queries live in `cataloging/models.py` and `auth/models.py`
- Client: `app/static/js/autosuggest.js` — inputs with `data-suggest="<field>"` get a debounced suggestion dropdown; forms with `data-exists-book` / `data-exists-student` show `data-exists-msg` feedback only for confirmed duplicate records
- Suggestion fields: book search bar, book Title/Author/Publisher/Subject/ISBN in the Add Book modal, and Program/Department on `role_select.html`; NOT on accession number or student name
- Keyboard: Tab / Enter / Right Arrow accept the highlighted (first) suggestion; Tab then advances to the next field; ArrowUp/Down move the highlight; Escape closes

## Test Coverage
`tests/test_main.py` — 12 tests covering: landing page render/shows arrivals, dashboard redirect/access (all 4 roles + unauthenticated), user profile redirect/access, history access, `/users` redirect to `/admin/users`
