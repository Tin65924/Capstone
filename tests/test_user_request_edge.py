"""Edge-case regression tests for the student Request Book page.

Covers the request form and My Requests list: DB column length limits
(255/150 enforced server-side plus maxlength inputs), duplicate
detection across case/abbreviation variants, all status badges,
short rows, `None` rows, string dates, and XSS everywhere. Includes
the length-validation and badge-rendering fixes.
"""


def _borrower(mock_db, bid=5):
    mock_db['fetch_one'].return_value = (bid,)
    mock_db['fetch_all'].return_value = []
    mock_db['execute'].return_value = [(9,)]


class TestLengthLimits:
    def test_overlong_title_rejected(self, student_client, mock_db):
        """Validates overlong title rejected `/user/request-book` as student (expects 302) [TestLengthLimits / user request edge cases].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates request/procurement workflow is broken."""
        _borrower(mock_db)
        resp = student_client.post('/user/request-book',
                                   data={'book-title': 'T' * 256})
        assert resp.status_code == 302
        writes = [c[0][0] for c in mock_db['execute'].call_args_list
                  if 'INSERT INTO request_records' in c[0][0]]
        assert writes == []

    def test_overlong_author_rejected(self, student_client, mock_db):
        """Validates overlong author rejected `/user/request-book` as student (expects 302) [TestLengthLimits / user request edge cases].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates request/procurement workflow is broken."""
        _borrower(mock_db)
        resp = student_client.post('/user/request-book',
                                   data={'book-title': 'T',
                                         'author': 'A' * 151})
        assert resp.status_code == 302
        writes = [c[0][0] for c in mock_db['execute'].call_args_list
                  if 'INSERT INTO request_records' in c[0][0]]
        assert writes == []

    def test_boundary_lengths_accepted(self, student_client, mock_db):
        """Validates boundary lengths accepted `/user/request-book` as student (expects 302) [TestLengthLimits / user request edge cases].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates request/procurement workflow is broken."""
        _borrower(mock_db)
        resp = student_client.post('/user/request-book',
                                   data={'book-title': 'T' * 255,
                                         'author': 'A' * 150})
        assert resp.status_code == 302
        writes = [c[0][0] for c in mock_db['execute'].call_args_list
                  if 'INSERT INTO request_records' in c[0][0]]
        assert len(writes) == 1


class TestDuplicates:
    def test_case_variant_blocked(self, student_client, mock_db):
        """Validates case variant blocked `/user/request-book` as student (expects 302) [TestDuplicates / user request edge cases].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates request/procurement workflow is broken."""
        _borrower(mock_db)
        mock_db['fetch_all'].return_value = [('clean code',)]
        resp = student_client.post('/user/request-book',
                                   data={'book-title': 'Clean Code'})
        assert resp.status_code == 302
        writes = [c[0][0] for c in mock_db['execute'].call_args_list
                  if 'INSERT INTO request_records' in c[0][0]]
        assert writes == []

    def test_abbreviation_blocked(self, student_client, mock_db):
        """Validates abbreviation blocked `/user/request-book` as student (expects 302) [TestDuplicates / user request edge cases].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates request/procurement workflow is broken."""
        _borrower(mock_db)
        mock_db['fetch_all'].return_value = [('Introduction to Programming',)]
        resp = student_client.post('/user/request-book',
                                   data={'book-title': 'Intro to Programming'})
        assert resp.status_code == 302
        writes = [c[0][0] for c in mock_db['execute'].call_args_list
                  if 'INSERT INTO request_records' in c[0][0]]
        assert writes == []


class TestDisplayStates:
    @staticmethod
    def _page(student_client, mock_db, rows):
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].return_value = rows
        return student_client.get('/user/request-book').data.decode()

    def test_all_statuses(self, student_client, mock_db):
        """Validates all statuses as student [TestDisplayStates / user request edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates request/procurement workflow is broken."""
        rows = [(1, 'A', 'Au', s, '2026-01-05', None)
                for s in ('pending_review', 'approved', 'rejected',
                          'procured', 'existing_in_collection')]
        body = self._page(student_client, mock_db, rows)
        for label in ('Pending Review', 'Approved', 'Rejected', 'Procured',
                      'Existing In Collection'):
            assert label in body, label

    def test_short_rows(self, student_client, mock_db):
        """Validates short rows as student [TestDisplayStates / user request edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates request/procurement workflow is broken."""
        body = self._page(student_client, mock_db, [(1,)])
        assert 'My Requests' in body

    def test_none_rows(self, student_client, mock_db):
        """Validates none rows `/user/request-book` as student (expects 200) [TestDisplayStates / user request edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates request/procurement workflow is broken."""
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].return_value = None
        assert student_client.get('/user/request-book').status_code == 200

    def test_string_dates(self, student_client, mock_db):
        """Validates string dates as student [TestDisplayStates / user request edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates request/procurement workflow is broken."""
        rows = [(1, 'A', 'Au', 'pending_review', 'Jan 5', None)]
        body = self._page(student_client, mock_db, rows)
        assert 'Jan 5' in body

    def test_xss_everywhere(self, student_client, mock_db):
        """Validates xss everywhere as student [TestDisplayStates / user request edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates request/procurement workflow is broken."""
        evil = '<script>alert(1)</script>'
        rows = [(1, evil, evil, 'rejected', '2026-01-05', evil)]
        body = self._page(student_client, mock_db, rows)
        assert evil not in body
