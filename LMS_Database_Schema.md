# Library Management System — Database Schema (Rev. 2)
Revised against `Proposed_Modules-1.docx` and your answers on OAuth, borrower/user linkage,
demand counter, and supplier list scope.

## What changed from Rev. 1
- **No `password_hash` anywhere.** Google OAuth only — `user_accounts` now stores an OAuth
  subject id instead.
- **`borrowers` and `user_accounts` stay separate, linked 1-to-1** (your choice). Every
  borrower is also a `user_accounts` row (since login is now required for everyone), but
  `borrowers` only exists for Student/Faculty roles as a role-specific extension.
- **`borrower_type` removed** from `borrowers` — it was redundant with `role_id` on
  `user_accounts` (Librarian/Faculty/Student/Admin already lives there).
- **`contact_info` removed** from `borrowers` — email lives on `user_accounts`.
- **`demand_counter` removed** as a stored field — computed live from `request_records` (your
  choice, see query at the bottom of §3).
- **`supplier` removed** from `procurement_log` — status-only, per your note.
- **No `supplier_catalog` table added** — out of scope per your answer.
- Added fields from the new doc: `year_published`, `subject_classification`, `call_number` on
  `book_catalog`; `borrow_type`, `damage_notes`, `lost_flag` on `circulation_records`; expanded
  status ENUMs to match the doc's actual workflow states.
- **Open question (flagged, not yet resolved):** the new doc's module list and final
  architecture flow don't mention Reservations at all — Request → Procurement → Accessioning →
  Cataloging → Circulation → Monitoring/Analytics → Inventory → Procurement Feedback. I've left
  `reservation_queue` and `notification_log` in place since removing them is destructive, but
  flag if that module is actually dropped.
- **Open question:** "Online Resource Usage" is listed as a KPI in Module 5, but no module
  describes tracking digital/online resources anywhere else in the doc. I haven't added a
  table for it — assuming it's out of scope until there's a digital-resources module to back it.

---

## 1. Identity & Access (Module 6)

### `roles`
| Field | Type | Constraint |
|---|---|---|
| role_id | INT | PK |
| role_name | VARCHAR(50) | UNIQUE, NOT NULL — Librarian, Faculty, Student, Admin |
| permissions | JSON | module-level permission list |

### `user_accounts`
| Field | Type | Constraint |
|---|---|---|
| user_id | INT | PK |
| email | VARCHAR(100) | UNIQUE, NOT NULL — must match institutional domain (e.g. `@mcst.edu.ph`), enforced at the application layer during OAuth callback |
| oauth_sub | VARCHAR(255) | UNIQUE, NOT NULL — Google OAuth subject identifier |
| full_name | VARCHAR(150) | NOT NULL — pulled from Google profile on first login |
| role_id | INT | FK → roles.role_id |
| account_status | ENUM('active','disabled') | NOT NULL |
| created_at | DATETIME | NOT NULL |

*No password field exists anywhere in this schema — authentication is fully delegated to Google.*

### `audit_trail`
| Field | Type | Constraint |
|---|---|---|
| log_id | INT | PK |
| user_id | INT | FK → user_accounts.user_id |
| activity | VARCHAR(255) | NOT NULL |
| session_token | VARCHAR(255) | nullable |
| log_timestamp | DATETIME | NOT NULL |

---

## 2. Borrowers (extension of `user_accounts`, Students & Faculty only)

### `borrowers`
| Field | Type | Constraint |
|---|---|---|
| borrower_id | INT | PK |
| user_id | INT | FK → user_accounts.user_id, UNIQUE, NOT NULL (1-to-1) |
| id_number | VARCHAR(30) | UNIQUE, NOT NULL |
| department | VARCHAR(100) | nullable — Program/Department |
| borrower_status | ENUM('active','blocked') | NOT NULL, default 'active' — this is the "Active Status Validation" the doc requires; blocked = can't transact (e.g. unpaid fine, lost book, disciplinary hold) |

Role (student vs. faculty) is read from `user_accounts.role_id` via the join — not duplicated here.

---

## 3. Request Management (Module 1A)

### `request_records`
| Field | Type | Constraint |
|---|---|---|
| request_id | INT | PK |
| requester_id | INT | FK → borrowers.borrower_id |
| book_title | VARCHAR(255) | NOT NULL |
| author | VARCHAR(150) | nullable — "Optional Author" per the doc |
| matched_book_id | INT | FK → book_catalog.book_id, nullable — set by the system when duplicate/inventory detection finds an existing title |
| request_status | ENUM('pending_review','existing_in_collection','approved','rejected','procured') | NOT NULL, default 'pending_review' |
| request_date | DATETIME | NOT NULL |
| reviewed_by | INT | FK → user_accounts.user_id, nullable (librarian) |
| review_date | DATETIME | nullable |

