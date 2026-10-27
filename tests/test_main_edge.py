"""Edge-case regression tests for the Home surface.

Covers `/`, `/dashboard`, `/librarian`, `/admin`, `/admin/audits`,
`/user/*`, and `/api/*`: empty database, hostile params (bad fields,
oversized/XSS input, invalid ids, open-redirect `next` values), missing
borrower rows, malformed loan data, stored-XSS round-trip, validation
boundaries, per-role dashboard redirects, and auth guards. Everything
must degrade gracefully — never 500, never raw HTML injection.
"""
import re


class TestEmptyDb:
    @staticmethod
    def _empty(mock_db):
        """Test helper _empty: build mocked data or DB stub for the test."""
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        mock_db['execute'].return_value = []

    def test_public_index_empty(self, client, mock_db):
        """Validates public index empty `/` (expects 200) [TestEmptyDb / main edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates main edge cases is broken for this case (users see wrong page, blocked action, or bad data)."""
        self._empty(mock_db)
        assert client.get('/').status_code == 200

    def test_librarian_home_empty(self, librarian_client, mock_db):
        """Validates librarian home empty `/librarian` as librarian (expects 200) [TestEmptyDb / main edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates main edge cases is broken for this case (users see wrong page, blocked action, or bad data)."""
        self._empty(mock_db)
        assert librarian_client.get('/librarian').status_code == 200

    def test_admin_home_empty(self, admin_client, mock_db):
        """Validates admin home empty `/admin` as admin (expects 200) [TestEmptyDb / main edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates main edge cases is broken for this case (users see wrong page, blocked action, or bad data)."""
        self._empty(mock_db)
        assert admin_client.get('/admin').status_code == 200

    def test_user_home_empty(self, student_client, mock_db):
        """Validates user home empty `/user/profile` as student (expects 200) [TestEmptyDb / main edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates main edge cases is broken for this case (users see wrong page, blocked action, or bad data)."""
        self._empty(mock_db)
        assert student_client.get('/user/profile').status_code == 200

    def test_history_notifications_empty(self, student_client, mock_db):
        """Validates history notifications empty `/user/history` as student (expects 200) [TestEmptyDb / main edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates main edge cases is broken for this case (users see wrong page, blocked action, or bad data)."""
        self._empty(mock_db)
        assert student_client.get('/user/history').status_code == 200
        assert student_client.get('/user/notifications').status_code == 200

    def test_api_empty(self, client, mock_db):
        """Validates api empty (expects 200) [TestEmptyDb / main edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates main edge cases is broken for this case (users see wrong page, blocked action, or bad data)."""
        self._empty(mock_db)
        for url in ('/api/bloom',
                    '/api/suggestions?field=book_title&q=clean',
                    '/api/book-exists?title=T&author=A'):
            assert client.get(url).status_code == 200, url


