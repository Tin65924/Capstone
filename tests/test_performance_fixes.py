"""Tests for the low-risk performance fixes from the audit.

Covers the memoized notification-badge context processor (which used to run
1-2 COUNT queries on every page render) and the hot-path indexes added to
``app/schema.sql``. The connection-revalidation window and pool sizing are
covered in ``tests/test_database.py``.
"""
import os
from unittest.mock import patch

import pytest

from app import _badge_count_cached, clear_notif_badge_cache


class _FakeUser:
    """Minimal stand-in for flask_login's current_user."""

    def __init__(self, uid, role, authenticated=True):
        self.id = uid
        self.role = role
        self.is_authenticated = authenticated


class _AnonUser:
    is_authenticated = False


def _badge_processor(app):
    """Return the registered notif_unread context processor."""
    procs = app.template_context_processors[None]
    return next(p for p in procs if p.__name__ == '_inject_notif_unread')


def _badge_query_calls(mock_fetch_one):
    """Calls to fetch_one that belong to the staff badge counter."""
    return [c for c in mock_fetch_one.call_args_list
            if 'pending_review' in str(c.args[0]) or 'reservation_queue' in str(c.args[0])]


@pytest.fixture(autouse=True)
def _clear_badge_cache():
    """Each test starts with an empty badge cache."""
    clear_notif_badge_cache()
    yield
    clear_notif_badge_cache()


class TestBadgeCacheHelper:
    def test_memoizes_within_ttl(self):
        """Validates _badge_count_cached calls compute once inside the TTL [TestBadgeCacheHelper / performance].
    If fails: the badge would still hit the DB on every render.
    Failure indicates the memoization is broken."""
        calls = []

        def compute():
            calls.append(1)
            return 7

        assert _badge_count_cached('k', compute, ttl=60) == 7
        assert _badge_count_cached('k', compute, ttl=60) == 7
        assert len(calls) == 1

    def test_recomputes_after_ttl(self):
        """Validates a zero TTL always recomputes [TestBadgeCacheHelper / performance].
    If fails: a stale badge could stick forever.
    Failure indicates expiry is not honoured."""
        calls = []

        def compute():
            calls.append(1)
            return len(calls)

        assert _badge_count_cached('k2', compute, ttl=0) == 1
        assert _badge_count_cached('k2', compute, ttl=0) == 2
        assert len(calls) == 2

    def test_keys_are_isolated(self):
        """Validates separate keys do not share a cached value [TestBadgeCacheHelper / performance].
    If fails: one user could see another user's badge count.
    Failure indicates the cache key is not per user."""
        assert _badge_count_cached('a', lambda: 1, ttl=60) == 1
        assert _badge_count_cached('b', lambda: 2, ttl=60) == 2


