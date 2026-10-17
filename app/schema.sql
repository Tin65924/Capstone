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
                   CHECK (account_status IN ('active', 'disabled', 'pending', 'archived')),
    created_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMP,
    updated_by     INT REFERENCES user_accounts(user_id)
);

CREATE TABLE IF NOT EXISTS audit_trail (
    log_id        SERIAL PRIMARY KEY,
    user_id       INT REFERENCES user_accounts(user_id),
    activity      VARCHAR(255) NOT NULL,
    session_token VARCHAR(255),
    log_timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS borrowers (
    borrower_id     SERIAL PRIMARY KEY,
    user_id         INT UNIQUE NOT NULL REFERENCES user_accounts(user_id),
    id_number       VARCHAR(30) UNIQUE NOT NULL,
    department      VARCHAR(100),
    phone_number    VARCHAR(30),
    borrower_status VARCHAR(20) NOT NULL DEFAULT 'active'
                    CHECK (borrower_status IN ('active', 'blocked')),
    updated_at      TIMESTAMP,
    updated_by      INT REFERENCES user_accounts(user_id)
);

ALTER TABLE borrowers ADD COLUMN IF NOT EXISTS phone_number VARCHAR(30);

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
    date_added            DATE NOT NULL DEFAULT CURRENT_DATE,
    updated_at            TIMESTAMP,
    updated_by            INT REFERENCES user_accounts(user_id)
);

CREATE TABLE IF NOT EXISTS accession_log (
    accession_id     SERIAL PRIMARY KEY,
    accession_number VARCHAR(30) UNIQUE NOT NULL,
    book_id          INT NOT NULL REFERENCES book_catalog(book_id),
    librarian_id     INT NOT NULL REFERENCES user_accounts(user_id),
    date_accessioned DATE NOT NULL DEFAULT CURRENT_DATE,
    source           VARCHAR(20) CHECK (source IN ('purchase', 'donation', 'others')),
    updated_at       TIMESTAMP,
    updated_by       INT REFERENCES user_accounts(user_id)
);

CREATE TABLE IF NOT EXISTS request_records (
    request_id     SERIAL PRIMARY KEY,
    requester_id   INT NOT NULL REFERENCES borrowers(borrower_id),
    book_title     VARCHAR(255) NOT NULL,
    author         VARCHAR(150),
    matched_book_id INT REFERENCES book_catalog(book_id),
    request_status VARCHAR(30) NOT NULL DEFAULT 'pending_review'
                   CHECK (request_status IN (
                       'pending_review', 'existing_in_collection',
                       'approved', 'rejected', 'procured', 'cancelled'
                   )),
    request_date   TIMESTAMP NOT NULL DEFAULT NOW(),
    reviewed_by    INT REFERENCES user_accounts(user_id),
    review_date    TIMESTAMP,
    remarks        VARCHAR(255),
    updated_at     TIMESTAMP,
    updated_by     INT REFERENCES user_accounts(user_id)
);

ALTER TABLE request_records ADD COLUMN IF NOT EXISTS remarks VARCHAR(255);

-- 'cancelled' lets members withdraw their own requests from /user/profile
-- before (or while) procurement orders them. The inline CHECK in the
-- CREATE TABLE above only exists on fresh databases, so re-declare the
-- constraint by name here for existing ones; the DROP+ADD pair converges
-- every boot and a failing ADD never blocks the rest (see run_schema).
ALTER TABLE request_records DROP CONSTRAINT IF EXISTS request_records_request_status_check;
ALTER TABLE request_records ADD CONSTRAINT request_records_request_status_check
    CHECK (request_status IN (
        'pending_review', 'existing_in_collection',
        'approved', 'rejected', 'procured', 'cancelled'
    ));

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
    remarks        VARCHAR(255),
    updated_at     TIMESTAMP,
    updated_by     INT REFERENCES user_accounts(user_id)
);

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
    due_date           TIMESTAMP,
    return_date        DATE,
    fine_amount        DECIMAL(8,2) NOT NULL DEFAULT 0.00,
    fine_paid          BOOLEAN NOT NULL DEFAULT FALSE,
    damage_notes       TEXT,
    lost_flag          BOOLEAN NOT NULL DEFAULT FALSE,
    transaction_status VARCHAR(20) NOT NULL
                       CHECK (transaction_status IN ('active', 'returned', 'overdue')),
    updated_at         TIMESTAMP,
    updated_by         INT REFERENCES user_accounts(user_id)
);

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

