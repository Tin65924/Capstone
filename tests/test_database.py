"""Tests for Database.execute transaction handling.

SELECTs must end their transaction (commit) so pooled connections never
sit idle-in-transaction holding shared locks — that exact pattern used to
deadlock backup restores: the worker's own SELECT on backup_log blocked
psql's DROP TABLE of the same table forever.
"""
from unittest.mock import MagicMock

import pytest


def _db_with_fake_pool():
    from app.database import Database
    db = Database()
    pool = MagicMock()
    db._pool = pool
    return db, pool


def _cursor_mock(conn, description, fetchall_result=None):
    cur = conn.cursor.return_value.__enter__.return_value
    cur.description = description
    if fetchall_result is not None:
        cur.fetchall.return_value = fetchall_result
    return cur


class TestExecuteTransactions:
    def test_select_commits_to_release_locks(self, app):
        db, pool = _db_with_fake_pool()
        conn = MagicMock()
        pool.getconn.return_value = conn
        _cursor_mock(conn, [('backup_id',)], [(14,)])
        with app.app_context():
            assert db.fetch_one('SELECT 1') == (14,)
        conn.commit.assert_called_once()
        conn.rollback.assert_not_called()

    def test_write_commits(self, app):
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
        import sys
        patcher = getattr(sys.modules.get('conftest'), 'patcher_init_db', None)
        if patcher is None:
            pytest.skip('conftest init_db patcher unavailable')
        patcher.stop()
        return patcher

    def test_schema_runs_by_default(self, app):
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
        assert app.config.get('SKIP_SCHEMA_SYNC') is False
