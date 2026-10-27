import os
import re
import time
from contextlib import contextmanager

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

    # A pooled connection used within this many seconds is assumed still
    # live; only older checkouts are probed with SELECT 1 (see
    # :meth:`get_connection`). 0 restores validate-on-every-checkout.
    # Overridable per app via DB_REVALIDATE_IDLE_SECONDS.
    _revalidate_idle_seconds = 30

    def __init__(self, app=None):
        """Create the wrapper, optionally binding it to a Flask app immediately.

        Args:
            app: Flask application to call :meth:`init_app` on, or None to
                bind later (the module-level ``db`` singleton uses this).
        """
        self._pool = None
        # Last-use stamps for pooled connections, used to skip the
        # revalidation probe on hot checkouts (see get_connection). Kept on
        # the wrapper rather than the connection object so it works for any
        # connection type.
        self._conn_used_at = {}
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Build the connection pool from app config and register teardown.

        Reads ``DATABASE_URL`` from the Flask config, adds connect timeout
        and TCP keepalive parameters, creates a ThreadedConnectionPool
        (sized by ``DB_POOL_MINCONN``/``DB_POOL_MAXCONN``), and registers
        :meth:`close_connection` as the app-context teardown so each
        request returns its connection.

        Args:
            app: Flask application whose config holds DATABASE_URL.
        """
        dsn = _with_conn_params(app.config['DATABASE_URL'])
        self._pool = pool.ThreadedConnectionPool(
            minconn=app.config.get('DB_POOL_MINCONN', 1),
            maxconn=app.config.get('DB_POOL_MAXCONN', 16),
            dsn=dsn
        )
        self._revalidate_idle_seconds = app.config.get(
            'DB_REVALIDATE_IDLE_SECONDS', self._revalidate_idle_seconds)
        app.teardown_appcontext(self.close_connection)

    def get_connection(self):
        """Return the current request's pooled PostgreSQL connection.

        Reuses the connection stored on ``flask.g`` when one already exists
        for this request, otherwise checks one out of the pool. Hosting
        providers (Render/Neon/Supabase) silently close idle connections
        and psycopg2 does not verify on checkout, but a ``SELECT 1`` on
        every request costs a full round-trip on a hot path. So a
        connection used within ``_revalidate_idle_seconds`` is assumed
        live; an older checkout is probed with ``SELECT 1`` and, if dead,
        its slot is discarded and a fresh connection checked out.

        Returns:
            A live psycopg2 connection bound to the current request.
        """
        if 'db_conn' in g:
            return g.db_conn
        conn = self._pool.getconn()
        # Validate only once a pooled connection may have gone stale; a slot
        # never seen before has no stamp and is always validated. The stamp
        # survives the connection's trips back into the pool, so a busy pool
        # pays at most one SELECT 1 per connection per window.
        now = time.monotonic()
        last_used = self._conn_used_at.get(conn)
        if last_used is None or now - last_used >= self._revalidate_idle_seconds:
            try:
                with conn.cursor() as cur:
                    cur.execute('SELECT 1')
                # No commit/rollback here on success: the validation SELECT
                # joins the request's transaction, which execute() commits.
                # (A separate rollback/commit would break transaction tests
                # and leave nothing for the real query to clean up.)
            except Exception:
                self._conn_used_at.pop(conn, None)
                try:
                    self._pool.putconn(conn, close=True)
                except Exception:
                    pass
                g.pop('db_conn', None)
                conn = self._pool.getconn()
        self._conn_used_at[conn] = now
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
                    self._conn_used_at.pop(conn, None)
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
                in_transaction = getattr(g, 'db_transaction_depth', 0) > 0
                if cur.description:
                    rows = cur.fetchall()
                    # End the read transaction: otherwise the pooled
                    # connection sits idle-in-transaction holding shared
                    # locks, which blocks DDL (e.g. a backup restore's
                    # DROP TABLE) forever. Harmless under READ COMMITTED —
                    # every statement already sees the latest snapshot.
                    if not in_transaction:
                        conn.commit()
                    return rows
                if not in_transaction:
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
            raise

    @contextmanager
    def transaction(self):
        """Group several database statements into one atomic transaction.

        Single-statement model methods retain ``execute``'s commit behavior.
        Multi-write workflows opt in to this context so an error rolls back
        every statement in the unit of work. Nested uses share the outer
        transaction. The no-pool branch keeps the lightweight mocked test
        database compatible with model-level transaction tests.
        """
        if self._pool is None:
            yield
            return

        conn = self.get_connection()
        depth = getattr(g, 'db_transaction_depth', 0)
        g.db_transaction_depth = depth + 1
        try:
            yield
            if depth == 0:
                conn.commit()
        except Exception:
            if depth == 0:
                conn.rollback()
            raise
        finally:
            if depth:
                g.db_transaction_depth = depth
            else:
                g.pop('db_transaction_depth', None)

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


class RequiredSchemaMigrationError(RuntimeError):
    """A required invariant could not be installed without operator review."""


def run_schema(app):
    """Apply schema.sql plus follow-up constraint patches at app startup.

    Reads ``app/schema.sql`` (the idempotent source of truth, safe to
    re-apply), strips full-line ``--`` comments, and executes it
    statement-by-statement so one failing statement never rolls back the
    whole schema into an empty database. Then applies extra ALTER TABLE
    patches (account/backup/accession status checks, phone/is_read
    columns, notification and analytics-cache checks) the same way.
    Skips entirely with a warning when schema.sql is missing or a
    statement fails, logging applied/skipped counts. Adjacent constraint
    replacement pairs are committed together so a failed replacement never
    leaves an existing database without its former constraint. Never raises.

    Args:
        app: Flask application providing config and ``logger``.
    """
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    if not os.path.isfile(schema_path):
        app.logger.warning('schema.sql not found — skipping schema initialization')
        return
    conn = db._pool.getconn()
    # A pooled connection can be closed while idle by the provider
    # (Render/Neon). run_schema does not otherwise validate it, so a dead
    # checkout would fail every statement and be reported only as skipped
    # ones. Validate here and replace the slot once so the migration
    # actually runs.
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT 1')
        conn.rollback()
    except Exception:
        try:
            db._pool.putconn(conn, close=True)
        except Exception:
            pass
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
                statements = list(statements)
                index = 0
                while index < len(statements):
                    stmt = statements[index]
                    stmt = stmt.strip()
                    if not stmt:
                        index += 1
                        continue
                    try:
                        # Constraint migrations are written as adjacent
                        # DROP/ADD pairs. Run them in one transaction: a
                        # rejected ADD rolls the DROP back instead of
                        # silently weakening an existing database.
                        next_stmt = (
                            statements[index + 1].strip()
                            if index + 1 < len(statements) else ''
                        )
                        is_constraint_drop = 'DROP CONSTRAINT' in stmt.upper()
                        is_constraint_add = 'ADD CONSTRAINT' in next_stmt.upper()
                        cur.execute(stmt)
                        if is_constraint_drop and is_constraint_add:
                            cur.execute(next_stmt)
                            index += 1
                        conn.commit()
                        ok += 1
                    except Exception as e:
                        conn.rollback()
                        if any(name in stmt for name in (
                            'uq_procurement_log_request_id',
                            'uq_inventory_status_accession_id',
                        )):
                            raise RequiredSchemaMigrationError(
                                'Required uniqueness index could not be created. '
                                'Review duplicate procurement request IDs and inventory '
                                'accession IDs and reconcile them before restarting.'
                            ) from e
                        failed += 1
                        app.logger.warning('Schema statement skipped: %s | %.120s',
                                            e, stmt)
                    index += 1
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
        # Analytics-cache CHECK must cover every exportable report type
        # (single source: analytics.models.ANALYTICS_REPORT_TYPES), or
        # export snapshots for newer sections fail the INSERT and are
        # silently dropped. Built dynamically so the next new KPI cannot
        # drift out of sync; falls back to no patch when unimportable.
        try:
            from app.analytics.models import ANALYTICS_REPORT_TYPES
            _rt_list = ', '.join("'%s'" % t for t in ANALYTICS_REPORT_TYPES)
        except Exception:
            _rt_list = None
        _cache_patches = []
        if _rt_list:
            _cache_patches = [
                'ALTER TABLE analytics_cache DROP CONSTRAINT IF EXISTS analytics_cache_report_type_check;',
                'ALTER TABLE analytics_cache ADD CONSTRAINT analytics_cache_report_type_check '
                'CHECK (report_type IN (%s));' % _rt_list,
            ]
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
        ] + _cache_patches)
        app.logger.info('Database schema initialized: %d applied, %d skipped.',
                        ok + ok2, failed + failed2)
    except RequiredSchemaMigrationError:
        conn.rollback()
        app.logger.exception('Required schema migration failed; no duplicate rows were removed')
        raise
    except Exception as e:
        conn.rollback()
        app.logger.warning('Schema initialization skipped (may already exist): %s', e)
    finally:
        db._pool.putconn(conn)


# book_catalog columns added by later migrations. schema.sql introduces
# them, but a database whose startup sync was skipped or whose ALTERs were
# silently skipped ends up without them, and the book write paths then
# degrade (drop the missing column) so e-book links and category links are
# never stored. Re-applied here as a last line of defense, each statement
# isolated so one failure never masks the rest.
_REQUIRED_BOOK_COLUMNS = (
    'ALTER TABLE book_catalog '
    'ADD COLUMN IF NOT EXISTS category_id INT REFERENCES categories(category_id)',
    'ALTER TABLE book_catalog ADD COLUMN IF NOT EXISTS ebook_url VARCHAR(500)',
    'ALTER TABLE book_catalog '
    'ADD COLUMN IF NOT EXISTS ebook_allow_download BOOLEAN NOT NULL DEFAULT TRUE',
    'ALTER TABLE book_catalog ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP',
    'ALTER TABLE book_catalog '
    'ADD COLUMN IF NOT EXISTS updated_by INT REFERENCES user_accounts(user_id)',
)


def ensure_book_catalog_columns(app):
    """Guarantee book_catalog's later migration columns exist.

    Runs the idempotent ALTERs for the columns the book read/write paths
    assume (category_id, ebook_url and the audit stamps) on a validated
    connection, logging a warning naming any that still fail. Complements
    :func:`run_schema`, which already applies them, so a database that
    missed or skipped that sync is healed at the next start instead of
    silently dropping e-book links on every save. Never raises.

    Args:
        app: Flask application providing config and ``logger``.
    """
    if app.config.get('TESTING'):
        return
    try:
        conn = db._pool.getconn()
    except Exception as e:
        app.logger.warning('book_catalog column check skipped: %s', e)
        return
    try:
        # Validate the checkout: an idle-closed connection would fail
        # every ALTER below and leave the column missing.
        try:
            with conn.cursor() as cur:
                cur.execute('SELECT 1')
            conn.rollback()
        except Exception:
            try:
                db._pool.putconn(conn, close=True)
            except Exception:
                pass
            conn = db._pool.getconn()
        ok, failed = 0, 0
        for stmt in _REQUIRED_BOOK_COLUMNS:
            try:
                with conn.cursor() as cur:
                    cur.execute(stmt)
                conn.commit()
                ok += 1
            except Exception as e:
                conn.rollback()
                failed += 1
                app.logger.warning(
                    'book_catalog column ensure skipped: %s | %.120s', e, stmt)
        if failed:
            app.logger.warning(
                'book_catalog schema not fully ensured: %d of %d statements '
                'skipped', failed, ok + failed)
    except Exception as e:
        app.logger.warning('book_catalog column ensure failed: %s', e)
    finally:
        try:
            db._pool.putconn(conn)
        except Exception:
            pass


def verify_schema_tables(app):
    """Log loudly any table expected by schema.sql that is missing.

    run_schema logs skipped statements per boot, but Render log search
    only retains recent lines, so a silently skipped CREATE TABLE (e.g.
    ebook_access_log against Neon) can go unnoticed for days. This
    re-checks every CREATE TABLE name from schema.sql via to_regclass
    after the sync and prints one line per missing table. Never raises.
    """
    if app.config.get('TESTING'):
        return
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    if not os.path.isfile(schema_path):
        return
    try:
        with open(schema_path, 'r') as f:
            sql = f.read()
        # Ignore comment lines so prose like "-- CREATE TABLE above only
        # exists on fresh databases" doesn't register a fake table name.
        sql = '\n'.join(
            line for line in sql.splitlines()
            if not line.strip().startswith('--'))
        tables = re.findall(
            r'CREATE TABLE (?:IF NOT EXISTS )?([a-zA-Z_][a-zA-Z0-9_.]*)', sql)
        if not tables:
            return
        try:
            conn = db._pool.getconn()
        except Exception as e:
            app.logger.warning('schema table verification skipped: %s', e)
            return
        try:
            missing = []
            with conn.cursor() as cur:
                for name in tables:
                    cur.execute('SELECT to_regclass(%s)', (name,))
                    if cur.fetchone()[0] is None:
                        missing.append(name)
            if missing:
                app.logger.warning(
                    'Schema verification: %d table(s) missing after sync: %s',
                    len(missing), ', '.join(missing))
            else:
                app.logger.info(
                    'Schema verification: all %d tables present.', len(tables))
        except Exception as e:
            app.logger.warning('schema table verification failed: %s', e)
        finally:
            try:
                db._pool.putconn(conn)
            except Exception:
                pass
    except Exception as e:
        app.logger.warning('schema table verification skipped: %s', e)


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
    else:
        run_schema(app)
    # Always ensure the critical book_catalog columns: even with the batch
    # sync skipped, a missing ebook_url silently breaks e-book saving.
    ensure_book_catalog_columns(app)
    verify_schema_tables(app)