CREATE TABLE IF NOT EXISTS inventory_sessions (
    session_id     SERIAL PRIMARY KEY,
    librarian_id   INT NOT NULL REFERENCES user_accounts(user_id),
    total_books    INT NOT NULL,
    scanned_count  INT NOT NULL DEFAULT 0,
    session_status VARCHAR(20) NOT NULL DEFAULT 'active'
                   CHECK (session_status IN ('active', 'completed', 'cancelled')),
    started_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    ended_at       TIMESTAMP,
    updated_at     TIMESTAMP,
    updated_by     INT REFERENCES user_accounts(user_id)
);

ALTER TABLE inventory_status ADD COLUMN IF NOT EXISTS session_id INT REFERENCES inventory_sessions(session_id);
ALTER TABLE inventory_status ADD COLUMN IF NOT EXISTS notes VARCHAR(255);

CREATE TABLE IF NOT EXISTS reservation_queue (
    reservation_id     SERIAL PRIMARY KEY,
    book_id            INT NOT NULL REFERENCES book_catalog(book_id),
    borrower_id        INT NOT NULL REFERENCES borrowers(borrower_id),
    queue_position     INT NOT NULL,
    request_date       TIMESTAMP NOT NULL DEFAULT NOW(),
    reservation_status VARCHAR(20) NOT NULL
                       CHECK (reservation_status IN ('waiting', 'allocated', 'claimed', 'expired')),
    claim_deadline     TIMESTAMP,
    updated_at         TIMESTAMP,
    updated_by         INT REFERENCES user_accounts(user_id)
);

CREATE TABLE IF NOT EXISTS notification_log (
    notification_id SERIAL PRIMARY KEY,
    recipient_id    INT NOT NULL REFERENCES borrowers(borrower_id),
    message         VARCHAR(500) NOT NULL,
    notif_type      VARCHAR(30) NOT NULL
                    CHECK (notif_type IN ('status_update', 'hold_ready', 'overdue_reminder',
                                         'borrow', 'return', 'request_update', 'fine',
                                         'due_soon', 'reservation')),
    related_reference VARCHAR(50),
    is_read         BOOLEAN NOT NULL DEFAULT FALSE,
    date_sent       TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP,
    updated_by      INT REFERENCES user_accounts(user_id)
);

ALTER TABLE notification_log ADD COLUMN IF NOT EXISTS is_read BOOLEAN NOT NULL DEFAULT FALSE;

CREATE TABLE IF NOT EXISTS user_favorites (
    favorite_id SERIAL PRIMARY KEY,
    user_id     INT NOT NULL REFERENCES user_accounts(user_id),
    book_id     INT NOT NULL REFERENCES book_catalog(book_id),
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, book_id)
);

CREATE TABLE IF NOT EXISTS ebook_access_log (
    access_id     SERIAL PRIMARY KEY,
    book_id       INT NOT NULL REFERENCES book_catalog(book_id),
    access_kind   VARCHAR(20) NOT NULL
                  CHECK (access_kind IN ('read', 'download')),
    user_id       INT REFERENCES user_accounts(user_id),
    accessed_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMP,
    updated_by    INT REFERENCES user_accounts(user_id)
);

