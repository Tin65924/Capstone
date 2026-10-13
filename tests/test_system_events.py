"""Tests for system-generated audit events (NULL-user rows for the System tab)."""

from unittest.mock import MagicMock, patch


def _audit_inserts(mock_db):
    return [c for c in mock_db['execute'].call_args_list
            if 'INSERT INTO audit_trail' in c[0][0]]


class TestLogSystemEvent:
    def test_writes_null_user_row(self, mock_db):
        """Validates writes null user row [TestLogSystemEvent / system events].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates audit trail is incomplete (compliance gap)."""
        from app.auth.models import log_system_event
        log_system_event('system:scheduled_backup:completed:f.sql')
        rows = _audit_inserts(mock_db)
        assert len(rows) == 1
        _, params = rows[0][0]
        assert params == (None, 'system:scheduled_backup:completed:f.sql', None)


class TestSchedulerSystemEvents:
    def test_scheduled_success_logs_system_event(self, app, mock_db):
        """Validates scheduled success logs system event [TestSchedulerSystemEvents / system events].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates audit trail is incomplete (compliance gap)."""
        from app.backup import scheduler as sched
        mock_db['fetch_one'].return_value = (1,)
        mock_db['fetch_all'].return_value = []
        with patch('app.backup.utils.create_backup', return_value=('f.sql', 5)):
            sched.run_scheduled_backup(app)
        rows = _audit_inserts(mock_db)
        assert len(rows) == 1
        _, params = rows[0][0]
        assert params[0] is None
        assert params[1] == 'system:scheduled_backup:completed:f.sql'

    def test_scheduled_failure_logs_system_event(self, app, mock_db):
        """Validates scheduled failure logs system event [TestSchedulerSystemEvents / system events].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates audit trail is incomplete (compliance gap)."""
        from app.backup import scheduler as sched
        with patch('app.backup.utils.create_backup', side_effect=RuntimeError('x')):
            sched.run_scheduled_backup(app)
        rows = _audit_inserts(mock_db)
        assert len(rows) == 1
        _, params = rows[0][0]
        assert params == (None, 'system:scheduled_backup:failed', None)


class TestServerErrorSystemEvent:
    def test_500_logs_system_event_and_renders(self, app, client, mock_db):
        """Validates 500 logs system event and renders `/__boom__` (expects 500) [TestServerErrorSystemEvent / system events].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates audit trail is incomplete (compliance gap)."""
        app.testing = False
        app.add_url_rule('/__boom__', view_func=lambda: 1 / 0)
        resp = client.get('/__boom__')
        assert resp.status_code == 500
        assert b'Something Went Wrong' in resp.data
        rows = _audit_inserts(mock_db)
        assert len(rows) == 1
        _, params = rows[0][0]
        assert params[0] is None
        assert params[1] == 'system:error:500:/__boom__'


