# Plan: Circulation Module (`app/circulation`)

Scope: Module 3 from `PlannedModules.txt` — Borrowing, Returning, Fines/Penalties, Reservations. Includes the reservation page (`/librarian/reservations`).

## Current State

- **Routes are stubs** (`app/circulation/routes.py`): `/librarian/circulation` and `/librarian/reservations` render static templates with no data.
- **Models exist but unused** (`app/circulation/models.py`):
  - `borrow_book(...)`, `return_book(...)`, `get_active_loans_by_borrower`, `get_active_loan_by_accession`, `count_active_loans`, `calculate_fine(...)`, `get_overdue_loans()`, `get_due_within_days(days=2)`, `get_borrowing_frequency`, `get_borrowing_by_program`.
- **Schema** (`app/schema.sql:92`): `circulation_records` with `borrow_type CHECK (overnight|daily_circulation)`, `transaction_status CHECK (active|returned|overdue)`, `fine_amount`, `damage_notes`, `lost_flag`.
- **`reservation_queue` exists** (`:134`): `reservation_id, book_id, borrower_id, queue_position, request_date, status (waiting|allocated|claimed|expired), claim_deadline`. **No model writes it.**
- **`notification_log` exists** (`:145`): `recipient_id, message, notif_type (status_update|hold_ready|overdue_reminder), date_sent`. **Unused.**
- **Rules config** (`app/config.py`): `MAX_BORROW_LIMIT_STUDENT=3`, `MAX_BORROW_LIMIT_FACULTY=10`, `OVERNIGHT_DUE_DAYS=1`, `DAILY_CIRCULATION_DUE_DAYS=7`, `FACULTY_LOAN_DAYS=30`, `OVERDUE_FINE_PER_DAY=10.0`.
- **Reusable pattern**: `app/main/models.py` already reads circulation for the dashboard stats — reuse its join style.
- **Templates** are fully static (hardcoded 42/05/08 stats, fake borrower/book rows; reservations fake counts).

## Key gaps

1. **No borrow/return POST handlers** — UI is decorative.
2. **No `get_borrower_by_user`** helper → can't start a loan at the desk (librarian types student/faculty ID number).
3. **No reservation models** — `reservation_queue` dead.
4. **No notification writes** — `notification_log` unused.
5. **Rules not enforced** — max copies, due-date auto-calc, high-demand daily-only are spec rules with no code.

## Data Flow

### Flow A — Borrower lookup (read-only)

1. Librarian types a borrower ID (e.g. `2024-...`) → `GET /librarian/circulation?search=<id>`.
2. `get_borrower_by_user` (new model, maps id_number→borrower) → returns name, role, department, active-loan count (`count_active_loans`).
3. Render borrower panel + their active loans. No writes.

### Flow B — Borrow a book

1. Librarian scans/enters the book accession number → `POST /librarian/circulation/borrow` with `{borrower_id, accession_number, borrow_type}`.
2. Route (`@librarian_required`, CSRF-checked):
   a. `get_accession_by_number(number)` → not found → error → **stop**.
   b. `get_active_loan_by_accession(acc_id)` → already borrowed → error → **stop**.
   c. `get_borrower_by_user(borrower_id)` + borrower_status → not active → **stop**.
   d. `count_active_loans(borrower_id)` ≥ limit (Student=3, Faculty=10) → **stop**.
   e. **Due date**: `borrow_type='overnight'` → `due_date = today + OVERNIGHT_DUE_DAYS`; `daily_circulation` → `today + DAILY_CIRCULATION_DUE_DAYS`; Faculty+overnight → `FACULTY_LOAN_DAYS`.
   f. `borrow_book(...)`. `log_activity`. Flash.
3. Borrower panel + recent transactions refresh.

Data written: `circulation_records` (1 row).

### Flow C — Return a book

1. Librarian scans the same accession → `POST /librarian/circulation/return` with `{accession_number, damage_notes?, lost?}`.
2. Route:
   a. `get_active_loan_by_accession(acc_id)` → none → "not borrowed" → **stop**.
   b. `calculate_fine(circulation_id, OVERDUE_FINE_PER_DAY)` if overdue.
   c. `return_book(circulation_id, fine, damage_notes, lost_flag)` → `transaction_status='returned'`, `return_date=today`.
   d. If a **reservation** for this book → `create_notification('hold_ready', ...)` to next in queue.
   e. `log_activity`, flash fine → redirect.

Data written: `circulation_records` (update), possibly `notification_log`. Data read: `circulation_records`, `reservation_queue`.

### Flow (reservations)

1. **Create** — user clicks "Reserve" on the catalog → `POST /user/reserve` with `{book_id}` → `create_reservation` (insert into `reservation_queue`, status `waiting`). Or librarian-managed.
2. **Librarian view** — `GET /librarian/reservations` → list grouped by book, "Users Reserved" count, status columns (Waiting / Allocated / Claimed / Expired), export button.
3. **Allocate** (book available) → `POST /librarian/reservations/<id>/allocate` → status `allocated`, `claim_deadline`, write `hold_ready` notification.
4. **Claim** (pickup) → `POST /librarian/reservations/<id>/claim` → status `claimed`.
5. **Expire** (past deadline) → `POST /librarian/reservations/<id>/expire` → status `expired`.

## Phases — Proposed (to be finalized with answers)

### Phase 1 — Models
- `get_borrower_by_user` (user_id→borrower row) — critical, mirrors Requests/Inventory gap.
- Reservation models: `create_reservation`, `get_reservations_by_book`, `allocate_reservation`, `claim_reservation`, `expire_reservation`, `next_in_queue`.
- Notification: `create_notification(recipient, message, type, ref)`.
- Extend `return_book` to accept `damage_notes`, `lost_flag`.

### Phase 2 — Routes (Facts)
- `GET /librarian/circulation` → real data (borrower panel, active loans, recent transactions, overdue list, due-soon list).
- `GET /librarian/reservations` → real grouped data.
- `POST /librarian/circulation/borrow` → Flow B.
- `POST /librarian/circulation/return` → Flow C.
- `POST /librarian/reservations/<id>/allocate|/claim|/expire`.
- Optional user-facing `POST /user/reserve`.

### Phase 3 — Template
- `circulation.html`: real stats, borrower lookup, borrow/return forms, live tables (replace hardcoded).
- `reservations.html`: real grouped reservations + status badges + export.

### Phase 4 — Tests (`tests/test_circulation.py`)
- Borrow: valid accession → record; already-borrowed → rejected; over-limit → rejected; due-date computed correctly.
- Return: fine computed; damage_notes/lost saved; reservation → hold notification written.
- Reservation lifecycle: create/allocate/claim/expire + next_in_queue.
- CSRF on all POST routes.
- Regression: `python -m pytest -q`.

## Open questions
1. Due-date high-demand "daily-only" (spec) — how to flag a book as high-demand, or skip this rule?
2. User-facing "Reserve" button on catalog, or librarian-managed reservation creation?
3. Overdue automation — scheduled job or compute-on-read?