**Duplicate/demand detection** (both described in the doc, neither needs a stored counter):
```sql
-- "already exists" check → search book_catalog by title
-- "already requested" check + demand counter, computed on read:
SELECT book_title, COUNT(*) AS demand_count
FROM request_records
WHERE request_status IN ('pending_review','approved')
GROUP BY book_title;
```
This stays accurate automatically as requests come in, at the cost of a GROUP BY on read instead
of an O(1) field lookup — reasonable trade-off unless this table gets very large.

*Faculty-specific flow (checking a librarian-uploaded supplier list before requesting) has no
table yet since you said that's out of scope for now — when it's in scope, this table's
`matched_book_id` pattern extends naturally to a `matched_supplier_item_id`.*

---

## 4. Procurement (Module 1B)

### `procurement_log`
| Field | Type | Constraint |
|---|---|---|
| procurement_id | INT | PK |
| request_id | INT | FK → request_records.request_id |
| order_status | ENUM('for_ordering','ordered','delivered','cancelled','out_of_stock','procured') | NOT NULL |
| order_date | DATE | NOT NULL |
| date_received | DATE | nullable |
| book_id | INT | FK → book_catalog.book_id, nullable — filled once the item is catalogued |
| remarks | VARCHAR(255) | nullable — free-text librarian note |

*No supplier field, no payment/shipping data — matches the doc's explicit system limitation
("system only allows status updates").*

---

## 5. Cataloging & Accessioning (Module 2)

### `book_catalog`
| Field | Type | Constraint |
|---|---|---|
| book_id | INT | PK |
| title | VARCHAR(255) | NOT NULL |
| author | VARCHAR(150) | NOT NULL |
| edition | VARCHAR(30) | nullable |
| publisher | VARCHAR(150) | nullable |
| year_published | INT | nullable |
| subject_classification | VARCHAR(100) | nullable |
| call_number | VARCHAR(50) | nullable |
| isbn | VARCHAR(20) | nullable — kept as a convenience field; not in the doc's list, drop if you don't want it |
| material_type | VARCHAR(30) | NOT NULL, default 'Book' — Book, E-Book, Journal, Dissertation |
| description | TEXT | nullable — free-text book summary/abstract |
| catalog_status | ENUM('active','archived') | NOT NULL, default 'active' — librarian-facing lifecycle status; real-time copy availability is derived from circulation_records + inventory_status |
| date_added | DATE | NOT NULL |

### `accession_log`
| Field | Type | Constraint |
|---|---|---|
| accession_id | INT | PK |
| accession_number | VARCHAR(30) | UNIQUE, NOT NULL |
| book_id | INT | FK → book_catalog.book_id |
| copy_number | INT | nullable — sequential copy number per title (e.g., copy 1 of 5) |
| librarian_id | INT | FK → user_accounts.user_id |
| date_accessioned | DATE | NOT NULL |
| source | ENUM('purchase','donation') | nullable |

*One title (`book_catalog`) → many physical copies (`accession_log`), unchanged from Rev. 1.*

---

## 6. Circulation (Module 3)

### `circulation_records`
| Field | Type | Constraint |
|---|---|---|
| circulation_id | INT | PK |
| book_id | INT | FK → book_catalog.book_id |
| accession_id | INT | FK → accession_log.accession_id |
| borrower_id | INT | FK → borrowers.borrower_id |
| processed_by | INT | FK → user_accounts.user_id (librarian) |
| borrow_type | ENUM('overnight','daily_circulation') | NOT NULL |
| transaction_type | ENUM('borrow','return') | NOT NULL |
| borrow_date | DATE | NOT NULL |
| due_date | DATE | nullable — only applies to `overnight`; `daily_circulation` has none per the doc |
| return_date | DATE | nullable |
| fine_amount | DECIMAL(8,2) | default 0.00 |
| damage_notes | TEXT | nullable — librarian's damage-tagging notes |
| lost_flag | BOOLEAN | default FALSE |
| transaction_status | ENUM('active','returned','overdue') | NOT NULL |

**Business rules kept out of the schema** (enforced in application logic, not columns):
- Students capped at 3 concurrent active borrows.
- Faculty borrow window up to 1 month, if multiple copies exist.
- High-demand titles forced to `daily_circulation` only.
- Overdue reminder fires 2 days before `due_date`.

