"""Library opening/closing hours: settings UI + validation, borrow
guards, and closing-time dues. Mocked DB — no Postgres.
"""

from datetime import datetime
from unittest.mock import patch

from app.settings.models import (
    parse_hhmm, is_library_open, library_hours_label, get_closing_time,
    get_open_days, is_open_day,
)

OPEN = {'LIBRARY_OPENING_TIME': '08:00', 'LIBRARY_CLOSING_TIME': '17:00'}
# _at() is a Tuesday (2026-10-06).
OPEN_DAYS = dict(OPEN, LIBRARY_OPEN_DAYS=(
    'Monday,Tuesday,Wednesday,Thursday,Friday,Saturday'))


def _at(hour, minute=0):
    """Test helper _at: build mocked data or DB stub for the test."""
    return datetime(2026, 10, 6, hour, minute)


class TestParseHhmm:
    def test_valid(self):
        """Validates valid [TestParseHhmm / library hours].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        assert parse_hhmm('08:00') == (8, 0)
        assert parse_hhmm(' 17:30 ') == (17, 30)
        assert parse_hhmm('00:00') == (0, 0)
        assert parse_hhmm('23:59') == (23, 59)

    def test_invalid(self):
        """Validates invalid [TestParseHhmm / library hours].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        for bad in (None, '', '   ', '8:00', '8:0', '24:00', '17:60',
                    'nope', '08:00:00', '08-00', '0800'):
            assert parse_hhmm(bad) is None, bad


