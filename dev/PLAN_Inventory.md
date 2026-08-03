# Plan: Inventory Module (`app/inventory`)

Scope: Module 4 from `PlannedModules.txt` — Inventory Monitoring (real-time + annual physical), plus supporting fixes to existing models. Professor item 9 (real-time available copies) is related and noted separately.

## Current State

- **Routes are stubs** (`app/inventory/routes.py`): `/librarian/inventory` renders `inventory.html` with no data, no POST handlers.
- **Models exist but have defects** (`app/inventory/models.py`):
  - `mark_copy_present/missing/lost(accession_id)` — UPDATE `inventory_status`; no-op if no row exists for that accession (no upsert).
  - `mark_copy_damaged(accession_id, notes)` — **BUG**: writes to `book_catalog.notes`, which does **not exist** in `book_catalog` (schema has `description`, no `notes`). Would error.
  - `upsert_inventory_record(accession_id, state, type, checked_by)` — upserts global per-accession row; no session linkage.
  - `reconcile_inventory(session_id, scanned_accessions)` — marks unscanned+not-loaned copies missing; **skips borrowed copies entirely** (neither borrowed nor missing).
  - `create_inventory_session`, `get_session`, `get_active_session`, `update_session_scan`, `end_session` — sessions track progress counts only.
- **Schema** (`app/schema.sql`):
  - `inventory_status`: `inventory_id, accession_id FK, inventory_state CHECK (available, borrowed, lost, damaged, missing), inventory_type CHECK (realtime_scan, annual_physical), checked_by, last_checked_date` — **no `session_id`, no `notes`**.
  - `inventory_sessions`: `session_id, librarian_id, total_books, scanned_count, session_status (active/completed/cancelled), started_at, ended_at`.
- **Reusable pieces**: `get_accession_by_number` (`app/cataloging/models.py:165`), `get_active_loan_by_accession` (`app/circulation/models.py:30`), `get_status_summary`.
- **Template** `inventory.html` is fully static (hardcoded 320/15/45/05/03 and fake rows).

## Decisions (confirmed)

1. **Add `session_id INT REFERENCES inventory_sessions(session_id)`** (nullable) + **`notes VARCHAR(255)`** to `inventory_status` — idempotent ALTERs in `run_schema`. Enables per-session scan history, accurate "Recently Scanned", and per-session discrepancy reports.
2. **Inventory status reflects active loans**: a scanned copy with an active loan → marked `borrowed` (not `available`); an unscanned copy with an active loan during reconcile → marked `borrowed` (not `missing`).
3. **Quick Status Check is read-only** — it shows state but never modifies it. Only the hero "Scan" updates inventory state.
4. **Fix `mark_copy_damaged`** — store notes in `inventory_status.notes` and set `inventory_state='damaged'` (never touch `book_catalog`).
5. **Schema additions**: `inventory_status.session_id`, `inventory_status.notes`.
6. **No Discrepancies/Issues section.** The "Discrepancies / Issues" table is removed entirely. Instead there is **one big paginated scan table** (10 rows/page) with status filter buttons (Present / Missing / Borrowed / Damaged / Lost). The reconcile result is surfaced via flash + the status grid, and the full session is viewable/exportable from this table.
7. **Display**: scan history table = 10 rows/page, newest first, paginated, filterable by state. CSV export for the completed session's report.

## Data Flow

### Flow A — Start a new inventory session

1. Librarian clicks **Start New Session** → `POST /librarian/inventory/session/start`.
2. Route (`@login_required`, `@librarian_required`, CSRF-checked):
   a. Check for an existing active session for this librarian (`get_active_session`) → if found, warn "resume instead" → **stop**.
   b. `total_books = COUNT(accession_log)` (all accessions in system).
   c. `create_inventory_session(current_user.id, total_books)` → INSERT into `inventory_sessions` (`librarian_id`, `total_books`, `scanned_count=0`, `session_status='active'`) RETURNING `session_id`.
   d. Redirect `/librarian/inventory?session_id=<id>`.
3. Page renders with real session data: total books, scanned=0, remaining=total, progress 0%, status grid from `get_status_summary()`.

