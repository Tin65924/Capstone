"""Edge-case regression tests for student History (/user/history).

Covers empty/`None` lists, short rows in every section (including the
fine-amount float crash), string amounts/dates, XSS everywhere, and
auth. Same float-on-missing-index hardening applied to the staff
per-user history page.
"""


def _base(mock_db):
    """Test helper _base: build mocked data or DB stub for the test."""
    mock_db['fetch_one'].side_effect = None
    mock_db['fetch_one'].return_value = (5, 1, 'S1', 'BSIS', 'a', None,
                                         None, None)
    mock_db['fetch_all'].side_effect = None
    mock_db['fetch_all'].return_value = []


class TestHistoryEdges:
    def test_empty(self, student_client, mock_db):
        """Validates empty `/user/history` as student (expects 200) [TestHistoryEdges / user history edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates user management/profile is broken."""
        _base(mock_db)
        assert student_client.get('/user/history').status_code == 200

    def test_none_lists(self, student_client, mock_db):
        """Validates none lists `/user/history` as student (expects 200) [TestHistoryEdges / user history edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates user management/profile is broken."""
        _base(mock_db)
        mock_db['fetch_all'].return_value = None
        assert student_client.get('/user/history').status_code == 200

    def test_no_borrower(self, admin_client, mock_db):
        """Validates no borrower `/user/history` as admin (expects 200) [TestHistoryEdges / user history edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates user management/profile is broken."""
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        assert admin_client.get('/user/history').status_code == 200

    def test_short_rows_every_section(self, student_client, mock_db):
        """Validates short rows every section `/user/history` as student (expects 200) [TestHistoryEdges / user history edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates user management/profile is broken."""
        _base(mock_db)
        mock_db['fetch_all'].side_effect = [
            [(7,)],  # transactions
            [(1,)],  # my_requests
            [(3,)],  # reservations
            [(9,)],  # fines
            [(0,)],  # total fines (fetch_one? no—side_effect order below)
            [(2,)],  # notifications
        ]
        mock_db['fetch_one'].return_value = (0,)
        assert student_client.get('/user/history').status_code == 200

    def test_string_amounts_dates(self, student_client, mock_db):
        """Validates string amounts dates `/user/history` as student [TestHistoryEdges / user history edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates user management/profile is broken."""
        _base(mock_db)
        tx = (7, '2026-01-01', '2026-01-02', '2026-01-03', 'overnight',
              'returned', '25.5', 'T', 'A', 'ACC-1')
        fine = (9, 7, '2026-01-02', '2026-01-03', '25.5', 'T', 'A')
        res = (3, 1, 'waiting', '2026-01-04', None, 'T', 'A')
        notif = (2, 'Hello', 'borrow', '1', '2026-01-05')
        mock_db['fetch_all'].side_effect = [
            [tx], [(1, 'T', 'A', 'pending_review', 'Jan 5', None)], [res],
            [fine], [notif]]
        mock_db['fetch_one'].return_value = (25.5,)
        body = student_client.get('/user/history').data.decode()
        assert '25.50' in body or '25.5' in body

    def test_evil_everywhere(self, student_client, mock_db):
        """Validates evil everywhere `/user/history` as student [TestHistoryEdges / user history edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates user management/profile is broken."""
        evil = '<script>alert(1)</script>'
        _base(mock_db)
        tx = (7, '2026-01-01', '2026-01-02', None, 'overnight', 'active',
              0.0, evil, evil, evil)
        fine = (9, 7, '2026-01-02', None, 10.0, evil, evil)
        res = (3, 1, 'waiting', '2026-01-04', None, evil, evil)
        notif = (2, evil, 'borrow', '1', '2026-01-05')
        req = (1, evil, evil, 'approved', '2026-01-05', evil)
        mock_db['fetch_all'].side_effect = [[tx], [req], [res], [fine],
                                            [notif]]
        mock_db['fetch_one'].return_value = (10.0,)
        body = student_client.get('/user/history').data.decode()
        assert evil not in body

    def test_anon(self, client):
        """Validates anon `/user/history` (expects 302) [TestHistoryEdges / user history edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates user management/profile is broken."""
        assert client.get('/user/history').status_code == 302

    def test_staff_short_fine_row(self, librarian_client, mock_db):
        """Validates staff short fine row `/librarian/users/4/history` as librarian (expects 200) [TestHistoryEdges / user history edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates user management/profile is broken."""
        mock_db['fetch_one'].side_effect = [
            (4, 'a@x.ph', 'Student', 'Ann'),
            (5, 1, 'S1', 'BSIS', 'a', None, None, None)]
        mock_db['fetch_all'].return_value = [(9,)]
        assert librarian_client.get(
            '/librarian/users/4/history').status_code == 200
