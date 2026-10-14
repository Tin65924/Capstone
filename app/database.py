import os
import psycopg2
from psycopg2 import pool
from flask import current_app, g

class Database:
    """Threaded PostgreSQL connection pool wrapper used by every model module.

    Holds a single psycopg2 ThreadedConnectionPool and binds one pooled
    connection per Flask request via ``flask.g``. All SQL in the codebase
    flows through this class so transaction handling, broken-connection
    recovery, and pool return live in one place.
    """

    def __init__(self, app=None):
        """Create the wrapper, optionally binding it to a Flask app immediately.

        Args:
            app: Flask application to call :meth:`init_app` on, or None to
                bind later (the module-level ``db`` singleton uses this).
        """
        self._pool = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Build the connection pool from app config and register teardown.

        Reads ``DATABASE_URL`` from the Flask config, adds connect timeout
        and TCP keepalive parameters, creates a ThreadedConnectionPool
        (1-10 connections), and registers :meth:`close_connection` as the
        app-context teardown so each request returns its connection.

        Args:
            app: Flask application whose config holds DATABASE_URL.
        """
        dsn = _with_conn_params(app.config['DATABASE_URL'])
        self._pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=dsn
        )
        app.teardown_appcontext(self.close_connection)

    def get_connection(self):
        """Return the current request's pooled PostgreSQL connection.

        Reuses the connection stored on ``flask.g`` when one already exists
        for this request, otherwise checks one out of the pool. Validates
        the checkout with ``SELECT 1`` because hosting providers
        (Render/Neon/Supabase) silently close idle connections, and a dead
        pooled connection would otherwise cause a random 500 on the next
        page load. A failed validation discards that slot and checks out
        a fresh connection.

        Returns:
            A live psycopg2 connection bound to the current request.
        """
        if 'db_conn' in g:
            return g.db_conn
        conn = self._pool.getconn()
        # Validate pooled connections: Render/Neon/Supabase close idle
        # connections, and psycopg2 does not check on checkout. A dead
        # conn would otherwise 500 the next page navigation at random.
        try:
            with conn.cursor() as cur:
                cur.execute('SELECT 1')
            # No commit/rollback here on success: the validation SELECT
            # joins the request's transaction, which execute() commits.
            # (A separate rollback/commit would break transaction tests
            # and leave nothing for the real query to clean up.)
        except Exception:
            try:
                self._pool.putconn(conn, close=True)
            except Exception:
                pass
            g.pop('db_conn', None)
            conn = self._pool.getconn()
        g.db_conn = conn
        return conn

    def close_connection(self, exc=None):
        """Return the current request's connection to the pool at teardown.

        Pops ``db_conn`` off ``flask.g`` and puts it back in the pool,
        closing the slot instead when the connection is already dead. Any
        teardown error is swallowed so teardown itself never raises.

        Args:
            exc: Exception that ended the request, if any (ignored; required
                by the Flask teardown signature).
        """
        conn = g.pop('db_conn', None)
        if conn is not None:
            try:
                if getattr(conn, 'closed', 0):
                    self._pool.putconn(conn, close=True)
                else:
                    self._pool.putconn(conn)
            except Exception:
                pass

    def execute(self, query, params=None):
        """Run any SQL statement and commit it, rolling back on failure.

        This is the single choke point for all database access: every
        ``fetch_one``/``fetch_all``/write in every ``models.py`` calls
        through here. SELECT statements return a list of positional tuple
        rows; INSERT/UPDATE/DELETE return the cursor rowcount, except an
        INSERT ... RETURNING which returns its returned rows. Commits after
        every statement (including reads) so pooled connections never sit
        idle-in-transaction holding locks that would block DDL such as a
        backup restore. On error the transaction is rolled back, a broken
        connection is discarded rather than returned to the pool, a warning
        is logged, and the original exception is re-raised for the route's
        error handler.

        Args:
            query: SQL string with ``%s`` placeholders (never f-string
                interpolated values).
            params: Tuple/list of bound parameters, or None.

        Returns:
            List of row tuples for statements that return rows, otherwise
            the affected-row count.

        Raises:
            Exception: Whatever psycopg2 raised, after rollback.
        """
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
            try:
                conn.rollback()
            except Exception:
                pass
            # Never return a broken connection to the pool to be reused
            # by the next page navigation.
            try:
                if getattr(conn, 'closed', 0):
                    self._pool.putconn(conn, close=True)
                    g.pop('db_conn', None)
            except Exception:
                pass
            try:
                current_app.logger.warning('DB query failed: %s', e)
            except Exception:
                pass
            raise e

    def fetch_one(self, query, params=None):
        """Fetch a single row for a SELECT expected to match zero or one rows.

        Convenience wrapper over :meth:`execute` used by all ``get_*``
        single-row model lookups. Returns the first positional tuple or
        None when nothing matched.

        Args:
            query: SELECT SQL with ``%s`` placeholders.
            params: Bound parameters, or None.

        Returns:
            The first row tuple, or None if the query returned no rows.
        """
        rows = self.execute(query, params)
        return rows[0] if rows else None

    def fetch_all(self, query, params=None):
        """Fetch every row for a SELECT expected to match many rows.

        Convenience wrapper over :meth:`execute` used by all list/search
        model queries. SELECT column order is the tuple contract callers
        index into. Returns an empty list (or rowcount passthrough from the
        mock in tests) when nothing matched.

        Args:
            query: SELECT SQL with ``%s`` placeholders.
            params: Bound parameters, or None.

        Returns:
            List of row tuples (possibly empty).
        """
        return self.execute(query, params)

db = Database()


def _with_conn_params(dsn, seconds=10):
    """Append connect_timeout + TCP keepalives so idle pooled connections survive.

    Without keepalives, Render/Neon/Supabase close idle connections and
    the next page navigation reuses the dead slot -> random 500.
    Handles both URL-style (postgresql://...) and keyword-style
    (host=... dbname=...) DSNs; leaves explicit values untouched.
    """
    if not isinstance(dsn, str):
        return dsn
    url_params = {
        'connect_timeout': str(seconds),
        'keepalives_idle': '60',
        'keepalives_interval': '10',
        'keepalives_count': '5',
    }
    kw_params = {
        'connect_timeout': str(seconds),
        'keepalives_idle': '60',
        'keepalives_interval': '10',
        'keepalives_count': '5',
    }
    if '://' in dsn:
        for key, value in url_params.items():
            if key not in dsn:
                sep = '&' if '?' in dsn else '?'
                dsn = f'{dsn}{sep}{key}={value}'
        return dsn
    for key, value in kw_params.items():
        if key not in dsn:
            spacer = ' ' if dsn and not dsn.endswith(' ') else ''
            dsn = f'{dsn}{spacer}{key}={value}'
    return dsn


def _with_connect_timeout(dsn, seconds=10):
    """Backwards-compatible wrapper (tests/imports may reference it)."""
    return _with_conn_params(dsn, seconds=seconds)


def run_schema(app):
    """Apply schema.sql plus follow-up constraint patches at app startup.

    Reads ``app/schema.sql`` (the idempotent source of truth, safe to
    re-apply), strips full-line ``--`` comments, and executes it
    statement-by-statement so one failing statement never rolls back the
    whole schema into an empty database. Then applies extra ALTER TABLE
    patches (account/backup/accession status checks, phone/is_read
    columns, notification and analytics-cache checks) the same way.
    Skips entirely with a warning when schema.sql is missing or a
    statement fails, logging applied/skipped counts. Never raises.

    Args:
        app: Flask application providing config and ``logger``.
    """
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    if not os.path.isfile(schema_path):
        app.logger.warning('schema.sql not found — skipping schema initialization')
        return
    conn = db._pool.getconn()
    try:
        def _exec_each(statements):
            """Execute one batch of raw DDL statements, counting results.

            Runs each non-blank statement on the schema connection with an
            immediate commit, rolling back and warning per failed
            statement instead of aborting the batch, so a partially
            initialized database still converges on restart.

            Args:
                statements: Iterable of raw SQL statement strings.

            Returns:
                Tuple (ok, failed) of applied vs skipped statement counts.
            """
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
    """Initialize the connection pool and sync the schema for the app.

    Calls :meth:`Database.init_app` to build the pool, then unless
    ``SKIP_SCHEMA_SYNC`` is set in config (used by tooling/tests),
    invokes :func:`run_schema` to re-apply the idempotent schema at
    every startup.

    Args:
        app: Flask application to initialize database access for.
    """
    db.init_app(app)
    if app.config.get('SKIP_SCHEMA_SYNC'):
        app.logger.info('SKIP_SCHEMA_SYNC is set — skipping schema initialization.')
        return
    run_schema(app)
