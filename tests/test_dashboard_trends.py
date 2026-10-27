"""Librarian overview Borrowing Trends: zero-filled series, hoverable SVG
chart with tooltips, and the info-button documentation modal.

Mocked DB — no Postgres.
"""

from datetime import timedelta


def _pht_today():
    """PHT library today (Asia/Manila) for building mock rows.

    get_daily_borrows zero-fills against library_today(); the host
    clock (UTC on Render, local elsewhere) can trail the Philippines
    by up to 8 hours, so mock dates must be PHT-derived too or the
    zero-filled window silently drops them.
    """
    from app.settings.models import library_today
    return library_today()


class TestDailyBorrowsFill:
    def test_sparse_days_zero_filled(self, mock_db):
        """Validates quiet days fill with zero across the window."""
        from app.main.models import get_daily_borrows
        recent = _pht_today() - timedelta(days=1)
        mock_db['fetch_all'].return_value = [(recent, 3)]
        rows = get_daily_borrows(6)
        assert len(rows) == 6
        assert sum(c for _, c in rows) == 3
        days = [d for d, _ in rows]
        assert days == sorted(days)
        assert days[-1] == _pht_today()
        assert days[0] == _pht_today() - timedelta(days=5)
        assert all(isinstance(c, int) for _, c in rows)

    def test_none_stays_empty(self, mock_db):
        """Validates no rows still means no chart data."""
        from app.main.models import get_daily_borrows
        mock_db['fetch_all'].return_value = None
        assert get_daily_borrows() == []

    def test_string_dates_fill(self, mock_db):
        """Validates ISO string days align to the window."""
        from app.main.models import get_daily_borrows
        today = _pht_today().isoformat()
        mock_db['fetch_all'].return_value = [(today, 2)]
        rows = get_daily_borrows(6)
        assert len(rows) == 6
        assert rows[-1][1] == 2


class TestTrendsCard:
    @staticmethod
    def _rows(mock_db):
        """Test helper _rows: build mocked data or DB stub for the test."""
        mock_db['fetch_one'].return_value = (0,)
        activity = [('Ann', 1, 'Borrowed', 'Some Title', '2026-01-05',
                     None, None)]
        # Days must sit inside the 6-day trailing window ending today
        # (get_daily_borrows zero-fills anything older), and that window
        # is the PHT library calendar, so build them from library_today().
        daily = [(_pht_today() - timedelta(days=1), 4), (_pht_today(), 7)]

        def _fetch_all(query, params=None):
            """Test helper _fetch_all: build mocked data or DB stub for the test."""
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
        # Today's PHT ISO string stays inside the trailing window no
        # matter when the suite runs.
        mock_db['fetch_all'].return_value = [(_pht_today().isoformat(), 5)]
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
