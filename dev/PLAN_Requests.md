# Plan: Requests Module (`app/requests`)

Scope: Module 1 from `PlannedModules.txt` — Request Management Submodule (procurement submodule handled under `app/procurement`).

## Current State

- **Routes are stubs** (`app/requests/routes.py`): `/librarian/requests` and `/user/request-book` render templates with no data and handle no POST.
- **Models exist but are never called** (`app/requests/models.py`):
  - `create_request(requester_id, book_title, author)` — requires `borrower_id`, not `user_id`
  - `get_requests(status)`, `get_request_by_id`, `update_request_status(status, reviewer_id)`
  - `get_demand_count(book_title)`, `get_demand_by_role()`
  - `check_duplicate_request(requester_id, book_title)`, `check_existing_in_collection(book_title)`
- **Schema already supports it** (`app/schema.sql:62`): `request_records` has `requester_id → borrowers(borrower_id)`, `matched_book_id → book_catalog`, `request_status CHECK IN ('pending_review','existing_in_collection','approved','rejected','procured')`, `reviewed_by`, `review_date`.
- **Procurement integration exists** (`app/procurement/models.py`): `create_procurement(request_id)`, `update_procurement_status(...)`, `get_procurement_items(status)`.

## Key gap discovered

`create_request` takes a `requester_id` that must be a **`borrower_id`**, but `current_user.id` is a **`user_accounts.user_id`**. There is **no model that maps `user_id → borrower_id`** anywhere. This blocks the request form.

## Title matching (variants & typos)

Current matching is exact-string (`WHERE title = %s`) — "intro to programming" and "Introduction to Programming" would be separate titles/demand buckets. **Decision: Tier 1 + 2.**

- `normalize_title(title)` util (single source of truth, used everywhere matching happens):
  - lowercase → strip punctuation → collapse whitespace
  - expand curated abbreviations: `intro→introduction`, `prog→programming`, `comp→computer`, `sci→science`, `admin→administration`, etc.
- Matching:
  - `check_existing_in_collection(title)` → normalize → exact match on catalog titles → if none, fuzzy `difflib.SequenceMatcher` (ratio ≥ 0.85) against candidate titles.
  - `check_duplicate_request(user, title)` → compare normalized; fuzzy only for cross-user requests (variants by *different* users still increment demand rather than creating a new bucket).
- Demand aggregation: `get_demand_count` / `get_demand_by_role` group by the normalized title (single canonical key per logical book).
- No schema change for this decision (no `normalized_title` column — Tier 3 deferred).

## Data Flow

### Flow A — Student/Faculty submits a request

1. User (Student/Faculty) opens `/user/request-book` (GET) → page renders the request form.
2. User enters **Book Title** (required) and **Author** (optional) → clicks **Submit Request**.
3. Browser sends `POST /user/request-book` with `{book_title, author}` + CSRF token.
4. Route (server):
   a. Verifies login (`@login_required`) and that the user has a borrower row (`get_borrower_by_user(user_id)`).
   b. Validates `book_title` non-empty.
   c. `check_existing_in_collection(title)` → title already in `book_catalog`? → flash "already in collection" + link to catalog → **stop**.
   d. `check_duplicate_request(borrower_id, title)` → same user already requested this title? → flash "already requested" → **stop**.
   e. `create_request(borrower_id, title, author)`:
      - INSERT into `request_records` (`requester_id`, `book_title`, `author`, `request_status`, `request_date`).
      - status = `'pending_review'` (or `'existing_in_collection'` + `matched_book_id` if matched in step c — c blocks, so normally `pending_review`).
   f. Flash success → redirect `GET /user/request-book`.
5. Page re-renders → "My Requests" section (`get_requests_by_borrower(borrower_id)`) now shows the new row with status badge `Pending Review`.

Data written: `request_records` (1 row).

### Flow B — Librarian reviews pending requests

1. Librarian opens `/librarian/requests` (GET) → route calls `get_requests_with_details()` (joins `request_records` + `borrowers` + `user_accounts` + `book_catalog`) → renders cards (title, author, requester name/role/department, demand count, status badge, actions).
2. Librarian clicks **Approve** on a card → `POST /librarian/requests/<id>/status` with `action=approved`.
3. Route (`@librarian_required`, CSRF-checked):
   a. `get_request_by_id(id)` → 404 if missing.
   b. `update_request_status(id, 'approved', reviewer=current_user.id)` → sets `request_status='approved'`, `reviewed_by`, `review_date=NOW()`.
   c. `create_procurement(id)` → INSERT into `procurement_log` (`request_id`, `order_status='for_ordering'`, `order_date=today`).
   d. Flash success → redirect `/librarian/requests`.
4. Librarian clicks **Reject** → `POST /librarian/requests/<id>/status` with `action=rejected` (+ optional `remarks`).
5. Route:
   a. `update_request_status(id, 'rejected', reviewer=current_user.id)`.
   b. If `remarks` → UPDATE `request_records.remarks`.
   c. No `procurement_log` row is created.
6. Card moves to the Rejected filter tab; request status shows on the user's "My Requests".

