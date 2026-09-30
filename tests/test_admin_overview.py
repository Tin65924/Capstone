"""Tests for the admin System Overview and Audit Logs (admin-only governance)."""

from datetime import datetime


def _admin_ok(mock_db):
    mock_db['fetch_one'].return_value = (0,)
    mock_db['fetch_all'].return_value = []


class TestAdminOverviewStats:
    def test_keys_and_role_mapping(self, mock_db):
        from app.main.models import get_admin_overview_stats
        mock_db['fetch_one'].side_effect = [(42,), (3,), (120,)]
        mock_db['fetch_all'].return_value = [
            ('Librarian', 4), ('Faculty', 6), ('Student', 30), ('Admin', 2),
        ]
        stats = get_admin_overview_stats()
        assert stats == {
            'total_users': 42,
            'pending_users': 3,
            'active_librarians': 4,
            'active_faculty': 6,
            'active_students': 30,
            'active_admins': 2,
            'total_collection': 120,
        }

    def test_skips_bad_role_rows(self, mock_db):
        from app.main.models import get_admin_overview_stats
        mock_db['fetch_one'].side_effect = [(10,), (0,), (5,)]
        mock_db['fetch_all'].return_value = [
            ('Librarian', 2), ('short',), ('Faculty', 'x'),
        ]
        stats = get_admin_overview_stats()
        assert stats['active_librarians'] == 2
        assert stats['active_faculty'] == 0

    def test_queries_use_placeholders(self, mock_db):
        from app.auth import models as auth_models
        mock_db['fetch_one'].return_value = (1,)
        mock_db['fetch_all'].return_value = []
        auth_models.count_total_users()
        auth_models.count_pending_users()
        auth_models.count_active_users_by_role()
        auth_models.get_audit_logs(limit=8)
        for mock in (mock_db['fetch_one'], mock_db['fetch_all']):
            for call in mock.call_args_list:
                assert '%s' in call[0][0] or 'COUNT(*)' in call[0][0]
                assert 'f-string' not in call[0][0].lower()
        # search path uses ILIKE with bound param
        auth_models.get_audit_logs(limit=10, search='backup')
        calls = mock_db['fetch_all'].call_args_list
        query, params = [c[0] for c in calls if 'a.log_id' in c[0][0]][-1]
        assert 'ILIKE %s' in query
        assert params == ('circulation:%', 'requests:%', '%backup%', 10)


class TestAdminDashboardRoute:
    def _mock_overview(self, mock_db):
        mock_db['fetch_one'].side_effect = [(42,), (3,), (120,)]
        mock_db['fetch_all'].side_effect = [
            [('Librarian', 4), ('Faculty', 6)],  # count_active_users_by_role
            [],  # get_pending_users
            [],  # get_audit_logs
            [],  # get_backup_logs
        ]

    def test_admin_allowed_renders_governance(self, admin_client, mock_db):
        self._mock_overview(mock_db)
        resp = admin_client.get('/admin')
        assert resp.status_code == 200
        assert b'System Overview' in resp.data
        assert b'Total Users' in resp.data
        assert b'Pending Approvals' in resp.data
        assert b'Backup Status' in resp.data
        assert b'Needs Attention' in resp.data
        assert b'Recent Admin Activity' in resp.data
        assert b'Audit Logs' in resp.data

    def test_backup_card_shows_auto_schedule(self, admin_client, mock_db, app):
        self._mock_overview(mock_db)
        from app.backup.scheduler import next_scheduled_backup
        day = app.config.get('BACKUP_DAY', 1)
        hour = app.config.get('BACKUP_HOUR', 2)
        keep = app.config.get('BACKUP_KEEP', 12)
        expected = next_scheduled_backup(day, hour).strftime('%Y-%m-%d %H:%M')
        resp = admin_client.get('/admin')
        assert resp.status_code == 200
        assert b'Auto-backup' in resp.data
        assert f'keeps newest {keep}'.encode() in resp.data
        assert expected.encode() in resp.data

    def test_backup_filename_cannot_overflow_card(self, admin_client, mock_db):
        """Long backup filenames must wrap/truncate, not overlap the card."""
        self._mock_overview(mock_db)
        resp = admin_client.get('/admin')
        assert resp.status_code == 200
        assert b'break-all' in resp.data

    def test_admin_sidebar_has_audit_link(self, admin_client, mock_db):
        self._mock_overview(mock_db)
        resp = admin_client.get('/admin')
        assert b'/admin/audits' in resp.data

    def test_librarian_forbidden(self, librarian_client):
        resp = librarian_client.get('/admin')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_student_forbidden(self, student_client):
        resp = student_client.get('/admin')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_unauthenticated_redirects(self, client):
        resp = client.get('/admin')
        assert resp.status_code == 302
        assert '/login' in resp.location


