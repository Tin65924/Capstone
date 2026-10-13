"""Overdue display regression tests (faculty /user pages).

The DB never flips circulation status to 'overdue', so date-past-due
active loans must still render as Overdue via Python-side date checks.
Covers profile + history badges, overdue_count, empty/XSS loans, the
suggestions fallback, and notifications pagination.
"""

import re
from datetime import date, timedelta
from unittest.mock import patch

FACULTY_PROFILE = (2, 'faculty@mcst.edu.ph', 'Faculty', 'Test Faculty',
                   5, 'F-1', 'Science', None, 'active')
FACULTY_BORROWER = (5, 2, 'F-1', 'Science', None, 'active', None, None)


def _install(mock_db, loans=None, transactions=None, notifications=None,
             active_count=None):
    """Dispatch mocked DB returns by SQL so fetch call order is irrelevant."""
    loans = list(loans or [])
    txs = list(transactions if transactions is not None else loans)
    notifs = list(notifications or [])
    count = len(loans) if active_count is None else active_count

    def fake_fetch_one(query, params=None):
        q = str(query)
        if 'LEFT JOIN borrowers' in q:
            return FACULTY_PROFILE
        if 'FROM borrowers WHERE user_id' in q:
            return FACULTY_BORROWER
        if 'COUNT(*) FROM circulation_records' in q:
            return (count,)
        if 'COUNT(*) FROM notification_log' in q:
            return (0,)
        if 'COALESCE(SUM(fine_amount)' in q:
            return (0,)
        if 'FROM notification_log' in q:
            return (1,)  # notification_exists -> already reminded
        return None

    def fake_fetch_all(query, params=None):
        q = str(query)
        if 'FROM notification_log' in q:
            return list(notifs)
        if 'FROM reservation_queue' in q:
            return []
        if 'FROM request_records' in q:
            return []
        if 'fine_amount > 0' in q:
            return []
        if 'br.user_id' in q:
            return list(txs)
        if 'FROM circulation_records' in q:
            return list(loans)
        if 'FROM departments' in q:
            return []
        return []

    mock_db['fetch_one'].side_effect = fake_fetch_one
    mock_db['fetch_all'].side_effect = fake_fetch_all


def _profile_loan(cid, due, status='active', title='T', acc='ACC-1'):
    return (cid, '2026-01-01', due, 'daily_circulation', status, title, acc)


def _history_tx(cid, due, status='active', returned=None, title='T'):
    return (cid, '2026-01-01', due, returned, 'daily_circulation',
            status, 0.0, title, 'A', 'ACC-1')


def _overdue_card_count(body):
    m = re.search(r'Overdue Books</p>\s*<h3[^>]*>(\d+)</h3>', body)
    assert m, 'overdue stat card not found'
    return int(m.group(1))