Data written: `request_records` (status/reviewer/review_date/remarks), `procurement_log` (only on approve).

### Flow C — Demand / status monitoring (read-only)

1. Any librarian request to `/librarian/requests?status=<filter>`:
   - `get_requests_with_details()` filtered by `request_status` → list.
2. Demand counts per title: `get_demand_count(title)` (COUNT of all `request_records` rows for the title) and `get_demand_by_role()` (Student vs Faculty counts grouped by title).
3. Dashboard/KPI views can call the same models for the analytics module later.

Data read: `request_records`, `borrowers`, `user_accounts`, `roles`, `book_catalog`.

## Phase 1 — Missing foundation (models)

- New model in `app/requests/models.py`: `get_borrower_by_user(user_id)` → returns borrower row or None (needed by request form; also reusable by circulation later).
- Extend `create_request` to accept `matched_book_id` and to auto-set status:
  - If `check_existing_in_collection(title)` → status `'existing_in_collection'` and set `matched_book_id`.
  - Else status `'pending_review'`.
- Add `remarks VARCHAR(255)` column to `request_records` (idempotent ALTER in `run_schema`) for rejection reasons.
- Add `get_requests_with_details()` — join `request_records` + `borrowers` + `user_accounts` + `book_catalog` so the librarian view shows requester name/role, and matched book info.

## Phase 2 — Student/Faculty request form (POST `/user/request-book`)

- Fix template `user_request_book.html`:
  - Form has `name="book-title"` but code needs `book_title` — unify to `book_title` (or read both).
  - `method="POST"`, `action="{{ url_for('requests.user_request_book') }}"`.
- Route logic:
  1. `@login_required`, must have a borrower row (Students/Faculty only — Admins/Librarians get a friendly error).
  2. Validate title non-empty.
  3. **Duplicate title detection** (professor spec): `check_existing_in_collection` → if already in catalog, block with message pointing to catalog. `check_duplicate_request` → if already requested by this user, block with "already requested".
  4. `create_request(borrower_id, title, author)` → auto-status as above.
  5. Flash success + redirect to `/user/request-book`.
- Add a "My Requests" section below the form: `get_requests_by_borrower(borrower_id)` (new model) showing title, status badge, date.

## Phase 3 — Librarian review view (`/librarian/requests`)

- Route: fetch `get_requests_with_details()` + filter by `?status=` query param (Pending / Approved / Rejected / Procured / Existing).
- Header stats: total, pending count, demand counts.
- Replace static cards in `requests.html` with loop over data:
  - Title, author, requester name + role + department
  - Demand count per title (`get_demand_count`)
  - Status badge
  - Action buttons per status (Approved / Reject; Reject needs a reason → optional `remarks`)
- Actions (all POST, `@librarian_required`, CSRF-protected):
  - `POST /librarian/requests/<id>/status` with `action=approved|rejected`
  - On **approve**: `update_request_status(id, 'approved', reviewer=current_user.id)` + optional `create_procurement(id)` in `procurement_log` (`for_ordering`) so it flows into the Procurement module.
  - On **reject**: `update_request_status(id, 'rejected', reviewer)`.
- Detail modal (reuse "View Details" buttons): shows full request info + matched book if `existing_in_collection`.

## Phase 4 — Demand / status monitoring

- `get_demand_by_role()` already aggregates student vs faculty counts per title — wire into librarian view and optionally the dashboard.
- Add status filter tabs (Pending / Approved / Rejected / Existing / Procured) mirroring the users page style.

## Phase 5 — Faculty supplier-list flow (from professor spec)

**Decision: Minimal — hint only.** Faculty submits the same title/author form. The system flags whether the title is already in the collection (or in the local CSV list) as a hint, with no new `supplier_catalog` table. Full supplier-list matching is deferred until Procurement module work.

## Phase 6 — Tests (`tests/test_requests.py`)

- `get_borrower_by_user` returns correct row / None.
- Request submission: success (pending_review), existing-in-collection auto-tag, duplicate blocked (own request), empty title rejected, non-borrower (Admin) blocked.
- Librarian approve → status approved **and** `procurement_log` row created (`for_ordering`); reject → rejected with reviewer + optional remarks.
- `get_demand_count` / `get_demand_by_role` correct after multiple requests.
- CSRF present on all POST routes.
- Regression: `python -m pytest -q`.

## Decisions (confirmed)

1. Faculty supplier flow: **Minimal — hint only** (no new table).
2. Approve → **auto-create `procurement_log` row** (`for_ordering`).
3. **Add `remarks` column** to `request_records` for rejection reasons.
4. Title matching: **Tier 1 + 2** — normalization + fuzzy (difflib), no schema change.

## Security notes (applies here too)

- CSRF tokens on all POST forms (global `CSRFProtect` from auth plan).
- Validate status transitions — librarian can only set valid statuses; never accept a status string from the client.
- `requester_id` comes from server-side `current_user` → borrower mapping, never from the form (prevents spoofing another user's request).
- Bound `matched_book_id` to a real `book_catalog` row via server check.
