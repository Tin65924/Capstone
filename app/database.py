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
        def _exec_each(statements):
            ok, failed = 0, 0
            with conn.cursor() as cur:
                for stmt in statements:
                    stmt = stmt.strip()
                    if not stmt:
                        continue
                    try:
                        cur.execute(stmt)
                        conn.commit()
                        ok += 1
                    except Exception as e:
                        conn.rollback()
                        failed += 1
                        app.logger.warning('Schema statement skipped: %s | %.120s',
                                           e, stmt)
            return ok, failed

        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        # Drop full-line -- comments first: after splitting on ';' they
        # would otherwise execute as bare text and spam skip-warnings.
        schema_sql = '\n'.join(
            line for line in schema_sql.splitlines()
            if not line.strip().startswith('--')
        )
        # Statement-by-statement (schema.sql is plain DDL, no function
        # bodies): one failing statement must never roll back the whole
        # schema into an empty database again.
        ok, failed = _exec_each(schema_sql.split(';'))
        ok2, failed2 = _exec_each([
            """
                ALTER TABLE user_accounts
                DROP CONSTRAINT IF EXISTS user_accounts_account_status_check;
            """,
            """
                ALTER TABLE user_accounts
                ADD CONSTRAINT user_accounts_account_status_check
                CHECK (account_status IN ('active', 'disabled', 'pending', 'archived'));
            """,
            """
                ALTER TABLE backup_log
                DROP CONSTRAINT IF EXISTS backup_log_status_check;
            """,
            """
                ALTER TABLE backup_log
                ADD CONSTRAINT backup_log_status_check
                CHECK (status IN ('completed', 'failed', 'in_progress'));
            """,
            """
                ALTER TABLE accession_log
                DROP CONSTRAINT IF EXISTS accession_log_source_check;
            """,
            """
                ALTER TABLE accession_log
                ADD CONSTRAINT accession_log_source_check
                CHECK (source IN ('purchase', 'donation', 'others'));
            """,
            """
                ALTER TABLE borrowers ADD COLUMN IF NOT EXISTS phone_number VARCHAR(30);
            """,
            """
                ALTER TABLE notification_log ADD COLUMN IF NOT EXISTS is_read BOOLEAN NOT NULL DEFAULT FALSE;
            """,
            """
                ALTER TABLE notification_log
                DROP CONSTRAINT IF EXISTS notification_log_notif_type_check;
            """,
            """
                ALTER TABLE notification_log
                ADD CONSTRAINT notification_log_notif_type_check
                CHECK (notif_type IN ('status_update', 'hold_ready', 'overdue_reminder',
                                      'borrow', 'return', 'request_update', 'fine',
                                      'due_soon', 'reservation'));
            """,
            """
                ALTER TABLE analytics_cache
                DROP CONSTRAINT IF EXISTS analytics_cache_report_type_check;
            """,
            """
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
            """,
        ])
        app.logger.info('Database schema initialized: %d applied, %d skipped.',
                        ok + ok2, failed + failed2)
    except Exception as e:
        conn.rollback()
        app.logger.warning('Schema initialization skipped (may already exist): %s', e)
    finally:
        db._pool.putconn(conn)


def init_db(app):
    db.init_app(app)
    if app.config.get('SKIP_SCHEMA_SYNC'):
        app.logger.info('SKIP_SCHEMA_SYNC is set — skipping schema initialization.')
        return
    run_schema(app)
