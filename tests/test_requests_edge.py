"""Edge-case regression tests for the Book Request pages.

Covers `/librarian/requests` (+ bulk review) and `/user/request-book`:
empty database, `None` query returns, hostile params (oversized/XSS
input, bogus status/page/sort, malformed bulk ids), missing-borrower
submission, XSS titles/remarks rendering, and the staff/borrower auth
matrix. Includes the `None`-list hardening and the request-date
`strftime` guard. Everything must degrade gracefully — never 500.
"""


def _borrower(mock_db, bid=5):
    """Test helper _borrower: build mocked data or DB stub for the test."""
    mock_db['fetch_one'].return_value = (bid,)


class TestEmptyDb:
    def test_list_empty(self, librarian_client, mock_db):
        """Validates list empty `/librarian/requests` as librarian (expects 200) [TestEmptyDb / requests edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates request/procurement workflow is broken."""
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        assert librarian_client.get('/librarian/requests').status_code == 200

    def test_user_page_empty(self, student_client, mock_db):
        """Validates user page empty `/user/request-book` as student (expects 200) [TestEmptyDb / requests edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates request/procurement workflow is broken."""
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        assert student_client.get('/user/request-book').status_code == 200

    def test_none_lists(self, librarian_client, mock_db):
        """Validates none lists `/librarian/requests` as librarian (expects 200) [TestEmptyDb / requests edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates request/procurement workflow is broken."""
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = None
        assert librarian_client.get('/librarian/requests').status_code == 200


class TestHostileParams:
    @staticmethod
    def _ok(mock_db):
        """Test helper _ok: build mocked data or DB stub for the test."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []

    def test_list_params(self, librarian_client, mock_db):
        """Validates list params as librarian (expects 200) [TestHostileParams / requests edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates request/procurement workflow is broken."""
        self._ok(mock_db)
        urls = ['/librarian/requests?status=bogus',
                '/librarian/requests?status=all',
                '/librarian/requests?search=' + 'x' * 3000,
                '/librarian/requests?search=<script>alert(1)</script>',
                '/librarian/requests?page=abc', '/librarian/requests?page=-5',
                '/librarian/requests?page=999999',
                '/librarian/requests?sort=bogus']
        for url in urls:
            assert librarian_client.get(url).status_code == 200, url[:70]

    def test_submit_hostile(self, student_client, mock_db):
        """Validates submit hostile `/user/request-book` as student (expects 302) [TestHostileParams / requests edge cases].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates request/procurement workflow is broken."""
        _borrower(mock_db)
        mock_db['fetch_all'].return_value = []
        mock_db['execute'].return_value = [(7,)]
        cases = [{'book-title': '   ', 'author': ''},
                 {'book-title': 'T' * 2000, 'author': 'A' * 2000},
                 {'book-title': '<script>alert(1)</script>',
                  'author': '<img src=x>'},
                 {},
                 {'book-title': 'Normal'}]
        for data in cases:
            assert student_client.post(
                '/user/request-book', data=data).status_code == 302, data

    def test_submit_no_borrower(self, admin_client, mock_db):
        """Validates submit no borrower `/user/request-book` as admin (expects 302) [TestHostileParams / requests edge cases].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates request/procurement workflow is broken."""
        mock_db['fetch_one'].return_value = None
        resp = admin_client.post('/user/request-book',
                                 data={'book-title': 'X'})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_bulk_hostile(self, librarian_client, mock_db):
        """Validates bulk hostile `/librarian/requests/bulk/approve` as librarian (expects 302) [TestHostileParams / requests edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates request/procurement workflow is broken."""
        mock_db['fetch_one'].return_value = None
        for data in ({}, {'request_ids': ''}, {'request_ids': 'abc,,--'},
                     {'request_ids': ','.join(['1'] * 150)},
                     {'request_ids': '1,2,3', 'remarks': 'R' * 2000}):
            assert librarian_client.post(
                '/librarian/requests/bulk/approve',
                data=data).status_code == 302, data

    def test_review_hostile_id(self, librarian_client, mock_db):
        """Validates review hostile id `/librarian/requests/999999999/approve` as librarian (expects 302) [TestHostileParams / requests edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates request/procurement workflow is broken."""
        mock_db['fetch_one'].return_value = None
        assert librarian_client.post(
            '/librarian/requests/999999999/approve').status_code == 302


class TestXss:
    def test_evil_titles_render_escaped(self, librarian_client, mock_db):
        """Validates evil titles render escaped `/librarian/requests` as librarian [TestXss / requests edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates request/procurement workflow is broken."""
        evil = '<script>alert(1)</script>'
        row = (1, 5, evil, evil, None, 'pending_review', '2026-01-05',
               None, None, 'note <b>x</b>', 'Ann', 'Student', 'BSIS')
        mock_db['fetch_all'].side_effect = [[row], [('pending_review', 1)],
                                            [(evil, 'Student', 1)]]
        mock_db['fetch_one'].return_value = (1,)
        body = librarian_client.get('/librarian/requests').data.decode()
        assert evil not in body
        assert '<b>x</b>' not in body

    def test_evil_my_requests(self, student_client, mock_db):
        """Validates evil my requests `/user/request-book` as student [TestXss / requests edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates request/procurement workflow is broken."""
        evil = '<img src=x onerror=alert(1)>'
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].return_value = [
            (1, evil, evil, 'pending_review', '2026-01-05', None)]
        body = student_client.get('/user/request-book').data.decode()
        assert evil not in body


class TestAuth:
    def test_anon(self, client):
        """Validates anon `/librarian/requests` (expects 302) [TestAuth / requests edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates request/procurement workflow is broken."""
        assert client.get('/librarian/requests').status_code == 302
        assert client.get('/user/request-book').status_code == 302
        assert client.post('/user/request-book').status_code == 302

    def test_faculty_can_request(self, faculty_client, mock_db):
        """Validates faculty can request `/user/request-book` as faculty (expects 302) [TestAuth / requests edge cases].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates request/procurement workflow is broken."""
        _borrower(mock_db, 6)
        mock_db['fetch_all'].return_value = []
        mock_db['execute'].return_value = [(8,)]
        assert faculty_client.post(
            '/user/request-book',
            data={'book-title': 'Y'}).status_code == 302

    def test_faculty_cannot_review(self, faculty_client, mock_db):
        """Validates faculty cannot review `/librarian/requests` as faculty (expects 302) [TestAuth / requests edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates request/procurement workflow is broken."""
        assert faculty_client.get('/librarian/requests').status_code == 302
        assert faculty_client.post(
            '/librarian/requests/bulk/approve',
            data={'request_ids': '1'}).status_code == 302
