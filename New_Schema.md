# MCST Library Management System — Database Schema

**Database:** PostgreSQL 18  
**Schema:** `public` (default)

---

## Entity Relationship Overview

```
roles ──< user_accounts >── audit_trail
  │            │
  │            └──< borrowers
  │
  └──< user_accounts.role_id

book_catalog ──< accession_log >── inventory_status
  │   │              │
  │   │              └──< inventory_sessions
  │   │
  │   ├──< circulation_records
  │   │
  │   ├──< request_records
  │   │
  │   ├──< procurement_log
  │   │
  │   └──< user_favorites
  │
borrowers ──< circulation_records
  │    │
  │    ├──< request_records
  │    │
  │    ├──< reservation_queue
  │    │
  │    └──< notification_log
```

---

## 1. Identity & Access (Module 6 — Auth)

### `roles`
| Column | Type | Constraints |
|--------|------|-------------|
| `role_id` | `SERIAL` | `PRIMARY KEY` |
| `role_name` | `VARCHAR(50)` | `UNIQUE`, `NOT NULL` |
| `permissions` | `JSONB` | nullable |

**Seed data:** `'Student'`, `'Faculty'`, `'Librarian'`, `'Admin'`

### `user_accounts`
| Column | Type | Constraints |
|--------|------|-------------|
| `user_id` | `SERIAL` | `PRIMARY KEY` |
| `email` | `VARCHAR(100)` | `UNIQUE`, `NOT NULL` |
| `oauth_sub` | `VARCHAR(255)` | `UNIQUE`, `NOT NULL` |
| `full_name` | `VARCHAR(150)` | `NOT NULL` |
| `role_id` | `INT` | `NOT NULL` → `roles(role_id)` |
| `account_status` | `VARCHAR(20)` | `NOT NULL`, `DEFAULT 'active'`, CHECK `IN ('active', 'disabled', 'pending')` |
| `created_at` | `TIMESTAMP` | `NOT NULL`, `DEFAULT NOW()` |

**Status meanings:**
- `active` — approved and able to log in
- `disabled` — suspended by admin
- `pending` — Faculty awaiting librarian approval

### `audit_trail`
| Column | Type | Constraints |
|--------|------|-------------|
| `log_id` | `SERIAL` | `PRIMARY KEY` |
| `user_id` | `INT` | → `user_accounts(user_id)`, nullable |
| `activity` | `VARCHAR(255)` | `NOT NULL` |
| `session_token` | `VARCHAR(255)` | nullable |
| `log_timestamp` | `TIMESTAMP` | `NOT NULL`, `DEFAULT NOW()` |

---

## 2. Borrowers (extends `user_accounts`)

### `borrowers`
| Column | Type | Constraints |
|--------|------|-------------|
| `borrower_id` | `SERIAL` | `PRIMARY KEY` |
| `user_id` | `INT` | `UNIQUE`, `NOT NULL` → `user_accounts(user_id)` |
| `id_number` | `VARCHAR(30)` | `UNIQUE`, `NOT NULL` |
| `department` | `VARCHAR(100)` | nullable |
| `borrower_status` | `VARCHAR(20)` | `NOT NULL`, `DEFAULT 'active'`, CHECK `IN ('active', 'blocked')` |

**Note:** Only `Student` and `Faculty` roles get a `borrowers` row.

---

## 3. Cataloging & Accessioning (Module 2)

### `book_catalog`
| Column | Type | Constraints |
|--------|------|-------------|
| `book_id` | `SERIAL` | `PRIMARY KEY` |
| `title` | `VARCHAR(255)` | `NOT NULL` |
| `author` | `VARCHAR(150)` | `NOT NULL` |
| `edition` | `VARCHAR(30)` | nullable |
| `publisher` | `VARCHAR(150)` | nullable |
| `year_published` | `INT` | nullable |
| `subject_classification` | `VARCHAR(100)` | nullable |
| `call_number` | `VARCHAR(50)` | nullable |
| `isbn` | `VARCHAR(20)` | nullable |
| `material_type` | `VARCHAR(30)` | `NOT NULL`, `DEFAULT 'Book'` |
| `description` | `TEXT` | nullable |
| `catalog_status` | `VARCHAR(20)` | `NOT NULL`, `DEFAULT 'active'`, CHECK `IN ('active', 'archived')` |
| `date_added` | `DATE` | `NOT NULL`, `DEFAULT CURRENT_DATE` |