class TestOpenCheck:
    def test_boundaries(self):
        """Validates boundaries [TestOpenCheck / library hours].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        assert is_library_open(_at(8, 0), OPEN) is True
        assert is_library_open(_at(12, 0), OPEN) is True
        assert is_library_open(_at(16, 59), OPEN) is True
        assert is_library_open(_at(17, 0), OPEN) is False
        assert is_library_open(_at(7, 59), OPEN) is False
        assert is_library_open(_at(23, 0), OPEN) is False

    def test_fail_open(self):
        """Validates fail open [TestOpenCheck / library hours].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        assert is_library_open(_at(3, 0), {}) is True
        assert is_library_open(_at(3, 0), {
            'LIBRARY_OPENING_TIME': 'junk',
            'LIBRARY_CLOSING_TIME': '17:00'}) is True
        assert is_library_open(_at(3, 0), {
            'LIBRARY_OPENING_TIME': '17:00',
            'LIBRARY_CLOSING_TIME': '08:00'}) is True

    def test_label_and_closing(self):
        """Validates label and closing [TestOpenCheck / library hours].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        assert library_hours_label(OPEN) == '08:00–17:00'
        assert library_hours_label({}) is None
        assert get_closing_time(OPEN) == (17, 0)
        assert get_closing_time({}) == (17, 0)


class TestHoursSettingsUi:
    def test_librarian_page_shows_hours(self, librarian_client, mock_db):
        """Validates librarian page shows hours `/librarian/settings` as librarian [TestHoursSettingsUi / library hours].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/settings').data.decode()
        assert 'Library Hours' in body
        assert 'LIBRARY_OPENING_TIME' in body
        assert 'LIBRARY_CLOSING_TIME' in body
        assert 'type="time"' in body

    def test_admin_page_hides_hours(self, admin_client, mock_db):
        """Validates admin page hides hours `/admin/settings` as admin [TestHoursSettingsUi / library hours].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_all'].return_value = []
        body = admin_client.get('/admin/settings').data.decode()
        assert 'LIBRARY_OPENING_TIME' not in body
        assert 'LIBRARY_CLOSING_TIME' not in body

    def test_valid_pair_writes_both(self, librarian_client, mock_db):
        """Validates valid pair writes both `/librarian/settings/update` as librarian (expects 302) [TestHoursSettingsUi / library hours].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_all'].return_value = []
        mock_db['execute'].return_value = 1
        resp = librarian_client.post('/librarian/settings/update', data={
            'LIBRARY_OPENING_TIME': '08:00',
            'LIBRARY_CLOSING_TIME': '17:00',
        })
        assert resp.status_code == 302
        keys = [c[0][1][0] for c in mock_db['execute'].call_args_list
                if 'INSERT INTO library_settings' in c[0][0]]
        assert 'LIBRARY_OPENING_TIME' in keys
        assert 'LIBRARY_CLOSING_TIME' in keys

    def test_bad_format_rejected(self, librarian_client, mock_db):
        """Validates bad format rejected `/librarian/settings/update` as librarian (expects 302) [TestHoursSettingsUi / library hours].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_all'].return_value = []
        for data in ({'LIBRARY_OPENING_TIME': '8am'},
                     {'LIBRARY_CLOSING_TIME': '25:00'},
                     {'LIBRARY_OPENING_TIME': '08:00',
                      'LIBRARY_CLOSING_TIME': '08:00'},
                     {'LIBRARY_OPENING_TIME': '18:00',
                      'LIBRARY_CLOSING_TIME': '17:00'}):
            with patch('app.settings.routes.get_settings_dict',
                       return_value={}):
                mock_db['execute'].call_args_list.clear()
                resp = librarian_client.post('/librarian/settings/update',
                                             data=data)
                assert resp.status_code == 302, data
                assert mock_db['execute'].call_count == 0, data

    def test_invalid_key_does_not_block_valid_key(
            self, librarian_client, mock_db):
        # Per-key errors like the rest of the form: the garbage opening
        # is rejected while the valid closing (coherent with stored
        # opening) is still saved.
        """Validates invalid key does not block valid key `/librarian/settings/update` as librarian (expects 302) [TestHoursSettingsUi / library hours].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_all'].return_value = []
        mock_db['execute'].return_value = 1
        resp = librarian_client.post('/librarian/settings/update', data={
            'LIBRARY_OPENING_TIME': '8am',
            'LIBRARY_CLOSING_TIME': '17:00',
        })
        assert resp.status_code == 302
        keys = [c[0][1][0] for c in mock_db['execute'].call_args_list
                if 'INSERT INTO library_settings' in c[0][0]]
        assert 'LIBRARY_OPENING_TIME' not in keys
        assert 'LIBRARY_CLOSING_TIME' in keys

    def test_single_side_uses_stored_other(self, librarian_client, mock_db):
        """Validates single side uses stored other `/librarian/settings/update` as librarian (expects 302) [TestHoursSettingsUi / library hours].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_all'].return_value = [
            ('LIBRARY_CLOSING_TIME', '17:00', '', None),
        ]
        mock_db['execute'].return_value = 1
        resp = librarian_client.post('/librarian/settings/update', data={
            'LIBRARY_OPENING_TIME': '09:00',
        })
        assert resp.status_code == 302
        keys = [c[0][1][0] for c in mock_db['execute'].call_args_list
                if 'INSERT INTO library_settings' in c[0][0]]
        assert keys == ['LIBRARY_OPENING_TIME']

    def test_admin_cannot_edit_hours(self, admin_client, mock_db):
        """Validates admin cannot edit hours `/admin/settings/update` as admin (expects 302) [TestHoursSettingsUi / library hours].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_all'].return_value = []
        resp = admin_client.post('/admin/settings/update', data={
            'LIBRARY_OPENING_TIME': '08:00',
            'LIBRARY_CLOSING_TIME': '17:00',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0


class TestBorrowGuards:
    ACC = (10, '2024-00123', 5, 1, '2024-01-10', 'purchase')
    BORROWER = (1, '2024-0001', 'CS', 'active', 'Stu', 1, 'Student')
    BOOK = (5, 'T', 'A', '', '', None, '', '', '', '', '', 'active',
            '2026-01-01', None, None)

    def test_desk_borrow_blocked_when_closed(
            self, librarian_client, mock_db):
        """Validates desk borrow blocked when closed `/librarian/circulation/borrow` as librarian (expects 302) [TestBorrowGuards / library hours].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        with patch('app.circulation.routes.is_library_open',
                   return_value=False):
            resp = librarian_client.post(
                '/librarian/circulation/borrow',
                data={'borrower_id': 1, 'accession_number': 'ACC-1',
                      'borrow_type': 'overnight'})
        assert resp.status_code == 302
        assert not any('INSERT INTO circulation_records' in c[0][0]
                       for c in mock_db['execute'].call_args_list)

    def test_user_daily_blocked_when_closed(
            self, student_client, mock_db):
        """Validates user daily blocked when closed `/user/borrow` as student (expects 302) [TestBorrowGuards / library hours].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].side_effect = [
            self.BOOK, self.BORROWER, None,
        ]
        with patch('app.circulation.routes.is_library_open',
                   return_value=False):
            resp = student_client.post('/user/borrow', data={
                'book_id': 5, 'borrow_type': 'daily_circulation'})
        assert resp.status_code == 302
        assert not any('INSERT INTO circulation_records' in c[0][0]
                       for c in mock_db['execute'].call_args_list)

    def test_overnight_request_allowed_when_closed(
            self, student_client, mock_db):
        """Validates overnight request allowed when closed `/user/borrow` as student (expects 302) [TestBorrowGuards / library hours].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].side_effect = [
            self.BOOK, self.BORROWER, None, None, (0,), (1,),
        ]
        with patch('app.circulation.routes.is_library_open',
                   return_value=False):
            resp = student_client.post('/user/borrow', data={
                'book_id': 5, 'borrow_type': 'overnight'})
        assert resp.status_code == 302
        assert any('INSERT INTO reservation_queue' in c[0][0]
                   for c in mock_db['execute'].call_args_list)

    def test_claim_blocked_when_closed(self, librarian_client, mock_db):
        """Validates claim blocked when closed `/librarian/reservations/9/claim` as librarian (expects 302) [TestBorrowGuards / library hours].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].return_value = (
            9, 5, 2, 1, '2026-08-01 10:00:00', 'allocated',
            '2026-08-03 10:00:00')
        with patch('app.circulation.routes.is_library_open',
                   return_value=False):
            resp = librarian_client.post(
                '/librarian/reservations/9/claim')
        assert resp.status_code == 302
        assert not any('INSERT INTO circulation_records' in c[0][0]
                       for c in mock_db['execute'].call_args_list)


