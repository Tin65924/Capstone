"""Edge-case regression tests for the Overview pages.

Covers `/librarian`, `/admin`, and `/admin/audits`: empty database,
`None`/short model returns, XSS content, string-vs-date values in the
trend/activity widgets (template must not assume date objects), and the
full auth matrix. Everything must degrade gracefully — never 500.
"""


class TestEmptyDb:
    @staticmethod
    def _empty(mock_db):
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        mock_db['execute'].return_value = []

    def test_librarian_empty(self, librarian_client, mock_db):
        """Validates librarian empty `/librarian` as librarian (expects 200) [TestEmptyDb / overview edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates dashboard/stats shown to staff are wrong."""
        self._empty(mock_db)
        assert librarian_client.get('/librarian').status_code == 200

    def test_admin_empty(self, admin_client, mock_db):
        """Validates admin empty `/admin` as admin (expects 200) [TestEmptyDb / overview edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates dashboard/stats shown to staff are wrong."""
        self._empty(mock_db)
        assert admin_client.get('/admin').status_code == 200

    def test_audits_empty(self, admin_client, mock_db):
        """Validates audits empty `/admin/audits` as admin (expects 200) [TestEmptyDb / overview edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates dashboard/stats shown to staff are wrong."""
        self._empty(mock_db)
        assert admin_client.get('/admin/audits').status_code == 200


class TestNoneGuards:
    def test_daily_borrows_none(self, mock_db):
        """Validates daily borrows none [TestNoneGuards / overview edge cases].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.main.models import get_daily_borrows
        mock_db['fetch_all'].return_value = None
        assert get_daily_borrows() == []

    def test_string_dates_render(self, librarian_client, mock_db):
        """Validates string dates render `/librarian` as librarian (expects 200) [TestNoneGuards / overview edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates dashboard/stats shown to staff are wrong.

Trend/activity widgets tolerate ISO strings, not just dates."""
        from datetime import date
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].side_effect = [
            [], [], [],  # stats: grouped, procurement x2
            [('Ann', 1, 'Borrowed', 'T', '2026-01-05', None, None)],
            [('2026-01-05', 3)],  # daily as ISO strings
            [], [], [], [],
        ]
        assert librarian_client.get('/librarian').status_code == 200

    def test_librarian_none_models(self, librarian_client, mock_db):
        """Validates librarian none models `/librarian` as librarian (expects 200) [TestNoneGuards / overview edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = None
        assert librarian_client.get('/librarian').status_code == 200

    def test_admin_short_backup_rows(self, admin_client, mock_db):
        """Validates admin short backup rows `/admin` as admin (expects 200) [TestNoneGuards / overview edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].side_effect = [
            [(1,)],  # by_role short rows
            [],  # pending
            [],  # audits
            [(1,)],  # backup short rows
        ]
        assert admin_client.get('/admin').status_code == 200

    def test_admin_none_models(self, admin_client, mock_db):
        """Validates admin none models `/admin` as admin (expects 200) [TestNoneGuards / overview edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = None
        assert admin_client.get('/admin').status_code == 200


class TestXss:
    def test_evil_activity(self, librarian_client, mock_db):
        """Validates evil activity `/librarian` as librarian [TestXss / overview edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        evil = '<script>alert(1)</script>'
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = [
            (evil, 1, 'Borrowed', evil, '2026-01-01', None, None)]
        body = librarian_client.get('/librarian').data.decode()
        assert evil not in body

    def test_evil_pending_user(self, admin_client, mock_db):
        """Validates evil pending user `/admin` as admin [TestXss / overview edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        evil = '<img src=x onerror=alert(1)>'
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].side_effect = [
            [], [(9, evil, 'e@x.ph', 'Student', 'pending')],
            [], [],
        ]
        body = admin_client.get('/admin').data.decode()
        assert evil not in body

    def test_evil_audit_row(self, admin_client, mock_db):
        """Validates evil audit row `/admin/audits` as admin [TestXss / overview edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        evil = '<svg onload=alert(1)>'
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].side_effect = [
            [(7, 1, evil, None, '2026-01-01')],
            [(0,)],
        ]
        body = admin_client.get('/admin/audits').data.decode()
        assert evil not in body


class TestAuth:
    # NOTE: logged-in fixtures share the base `client` object, so each
    # role gets its own test to keep sessions isolated.
    def test_anon_redirected(self, client):
        """Validates anon redirected (expects 302) [TestAuth / overview edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        for url in ('/librarian', '/admin', '/admin/audits'):
            resp = client.get(url)
            assert resp.status_code == 302, url
            assert '/login' in resp.location, url

    def test_student_blocked(self, student_client):
        """Validates student blocked as student (expects 302) [TestAuth / overview edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates dashboard/stats shown to staff are wrong."""
        for url in ('/librarian', '/admin', '/admin/audits'):
            assert student_client.get(url).status_code == 302, url

    def test_faculty_blocked(self, faculty_client):
        """Validates faculty blocked as faculty (expects 302) [TestAuth / overview edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates dashboard/stats shown to staff are wrong."""
        for url in ('/librarian', '/admin'):
            assert faculty_client.get(url).status_code == 302, url

    def test_librarian_blocked_from_admin(self, librarian_client):
        """Validates librarian blocked from admin as librarian (expects 302) [TestAuth / overview edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates dashboard/stats shown to staff are wrong."""
        for url in ('/admin', '/admin/audits'):
            assert librarian_client.get(url).status_code == 302, url