class TestAdminAuditsRoute:
    def test_admin_allowed_renders(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = [
            (1, 'Boss Admin', 'boss@mcst.edu.ph', 'Admin',
             'backup:created:f.sql', '2026-01-01'),
        ]
        resp = admin_client.get('/admin/audits')
        assert resp.status_code == 200
        assert b'Audit Logs' in resp.data
        assert b'backup:created:f.sql' in resp.data
        assert b'Showing 1 entry' in resp.data
        assert b'mobile-sidebar' in resp.data

    def test_timestamp_formatted(self, admin_client, mock_db):
        from datetime import datetime
        mock_db['fetch_all'].return_value = [
            (1, 'Boss Admin', 'boss@mcst.edu.ph', 'Admin',
             'login', datetime(2026, 3, 5, 14, 30)),
        ]
        resp = admin_client.get('/admin/audits')
        assert resp.status_code == 200
        assert b'Mar 05, 2026 14:30' in resp.data
        assert b'2026-03-05 14:30:00' not in resp.data

    def test_deleted_user_shows_system(self, admin_client, mock_db):
        from datetime import datetime
        mock_db['fetch_all'].return_value = [
            (9, None, None, None, 'login', datetime(2026, 3, 5, 9, 0)),
        ]
        resp = admin_client.get('/admin/audits')
        assert resp.status_code == 200
        assert b'System' in resp.data

    def test_search_filters(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = admin_client.get('/admin/audits?q=backup')
        assert resp.status_code == 200
        calls = mock_db['fetch_all'].call_args_list
        query, params = [c[0] for c in calls if 'a.log_id' in c[0][0]][-1]
        assert 'ILIKE %s' in query
        assert params[2] == '%backup%'
        assert b'No entries match' in resp.data

    def test_limit_clamped(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = admin_client.get('/admin/audits?limit=9999')
        assert resp.status_code == 200
        calls = mock_db['fetch_all'].call_args_list
        _, params = [c[0] for c in calls if 'a.log_id' in c[0][0]][-1]
        assert params[-1] == 200
        mock_db['fetch_all'].reset_mock()
        resp = admin_client.get('/admin/audits?limit=bogus')
        assert resp.status_code == 200
        calls = mock_db['fetch_all'].call_args_list
        _, params = [c[0] for c in calls if 'a.log_id' in c[0][0]][-1]
        assert params[-1] == 50

    def test_empty_state(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = admin_client.get('/admin/audits')
        assert resp.status_code == 200
        assert b'No audit entries yet' in resp.data


class TestAuditTabs:
    def test_staff_tab_filters_roles(self, mock_db):
        from app.auth.models import get_audit_logs
        mock_db['fetch_all'].return_value = []
        get_audit_logs(limit=25, tab='staff')
        calls = mock_db['fetch_all'].call_args_list
        query, params = [c[0] for c in calls if 'a.log_id' in c[0][0]][-1]
        assert "r.role_name IN ('Admin', 'Librarian')" in query
        assert 'ILIKE' not in query
        assert params == ('circulation:%', 'requests:%', 25)

    def test_members_and_system_tabs(self, mock_db):
        from app.auth.models import get_audit_logs
        mock_db['fetch_all'].return_value = []
        get_audit_logs(tab='members')
        calls = mock_db['fetch_all'].call_args_list
        query, _ = [c[0] for c in calls if 'a.log_id' in c[0][0]][-1]
        assert "r.role_name IN ('Student', 'Faculty')" in query
        get_audit_logs(tab='system')
        calls = mock_db['fetch_all'].call_args_list
        query, _ = [c[0] for c in calls if 'a.log_id' in c[0][0]][-1]
        assert 'a.user_id IS NULL' in query

    def test_all_and_invalid_tab_have_no_role_filter(self, mock_db):
        from app.auth.models import get_audit_logs
        mock_db['fetch_all'].return_value = []
        get_audit_logs(tab='all')
        calls = mock_db['fetch_all'].call_args_list
        query, _ = [c[0] for c in calls if 'a.log_id' in c[0][0]][-1]
        assert 'role_name IN' not in query
        assert 'IS NULL' not in query
        get_audit_logs(tab='bogus')
        calls = mock_db['fetch_all'].call_args_list
        query, _ = [c[0] for c in calls if 'a.log_id' in c[0][0]][-1]
        assert 'role_name IN' not in query

    def test_tab_combines_with_search(self, mock_db):
        from app.auth.models import get_audit_logs
        mock_db['fetch_all'].return_value = []
        get_audit_logs(limit=10, search='backup', tab='staff')
        calls = mock_db['fetch_all'].call_args_list
        query, params = [c[0] for c in calls if 'a.log_id' in c[0][0]][-1]
        assert "r.role_name IN ('Admin', 'Librarian')" in query
        assert 'a.activity ILIKE %s' in query
        assert params == ('circulation:%', 'requests:%', '%backup%', 10)

    def test_route_staff_tab(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = admin_client.get('/admin/audits?tab=staff')
        assert resp.status_code == 200
        calls = mock_db['fetch_all'].call_args_list
        query, _ = [c[0] for c in calls if 'a.log_id' in c[0][0]][-1]
        assert "r.role_name IN ('Admin', 'Librarian')" in query
        assert b'Staff' in resp.data
        assert b'name="tab" value="staff"' in resp.data

    def test_route_invalid_tab_falls_back(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = admin_client.get('/admin/audits?tab=bogus')
        assert resp.status_code == 200
        calls = mock_db['fetch_all'].call_args_list
        query, _ = [c[0] for c in calls if 'a.log_id' in c[0][0]][-1]
        assert 'role_name IN' not in query

    def test_route_search_keeps_tab(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = admin_client.get('/admin/audits?tab=system&q=login')
        assert resp.status_code == 200
        calls = mock_db['fetch_all'].call_args_list
        query, params = [c[0] for c in calls if 'a.log_id' in c[0][0]][-1]
        assert 'a.user_id IS NULL' in query
        assert params[2] == '%login%'
        assert b'tab=system' in resp.data

    def test_librarian_forbidden(self, librarian_client):
        resp = librarian_client.get('/admin/audits')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_student_forbidden(self, student_client):
        resp = student_client.get('/admin/audits')
        assert resp.status_code == 302

    def test_unauthenticated_redirects(self, client):
        resp = client.get('/admin/audits')
        assert resp.status_code == 302
        assert '/login' in resp.location


class TestStatsEdges:
    def test_weird_role_rows(self, admin_client, mock_db):
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].side_effect = [
            [(None, 3), ('Student', -2), ('X', 'junk'), ('Y',)],
            [], [], [],
        ]
        assert admin_client.get('/admin').status_code == 200

    def test_short_pending_activity(self, admin_client, mock_db):
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].side_effect = [
            [], [(9,)], [(7,)],
            [(1, 'f', 100, 'completed', 'm', None, '2026-01-01')],
        ]
        assert admin_client.get('/admin').status_code == 200


class TestBackupStates:
    def test_failed_backup_banner(self, admin_client, mock_db):
        _admin_ok(mock_db)
        mock_db['fetch_all'].side_effect = [
            [], [],
            [(1, 'b.pg', 100, 'failed', 'manual', 'boom',
              '2026-01-01')],
            [(1, 'b.pg', 100, 'failed', 'manual', 'boom',
              '2026-01-01')],
        ]
        assert admin_client.get('/admin').status_code == 200

    def test_evil_filename_and_error(self, admin_client, mock_db):
        evil = '<script>alert(1)</script>'
        _admin_ok(mock_db)
        row = (1, evil, 100, 'failed', 'manual', evil, '2026-01-01')
        mock_db['fetch_all'].side_effect = [[], [], [row], [row]]
        body = admin_client.get('/admin').data.decode()
        assert evil not in body

    def test_short_backup_rows(self, admin_client, mock_db):
        _admin_ok(mock_db)
        mock_db['fetch_all'].side_effect = [[], [], [(1,)], [(1,)]]
        assert admin_client.get('/admin').status_code == 200


class TestScheduler:
    def test_garbage_config(self):
        from app.backup.scheduler import next_scheduled_backup
        for day, hour in ((None, None), ('x', 'y'), (-5, 99),
                          (0, -1), (31, 25), ('15', '9')):
            nxt = next_scheduled_backup(day, hour)
            assert isinstance(nxt, datetime)

    def test_december_rollover(self):
        from app.backup.scheduler import next_scheduled_backup
        now = datetime(2026, 12, 20, 10, 0)
        nxt = next_scheduled_backup(1, 2, now=now)
        assert (nxt.year, nxt.month) == (2027, 1)


class TestDescribeActivity:
    def test_garbage(self):
        from app.auth.models import describe_activity
        for actor, code in ((None, None), ('', ''), ('A', 'nonsense xyz'),
                            ('A', 'approved_user:notanid'),
                            ('<b>A</b>', 'deleted_user:1:<i>x</i>'),
                            ('A', 'X' * 3000)):
            out = describe_activity(actor, code)
            assert isinstance(out, str)

    def test_evil_audit_renders_escaped(self, admin_client, mock_db):
        evil = '<img src=x onerror=alert(1)>'
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].side_effect = [
            [(7, 1, evil, None, '2026-01-05')],
            [(0,)],
        ]
        body = admin_client.get('/admin/audits').data.decode()
        assert evil not in body

    def test_audit_wildcard_search(self, admin_client, mock_db):
        _admin_ok(mock_db)
        assert admin_client.get('/admin/audits?q=%_').status_code == 200