class TestHostileParams:
    @staticmethod
    def _ok(mock_db):
        """Test helper _ok: build mocked data or DB stub for the test."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []

    def test_suggestions_bad_field(self, client, mock_db):
        """Validates suggestions bad field (expects 200) [TestHostileParams / main edge cases].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates main edge cases is broken for this case (users see wrong page, blocked action, or bad data)."""
        self._ok(mock_db)
        for url in ('/api/suggestions?field=drop_table&q=clean',
                    '/api/suggestions?field=book_title&q=x',
                    '/api/suggestions?field=book_title&q=' + 'A' * 5000,
                    '/api/suggestions?field=book_title&q=<script>alert(1)</script>',
                    '/api/suggestions'):
            resp = client.get(url)
            assert resp.status_code == 200, url[:80]
            assert resp.get_json() == {'suggestions': []} or isinstance(
                resp.get_json().get('suggestions'), list)

    def test_existence_endpoints(self, client, mock_db):
        """Validates existence endpoints (expects 200) [TestHostileParams / main edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates main edge cases is broken for this case (users see wrong page, blocked action, or bad data)."""
        self._ok(mock_db)
        for url in ('/api/book-exists', '/api/book-exists?title=T',
                    '/api/book-exists?title=' + 'T' * 2000 + '&author=A'):
            assert client.get(url).status_code == 200, url[:60]

    def test_audits_params(self, admin_client, mock_db):
        """Validates audits params as admin (expects 200) [TestHostileParams / main edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates main edge cases is broken for this case (users see wrong page, blocked action, or bad data)."""
        self._ok(mock_db)
        for url in ('/admin/audits?limit=abc', '/admin/audits?limit=-5',
                    '/admin/audits?limit=999999', '/admin/audits?tab=bogus',
                    '/admin/audits?q=<script>alert(1)</script>',
                    '/admin/audits?q=' + 'x' * 3000):
            assert admin_client.get(url).status_code == 200, url[:80]

    def test_notification_ids(self, student_client, mock_db):
        """Validates notification ids `/user/notifications/999999/read` as student (expects 302) [TestHostileParams / main edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates main edge cases is broken for this case (users see wrong page, blocked action, or bad data)."""
        self._ok(mock_db)
        mock_db['fetch_one'].return_value = (9,)
        assert student_client.post(
            '/user/notifications/999999/read').status_code == 302
        assert student_client.post('/user/notifications/read-all').status_code == 302

    def test_next_redirect_guards(self, student_client, mock_db):
        """Validates next redirect guards `/user/notifications/read-all` as student (expects 302) [TestHostileParams / main edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates main edge cases is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].return_value = (9,)
        for nxt in ('https://evil.com', '//evil.com', 'javascript:alert(1)',
                    '/user/profile'):
            resp = student_client.post('/user/notifications/read-all',
                                       data={'next': nxt})
            assert resp.status_code == 302
            loc = resp.location
            if nxt == '/user/profile':
                assert loc.endswith(nxt), loc
            else:
                assert 'evil' not in loc and 'javascript' not in loc, loc

    def test_profile_update_validation(self, student_client, mock_db):
        """Validates profile update validation `/user/profile/update` as student [TestHostileParams / main edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates main edge cases is broken for this case (users see wrong page, blocked action, or bad data)."""
        self._ok(mock_db)
        base = {'full_name': 'Test Student'}
        cases = [
            ({}, 302),  # missing name
            ({'full_name': ''}, 302),
            ({'full_name': 'A', 'phone_number': 'not-a-phone'}, 302),
            ({'full_name': 'A', 'id_number': 'X'}, 302),
            ({'full_name': '<script>alert(1)</script>'}, 302),
            ({'full_name': 'A' * 500}, 302),
        ]
        for data, code in cases:
            assert student_client.post('/user/profile/update',
                                       data=data).status_code == code, data


class TestNoBorrower:
    def test_admin_profile_without_borrower(self, admin_client, mock_db):
        """Validates admin profile without borrower `/user/profile` as admin (expects 200) [TestNoBorrower / main edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates main edge cases is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        assert admin_client.get('/user/profile').status_code == 200

    def test_notify_without_borrower(self, admin_client, mock_db):
        """Validates notify without borrower `/user/notifications/read-all` as admin (expects 302) [TestNoBorrower / main edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates main edge cases is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].return_value = None
        assert admin_client.post('/user/notifications/read-all').status_code == 302


class TestXss:
    def test_evil_arrival_on_index(self, client, mock_db):
        """Validates evil arrival on index `/` [TestXss / main edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates main edge cases is broken for this case (users see wrong page, blocked action, or bad data)."""
        evil = '<script>alert(1)</script>'
        mock_db['fetch_all'].return_value = [(1, evil, 'A', 'E', 'P', 2020,
                                              'S', 'C', 'I', 'B', 'D', 1, 'x')]
        body = client.get('/').data.decode()
        assert evil not in body

    def test_evil_name_in_admin(self, admin_client, mock_db):
        """Validates evil name in admin `/admin` as admin [TestXss / main edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates main edge cases is broken for this case (users see wrong page, blocked action, or bad data)."""
        evil = '<img src=x onerror=alert(1)>'
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = [(9, evil, 'e@x.ph', 'Student',
                                              'active', '2026-01-01')]
        body = admin_client.get('/admin').data.decode()
        assert evil not in body

    def test_evil_search_echo_in_audits(self, admin_client, mock_db):
        """Validates evil search echo in audits `/admin/audits?q=<script>alert(1)</script>` as admin [TestXss / main edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates main edge cases is broken for this case (users see wrong page, blocked action, or bad data)."""
        self_ok = (0,)
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        body = admin_client.get(
            '/admin/audits?q=<script>alert(1)</script>').data.decode()
        assert '<script>alert(1)</script>' not in body


class TestAuth:
    def test_anon_redirects(self, client, mock_db):
        """Validates anon redirects `/` (expects 302) [TestAuth / main edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        for url in ('/dashboard', '/user/profile', '/user/history',
                    '/user/notifications', '/librarian', '/admin',
                    '/admin/audits'):
            resp = client.get(url)
            assert resp.status_code == 302, url
            assert '/login' in resp.location, url
        assert client.get('/').status_code == 200
        for url in ('/api/bloom', '/api/suggestions?field=book_title&q=ab'):
            assert client.get(url).status_code == 200, url

    def test_student_cannot_see_staff_homes(self, student_client):
        """Validates student cannot see staff homes as student (expects 302) [TestAuth / main edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates main edge cases is broken for this case (users see wrong page, blocked action, or bad data)."""
        for url in ('/librarian', '/admin', '/admin/audits'):
            resp = student_client.get(url)
            assert resp.status_code == 302, url
            assert '/user/profile' in resp.location, url

    def test_faculty_cannot_see_admin(self, faculty_client):
        """Validates faculty cannot see admin `/admin` as faculty (expects 302) [TestAuth / main edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates main edge cases is broken for this case (users see wrong page, blocked action, or bad data)."""
        assert faculty_client.get('/admin').status_code == 302

    def test_librarian_cannot_see_admin(self, librarian_client):
        """Validates librarian cannot see admin `/admin` as librarian (expects 302) [TestAuth / main edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates main edge cases is broken for this case (users see wrong page, blocked action, or bad data)."""
        assert librarian_client.get('/admin').status_code == 302

    def test_librarian_can_see_own_home(self, librarian_client, mock_db):
        """Validates librarian can see own home `/librarian` as librarian (expects 200) [TestAuth / main edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates main edge cases is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        assert librarian_client.get('/librarian').status_code == 200


class TestDeeperEdges:
    def test_malformed_loan_rows(self, student_client, mock_db):
        """Validates malformed loan rows `/user/profile` as student (expects 200) [TestDeeperEdges / main edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates main edge cases is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].side_effect = [(5,), (1,), (0,), (0,)]
        mock_db['fetch_all'].side_effect = [
            [(1,)],  # get_borrower_by_user -> short row
            [(), ('9',), (7, 1, '2026-01-05', None, 'overdue', 'T')],
            [], [], [], [], [],
        ]
        assert student_client.get('/user/profile').status_code == 200

    def test_bad_due_date_string(self, student_client, mock_db):
        """Validates bad due date string `/user/profile` as student (expects 200) [TestDeeperEdges / main edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates main edge cases is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].side_effect = [(5,), (1,), (0,), (0,)]
        mock_db['fetch_all'].side_effect = [
            [(5,)],
            [(7, 1, 'not-a-date', None, 'active', 'T')],
            [], [], [], [], [],
        ]
        assert student_client.get('/user/profile').status_code == 200

    def test_stored_xss_round_trip(self, student_client, mock_db):
        """Validates stored xss round trip `/user/profile/update` as student (expects 302) [TestDeeperEdges / main edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates main edge cases is broken for this case (users see wrong page, blocked action, or bad data)."""
        evil = '<script>alert(1)</script>'
        profile = (1, 'e@x.ph', 'Student', 'Old', 5, 'S1', 'BSIS')
        mock_db['fetch_one'].side_effect = [profile, profile]
        mock_db['fetch_all'].return_value = []
        resp = student_client.post('/user/profile/update',
                                   data={'full_name': evil})
        assert resp.status_code == 302
        mock_db['fetch_one'].side_effect = None
        mock_db['fetch_one'].return_value = (1, 'e@x.ph', 'Student', evil,
                                             5, 'S1', 'BSIS')
        body = student_client.get('/user/profile').data.decode()
        assert evil not in body

    def test_profile_update_success(self, student_client, mock_db):
        """Validates profile update success `/user/profile/update` as student (expects 302) [TestDeeperEdges / main edge cases].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (UPDATE).
    Failure indicates main edge cases is broken for this case (users see wrong page, blocked action, or bad data)."""
        profile = (1, 'e@x.ph', 'Student', 'Old', 5, 'S1', 'BSIS')
        mock_db['fetch_one'].return_value = profile
        mock_db['fetch_all'].return_value = [('BSIS',)]
        resp = student_client.post('/user/profile/update',
                                   data={'full_name': 'New Name',
                                         'phone_number': '+639171234567',
                                         'department': 'BSIS'})
        assert resp.status_code == 302
        queries = [c[0][0] for c in mock_db['execute'].call_args_list]
        assert any('UPDATE' in q for q in queries)

    def test_phone_boundaries(self, student_client, mock_db):
        """Validates phone boundaries `/user/profile/update` as student (expects 302) [TestDeeperEdges / main edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates main edge cases is broken for this case (users see wrong page, blocked action, or bad data)."""
        profile = (1, 'e@x.ph', 'Student', 'Old', None, None, None)
        mock_db['fetch_one'].return_value = profile
        for phone in ('+63917', '1' * 21):
            resp = student_client.post('/user/profile/update',
                                       data={'full_name': 'A',
                                             'phone_number': phone})
            assert resp.status_code == 302, phone

    def test_dashboard_redirects_per_role(self, student_client,
                                          librarian_client, admin_client):
        """Validates dashboard redirects per role as student (expects 302) [TestDeeperEdges / main edge cases].
    If fails: likely RBAC decorator or role mock wrong.
    Failure indicates main edge cases is broken for this case (users see wrong page, blocked action, or bad data)."""
        for c in (student_client, librarian_client, admin_client):
            resp = c.get('/dashboard')
            assert resp.status_code == 302
            assert resp.location.endswith('/user/profile')

    def test_student_program_suggest(self, client, mock_db):
        """Validates student program suggest `/api/suggestions?field=student_program&q=bs` (expects 200) [TestDeeperEdges / main edge cases].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates main edge cases is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_all'].return_value = [('BSIS',)]
        resp = client.get('/api/suggestions?field=student_program&q=bs')
        assert resp.status_code == 200
        assert resp.get_json() == {'suggestions': ['BSIS']}

    def test_read_single_notification_evil_next(self, student_client, mock_db):
        """Validates read single notification evil next `/user/notifications/7/read` as student (expects 302) [TestDeeperEdges / main edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates main edge cases is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].return_value = (9,)
        resp = student_client.post('/user/notifications/7/read',
                                   data={'next': 'https://evil.com/x'})
        assert resp.status_code == 302
        assert 'evil' not in resp.location
