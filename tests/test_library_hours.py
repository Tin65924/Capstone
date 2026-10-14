"""Library opening/closing hours: settings UI + validation, borrow
guards, and closing-time dues. Mocked DB — no Postgres.
"""

from datetime import datetime
from unittest.mock import patch

from app.settings.models import (
    parse_hhmm, is_library_open, library_hours_label, get_closing_time,
)

OPEN = {'LIBRARY_OPENING_TIME': '08:00', 'LIBRARY_CLOSING_TIME': '17:00'}


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
