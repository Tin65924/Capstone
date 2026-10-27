# Performance & Optimization Audit

Read-only audit of the MCST LMS Flask application. No files were modified, no code was
executed, and no tests or servers were run to produce these findings.

- **Branch:** `fix-inventory-sessions`
- **Date:** 2026-10-19
- **Scope:** `app/` (analytics, cataloging, circulation, inventory, auth, database, main,
  settings, backup, requests, procurement, boot/infra)
- **Total findings:** 55 — 16 high, 25 medium, 14 low

Line numbers refer to the current working tree and may drift as code changes.

---

## Cross-cutting themes

| Theme | Summary |
| --- | --- |
| Boot path is heavy | The full DDL plus non-idempotent data backfills replay on every start; analytics prewarm recomputes the whole dashboard for every preset and department, sequentially. |
| Missing indexes | Hot FK/date columns have none: `borrower_id`, `due_date`, `session_id`, `created_at`, and the procurement/request dates. |
| Function-wrapped predicates | `col::date` and `COALESCE(...)` in `WHERE`/`ORDER BY` make date indexes unusable across analytics, main and circulation. |
| Unbounded reads | Desk loans, admin users, procurement/backup logs and the catalog fuzzy-match all load whole tables, then filter or paginate in Python. |
| N+1 and per-row loops | The reservation page, `delete_user`, per-accession condition lookups and the CSV importer each issue one statement per row. |
| Caching and concurrency | The analytics cache is unindexed and append-only; pool of 10 vs 8 workers plus prewarm/backup threads; bloom and scheduler are per-process. |

---

## High-severity findings

| Sev | Finding | Location | Impact |
| --- | --- | --- | --- |
| High | Schema replay: full DDL + non-idempotent data DML on every boot | `app/database.py:243-391,526-545` · `app/schema.sql:336-367` | Full-scan `UPDATE`/`DELETE` + `ACCESS EXCLUSIVE` locks stall every restart |
| High | Connection pool too small for workers + background threads | `app/database.py:40-44,132` | `PoolError` under concurrency surfaces as HTTP 500 |
| High | Per-request `SELECT 1` connection validation | `app/database.py:67-73` | Extra network round-trip on every request that touches the DB |
| High | Context processor runs COUNT queries on every page render | `app/__init__.py:127-162` | 1–2 extra queries per page for every role; unbounded count |
| High | Live notification poll re-queries user and sorts unindexed expression | `app/main/routes.py:790-813,649-655` | Every client ~15s: full sort of `circulation_records` |
| High | Analytics cache table unindexed and append-only | `app/analytics/models.py:383,412,433` | Two seq scans per load; prune `DELETE` full-scans |
| High | Boot prewarm recomputes ~35-query dashboard for every preset + department | `app/analytics/__init__.py:21-38` | Minutes of sequential DB work at each restart, pool contention |
| High | PDF export: N KPI queries + N cache inserts + CPU PDF, synchronously | `app/analytics/routes.py:2694-2725` | `export all` ≈ 30 queries + 30 writes on one request |
| High | Duplicate heavy aggregates inside one dashboard compute | `app/analytics/routes.py:536/583, 589/616` | Same queries run twice per cold or no-filter load |
| High | Leading-wildcard `ILIKE`; no trigram or full-text index | `app/cataloging/models.py:459,464-484,1021-1039` | Every search/suggest seq-scans and sorts `book_catalog` |
| High | Autosuggest fires a 4-way UNION plus two more scans per keystroke | `app/cataloging/models.py:580-589,600-605` | ~6 table scans per keystroke on the public path |
| High | Bulk CSV import issues ~5–6 auto-committed statements per row | `app/cataloging/routes.py:1185-1278` | Thousands of round-trips and commits per import |
| High | Desk loads all active loans, then filters in Python | `app/circulation/routes.py:252,286-296` | Unbounded 5-table join on every desk render |
| High | No index on `circulation_records.borrower_id` | `app/schema.sql:437-440` | Seq scan for every borrower loan/history/fine lookup |
| High | Reservation page N+1: one JOIN query per reserved book | `app/circulation/routes.py:665-671` | +1 query per reserved book on every page load |
| High | `check_catalog_exists` full fetch + Python fuzzy match on POST | `app/requests/models.py:514-524` | ~4.5k rows + O(n) `SequenceMatcher` per submission |