class TestProfileOverdueDisplay:
    def test_past_due_active_renders_overdue(self, faculty_client, mock_db):
        """Validates past due active renders overdue `/user/profile` as faculty (expects 200) [TestProfileOverdueDisplay / overdue display].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates overdue display is broken for this case (users see wrong page, blocked action, or bad data)."""
        past = (date.today() - timedelta(days=3)).isoformat()
        _install(mock_db, loans=[_profile_loan(7, past)], active_count=1)
        resp = faculty_client.get('/user/profile')
        assert resp.status_code == 200
        body = resp.data.decode()
        assert '>Overdue</span>' in body
        assert '>On Time</span>' not in body
        assert _overdue_card_count(body) == 1

    def test_due_today_renders_on_time(self, faculty_client, mock_db):
        """Validates due today renders on time `/user/profile` as faculty (expects 200) [TestProfileOverdueDisplay / overdue display].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates overdue display is broken for this case (users see wrong page, blocked action, or bad data)."""
        _install(mock_db, loans=[_profile_loan(8, date.today().isoformat())],
                 active_count=1)
        resp = faculty_client.get('/user/profile')
        assert resp.status_code == 200
        body = resp.data.decode()
        assert '>On Time</span>' in body
        assert '>Overdue</span>' not in body
        assert _overdue_card_count(body) == 0

    def test_flagged_overdue_still_renders(self, faculty_client, mock_db):
        """Validates flagged overdue still renders `/user/profile` as faculty (expects 200) [TestProfileOverdueDisplay / overdue display].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates overdue display is broken for this case (users see wrong page, blocked action, or bad data)."""
        future = (date.today() + timedelta(days=5)).isoformat()
        _install(mock_db, loans=[_profile_loan(9, future, status='overdue')],
                 active_count=1)
        resp = faculty_client.get('/user/profile')
        assert resp.status_code == 200
        body = resp.data.decode()
        assert '>Overdue</span>' in body
        assert _overdue_card_count(body) == 1

    def test_datetime_due_in_past_renders_overdue(self, faculty_client, mock_db):
        """Validates datetime due in past renders overdue `/user/profile` as faculty (expects 200) [TestProfileOverdueDisplay / overdue display].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates overdue display is broken for this case (users see wrong page, blocked action, or bad data)."""
        from datetime import datetime
        due = datetime.now().replace(microsecond=0) - timedelta(days=2)
        _install(mock_db, loans=[_profile_loan(10, due)], active_count=1)
        resp = faculty_client.get('/user/profile')
        assert resp.status_code == 200
        assert '>Overdue</span>' in resp.data.decode()

    def test_empty_loans_render(self, faculty_client, mock_db):
        """Validates empty loans render `/user/profile` as faculty (expects 200) [TestProfileOverdueDisplay / overdue display].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates overdue display is broken for this case (users see wrong page, blocked action, or bad data)."""
        _install(mock_db, loans=[], active_count=0)
        resp = faculty_client.get('/user/profile')
        assert resp.status_code == 200
        body = resp.data.decode()
        assert 'You have no active borrowings.' in body
        assert _overdue_card_count(body) == 0

    def test_hostile_loan_rows_escaped(self, faculty_client, mock_db):
        """Validates hostile loan rows escaped `/user/profile` as faculty [TestProfileOverdueDisplay / overdue display].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates overdue display is broken for this case (users see wrong page, blocked action, or bad data)."""
        evil = '<script>alert(1)</script>'
        future = (date.today() + timedelta(days=5)).isoformat()
        _install(mock_db, loans=[_profile_loan(11, future, title=evil, acc=evil)],
                 active_count=1)
        body = faculty_client.get('/user/profile').data.decode()
        assert evil not in body


class TestHistoryOverdueDisplay:
    def test_past_due_active_badge(self, faculty_client, mock_db):
        """Validates past due active badge `/user/history` as faculty [TestHistoryOverdueDisplay / overdue display].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates overdue display is broken for this case (users see wrong page, blocked action, or bad data)."""
        past = (date.today() - timedelta(days=4)).isoformat()
        _install(mock_db, transactions=[_history_tx(7, past)])
        body = faculty_client.get('/user/history').data.decode()
        assert re.search(r'>\s*Overdue\s*<', body)

    def test_due_today_badge_borrowed(self, faculty_client, mock_db):
        """Validates due today badge borrowed `/user/history` as faculty [TestHistoryOverdueDisplay / overdue display].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates overdue display is broken for this case (users see wrong page, blocked action, or bad data)."""
        _install(mock_db,
                 transactions=[_history_tx(8, date.today().isoformat())])
        body = faculty_client.get('/user/history').data.decode()
        assert re.search(r'>\s*Borrowed\s*<', body)
        assert re.search(r'>\s*Overdue\s*<', body) is None

    def test_returned_past_due_not_overdue(self, faculty_client, mock_db):
        """Validates returned past due not overdue `/user/history` as faculty [TestHistoryOverdueDisplay / overdue display].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates overdue display is broken for this case (users see wrong page, blocked action, or bad data)."""
        past = (date.today() - timedelta(days=9)).isoformat()
        _install(mock_db, transactions=[_history_tx(9, past, status='returned',
                                                    returned='2026-01-10')])
        body = faculty_client.get('/user/history').data.decode()
        assert re.search(r'>\s*Returned\s*<', body)
        assert re.search(r'>\s*Overdue\s*<', body) is None

    def test_flagged_overdue_badge(self, faculty_client, mock_db):
        """Validates flagged overdue badge `/user/history` as faculty [TestHistoryOverdueDisplay / overdue display].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates overdue display is broken for this case (users see wrong page, blocked action, or bad data)."""
        future = (date.today() + timedelta(days=5)).isoformat()
        _install(mock_db, transactions=[_history_tx(10, future,
                                                    status='overdue')])
        body = faculty_client.get('/user/history').data.decode()
        assert re.search(r'>\s*Overdue\s*<', body)

    def test_history_hostile_rows_escaped(self, faculty_client, mock_db):
        """Validates history hostile rows escaped `/user/history` as faculty [TestHistoryOverdueDisplay / overdue display].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates overdue display is broken for this case (users see wrong page, blocked action, or bad data)."""
        evil = '<script>alert(1)</script>'
        _install(mock_db, transactions=[_history_tx(11, 'not-a-date',
                                                    title=evil)])
        body = faculty_client.get('/user/history').data.decode()
        assert evil not in body