class TestClosingDueTime:
    def test_due_uses_configured_closing(self, app):
        """Validates due uses configured closing [TestClosingDueTime / library hours].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        from app.circulation.routes import _compute_due_date
        from datetime import date
        with app.test_request_context():
            app.config['LIBRARY_CLOSING_TIME'] = '15:30'
            due = _compute_due_date('daily_circulation', 'Student')
            assert (due.hour, due.minute) == (15, 30)
            assert due.date() == date.today()

    def test_due_defaults_to_five_pm(self, app):
        """Validates due defaults to five pm [TestClosingDueTime / library hours].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        from app.circulation.routes import _compute_due_date
        from datetime import date
        with app.test_request_context():
            app.config.pop('LIBRARY_CLOSING_TIME', None)
            app.config.pop('LIBRARY_OPENING_TIME', None)
            due = _compute_due_date('daily_circulation', 'Student')
            assert (due.hour, due.minute) == (17, 0)
            assert due.date() == date.today()


class TestOpenDays:
    """Weekday open-day checkboxes: gate, settings UI, and saves."""

    def test_checked_day_allows_borrow_in_hours(self):
        """Validates checked day allows borrow in hours [TestOpenDays / library hours].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        # _at() is a Tuesday and Tuesday is checked.
        assert is_library_open(_at(12, 0), OPEN_DAYS) is True
        assert is_open_day(_at(12, 0).date(), OPEN_DAYS) is True

    def test_unchecked_day_blocks_borrow(self):
        """Validates unchecked day blocks borrow [TestOpenDays / library hours].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        cfg = dict(OPEN, LIBRARY_OPEN_DAYS='Monday,Wednesday')
        assert is_library_open(_at(12, 0), cfg) is False
        assert is_open_day(_at(12, 0).date(), cfg) is False

    def test_unconfigured_days_fail_open(self):
        """Validates unconfigured days fail open [TestOpenDays / library hours].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        assert get_open_days({}) is None
        assert get_open_days(OPEN) is None
        assert is_open_day(_at(12, 0).date(), {}) is True
        # Hours-only config keeps the historical behavior (gate on time).
        assert is_library_open(_at(12, 0), OPEN) is True

    def test_empty_means_closed_all_week(self):
        """Validates empty means closed all week [TestOpenDays / library hours].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        cfg = dict(OPEN, LIBRARY_OPEN_DAYS='')
        assert get_open_days(cfg) == set()
        assert is_library_open(_at(12, 0), cfg) is False

    def test_unknown_day_tokens_dropped(self):
        """Validates unknown day tokens dropped [TestOpenDays / library hours].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        cfg = dict(OPEN, LIBRARY_OPEN_DAYS='Tuesday,Funday')
        assert get_open_days(cfg) == {'Tuesday'}
        assert is_library_open(_at(12, 0), cfg) is True

    def test_librarian_page_shows_day_checkboxes(
            self, librarian_client, mock_db):
        """Validates librarian page shows day checkboxes `/librarian/settings` as librarian [TestOpenDays / library hours].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/settings').data.decode()
        assert 'LIBRARY_OPEN_DAYS' in body
        for day in ('Monday', 'Tuesday', 'Wednesday', 'Thursday',
                    'Friday', 'Saturday', 'Sunday'):
            assert f'value="{day}"' in body, day
        assert 'type="checkbox"' in body

    def test_admin_page_hides_open_days(self, admin_client, mock_db):
        """Validates admin page hides open days `/admin/settings` as admin [TestOpenDays / library hours].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_all'].return_value = []
        body = admin_client.get('/admin/settings').data.decode()
        assert 'LIBRARY_OPEN_DAYS' not in body

    def test_valid_days_stored_canonical(
            self, librarian_client, mock_db):
        """Validates valid days stored canonical `/librarian/settings/update` as librarian (expects 302) [TestOpenDays / library hours].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_all'].return_value = []
        mock_db['execute'].return_value = 1
        resp = librarian_client.post('/librarian/settings/update', data={
            'LIBRARY_OPEN_DAYS': ['Sunday', 'Monday'],
        })
        assert resp.status_code == 302
        writes = [c[0][1] for c in mock_db['execute'].call_args_list
                  if 'INSERT INTO library_settings' in c[0][0]]
        assert any(w[0] == 'LIBRARY_OPEN_DAYS' and w[1] == 'Monday,Sunday'
                   for w in writes)

    def test_unknown_day_rejected(self, librarian_client, mock_db):
        """Validates unknown day rejected `/librarian/settings/update` as librarian (expects 302) [TestOpenDays / library hours].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.post('/librarian/settings/update', data={
            'LIBRARY_OPEN_DAYS': 'Funday',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_all_unchecked_stores_empty(self, librarian_client, mock_db):
        """Validates all unchecked stores empty `/librarian/settings/update` as librarian (expects 302) [TestOpenDays / library hours].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_all'].return_value = []
        mock_db['execute'].return_value = 1
        # Only the hidden '' fallback submits: every day unchecked.
        resp = librarian_client.post('/librarian/settings/update', data={
            'LIBRARY_OPEN_DAYS': '',
        })
        assert resp.status_code == 302
        writes = [c[0][1] for c in mock_db['execute'].call_args_list
                  if 'INSERT INTO library_settings' in c[0][0]]
        assert any(w[0] == 'LIBRARY_OPEN_DAYS' and w[1] == ''
                   for w in writes)


