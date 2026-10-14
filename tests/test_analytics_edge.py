"""Edge-case regression tests for the Analytics page.

Covers: empty database, hostile query params (bogus preset, garbage
dates, inverted ranges, bad book ids, huge/XSS search input), invalid
chart/kpi/export types, XSS payloads in titles/departments, auth guards,
and PDF export with special characters. All transport/rendering paths
must degrade gracefully — never 500, never raw HTML injection.
"""
import re


def _login(client, uid='3'):
    """Test helper _login: build mocked data or DB stub for the test."""
    with client.session_transaction() as s:
        s['_user_id'] = uid
        s['_fresh'] = True


class TestEmptyDatabase:
    def test_page_empty_db(self, librarian_client, mock_db):
        """Validates page empty db `/librarian/analytics` as librarian (expects 200) [TestEmptyDatabase / analytics edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics')
        assert resp.status_code == 200

    def test_dashboard_empty_db(self, librarian_client, mock_db):
        """Validates dashboard empty db `/librarian/analytics/dashboard` as librarian (expects 200) [TestEmptyDatabase / analytics edge cases].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics/dashboard')
        assert resp.status_code == 200
        body = resp.get_json()
        assert set(body.keys()) >= {'collection', 'circulation', 'usage', 'requests'}

    def test_forecast_empty_db(self, librarian_client, mock_db):
        """Validates forecast empty db `/librarian/analytics/forecast` as librarian (expects 200) [TestEmptyDatabase / analytics edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics/forecast')
        assert resp.status_code == 200

    def test_export_empty_db(self, librarian_client, mock_db):
        """Validates export empty db `/librarian/analytics/export` as librarian (expects 200) [TestEmptyDatabase / analytics edge cases].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'all', 'format': 'pdf'})
        assert resp.status_code == 200
        assert resp.data[:4] == b'%PDF'


