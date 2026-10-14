"""Regression tests for the concurrency fixes: queue-position retry,
allocate over-booking guard, claim compensation, and user daily
queue-jump parity. All DB access is mocked (see conftest.py)."""

import pytest
from psycopg2 import errors as pg_errors

BOOK = (5, 'Intro to Algorithms', 'Cormen')
BORROWER = (1, 1, '2024-0001', 'CS', 'active')
DETAIL = (2, '2024-0002', 'CS', 'active', 'Test Student', 1, 'Student')
ACC = (10, '2024-00123', 5, 1, '2024-01-10', 'purchase')


def _flashes(client):
    """Test helper _flashes: build mocked data or DB stub for the test."""
    with client.session_transaction() as sess:
        return [msg for _cat, msg in sess.get('_flashes', [])]


class TestQueuePositionRetry:
    def test_collision_retries_then_succeeds(self, student_client, mock_db):
        """Validates collision retries then succeeds `/user/reserve` as student (expects 302) [TestQueuePositionRetry / concurrency fixes].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates concurrency fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].side_effect = [
            BOOK,
            BORROWER,
            None,    # no existing reservation (pre-check)
            None,    # no active loan
            None,    # no available copy -> queue
            (1,),    # first position attempt
            None,    # dup re-check after collision: no dup -> retry
            (2,),    # fresh position
        ]

        def _exec(q, p=None):
            """Test helper _exec: build mocked data or DB stub for the test."""
            if 'INSERT INTO reservation_queue' in q:
                if _exec.calls == 0:
                    _exec.calls += 1
                    raise pg_errors.UniqueViolation('duplicate queue position')
                return 1
            return []

        _exec.calls = 0
        mock_db['execute'].side_effect = _exec
        resp = student_client.post('/user/reserve', data={'book_id': 5})
        assert resp.status_code == 302
        inserts = [c for c in mock_db['execute'].call_args_list
                   if 'INSERT INTO reservation_queue' in c[0][0]]
        assert len(inserts) == 2
        assert inserts[0][0][1] == (5, 1, 1)
        assert inserts[1][0][1] == (5, 1, 2)

    def test_duplicate_reservation_is_friendly_block(self, student_client, mock_db):
        """Validates duplicate reservation is friendly block `/user/reserve` as student (expects 302) [TestQueuePositionRetry / concurrency fixes].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates concurrency fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        existing = (9, 5, 1, 1, '2026-08-01 10:00:00', 'waiting', None)
        mock_db['fetch_one'].side_effect = [
            BOOK,
            BORROWER,
            None,    # pre-check passes (race: created concurrently)
            None,    # no active loan
            None,    # no available copy
            (1,),    # position attempt
            existing,  # dup re-check: already reserved -> sentinel
        ]
        mock_db['execute'].side_effect = pg_errors.UniqueViolation('dup reservation')
        resp = student_client.post('/user/reserve', data={'book_id': 5})
        assert resp.status_code == 302
        inserts = [c for c in mock_db['execute'].call_args_list
                   if 'INSERT INTO reservation_queue' in c[0][0]]
        assert len(inserts) == 1
        assert any('already have' in msg for msg in _flashes(student_client))


class TestAllocateOverbooking:
    def test_overbooking_refused(self, librarian_client, mock_db):
        """Validates overbooking refused `/librarian/reservations/9/allocate` as librarian (expects 302) [TestAllocateOverbooking / concurrency fixes].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates concurrency fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].side_effect = [
            (9, 5, 2, 1, '2026-08-01 10:00:00', 'waiting', None),  # reservation
            ACC,                                                   # available copy
            None,                                                  # book lookup (active)
            DETAIL,                                                # borrower active
            None,                                                  # no active loan
            (0,),                                                  # under limit
            (1,),                                                  # 1 allocated ...
            (1,),                                                  # ... vs 1 available copy
        ]
        resp = librarian_client.post('/librarian/reservations/9/allocate')
        assert resp.status_code == 302
        allocates = [c for c in mock_db['execute'].call_args_list
                     if "SET reservation_status = 'allocated'" in c[0][0]]
        assert allocates == []
        assert any('no unallocated copy' in msg
                   for msg in _flashes(librarian_client))

    def test_count_available_accessions_sql(self, mock_db):
        """Validates count available accessions sql [TestAllocateOverbooking / concurrency fixes].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates concurrency fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        from app.circulation.models import count_available_accessions
        mock_db['fetch_one'].return_value = (2,)
        assert count_available_accessions(5) == 2
        query, params = mock_db['fetch_one'].call_args[0]
        assert 'COUNT(*)' in query
        assert 'accession_log' in query
        assert 'lost_flag' in query
        assert params == (5,)