Data written: `inventory_sessions` (1 row). Data read: `accession_log` (count), `inventory_status` (summary).

### Flow B — Scan an accession (realtime or during a session)

1. Librarian enters/scans an accession number in the hero input → `POST /librarian/inventory/scan` with `{accession_number, session_id?}`.
2. Route:
   a. `get_accession_by_number(number)` → not found → flash "Accession not found" → **stop**.
   b. `get_active_loan_by_accession(acc_id)` → loan present? → `state='borrowed'` else `state='available'`.
   c. `upsert_inventory_record(acc_id, state, 'realtime_scan'|'annual_physical', current_user.id, session_id)` — INSERT or UPDATE the `inventory_status` row, setting `last_checked_date=today`, `checked_by`, and **`session_id`**.
   d. If a session is active → `update_session_scan(session_id)` (scanned_count + 1).
   e. Redirect back (or JS re-render) → the scan-history table (10/page, newest first, filterable) updates live.
3. Status grid + progress bar recompute on reload.

Data written: `inventory_status` (upsert), `inventory_sessions.scanned_count`. Data read: `accession_log`, `circulation_records`, `book_catalog`.

### Flow C — Quick Status Check (read-only)

1. Librarian enters accession number in the "Quick Status Check" box → `POST /librarian/inventory/check`.
2. Route:
   a. `get_accession_by_number(number)` → not found → flash error → **stop**.
   b. Look up current `inventory_status` row for the accession + active loan state.
   c. **No writes.** Render the result card: title (from `book_catalog`), accession, current state (Available/Borrowed/Lost/Damaged/Missing), and whether it's currently loaned.

Data read: `accession_log`, `inventory_status`, `circulation_records`, `book_catalog`. Data written: none.

### Flow D — Complete session (annual physical reconcile)

1. Librarian clicks **Complete Session** → `POST /librarian/inventory/session/<id>/complete`.
2. Route:
   a. Verify session exists + belongs to `current_user`.
   b. `scanned_accessions = get_scanned_in_session(session_id)` — `SELECT accession_id FROM inventory_status WHERE session_id = <id>` (new model).
   c. `reconcile_inventory(session_id, scanned_accessions)`:
      - For every accession in `accession_log`:
        - scanned → upsert `state='available'` (borrowed if active loan).
        - not scanned + **active loan** → upsert `state='borrowed'`.
        - not scanned + no loan → upsert `state='missing'` + add to `discrepancies` list.
      - UPDATE `inventory_sessions` → `scanned_count`, `session_status='completed'`, `ended_at=NOW()`.
   d. Flash "Reconcile complete — N discrepancies" + redirect.
3. Discrepancy count is reflected in the status grid; the full scan table (filtered to Missing) shows which copies are flagged.

Data written: `inventory_status` (bulk upserts), `inventory_sessions`. Data read: `accession_log`, `circulation_records`, `inventory_status`.

### Flow E — Damage / Lost tagging

1. From the discrepancy list (or a status result), librarian clicks **Mark Damaged** (with notes) or **Mark Lost** → `POST /librarian/inventory/accession/<id>/damage` | `/lost`.
2. Route:
   a. `mark_copy_damaged(acc_id, notes)` → UPDATE `inventory_status` set `inventory_state='damaged'`, `notes=<notes>` (fixes the bug). If no row exists, insert first.
   b. `mark_copy_lost(acc_id)` → `inventory_state='lost'` (upsert if missing).
   c. `log_activity(current_user.id, ...)`.
   d. Redirect → status grid updates.

Data written: `inventory_status` (state + notes). Data read: `accession_log`.

### Flow F — Real-time monitoring (dashboards)

- `get_status_summary()` → `SELECT inventory_state, COUNT(*) FROM inventory_status GROUP BY inventory_state` → status grid (Available=Present, Borrowed, Lost, Damaged, Missing).
- Optionally expose the same numbers on the librarian dashboard later.

Data read: `inventory_status`.

## Phases

## Phase 1 — Schema + model fixes

