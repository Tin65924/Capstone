# Plan: Analytics & Reporting Module (`app/analytics`)

Scope: Module 5 from `PlannedModules.txt` — Descriptive Analytics & Reporting Dashboard (KPI cards, time filtering, exportable reports, per-librarian board).

## Current State

- **Routes are stubs** (`app/analytics/routes.py`): `/librarian/analytics` renders `analytics.html` with no data.
- **Models written but unused** (`app/analytics/models.py`):
  - `books_borrowed_per_program()` — department, total
  - `utilization_rate()` — borrowed ÷ active collection
  - `most_borrowed_titles(limit=10)` — title, borrow_count
  - `underutilized_titles()` — titles with zero borrows
  - None accept a date range.
- **`analytics_cache` exists** (`app/schema.sql:163`): `report_type CHECK (books_borrowed_per_program, utilization_rate, most_borrowed_titles, underutilized_titles, online_resource_usage)`, `filter_params JSONB`, `kpi_data JSONB`, `generated_by`, `generated_date`. Unused.
- **Template** is an elaborate drag-and-drop KPI builder with **hardcoded data** (2,840 borrows, 84%, 320/210/180/140, fake top-titles). All of it is placeholder — **will not be used**.

## Decisions (confirmed)

1. **Remove drag-and-drop.** The board renders the saved KPI cards plus one dashed "Add KPI" card; clicking it opens a modal listing all available KPIs with a description of what each shows.
2. **Board layout in localStorage.** The librarian's KPI arrangement (which KPIs, position, visibility) is saved in the browser (`localStorage`) — **no DB table, no schema change**. Trade-off accepted: the board persists per-browser/device, not per-account across machines.
3. **Time filter = date range + presets**: From/To date inputs plus preset buttons (This semester / This year / All time). Filter applies to every KPI query.
4. **Online Resource Usage is dropped** — it's in the spec but has no data source (no tracking table) and the template placeholder is not used. `analytics_cache` CHECK keeps the name (harmless), but we never write that type.
5. **Cache on export** — each export writes a snapshot row to `analytics_cache` (report history for budget defense). Dashboard views compute fresh.
6. KPIs (4 real ones): Books Borrowed per Program, Utilization Rate, Most Borrowed Titles, Underutilized Titles.

## Data Flow

### Flow A — View dashboard (read-only)

1. `GET /librarian/analytics?from=&to=&preset=` → route parses the range:
   - preset `all` → `(None, None)`; preset `semester` → current academic semester bounds; preset `year` → current calendar year; else use `from`/`to` dates.
2. Server renders **all KPI data** for the range (each KPI model + its label/description) into a JS-accessible payload (e.g., `<script type="application/json" id="kpi-data">` or data attributes).
3. Client JS reads the saved board from `localStorage` (`mcst_kpi_board`) → renders only the saved KPI cards in saved order + the trailing dashed "Add KPI" card.
4. No board writes to the DB.

Data read: `book_catalog`, `circulation_records`, `borrowers`. Data written (server): none for the board.

### Flow B — Add a KPI (via modal)

1. Librarian clicks the dashed **Add KPI** card → modal lists the 4 KPIs with descriptions.
2. Librarian picks one → client JS appends the card and saves the new arrangement to `localStorage['mcst_kpi_board']` (array of `{kpi_type, position, visible}`).
3. No POST — purely client-side; persists on that browser.

Data written: browser localStorage.

### Flow C — Remove a KPI

1. Librarian clicks Remove (×) on a card → JS removes it and rewrites `localStorage['mcst_kpi_board']`.
2. No POST.

Data written: browser localStorage.

### Flow D — Export a report (CSV + cache snapshot)

1. Librarian clicks **Export** on a KPI card (or **Export All**) → `POST /librarian/analytics/export` with `{kpi_type(s), from, to}`.
2. Route:
   a. Re-run the KPI query(ies) with the range.
   b. `save_report_snapshot(kpi_type, filter_params, kpi_data, current_user.id)` → INSERT `analytics_cache` (report history).
   c. Build CSV (header row + rows) → stream as `text/csv` attachment.
3. Dashboard is unchanged.

Data written: `analytics_cache` (1 row per exported KPI). Data read: the KPI source tables.

## Phases

### Phase 1 — Models

- Extend the 4 KPI models to accept `(start_date=None, end_date=None)`:
  - `books_borrowed_per_program(start, end)` → add `AND c.borrow_date BETWEEN %s AND %s` when both set.
  - `utilization_rate(start, end)` → borrowed count scoped to the range (total collection unscoped).
  - `most_borrowed_titles(start, end, limit=10)`.
  - `underutilized_titles(start, end)` → zero borrows *in the range*.
- New `save_report_snapshot(report_type, filter_params, kpi_data, generated_by)`.
- **No `dashboard_layouts` table** — board layout lives in browser localStorage.

### Phase 2 — Routes

- `GET /librarian/analytics` → parse range + presets, compute all KPI data, embed as a JSON payload for the client.
- `POST /librarian/analytics/export` → CSV export + `analytics_cache` snapshot.
- No add/remove KPI routes (handled client-side via localStorage).

### Phase 3 — Template rewiring

- Delete the drag-and-drop JS + KPI library panel + hardcoded cards.
- Top bar: real time filter — From/To date inputs + preset buttons (This semester / This year / All time) + Export All.
- Board JS:
  - Read `localStorage['mcst_kpi_board']` (default: first 2 KPIs if unset) → render saved cards in saved order.
  - Server embeds all computed KPI data + labels via a JSON script tag; JS picks the ones the board references.
  - Dashed **Add KPI** card at the end → modal lists the 4 KPIs with descriptions → click appends + saves to localStorage.
  - Remove (×) → deletes from localStorage.
- Each card: title, data visual (reuse existing SVG/progress/bar styles), Export button (POST form, CSRF).
- Keep existing visual style; reuse `flash_messages.html`.

### Phase 4 — Tests (`tests/test_analytics.py`)

- Each KPI model returns correct data for a seeded range (and empty/all-time).
- Date filtering: records outside the range excluded.
- Export route: returns CSV with headers + data, writes one `analytics_cache` row.
- CSRF on the export POST route.
- Regression: `python -m pytest -q`.

## Security notes

- CSRF tokens on all POST forms (global `CSRFProtect` from auth plan).
- All routes `@librarian_required`.
- `kpi_type` validated server-side against the allowed set (never accept arbitrary strings).
- Date inputs parsed defensively (invalid dates → fall back to All time).
- Parameterized queries (existing pattern) — no SQL injection.
- localStorage board is client-side only — no server trust boundary (server never reads it).