**Tuple index map (SELECT \*):**
| Index | Column |
|-------|--------|
| 0 | `book_id` |
| 1 | `title` |
| 2 | `author` |
| 3 | `edition` |
| 4 | `publisher` |
| 5 | `year_published` |
| 6 | `subject_classification` |
| 7 | `call_number` |
| 8 | `isbn` |
| 9 | `material_type` |
| 10 | `description` |
| 11 | `catalog_status` |
| 12 | `date_added` |

### `accession_log`
| Column | Type | Constraints |
|--------|------|-------------|
| `accession_id` | `SERIAL` | `PRIMARY KEY` |
| `accession_number` | `VARCHAR(30)` | `UNIQUE`, `NOT NULL` |
| `book_id` | `INT` | `NOT NULL` → `book_catalog(book_id)` |
| `copy_number` | `INT` | nullable |
| `librarian_id` | `INT` | `NOT NULL` → `user_accounts(user_id)` |
| `date_accessioned` | `DATE` | `NOT NULL`, `DEFAULT CURRENT_DATE` |
| `source` | `VARCHAR(20)` | CHECK `IN ('purchase', 'donation')`, nullable |

**Tuple index map (SELECT \*):**
| Index | Column |
|-------|--------|
| 0 | `accession_id` |
| 1 | `accession_number` |
| 2 | `book_id` |
| 3 | `copy_number` |
| 4 | `librarian_id` |
| 5 | `date_accessioned` |
| 6 | `source` |

---

## 4. Request Management (Module 1A)

### `request_records`
| Column | Type | Constraints |
|--------|------|-------------|
| `request_id` | `SERIAL` | `PRIMARY KEY` |
| `requester_id` | `INT` | `NOT NULL` → `borrowers(borrower_id)` |
| `book_title` | `VARCHAR(255)` | `NOT NULL` |
| `author` | `VARCHAR(150)` | nullable |
| `matched_book_id` | `INT` | → `book_catalog(book_id)`, nullable |
| `request_status` | `VARCHAR(30)` | `NOT NULL`, `DEFAULT 'pending_review'`, CHECK `IN ('pending_review', 'existing_in_collection', 'approved', 'rejected', 'procured')` |
| `request_date` | `TIMESTAMP` | `NOT NULL`, `DEFAULT NOW()` |
| `reviewed_by` | `INT` | → `user_accounts(user_id)`, nullable |
| `review_date` | `TIMESTAMP` | nullable |

---

## 5. Procurement (Module 1B)

### `procurement_log`
| Column | Type | Constraints |
|--------|------|-------------|
| `procurement_id` | `SERIAL` | `PRIMARY KEY` |
| `request_id` | `INT` | `NOT NULL` → `request_records(request_id)` |
| `order_status` | `VARCHAR(30)` | `NOT NULL`, CHECK `IN ('for_ordering', 'ordered', 'delivered', 'cancelled', 'out_of_stock', 'procured')` |
| `order_date` | `DATE` | `NOT NULL` |
| `date_received` | `DATE` | nullable |
| `book_id` | `INT` | → `book_catalog(book_id)`, nullable |
| `remarks` | `VARCHAR(255)` | nullable |

---

## 6. Circulation (Module 3)

### `circulation_records`
| Column | Type | Constraints |
|--------|------|-------------|
| `circulation_id` | `SERIAL` | `PRIMARY KEY` |
| `book_id` | `INT` | `NOT NULL` → `book_catalog(book_id)` |
| `accession_id` | `INT` | `NOT NULL` → `accession_log(accession_id)` |
| `borrower_id` | `INT` | `NOT NULL` → `borrowers(borrower_id)` |
| `processed_by` | `INT` | `NOT NULL` → `user_accounts(user_id)` |
| `borrow_type` | `VARCHAR(30)` | `NOT NULL`, CHECK `IN ('overnight', 'daily_circulation')` |
| `transaction_type` | `VARCHAR(20)` | `NOT NULL`, CHECK `IN ('borrow', 'return')` |
| `borrow_date` | `DATE` | `NOT NULL` |
| `due_date` | `DATE` | nullable |
| `return_date` | `DATE` | nullable |
| `fine_amount` | `DECIMAL(8,2)` | `NOT NULL`, `DEFAULT 0.00` |
| `damage_notes` | `TEXT` | nullable |
| `lost_flag` | `BOOLEAN` | `NOT NULL`, `DEFAULT FALSE` |
| `transaction_status` | `VARCHAR(20)` | `NOT NULL`, CHECK `IN ('active', 'returned', 'overdue')` |

