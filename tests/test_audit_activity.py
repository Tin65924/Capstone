"""Tests for audit analytics (get_audit_stats) and descriptive activities."""

from datetime import date, datetime, timedelta
from unittest.mock import patch

from app.auth.models import describe_activity, get_audit_stats

TODAY = date(2026, 9, 24)


def _row(activity, ts, uid=1, name='Ann', role='Librarian'):
    """Test helper _row: build mocked data or DB stub for the test."""
    return (activity, ts, uid, name, role)


def _noon(days_ago=0):
    """Test helper _noon: build mocked data or DB stub for the test."""
    return datetime(2026, 9, 24, 12, 0) - timedelta(days=days_ago)


class TestAuditStats:
    def _sample_rows(self):
        """Test helper _sample_rows: build mocked data or DB stub for the test."""
        now = _noon()
        return [
            _row('login', now, 1, 'Ann', 'Librarian'),
            _row('login', now - timedelta(hours=2), 2, 'Bob', 'Student'),
            _row('logout', now - timedelta(hours=3), 2, 'Bob', 'Student'),
            _row('login', now - timedelta(days=3), 3, 'Cat', 'Faculty'),
            _row('logout', now - timedelta(days=1), 3, 'Cat', 'Faculty'),
            _row('system:login_failed:domain', now, None, None, None),
            _row('system:error:500:/admin/backup', now, None, None, None),
            _row('security:denied:backup.backup_page', now - timedelta(days=2),
                 2, 'Bob', 'Student'),
            _row('backup:created:f.sql', now - timedelta(days=2),
                 1, 'Ann', 'Librarian'),
        ]

    def test_kpis(self, mock_db):
        """Validates kpis [TestAuditStats / audit activity].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_all'].return_value = self._sample_rows()
        stats = get_audit_stats(today=TODAY)
        assert stats['window_days'] == 30
        assert stats['total_events'] == 9
        assert stats['logins_today'] == 2
        assert stats['logins_7d'] == 3
        assert stats['failed_logins'] == 1
        assert stats['denials'] == 1
        assert stats['server_errors'] == 1

    def test_active_now_needs_login_after_logout(self, mock_db):
        """Validates active now needs login after logout [TestAuditStats / audit activity].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_all'].return_value = self._sample_rows()
        stats = get_audit_stats(today=TODAY)
        # Ann (no logout) and Bob (login newer than logout) are active;
        # Cat logged out after her last login.
        assert stats['active_now'] == 2
        assert stats['active_users'][0] == ['Ann', 'Librarian']
        assert stats['active_users'][1] == ['Bob', 'Student']

    def test_daily_buckets(self, mock_db):
        """Validates daily buckets [TestAuditStats / audit activity].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_all'].return_value = self._sample_rows()
        stats = get_audit_stats(today=TODAY)
        assert len(stats['logins_per_day']) == 14
        assert len(stats['errors_per_day']) == 14
        assert sum(c for _, c in stats['logins_per_day']) == 3
        assert sum(c for _, c in stats['errors_per_day']) == 2
        assert stats['logins_per_day'][-1] == ['Sep 24', 2]

    def test_categories_roles_and_paths(self, mock_db):
        """Validates categories roles and paths [TestAuditStats / audit activity].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_all'].return_value = self._sample_rows()
        stats = get_audit_stats(today=TODAY)
        by_cat = dict(stats['by_category'])
        assert by_cat['Sign-ins'] == 3
        assert by_cat['Failed sign-ins'] == 1
        assert by_cat['Backups'] == 1
        assert dict(stats['logins_by_role']) == {
            'Librarian': 1, 'Student': 1, 'Faculty': 1}
        assert stats['top_error_paths'] == [['/admin/backup', 1]]

    def test_empty_table(self, mock_db):
        """Validates empty table [TestAuditStats / audit activity].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_all'].return_value = []
        stats = get_audit_stats(today=TODAY)
        assert stats['total_events'] == 0
        assert stats['active_now'] == 0
        assert stats['active_users'] == []
        assert len(stats['logins_per_day']) == 14
        assert stats['by_category'] == []
        assert stats['top_error_paths'] == []

    def test_malformed_rows_skipped(self, mock_db):
        """Validates malformed rows skipped [TestAuditStats / audit activity].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_all'].return_value = [None, ('only',), ('login',)]
        stats = get_audit_stats(today=TODAY)
        assert stats['total_events'] == 3
        assert stats['logins_today'] == 0

    def test_string_timestamps(self, mock_db):
        """Validates string timestamps [TestAuditStats / audit activity].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_all'].return_value = [
            _row('login', '2026-09-24 10:00:00', 1, 'Ann', 'Librarian'),
        ]
        stats = get_audit_stats(today=TODAY)
        assert stats['logins_today'] == 1

    def test_query_shape(self, mock_db):
        """Validates query shape [TestAuditStats / audit activity].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates audit trail is incomplete (compliance gap)."""
        mock_db['fetch_all'].return_value = []
        get_audit_stats(days=7, limit=100, today=TODAY)
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'a.activity NOT LIKE %s' in query
        assert 'LIMIT %s' in query
        assert params[1] == 'circulation:%'
        assert params[2] == 'requests:%'
        assert params[3] == 100
        assert (TODAY - params[0].date()).days == 6


class TestDescribeActivity:
    CASES = [
        ('Ann', 'login', 'Ann signed in'),
        ('Ann', 'first_login', 'Ann signed in for the first time'),
        ('Ann', 'logout', 'Ann signed out'),
        (None, 'system:login_failed:domain',
         'A sign-in attempt failed (non-library email domain)'),
        (None, 'system:login_failed:token_exchange',
         'A sign-in attempt failed (identity provider error)'),
        (None, 'system:scheduled_backup:completed:f.sql',
         'Scheduled backup completed (f.sql)'),
        (None, 'system:scheduled_backup:failed', 'Scheduled backup failed'),
        (None, 'system:error:500:/admin/backup',
         'Server error (500) on /admin/backup'),
        (None, 'system:auth_required:/admin',
         'Someone tried to open /admin without signing in'),
        ('Ann', 'security:denied:backup.backup_page',
         'Ann was denied access to backup.backup_page'),
        ('Boss', 'backup:created:f.sql', 'Boss created backup f.sql'),
        ('Boss', 'backup:restored:f.sql',
         'Boss restored the database from f.sql'),
        ('Boss', 'backup:deleted:f.sql', 'Boss deleted backup f.sql'),
        ('Boss', 'backup:failed:manual', "Boss's manual backup failed"),
        ('Boss', 'backup:restore_failed:f.sql',
         "Boss's restore from f.sql failed"),
        ('Staff1', 'cataloging:edit_book:42:title:1984~>1985',
         "Staff1 edited the title of book #42 from '1984' to '1985'"),
        ('Staff1', 'cataloging:edit_book:42', 'Staff1 edited book #42'),
        ('Staff1', 'cataloging:toggle_status:42:archived',
         'Staff1 archived book #42'),
        ('Staff1', 'cataloging:bulk_import:3_success_0_errors',
         'Staff1 bulk-imported 3 book(s) with 0 error(s)'),
        ('Admin', 'approved_user:5:Ann Cruz',
         'Admin approved user Ann Cruz (#5)'),
        ('Admin', 'approved_user:5', 'Admin approved user #5'),
        ('Admin', 'changed_role:5:Member~>Librarian:Ann Cruz',
         "Admin changed the role of user Ann Cruz (#5) from Member to Librarian"),
        ('Admin', 'changed_role:5_to_3',
         'Admin changed the role of user #5 (to role #3)'),
        ('Admin', 'settings:update:2:BACKUP_DAY,BACKUP_KEEP',
         'Admin updated 2 library setting(s) (BACKUP_DAY,BACKUP_KEEP)'),
        ('Admin', 'settings:update:1', 'Admin updated 1 library setting(s)'),
        ('Ann', 'profile:update', 'Ann updated their profile'),
        ('Ann', 'notifications:read_all',
         'Ann marked all notifications as read'),
        ('Ann', 'inventory:scan:9', 'Ann scanned copy #9'),
        ('Ann', 'procurement:update_status:4',
         'Ann updated procurement request #4'),
        ('Bob', 'circulation:borrow:9', 'Bob borrowed copy #9'),
        (None, 'login', 'System signed in'),
        ('A', 'frobnicate:xyz', 'frobnicate:xyz'),
        ('A', '', ''),
    ]

    def test_cases(self):
        """Validates cases [TestDescribeActivity / audit activity].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates audit trail is incomplete (compliance gap)."""
        for actor, code, expected in self.CASES:
            assert describe_activity(actor, code) == expected, code


class TestAuditStatsRoute:
    def test_page_renders_kpis_charts_and_descriptions(
            self, admin_client, mock_db):
        """Validates page renders kpis charts and descriptions `/admin/audits` as admin (expects 200) [TestAuditStatsRoute / audit activity].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_all'].side_effect = [
            [(1, 'Ann', 'a@x', 'Librarian', 'login',
              datetime(2026, 9, 24, 9, 0))],
            [],
        ]
        resp = admin_client.get('/admin/audits')
        assert resp.status_code == 200
        for kpi in (b'kpi-logins-today', b'kpi-logins-7d', b'kpi-active-now',
                    b'kpi-failed-logins', b'kpi-denials', b'kpi-server-errors'):
            assert kpi in resp.data
        for chart in (b'chart-logins-day', b'chart-errors-day',
                      b'chart-categories', b'chart-roles'):
            assert chart in resp.data
        assert b'audit-stats' in resp.data
        assert b'top-error-paths' in resp.data
        # Described sentence primary, raw code still present.
        assert b'Ann signed in' in resp.data
        assert b'>login<' in resp.data

    def test_stats_failure_keeps_table(self, admin_client, mock_db):
        """Validates stats failure keeps table `/admin/audits` as admin (expects 200) [TestAuditStatsRoute / audit activity].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_all'].side_effect = [
            [(1, 'Ann', 'a@x', 'Librarian', 'login',
              datetime(2026, 9, 24, 9, 0))],
            RuntimeError('db down'),
        ]
        resp = admin_client.get('/admin/audits')
        assert resp.status_code == 200
        assert b'Ann signed in' in resp.data
        assert b'kpi-logins-today' not in resp.data

    def test_page_wires_chart_axes_and_hover(self, admin_client, mock_db):
        """Validates page wires chart axes and hover `/admin/audits` as admin (expects 200) [TestAuditStatsRoute / audit activity].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates audit trail is incomplete (compliance gap)."""
        mock_db['fetch_all'].side_effect = [[], []]
        resp = admin_client.get('/admin/audits')
        assert resp.status_code == 200
        assert b"xLabel: 'Date'" in resp.data
        assert b"yLabel: 'Sign-ins'" in resp.data
        assert b'#audit-chart-tip' in resp.data


class TestAuditChartsJs:
    @staticmethod
    def _js():
        """Test helper _js: build mocked data or DB stub for the test."""
        from pathlib import Path
        return (Path(__file__).resolve().parent.parent / 'app' /
                'static' / 'js' / 'charts.js').read_text()

    def test_line_has_xy_axes(self):
        """Validates line has xy axes [TestAuditChartsJs / audit activity].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates audit trail is incomplete (compliance gap)."""
        js = self._js()
        assert 'xLabel' in js
        assert 'yLabel' in js
        assert 'text-anchor' in js

    def test_renderers_are_hoverable(self):
        """Validates renderers are hoverable [TestAuditChartsJs / audit activity].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates audit trail is incomplete (compliance gap)."""
        js = self._js()
        assert 'audit-chart-tip' in js
        assert '<title>' in js
        assert 'audit-seg' in js
        assert 'audit-hbar-row' in js
        assert 'audit-dot' in js


class TestEnrichedWrites:
    def _audit_inserts(self, mock_db):
        """Test helper _audit_inserts: build mocked data or DB stub for the test."""
        return [c for c in mock_db['execute'].call_args_list
                if 'INSERT INTO audit_trail' in c[0][0]]

    def test_edit_book_logs_title_change(self, librarian_client, mock_db):
        """Validates edit book logs title change `/librarian/cataloging/1/edit` as librarian (expects 302) [TestEnrichedWrites / audit activity].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].return_value = (
            1, '1984', 'George Orwell', None, None, None,
            None, None, None, None, 'Book', None, 'active', None)
        resp = librarian_client.post('/librarian/cataloging/1/edit', data={
            'title': '1985', 'author': 'George Orwell',
            'edition': '1st', 'publisher': 'Pub', 'year_published': '1949',
            'isbn': '978-0', 'subject_classification': 'Fiction',
            'call_number': 'PR6029'})
        assert resp.status_code == 302
        inserts = self._audit_inserts(mock_db)
        assert inserts
        assert 'cataloging:edit_book:1:title:1984~>1985' in inserts[0][0][1]

    def test_edit_book_unchanged_title_keeps_legacy(
            self, librarian_client, mock_db):
        """Validates edit book unchanged title keeps legacy `/librarian/cataloging/1/edit` as librarian (expects 302) [TestEnrichedWrites / audit activity].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].return_value = (
            1, '1984', 'George Orwell', None, None, None,
            None, None, None, None, 'Book', None, 'active', None)
        resp = librarian_client.post('/librarian/cataloging/1/edit', data={
            'title': '1984', 'author': 'George Orwell',
            'edition': '1st', 'publisher': 'Pub', 'year_published': '1949',
            'isbn': '978-0', 'subject_classification': 'Fiction',
            'call_number': 'PR6029'})
        assert resp.status_code == 302
        inserts = self._audit_inserts(mock_db)
        assert inserts
        assert inserts[0][0][1][1] == 'cataloging:edit_book:1'

    def test_approve_includes_target_name(self, admin_client, mock_db):
        """Validates approve includes target name `/librarian/users/5/approve` as admin (expects 302) [TestEnrichedWrites / audit activity].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates audit trail is incomplete (compliance gap)."""
        mock_db['fetch_one'].return_value = (
            5, 'a@mcst.edu.ph', 'Student', 'Ann Cruz', 'pending')
        resp = admin_client.post('/librarian/users/5/approve')
        assert resp.status_code == 302
        inserts = self._audit_inserts(mock_db)
        assert inserts
        assert inserts[0][0][1][1] == 'approved_user:5:Ann Cruz'

    def test_change_role_enriched(self, admin_client, mock_db):
        """Validates change role enriched `/admin/users/5/role` as admin (expects 302) [TestEnrichedWrites / audit activity].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates audit trail is incomplete (compliance gap)."""
        mock_db['fetch_one'].return_value = (
            5, 'a@mcst.edu.ph', 'Member', 'Ann Cruz', 'active')
        mock_db['fetch_all'].return_value = [(3, 'Librarian')]
        resp = admin_client.post('/admin/users/5/role', data={'role_id': '3'})
        assert resp.status_code == 302
        inserts = self._audit_inserts(mock_db)
        assert inserts
        assert inserts[0][0][1][1] == \
            'changed_role:5:Member~>Librarian:Ann Cruz'

    def test_settings_update_lists_keys(self, admin_client, mock_db):
        """Validates settings update lists keys `/admin/settings/update` as admin (expects 302) [TestEnrichedWrites / audit activity].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates audit trail is incomplete (compliance gap)."""
        mock_db['fetch_all'].return_value = []
        with patch('app.backup.scheduler.reschedule'):
            resp = admin_client.post('/admin/settings/update', data={
                'BACKUP_DAY': '15', 'BACKUP_KEEP': '5'})
        assert resp.status_code == 302
        inserts = self._audit_inserts(mock_db)
        assert inserts
        assert inserts[0][0][1][1] == \
            'settings:update:2:BACKUP_DAY,BACKUP_KEEP'
