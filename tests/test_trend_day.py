"""Borrowings Trend dot drill-down: per-program breakdown for one date.

Mocked DB — no Postgres. Covers the trend_day endpoint (validation,
RBAC, SQL shape, totals) and the page wiring (modal + drill attrs).
"""


class TestTrendDayEndpoint:
    URL = '/librarian/analytics/trend_day?date=2026-10-06'

    def test_requires_login(self, client):
        """Validates trend day requires login (expects 302)."""
        assert client.get(self.URL).status_code == 302

    def test_student_blocked(self, student_client):
        """Validates trend day blocked for student (expects 302)."""
        assert student_client.get(self.URL).status_code == 302

    def test_faculty_blocked(self, faculty_client):
        """Validates trend day blocked for faculty (expects 302)."""
        assert faculty_client.get(self.URL).status_code == 302

    def test_invalid_date_rejected(self, librarian_client, mock_db):
        """Validates bad dates return 400 without touching the DB."""
        for bad in ('', 'not-a-date', '10/06/2026', '2026-13-01',
                    '2026-10-06T00:00', '2026-10-06 ' * 3):
            resp = librarian_client.get(
                '/librarian/analytics/trend_day?date=' + bad.strip())
            assert resp.status_code == 400, bad
        assert mock_db['fetch_all'].call_count == 0

    def test_breakdown_totals(self, librarian_client, mock_db):
        """Validates per-program rows and day total."""
        mock_db['fetch_all'].return_value = [('BSCS', 4), ('BSIT', 2)]
        resp = librarian_client.get(self.URL)
        assert resp.status_code == 200
        payload = resp.get_json()
        assert payload['date'] == '2026-10-06'
        assert payload['total'] == 6
        assert payload['by_program'] == [['BSCS', 4], ['BSIT', 2]]

    def test_empty_day(self, librarian_client, mock_db):
        """Validates a date with no borrowings returns total 0."""
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get(self.URL)
        assert resp.status_code == 200
        payload = resp.get_json()
        assert payload['total'] == 0
        assert payload['by_program'] == []

    def test_sql_shape(self, librarian_client, mock_db):
        """Validates the query hits circulation_records with placeholders."""
        mock_db['fetch_all'].return_value = [('BSCS', 1)]
        librarian_client.get(self.URL)
        assert mock_db['fetch_all'].call_count == 1
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'circulation_records' in query
        assert '%s' in query
        assert 'f-string' not in query.lower()
        assert params[0] == '2026-10-06'

    def test_borrow_type_filter_passes_through(self, librarian_client,
                                               mock_db):
        """Validates borrow_type allowlist reaches the query params."""
        mock_db['fetch_all'].return_value = []
        librarian_client.get(self.URL + '&borrow_type=overnight')
        params = mock_db['fetch_all'].call_args[0][1]
        assert 'overnight' in params

    def test_bad_borrow_type_ignored(self, librarian_client, mock_db):
        """Validates an off-allowlist borrow_type means unfiltered."""
        mock_db['fetch_all'].return_value = []
        librarian_client.get(self.URL + '&borrow_type=drop_table')
        params = mock_db['fetch_all'].call_args[0][1]
        assert 'drop_table' not in params


class TestTrendDayPageWiring:
    def test_page_has_modal_and_url(self, librarian_client, mock_db):
        """Validates the analytics page embeds the drill-down modal."""
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/analytics').data.decode()
        assert 'id="trendDayModal"' in body
        assert 'id="trendDayBody"' in body
        assert 'trend-day-bars' in body  # built client-side on open
        assert 'TREND_DAY_URL' in body
        assert '/librarian/analytics/trend_day' in body

    def test_dots_carry_drill_attrs(self, librarian_client, mock_db):
        """Validates trend dots are rendered clickable with their date."""
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/analytics').data.decode()
        assert 'data-drill' in body
        assert "drilldown: 'borrowings'" in body
        assert 'openTrendDayModal' in body
        assert 'z-[130]' in body
