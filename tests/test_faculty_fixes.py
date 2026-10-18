"""Regression tests for the faculty edge-case fixes (F1-F8).

Each test pins the fixed behavior with mocked DB returns — no Postgres.
"""

from unittest.mock import patch


BOOK_ACTIVE = (5, 'Intro to Algorithms', 'Cormen', '', '', None, '', '',
               '', '', '', 'active', '2026-01-01', None, None)
BOOK_ARCHIVED = (5, 'Intro to Algorithms', 'Cormen', '', '', None, '', '',
                 '', '', '', 'archived', '2026-01-01', None, None)
BORROWER_ACTIVE = (1, 1, '2024-0001', 'CS', '0917', 'active', None, None)
BORROWER_BLOCKED = (5, 'S1', 'BSIS', 'blocked', 'Ann', 1, 'Student')
ACC = (10, '2024-00123', 5, 1, '2024-01-10', 'purchase')


class TestNotifyResilience:
    """F1: a failing notification must not turn a good write into a 500."""

    def test_user_borrow_ok_when_notify_fails(self, student_client, mock_db):
        """Validates user borrow ok when notify fails `/user/borrow` as student (expects 302) [TestNotifyResilience / faculty fixes].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates faculty fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].side_effect = [
            BOOK_ACTIVE,
            BORROWER_ACTIVE,
            None,   # no active loan
            ACC,    # available copy
            (0,),   # count
            None,   # no active reservation (F7 guard)
        ]
        with patch('app.circulation.routes.create_notification',
                   side_effect=Exception('notif down')):
            resp = student_client.post('/user/borrow', data={
                'book_id': 5, 'borrow_type': 'daily_circulation'})
        assert resp.status_code == 302

    def test_user_return_is_desk_only(self, student_client, mock_db):
        # Desk-only returns: self-service check-in writes nothing, even
        # for a valid daily loan with notifications down.
        """Validates user return is desk only `/user/return` as student (expects 302) [TestNotifyResilience / faculty fixes].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates faculty fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        from datetime import date
        mock_db['fetch_one'].side_effect = [
            (55, 10, 1, '2026-08-02', 'active', 'daily_circulation'),
            (date(2026, 8, 1), date(2026, 8, 2), 'daily_circulation'),
            None,
        ]
        with patch('app.circulation.routes.create_notification',
                   side_effect=Exception('notif down')):
            resp = student_client.post('/user/return',
                                       data={'circulation_id': 55})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_user_reserve_ok_when_notify_fails(self, student_client, mock_db):
        """Validates user reserve ok when notify fails `/user/reserve` as student (expects 302) [TestNotifyResilience / faculty fixes].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates faculty fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].side_effect = [
            BOOK_ACTIVE,
            BORROWER_ACTIVE,
            None,   # no existing reservation
            None,   # no active loan
            None,   # no available copy
            (1,),   # queue position
        ]
        with patch('app.circulation.routes.create_notification',
                   side_effect=Exception('notif down')):
            resp = student_client.post('/user/reserve', data={'book_id': 5})
        assert resp.status_code == 302


class TestUniqueViolationRetry:
    """F2: a lost race surfaces as a friendly retry, not a 500."""

    def test_daily_borrow_conflict_is_retry(self, student_client, mock_db):
        """Validates daily borrow conflict is retry `/user/borrow` as student (expects 302) [TestUniqueViolationRetry / faculty fixes].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates faculty fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        from psycopg2 import errors as pg_errors
        mock_db['fetch_one'].side_effect = [
            BOOK_ACTIVE,
            BORROWER_ACTIVE,
            None,
            ACC,
            (0,),
            None,
        ]
        mock_db['execute'].side_effect = pg_errors.UniqueViolation('duplicate')
        resp = student_client.post('/user/borrow', data={
            'book_id': 5, 'borrow_type': 'daily_circulation'})
        assert resp.status_code == 302