---

## Highest-leverage fixes

### Indexes to add (`app/schema.sql`)

```sql
-- circulation
CREATE INDEX idx_circ_borrower    ON circulation_records(borrower_id);
CREATE INDEX idx_circ_due         ON circulation_records(due_date);
CREATE INDEX idx_circ_recent      ON circulation_records((COALESCE(return_date, borrow_date)) DESC);

-- inventory
CREATE INDEX idx_inv_session      ON inventory_status(session_id);
CREATE INDEX idx_inv_checked      ON inventory_status(last_checked_date DESC);

-- reservations / requests / procurement
CREATE INDEX idx_res_borrower     ON reservation_queue(borrower_id);
CREATE INDEX idx_req_date         ON request_records(request_date);
CREATE INDEX idx_req_status_date  ON request_records(request_status, request_date);
CREATE INDEX idx_proc_request     ON procurement_log(request_id);
CREATE INDEX idx_proc_status      ON procurement_log(order_status);

-- accounts / analytics
CREATE INDEX idx_users_created    ON user_accounts(created_at DESC);
CREATE INDEX idx_analytics_cache  ON analytics_cache(report_type, generated_date DESC);

-- catalog search (requires pg_trgm)
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_book_title_trgm  ON book_catalog USING gin (title  gin_trgm_ops);
CREATE INDEX idx_book_author_trgm ON book_catalog USING gin (author gin_trgm_ops);
CREATE INDEX idx_book_isbn_trgm   ON book_catalog USING gin (isbn   gin_trgm_ops);
```

### Code changes

- Gate `run_schema`/`init_db` behind a schema-version table and default `SKIP_SCHEMA_SYNC=1`
  after the first boot.
- Drop the per-request `SELECT 1`; validate only newly created connections.
- Cache the unread-badge context processor per user (15–30s) instead of querying every render.
- Serialize analytics prewarm to one worker and warm a couple of keys, not every department.
- Raise pool `maxconn` (10 → ~20) and handle `PoolError` in `get_connection`.
- Replace `col::date` comparisons with half-open ranges (`>= d AND < d + 1`) so date indexes
  can be used.

---

## Medium-severity findings

