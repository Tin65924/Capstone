# Cataloging Module — Technical Documentation

## Blueprint
`cataloging_bp` — registered at no prefix (`/cataloging`, `/catalog`, `/book/*`)

## Database Schema

### `book_catalog` tuple index map (SELECT *)
| Index | Column | Type | Notes |
|-------|--------|------|-------|
| 0 | `book_id` | int | PK |
| 1 | `title` | str | NOT NULL |
| 2 | `author` | str | NOT NULL |
| 3 | `edition` | str\|None | |
| 4 | `publisher` | str\|None | |
| 5 | `year_published` | int\|None | |
| 6 | `subject_classification` | str\|None | |
| 7 | `call_number` | str\|None | |
| 8 | `isbn` | str\|None | |
| 9 | `material_type` | str | defaults `'Book'` |
| 10 | `description` | str\|None | |
| 11 | `catalog_status` | str | `'active'` or `'archived'` |
| 12 | `date_added` | date (str) | ISO format |

### `accession_log` tuple index map (SELECT *)
| Index | Column | Type | Notes |
|-------|--------|------|-------|
| 0 | `accession_id` | int | PK |
| 1 | `accession_number` | str | UNIQUE |
| 2 | `book_id` | int | FK → `book_catalog` |
| 3 | `copy_number` | int\|None | |
| 4 | `librarian_id` | int | FK → `user_accounts` |
| 5 | `date_accessioned` | date (str) | |
| 6 | `source` | str\|None | `'purchase'` or `'donation'` |

## Endpoints

| Method | Path | Decorators | Query Params | Description |
|--------|------|------------|-------------|-------------|
| GET | `/cataloging` | `@login_required @librarian_required` | `q`, `field`, `page` | Librarian catalog listing with search + pagination |
| POST | `/cataloging/add` | `@login_required @librarian_required` | — | Create a new book. Validates title+author required |
| POST | `/cataloging/<int:book_id>/edit` | `@login_required @librarian_required` | — | Update book metadata. 404 if book not found |
| POST | `/cataloging/<int:book_id>/status` | `@login_required @librarian_required` | — | Toggle `catalog_status` between `'active'` and `'archived'` |
| POST | `/cataloging/<int:book_id>/accession/add` | `@login_required @librarian_required` | — | Add copy. Checks duplicate `accession_number`, validates required |
| POST | `/cataloging/bulk-import` | `@login_required @librarian_required` | — | CSV upload (10MB max, 30+ header synonyms, multi-encoding) |
| GET | `/catalog` | public | `q`, `field` | Public catalog — all books / filtered search |
| GET | `/book/<int:book_id>` | public | — | Single book detail + accession list |

## Route Handler Details

### `cataloging_page()`
- If `query` present, calls `search_books_paginated(query, field, page, per_page=20)` → `(books_list, total)`
- If no query, calls `get_all_books()` → `books_list`, `total = len(books)`
- Renders `cataloging/cataloging.html`

### `add_book()`
- `request.form`: `title`*, `author`*, `edition`, `publisher`, `year_published`, `subject_classification`, `call_number`, `isbn`, `material_type` (default `'Book'`), `description`
- Empty required → flash error + redirect back
- Calls `create_book(...)` then `log_activity(current_user.id, 'cataloging:add_book')`

### `edit_book(book_id)`
- `get_book_by_id(book_id)` — if `None`, flash error + redirect
- Same form fields as add (all optional except title/author same validation)
- Calls `update_book(...)` then `log_activity(current_user.id, f'cataloging:edit_book:{book_id}')`

### `toggle_book_status(book_id)`
- Reads `book[11]` (catalog_status, 0-indexed from `SELECT *`)
- `'active'` → `'archived'`, else → `'active'`
- Calls `update_book_status(book_id, new_status)`

### `add_accession(book_id)`
- `request.form`: `accession_number`*, `copy_number`, `source`
- Validates `accession_number` not empty
- `get_accession_by_number(accession_number)` — if truthy, duplicate error
- Calls `create_accession(accession_number, book_id, current_user.id, source, copy_number)`

### `bulk_import()`
- File validation:
  - File present in `request.files`, filename not empty
  - Extension `.csv` (case-insensitive)
  - Max 10MB (`len(raw) > 10 * 1024 * 1024`)
- Encoding: `_decode_csv(raw)` tries `utf-8-sig` → `utf-8` → `latin-1` → `cp1252`; returns `None` if all fail
- CSV parsing: `csv.DictReader`, checks `fieldnames` not empty
- Header mapping: `_map_headers(fieldnames)` normalizes headers via `HEADER_MAP` (30+ synonyms like `'Book Title'` → `'title'`, `'Author(s)'` → `'author'`)
- Required columns: `'title'` and `'author'` must be in mapped columns
- Per-row: title/author required; `year_published` from `int(year_str)` if digit-only; empty strings → `None`
- `create_book(...)` per valid row; exceptions caught per-row
- `log_activity` with summary: `cataloging:bulk_import:{imported}_success_{errors}_errors`
- Flash: success count; first 10 errors individually; `"... and N more error(s)"` if >10

### `public_catalog()`
- `?q=` → `search_books(query, field=field if field else None)` — field-specialized ILIKE queries
- No q → `get_all_books()`
- Renders `public/catalog.html`