- `run_schema`: idempotent `ALTER TABLE inventory_status ADD COLUMN IF NOT EXISTS session_id INT REFERENCES inventory_sessions(session_id)`, `ADD COLUMN IF NOT EXISTS notes VARCHAR(255)`.
- Fix `mark_copy_damaged` (notes → `inventory_status`, set `damaged`).
- Add `get_scanned_in_session(session_id)`, `get_scan_history(page, per_page, status_filter)` (paged, joined to `accession_log` + `book_catalog`, newest first), `get_accession_status(accession_id)` (title + state + loan info).
- Update `upsert_inventory_record` to accept `session_id` and set it on INSERT/UPDATE.
- Update `reconcile_inventory` to mark borrowed (loaned) copies as `borrowed` instead of skipping them, and to read scanned accessions from the session.

## Phase 2 — Session lifecycle routes

- `POST /librarian/inventory/session/start` → create active session, redirect with `?session_id=`.
- `POST /librarian/inventory/session/<id>/complete` → reconcile + discrepancies.
- `POST /librarian/inventory/session/<id>/cancel` → `session_status='cancelled'`.
- `GET /librarian/inventory` → if `?session_id=` present, show active session data (total/scanned/remaining, progress, recent scans); else show "No active session" state with Start button.

## Phase 3 — Scan + status-check routes

- `POST /librarian/inventory/scan` (writes state, per Flow B).
- `POST /librarian/inventory/check` (read-only, per Flow C).
- `POST /librarian/inventory/accession/<id>/damage` and `/lost` (per Flow E).
- `GET /librarian/inventory/session/<id>/export` → CSV download of the full session scan list + missing copies.

## Phase 4 — Template rewiring

- Replace static values with real data:
  - Status grid from `get_status_summary()`.
  - Progress bar from session `scanned_count / total_books`.
  - **One big scan-history table** — 10 rows/page, newest first, paginated (Prev/Next + page numbers), with status filter buttons (Present / Missing / Borrowed / Damaged / Lost) wired to `?status=` query param. Columns: Accession No., Title, Status, Scanned At (`last_checked_date`).
  - **No Discrepancies/Issues section** — removed; reconcile result surfaces via flash + status grid.
  - Quick Status Check result card from `get_accession_status()`.
  - CSV export button on a completed session (`GET /librarian/inventory/session/<id>/export`).
- All action buttons become real POST forms with CSRF tokens.
- Keep the existing visual style; reuse `flash_messages.html`.

## Phase 5 — Tests (`tests/test_inventory.py`)

- `upsert_inventory_record` inserts then updates the same accession; preserves `session_id`.
- Scan: valid accession → `available`; loaned accession → `borrowed`; unknown accession → rejected.
- Reconcile: scanned → available, unscanned+loaned → borrowed, unscanned+not-loaned → missing + in discrepancies; session marked completed.
- `mark_copy_damaged` writes to `inventory_status.notes` (regression for the `book_catalog.notes` bug).
- Quick check never writes (state unchanged after call).
- Scan-history table pagination: 10/page, correct totals per status filter.
- CSV export returns the completed session's rows.
- CSRF present on all POST routes.
- Regression: `python -m pytest -q`.

## Related — Professor item 9 (real-time available copies)

- The catalog currently shows a static copy count that borrowing doesn't update. Item 9 wants availability computed from `circulation_records` (Total 5, Borrowed 4, Available 1).
- `inventory_status` (this plan) is a **physical shelf state** — different concern from **loan availability**. Keep them separate:
  - Availability for the catalog = `accession_log` count − active loans (computed in cataloging, item 9 work).
  - Inventory state = physical presence (this module).
- Note in the plan: after item 9, the catalog availability badge derives from circulation, not from `inventory_status`.

## Security notes

- CSRF tokens on all POST forms (global `CSRFProtect` from auth plan).
- All routes `@librarian_required`; session ops bound to `current_user.id` (a librarian can't reconcile another's session).
- `accession_number` lookup uses parameterized queries (existing pattern) — no SQL injection.
- Never trust `session_id` from the client — verify it exists and belongs to the user; otherwise default to a fresh session prompt.
