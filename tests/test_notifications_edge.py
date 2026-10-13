"""Edge-case regression tests for user Notifications.

Covers `/user/notifications` and mark-read actions: empty/`None`
lists, short rows, unknown future types, string dates, XSS content,
missing borrowers, cross-user reads (scoped writes only), double
reads, huge ids, and `next` preservation. Everything degrades
gracefully — never 500.
"""


def _borrower(mock_db, bid=5):
    mock_db['fetch_one'].return_value = (bid,)
    mock_db['fetch_all'].return_value = []
    mock_db['execute'].return_value = []


class TestListEdges:
    def test_empty(self, student_client, mock_db):
        """Validates empty `/user/notifications` as student (expects 200) [TestListEdges / notifications edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates notifications are missing or misrouted."""
        _borrower(mock_db)
        assert student_client.get('/user/notifications').status_code == 200

    def test_none_list(self, student_client, mock_db):
        """Validates none list `/user/notifications` as student (expects 200) [TestListEdges / notifications edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates notifications are missing or misrouted."""
        _borrower(mock_db)
        mock_db['fetch_all'].return_value = None
        assert student_client.get('/user/notifications').status_code == 200

    def test_short_rows(self, student_client, mock_db):
        """Validates short rows `/user/notifications` as student (expects 200) [TestListEdges / notifications edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates notifications are missing or misrouted."""
        _borrower(mock_db)
        mock_db['fetch_all'].return_value = [(3,)]
        assert student_client.get('/user/notifications').status_code == 200

    def test_unknown_type(self, student_client, mock_db):
        """Validates unknown type `/user/notifications` as student [TestListEdges / notifications edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates notifications are missing or misrouted."""
        _borrower(mock_db)
        row = (1, 'Hello', 'weird_future_type', '1', '2026-01-05', False)
        mock_db['fetch_all'].return_value = [row]
        body = student_client.get('/user/notifications').data.decode()
        assert 'Weird Future Type' in body

    def test_string_dates(self, student_client, mock_db):
        """Validates string dates `/user/notifications` as student (expects 200) [TestListEdges / notifications edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates notifications are missing or misrouted."""
        _borrower(mock_db)
        row = (1, 'Hello', 'borrow', '1', 'Jan 5', True)
        mock_db['fetch_all'].return_value = [row]
        assert student_client.get('/user/notifications').status_code == 200

    def test_evil_content(self, student_client, mock_db):
        """Validates evil content `/user/notifications` as student [TestListEdges / notifications edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates notifications are missing or misrouted."""
        evil = '<script>alert(1)</script>'
        _borrower(mock_db)
        row = (1, evil, evil, '1', '2026-01-05', False)
        mock_db['fetch_all'].return_value = [row]
        body = student_client.get('/user/notifications').data.decode()
        assert evil not in body

    def test_no_borrower_hides_list(self, admin_client, mock_db):
        """Validates no borrower hides list `/user/notifications` as admin [TestListEdges / notifications edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates notifications are missing or misrouted."""
        mock_db['fetch_one'].return_value = None
        body = admin_client.get('/user/notifications').data.decode()
        assert 'You have no notifications.' in body


class TestReadGuards:
    def test_read_other_users_notification(self, student_client, mock_db):
        """Validates read other users notification `/user/notifications/999/read` as student (expects 302) [TestReadGuards / notifications edge cases].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (UPDATE).
    Failure indicates notifications are missing or misrouted."""
        _borrower(mock_db)
        before = mock_db['execute'].call_count
        resp = student_client.post('/user/notifications/999/read')
        assert resp.status_code == 302
        # Scoped UPDATE only; assert it ran constrained (or not at all).
        for c in mock_db['execute'].call_args_list[before:]:
            assert 'recipient_id' in c[0][0] or 'audit_trail' in c[0][0]

    def test_double_read(self, student_client, mock_db):
        """Validates double read `/user/notifications/1/read` as student (expects 302) [TestReadGuards / notifications edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates notifications are missing or misrouted."""
        _borrower(mock_db)
        assert student_client.post(
            '/user/notifications/1/read').status_code == 302
        assert student_client.post(
            '/user/notifications/1/read').status_code == 302

    def test_read_all_empty(self, student_client, mock_db):
        """Validates read all empty `/user/notifications/read-all` as student (expects 302) [TestReadGuards / notifications edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates notifications are missing or misrouted."""
        _borrower(mock_db)
        assert student_client.post(
            '/user/notifications/read-all').status_code == 302

    def test_huge_id(self, student_client, mock_db):
        """Validates huge id `/user/notifications/999999999/read` as student (expects 302) [TestReadGuards / notifications edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates notifications are missing or misrouted."""
        _borrower(mock_db)
        assert student_client.post(
            '/user/notifications/999999999/read').status_code == 302

    def test_next_preserved(self, student_client, mock_db):
        """Validates next preserved `/user/notifications/read-all` as student (expects 302) [TestReadGuards / notifications edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates notifications are missing or misrouted."""
        _borrower(mock_db)
        resp = student_client.post('/user/notifications/read-all',
                                   data={'next': '/user/history'})
        assert resp.status_code == 302
        assert resp.location.endswith('/user/history')
