"""Edge-case regression tests for Reservation Management.

Covers `/librarian/reservations` and all review actions
(allocate/claim/expire): empty database, `None`/short model returns,
hostile status filters and action names, missing/short reservations,
full allocate/claim state guards, XSS rows, string dates, and the
staff auth matrix. Everything must degrade gracefully — never 500.
"""

GROUP = (1, 'Clean Code', 'R. Martin', 3, 2, 1, 0, 0)
RES = (7, 1, 'waiting', '2026-01-05', None, 'Clean Code', 'Ann', 2, 'S1')
RES_ALLOC = (7, 1, 'allocated', '2026-01-05', '2026-01-06', 'Clean Code',
             'Ann', 2, 'S1')
DETAIL = (5, 'S1', 'BSIS', 'active', 'Ann', 1, 'Student')
ACC = (10, 'ACC-001', 1)


class TestEmptyDb:
    @staticmethod
    def _empty(mock_db):
        """Test helper _empty: build mocked data or DB stub for the test."""
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        mock_db['execute'].return_value = []

    def test_page_empty(self, librarian_client, mock_db):
        """Validates page empty `/librarian/reservations` as librarian (expects 200) [TestEmptyDb / reservations edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        self._empty(mock_db)
        assert librarian_client.get('/librarian/reservations').status_code == 200

    def test_none_groups(self, librarian_client, mock_db):
        """Validates none groups `/librarian/reservations` as librarian (expects 200) [TestEmptyDb / reservations edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = None
        assert librarian_client.get('/librarian/reservations').status_code == 200


class TestHostileParams:
    @staticmethod
    def _ok(mock_db):
        """Test helper _ok: build mocked data or DB stub for the test."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []

    def test_status_filters(self, librarian_client, mock_db):
        """Validates status filters as librarian (expects 200) [TestHostileParams / reservations edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        self._ok(mock_db)
        for url in ('/librarian/reservations?status=bogus',
                    '/librarian/reservations?status=history',
                    '/librarian/reservations?status=all',
                    '/librarian/reservations?status=waiting',
                    '/librarian/reservations?status=ALLOCATED'):
            assert librarian_client.get(url).status_code == 200, url

    def test_action_variants(self, librarian_client, mock_db):
        """Validates action variants as librarian (expects 302) [TestHostileParams / reservations edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        for url in ('/librarian/reservations/999999/approve',
                    '/librarian/reservations/999999/drop_table',
                    '/librarian/reservations/999999999/claim'):
            assert librarian_client.post(url).status_code == 302, url

    def test_short_reservation_row(self, librarian_client, mock_db):
        """Validates short reservation row `/librarian/reservations/7/claim` as librarian (expects 302) [TestHostileParams / reservations edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].return_value = (7, 1)
        assert librarian_client.post(
            '/librarian/reservations/7/claim').status_code == 302

    def test_short_group_rows(self, librarian_client, mock_db):
        """Validates short group rows `/librarian/reservations` as librarian (expects 200) [TestHostileParams / reservations edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].side_effect = [[(1, 'T')], []]
        assert librarian_client.get('/librarian/reservations').status_code == 200


class TestActions:
    def test_allocate_success(self, librarian_client, mock_db):
        """Validates allocate success `/librarian/reservations/7/allocate` as librarian (expects 302) [TestActions / reservations edge cases].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (7, 1, 5, 1, None, 'waiting', None, None), ACC, None, DETAIL,
            None, (0,), (0,), (2,), (7, 1, 5, 1, None, 'waiting', None, None)]
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.post('/librarian/reservations/7/allocate')
        assert resp.status_code == 302
        stmts = [c[0][0] for c in mock_db['execute'].call_args_list]
        assert any('reservation' in s.lower() for s in stmts)

    def test_allocate_not_waiting(self, librarian_client, mock_db):
        """Validates allocate not waiting `/librarian/reservations/7/allocate` as librarian (expects 302) [TestActions / reservations edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].return_value = (7, 1, 5, 1, None, 'allocated',
                                             None, None)
        assert librarian_client.post(
            '/librarian/reservations/7/allocate').status_code == 302

    def test_allocate_no_copies(self, librarian_client, mock_db):
        """Validates allocate no copies `/librarian/reservations/7/allocate` as librarian (expects 302) [TestActions / reservations edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (7, 1, 5, 1, None, 'waiting', None, None), None]
        assert librarian_client.post(
            '/librarian/reservations/7/allocate').status_code == 302

    def test_claim_success(self, librarian_client, mock_db):
        """Validates claim success `/librarian/reservations/7/claim` as librarian (expects 302) [TestActions / reservations edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (7, 1, 5, 1, None, 'allocated', None, None), ACC, None, DETAIL,
            None, (0,)]
        mock_db['fetch_all'].return_value = []
        assert librarian_client.post(
            '/librarian/reservations/7/claim').status_code == 302

    def test_claim_not_allocated(self, librarian_client, mock_db):
        """Validates claim not allocated `/librarian/reservations/7/claim` as librarian (expects 302) [TestActions / reservations edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].return_value = (7, 1, 5, 1, None, 'waiting',
                                             None, None)
        assert librarian_client.post(
            '/librarian/reservations/7/claim').status_code == 302

    def test_expire_finished(self, librarian_client, mock_db):
        """Validates expire finished `/librarian/reservations/7/expire` as librarian (expects 302) [TestActions / reservations edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].return_value = (7, 1, 5, 1, None, 'claimed',
                                             None, None)
        assert librarian_client.post(
            '/librarian/reservations/7/expire').status_code == 302

    def test_expire_waiting(self, librarian_client, mock_db):
        """Validates expire waiting `/librarian/reservations/7/expire` as librarian (expects 302) [TestActions / reservations edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].return_value = (7, 1, 5, 1, None, 'waiting',
                                             None, None)
        assert librarian_client.post(
            '/librarian/reservations/7/expire').status_code == 302


class TestXss:
    def test_evil_rows(self, librarian_client, mock_db):
        """Validates evil rows `/librarian/reservations` as librarian [TestXss / reservations edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        evil = '<script>alert(1)</script>'
        group = (1, evil, evil, 1, 1, 0, 0, 0)
        res = (7, 1, 'waiting', '2026-01-05', None, evil, evil, 2, evil)
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].side_effect = [[group], [res]]
        body = librarian_client.get('/librarian/reservations').data.decode()
        assert evil not in body

    def test_string_dates(self, librarian_client, mock_db):
        """Validates string dates `/librarian/reservations` as librarian (expects 200) [TestXss / reservations edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].return_value = (0,)
        res = (7, 1, 'waiting', '2026-01-05', None, 'T', 'Ann', 2, 'S1')
        mock_db['fetch_all'].side_effect = [[GROUP], [res]]
        assert librarian_client.get('/librarian/reservations').status_code == 200


class TestAuth:
    def test_anon(self, client):
        """Validates anon `/librarian/reservations` (expects 302) [TestAuth / reservations edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        assert client.get('/librarian/reservations').status_code == 302
        assert client.post('/librarian/reservations/1/claim').status_code == 302

    def test_student_blocked(self, student_client, mock_db):
        """Validates student blocked `/librarian/reservations` as student (expects 302) [TestAuth / reservations edge cases].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        assert student_client.get('/librarian/reservations').status_code == 302
        resp = student_client.post('/librarian/reservations/1/claim')
        assert resp.status_code == 302
        writes = [c[0][0] for c in mock_db['execute'].call_args_list
                  if 'INSERT' in c[0][0] and 'audit_trail' not in c[0][0]]
        assert writes == []

    def test_faculty_blocked(self, faculty_client):
        """Validates faculty blocked `/librarian/reservations` as faculty (expects 302) [TestAuth / reservations edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        assert faculty_client.get('/librarian/reservations').status_code == 302
