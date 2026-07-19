-- ============================================================
-- LMS Database Schema — PostgreSQL
-- Run after CREATE DATABASE library_db;
-- ============================================================

-- 1. Identity & Access (Module 6)
CREATE TABLE IF NOT EXISTS roles (
    role_id   SERIAL PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL,
    permissions JSONB
);

CREATE TABLE IF NOT EXISTS user_accounts (
    user_id        SERIAL PRIMARY KEY,
    email          VARCHAR(100) UNIQUE NOT NULL,
    oauth_sub      VARCHAR(255) UNIQUE NOT NULL,
    full_name      VARCHAR(150) NOT NULL,
    role_id        INT NOT NULL REFERENCES roles(role_id),
    account_status VARCHAR(20) NOT NULL DEFAULT 'active'
                   CHECK (account_status IN ('active', 'disabled')),
    created_at     TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_trail (
    log_id        SERIAL PRIMARY KEY,
    user_id       INT REFERENCES user_accounts(user_id),
    activity      VARCHAR(255) NOT NULL,
    session_token VARCHAR(255),
    log_timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 2. Borrowers (extension of user_accounts — Students & Faculty only)
CREATE TABLE IF NOT EXISTS borrowers (
    borrower_id     SERIAL PRIMARY KEY,
    user_id         INT UNIQUE NOT NULL REFERENCES user_accounts(user_id),
    id_number       VARCHAR(30) UNIQUE NOT NULL,
    department      VARCHAR(100),
    borrower_status VARCHAR(20) NOT NULL DEFAULT 'active'
                    CHECK (borrower_status IN ('active', 'blocked'))
);

-- 3. Cataloging & Accessioning (Module 2)
CREATE TABLE IF NOT EXISTS book_catalog (
    book_id               SERIAL PRIMARY KEY,
    title                 VARCHAR(255) NOT NULL,
    author                VARCHAR(150) NOT NULL,
    edition               VARCHAR(30),
    publisher             VARCHAR(150),
    year_published        INT,
    subject_classification VARCHAR(100),
    call_number           VARCHAR(50),
    isbn                  VARCHAR(20),
    material_type         VARCHAR(30) NOT NULL DEFAULT 'Book',
    description           TEXT,
    catalog_status        VARCHAR(20) NOT NULL DEFAULT 'active'
                          CHECK (catalog_status IN ('active', 'archived')),
    date_added            DATE NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS accession_log (
    accession_id     SERIAL PRIMARY KEY,
    accession_number VARCHAR(30) UNIQUE NOT NULL,
    book_id          INT NOT NULL REFERENCES book_catalog(book_id),
    copy_number      INT,
    librarian_id     INT NOT NULL REFERENCES user_accounts(user_id),
    date_accessioned DATE NOT NULL DEFAULT CURRENT_DATE,
    source           VARCHAR(20) CHECK (source IN ('purchase', 'donation'))
);

-- 4. Request Management (Module 1A) — depends on book_catalog, borrowers
CREATE TABLE IF NOT EXISTS request_records (
    request_id     SERIAL PRIMARY KEY,
    requester_id   INT NOT NULL REFERENCES borrowers(borrower_id),
    book_title     VARCHAR(255) NOT NULL,
    author         VARCHAR(150),
    matched_book_id INT REFERENCES book_catalog(book_id),
    request_status VARCHAR(30) NOT NULL DEFAULT 'pending_review'
                   CHECK (request_status IN (
                       'pending_review', 'existing_in_collection',
                       'approved', 'rejected', 'procured'
                   )),
    request_date   TIMESTAMP NOT NULL DEFAULT NOW(),
    reviewed_by    INT REFERENCES user_accounts(user_id),
    review_date    TIMESTAMP
);

-- 5. Procurement (Module 1B) — depends on request_records, book_catalog
CREATE TABLE IF NOT EXISTS procurement_log (
    procurement_id SERIAL PRIMARY KEY,
    request_id     INT NOT NULL REFERENCES request_records(request_id),
    order_status   VARCHAR(30) NOT NULL
                   CHECK (order_status IN (
                       'for_ordering', 'ordered', 'delivered',
                       'cancelled', 'out_of_stock', 'procured'
                   )),
    order_date     DATE NOT NULL,
    date_received  DATE,
    book_id        INT REFERENCES book_catalog(book_id),
    remarks        VARCHAR(255)
);

-- 6. Circulation (Module 3)
CREATE TABLE IF NOT EXISTS circulation_records (
    circulation_id     SERIAL PRIMARY KEY,
    book_id            INT NOT NULL REFERENCES book_catalog(book_id),
    accession_id       INT NOT NULL REFERENCES accession_log(accession_id),
    borrower_id        INT NOT NULL REFERENCES borrowers(borrower_id),
    processed_by       INT NOT NULL REFERENCES user_accounts(user_id),
    borrow_type        VARCHAR(30) NOT NULL
                       CHECK (borrow_type IN ('overnight', 'daily_circulation')),
    transaction_type   VARCHAR(20) NOT NULL
                       CHECK (transaction_type IN ('borrow', 'return')),
    borrow_date        DATE NOT NULL,
    due_date           DATE,
    return_date        DATE,
    fine_amount        DECIMAL(8,2) NOT NULL DEFAULT 0.00,
    damage_notes       TEXT,
    lost_flag          BOOLEAN NOT NULL DEFAULT FALSE,
    transaction_status VARCHAR(20) NOT NULL
                       CHECK (transaction_status IN ('active', 'returned', 'overdue'))
);

-- 7. Inventory Monitoring (Module 4)
CREATE TABLE IF NOT EXISTS inventory_status (
    inventory_id     SERIAL PRIMARY KEY,
    accession_id     INT NOT NULL REFERENCES accession_log(accession_id),
    inventory_state  VARCHAR(20) NOT NULL
                     CHECK (inventory_state IN ('available', 'borrowed', 'lost', 'damaged', 'missing')),
    inventory_type   VARCHAR(20) NOT NULL
                     CHECK (inventory_type IN ('realtime_scan', 'annual_physical')),
    checked_by       INT REFERENCES user_accounts(user_id),
    last_checked_date DATE NOT NULL
);

-- 8. Inventory Sessions (Module 4 — session tracking)
CREATE TABLE IF NOT EXISTS inventory_sessions (
    session_id     SERIAL PRIMARY KEY,
    librarian_id   INT NOT NULL REFERENCES user_accounts(user_id),
    total_books    INT NOT NULL,
    scanned_count  INT NOT NULL DEFAULT 0,
    session_status VARCHAR(20) NOT NULL DEFAULT 'active'
                   CHECK (session_status IN ('active', 'completed', 'cancelled')),
    started_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    ended_at       TIMESTAMP
);

-- 9. Reservations
CREATE TABLE IF NOT EXISTS reservation_queue (
    reservation_id     SERIAL PRIMARY KEY,
    book_id            INT NOT NULL REFERENCES book_catalog(book_id),
    borrower_id        INT NOT NULL REFERENCES borrowers(borrower_id),
    queue_position     INT NOT NULL,
    request_date       TIMESTAMP NOT NULL DEFAULT NOW(),
    reservation_status VARCHAR(20) NOT NULL
                       CHECK (reservation_status IN ('waiting', 'allocated', 'claimed', 'expired')),
    claim_deadline     TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notification_log (
    notification_id SERIAL PRIMARY KEY,
    recipient_id    INT NOT NULL REFERENCES borrowers(borrower_id),
    message         VARCHAR(500) NOT NULL,
    notif_type      VARCHAR(30) NOT NULL
                    CHECK (notif_type IN ('status_update', 'hold_ready', 'overdue_reminder')),
    related_reference VARCHAR(50),
    date_sent       TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 10. User Favorites / Wishlist
CREATE TABLE IF NOT EXISTS user_favorites (
    favorite_id SERIAL PRIMARY KEY,
    user_id     INT NOT NULL REFERENCES user_accounts(user_id),
    book_id     INT NOT NULL REFERENCES book_catalog(book_id),
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, book_id)
);

-- 11. Analytics Cache (Module 5)
CREATE TABLE IF NOT EXISTS analytics_cache (
    cache_id       SERIAL PRIMARY KEY,
    report_type    VARCHAR(40) NOT NULL
                   CHECK (report_type IN (
                       'books_borrowed_per_program', 'utilization_rate',
                       'most_borrowed_titles', 'underutilized_titles',
                       'online_resource_usage'
                   )),
    filter_params  JSONB,
    kpi_data       JSONB NOT NULL,
    generated_by   INT REFERENCES user_accounts(user_id),
    generated_date TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ============================================================
-- Seed Data
-- ============================================================
INSERT INTO roles (role_name) VALUES
    ('Student'),
    ('Faculty'),
    ('Librarian'),
    ('Admin')
ON CONFLICT (role_name) DO NOTHING;
