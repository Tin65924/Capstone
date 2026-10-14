"""Edge-case regression tests for Audit Logs (second pass).

Covers mixed date/datetime/string timestamps in stats aggregation
(the old code crashed sorting them), non-string activity codes,
unknown/describe-all audit codes, hostile search input, short log
rows, and string timestamps on the page. Includes the timestamp
normalization and activity-code coercion fixes.
"""
from datetime import datetime, date


class TestStatsEdges:
    def test_weird_timestamps(self, mock_db):
        """Validates weird timestamps [TestStatsEdges / audits edge cases].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        from app.auth.models import get_audit_stats
        mock_db['fetch_all'].return_value = [
            ('login', 'not-a-date', 1, 'A', 'Student'),
            ('login', None, 2, 'B', 'Faculty'),
            ('login', datetime(2026, 1, 5, 10, 0), 3, 'C', None),
            ('login', date(2026, 1, 5), 4, 'D', 'Admin'),
            ('x', 'y'),
            (),
            ('server_error', datetime(2026, 1, 5), 5, 'E', 'Librarian'),
        ]
        stats = get_audit_stats()
        assert isinstance(stats['logins_today'], int)

    def test_none_rows(self, mock_db):
        """Validates none rows [TestStatsEdges / audits edge cases].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        from app.auth.models import get_audit_stats
        mock_db['fetch_all'].return_value = None
        stats = get_audit_stats()
        assert stats['logins_today'] == 0

    def test_non_string_activity(self, mock_db):
        """Validates non string activity [TestStatsEdges / audits edge cases].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        from app.auth.models import get_audit_stats
        mock_db['fetch_all'].return_value = [
            (12345, datetime(2026, 1, 5, 10, 0), 1, 'A', 'Student'),
            (None, datetime(2026, 1, 5, 11, 0), 2, 'B', 'Faculty'),
        ]
        stats = get_audit_stats()
        assert stats['logins_today'] == 0

    def test_stats_json_safe(self, mock_db):
        """Validates stats json safe [TestStatsEdges / audits edge cases].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        import json
        from app.auth.models import get_audit_stats
        mock_db['fetch_all'].return_value = [
            ('login', datetime(2026, 1, 5, 10, 0), 1, 'A', 'Student')]
        json.dumps(get_audit_stats())


class TestPageEdges:
    @staticmethod
    def _empty(mock_db):
        """Test helper _empty: build mocked data or DB stub for the test."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []

    def test_short_log_rows(self, admin_client, mock_db):
        """Validates short log rows `/admin/audits` as admin (expects 200) [TestPageEdges / audits edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates audit trail is incomplete (compliance gap)."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].side_effect = [[(7,)], [(0,)]]
        assert admin_client.get('/admin/audits').status_code == 200

    def test_string_timestamps(self, admin_client, mock_db):
        """Validates string timestamps `/admin/audits` as admin (expects 200) [TestPageEdges / audits edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].return_value = (0,)
        row = (7, 'Ann', 'e@x.ph', 'Student', 'login', '2026-01-05 10:00')
        mock_db['fetch_all'].side_effect = [[row], [(0,)]]
        assert admin_client.get('/admin/audits').status_code == 200

    def test_hostile_search(self, admin_client, mock_db):
        """Validates hostile search as admin (expects 200) [TestPageEdges / audits edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates audit trail is incomplete (compliance gap)."""
        self._empty(mock_db)
        for url in ('/admin/audits?q=' + '%_\\',
                    '/admin/audits?q=' + 'x' * 3000,
                    '/admin/audits?q=\' OR \'1\'=\'1',
                    '/admin/audits?tab=%00',
                    '/admin/audits?limit=1'):
            assert admin_client.get(url).status_code == 200, url[:60]

    def test_describe_all_codes(self, mock_db):
        """Validates describe all codes [TestPageEdges / audits edge cases].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        from app.auth.models import describe_activity
        codes = ['login', 'first_login', 'logout', 'approved_user:1:X',
                 'toggled_user_status:2', 'archived_user:3:a~>b',
                 'unarchived_user:4', 'deleted_user:5:N',
                 'changed_role:6:Student~>Admin:N',
                 'cataloging:edit_book:7:title:a~>b',
                 'circulation:user_borrow:8', 'system:error:500:/x',
                 'security:denied:/admin', '', None, 'a' * 2000,
                 'weird:code:with:many:colons:here']
        for code in codes:
            out = describe_activity('Ann', code)
            assert isinstance(out, str), code