class TestSuggestionsFallback:
    def test_suggest_book_values_failure_still_200(self, faculty_client,
                                                   mock_db):
        """Validates suggest book values failure still 200 `/api/suggestions?field=book_title&q=clean` as faculty (expects 200) [TestSuggestionsFallback / overdue display].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates overdue display is broken for this case (users see wrong page, blocked action, or bad data)."""
        with patch('app.main.routes.suggest_book_values',
                    side_effect=Exception('db down')):
            resp = faculty_client.get(
                '/api/suggestions?field=book_title&q=clean')
        assert resp.status_code == 200
        assert resp.get_json() == {'suggestions': []}


class TestNotificationsPagination:
    @staticmethod
    def _rows(n):
        return [(i, 'note-%03d-xyz' % i, 'borrow', str(i), '2026-01-05',
                 False) for i in range(1, n + 1)]

    def test_page_two_slices(self, faculty_client, mock_db):
        """Validates page two slices `/user/notifications?page=2` as faculty [TestNotificationsPagination / overdue display].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates overdue display is broken for this case (users see wrong page, blocked action, or bad data)."""
        _install(mock_db, notifications=self._rows(55))
        body = faculty_client.get(
            '/user/notifications?page=2').data.decode()
        assert 'note-011-xyz' in body
        assert 'note-020-xyz' in body
        assert 'note-001-xyz' not in body
        assert 'note-021-xyz' not in body
        assert 'Page 2 of 6' in body
        assert '?page=1' in body
        assert '?page=3' in body

    def test_bad_page_falls_back_to_one(self, faculty_client, mock_db):
        """Validates bad page falls back to one `/user/notifications?page=%s` as faculty [TestNotificationsPagination / overdue display].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates overdue display is broken for this case (users see wrong page, blocked action, or bad data)."""
        _install(mock_db, notifications=self._rows(55))
        for bad in ('abc', '0', '-3'):
            body = faculty_client.get(
                '/user/notifications?page=%s' % bad).data.decode()
            assert 'note-001-xyz' in body
            assert 'Page 1 of 6' in body

    def test_huge_page_clamps_to_last(self, faculty_client, mock_db):
        """Validates huge page clamps to last `/user/notifications?page=999` as faculty [TestNotificationsPagination / overdue display].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates overdue display is broken for this case (users see wrong page, blocked action, or bad data)."""
        _install(mock_db, notifications=self._rows(55))
        body = faculty_client.get(
            '/user/notifications?page=999').data.decode()
        assert 'note-055-xyz' in body
        assert 'note-001-xyz' not in body
        assert 'Page 6 of 6' in body