class TestBadgeContextProcessor:
    def test_anonymous_gets_zero_without_querying(self, app, mock_db):
        """Validates an anonymous render reports 0 and touches no DB [TestBadgeContextProcessor / performance].
    If fails: public pages would query for a logged-out visitor.
    Failure indicates the auth check regressed."""
        fn = _badge_processor(app)
        with app.test_request_context('/'):
            with patch('flask_login.current_user', _AnonUser()):
                assert fn() == {'notif_unread': 0}
        mock_db['fetch_one'].assert_not_called()

    def test_staff_badge_cached_between_renders(self, app, mock_db):
        """Validates a second staff render reuses the cached badge [TestBadgeContextProcessor / performance].
    If fails: every page view pays 2 COUNT queries again (the audit's finding).
    Failure indicates badge caching is not active outside testing."""
        mock_db['fetch_one'].return_value = (2,)
        fn = _badge_processor(app)
        app.config['TESTING'] = False
        try:
            with app.test_request_context('/'):
                with patch('flask_login.current_user', _FakeUser(4, 'Admin')):
                    assert fn() == {'notif_unread': 18}
                    first = len(_badge_query_calls(mock_db['fetch_one']))
                    assert first == 2
                    assert fn() == {'notif_unread': 18}
                    second = len(_badge_query_calls(mock_db['fetch_one']))
            assert second == first
        finally:
            app.config['TESTING'] = True

    def test_member_badge_cached_between_renders(self, app, mock_db):
        """Validates borrower badge lookup is cached between renders [TestBadgeContextProcessor / performance].
    If fails: borrower pages pay a borrower lookup plus an unread COUNT every render.
    Failure indicates member-side caching is not active."""
        def side_effect(query, params=None):
            if 'FROM borrowers' in query:
                return (9, 1, 'ID-9', 'CS', None, 'active', None, None)
            if 'notification_log' in query:
                return (3,)
            return None

        mock_db['fetch_one'].side_effect = side_effect
        fn = _badge_processor(app)
        app.config['TESTING'] = False
        try:
            with app.test_request_context('/'):
                with patch('flask_login.current_user', _FakeUser(1, 'Student')):
                    assert fn() == {'notif_unread': 3}
                    first = mock_db['fetch_one'].call_count
                    assert fn() == {'notif_unread': 3}
                    assert mock_db['fetch_one'].call_count == first
        finally:
            app.config['TESTING'] = True

    def test_badge_recomputed_each_render_in_testing(self, app, mock_db):
        """Validates tests still see every badge query (cache disabled under TESTING) [TestBadgeContextProcessor / performance].
    If fails: route tests could pass on a stale badge and miss regressions.
    Failure indicates the TESTING bypass regressed."""
        mock_db['fetch_one'].return_value = (1,)
        fn = _badge_processor(app)
        with app.test_request_context('/'):
            with patch('flask_login.current_user', _FakeUser(4, 'Admin')):
                fn()
                fn()
        assert len(_badge_query_calls(mock_db['fetch_one'])) == 4

    def test_db_failure_fails_open(self, app, mock_db):
        """Validates a DB error yields a 0 badge instead of breaking the page [TestBadgeContextProcessor / performance].
    If fails: a DB blip would 500 every page for a logged-in user.
    Failure indicates the fail-open guard regressed."""
        mock_db['fetch_one'].side_effect = RuntimeError('db down')
        fn = _badge_processor(app)
        with app.test_request_context('/'):
            with patch('flask_login.current_user', _FakeUser(4, 'Admin')):
                assert fn() == {'notif_unread': 0}


class TestSchemaIndexes:
    EXPECTED_INDEXES = (
        'idx_circ_borrower',
        'idx_circ_due',
        'idx_circ_recent',
        'idx_inventory_session',
        'idx_inventory_checked',
        'idx_reservation_borrower',
        'idx_requests_date',
        'idx_requests_status_date',
        'idx_procurement_request',
        'idx_procurement_status',
        'idx_user_accounts_created',
        'idx_analytics_cache_lookup',
    )

    def test_schema_declares_hot_path_indexes(self):
        """Validates schema.sql declares the audit's hot-path indexes [TestSchemaIndexes / performance].
    If fails: the unindexed scans the audit found (close to sequential on Neon) are back.
    Failure indicates the schema index block was reverted."""
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, 'app', 'schema.sql'), encoding='utf-8') as handle:
            sql = handle.read()
        for name in self.EXPECTED_INDEXES:
            assert 'CREATE INDEX IF NOT EXISTS %s' % name in sql, name

    def test_schema_replay_executes_new_indexes(self, app):
        """Validates run_schema replays the new index statements onto the DB [TestSchemaIndexes / performance].
    If fails: a fresh or reconciled deploy would never create the indexes (schema.sql is re-applied on boot).
    Failure indicates the index block is unreachable by run_schema's statement splitter."""
        from unittest.mock import MagicMock
        from app import database
        pool = MagicMock()
        conn = MagicMock()
        pool.getconn.return_value = conn
        original = database.db._pool
        database.db._pool = pool
        try:
            with app.app_context():
                database.run_schema(app)
        finally:
            database.db._pool = original
        cur = conn.cursor.return_value.__enter__.return_value
        statements = [str(c.args[0]) for c in cur.execute.call_args_list]
        for name in self.EXPECTED_INDEXES:
            assert any('CREATE INDEX IF NOT EXISTS %s' % name in stmt for stmt in statements), name