class TestDailyReservationGuard:
    """F7: daily borrow is blocked by a pending reservation for same title."""

    def test_daily_blocked_by_pending_reservation(
            self, faculty_client, mock_db):
        """Validates daily blocked by pending reservation `/user/borrow` as faculty (expects 302) [TestDailyReservationGuard / faculty fixes].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates faculty fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].side_effect = [
            BOOK_ACTIVE,
            (2, 2, '2024-0002', 'CS', 'active'),
            None,   # no active loan
            ACC,    # available copy
            (0,),   # under limit
            (9, 5, 2, 1, '2026-08-01 10:00:00', 'waiting', None),
        ]
        resp = faculty_client.post('/user/borrow', data={
            'book_id': 5, 'borrow_type': 'daily_circulation'})
        assert resp.status_code == 302
        writes = [c[0][0] for c in mock_db['execute'].call_args_list
                  if 'INSERT INTO circulation_records' in c[0][0]]
        assert writes == []


class TestAllocateClaimGuards:
    """F6/F8: allocate/claim refuse inactive borrowers and archived books."""

    def test_allocate_blocked_inactive_borrower(
            self, librarian_client, mock_db):
        """Validates allocate blocked inactive borrower `/librarian/reservations/9/allocate` as librarian (expects 302) [TestAllocateClaimGuards / faculty fixes].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates faculty fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].side_effect = [
            (9, 5, 2, 1, '2026-08-01 10:00:00', 'waiting', None),
            ACC,
            None,  # book lookup (active)
            (5, 'S1', 'BSIS', 'blocked', 'Ann', 1, 'Student'),
        ]
        resp = librarian_client.post('/librarian/reservations/9/allocate')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 1  # sweep only

    def test_allocate_blocked_archived_book(
            self, librarian_client, mock_db):
        """Validates allocate blocked archived book `/librarian/reservations/9/allocate` as librarian (expects 302) [TestAllocateClaimGuards / faculty fixes].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates faculty fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].side_effect = [
            (9, 5, 2, 1, '2026-08-01 10:00:00', 'waiting', None),
            ACC,
            BOOK_ARCHIVED,
        ]
        resp = librarian_client.post('/librarian/reservations/9/allocate')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 1  # sweep only

    def test_claim_blocked_inactive_borrower(
            self, librarian_client, mock_db):
        """Validates claim blocked inactive borrower `/librarian/reservations/9/claim` as librarian (expects 302) [TestAllocateClaimGuards / faculty fixes].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates faculty fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].side_effect = [
            (9, 5, 2, 1, '2026-08-01 10:00:00', 'allocated',
             '2026-08-03 10:00:00'),
            ACC,
            None,  # book lookup (active)
            (3,),  # floor check passes
            (5, 'S1', 'BSIS', 'blocked', 'Ann', 1, 'Student'),
        ]
        resp = librarian_client.post('/librarian/reservations/9/claim')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 1  # sweep only


class TestProfileValidation:
    """F5: overlong names/departments are rejected before touching the DB."""

    def test_overlong_name_rejected(self, student_client, mock_db):
        """Validates overlong name rejected `/user/profile/update` as student (expects 302) [TestProfileValidation / faculty fixes].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (UPDATE).
    Failure indicates faculty fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].return_value = (
            1, 'e@x.ph', 'Student', 'Old', 5, 'S1', 'BSIS')
        resp = student_client.post('/user/profile/update',
                                   data={'full_name': 'A' * 151})
        assert resp.status_code == 302
        writes = [c[0][0] for c in mock_db['execute'].call_args_list
                  if 'UPDATE user_accounts' in c[0][0]]
        assert writes == []

    def test_failed_update_is_graceful(self, student_client, mock_db):
        """Validates failed update is graceful `/user/profile/update` as student (expects 302) [TestProfileValidation / faculty fixes].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates faculty fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        profile = (1, 'e@x.ph', 'Student', 'Old', 5, 'S1', 'BSIS')
        mock_db['fetch_one'].side_effect = [profile, profile]
        mock_db['execute'].side_effect = [
            1, Exception('borrowers down'), 1]
        resp = student_client.post('/user/profile/update',
                                   data={'full_name': 'New Name'})
        assert resp.status_code == 302


class TestFacultySignupAtomicity:
    """F3: borrower-insert failure leaves no orphan pending user."""

    def test_faculty_borrower_failure_cleans_up(self, client, mock_db):
        """Validates faculty borrower failure cleans up `/login/role-select` (expects 200) [TestFacultySignupAtomicity / faculty fixes].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (DELETE FROM).
    Failure indicates faculty fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        with client.session_transaction() as sess:
            sess['_google_oauth_data'] = {
                'email': 'faculty@mcst.edu.ph',
                'oauth_sub': 'sub-789',
                'full_name': 'Faculty User',
            }
        mock_db['fetch_one'].side_effect = lambda q, p=None: (
            (2, 'Faculty') if p and p and p[0] == 'Faculty'
            else (1,) if 'FROM departments' in q
            else (7,) if 'RETURNING user_id' in q
            else None)
        with patch('app.auth.routes.create_borrower',
                   side_effect=Exception('db down')), \
             patch('app.auth.routes.get_admin_count', return_value=1):
            resp = client.post('/login/role-select', data={
                'role': 'Faculty',
                'id_number': '100012345',
                'department': 'CS Department',
            })
        assert resp.status_code == 200
        stmts = [c[0][0] for c in mock_db['execute'].call_args_list]
        assert any('DELETE FROM user_accounts' in s for s in stmts)
