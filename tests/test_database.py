"""Tests for Database.execute transaction handling.

SELECTs must end their transaction (commit) so pooled connections never
sit idle-in-transaction holding shared locks — that exact pattern used to
deadlock backup restores: the worker's own SELECT on backup_log blocked
psql's DROP TABLE of the same table forever.
"""
from unittest.mock import MagicMock

import pytest


def _db_with_fake_pool():
    """Test helper _db_with_fake_pool: build mocked data or DB stub for the test."""
    from app.database import Database
    db = Database()
    pool = MagicMock()
    db._pool = pool
    return db, pool


def _cursor_mock(conn, description, fetchall_result=None):
    """Test helper _cursor_mock: build mocked data or DB stub for the test."""
    cur = conn.cursor.return_value.__enter__.return_value
    cur.description = description
    if fetchall_result is not None:
        cur.fetchall.return_value = fetchall_result
    return cur


class TestExecuteTransactions:
    def test_select_commits_to_release_locks(self, app):
        """Validates select commits to release locks [TestExecuteTransactions / database].
    If fails: likely model SQL changed (SELECT).
    Failure indicates database is broken for this case (users see wrong page, blocked action, or bad data)."""
        db, pool = _db_with_fake_pool()
        conn = MagicMock()
        pool.getconn.return_value = conn
        _cursor_mock(conn, [('backup_id',)], [(14,)])
        with app.app_context():
            assert db.fetch_one('SELECT 1') == (14,)
        conn.commit.assert_called_once()
        conn.rollback.assert_not_called()

    def test_write_commits(self, app):
        """Validates write commits [TestExecuteTransactions / database].
    If fails: likely model SQL changed (UPDATE).
    Failure indicates database is broken for this case (users see wrong page, blocked action, or bad data)."""
        db, pool = _db_with_fake_pool()
        conn = MagicMock()
        pool.getconn.return_value = conn
        cur = _cursor_mock(conn, None)
        cur.rowcount = 1
        with app.app_context():
            assert db.execute('UPDATE t SET a = %s', (1,)) == 1
        conn.commit.assert_called_once()
        conn.rollback.assert_not_called()

    def test_error_rolls_back_without_commit(self, app):
        """Validates error rolls back without commit [TestExecuteTransactions / database].
    If fails: likely model SQL changed (UPDATE).
    Failure indicates database is broken for this case (users see wrong page, blocked action, or bad data)."""
        db, pool = _db_with_fake_pool()
        conn = MagicMock()
        pool.getconn.return_value = conn
        cur = _cursor_mock(conn, None)
        cur.execute.side_effect = RuntimeError('boom')
        with app.app_context():
            with pytest.raises(RuntimeError, match='boom'):
                db.execute('UPDATE t SET a = %s', (1,))
        conn.rollback.assert_called_once()
        conn.commit.assert_not_called()


class TestInitDbSchemaGate:
    """init_db itself is globally mocked in tests (conftest.patcher_init_db),
    so these pause that patcher to exercise the real gating logic."""

    @staticmethod
    def _pause_init_db_patch():
        """Test helper _pause_init_db_patch: build mocked data or DB stub for the test."""
        import sys
        patcher = getattr(sys.modules.get('conftest'), 'patcher_init_db', None)
        if patcher is None:
            pytest.skip('conftest init_db patcher unavailable')
        patcher.stop()
        return patcher

    def test_schema_runs_by_default(self, app):
        """Validates schema runs by default [TestInitDbSchemaGate / database].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates database is broken for this case (users see wrong page, blocked action, or bad data)."""
        from unittest.mock import patch
        from app import database
        patcher = self._pause_init_db_patch()
        try:
            app.config['SKIP_SCHEMA_SYNC'] = False
            with patch.object(database, 'run_schema') as mock_run:
                database.init_db(app)
                mock_run.assert_called_once_with(app)
        finally:
            patcher.start()

    def test_schema_skipped_when_flagged(self, app):
        """Validates schema skipped when flagged [TestInitDbSchemaGate / database].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates database is broken for this case (users see wrong page, blocked action, or bad data)."""
        from unittest.mock import patch
        from app import database
        patcher = self._pause_init_db_patch()
        try:
            app.config['SKIP_SCHEMA_SYNC'] = True
            with patch.object(database, 'run_schema') as mock_run:
                database.init_db(app)
                mock_run.assert_not_called()
        finally:
            app.config['SKIP_SCHEMA_SYNC'] = False
            patcher.start()

    def test_flag_defaults_off(self, app):
        """Validates flag defaults off [TestInitDbSchemaGate / database].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates database is broken for this case (users see wrong page, blocked action, or bad data)."""
        assert app.config.get('SKIP_SCHEMA_SYNC') is False


    def test_critical_columns_ensured_even_when_sync_skipped(self, app):
        """Validates book_catalog columns are healed even with SKIP_SCHEMA_SYNC [TestInitDbSchemaGate / database].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates database is broken for this case (a database missing ebook_url is never healed)."""
        from unittest.mock import patch
        from app import database
        patcher = self._pause_init_db_patch()
        try:
            app.config['SKIP_SCHEMA_SYNC'] = True
            with patch.object(database, 'run_schema') as mock_run, \
                    patch.object(database, 'ensure_book_catalog_columns') as mock_ensure, \
                    patch.object(database, 'verify_schema_tables') as mock_verify:
                database.init_db(app)
                mock_run.assert_not_called()
                mock_ensure.assert_called_once_with(app)
                mock_verify.assert_called_once_with(app)
        finally:
            app.config['SKIP_SCHEMA_SYNC'] = False
            patcher.start()


