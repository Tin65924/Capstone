"""Tests for the admin System Overview and Audit Logs (admin-only governance)."""


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
        query, params = mock_db['fetch_all'].call_args[0]
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
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'ILIKE %s' in query
        assert params[2] == '%backup%'
        assert b'No entries match' in resp.data

    def test_limit_clamped(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = admin_client.get('/admin/audits?limit=9999')
        assert resp.status_code == 200
        _, params = mock_db['fetch_all'].call_args[0]
        assert params[-1] == 200
        mock_db['fetch_all'].reset_mock()
        resp = admin_client.get('/admin/audits?limit=bogus')
        assert resp.status_code == 200
        _, params = mock_db['fetch_all'].call_args[0]
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
        query, params = mock_db['fetch_all'].call_args[0]
        assert "r.role_name IN ('Admin', 'Librarian')" in query
        assert 'ILIKE' not in query
        assert params == ('circulation:%', 'requests:%', 25)

    def test_members_and_system_tabs(self, mock_db):
        from app.auth.models import get_audit_logs
        mock_db['fetch_all'].return_value = []
        get_audit_logs(tab='members')
        query, _ = mock_db['fetch_all'].call_args[0]
        assert "r.role_name IN ('Student', 'Faculty')" in query
        get_audit_logs(tab='system')
        query, _ = mock_db['fetch_all'].call_args[0]
        assert 'a.user_id IS NULL' in query

    def test_all_and_invalid_tab_have_no_role_filter(self, mock_db):
        from app.auth.models import get_audit_logs
        mock_db['fetch_all'].return_value = []
        get_audit_logs(tab='all')
        query, _ = mock_db['fetch_all'].call_args[0]
        assert 'role_name IN' not in query
        assert 'IS NULL' not in query
        get_audit_logs(tab='bogus')
        query, _ = mock_db['fetch_all'].call_args[0]
        assert 'role_name IN' not in query

    def test_tab_combines_with_search(self, mock_db):
        from app.auth.models import get_audit_logs
        mock_db['fetch_all'].return_value = []
        get_audit_logs(limit=10, search='backup', tab='staff')
        query, params = mock_db['fetch_all'].call_args[0]
        assert "r.role_name IN ('Admin', 'Librarian')" in query
        assert 'a.activity ILIKE %s' in query
        assert params == ('circulation:%', 'requests:%', '%backup%', 10)

    def test_route_staff_tab(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = admin_client.get('/admin/audits?tab=staff')
        assert resp.status_code == 200
        query, _ = mock_db['fetch_all'].call_args[0]
        assert "r.role_name IN ('Admin', 'Librarian')" in query
        assert b'Staff' in resp.data
        assert b'name="tab" value="staff"' in resp.data

    def test_route_invalid_tab_falls_back(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = admin_client.get('/admin/audits?tab=bogus')
        assert resp.status_code == 200
        query, _ = mock_db['fetch_all'].call_args[0]
        assert 'role_name IN' not in query

    def test_route_search_keeps_tab(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = admin_client.get('/admin/audits?tab=system&q=login')
        assert resp.status_code == 200
        query, params = mock_db['fetch_all'].call_args[0]
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
