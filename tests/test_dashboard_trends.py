"""Librarian overview Borrowing Trends: zero-filled series, hoverable SVG
chart with tooltips, and the info-button documentation modal.

Mocked DB — no Postgres.
"""

from datetime import date, timedelta


class TestDailyBorrowsFill:
    def test_sparse_days_zero_filled(self, mock_db):
        """Validates quiet days fill with zero across the window."""
        from app.main.models import get_daily_borrows
        mock_db['fetch_all'].return_value = [(date(2026, 10, 10), 3)]
        rows = get_daily_borrows(6)
        assert len(rows) == 6
        assert sum(c for _, c in rows) == 3
        days = [d for d, _ in rows]
        assert days == sorted(days)
        assert days[-1] == date.today()
        assert days[0] == date.today() - timedelta(days=5)
        assert all(isinstance(c, int) for _, c in rows)

    def test_none_stays_empty(self, mock_db):
        """Validates no rows still means no chart data."""
        from app.main.models import get_daily_borrows
        mock_db['fetch_all'].return_value = None
        assert get_daily_borrows() == []

    def test_string_dates_fill(self, mock_db):
        """Validates ISO string days align to the window."""
        from app.main.models import get_daily_borrows
        today = date.today().isoformat()
        mock_db['fetch_all'].return_value = [(today, 2)]
        rows = get_daily_borrows(6)
        assert len(rows) == 6
        assert rows[-1][1] == 2


class TestTrendsCard:
    @staticmethod
    def _rows(mock_db):
        mock_db['fetch_one'].return_value = (0,)
        activity = [('Ann', 1, 'Borrowed', 'Some Title', '2026-01-05',
                     None, None)]
        daily = [(date(2026, 10, 12), 4), (date(2026, 10, 13), 7)]

        def _fetch_all(query, params=None):
            q = str(query)
            if 'DATE(borrow_date)' in q:
                return list(daily)
            if 'full_name' in q:
                return list(activity)
            return []

        mock_db['fetch_all'].side_effect = _fetch_all

    def test_hoverable_chart(self, librarian_client, mock_db):
        """Validates the SVG chart with hoverable dots renders."""
        self._rows(mock_db)
        body = librarian_client.get('/librarian').data.decode()
        assert 'Borrowing Trends' in body
        assert '<svg' in body
        assert 'trend-dot' in body
        assert 'data-count="7"' in body
        assert 'data-date=' in body
        assert 'id="trend-tip"' in body
        assert 'Full trend in Analytics' in body

    def test_info_button_and_modal(self, librarian_client, mock_db):
        """Validates the info button and documentation modal exist."""
        self._rows(mock_db)
        body = librarian_client.get('/librarian').data.decode()
        assert 'data-trend-info' in body
        assert 'id="trendInfoModal"' in body
        for section in ('Definition', 'How to interpret',
                        "How it", 'Example'):
            assert section in body, section

    def test_string_dates_render(self, librarian_client, mock_db):
        """Validates ISO string days render without assuming dates."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = [('2026-10-13', 5)]
        body = librarian_client.get('/librarian').data.decode()
        assert '<svg' in body
        assert 'data-count="5"' in body

    def test_empty_state(self, librarian_client, mock_db):
        """Validates the empty placeholder with no chart data."""
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian').data.decode()
        assert 'No borrowings recorded' in body
        assert 'data-trend-info' in body