| Sev | Finding | Location |
| --- | --- | --- |
| Med | Function-wrapped `::date` / `COALESCE` predicates defeat date indexes | `app/analytics/models.py:751,1781,860,694,179,526` · `app/main/models.py:136,337` · `app/circulation/models.py:624` |
| Med | Missing index: `inventory_status.session_id` | `app/schema.sql:168,446` |
| Med | Missing index: `circulation_records.due_date` | `app/schema.sql:437` |
| Med | Missing index: `reservation_queue.borrower_id` | `app/circulation/models.py:940,964` |
| Med | No index on `user_accounts.created_at`; admin list unpaginated in SQL | `app/auth/models.py:403-431` · `app/auth/routes.py:445-446` |
| Med | No indexes on `procurement_log(request_id / order_status)`; unbounded listing | `app/procurement/models.py:34-46,91-98` |
| Med | Missing `request_records(request_date)` / (status, date) index | `app/schema.sql:447` |
| Med | `get_audit_stats` pulls 2000 rows and aggregates in Python | `app/auth/models.py:858-896` |
| Med | `delete_user` runs one DELETE per request row | `app/auth/models.py:1107-1119` |
| Med | Heavy modules (`openpyxl`, google libs) imported at app import time | `app/auth/routes.py:8-12` |
| Med | Settings save commits once per key (~11 round-trips) | `app/settings/routes.py:97,128,190,230` |
| Med | `_import_jobs` cleanup mutates dict without the lock | `app/cataloging/routes.py:1314-1328` |
| Med | Two correlated condition subqueries per accession on cataloging page | `app/inventory/models.py:492-506` |
| Med | Bloom rebuild full-scans three tables; per-process staleness; serializes readers | `app/bloom_registry.py:109-159` |
| Med | `COUNT(DISTINCT ON)` then re-sorts the same set for the page | `app/cataloging/models.py:1129-1156` |
| Med | Correlated availability `EXISTS` evaluated per candidate row | `app/cataloging/models.py:1090-1110` |
| Med | Duplicate availability scans per reservation allocate | `app/circulation/routes.py:748,774` |
| Med | `get_recent_transactions` sorts the whole history by expression | `app/circulation/models.py:685` |
| Med | Desk borrow: ~9 sequential round-trips, no `FOR UPDATE` (overnight floor race) | `app/circulation/routes.py:425-462,152` |
| Med | Scan-history OFFSET pagination plus a separate full COUNT | `app/inventory/models.py:414,433` |
| Med | `_cluster_demand` O(n²) fuzzy computed twice per requests page | `app/requests/routes.py:81,87` · `app/requests/models.py:337` |
| Med | In-process scheduler duplicates under >1 worker; orphaned `pg_dump` on restart | `app/backup/scheduler.py:147-181` · `app/backup/jobs.py:155` |
| Med | Analytics page runs two uncached heavy queries even on a cache hit | `app/analytics/routes.py:800,804` · `app/analytics/models.py:255,277` |

---

## Low-severity findings

| Sev | Finding | Location |
| --- | --- | --- |
| Low | Cache-key normalization diverges from compute normalization | `app/analytics/routes.py:198-213` vs `:524` |
| Low | Per-cell `import decimal` inside serialization loops | `app/analytics/routes.py:1361,1898` |
| Low | Catalog export materializes all rows plus per-book `string_agg` | `app/cataloging/routes.py:610-616` · `app/cataloging/models.py:608-620` |
| Low | `MAX(CAST regex)` full `accession_log` scan when the add-book modal opens | `app/cataloging/routes.py:195` |
| Low | Stray broken debug file (fails at runtime, unused) | `app/cataloging/get_book.py:9` |
| Low | Unbounded `get_backup_logs()` loaded whole on two pages | `app/backup/routes.py:193` · `app/main/routes.py:1003` |
| Low | Unbounded fuzzy scan in `check_approved_request_exists` | `app/requests/models.py:532-542` |
| Low | Procurement counted by fetching all rows instead of `COUNT(*)` | `app/main/models.py:187-188` |
| Low | `get_status_summary` full-scans `inventory_status` every load | `app/inventory/models.py:219` |
| Low | `upsert_inventory_record` SELECT-then-write; no UNIQUE on `accession_id` | `app/inventory/models.py:101-113` |
| Low | Duplicate counts (aggregate stats vs Python sums) | `app/circulation/routes.py:324-326` |
| Low | Redundant `get_user_by_id` in notification APIs | `app/main/routes.py:724-729,804-810` |
| Low | `search_books_for_analytics` leading-wildcard `ILIKE` + `DISTINCT` over a join | `app/analytics/models.py:1349-1361` |
| Low | `is_valid_any_department` filters `departments.name` with no name index | `app/auth/models.py:1470-1473` |

---

## Suggested sequencing

1. **Low-risk, high-return:** add the index set, gate schema sync behind `SKIP_SCHEMA_SYNC`,
   remove the per-request `SELECT 1`, cache the badge context processor, and raise the pool size.
2. **Query shape:** rewrite `::date` / `COALESCE` predicates as ranges; collapse duplicate
   aggregates (analytics dashboard, `circulation_overview`).
3. **N+1 fixes:** reservation page, `delete_user`, per-accession condition lookups, and the bulk
   CSV import.
4. **Feature-level:** serialize analytics prewarm, queue the PDF export, and replace the in-process
   scheduler with a DB advisory lock or external scheduler.