---

## 7. Inventory Monitoring (Module 4)

### `inventory_status`
| Column | Type | Constraints |
|--------|------|-------------|
| `inventory_id` | `SERIAL` | `PRIMARY KEY` |
| `accession_id` | `INT` | `NOT NULL` → `accession_log(accession_id)` |
| `inventory_state` | `VARCHAR(20)` | `NOT NULL`, CHECK `IN ('available', 'borrowed', 'lost', 'damaged', 'missing')` |
| `inventory_type` | `VARCHAR(20)` | `NOT NULL`, CHECK `IN ('realtime_scan', 'annual_physical')` |
| `checked_by` | `INT` | → `user_accounts(user_id)`, nullable |
| `last_checked_date` | `DATE` | `NOT NULL` |

### `inventory_sessions`
| Column | Type | Constraints |
|--------|------|-------------|
| `session_id` | `SERIAL` | `PRIMARY KEY` |
| `librarian_id` | `INT` | `NOT NULL` → `user_accounts(user_id)` |
| `total_books` | `INT` | `NOT NULL` |
| `scanned_count` | `INT` | `NOT NULL`, `DEFAULT 0` |
| `session_status` | `VARCHAR(20)` | `NOT NULL`, `DEFAULT 'active'`, CHECK `IN ('active', 'completed', 'cancelled')` |
| `started_at` | `TIMESTAMP` | `NOT NULL`, `DEFAULT NOW()` |
| `ended_at` | `TIMESTAMP` | nullable |

---

## 8. Reservations

### `reservation_queue`
| Column | Type | Constraints |
|--------|------|-------------|
| `reservation_id` | `SERIAL` | `PRIMARY KEY` |
| `book_id` | `INT` | `NOT NULL` → `book_catalog(book_id)` |
| `borrower_id` | `INT` | `NOT NULL` → `borrowers(borrower_id)` |
| `queue_position` | `INT` | `NOT NULL` |
| `request_date` | `TIMESTAMP` | `NOT NULL`, `DEFAULT NOW()` |
| `reservation_status` | `VARCHAR(20)` | `NOT NULL`, CHECK `IN ('waiting', 'allocated', 'claimed', 'expired')` |
| `claim_deadline` | `TIMESTAMP` | nullable |

### `notification_log`
| Column | Type | Constraints |
|--------|------|-------------|
| `notification_id` | `SERIAL` | `PRIMARY KEY` |
| `recipient_id` | `INT` | `NOT NULL` → `borrowers(borrower_id)` |
| `message` | `VARCHAR(500)` | `NOT NULL` |
| `notif_type` | `VARCHAR(30)` | `NOT NULL`, CHECK `IN ('status_update', 'hold_ready', 'overdue_reminder')` |
| `related_reference` | `VARCHAR(50)` | nullable |
| `date_sent` | `TIMESTAMP` | `NOT NULL`, `DEFAULT NOW()` |

---

## 9. User Favorites / Wishlist

### `user_favorites`
| Column | Type | Constraints |
|--------|------|-------------|
| `favorite_id` | `SERIAL` | `PRIMARY KEY` |
| `user_id` | `INT` | `NOT NULL` → `user_accounts(user_id)` |
| `book_id` | `INT` | `NOT NULL` → `book_catalog(book_id)` |
| `created_at` | `TIMESTAMP` | `NOT NULL`, `DEFAULT NOW()` |
| | | `UNIQUE (user_id, book_id)` |

---

## 10. Analytics Cache (Module 5)

### `analytics_cache`
| Column | Type | Constraints |
|--------|------|-------------|
| `cache_id` | `SERIAL` | `PRIMARY KEY` |
| `report_type` | `VARCHAR(40)` | `NOT NULL`, CHECK `IN ('books_borrowed_per_program', 'utilization_rate', 'most_borrowed_titles', 'underutilized_titles', 'online_resource_usage')` |
| `filter_params` | `JSONB` | nullable |
| `kpi_data` | `JSONB` | `NOT NULL` |
| `generated_by` | `INT` | → `user_accounts(user_id)`, nullable |
| `generated_date` | `TIMESTAMP` | `NOT NULL`, `DEFAULT NOW()` |

---

## Foreign Key Relationship Map