class TestVerifySchemaTables:
    """verify_schema_tables surfaces tables silently missing in prod."""

    def test_skipped_in_testing(self, app):
        """TESTING guard runs before any pool access [TestVerifySchemaTables / database].
    If fails: verification would hit the mocked pool in tests and break suites."""
        from app import database
        fake_db, pool = _db_with_fake_pool()
        original = database.db
        database.db = fake_db
        try:
            database.verify_schema_tables(app)
        finally:
            database.db = original
        pool.getconn.assert_not_called()

    def test_warning_names_missing_tables(self, app, caplog):
        """Each schema.sql CREATE TABLE name is checked and a missing one
        is warned by name [TestVerifySchemaTables / database].
    If fails: silent skip of ebook_access_log-style CREATEs would stay invisible."""
        import logging
        from unittest.mock import MagicMock
        from app import database
        fake_db, pool = _db_with_fake_pool()
        conn = MagicMock()
        pool.getconn.return_value = conn
        cur = conn.cursor.return_value.__enter__.return_value
        cur.fetchone.return_value = (None,)
        original = database.db
        app.config['TESTING'] = False
        database.db = fake_db
        try:
            with caplog.at_level(logging.WARNING):
                database.verify_schema_tables(app)
        finally:
            database.db = original
            app.config['TESTING'] = True
        assert pool.putconn.called
        assert cur.execute.call_count >= 1
        assert all('to_regclass' in c.args[0] for c in cur.execute.call_args_list)
        assert any('missing after sync' in r.getMessage() for r in caplog.records), \
            [r.getMessage() for r in caplog.records]



class TestEnsureBookCatalogColumns:
    """ensure_book_catalog_columns re-runs the critical ALTERs as a heal."""

    def test_runs_each_alter_and_commits(self, app):
        """Validates ensure runs the critical ALTERs and commits [TestEnsureBookCatalogColumns / database].
    If fails: likely ensure_book_catalog_columns changed.
    Failure indicates a database missing ebook_url is not healed on startup."""
        from unittest.mock import MagicMock
        from app import database
        fake_db, pool = _db_with_fake_pool()
        conn = MagicMock()
        pool.getconn.return_value = conn
        original = database.db
        app.config['TESTING'] = False
        database.db = fake_db
        try:
            database.ensure_book_catalog_columns(app)
        finally:
            database.db = original
            app.config['TESTING'] = True
        executed = ' | '.join(
            call.args[0] for call in conn.cursor.return_value
            .__enter__.return_value.execute.call_args_list)
        assert 'ebook_url' in executed
        assert 'category_id' in executed
        assert conn.commit.call_count == len(database._REQUIRED_BOOK_COLUMNS)
        pool.putconn.assert_called_once_with(conn)

    def test_swallows_statement_failure(self, app):
        """Validates a failing ALTER is logged, not raised [TestEnsureBookCatalogColumns / database].
    If fails: likely error handling removed.
    Failure indicates startup crashes when one column cannot be ensured."""
        from unittest.mock import MagicMock
        from app import database
        fake_db, pool = _db_with_fake_pool()
        conn = MagicMock()
        pool.getconn.return_value = conn
        cur = conn.cursor.return_value.__enter__.return_value
        cur.execute.side_effect = RuntimeError('no permission')
        original = database.db
        app.config['TESTING'] = False
        database.db = fake_db
        try:
            database.ensure_book_catalog_columns(app)
        finally:
            database.db = original
            app.config['TESTING'] = True
        conn.commit.assert_not_called()
