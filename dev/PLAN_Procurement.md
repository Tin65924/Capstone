# Plan: Procurement Module (`app/procurement`)

Scope: Module 1B from `PlannedModules.txt` — Procurement Management Submodule (status tracking for approved requests). Ties into Requests (approve → create) and Cataloging (procured → accessioned).

## Current State

- **Routes are stubs** (`app/procurement/routes.py`): `/librarian/procurement` renders `procurement.html` with no data, no POST handlers.
- **Models are written and mostly sound** (`app/procurement/models.py`):
  - `get_procurement_items(status=None)` — optional status filter; joins `procurement_log` + `request_records` for title/author.
  - `create_procurement(request_id)` — INSERT `for_ordering`, `order_date=today`.
  - `update_procurement_status(id, order_status, remarks, date_received, book_id)` — updates status + optional fields.
  - `VALID_STATUSES = ['for_ordering', 'ordered', 'delivered', 'cancelled', 'out_of_stock', 'procured']`.
- **Schema** (`app/schema.sql:78`): `procurement_log (procurement_id, request_id FK→request_records, order_status CHECK IN (6 statuses), order_date, date_received, book_id FK→book_catalog, remarks)`.
- **Already connected from Requests plan**: approve → `create_procurement(id)` (decision #2 in `PLAN_Requests.md`). So procurement items appear automatically when requests are approved.
- **Template** `procurement.html` is static: 3 hardcoded cards, status dropdowns with only 3 options (schema has 6), no real data.

## Key gaps

1. **No "procured → catalog" handoff.** The professor's flow is Request → Procurement Status → **Accessioning → Cataloging**. When a book is marked `procured`, it should create a `book_catalog` row + `accession_log` entry so it becomes searchable. No model does this.
2. **No status-change POST handler.** The template's dropdown is decorative.
3. **No status filter on the view** (though `get_procurement_items(status)` supports it).
4. **No stats** — total / per-status counts for the dashboard.
5. `order_date` is NOT NULL and always today on create — fine, but date_received should be auto-set when transitioning to `delivered`.

## Decisions (confirmed)

1. **Cancelled / out_of_stock → reject the request**: also sets linked `request_records.status = 'rejected'` with a remark, closing the request lifecycle.
2. **Procured → inline accession, two outcomes**:
   - Librarian fills the modal with book details + accession → `create_book` + `create_accession`, link `procurement_log.book_id`, procurement status = **`cataloged`**, request status = `procured`.
   - Librarian submits **without details** → procurement status stays **`procured`** (book not in catalog yet); an "Accession Book" button remains to complete it later.
3. **New status `cataloged`**: add to `procurement_log.order_status` CHECK (idempotent ALTER in `run_schema`). Existing 6 + `cataloged` = 7.
4. `request_records.status = 'procured'` when the book is accessioned (closes the lifecycle).

## Data Flow

### Flow A — Approve request → procurement item appears (from Requests plan)

1. Librarian approves a request (`POST /librarian/requests/<id>/status`, action=approved).
2. Route: `update_request_status(id, 'approved', reviewer)` **and** `create_procurement(id)` → INSERT `procurement_log (request_id, order_status='for_ordering', order_date=today)`.
3. Item now appears in `/librarian/procurement` under "For Ordering".

Data written: `procurement_log` (1 row). Data read: `request_records` (title/author on the dashboard join).

### Flow B — Librarian views procurement dashboard

1. `GET /librarian/procurement` → `get_procurement_items(status?)` → cards with title, author, status badge, order date, remarks.
2. Header stats: total items + per-status counts (`get_procurement_counts()`, new model).
3. Filter tabs/links: All / For Ordering / Ordered / Delivered / Cancelled / Out of Stock / Procured → `?status=` param.

Data read: `procurement_log`, `request_records`.

### Flow C — Update procurement status

1. Librarian changes the dropdown on a card → `POST /librarian/procurement/<id>/status` with `{order_status, remarks?}`.
2. Route:
   a. Validate `order_status in VALID_STATUSES` (never trust client).
   b. If `order_status in ('delivered', 'procured')` → set `date_received = today` automatically (unless provided).
   c. If `order_status in ('cancelled', 'out_of_stock')` → also **reject the linked request** (`update_request_status(request_id, 'rejected', reviewer, remarks)`).
   d. If `order_status == 'procured'` → **inline accession modal** (Flow D) — status only becomes `cataloged` if details are provided; otherwise stays `procured`.
   e. `update_procurement_status(id, order_status, remarks, date_received)`.
   f. `log_activity(current_user.id, 'procurement_status:...')`.
   g. Flash + redirect.
3. Card badge + filter tabs update.

Data written: `procurement_log` (status/remarks/date_received), possibly `request_records`.

### Flow D — Procured → book accessioned into catalog (two outcomes)

When order status moves to `procured`, an **inline modal** opens with optional book details + accession number:

1. **Librarian fills details + accession number** → submit:
   a. Validate title/author required; `get_accession_by_number(accession_number)` → duplicate → error.
   b. `create_book(...)` → `book_id`; `create_accession(accession_number, book_id, current_user.id, source='purchase')`.
   c. UPDATE `procurement_log SET book_id = <id>`, `order_status = 'cataloged'`.
   d. UPDATE `request_records SET request_status = 'procured'`.
   e. Book is now searchable in the catalog; inventory sees the new accession.
2. **Librarian submits without details** → `update_procurement_status(id, 'procured')` only; `book_id` stays NULL; request stays `approved`. Card keeps an "Accession Book" button to run step 1 later.
3. **Accession later**: "Accession Book" button → same modal/form → completes step 1 (idempotent — skipped if `book_id` already set).

Data written: `book_catalog`, `accession_log`, `procurement_log` (book_id/status), `request_records` (status).

## Phases

### Phase 1 — Models + schema

- **Schema**: idempotent ALTER — add `'cataloged'` to `procurement_log.order_status` CHECK (drop + re-add constraint, as done for `account_status`).
- New `get_procurement_counts()` → per-status counts + total.
- New `get_procurement_by_id(procurement_id)` → single item w/ request info (for the accessioning modal + status form).
- New `mark_request_procured(request_id)` → `UPDATE request_records SET request_status='procured'`.
- New `complete_procurement_accession(procurement_id, request_id, book_id)` → set `book_id` + `order_status='cataloged'` + mark request procured (single transaction).
- Update `VALID_STATUSES` to include `'cataloged'`.
- Keep `create_procurement`, `update_procurement_status`, `get_procurement_items` as-is (they're correct).

### Phase 2 — Dashboard routes

- `GET /librarian/procurement` → real data (stats + filtered items).
- `POST /librarian/procurement/<id>/status` → Flow C (validation, date_received, cancelled→reject request, procured→modal).
- `POST /librarian/procurement/<id>/accession` → Flow D step 1 (create book + accession, link book_id, cataloged, request procured).

### Phase 3 — Template rewiring

- Header stats cards (total + status counts).
- Filter tabs (All + 7 statuses incl. Cataloged).
- Cards loop over `items`:
  - title, author (from join), status badge (color per status), order date, remarks.
  - Status dropdown → real `<form method="POST">` per card (CSRF token) → submits to `/librarian/procurement/<id>/status`.
  - Selecting "Procured" → inline modal (Flow D) with optional book details + accession number.
  - If status `procured` and `book_id` is NULL → "Accession Book" button reopens the modal.
- Keep existing visual style; reuse `flash_messages.html`.

### Phase 4 — Tests (`tests/test_procurement.py`)

- `get_procurement_counts` correct totals.
- Status update: valid status → row updated + date_received set on delivered/procured; invalid status → rejected.
- Cancelled/out_of_stock → linked request rejected with remark.
- Accession flow (full): creates book + accession, links `procurement_log.book_id`, status `cataloged`, request marked procured.
- Accession flow (no details): status stays `procured`, `book_id` NULL, request stays approved.
- Accession idempotent: second call skipped when `book_id` set.
- CSRF on all POST routes.
- Regression: `python -m pytest -q`.

## Security notes

- CSRF tokens on all POST forms (global `CSRFProtect` from auth plan).
- `order_status` validated against `VALID_STATUSES` server-side — never accept arbitrary strings.
- All routes `@librarian_required`.
- Accession form fields validated (title/author required, accession unique check via `get_accession_by_number`).