CREATE TABLE IF NOT EXISTS analytics_cache (
    cache_id       SERIAL PRIMARY KEY,
    report_type    VARCHAR(40) NOT NULL
                   CHECK (report_type IN (
                       'books_borrowed_per_program', 'utilization_rate',
                       'most_borrowed_titles', 'underutilized_titles',
                       'online_resource_usage',
                       'trend_borrowings', 'trend_overdue',
                       'trend_borrowings_by_program', 'trend_overdue_by_program',
                       'top_categories', 'top_categories_by_program',
                       'peak_periods', 'top_books', 'top_books_by_program',
                       'fines_by_book', 'high_demand', 'by_user_type',
                       'collection_by_category', 'copies_by_status',
                       'recent_circulation', 'recent_collection',
                       'circulation_summary',
                       'borrowers_by_department', 'overdue_by_department',
                       'department_leaderboard',
                       'top_requested_titles', 'requests_by_role',
                       'requests_trend', 'requests_by_program',
                       'ebook_trend', 'top_ebooks'
                    )),
    filter_params  JSONB,
    kpi_data       JSONB NOT NULL,
    generated_by   INT REFERENCES user_accounts(user_id),
    generated_date TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Prod deployments predate the e-book report types; re-apply the widened
-- report_type check (mirrors the request_records status-check pattern).
ALTER TABLE analytics_cache DROP CONSTRAINT IF EXISTS analytics_cache_report_type_check;
ALTER TABLE analytics_cache ADD CONSTRAINT analytics_cache_report_type_check
    CHECK (report_type IN (
        'books_borrowed_per_program', 'utilization_rate',
        'most_borrowed_titles', 'underutilized_titles',
        'online_resource_usage',
        'trend_borrowings', 'trend_overdue',
        'trend_borrowings_by_program', 'trend_overdue_by_program',
        'top_categories', 'top_categories_by_program',
        'peak_periods', 'top_books', 'top_books_by_program',
        'fines_by_book', 'high_demand', 'by_user_type',
        'collection_by_category', 'copies_by_status',
        'recent_circulation', 'recent_collection',
        'circulation_summary',
        'borrowers_by_department', 'overdue_by_department',
        'department_leaderboard',
        'top_requested_titles', 'requests_by_role',
        'requests_trend', 'requests_by_program',
        'ebook_trend', 'top_ebooks'
    ));

INSERT INTO roles (role_name) VALUES
    ('Student'),
    ('Faculty'),
    ('Librarian'),
    ('Admin')
ON CONFLICT (role_name) DO NOTHING;

CREATE TABLE IF NOT EXISTS backup_log (
    backup_id   SERIAL PRIMARY KEY,
    filename    VARCHAR(255) NOT NULL,
    size_bytes  BIGINT,
    status      VARCHAR(20) NOT NULL DEFAULT 'completed'
                CHECK (status IN ('completed', 'failed', 'in_progress')),
    backup_type VARCHAR(20) NOT NULL DEFAULT 'manual'
                CHECK (backup_type IN ('manual', 'scheduled')),
    error_msg   VARCHAR(500),
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS library_settings (
    setting_key   VARCHAR(60) PRIMARY KEY,
    setting_value TEXT NOT NULL,
    description   VARCHAR(255),
    updated_at    TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_by    INT REFERENCES user_accounts(user_id)
);

INSERT INTO library_settings (setting_key, setting_value, description) VALUES
    ('MAX_BORROW_LIMIT_STUDENT', '3', 'Max active loans for students'),
    ('MAX_BORROW_LIMIT_FACULTY', '5', 'Max active loans for faculty'),
    ('OVERNIGHT_DUE_DAYS_STUDENT', '1', 'Overnight loan due days for students'),
    ('OVERNIGHT_DUE_DAYS_FACULTY', '7', 'Overnight loan due days for faculty'),
    ('OVERDUE_FINE_PER_DAY', '5.0', 'Overdue fine in pesos per day'),
    ('OVERDUE_GRACE_DAYS', '0', 'Grace days before fines accrue'),
    ('RESERVATION_CLAIM_HOURS', '2', 'Hours to claim an allocated reservation (2-hour pickup window)'),
    ('DUE_SOON_NOTIFY_DAYS', '2', 'Days before due date to send due-soon reminders'),
    ('LIBRARY_OPENING_TIME', '08:00', 'Daily opening hour (HH:MM, 24-hour)'),
    ('LIBRARY_CLOSING_TIME', '17:00', 'Daily closing hour (HH:MM, 24-hour)'),
    ('LIBRARY_OPEN_DAYS', 'Monday,Tuesday,Wednesday,Thursday,Friday,Saturday', 'Days the library is open (borrowing blocked on other days)'),
    ('LIBRARY_MONTH_DAYS', '', 'Per-date open map YYYY-MM:bits for the current month (empty = weekly pattern applies)')
ON CONFLICT (setting_key) DO NOTHING;

-- Removed settings: the reservation cutoff is derived from closing time
-- minus claim hours; the legacy days fallback, the daily-circulation due
-- setting, the weeding lifespan, and the daily-max-hours cap are retired
-- (daily loans now run until closing time).
DELETE FROM library_settings
WHERE setting_key IN ('RESERVATION_CUTOFF_TIME', 'RESERVATION_CLAIM_DAYS',
                      'DAILY_CIRCULATION_DUE_DAYS', 'BOOK_LIFESPAN_YEARS',
                      'DAILY_MAX_HOURS');

-- Controlled vocabulary for book categories. Cataloging stores the
-- canonical name in book_catalog.subject_classification and the FK in
-- book_catalog.category_id (resolved case-insensitively so 'computer
-- science' and 'Computer Science' share one row). Analytics GROUP BYs
-- read the canonical name through the FK.
CREATE TABLE IF NOT EXISTS categories (
    category_id SERIAL PRIMARY KEY,
    name        VARCHAR(100) UNIQUE NOT NULL
);

ALTER TABLE book_catalog ADD COLUMN IF NOT EXISTS category_id INT REFERENCES categories(category_id);

-- Backfill: one category per distinct subject (case-insensitive dedup,
-- alphabetically-first casing wins), then link every unlinked book
-- case-insensitively. Idempotent: re-runs only fill gaps.
INSERT INTO categories (name)
SELECT DISTINCT ON (LOWER(TRIM(subject_classification))) TRIM(subject_classification)
FROM book_catalog
WHERE subject_classification IS NOT NULL AND TRIM(subject_classification) != ''
ORDER BY LOWER(TRIM(subject_classification)), TRIM(subject_classification)
ON CONFLICT (name) DO NOTHING;

UPDATE book_catalog SET category_id = categories.category_id FROM categories
WHERE book_catalog.category_id IS NULL
  AND book_catalog.subject_classification IS NOT NULL
  AND LOWER(categories.name) = LOWER(TRIM(book_catalog.subject_classification));

-- Secondary categories per title (the primary stays book_catalog.category_id
-- so analytics GROUP BYs keep one row per book). Links vanish with the book.
CREATE TABLE IF NOT EXISTS book_categories (
    book_id     INT NOT NULL REFERENCES book_catalog(book_id) ON DELETE CASCADE,
    category_id INT NOT NULL REFERENCES categories(category_id) ON DELETE CASCADE,
    PRIMARY KEY (book_id, category_id)
);

-- A title's primary category (book_catalog.category_id) must never also
-- be linked in book_categories, or the detail page lists it twice. Clean
-- up links already stored by earlier builds that echoed the primary back
-- as an extra. Idempotent.
DELETE FROM book_categories bc
USING book_catalog b
WHERE bc.book_id = b.book_id AND bc.category_id = b.category_id;

-- Retired material types: 'Multimedia' was removed from the catalog
-- vocabulary; any lingering rows fold into the general 'Book' type so
-- they stay searchable, editable, and borrowable. Idempotent.
UPDATE book_catalog SET material_type = 'Book' WHERE material_type = 'Multimedia';

-- E-book access link (Google Drive / publisher URL). Nullable: only
-- meaningful for E-Book titles, shown as Read/Preview actions.
ALTER TABLE book_catalog ADD COLUMN IF NOT EXISTS ebook_url VARCHAR(500);

-- Controlled vocabulary for borrower programs (students) and departments
-- (faculty). Registration, profile, and user-management forms only accept
-- values from this table; borrowers.department stores the canonical name.
-- No seed rows: librarians add programs/departments via User Management.
CREATE TABLE IF NOT EXISTS departments (
    department_id SERIAL PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    dept_type     VARCHAR(20) NOT NULL
                  CHECK (dept_type IN ('program', 'department')),
    status        VARCHAR(20) NOT NULL DEFAULT 'active'
                  CHECK (status IN ('active', 'inactive')),
    UNIQUE (dept_type, name)
);

-- Active/inactive toggle for programs & departments. Inactive entries
-- stay in the table (borrower history intact) but are hidden from every
-- registration/profile option. Idempotent for existing databases.
ALTER TABLE departments ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'active';

-- Audit columns (Updated By / Updated Date) for every table editable via
-- the frontend. inventory_status already audits via checked_by /
-- last_checked_date and library_settings via updated_at / updated_by,
-- so they are intentionally excluded here. IF NOT EXISTS keeps this
-- idempotent for existing databases (run_schema re-applies this file).
ALTER TABLE user_accounts ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;
ALTER TABLE user_accounts ADD COLUMN IF NOT EXISTS updated_by INT REFERENCES user_accounts(user_id);
ALTER TABLE borrowers ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;
ALTER TABLE borrowers ADD COLUMN IF NOT EXISTS updated_by INT REFERENCES user_accounts(user_id);
ALTER TABLE book_catalog ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;
ALTER TABLE book_catalog ADD COLUMN IF NOT EXISTS updated_by INT REFERENCES user_accounts(user_id);
ALTER TABLE accession_log ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;
ALTER TABLE accession_log ADD COLUMN IF NOT EXISTS updated_by INT REFERENCES user_accounts(user_id);
ALTER TABLE request_records ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;
ALTER TABLE request_records ADD COLUMN IF NOT EXISTS updated_by INT REFERENCES user_accounts(user_id);
ALTER TABLE procurement_log ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;
ALTER TABLE procurement_log ADD COLUMN IF NOT EXISTS updated_by INT REFERENCES user_accounts(user_id);
ALTER TABLE circulation_records ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;
ALTER TABLE circulation_records ADD COLUMN IF NOT EXISTS updated_by INT REFERENCES user_accounts(user_id);
ALTER TABLE circulation_records ADD COLUMN IF NOT EXISTS fine_paid BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE reservation_queue ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;
ALTER TABLE reservation_queue ADD COLUMN IF NOT EXISTS updated_by INT REFERENCES user_accounts(user_id);
ALTER TABLE inventory_sessions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;
ALTER TABLE inventory_sessions ADD COLUMN IF NOT EXISTS updated_by INT REFERENCES user_accounts(user_id);
ALTER TABLE notification_log ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;
ALTER TABLE notification_log ADD COLUMN IF NOT EXISTS updated_by INT REFERENCES user_accounts(user_id);

-- Read-path indexes for catalog scale (4.5k+ books). Plain btree covers
-- prefix ILIKE, equality filters, joins, and ORDER BY; UNIQUE constraints
-- elsewhere already index their columns, so they are not repeated here.
-- IF NOT EXISTS keeps the re-applied schema idempotent; a failing
-- statement never blocks the rest (see run_schema).
CREATE INDEX IF NOT EXISTS idx_book_catalog_status ON book_catalog (catalog_status);
CREATE INDEX IF NOT EXISTS idx_book_catalog_title ON book_catalog (title);
CREATE INDEX IF NOT EXISTS idx_book_catalog_author ON book_catalog (author);
CREATE INDEX IF NOT EXISTS idx_book_catalog_isbn ON book_catalog (isbn);
CREATE INDEX IF NOT EXISTS idx_book_catalog_subject ON book_catalog (subject_classification);
CREATE INDEX IF NOT EXISTS idx_book_catalog_year ON book_catalog (year_published);
CREATE INDEX IF NOT EXISTS idx_accession_log_book ON accession_log (book_id);
CREATE INDEX IF NOT EXISTS idx_accession_log_number ON accession_log (accession_number);
CREATE INDEX IF NOT EXISTS idx_circ_accession ON circulation_records (accession_id);
CREATE INDEX IF NOT EXISTS idx_circ_book ON circulation_records (book_id);
CREATE INDEX IF NOT EXISTS idx_circ_status ON circulation_records (transaction_status);
CREATE INDEX IF NOT EXISTS idx_circ_borrow_date ON circulation_records (borrow_date);
CREATE INDEX IF NOT EXISTS idx_borrowers_department ON borrowers (department);
CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_trail (log_timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_trail (user_id);
CREATE INDEX IF NOT EXISTS idx_reservation_book ON reservation_queue (book_id);
CREATE INDEX IF NOT EXISTS idx_reservation_status ON reservation_queue (reservation_status);
CREATE INDEX IF NOT EXISTS idx_inventory_accession ON inventory_status (accession_id);
CREATE INDEX IF NOT EXISTS idx_requests_status ON request_records (request_status);
CREATE INDEX IF NOT EXISTS idx_requests_requester ON request_records (requester_id);
CREATE INDEX IF NOT EXISTS idx_ebook_access_book ON ebook_access_log (book_id);
CREATE INDEX IF NOT EXISTS idx_ebook_access_time ON ebook_access_log (accessed_at);
CREATE INDEX IF NOT EXISTS idx_notif_recipient ON notification_log (recipient_id);
CREATE INDEX IF NOT EXISTS idx_user_accounts_status ON user_accounts (account_status);
CREATE INDEX IF NOT EXISTS idx_user_accounts_role ON user_accounts (role_id);
-- Race guards for concurrent borrows/reserves (F2): the app checks
-- first (SELECT-then-INSERT), but two simultaneous POSTs can both pass
-- the check. These partial unique indexes make the loser fail with a
-- unique violation instead of creating a duplicate loan/reservation;
-- routes catch it and ask the user to refresh. IF NOT EXISTS keeps the
-- re-applied schema idempotent; pre-existing duplicates only log a
-- skip-warning in run_schema without blocking the rest.
CREATE UNIQUE INDEX IF NOT EXISTS uq_active_loan_per_accession ON circulation_records (accession_id) WHERE transaction_status IN ('active', 'overdue');
CREATE UNIQUE INDEX IF NOT EXISTS uq_active_loan_per_book_borrower ON circulation_records (book_id, borrower_id) WHERE transaction_status IN ('active', 'overdue');
CREATE UNIQUE INDEX IF NOT EXISTS uq_active_reservation_per_book_borrower ON reservation_queue (book_id, borrower_id) WHERE reservation_status IN ('waiting', 'allocated');
-- Queue-position race net (F2 follow-up): get_next_queue_position() is
-- SELECT-then-INSERT, so two simultaneous reserves can compute the same
-- MAX(pos)+1. The loser fails here instead of silently sharing a queue
-- slot; routes retry with a fresh position (see _create_reservation_retry).
CREATE UNIQUE INDEX IF NOT EXISTS uq_active_queue_pos ON reservation_queue (book_id, queue_position) WHERE reservation_status IN ('waiting', 'allocated');
-- Pending-request race net: routes .strip() titles and the app fuzzy layer
-- handles case, so LOWER(TRIM()) here is only a best-effort race net for
-- exact-match double-submits — near-duplicates still rely on the app layer.
CREATE UNIQUE INDEX IF NOT EXISTS uq_pending_req ON request_records (requester_id, LOWER(TRIM(book_title))) WHERE request_status = 'pending_review';

-- Due dates carry hours (library closing, 5:00 PM) instead of bare dates.
-- Midnight legacy rows keep exact semantics: every overdue/due-soon
-- comparison in the app uses date parts (due_date::date), so old and new
-- rows behave identically. Re-running this ALTER on an already-TIMESTAMP
-- column is a harmless no-op, keeping run_schema idempotent.
ALTER TABLE circulation_records ALTER COLUMN due_date TYPE TIMESTAMP USING due_date::timestamp;
