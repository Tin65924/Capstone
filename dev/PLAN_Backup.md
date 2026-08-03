# Plan: Backup & Recovery Module (`app/backup`)

Scope: Module 7 from `PlannedModules.txt` — Automated monthly backup, secure storage, restore. The last stub module.

## Current State

- **Route is a stub** (`app/backup/routes.py`): `/admin/backup` renders `backup.html` with no data.
- **`create_backup()` exists but is never called** (`app/backup/utils.py`):
  - `BACKUP_DIR = <repo>/backups`
  - Runs `pg_dump "<DATABASE_URL>" > "<filepath>"` via `subprocess.run(cmd, shell=True, check=True)`.
  - Returns the filename only (no metadata, no size, no error capture into DB).
- **Restore: not implemented at all** (template has a static restore icon button only).
- **Scheduling: not wired** — `APScheduler==3.10.4` is in `requirements.txt` but imported nowhere. "Automated Monthly Backup" is unbuilt.
- **Template** `backup.html` is fully static (Status: Healthy, "Last Backup: 4 Hours Ago", "Redundancy: Cloud + Local", fake history + fake recovery logs). Hardcoded.
- **`backups/` folder is empty** — zero real backups exist.
- No DB table for backup metadata/history (each backup is just a file on disk).

## Key gaps

1. **Backup never runs** — no trigger button handler, no scheduler.
2. **No history** — the page can't list real backups (no metadata source).
3. **No restore** — cannot recover from a backup file.
4. **Automated monthly backup** — spec requirement, APScheduler present but unused.
5. **`create_backup` uses `shell=True` + string interpolation** — a command-injection risk if `DATABASE_URL` were ever attacker-influenced; also quoting-fragile. Should use a parameter list (no shell).
6. **"Secure storage"** — spec says secure storage location; currently just a repo folder. Need a documented/configurable `BACKUP_DIR` and retention (e.g., keep last N).

## Decisions (pending user confirmation — see questions)

Proposed default behavior (to confirm):
- Manual **Run Backup Now** button → `create_backup()` → real file + recorded metadata.
- **Scheduled monthly** via APScheduler (BackgroundScheduler started in `create_app`), auto-running on a configurable day/time.
- **Backup history** listed from real files + a small `backup_log` table (filename, created_at, size_bytes, status, type=manual|scheduled).
- **Restore**: download a backup file; restore = run `psql` against the selected `.sql` (destructive, confirm-modal, admin-only, logs activity). Restore is inherently risky — see open question.
- **Retention**: keep the newest N backups (e.g., 12 = a year of monthly backups), auto-delete older.
- **Fix `create_backup`**: use `subprocess.run([...])` without `shell=True`.

## Decisions (confirmed)

1. **Direct restore + auto-backup**: Restore runs `psql` against the selected file, but **first** auto-creates a fresh backup of the current state (so a mis-click is never catastrophic). Destructive but recoverable.
2. **Env-configurable schedule**: `BACKUP_DAY` / `BACKUP_HOUR` (default 1st-of-month 02:00), plus `BACKUP_KEEP` for retention.
3. **Retention: keep 12** newest backups (a year of monthly backups), auto-delete older.

## Data Flow

### Flow A — Manual backup

1. Admin clicks **Run Backup Now** → `POST /admin/backup/create`.
2. Route (`@admin_required`, CSRF-checked):
   a. `create_backup()` → `pg_dump` runs (no shell), writes `<BACKUP_DIR>/library_backup_<ts>.sql`.
   b. Get file size + timestamp.
   c. INSERT into `backup_log` (filename, size_bytes, created_at, status='completed', type='manual').
   d. Retention: delete `backup_log` rows + files beyond the newest N.
   e. `log_activity(current_user.id, 'backup_created:...')` → flash → redirect.
3. Page re-renders → history table shows the new row.

Data written: `backups/*.sql` (file), `backup_log` (1 row). Data read: `backup_log`.

### Flow B — Automated monthly backup (scheduler)

1. `create_app` starts a `BackgroundScheduler` (`app/backup/scheduler.py`).
2. Cron trigger (e.g., 1st of month 02:00, configurable via `BACKUP_SCHEDULE` env) → job calls the same `create_backup()` → INSERT `backup_log` with `type='scheduled'` + retention.
3. Job failures are caught → `backup_log` row with `status='failed'` + error message (logged, not raised).

Data written: `backups/*.sql` (file), `backup_log` (1 row). No web request involved.

### Flow C — View backup page

1. `GET /admin/backup` → `get_backup_logs()` (newest first) + latest entry for the "Last Backup" status + total count/size.
2. Template renders: Status (Healthy if last backup within expected window / Warning otherwise), Last Backup time, count of backups, history table (filename, date, size, status, actions: Download / Restore), retention note.

Data read: `backup_log`, `backups/` directory.

### Flow D — Download a backup

1. Admin clicks download icon → `GET /admin/backup/<id>/download`.
2. Route: look up file in `backup_log` → `send_file` with `as_attachment=True`. Verify path is within `BACKUP_DIR` (prevent path traversal).

