"""User history tabs + pagination (/user/history) and notification page size.

Mocked DB — no Postgres. History shows one tab at a time (borrowing /
fines / reservations / requests), 10 cards per page; the notifications
section is gone from history and the notifications page shows 10/page.
"""

from datetime import date

BORROWER = (1, 1, '2024-0001', 'CS', 'active', None, None, None)


def _tx(i):
    return (i, date(2026, 8, 1), date(2026, 8, 2), None, 'overnight',
            'active', 0, 'Hist-Book-%02d' % i, 'Hist-Author', 'ACC-%02d' % i)


def _fine(i):
    return (i, 7, date(2026, 8, 2), None, 5.0, 'Fine-Book-%02d' % i,
            'Fine-Author')


def _res(i):
    return (i, i, 'waiting', '2026-01-04', None, 'Res-Book-%02d' % i,
            'Res-Author')


def _req(i):
    return (i, 'Req-Book-%02d' % i, 'Req-Author', 'pending_review',
            'Jan 5', None)


def _install(mock_db, tx=(), req=(), res=(), fines=()):
    mock_db['fetch_one'].return_value = BORROWER
    # Cycle per request: each page load consumes the four fetches in
    # route-call order, so a plain list would be exhausted by request 2.
    data = [list(tx), list(req), list(res), list(fines)]
    calls = {'n': 0}

    def _next(*args, **kwargs):
        out = data[calls['n'] % len(data)]
        calls['n'] += 1
        return list(out)

    mock_db['fetch_all'].side_effect = _next


class TestHistoryTabs:
    def test_default_tab_is_borrowing(self, student_client, mock_db):
        """Validates default tab shows borrowings only."""
        _install(mock_db, tx=[_tx(1)], req=[_req(1)], res=[_res(1)],
                 fines=[_fine(1)])
        body = student_client.get('/user/history').data.decode()
        assert 'Hist-Book-01' in body
        assert 'Fine-Book-01' not in body
        assert 'Res-Book-01' not in body
        assert 'Req-Book-01' not in body
        for label in ('Borrowings &amp; Returns', 'Fines',
                      'Reservation History', 'Book Requests'):
            assert label in body

    def test_fines_tab(self, student_client, mock_db):
        """Validates fines tab shows fines only."""
        _install(mock_db, tx=[_tx(1)], fines=[_fine(1)])
        body = student_client.get('/user/history?tab=fines').data.decode()
        assert 'Fine-Book-01' in body
        assert 'Hist-Book-01' not in body

    def test_reservations_tab(self, student_client, mock_db):
        """Validates reservations tab shows reservations only."""
        _install(mock_db, tx=[_tx(1)], res=[_res(1)])
        body = student_client.get(
            '/user/history?tab=reservations').data.decode()
        assert 'Res-Book-01' in body
        assert 'Hist-Book-01' not in body

    def test_requests_tab(self, student_client, mock_db):
        """Validates requests tab shows book requests only."""
        _install(mock_db, tx=[_tx(1)], req=[_req(1)])
        body = student_client.get(
            '/user/history?tab=requests').data.decode()
        assert 'Req-Book-01' in body
        assert 'Hist-Book-01' not in body

    def test_invalid_tab_falls_back(self, student_client, mock_db):
        """Validates a bogus tab falls back to borrowing."""
        _install(mock_db, tx=[_tx(1)], fines=[_fine(1)])
        body = student_client.get('/user/history?tab=drop_table').data.decode()
        assert 'Hist-Book-01' in body
        assert 'Fine-Book-01' not in body

    def test_notifications_gone(self, student_client, mock_db):
        """Validates no notification section on the history page."""
        _install(mock_db, tx=[_tx(1)])
        body = student_client.get('/user/history').data.decode()
        assert 'Notification History' not in body


class TestHistoryPagination:
    def test_eleven_borrowings_paginate(self, student_client, mock_db):
        """Validates max 10 cards per page with a pager."""
        _install(mock_db, tx=[_tx(i) for i in range(1, 12)])
        page1 = student_client.get('/user/history').data.decode()
        assert 'Hist-Book-01' in page1
        assert 'Hist-Book-10' in page1
        assert 'Hist-Book-11' not in page1
        assert 'Page 1 of 2' in page1
        assert '?tab=borrowing&page=2' in page1
        page2 = student_client.get('/user/history?page=2').data.decode()
        assert 'Hist-Book-11' in page2
        assert 'Hist-Book-01' not in page2
        assert 'Page 2 of 2' in page2

    def test_ten_or_fewer_no_pager(self, student_client, mock_db):
        """Validates short lists render without a pager."""
        _install(mock_db, tx=[_tx(i) for i in range(1, 4)])
        body = student_client.get('/user/history').data.decode()
        assert 'Hist-Book-03' in body
        assert 'Page 1 of' not in body

    def test_bad_and_huge_page(self, student_client, mock_db):
        """Validates bad pages fall back and huge pages clamp."""
        _install(mock_db, tx=[_tx(i) for i in range(1, 12)])
        for bad in ('abc', '0', '-3'):
            body = student_client.get(
                '/user/history?page=%s' % bad).data.decode()
            assert 'Hist-Book-01' in body
            assert 'Page 1 of 2' in body
        body = student_client.get('/user/history?page=999').data.decode()
        assert 'Hist-Book-11' in body
        assert 'Page 2 of 2' in body

    def test_each_tab_paginates(self, student_client, mock_db):
        """Validates pagination applies to every tab, not just borrowing."""
        _install(mock_db, fines=[_fine(i) for i in range(1, 12)])
        body = student_client.get('/user/history?tab=fines').data.decode()
        assert 'Fine-Book-10' in body
        assert 'Fine-Book-11' not in body
        assert 'Page 1 of 2' in body
        body = student_client.get(
            '/user/history?tab=fines&page=2').data.decode()
        assert 'Fine-Book-11' in body
        assert '?tab=fines&page=1' in body


class TestNotificationsPageSize:
    @staticmethod
    def _rows(n):
        return [(i, 'np-%03d-xyz' % i, 'borrow', str(i), '2026-01-05',
                 False) for i in range(1, n + 1)]

    def test_ten_per_page(self, student_client, mock_db):
        """Validates the notifications page shows max 10 per page."""
        mock_db['fetch_one'].return_value = BORROWER
        mock_db['fetch_all'].return_value = self._rows(11)
        page1 = student_client.get('/user/notifications').data.decode()
        assert 'np-001-xyz' in page1
        assert 'np-010-xyz' in page1
        assert 'np-011-xyz' not in page1
        assert 'Page 1 of 2' in page1
        page2 = student_client.get('/user/notifications?page=2').data.decode()
        assert 'np-011-xyz' in page2
        assert 'np-001-xyz' not in page2
        assert 'Page 2 of 2' in page2