class TestMonthDays:
    """Per-date month overrides: precedence, real-calendar grid, saves."""

    def test_override_closes_open_weekday(self):
        """Validates override closes open weekday [TestMonthDays / library hours].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        from datetime import date
        # Tuesday 2026-10-06 is weekly-open but explicitly closed.
        bits = '1' * 5 + '0' + '1' * 25
        cfg = {'LIBRARY_OPENING_TIME': '08:00',
               'LIBRARY_CLOSING_TIME': '17:00',
               'LIBRARY_OPEN_DAYS': OPEN_DAYS['LIBRARY_OPEN_DAYS'],
               'LIBRARY_MONTH_DAYS': f'2026-10:{bits}'}
        assert is_open_day(date(2026, 10, 6), cfg) is False
        assert is_open_day(date(2026, 10, 7), cfg) is True
        assert is_library_open(datetime(2026, 10, 6, 12, 0), cfg) is False

    def test_override_opens_closed_weekday(self):
        """Validates override opens closed weekday [TestMonthDays / library hours].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        from datetime import date
        # Sunday 2026-10-04 is weekly-closed but explicitly opened.
        bits = '0' * 3 + '1' + '0' * 27
        cfg = {'LIBRARY_OPEN_DAYS': 'Monday,Tuesday,Wednesday,Thursday,Friday',
               'LIBRARY_MONTH_DAYS': f'2026-10:{bits}'}
        assert is_open_day(date(2026, 10, 4), cfg) is True
        assert is_open_day(date(2026, 10, 11), cfg) is False

    def test_stale_month_ignored(self):
        """Validates stale month ignored [TestMonthDays / library hours].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        from datetime import date
        cfg = {'LIBRARY_OPEN_DAYS': OPEN_DAYS['LIBRARY_OPEN_DAYS'],
               'LIBRARY_MONTH_DAYS': '2026-09:' + '0' * 30}
        # September map must not close October dates.
        assert is_open_day(date(2026, 10, 6), cfg) is True

    def test_malformed_map_ignored(self):
        """Validates malformed map ignored [TestMonthDays / library hours].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        from datetime import date
        for bad in ('2026-10:111', '2026-13:' + '1' * 31, 'nope',
                    '2026-10:' + '1' * 30):
            cfg = {'LIBRARY_OPEN_DAYS': OPEN_DAYS['LIBRARY_OPEN_DAYS'],
                   'LIBRARY_MONTH_DAYS': bad}
            assert is_open_day(date(2026, 10, 6), cfg) is True, bad

    def test_month_grid_uses_real_calendar(self):
        """Validates month grid uses real calendar [TestMonthDays / library hours].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        from app.settings.models import month_grid
        october = month_grid(2026, 10, {})
        assert len(october) == 31
        assert october[0]['iso'] == '2026-10-01'
        assert october[0]['weekday'] == 'Thu'
        assert october[-1]['iso'] == '2026-10-31'
        assert october[-1]['weekday'] == 'Sat'
        assert len(month_grid(2026, 2, {})) == 28
        assert len(month_grid(2024, 2, {})) == 29

    def test_librarian_page_shows_month_grid(
            self, librarian_client, mock_db):
        """Validates librarian page shows month grid `/librarian/settings` as librarian [TestMonthDays / library hours].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        from datetime import datetime, timedelta, timezone
        from calendar import monthrange
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/settings').data.decode()
        assert 'Open Days In Week' in body
        assert 'Open Days In Month (' in body
        assert 'LIBRARY_MONTH_DAYS' in body
        assert 'name="open_month"' in body
        manila = datetime.now(timezone(timedelta(hours=8)))
        expected = monthrange(manila.year, manila.month)[1]
        # One checkbox per real calendar date plus the hidden fallback.
        assert body.count('name="LIBRARY_MONTH_DAYS"') == expected + 1

    def test_admin_page_hides_month_grid(self, admin_client, mock_db):
        """Validates admin page hides month grid `/admin/settings` as admin [TestMonthDays / library hours].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_all'].return_value = []
        body = admin_client.get('/admin/settings').data.decode()
        assert 'LIBRARY_MONTH_DAYS' not in body
        assert 'Open Days In Month' not in body

    def test_week_toggle_wired_to_month_grid(
            self, librarian_client, mock_db):
        """Validates week toggle wired to month grid `/librarian/settings` as librarian [TestMonthDays / library hours].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/settings').data.decode()
        # Weekly boxes drive the month grid live (no save needed).
        assert 'onchange="syncMonthToWeek(this)"' in body
        assert 'function syncMonthToWeek' in body

    def test_month_toggle_never_drives_week(
            self, librarian_client, mock_db):
        """Validates month toggle never drives week `/librarian/settings` as librarian [TestMonthDays / library hours].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        import re
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/settings').data.decode()
        # One sync hook per weekly box (7), none anywhere else.
        assert body.count('onchange="syncMonthToWeek(this)"') == 7
        # Rendered month-date inputs carry no change handler of any kind.
        month_tags = re.findall(
            r'<input[^>]*value="\d{4}-\d{2}-\d{2}"[^>]*>', body)
        assert month_tags, 'month grid inputs missing'
        for tag in month_tags:
            assert 'onchange' not in tag and 'oninput' not in tag, tag
        # The sync writer is scoped to the month grid container, so it
        # can never alter the weekly boxes outside of it.
        assert "'#month-day-grid input[type=\"checkbox\"]'" in body

    def test_valid_month_days_stored(self, librarian_client, mock_db):
        """Validates valid month days stored `/librarian/settings/update` as librarian (expects 302) [TestMonthDays / library hours].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_all'].return_value = []
        mock_db['execute'].return_value = 1
        resp = librarian_client.post('/librarian/settings/update', data={
            'LIBRARY_MONTH_DAYS': ['2026-10-01', '2026-10-31'],
        })
        assert resp.status_code == 302
        writes = [c[0][1] for c in mock_db['execute'].call_args_list
                  if 'INSERT INTO library_settings' in c[0][0]]
        assert any(w[0] == 'LIBRARY_MONTH_DAYS'
                   and w[1] == '2026-10:' + '1' + '0' * 29 + '1'
                   for w in writes)

    def test_mixed_months_rejected(self, librarian_client, mock_db):
        """Validates mixed months rejected `/librarian/settings/update` as librarian (expects 302) [TestMonthDays / library hours].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.post('/librarian/settings/update', data={
            'LIBRARY_MONTH_DAYS': ['2026-10-01', '2026-11-01'],
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_impossible_day_rejected(self, librarian_client, mock_db):
        """Validates impossible day rejected `/librarian/settings/update` as librarian (expects 302) [TestMonthDays / library hours].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_all'].return_value = []
        # February 2026 has 28 days — the 29th cannot exist.
        resp = librarian_client.post('/librarian/settings/update', data={
            'LIBRARY_MONTH_DAYS': ['2026-02-29'],
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_all_unchecked_month_stores_closed(
            self, librarian_client, mock_db):
        """Validates all unchecked month stores closed `/librarian/settings/update` as librarian (expects 302) [TestMonthDays / library hours].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_all'].return_value = []
        mock_db['execute'].return_value = 1
        resp = librarian_client.post('/librarian/settings/update', data={
            'LIBRARY_MONTH_DAYS': '',
            'open_month': '2026-10',
        })
        assert resp.status_code == 302
        writes = [c[0][1] for c in mock_db['execute'].call_args_list
                  if 'INSERT INTO library_settings' in c[0][0]]
        assert any(w[0] == 'LIBRARY_MONTH_DAYS'
                   and w[1] == '2026-10:' + '0' * 31
                   for w in writes)

    def test_unchecked_without_month_rejected(
            self, librarian_client, mock_db):
        """Validates unchecked without month rejected `/librarian/settings/update` as librarian (expects 302) [TestMonthDays / library hours].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.post('/librarian/settings/update', data={
            'LIBRARY_MONTH_DAYS': '',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0


class TestOperationsCleanup:
    """Operations holds only open-days fields; closures follow them."""

    def test_operations_shows_only_open_days(
            self, librarian_client, mock_db):
        """Validates operations shows only open days `/librarian/settings` as librarian [TestOperationsCleanup / library hours].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/settings').data.decode()
        assert 'Library Operations Schedule' in body
        assert 'LIBRARY_OPEN_DAYS' in body
        assert 'LIBRARY_MONTH_DAYS' in body
        for gone in ('LIBRARY_SATURDAY_OPENING_TIME',
                     'LIBRARY_SATURDAY_CLOSING_TIME',
                     'LIBRARY_SEMBREAK_OPENING_TIME',
                     'LIBRARY_SEMBREAK_CLOSING_TIME',
                     'LIBRARY_CLOSED_DAYS'):
            assert gone not in body, gone

    def test_closed_day_follows_open_days(self):
        """Validates closed day follows open days [TestOperationsCleanup / library hours].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates library hours is broken for this case (users see wrong page, blocked action, or bad data)."""
        from datetime import date
        from app.settings.models import is_closed_day, get_closed_days
        cfg = {'LIBRARY_OPEN_DAYS': OPEN_DAYS['LIBRARY_OPEN_DAYS']}
        # Sunday unchecked -> closed (keeps the old Sunday reservation block).
        assert is_closed_day(date(2026, 10, 4), cfg) is True
        assert is_closed_day(date(2026, 10, 6), cfg) is False
        assert get_closed_days(cfg) == {'sunday'}
        # Per-date override closing a Monday counts as closed too.
        bits = '1' * 5 + '0' + '1' * 25
        cfg2 = dict(cfg, LIBRARY_MONTH_DAYS=f'2026-10:{bits}')
        assert is_closed_day(date(2026, 10, 6), cfg2) is True
        # Unconfigured days fail open, as before.
        assert is_closed_day(date(2026, 10, 4), {}) is False
        assert get_closed_days({}) == set()