Data read: file. Data written: none.

### Flow E — Restore from a backup

1. Admin clicks restore icon on a history row → confirm modal (destructive warning + data-loss window note) → `POST /admin/backup/<id>/restore`.
2. Route (`@admin_required`, CSRF-checked):
   a. **Safety step**: `create_backup()` first → auto-backup of the current state, logged (`type='manual'`, remark "pre-restore").
   b. Load the selected `.sql` file.
   c. Run `psql` against `DATABASE_URL` (parameterized argv, no shell).
   d. Success → `log_activity` (who/what file/when) → flash "Restore complete".
   e. Failure → flash error; the auto-backup from (a) is the recovery point.
3. Note: everything created after the backup's timestamp is lost on restore (data-loss window) — shown in the modal.

Data written: auto-backup file + `backup_log` row (safety), then the entire DB (destructive). Data read: backup file.

## Phases

### Phase 1 — Fix utils + new models

- Rewrite `create_backup()`:
  - `subprocess.run([pg_dump, '--dbname=' + url, '--file=' + path])` — no `shell=True`.
  - Return `(filename, size_bytes)` or raise with the captured stderr.
- New `backup_log` table in `schema.sql`:
  ```sql
  CREATE TABLE IF NOT EXISTS backup_log (
      backup_id   SERIAL PRIMARY KEY,
      filename    VARCHAR(255) NOT NULL,
      size_bytes  BIGINT,
      status      VARCHAR(20) NOT NULL DEFAULT 'completed'
                  CHECK (status IN ('completed', 'failed')),
      backup_type VARCHAR(20) NOT NULL DEFAULT 'manual'
                  CHECK (backup_type IN ('manual', 'scheduled')),
      error_msg   VARCHAR(500),
      created_at  TIMESTAMP NOT NULL DEFAULT NOW()
  );
  ```
- Models: `log_backup(filename, size, type, status, error)`, `get_backup_logs()`, `get_backup_by_id(id)`, `delete_old_backups(keep_n)`.

### Phase 2 — Routes

- `POST /admin/backup/create` → Flow A (create, log, retention).
- `GET /admin/backup/<id>/download` → Flow D (`send_file`, path-validate).
- `POST /admin/backup/<id>/restore` → Flow E (confirm + psql).
- `GET /admin/backup` → Flow C (real data).

### Phase 3 — Scheduler

- New `app/backup/scheduler.py`: `start_scheduler(app)` creates a `BackgroundScheduler`, adds a monthly cron job (configurable), calls `create_backup` + `log_backup`.
- Call `start_scheduler(app)` in `create_app` (guard: don't start in tests or when `WERKZEUG_RUN_MAIN` is the reloader child only).
- Config: `BACKUP_SCHEDULE` (cron fields) + `BACKUP_KEEP` (retention count) in `config.py` from env. Schedule env-configurable: `BACKUP_DAY` (default 1), `BACKUP_HOUR` (default 2). Retention default 12.

### Phase 4 — Template rewiring

- Replace hardcoded values with real data:
  - Status pill: Healthy if last backup within the schedule window, else Warning.
  - Last Backup: from newest `backup_log` row.
  - Backup count / total size.
  - History table: loop over `get_backup_logs()` — filename, created_at, size (MB), status badge, Download + Restore action buttons (real POST forms, CSRF).
  - Recovery Logs panel → real `backup_log` entries (failed/restore events) instead of fake timeline.
  - "Configuration Settings" → retention count (read from `BACKUP_KEEP`), not a fake button.
- Keep existing visual style; reuse `flash_messages.html`.

### Phase 5 — Tests (`tests/test_backup.py`)

- `create_backup` writes a file into `BACKUP_DIR` (mock `pg_dump` via `unittest.mock`), returns size; raises on failure.
- No `shell=True` in the subprocess call (assert call args are a list).
- `get_backup_logs` order + fields; `delete_old_backups` keeps newest N.
- Create route: calls create_backup + logs a row (mock pg_dump); failure → `status='failed'` row.
- Download route: serves the file; path traversal blocked for ids with missing files.
- Restore route: auto-backups current state (mock), then calls psql (mock) on success; logged to activity.
- Scheduler: job is registered when `start_scheduler` runs (can assert on the scheduler's job list).
- Regression: `python -m pytest -q`.

## Security notes

- **Remove `shell=True`** — parameterized argv list (command injection / quoting hardening). Applies to both `pg_dump` and `psql`.
- `BACKUP_DIR` path from config (env), not client input; download path validated to stay within it.
- Restore is destructive → admin-only, CSRF, explicit confirm modal with data-loss warning, auto-backup safety net, `log_activity` record of who/when/what file.
- `DATABASE_URL` passed via env/argv, never echoed in UI/logs.
- Scheduler disabled during tests (avoid background threads in the test client).
- Retention deletion only touches files recorded in `backup_log` within `BACKUP_DIR`.

## Open questions

1. **Post-restore session**: after a successful restore, should the admin be logged out / prompted to re-login (schema may differ), or stay logged in? (Deferred — recommend re-login prompt.)