### `book_info(book_id)`
- `get_book_by_id(book_id)` — redirect if None
- `get_accessions_by_book(book_id)` — list of accession tuples
- `get_user_by_id(current_user.id)` — only if authenticated (lazy import)
- Renders `public/bookinfo.html`

## Models Catalog

| Function | Returns | SQL |
|----------|---------|-----|
| `get_all_books()` | `list[tuple]` | `SELECT * FROM book_catalog ORDER BY title` |
| `get_book_by_id(book_id)` | `tuple\|None` | `SELECT * FROM book_catalog WHERE book_id = %s` |
| `search_books(query, field=None)` | `list[tuple]` | ILIKE on one or all of title/author/isbn/subject |
| `search_books_paginated(query, field, page, per_page)` | `(list[tuple], total_count)` | Same WHERE as search + `LIMIT %s OFFSET %s` + `COUNT(*)` |
| `get_recent_books(limit=5)` | `list[tuple]` | `ORDER BY date_added DESC LIMIT %s` |
| `create_book(...)` | int (rowcount) | `INSERT INTO book_catalog (...)` 11 columns |
| `update_book(book_id, ...)` | int (rowcount) | `UPDATE book_catalog SET ... WHERE book_id=%s` |
| `update_book_status(book_id, status)` | int (rowcount) | `UPDATE book_catalog SET catalog_status=%s WHERE book_id=%s` |
| `create_accession(acc_num, book_id, lib_id, source, copy_num)` | int (rowcount) | `INSERT INTO accession_log (...)` |
| `get_accessions_by_book(book_id)` | `list[tuple]` | `SELECT * FROM accession_log WHERE book_id = %s ORDER BY copy_number` |
| `get_accession_by_number(acc_number)` | `tuple\|None` | `SELECT * FROM accession_log WHERE accession_number = %s` |
| `add_favorite(user_id, book_id)` | int (rowcount) | `INSERT ... ON CONFLICT DO NOTHING` |
| `remove_favorite(user_id, book_id)` | int (rowcount) | `DELETE FROM user_favorites WHERE ...` |
| `get_user_favorites(user_id)` | `list[tuple]` | JOIN `book_catalog` + `user_favorites` ORDER BY `favorites.created_at DESC` |

## Bulk Import Technical Details

### `HEADER_MAP` (30+ synonyms)
Maps normalized header names (`strip().lower().replace('_',' ').replace('-',' ')`) to db column keys:
- `'title'`: `title`, `book title`, `book_title`, `name`
- `'author'`: `author`, `authors`, `creator`, `author(s)`
- `'isbn'`: `isbn`, `isbn-13`, `isbn13`, `isbn 13`
- `'edition'`: `edition`, `ed`
- `'publisher'`: `publisher`, `publishers`
- `'year_published'`: `year`, `year published`, `year_published`, `publication year`, `publication_year`, `pub year`
- `'subject_classification'`: `subject`, `subjects`, `subject classification`, `subject_classification`, `category`
- `'call_number'`: `call number`, `call_number`, `call no`
- `'material_type'`: `material type`, `material_type`, `type`, `material`, `format`
- `'description'`: `description`, `desc`

### `_normalize_header(name)`
1. `strip().lower()`
2. Replace `_` and `-` with spaces
3. Collapse multiple spaces

### `_decode_csv(raw)`
Tries encodings in order: `utf-8-sig` → `utf-8` → `latin-1` → `cp1252`. Returns decoded string or `None`.

### `_map_headers(fieldnames)`
Returns `dict[str, str]` mapping original CSV header → db column key. Unmapped headers are excluded.

### CSV validation chain
1. File present + non-empty filename
2. `.csv` extension
3. Size ≤ 10MB
4. Decodable content
5. Non-empty line count
6. Has `fieldnames` (headers)
7. `column_map` contains at least `title` and `author`

## Template Files Referenced
- `cataloging/cataloging.html` — librarian page (search results table, add/edit/accession/bulk modals)
- `public/catalog.html` — public search/discover
- `public/bookinfo.html` — single book detail + accession copies
- `public/index.html` — landing page (consumes `new_arrivals`)

## Important Tuple Indexing Notes
- `book[11]` = `catalog_status` (used in `toggle_book_status`)
- `book[0]` = `book_id` (used in templates for URLs)
- `book[1]` = `title`, `book[2]` = `author`
- Accession tuple: `ac[0]` = id, `ac[1]` = accession_number, `ac[2]` = book_id, `ac[3]` = copy_number

## Test Coverage
`tests/test_cataloging.py` — 422 lines, 45 tests:
- `TestCatalogingAccess` (5): RBAC — student(403), faculty(403), librarian(200), admin(200), unauthenticated(302)
- `TestCatalogingCRUD` (8): add book success/missing-title/missing-author, edit success/not-found, toggle archive/not-found, add accession success/duplicate/missing-number
- `TestCatalogingSearch` (4): by title, by author, no results, pagination
- `TestPublicCatalog` (6): all/search/no-results, book-info found/not-found/with-accessions
- `TestBulkImport` (20): RBAC (3), edge cases (6), success (1), header order (1), synonyms (1), partial errors (1), utf-8-bom (1), latin-1 (1), unicode (1), no headers (1), whitespace headers (1), large file 500 rows (1), extra unknown headers (1)