| FK Column | Parent Table | Parent Column |
|-----------|-------------|---------------|
| `user_accounts.role_id` | `roles` | `role_id` |
| `audit_trail.user_id` | `user_accounts` | `user_id` |
| `borrowers.user_id` | `user_accounts` | `user_id` |
| `accession_log.book_id` | `book_catalog` | `book_id` |
| `accession_log.librarian_id` | `user_accounts` | `user_id` |
| `circulation_records.book_id` | `book_catalog` | `book_id` |
| `circulation_records.accession_id` | `accession_log` | `accession_id` |
| `circulation_records.borrower_id` | `borrowers` | `borrower_id` |
| `circulation_records.processed_by` | `user_accounts` | `user_id` |
| `request_records.requester_id` | `borrowers` | `borrower_id` |
| `request_records.matched_book_id` | `book_catalog` | `book_id` |
| `request_records.reviewed_by` | `user_accounts` | `user_id` |
| `procurement_log.request_id` | `request_records` | `request_id` |
| `procurement_log.book_id` | `book_catalog` | `book_id` |
| `inventory_status.accession_id` | `accession_log` | `accession_id` |
| `inventory_status.checked_by` | `user_accounts` | `user_id` |
| `inventory_sessions.librarian_id` | `user_accounts` | `user_id` |
| `reservation_queue.book_id` | `book_catalog` | `book_id` |
| `reservation_queue.borrower_id` | `borrowers` | `borrower_id` |
| `notification_log.recipient_id` | `borrowers` | `borrower_id` |
| `user_favorites.user_id` | `user_accounts` | `user_id` |
| `user_favorites.book_id` | `book_catalog` | `book_id` |
| `analytics_cache.generated_by` | `user_accounts` | `user_id` |

---

## Seed Data

```sql
INSERT INTO roles (role_name) VALUES
    ('Student'),
    ('Faculty'),
    ('Librarian'),
    ('Admin')
ON CONFLICT (role_name) DO NOTHING;
```

---

## CHECK Constraints Summary

| Table | Column | Allowed Values |
|-------|--------|----------------|
| `user_accounts` | `account_status` | `'active'`, `'disabled'`, `'pending'` |
| `borrowers` | `borrower_status` | `'active'`, `'blocked'` |
| `book_catalog` | `catalog_status` | `'active'`, `'archived'` |
| `accession_log` | `source` | `'purchase'`, `'donation'` (nullable) |
| `request_records` | `request_status` | `'pending_review'`, `'existing_in_collection'`, `'approved'`, `'rejected'`, `'procured'` |
| `procurement_log` | `order_status` | `'for_ordering'`, `'ordered'`, `'delivered'`, `'cancelled'`, `'out_of_stock'`, `'procured'` |
| `circulation_records` | `borrow_type` | `'overnight'`, `'daily_circulation'` |
| `circulation_records` | `transaction_type` | `'borrow'`, `'return'` |
| `circulation_records` | `transaction_status` | `'active'`, `'returned'`, `'overdue'` |
| `inventory_status` | `inventory_state` | `'available'`, `'borrowed'`, `'lost'`, `'damaged'`, `'missing'` |
| `inventory_status` | `inventory_type` | `'realtime_scan'`, `'annual_physical'` |
| `inventory_sessions` | `session_status` | `'active'`, `'completed'`, `'cancelled'` |
| `reservation_queue` | `reservation_status` | `'waiting'`, `'allocated'`, `'claimed'`, `'expired'` |
| `notification_log` | `notif_type` | `'status_update'`, `'hold_ready'`, `'overdue_reminder'` |
| `analytics_cache` | `report_type` | `'books_borrowed_per_program'`, `'utilization_rate'`, `'most_borrowed_titles'`, `'underutilized_titles'`, `'online_resource_usage'` |

---

## UNIQUE Constraints

| Table | Column(s) |
|-------|-----------|
| `roles` | `role_name` |
| `user_accounts` | `email` |
| `user_accounts` | `oauth_sub` |
| `borrowers` | `user_id` |
| `borrowers` | `id_number` |
| `accession_log` | `accession_number` |
| `user_favorites` | `(user_id, book_id)` |

---

## Indexes

- All `PRIMARY KEY` columns are auto-indexed (SERIAL)
- All `UNIQUE` columns have a unique index
- No additional explicit indexes are defined (the `SELECT *` queries rely on sequential scan for small datasets — add indexes on `book_catalog(title)`, `book_catalog(author)`, and `book_catalog(isbn)` if performance becomes an issue)