class TestDenialAudit:
    def test_student_denied_logged_attributed(self, student_client, mock_db):
        """Validates student denied logged attributed `/admin/backup` as student (expects 302) [TestDenialAudit / system events].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates audit trail is incomplete (compliance gap)."""
        resp = student_client.get('/admin/backup')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location
        rows = _audit_inserts(mock_db)
        assert len(rows) == 1
        _, params = rows[0][0]
        assert params == ('1', 'security:denied:backup.backup_page', None)

    def test_anonymous_probe_logged_as_system(self, client, mock_db):
        """Validates anonymous probe logged as system `/admin/backup` (expects 302) [TestDenialAudit / system events].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = client.get('/admin/backup')
        assert resp.status_code == 302
        assert '/login' in resp.location
        rows = _audit_inserts(mock_db)
        assert len(rows) == 1
        _, params = rows[0][0]
        assert params == (None, 'system:auth_required:/admin/backup', None)

    def test_allowed_access_writes_no_denial(self, admin_client, mock_db):
        """Validates allowed access writes no denial `/admin/backup` as admin (expects 200) [TestDenialAudit / system events].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates audit trail is incomplete (compliance gap)."""
        mock_db['fetch_all'].return_value = []
        resp = admin_client.get('/admin/backup')
        assert resp.status_code == 200
        assert _audit_inserts(mock_db) == []

    def test_denial_visible_in_audit_logs(self, admin_client, mock_db):
        """Validates denial visible in audit logs `/admin/audits` as admin (expects 200) [TestDenialAudit / system events].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates audit trail is incomplete (compliance gap)."""
        from datetime import datetime
        mock_db['fetch_all'].return_value = [
            (7, 'Stu One', 's@mcst.edu.ph', 'Student',
             'security:denied:backup.backup_page', datetime(2026, 9, 19, 10, 0)),
        ]
        resp = admin_client.get('/admin/audits')
        assert resp.status_code == 200
        assert b'security:denied:backup.backup_page' in resp.data


class TestOperationalExclusion:
    def test_circulation_and_requests_excluded(self, mock_db):
        """Validates circulation and requests excluded [TestOperationalExclusion / system events].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates audit trail is incomplete (compliance gap)."""
        from app.auth.models import get_audit_logs
        mock_db['fetch_all'].return_value = []
        get_audit_logs()
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'a.activity NOT LIKE %s' in query
        # LIKE patterns travel as bound params — a literal % in the SQL
        # string breaks psycopg2 placeholder parsing (500 on /admin/audits).
        assert '%' not in query.replace('%s', '')
        assert params == ('circulation:%', 'requests:%', 50)

    def test_exclusion_combines_with_tab_and_search(self, mock_db):
        """Validates exclusion combines with tab and search [TestOperationalExclusion / system events].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates audit trail is incomplete (compliance gap)."""
        from app.auth.models import get_audit_logs
        mock_db['fetch_all'].return_value = []
        get_audit_logs(limit=10, search='denied', tab='staff')
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'a.activity NOT LIKE %s' in query
        assert "r.role_name IN ('Admin', 'Librarian')" in query
        assert 'a.activity ILIKE %s' in query
        assert params == ('circulation:%', 'requests:%', '%denied%', 10)


class TestLoginFailureSystemEvents:
    def test_missing_state_logs(self, client, mock_db):
        """Validates missing state logs `/login/google/callback` (expects 302) [TestLoginFailureSystemEvents / system events].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = client.get('/login/google/callback')
        assert resp.status_code == 302
        rows = _audit_inserts(mock_db)
        assert len(rows) == 1
        assert rows[0][0][1] == (None, 'system:login_failed:invalid_state', None)

    def test_blocked_domain_logs(self, client, mock_db):
        """Validates blocked domain logs `/login/google/callback` (expects 302) [TestLoginFailureSystemEvents / system events].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates audit trail is incomplete (compliance gap)."""
        with client.session_transaction() as sess:
            sess['_oauth_state'] = 'test-state'
        mock_flow = MagicMock()
        mock_flow.fetch_token.return_value = None
        mock_flow.credentials.id_token = 'fake-id-token'
        with patch('app.auth.routes._build_flow', return_value=mock_flow):
            import app.auth.routes as auth_routes
            with patch.object(auth_routes, 'id_token') as mock_id_token:
                mock_id_token.verify_oauth2_token.return_value = {
                    'iss': 'accounts.google.com',
                    'email': 'user@gmail.com',
                    'sub': 'google-sub-123',
                    'name': 'Test User',
                }
                resp = client.get('/login/google/callback',
                                  query_string={'state': 'test-state', 'code': 'x'})
                assert resp.status_code == 302
        rows = _audit_inserts(mock_db)
        assert len(rows) == 1
        assert rows[0][0][1] == (None, 'system:login_failed:domain', None)

    def test_token_exchange_failure_logs(self, client, mock_db):
        """Validates token exchange failure logs `/login/google/callback` (expects 302) [TestLoginFailureSystemEvents / system events].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        with client.session_transaction() as sess:
            sess['_oauth_state'] = 'test-state'
        mock_flow = MagicMock()
        mock_flow.fetch_token.side_effect = RuntimeError('bad code')
        with patch('app.auth.routes._build_flow', return_value=mock_flow):
            resp = client.get('/login/google/callback',
                              query_string={'state': 'test-state', 'code': 'x'})
            assert resp.status_code == 302
        rows = _audit_inserts(mock_db)
        assert len(rows) == 1
        assert rows[0][0][1] == (None, 'system:login_failed:token_exchange', None)

    def test_successful_login_logs_no_system_event(self, client, mock_db, mock_oauth_flow):
        """Validates successful login logs no system event `/login/google/callback` (expects 302) [TestLoginFailureSystemEvents / system events].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        with client.session_transaction() as sess:
            sess['_oauth_state'] = 'test-state'
        mock_oauth_flow.fetch_token.return_value = None
        mock_oauth_flow.credentials.id_token = 'fake-id-token'
        import app.auth.routes as auth_routes
        with patch.object(auth_routes, 'id_token') as mock_id_token:
            mock_id_token.verify_oauth2_token.return_value = {
                'iss': 'accounts.google.com',
                'email': 'user@mcst.edu.ph',
                'sub': 'google-sub-123',
                'name': 'Test User',
            }
            with patch('app.auth.routes.get_user_by_oauth_sub') as mock_get:
                mock_get.return_value = ('1', 'user@mcst.edu.ph', 'Student', 'Test User')
                with patch('app.auth.routes.login_user'):
                    resp = client.get('/login/google/callback',
                                      query_string={'state': 'test-state', 'code': 'x'})
                    assert resp.status_code == 302
        # Success writes a user-attributed 'login' row — but no NULL-user row.
        rows = _audit_inserts(mock_db)
        assert rows and all(c[0][1][0] is not None for c in rows)
