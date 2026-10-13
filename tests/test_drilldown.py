"""Library card drill-down: per-program breakdowns for chart segments.

Mocked DB — no Postgres. Covers the drilldown endpoint (validation,
RBAC, SQL shape per type) and the page wiring (clickable segments).
"""

BASE = '/librarian/analytics/drilldown'


class TestDrilldownAuth:
    def test_requires_login(self, client):
        """Validates drilldown requires login (expects 302)."""
        assert client.get(BASE + '?type=category&category=Science').status_code == 302

    def test_student_blocked(self, student_client):
        """Validates drilldown blocked for student (expects 302)."""
        assert student_client.get(BASE + '?type=category&category=Science').status_code == 302

    def test_faculty_blocked(self, faculty_client):
        """Validates drilldown blocked for faculty (expects 302)."""
        assert faculty_client.get(BASE + '?type=category&category=Science').status_code == 302


class TestDrilldownValidation:
    def test_invalid_type_rejected(self, librarian_client, mock_db):
        """Validates off-allowlist types return 400 without DB touch."""
        for bad in ('', 'drop_table', 'trend_borrowings', 'CATEGORY'):
            resp = librarian_client.get(BASE + '?type=' + bad)
            assert resp.status_code == 400, bad
        assert mock_db['fetch_all'].call_count == 0

    def test_day_types_need_valid_date(self, librarian_client, mock_db):
        """Validates overdue/request day types reject bad dates."""
        for dtype in ('overdue_day', 'request_day'):
            for bad in ('', 'not-a-date', '10/06/2026', '2026-13-40'):
                resp = librarian_client.get(
                    BASE + '?type=' + dtype + '&date=' + bad)
                assert resp.status_code == 400, (dtype, bad)
        assert mock_db['fetch_all'].call_count == 0

    def test_segment_types_need_key(self, librarian_client, mock_db):
        """Validates category/title types reject a missing key."""
        for dtype, param in (('category', 'category'),
                             ('title_demand', 'title'),
                             ('title_fines', 'title'),
                             ('request_title', 'title')):
            resp = librarian_client.get(BASE + '?type=' + dtype)
            assert resp.status_code == 400, dtype
            resp = librarian_client.get(
                BASE + '?type=' + dtype + '&' + param + '=')
            assert resp.status_code == 400, dtype
        assert mock_db['fetch_all'].call_count == 0


class TestDrilldownData:
    def test_overdue_day(self, librarian_client, mock_db):
        """Validates overdue-day breakdown shape and SQL."""
        mock_db['fetch_all'].return_value = [('BSCS', 2), ('BSIT', 1)]
        resp = librarian_client.get(BASE + '?type=overdue_day&date=2026-10-06')
        assert resp.status_code == 200
        payload = resp.get_json()
        assert payload['type'] == 'overdue_day'
        assert payload['key'] == '2026-10-06'
        assert payload['unit'] == 'overdue items'
        assert payload['total'] == 3
        assert payload['by_program'] == [['BSCS', 2], ['BSIT', 1]]
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'circulation_records' in query
        assert '%s' in query
        assert 'overdue' in query
        assert params[0] == '2026-10-06'

    def test_request_day(self, librarian_client, mock_db):
        """Validates request-day breakdown hits request_records."""
        mock_db['fetch_all'].return_value = [('BSCS', 4)]
        resp = librarian_client.get(BASE + '?type=request_day&date=2026-10-06')
        assert resp.status_code == 200
        payload = resp.get_json()
        assert payload['unit'] == 'requests'
        assert payload['total'] == 4
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'request_records' in query
        assert params[0] == '2026-10-06'

    def test_category(self, librarian_client, mock_db):
        """Validates category breakdown passes the category first."""
        mock_db['fetch_all'].return_value = [('BSCS', 5), ('No program', 1)]
        resp = librarian_client.get(BASE + '?type=category&category=Science')
        assert resp.status_code == 200
        payload = resp.get_json()
        assert payload['key'] == 'Science'
        assert payload['unit'] == 'borrowings'
        assert payload['total'] == 6
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'circulation_records' in query and 'book_catalog' in query
        assert params[0] == 'Science'

    def test_title_demand(self, librarian_client, mock_db):
        """Validates demand breakdown scopes to active loans."""
        mock_db['fetch_all'].return_value = [('BSCS', 3)]
        resp = librarian_client.get(BASE + '?type=title_demand&title=Java')
        assert resp.status_code == 200
        payload = resp.get_json()
        assert payload['unit'] == 'active loans'
        assert payload['total'] == 3
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'active' in query
        assert params[0] == 'Java'

    def test_title_fines_money(self, librarian_client, mock_db):
        """Validates fine amounts stay decimal with fines unit."""
        mock_db['fetch_all'].return_value = [('BSCS', 12.5, 2),
                                              ('BSIT', 5.0, 1)]
        resp = librarian_client.get(BASE + '?type=title_fines&title=Java')
        assert resp.status_code == 200
        payload = resp.get_json()
        assert payload['unit'] == 'fines'
        assert payload['total'] == 17.5
        assert payload['by_program'] == [['BSCS', 12.5], ['BSIT', 5.0]]

    def test_request_title(self, librarian_client, mock_db):
        """Validates per-title request breakdown is pending-scoped."""
        mock_db['fetch_all'].return_value = [('BSCS', 2)]
        resp = librarian_client.get(BASE + '?type=request_title&title=Java')
        assert resp.status_code == 200
        payload = resp.get_json()
        assert payload['unit'] == 'requests'
        assert payload['total'] == 2
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'request_records' in query
        assert 'pending_review' in query
        assert params[0] == 'Java'

    def test_empty_segment(self, librarian_client, mock_db):
        """Validates an empty breakdown returns total 0."""
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get(BASE + '?type=category&category=Science')
        assert resp.status_code == 200
        assert resp.get_json()['total'] == 0


class TestDrilldownPageWiring:
    def test_page_wiring(self, librarian_client, mock_db):
        """Validates the analytics page wires every drill-down."""
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/analytics').data.decode()
        assert 'DRILLDOWN_URL' in body
        assert '/librarian/analytics/drilldown' in body
        assert 'openDrilldownFor' in body
        assert 'openProgramModal' in body
        for kind in ("drilldown: 'overdue'", "drilldown: 'requests'",
                     "'data-drill', 'category'",
                     'data-drill="title_demand"', 'data-drill="title_fines"',
                     'data-drill="request_title"',
                     "kind === 'overdue'", "kind === 'category'",
                     "kind === 'title_fines'", "kind === 'request_title'",
                     'annotatePeakBarsInto', 'annotateTopCats'):
            assert kind in body, kind