class TestClaimCompensation:
    def test_failed_claim_returns_orphan_loan(self, librarian_client, mock_db):
        """Validates failed claim returns orphan loan `/librarian/reservations/9/claim` as librarian [TestClaimCompensation / concurrency fixes].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (UPDATE).
    Failure indicates concurrency fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        orphan = (77, 5, 10, 2, 1, 'overnight', 'borrow', '2026-08-01',
                  '2026-08-03', None, 0, None, False, 'active')
        mock_db['fetch_one'].side_effect = [
            (9, 5, 2, 1, '2026-08-01 10:00:00', 'allocated',
             '2026-08-03 10:00:00'),  # reservation
            ACC,                       # available copy
            None,                      # book lookup (active)
            DETAIL,                    # borrower active
            None,                      # no active loan
            (0,),                      # under limit
            orphan,                    # compensation lookup finds the orphan
        ]

        def _exec(q, p=None):
            """Test helper _exec: build mocked data or DB stub for the test."""
            if "reservation_status = 'claimed'" in q:
                raise RuntimeError('claim down')
            return 1

        mock_db['execute'].side_effect = _exec
        with pytest.raises(RuntimeError):
            librarian_client.post('/librarian/reservations/9/claim')
        compensations = [
            c for c in mock_db['execute'].call_args_list
            if 'UPDATE circulation_records' in c[0][0]
            and 'returned' in c[0][1]
        ]
        assert compensations


class TestUserDailyQueueParity:
    def _daily_mocks(self, mock_db, queue_row):
        """Test helper _daily_mocks: build mocked data or DB stub for the test."""
        mock_db['fetch_one'].side_effect = [
            BOOK,
            BORROWER,
            None,    # no active loan
            ACC,     # available copy
            (0,),    # under limit
            None,    # F7: no pending reservation of my own
            queue_row,
        ]

    def test_daily_blocked_by_others_queue(self, student_client, mock_db):
        """Validates daily blocked by others queue `/user/borrow` as student (expects 302) [TestUserDailyQueueParity / concurrency fixes].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates concurrency fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        other = (7, 5, 99, 1, '2026-08-01 10:00:00', 'waiting', None)
        self._daily_mocks(mock_db, other)
        resp = student_client.post('/user/borrow', data={
            'book_id': 5, 'borrow_type': 'daily_circulation'})
        assert resp.status_code == 302
        loans = [c for c in mock_db['execute'].call_args_list
                 if 'INSERT INTO circulation_records' in c[0][0]]
        assert loans == []
        assert any('waiting reservation queue' in msg
                   for msg in _flashes(student_client))

    def test_daily_allowed_when_first_waiter_is_self(self, student_client, mock_db):
        """Validates daily allowed when first waiter is self `/user/borrow` as student (expects 302) [TestUserDailyQueueParity / concurrency fixes].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates concurrency fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        mine = (7, 5, 1, 1, '2026-08-01 10:00:00', 'waiting', None)
        self._daily_mocks(mock_db, mine)
        resp = student_client.post('/user/borrow', data={
            'book_id': 5, 'borrow_type': 'daily_circulation'})
        assert resp.status_code == 302
        loans = [c for c in mock_db['execute'].call_args_list
                 if 'INSERT INTO circulation_records' in c[0][0]]
        assert len(loans) == 1


class TestSchemaRaceNets:
    def test_partial_unique_indexes_present(self):
        """Validates partial unique indexes present [TestSchemaRaceNets / concurrency fixes].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates concurrency fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        import pathlib
        schema = pathlib.Path('app/schema.sql').read_text()
        assert 'uq_active_queue_pos' in schema
        assert 'uq_pending_req' in schema
        assert 'IF NOT EXISTS' in schema