class TestHostileParams:
    @staticmethod
    def _ok_db(mock_db):
        """Test helper _ok_db: build mocked data or DB stub for the test."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []

    def test_bogus_preset(self, librarian_client, mock_db):
        """Validates bogus preset as librarian (expects 200) [TestHostileParams / analytics edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates dashboard/stats shown to staff are wrong."""
        self._ok_db(mock_db)
        for url in ('/librarian/analytics?preset=bogus',
                    '/librarian/analytics/dashboard?preset=bogus',
                    '/librarian/analytics/forecast?preset=bogus',
                    '/librarian/analytics/chart?name=top_books&preset=bogus'):
            assert librarian_client.get(url).status_code == 200, url

    def test_garbage_dates(self, librarian_client, mock_db):
        """Validates garbage dates as librarian (expects 200) [TestHostileParams / analytics edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates dashboard/stats shown to staff are wrong."""
        self._ok_db(mock_db)
        for url in ('/librarian/analytics?preset=custom&from=not-a-date&to=32-13-99',
                    '/librarian/analytics/dashboard?from=foo&to=bar',
                    '/librarian/analytics?from=2026-12-31&to=2026-01-01'):
            assert librarian_client.get(url).status_code == 200, url

    def test_book_id_variants(self, librarian_client, mock_db):
        """Validates book id variants `/librarian/analytics?book_id=999999999` as librarian (expects 200) [TestHostileParams / analytics edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates dashboard/stats shown to staff are wrong."""
        self._ok_db(mock_db)
        for url in ('/librarian/analytics?book_id=abc',
                    '/librarian/analytics?book_id=-5',
                    '/librarian/analytics?book_id=0',
                    '/librarian/analytics/book/data',
                    '/librarian/analytics/book/data?book_id=abc'):
            resp = librarian_client.get(url)
            assert resp.status_code in (200, 400, 404), (url, resp.status_code)
        # Nonexistent book: page flashes + 200, JSON endpoint 404s.
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        assert librarian_client.get(
            '/librarian/analytics?book_id=999999999').status_code == 200
        assert librarian_client.get(
            '/librarian/analytics/book/data?book_id=999999999').status_code == 404
        # Corrupt short row (defensive: treated as not-found, never 500).
        mock_db['fetch_one'].return_value = (0,)
        assert librarian_client.get(
            '/librarian/analytics?book_id=999999999').status_code == 200
        assert librarian_client.get(
            '/librarian/analytics/book/data?book_id=999999999').status_code == 404

    def test_huge_search(self, librarian_client, mock_db):
        """Validates huge search as librarian (expects 200) [TestHostileParams / analytics edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates dashboard/stats shown to staff are wrong."""
        self._ok_db(mock_db)
        for url in ('/librarian/analytics?q=' + 'A' * 5000,
                    '/librarian/analytics/book/search?q=' + '%_',
                    '/librarian/analytics/book/search?q=<script>alert(1)</script>'):
            assert librarian_client.get(url).status_code == 200, url[:80]

    def test_xss_department(self, librarian_client, mock_db):
        """Validates xss department `/librarian/analytics/dashboard` as librarian (expects 200) [TestHostileParams / analytics edge cases].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        self._ok_db(mock_db)
        xss = '"><script>alert(1)</script>'
        resp = librarian_client.get('/librarian/analytics/dashboard',
                                    query_string={'department': xss})
        assert resp.status_code == 200
        # JSON transport is application/json (never executed as HTML); the
        # page re-embeds via tojson (unicode-escaped) and renders via
        # escapeHtml(), with Jinja autoescape on server-rendered parts.
        assert resp.content_type == 'application/json'
        resp.get_json()

    def test_invalid_chart_kpi(self, librarian_client, mock_db):
        """Validates invalid chart kpi `/librarian/analytics/chart?name=drop_table` as librarian (expects 400) [TestHostileParams / analytics edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        self._ok_db(mock_db)
        assert librarian_client.get(
            '/librarian/analytics/chart?name=drop_table').status_code == 400
        assert librarian_client.get(
            '/librarian/analytics/kpi?kpi_type=drop_table').status_code == 400

    def test_export_invalid(self, librarian_client, mock_db):
        """Validates export invalid `/librarian/analytics/export` as librarian (expects 302) [TestHostileParams / analytics edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates dashboard/stats shown to staff are wrong."""
        self._ok_db(mock_db)
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'drop_table'})
        # Graceful: flash + redirect back to the analytics page.
        assert resp.status_code == 302
        assert '/librarian/analytics' in resp.location


class TestXssPayloads:
    def test_evil_title_in_dashboard(self, librarian_client, mock_db):
        """Validates evil title in dashboard `/librarian/analytics/dashboard` as librarian (expects 200) [TestXssPayloads / analytics edge cases].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        evil = '<script>alert(1)</script> & "quoted"'
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = [(evil, 5)]
        resp = librarian_client.get('/librarian/analytics/dashboard')
        assert resp.status_code == 200
        # application/json is never executed as HTML; rendering escapes it
        # (tojson + escapeHtml client-side, Jinja autoescape server-side).
        assert resp.content_type == 'application/json'
        assert resp.get_json()['circulation']['total'] == 0

    def test_evil_title_in_page(self, librarian_client, mock_db):
        """Validates evil title in page `/librarian/analytics?q=x&book_id=1` as librarian (expects 200) [TestXssPayloads / analytics edge cases].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        evil = '<img src=x onerror=alert(1)>'
        mock_db['fetch_one'].return_value = (1, evil, 'A', 'C', 2020, 3)
        mock_db['fetch_all'].return_value = [(1, evil, 'A', 'C', 2020)]
        resp = librarian_client.get('/librarian/analytics?q=x&book_id=1')
        assert resp.status_code == 200
        assert b'<img src=x onerror=alert(1)>' not in resp.data

    def test_evil_title_pdf_export(self, librarian_client, mock_db):
        """Validates evil title pdf export `/librarian/analytics/export` as librarian (expects 200) [TestXssPayloads / analytics edge cases].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        evil = 'Fish & Chips <Best>'
        mock_db['fetch_all'].return_value = [(evil, 5)]
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'top_requested_titles'})
        assert resp.status_code == 200
        assert resp.data[:4] == b'%PDF'


class TestAuth:
    def test_student_blocked(self, student_client, mock_db):
        """Validates student blocked as student (expects 302) [TestAuth / analytics edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates dashboard/stats shown to staff are wrong."""
        for url in ('/librarian/analytics',
                    '/librarian/analytics/dashboard',
                    '/librarian/analytics/chart?name=top_books',
                    '/librarian/analytics/forecast'):
            resp = student_client.get(url)
            assert resp.status_code == 302, url

    def test_anon_redirected(self, client, mock_db):
        """Validates anon redirected `/librarian/analytics` (expects 302) [TestAuth / analytics edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = client.get('/librarian/analytics')
        assert resp.status_code == 302
        assert '/login' in resp.location

    def test_faculty_blocked(self, faculty_client, mock_db):
        """Validates faculty blocked `/librarian/analytics` as faculty (expects 302) [TestAuth / analytics edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates dashboard/stats shown to staff are wrong."""
        resp = faculty_client.get('/librarian/analytics')
        assert resp.status_code == 302
