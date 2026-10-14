"""Edge-case regression tests for the student/faculty overview (/user/profile).

Covers short/missing user rows, overdue/due-soon notification
generation, datetime due dates, garbage reminder config, faculty
borrow limits, XSS content across loans/requests/notifications, and
short request rows. Everything must degrade gracefully — never 500.
"""


def _base(mock_db, borrower=(5, 1, 'S1', 'BSIS', 'a', None, None, None),
          user=(1, 'e@x.ph', 'Student', 'Ann Santos')):
    """Test helper _base: build mocked data or DB stub for the test."""
    mock_db['fetch_one'].side_effect = None
    mock_db['fetch_one'].return_value = user
    mock_db['fetch_all'].side_effect = None
    mock_db['fetch_all'].return_value = []
    return borrower


class TestOverviewEdges:
    def test_short_user_data(self, student_client, mock_db):
        """Validates short user data `/user/profile` as student (expects 200) [TestOverviewEdges / profile edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates user management/profile is broken."""
        mock_db['fetch_one'].return_value = (1, 'e@x.ph')
        mock_db['fetch_all'].return_value = []
        assert student_client.get('/user/profile').status_code == 200

    def test_none_user_data(self, student_client, mock_db):
        """Validates none user data `/user/profile` as student (expects 200) [TestOverviewEdges / profile edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates user management/profile is broken."""
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        assert student_client.get('/user/profile').status_code == 200

    def test_overdue_generates_notification(self, student_client, mock_db):
        """Validates overdue generates notification `/user/profile` as student (expects 200) [TestOverviewEdges / profile edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates user management/profile is broken."""
        _base(mock_db)
        loan = (7, 1, '2026-01-01', '2026-01-02', 'overdue', 'T',
                '2026-01-01', '2026-01-01', 0.0, 'active')
        mock_db['fetch_all'].side_effect = [[(5, 1, 'S1', 'BSIS', 'a',
                                              None, None, None)],
                                            [loan], [], [], [], [],
                                            [(0,)], []]
        mock_db['fetch_one'].side_effect = [(1, 'e@x.ph', 'Student',
                                             'Ann Santos'),
                                            (5, 1, 'S1', 'BSIS', 'a',
                                             None, None, None),
                                            None, None, (0,), None, None]
        assert student_client.get('/user/profile').status_code == 200

    def test_datetime_due(self, student_client, mock_db):
        """Validates datetime due `/user/profile` as student (expects 200) [TestOverviewEdges / profile edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates user management/profile is broken."""
        from datetime import datetime
        _base(mock_db)
        loan = (7, 1, datetime(2026, 1, 2, 10, 0), '2026-01-02', 'active',
                'T', '2026-01-01', '2026-01-01', 0.0, 'active')
        mock_db['fetch_all'].side_effect = [[(5, 1, 'S1', 'BSIS', 'a',
                                              None, None, None)],
                                            [loan], [], [], [], [], [],
                                            []]
        assert student_client.get('/user/profile').status_code == 200

    def test_garbage_due_config(self, student_client, mock_db, app):
        """Validates garbage due config `/user/profile` as student (expects 200) [TestOverviewEdges / profile edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates user management/profile is broken."""
        _base(mock_db)
        app.config['DUE_SOON_NOTIFY_DAYS'] = 'junk'
        try:
            assert student_client.get('/user/profile').status_code == 200
        finally:
            app.config.pop('DUE_SOON_NOTIFY_DAYS', None)

    def test_faculty_limit_path(self, faculty_client, mock_db):
        """Validates faculty limit path `/user/profile` as faculty (expects 200) [TestOverviewEdges / profile edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates user management/profile is broken."""
        mock_db['fetch_one'].return_value = (2, 'f@x.ph', 'Faculty', 'Fac')
        mock_db['fetch_all'].return_value = []
        assert faculty_client.get('/user/profile').status_code == 200

    def test_evil_content(self, student_client, mock_db):
        """Validates evil content `/user/profile` as student [TestOverviewEdges / profile edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates user management/profile is broken."""
        evil = '<script>alert(1)</script>'
        _base(mock_db, user=(1, 'e@x.ph', 'Student', evil))
        loan = (7, 1, '2026-01-01', '2026-01-02', 'active', evil,
                '2026-01-01', '2026-01-01', 0.0, 'active')
        notif = (1, 5, evil, 'borrow', '1', False, '2026-01-01')
        mock_db['fetch_all'].side_effect = [
            [(5, 1, 'S1', 'BSIS', 'a', None, None, None)],
            [loan], [], [(1, evil, evil, 'pending_review', '2026-01-05',
                          None)],
            [notif], [(0,)], [(0.0,)], [notif]]
        body = student_client.get('/user/profile').data.decode()
        assert evil not in body

    def test_short_my_requests(self, student_client, mock_db):
        """Validates short my requests `/user/profile` as student (expects 200) [TestOverviewEdges / profile edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates user management/profile is broken."""
        _base(mock_db)
        mock_db['fetch_all'].side_effect = [
            [(5, 1, 'S1', 'BSIS', 'a', None, None, None)],
            [], [], [(1,)], [], [], [], []]
        assert student_client.get('/user/profile').status_code == 200
