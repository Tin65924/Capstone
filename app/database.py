import os
import psycopg2
from psycopg2 import pool
from flask import current_app, g

class Database:
    def __init__(self, app=None):
        self._pool = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        dsn = app.config['DATABASE_URL']
        self._pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=dsn
        )
        app.teardown_appcontext(self.close_connection)

    def get_connection(self):
        if 'db_conn' not in g:
            g.db_conn = self._pool.getconn()
        return g.db_conn

    def close_connection(self, exc=None):
        conn = g.pop('db_conn', None)
        if conn is not None:
            self._pool.putconn(conn)

    def execute(self, query, params=None):
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                if cur.description:
                    rows = cur.fetchall()
                    # End the read transaction: otherwise the pooled
                    # connection sits idle-in-transaction holding shared
                    # locks, which blocks DDL (e.g. a backup restore's
                    # DROP TABLE) forever. Harmless under READ COMMITTED —
                    # every statement already sees the latest snapshot.
                    conn.commit()
                    return rows
                conn.commit()
                return cur.rowcount
        except Exception as e:
            conn.rollback()
            raise e

    def fetch_one(self, query, params=None):
        rows = self.execute(query, params)
        return rows[0] if rows else None

    def fetch_all(self, query, params=None):
        return self.execute(query, params)

db = Database()


def run_schema(app):
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    if not os.path.isfile(schema_path):
        app.logger.warning('schema.sql not found — skipping schema initialization')
        return
    conn = db._pool.getconn()
    try:
        with conn.cursor() as cur:
            with open(schema_path, 'r') as f:
                cur.execute(f.read())
            cur.execute("""
                ALTER TABLE user_accounts
                DROP CONSTRAINT IF EXISTS user_accounts_account_status_check;
            """)
            cur.execute("""
                ALTER TABLE user_accounts
                ADD CONSTRAINT user_accounts_account_status_check
                CHECK (account_status IN ('active', 'disabled', 'pending', 'archived'));
            """)
            cur.execute("""
                ALTER TABLE accession_log
                DROP CONSTRAINT IF EXISTS accession_log_source_check;
            """)
            cur.execute("""
                ALTER TABLE accession_log
                ADD CONSTRAINT accession_log_source_check
                CHECK (source IN ('purchase', 'donation', 'others'));
            """)
            cur.execute("""
                ALTER TABLE borrowers ADD COLUMN IF NOT EXISTS phone_number VARCHAR(30);
            """)
            cur.execute("""
                ALTER TABLE notification_log ADD COLUMN IF NOT EXISTS is_read BOOLEAN NOT NULL DEFAULT FALSE;
            """)
            cur.execute("""
                ALTER TABLE notification_log
                DROP CONSTRAINT IF EXISTS notification_log_notif_type_check;
            """)
            cur.execute("""
                ALTER TABLE notification_log
                ADD CONSTRAINT notification_log_notif_type_check
                CHECK (notif_type IN ('status_update', 'hold_ready', 'overdue_reminder',
                                      'borrow', 'return', 'request_update', 'fine',
                                      'due_soon', 'reservation'));
            """)
            cur.execute("""
                ALTER TABLE analytics_cache
                DROP CONSTRAINT IF EXISTS analytics_cache_report_type_check;
            """)
            cur.execute("""
                ALTER TABLE analytics_cache
                ADD CONSTRAINT analytics_cache_report_type_check
                CHECK (report_type IN (
                    'books_borrowed_per_program', 'utilization_rate',
                    'most_borrowed_titles', 'underutilized_titles',
                    'online_resource_usage',
                    'trend_borrowings', 'trend_overdue', 'top_categories',
                    'top_books', 'high_demand', 'by_user_type',
                    'collection_by_category', 'copies_by_status',
                    'recent_circulation', 'recent_collection',
                    'circulation_summary'
                ));
            """)
        conn.commit()
        app.logger.info('Database schema initialized successfully.')
    except Exception as e:
        conn.rollback()
        app.logger.warning('Schema initialization skipped (may already exist): %s', e)
    finally:
        db._pool.putconn(conn)


def init_db(app):
    db.init_app(app)
    run_schema(app)