These are *rules*, not data — encoding them as columns would just duplicate logic that belongs
in the app layer, so the schema only stores the resulting transaction facts.

---

## 7. Inventory Monitoring (Module 4)

### `inventory_status`
| Field | Type | Constraint |
|---|---|---|
| inventory_id | INT | PK |
| accession_id | INT | FK → accession_log.accession_id |
| inventory_state | ENUM('available','borrowed','lost','damaged','missing') | NOT NULL |
| inventory_type | ENUM('realtime_scan','annual_physical') | NOT NULL — distinguishes ad-hoc scans from the yearly full inventory |
| checked_by | INT | FK → user_accounts.user_id (librarian) |
| last_checked_date | DATE | NOT NULL |

*Discrepancy reports (missing vs. borrowed cross-check) are generated on demand from this table
joined against `circulation_records` — same pattern as `analytics_cache` below, not stored
separately.*

---
 
## 8. Inventory Sessions (Module 4 — session tracking)

### `inventory_sessions`
| Field | Type | Constraint |
|---|---|---|
| session_id | INT | PK |
| librarian_id | INT | FK → user_accounts.user_id |
| total_books | INT | NOT NULL — total books in system at session start |
| scanned_count | INT | NOT NULL, default 0 |
| session_status | ENUM('active','completed','cancelled') | NOT NULL, default 'active' |
| started_at | DATETIME | NOT NULL |
| ended_at | DATETIME | nullable |

---
 
## 9. Reservations — flagged as possibly out of scope, kept for now

### `reservation_queue`
| Field | Type | Constraint |
|---|---|---|
| reservation_id | INT | PK |
| book_id | INT | FK → book_catalog.book_id |
| borrower_id | INT | FK → borrowers.borrower_id |
| queue_position | INT | NOT NULL |
| request_date | DATETIME | NOT NULL |
| reservation_status | ENUM('waiting','allocated','claimed','expired') | NOT NULL |
| claim_deadline | DATETIME | nullable |

### `notification_log`
| Field | Type | Constraint |
|---|---|---|
| notification_id | INT | PK |
| recipient_id | INT | FK → borrowers.borrower_id |
| message | VARCHAR(500) | NOT NULL |
| notif_type | ENUM('status_update','hold_ready','overdue_reminder') | NOT NULL |
| related_reference | VARCHAR(50) | nullable — e.g. "reservation:12", "circulation:44" |
| date_sent | DATETIME | NOT NULL |

---

## 10. User Favorites / Wishlist

### `user_favorites`
| Field | Type | Constraint |
|---|---|---|
| favorite_id | INT | PK |
| user_id | INT | FK → user_accounts.user_id |
| book_id | INT | FK → book_catalog.book_id |
| created_at | DATETIME | NOT NULL |

UNIQUE(user_id, book_id) — prevents duplicate entries.

---

## 11. Reporting & Analytics (Module 5)

### `analytics_cache`
| Field | Type | Constraint |
|---|---|---|
| cache_id | INT | PK |
| report_type | ENUM('books_borrowed_per_program','utilization_rate','most_borrowed_titles','underutilized_titles','online_resource_usage') | NOT NULL |
| filter_params | JSON | e.g. `{"period":"semester","term":"2026-1"}` |
| kpi_data | JSON | NOT NULL |
| generated_by | INT | FK → user_accounts.user_id |
| generated_date | DATETIME | NOT NULL |

Rebuilt from `circulation_records`, `inventory_status`, and `book_catalog` — not a source of
truth, same as Rev. 1.

## 12. Backup & Recovery (Module 7)
No schema impact — automated monthly backups operate on the whole database at the infrastructure
level, not as application tables.

---

## Normalization notes (answering your question directly)
The schema is close to **3NF** with two deliberate exceptions, both trade-offs rather than
mistakes:
1. `book_catalog.catalog_status` (active/archived) is a librarian-facing lifecycle flag, not a real-time availability status. Per-copy availability is derived from `circulation_records` and `inventory_status` at query time. Risk: `catalog_status` and actual circulation state can drift if a title is archived while copies are still borrowed — enforce via trigger or service-layer guard.
2. `request_records.book_title`/`author` duplicate data that may later exist in `book_catalog` — necessary, not accidental, since a request can exist before a matching catalog entry does.

Everything else — no repeating groups, all non-key fields depend on the whole primary key, no
transitive dependencies through non-key fields — checks out.
