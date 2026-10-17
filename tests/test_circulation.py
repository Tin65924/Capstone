"""Tests for the Circulation module: desk borrow/return, reservations, user borrow/reserve, RBAC, availability labels."""

from datetime import date, datetime, timedelta


class TestCirculationAccess:
    def test_student_forbidden_from_circulation(self, student_client):
        """Validates student forbidden from circulation `/librarian/circulation` as student (expects 302) [TestCirculationAccess / circulation].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        resp = student_client.get('/librarian/circulation')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_faculty_forbidden_from_circulation(self, faculty_client):
        """Validates faculty forbidden from circulation `/librarian/circulation` as faculty (expects 302) [TestCirculationAccess / circulation].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        resp = faculty_client.get('/librarian/circulation')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_student_forbidden_from_reservations(self, student_client):
        """Validates student forbidden from reservations `/librarian/reservations` as student (expects 302) [TestCirculationAccess / circulation].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        resp = student_client.get('/librarian/reservations')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location


class TestCirculationPage:
    def test_librarian_circulation_renders(self, librarian_client, mock_db):
        """Validates librarian circulation renders `/librarian/circulation` as librarian (expects 200) [TestCirculationPage / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (2,),   # stats active loans
            (1,),   # stats overdue
            (0,),   # stats due soon
        ]
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/circulation')
        assert resp.status_code == 200
        assert b'Circulation Management' in resp.data
        assert b'No active loans' in resp.data

    def test_borrower_lookup_found(self, librarian_client, mock_db):
        """Validates borrower lookup found `/librarian/circulation?search=2024-0001` as librarian (expects 200) [TestCirculationPage / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].return_value = (1, '2024-0001', 'CS', 'active', 'Test Student', 1, 'Student')
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/circulation?search=2024-0001')
        assert resp.status_code == 200
        assert b'Test Student' in resp.data
        assert b'bg-blue-100 text-blue-700">Student</span>' in resp.data
        assert b'Limit: 3 books' in resp.data

    def test_borrower_lookup_not_found(self, librarian_client, mock_db):
        """Validates borrower lookup not found `/librarian/circulation?search=9999` as librarian (expects 200) [TestCirculationPage / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/circulation?search=9999')
        assert resp.status_code == 200
        assert b'No borrower found' in resp.data

    def test_stat_cards_link_to_filtered_borrowings(self, librarian_client, mock_db):
        """Validates stat cards link to filtered borrowings `/librarian/circulation` as librarian (expects 200) [TestCirculationPage / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (2,),   # stats active loans
            (1,),   # stats overdue
            (0,),   # stats due soon
        ]
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/circulation')
        assert resp.status_code == 200
        # One borrowings table; the stat cards deep-link into its filters.
        assert b'id="all-borrowings"' in resp.data
        assert b'loan_status=overdue' in resp.data
        assert b'loan_status=due_soon' in resp.data
        assert b'id="loan-filters"' in resp.data
        assert b'name="q"' in resp.data
        assert b'id="loan-filter-btn"' in resp.data
        assert b'id="loan-filter-modal"' in resp.data
        assert b'name="loan_type"' in resp.data
        assert b'name="borrow_date"' in resp.data
        # Body-level modal like the other modals: a fixed overlay nested
        # inside the animated card would be clipped to the card instead of
        # covering the whole screen.
        assert resp.data.index(b'id="loan-filter-modal"') > resp.data.index(b'</main>')
        # Modal fields still submit with the table search form.
        assert b'form="loan-filters"' in resp.data
        # Overdue / Due Soon are filters now, not separate tables.
        assert b'id="overdue-books"' not in resp.data
        assert b'id="due-soon"' not in resp.data


class TestCirculationLoanFilters:
    """All Borrowings filters: type, borrow date, overdue, due soon."""

    @staticmethod
    def _loan(cid=1, borrow=None, due=None, btype='overnight',
              status='active', name='Alice', title='Book A', acc='ACC-1'):
        """Test helper _loan: build mocked data or DB stub for the test."""
        return (cid, borrow, due, btype, status, name, 5, title, acc, 1)

    def _page(self, librarian_client, mock_db, loans, query=''):
        """Test helper _page: build mocked data or DB stub for the test."""
        mock_db['fetch_one'].side_effect = [
            (len(loans),),  # stats active loans
            (0,),           # stats overdue
            (0,),           # stats due soon
        ]
        mock_db['fetch_all'].side_effect = [loans, []]
        return librarian_client.get('/librarian/circulation' + query)

    def test_filter_overnight_only(self, librarian_client, mock_db):
        """Validates filter overnight only as librarian (expects 200) [TestCirculationLoanFilters / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        loans = [
            self._loan(1, date(2026, 8, 1), date(2099, 1, 1), 'overnight', 'active', 'Alice', 'Book A', 'ACC-1'),
            self._loan(2, date(2026, 8, 1), date(2099, 1, 1), 'daily_circulation', 'active', 'Bob', 'Book B', 'ACC-2'),
        ]
        resp = self._page(librarian_client, mock_db, loans, '?loan_type=overnight')
        assert resp.status_code == 200
        assert b'ACC-1' in resp.data
        assert b'ACC-2' not in resp.data

    def test_filter_daily_only(self, librarian_client, mock_db):
        """Validates filter daily only as librarian (expects 200) [TestCirculationLoanFilters / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        loans = [
            self._loan(1, date(2026, 8, 1), date(2099, 1, 1), 'overnight', 'active', 'Alice', 'Book A', 'ACC-1'),
            self._loan(2, date(2026, 8, 1), date(2099, 1, 1), 'daily_circulation', 'active', 'Bob', 'Book B', 'ACC-2'),
        ]
        resp = self._page(librarian_client, mock_db, loans, '?loan_type=daily_circulation')
        assert resp.status_code == 200
        assert b'ACC-2' in resp.data
        assert b'ACC-1' not in resp.data

    def test_filter_overdue(self, librarian_client, mock_db):
        """Validates filter overdue as librarian (expects 200) [TestCirculationLoanFilters / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        loans = [
            self._loan(1, date(2026, 8, 1), date.today() - timedelta(days=1), 'overnight', 'active', 'Alice', 'Book A', 'ACC-1'),
            self._loan(2, date(2026, 8, 1), date(2099, 1, 1), 'overnight', 'active', 'Bob', 'Book B', 'ACC-2'),
        ]
        resp = self._page(librarian_client, mock_db, loans, '?loan_status=overdue')
        assert resp.status_code == 200
        assert b'ACC-1' in resp.data
        assert b'ACC-2' not in resp.data
        assert b'Overdue' in resp.data

    def test_filter_due_soon(self, librarian_client, mock_db):
        """Validates filter due soon as librarian (expects 200) [TestCirculationLoanFilters / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        loans = [
            self._loan(1, date(2026, 8, 1), date.today() + timedelta(days=1), 'overnight', 'active', 'Alice', 'Book A', 'ACC-1'),
            self._loan(2, date(2026, 8, 1), date(2099, 1, 1), 'overnight', 'active', 'Bob', 'Book B', 'ACC-2'),
        ]
        resp = self._page(librarian_client, mock_db, loans, '?loan_status=due_soon')
        assert resp.status_code == 200
        assert b'ACC-1' in resp.data
        assert b'ACC-2' not in resp.data
        assert b'Due Soon' in resp.data

    def test_filter_borrow_date(self, librarian_client, mock_db):
        """Validates filter borrow date as librarian (expects 200) [TestCirculationLoanFilters / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        loans = [
            self._loan(1, date(2026, 8, 1), date(2099, 1, 1), 'overnight', 'active', 'Alice', 'Book A', 'ACC-1'),
            self._loan(2, date(2026, 8, 5), date(2099, 1, 1), 'overnight', 'active', 'Bob', 'Book B', 'ACC-2'),
        ]
        resp = self._page(librarian_client, mock_db, loans, '?borrow_date=2026-08-01')
        assert resp.status_code == 200
        assert b'ACC-1' in resp.data
        assert b'ACC-2' not in resp.data

    def test_invalid_filter_values_fall_back_to_all(self, librarian_client, mock_db):
        """Validates invalid filter values fall back to all as librarian (expects 200) [TestCirculationLoanFilters / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        loans = [
            self._loan(1, date(2026, 8, 1), date(2099, 1, 1), 'overnight', 'active', 'Alice', 'Book A', 'ACC-1'),
        ]
        resp = self._page(librarian_client, mock_db, loans,
                          '?loan_type=bogus&loan_status=bogus&borrow_date=not-a-date')
        assert resp.status_code == 200
        assert b'ACC-1' in resp.data

    def test_no_match_shows_clear_filters(self, librarian_client, mock_db):
        """Validates no match shows clear filters as librarian (expects 200) [TestCirculationLoanFilters / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        loans = [
            self._loan(1, date(2026, 8, 1), date(2099, 1, 1), 'overnight', 'active', 'Alice', 'Book A', 'ACC-1'),
        ]
        resp = self._page(librarian_client, mock_db, loans, '?loan_status=overdue')
        assert resp.status_code == 200
        assert b'No borrowings match the selected filters' in resp.data

    def test_table_search_matches_borrower(self, librarian_client, mock_db):
        """Validates table search matches borrower as librarian (expects 200) [TestCirculationLoanFilters / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        loans = [
            self._loan(1, date(2026, 8, 1), date(2099, 1, 1), 'overnight', 'active', 'Alice', 'Book A', 'ACC-1'),
            self._loan(2, date(2026, 8, 1), date(2099, 1, 1), 'overnight', 'active', 'Bob', 'Book B', 'ACC-2'),
        ]
        resp = self._page(librarian_client, mock_db, loans, '?q=alice')
        assert resp.status_code == 200
        assert b'ACC-1' in resp.data
        assert b'ACC-2' not in resp.data

    def test_table_search_matches_title_and_accession(self, librarian_client, mock_db):
        """Validates table search matches title and accession as librarian (expects 200) [TestCirculationLoanFilters / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        loans = [
            self._loan(1, date(2026, 8, 1), date(2099, 1, 1), 'overnight', 'active', 'Alice', 'Algorithms', 'ACC-1'),
            self._loan(2, date(2026, 8, 1), date(2099, 1, 1), 'overnight', 'active', 'Bob', 'Databases', 'ACC-2'),
        ]
        resp = self._page(librarian_client, mock_db, loans, '?q=algo')
        assert resp.status_code == 200
        assert b'Algorithms' in resp.data
        assert b'Databases' not in resp.data
        resp = self._page(librarian_client, mock_db, loans, '?q=acc-2')
        assert resp.status_code == 200
        assert b'ACC-2' in resp.data
        assert b'ACC-1' not in resp.data

    def test_table_search_combines_with_modal_filters(self, librarian_client, mock_db):
        """Validates table search combines with modal filters as librarian (expects 200) [TestCirculationLoanFilters / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        loans = [
            self._loan(1, date(2026, 8, 1), date(2099, 1, 1), 'overnight', 'active', 'Alice', 'Book A', 'ACC-1'),
            self._loan(2, date(2026, 8, 1), date(2099, 1, 1), 'daily_circulation', 'active', 'Alice', 'Book B', 'ACC-2'),
        ]
        resp = self._page(librarian_client, mock_db, loans, '?q=alice&loan_type=daily_circulation')
        assert resp.status_code == 200
        assert b'ACC-2' in resp.data
        assert b'ACC-1' not in resp.data

    def test_table_search_no_match(self, librarian_client, mock_db):
        """Validates table search no match as librarian (expects 200) [TestCirculationLoanFilters / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        loans = [
            self._loan(1, date(2026, 8, 1), date(2099, 1, 1), 'overnight', 'active', 'Alice', 'Book A', 'ACC-1'),
        ]
        resp = self._page(librarian_client, mock_db, loans, '?q=zzz-no-such-loan')
        assert resp.status_code == 200
        assert b'No borrowings match the selected filters' in resp.data


class TestDeskBorrow:
    def test_borrow_success(self, librarian_client, mock_db):
        """Validates borrow success `/librarian/circulation/borrow` as librarian (expects 302) [TestDeskBorrow / circulation].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (1, '2024-0001', 'CS', 'active', 'Test Student', 1, 'Student'),  # borrower details
            (10, '2024-00123', 5, 1, '2024-01-10', 'purchase'),              # accession
            None,                                                            # not lost
            None,                                                            # book lookup (active)
            None,                                                            # no active loan
            None,                                                            # no waiting queue
            None,                                                            # no active loan for this book
            (0,),                                                            # count active loans
        ]
        resp = librarian_client.post('/librarian/circulation/borrow', data={
            'borrower_id': 1,
            'accession_number': '2024-00123',
            'borrow_type': 'overnight',
        })
        assert resp.status_code == 302
        call_args = mock_db['execute'].call_args_list[0]
        assert 'INSERT INTO circulation_records' in call_args[0][0]

    def test_borrow_accession_not_found(self, librarian_client, mock_db):
        """Validates borrow accession not found `/librarian/circulation/borrow` as librarian (expects 302) [TestDeskBorrow / circulation].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (1, '2024-0001', 'CS', 'active', 'Test Student', 1, 'Student'),
            None,
        ]
        resp = librarian_client.post('/librarian/circulation/borrow', data={
            'borrower_id': 1,
            'accession_number': 'nonexistent',
            'borrow_type': 'overnight',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_borrow_already_loaned_rejected(self, librarian_client, mock_db):
        """Validates borrow already loaned rejected `/librarian/circulation/borrow` as librarian (expects 302) [TestDeskBorrow / circulation].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (1, '2024-0001', 'CS', 'active', 'Test Student', 1, 'Student'),
            (10, '2024-00123', 5, 1, '2024-01-10', 'purchase'),
            None,  # not lost
            None,  # book lookup (active)
            (55, 10, 1, 1, 5, 'overnight', 'borrow', '2026-08-01', '2026-08-03', None, 0, None, False, 'active'),
        ]
        resp = librarian_client.post('/librarian/circulation/borrow', data={
            'borrower_id': 1,
            'accession_number': '2024-00123',
            'borrow_type': 'overnight',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_borrow_over_limit_rejected(self, librarian_client, mock_db):
        """Validates borrow over limit rejected `/librarian/circulation/borrow` as librarian (expects 302) [TestDeskBorrow / circulation].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (1, '2024-0001', 'CS', 'active', 'Test Student', 1, 'Student'),
            (10, '2024-00123', 5, 1, '2024-01-10', 'purchase'),
            None,  # not lost
            None,  # book lookup (active)
            None,  # copy not on loan
            None,  # no waiting queue
            None,  # no active loan for this book
            (3,),  # count active loans == student limit
        ]
        resp = librarian_client.post('/librarian/circulation/borrow', data={
            'borrower_id': 1,
            'accession_number': '2024-00123',
            'borrow_type': 'overnight',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_borrow_duplicate_book_rejected(self, librarian_client, mock_db):
        """Validates borrow duplicate book rejected `/librarian/circulation/borrow` as librarian (expects 302) [TestDeskBorrow / circulation].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (1, '2024-0001', 'CS', 'active', 'Test Student', 1, 'Student'),
            (11, '2024-00124', 5, 1, '2024-01-10', 'purchase'),  # different copy, same book
            None,                                                 # not lost
            None,                                                 # book lookup (active)
            None,                                                 # this copy not on loan
            None,                                                 # no waiting queue
            (55, 10, 1, 1, 5, 'overnight', 'borrow', '2026-08-01', '2026-08-03', None, 0, None, False, 'active'),  # already holds book 5
        ]
        resp = librarian_client.post('/librarian/circulation/borrow', data={
            'borrower_id': 1,
            'accession_number': '2024-00124',
            'borrow_type': 'overnight',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0


class TestDeskReturn:
    def test_return_computes_fine(self, librarian_client, mock_db):
        """Validates return computes fine `/librarian/circulation/return` as librarian (expects 302) [TestDeskReturn / circulation].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (UPDATE).
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (10, '2024-00123', 5, 1, '2024-01-10', 'purchase'),       # accession
            (55, 10, 1, 1, 5, 'overnight', 'borrow', '2026-08-01', '2026-08-02', None, 0, None, False, 'active'),  # active loan
            (date(2026, 8, 1), date(2026, 8, 5), 'overnight'),     # calculate_fine due/returned/type
            None,                                                      # no waiting reservation
        ]
        resp = librarian_client.post('/librarian/circulation/return', data={
            'accession_number': '2024-00123',
        })
        assert resp.status_code == 302
        call_args = mock_db['execute'].call_args_list[0]
        assert 'UPDATE circulation_records' in call_args[0][0]
        assert 'returned' in call_args[0][1]
        # 4 days overdue x P5/day (overnight rate).
        assert call_args[0][1][2] == 20.0

    def test_return_not_borrowed_rejected(self, librarian_client, mock_db):
        """Validates return not borrowed rejected `/librarian/circulation/return` as librarian (expects 302) [TestDeskReturn / circulation].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (10, '2024-00123', 5, 1, '2024-01-10', 'purchase'),
            None,  # no active loan
        ]
        resp = librarian_client.post('/librarian/circulation/return', data={
            'accession_number': '2024-00123',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_return_daily_loan_accrues_no_fine(self, librarian_client, mock_db):
        """Validates return daily loan accrues no fine `/librarian/circulation/return` as librarian (expects 302) [TestDeskReturn / circulation].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (UPDATE).
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue).

Daily/in-library loans never accrue fines, however overdue."""
        mock_db['fetch_one'].side_effect = [
            (10, '2024-00123', 5, 1, '2024-01-10', 'purchase'),       # accession
            (55, 10, 1, 1, 5, 'daily_circulation', 'borrow', '2026-08-01', '2026-08-02', None, 0, None, False, 'active'),  # active loan
            (date(2026, 8, 1), date(2026, 9, 1), 'daily_circulation'),  # calculate_fine: month late
            None,                                                      # no waiting reservation
        ]
        resp = librarian_client.post('/librarian/circulation/return', data={
            'accession_number': '2024-00123',
        })
        assert resp.status_code == 302
        call_args = mock_db['execute'].call_args_list[0]
        assert 'UPDATE circulation_records' in call_args[0][0]
        assert call_args[0][1][2] == 0


class TestReservationLifecycle:
    def test_allocate_writes_notification(self, librarian_client, mock_db):
        """Validates allocate writes notification `/librarian/reservations/9/allocate` as librarian (expects 302) [TestReservationLifecycle / circulation].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (9, 5, 2, 1, '2026-08-01 10:00:00', 'waiting', None),  # reservation
            (10, '2024-00123', 5, 1, '2024-01-10', 'purchase'),    # available copy
            None,                                                  # book lookup (active)
            (2, '2024-0002', 'CS', 'active', 'Test Student', 1, 'Student'),  # borrower details
            None,                                                  # no active loan for this book
            (0,),                                                  # count active loans
            (0,),                                                  # count allocated reservations
            (2,),                                                  # count available accessions
        ]
        resp = librarian_client.post('/librarian/reservations/9/allocate')
        assert resp.status_code == 302
        # First execute is the expiry sweep, then allocate + 2 notifications.
        assert mock_db['execute'].call_count >= 3
        notif_calls = [c for c in mock_db['execute'].call_args_list
                       if 'INSERT INTO notification_log' in c[0][0]]
        assert notif_calls

    def test_allocate_rejected_when_no_available_copy(self, librarian_client, mock_db):
        """Validates allocate rejected when no available copy `/librarian/reservations/9/allocate` as librarian (expects 302) [TestReservationLifecycle / circulation].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (9, 5, 2, 1, '2026-08-01 10:00:00', 'waiting', None),  # reservation
            None,                                                   # no available copy
        ]
        resp = librarian_client.post('/librarian/reservations/9/allocate')
        assert resp.status_code == 302
        # Only the expiry sweep runs; no allocate/notification writes.
        assert mock_db['execute'].call_count == 1
        assert 'claim_deadline' in mock_db['execute'].call_args_list[0][0][0]

    def test_allocate_rejected_when_not_waiting(self, librarian_client, mock_db):
        """Validates allocate rejected when not waiting `/librarian/reservations/9/allocate` as librarian (expects 302) [TestReservationLifecycle / circulation].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].return_value = (9, 5, 2, 1, '2026-08-01 10:00:00', 'claimed', None)
        resp = librarian_client.post('/librarian/reservations/9/allocate')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 1  # expiry sweep only

    def test_claim_requires_allocated(self, librarian_client, mock_db):
        """Validates claim requires allocated `/librarian/reservations/9/claim` as librarian (expects 302) [TestReservationLifecycle / circulation].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].return_value = (9, 5, 2, 1, '2026-08-01 10:00:00', 'waiting', None)
        resp = librarian_client.post('/librarian/reservations/9/claim')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 1  # expiry sweep only

    def test_claim_success(self, librarian_client, mock_db):
        """Validates claim success `/librarian/reservations/9/claim` as librarian (expects 302) [TestReservationLifecycle / circulation].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (9, 5, 2, 1, '2026-08-01 10:00:00', 'allocated', '2026-08-03 10:00:00'),  # reservation
            (10, '2024-00123', 5, 1, '2024-01-10', 'purchase'),                        # available copy
            None,                                                                      # book lookup (active)
            (2, '2024-0002', 'CS', 'active', 'Test Student', 1, 'Student'),            # borrower details
            None,                                                                      # no active loan for this book
            (0,),                                                                      # count active loans
        ]
        resp = librarian_client.post('/librarian/reservations/9/claim')
        assert resp.status_code == 302
        # [0] expiry sweep, [1] INSERT loan, [2] claim update.
        first_call = mock_db['execute'].call_args_list[1]
        assert 'INSERT INTO circulation_records' in first_call[0][0]
        assert 'overnight' in first_call[0][1]
        second_call = mock_db['execute'].call_args_list[2]
        assert "reservation_status = 'claimed'" in second_call[0][0]

    def test_claim_rejected_when_no_available_copy(self, librarian_client, mock_db):
        """Validates claim rejected when no available copy `/librarian/reservations/9/claim` as librarian (expects 302) [TestReservationLifecycle / circulation].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (9, 5, 2, 1, '2026-08-01 10:00:00', 'allocated', '2026-08-03 10:00:00'),  # reservation
            None,                                                                      # no available copy
        ]
        resp = librarian_client.post('/librarian/reservations/9/claim')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 1  # expiry sweep only

    def test_claim_rejected_when_borrower_at_limit(self, librarian_client, mock_db):
        """Validates claim rejected when borrower at limit `/librarian/reservations/9/claim` as librarian (expects 302) [TestReservationLifecycle / circulation].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (9, 5, 2, 1, '2026-08-01 10:00:00', 'allocated', '2026-08-03 10:00:00'),  # reservation
            (10, '2024-00123', 5, 1, '2024-01-10', 'purchase'),                        # available copy
            None,                                                                      # book lookup (active)
            (2, '2024-0002', 'CS', 'active', 'Test Student', 1, 'Student'),            # borrower details
            None,                                                                      # no active loan for this book
            (3,),                                                                      # count == student limit
        ]
        resp = librarian_client.post('/librarian/reservations/9/claim')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 1  # expiry sweep only

    def test_claim_rejected_when_already_holding_book(self, librarian_client, mock_db):
        """Validates claim rejected when already holding book `/librarian/reservations/9/claim` as librarian (expects 302) [TestReservationLifecycle / circulation].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (9, 5, 2, 1, '2026-08-01 10:00:00', 'allocated', '2026-08-03 10:00:00'),  # reservation
            (10, '2024-00123', 5, 1, '2024-01-10', 'purchase'),                        # available copy
            None,                                                                      # book lookup (active)
            (2, '2024-0002', 'CS', 'active', 'Test Student', 1, 'Student'),            # borrower details
            (55, 5, 2, 1, 1, 'daily_circulation', 'borrow', '2026-08-01', '2026-08-02', None, 0, None, False, 'active'),  # already holds book 5
        ]
        resp = librarian_client.post('/librarian/reservations/9/claim')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 1  # expiry sweep only

    def test_allocate_rejected_when_borrower_at_limit(self, librarian_client, mock_db):
        """Validates allocate rejected when borrower at limit `/librarian/reservations/9/allocate` as librarian (expects 302) [TestReservationLifecycle / circulation].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (9, 5, 2, 1, '2026-08-01 10:00:00', 'waiting', None),  # reservation
            (10, '2024-00123', 5, 1, '2024-01-10', 'purchase'),    # available copy
            None,                                                  # book lookup (active)
            (2, '2024-0002', 'CS', 'active', 'Test Student', 1, 'Student'),  # borrower details
            None,                                                  # no active loan for this book
            (3,),                                                  # count == limit
        ]
        resp = librarian_client.post('/librarian/reservations/9/allocate')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 1  # expiry sweep only

    def test_allocate_rejected_when_already_holding_book(self, librarian_client, mock_db):
        """Validates allocate rejected when already holding book `/librarian/reservations/9/allocate` as librarian (expects 302) [TestReservationLifecycle / circulation].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (9, 5, 2, 1, '2026-08-01 10:00:00', 'waiting', None),  # reservation
            (10, '2024-00123', 5, 1, '2024-01-10', 'purchase'),    # available copy
            None,                                                  # book lookup (active)
            (2, '2024-0002', 'CS', 'active', 'Test Student', 1, 'Student'),  # borrower details
            (55, 5, 2, 1, 1, 'daily_circulation', 'borrow', '2026-08-01', '2026-08-02', None, 0, None, False, 'active'),  # already holds book 5
        ]
        resp = librarian_client.post('/librarian/reservations/9/allocate')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 1  # expiry sweep only

    def test_expire_success(self, librarian_client, mock_db):
        """Validates expire success `/librarian/reservations/9/expire` as librarian (expects 302) [TestReservationLifecycle / circulation].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].return_value = (9, 5, 2, 1, '2026-08-01 10:00:00', 'allocated', '2026-08-03 10:00:00')
        resp = librarian_client.post('/librarian/reservations/9/expire')
        assert resp.status_code == 302
        # Sweep + manual expire + notification (+ audit log).
        assert mock_db['execute'].call_count >= 2
        assert any("reservation_status = 'expired'" in c[0][0]
                   and 'claim_deadline' not in c[0][0]
                   for c in mock_db['execute'].call_args_list)

    def test_action_preserves_status_filter(self, librarian_client, mock_db):
        """Validates action preserves status filter `/librarian/reservations/9/expire` as librarian (expects 302) [TestReservationLifecycle / circulation].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].return_value = (9, 5, 2, 1, '2026-08-01 10:00:00', 'allocated', '2026-08-03 10:00:00')
        resp = librarian_client.post('/librarian/reservations/9/expire', data={'status': 'waiting'})
        assert resp.status_code == 302
        assert 'status=waiting' in resp.location

    def test_action_drops_invalid_status(self, librarian_client, mock_db):
        """Validates action drops invalid status `/librarian/reservations/9/expire` as librarian (expects 302) [TestReservationLifecycle / circulation].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].return_value = (9, 5, 2, 1, '2026-08-01 10:00:00', 'allocated', '2026-08-03 10:00:00')
        resp = librarian_client.post('/librarian/reservations/9/expire', data={'status': 'bogus'})
        assert resp.status_code == 302
        assert 'status=' not in resp.location

    def test_stats_sum_correct_status_columns(self, librarian_client, mock_db):
        """Validates stats sum correct status columns `/librarian/reservations` as librarian (expects 200) [TestReservationLifecycle / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        groups = [
            (1, 'Book A', 'Author A', 6, 1, 2, 0, 0),   # total, waiting, allocated, claimed, expired
            (3, 'Book B', 'Author B', 5, 2, 3, 0, 0),
        ]
        mock_db['fetch_all'].side_effect = [groups, [], []]
        resp = librarian_client.get('/librarian/reservations')
        assert resp.status_code == 200
        assert b'Active Reservations</div><div class="text-xl font-bold">8</div>' in resp.data
        assert b'Ready for Pickup</div><div class="text-xl font-bold">5</div>' in resp.data
        assert b'Waiting in Queue</div><div class="text-xl font-bold">3</div>' in resp.data


class TestReservationFilters:
    GROUPS = [
        (1, 'Book A', 'Author A', 3, 1, 1, 1, 0),  # waiting 1, allocated 1, claimed 1
        (2, 'Book B', 'Author B', 1, 0, 0, 0, 1),  # expired only
    ]
    BOOK_A_ROWS = [
        (11, 1, 'waiting', datetime(2026, 8, 1, 10, 0), None, 'Book A', 'Alice', 5, 'ID-1'),
        (12, 2, 'allocated', datetime(2026, 8, 2, 10, 0), None, 'Book A', 'Bob', 6, 'ID-2'),
        (13, 3, 'claimed', datetime(2026, 8, 3, 10, 0), None, 'Book A', 'Cara', 7, 'ID-3'),
    ]
    BOOK_B_ROWS = [
        (21, 1, 'expired', datetime(2026, 8, 4, 10, 0), None, 'Book B', 'Dan', 8, 'ID-4'),
    ]

    def _mock_page(self, mock_db):
        """Test helper _mock_page: build mocked data or DB stub for the test."""
        mock_db['fetch_all'].side_effect = [self.GROUPS, self.BOOK_A_ROWS, self.BOOK_B_ROWS]

    def test_no_filter_defaults_to_active(self, librarian_client, mock_db):
        # Finished (claimed/expired) history is auto-removed from the default view.
        """Validates no filter defaults to active `/librarian/reservations` as librarian (expects 200) [TestReservationFilters / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        self._mock_page(mock_db)
        resp = librarian_client.get('/librarian/reservations')
        assert resp.status_code == 200
        assert b'Alice' in resp.data
        assert b'Bob' in resp.data
        assert b'Book A' in resp.data
        for name in (b'Cara', b'Dan'):
            assert name not in resp.data
        assert b'Book B' not in resp.data
        assert b'Back to active' not in resp.data

    def test_filter_all_shows_everything(self, librarian_client, mock_db):
        """Validates filter all shows everything `/librarian/reservations?status=all` as librarian (expects 200) [TestReservationFilters / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        self._mock_page(mock_db)
        resp = librarian_client.get('/librarian/reservations?status=all')
        assert resp.status_code == 200
        for name in (b'Alice', b'Bob', b'Cara', b'Dan', b'Book A', b'Book B'):
            assert name in resp.data
        # Filter banner was removed: no "Back to active" notice in any view.
        assert b'Back to active' not in resp.data

    def test_filter_history_shows_claimed_and_expired(self, librarian_client, mock_db):
        """Validates filter history shows claimed and expired `/librarian/reservations?status=history` as librarian (expects 200) [TestReservationFilters / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        self._mock_page(mock_db)
        resp = librarian_client.get('/librarian/reservations?status=history')
        assert resp.status_code == 200
        assert b'Cara' in resp.data
        assert b'Dan' in resp.data
        for name in (b'Alice', b'Bob'):
            assert name not in resp.data

    def test_page_auto_expires_overdue(self, librarian_client, mock_db):
        """Validates page auto expires overdue `/librarian/reservations` as librarian (expects 200) [TestReservationFilters / circulation].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        self._mock_page(mock_db)
        resp = librarian_client.get('/librarian/reservations')
        assert resp.status_code == 200
        first_call = mock_db['execute'].call_args_list[0]
        assert "reservation_status = 'expired'" in first_call[0][0]
        assert 'claim_deadline' in first_call[0][0]

    def test_page_renders_when_expire_fails(self, librarian_client, mock_db):
        """Validates page renders when expire fails `/librarian/reservations` as librarian (expects 200) [TestReservationFilters / circulation].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        from unittest.mock import patch
        self._mock_page(mock_db)
        with patch('app.circulation.routes.expire_overdue_reservations',
                   side_effect=Exception('db down')):
            resp = librarian_client.get('/librarian/reservations')
        assert resp.status_code == 200

    def test_filter_waiting(self, librarian_client, mock_db):
        """Validates filter waiting `/librarian/reservations?status=waiting` as librarian (expects 200) [TestReservationFilters / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        self._mock_page(mock_db)
        resp = librarian_client.get('/librarian/reservations?status=waiting')
        assert resp.status_code == 200
        assert b'Alice' in resp.data
        for name in (b'Bob', b'Cara', b'Dan'):
            assert name not in resp.data
        assert b'Book B' not in resp.data

    def test_filter_allocated(self, librarian_client, mock_db):
        """Validates filter allocated `/librarian/reservations?status=allocated` as librarian (expects 200) [TestReservationFilters / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        self._mock_page(mock_db)
        resp = librarian_client.get('/librarian/reservations?status=allocated')
        assert resp.status_code == 200
        assert b'Bob' in resp.data
        for name in (b'Alice', b'Cara', b'Dan'):
            assert name not in resp.data

    def test_filter_active_shows_waiting_and_allocated(self, librarian_client, mock_db):
        """Validates filter active shows waiting and allocated `/librarian/reservations?status=active` as librarian (expects 200) [TestReservationFilters / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        self._mock_page(mock_db)
        resp = librarian_client.get('/librarian/reservations?status=active')
        assert resp.status_code == 200
        assert b'Alice' in resp.data
        assert b'Bob' in resp.data
        for name in (b'Cara', b'Dan'):
            assert name not in resp.data
        # Active is the default view: no banner, but history/all pills exist.
        assert b'status=history' in resp.data
        assert b'status=all' in resp.data

    def test_invalid_filter_falls_back_to_active(self, librarian_client, mock_db):
        """Validates invalid filter falls back to active `/librarian/reservations?status=bogus` as librarian (expects 200) [TestReservationFilters / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        self._mock_page(mock_db)
        resp = librarian_client.get('/librarian/reservations?status=bogus')
        assert resp.status_code == 200
        assert b'Alice' in resp.data
        assert b'Bob' in resp.data
        for name in (b'Cara', b'Dan'):
            assert name not in resp.data
        assert b'Back to active' not in resp.data

    def test_kpi_cards_link_to_filters(self, librarian_client, mock_db):
        """Validates kpi cards link to filters `/librarian/reservations` as librarian (expects 200) [TestReservationFilters / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        self._mock_page(mock_db)
        resp = librarian_client.get('/librarian/reservations')
        assert resp.status_code == 200
        assert b'status=active' in resp.data
        assert b'status=allocated' in resp.data
        assert b'status=waiting' in resp.data

    def test_cancel_button_replaces_expire(self, librarian_client, mock_db):
        """Validates cancel button replaces expire `/librarian/reservations` as librarian (expects 200) [TestReservationFilters / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        self._mock_page(mock_db)
        resp = librarian_client.get('/librarian/reservations')
        assert resp.status_code == 200
        assert b'>Cancel</button>' in resp.data
        assert b'>Expire</button>' not in resp.data


class TestStaffUserHistory:
    BORROWERS = [
        (1, 'Test Student', 'student@mcst.edu.ph', 'Student', 1, '2024-0001', 'CS'),
        (2, 'Test Faculty', 'faculty@mcst.edu.ph', 'Faculty', 2, '2024-0002', 'CS'),
    ]

    def test_student_forbidden_from_history_list(self, student_client):
        """Validates student forbidden from history list `/librarian/users/history` as student (expects 302) [TestStaffUserHistory / circulation].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        resp = student_client.get('/librarian/users/history')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_student_forbidden_from_history_detail(self, student_client):
        """Validates student forbidden from history detail `/librarian/users/1/history` as student (expects 302) [TestStaffUserHistory / circulation].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        resp = student_client.get('/librarian/users/1/history')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_history_list_renders(self, librarian_client, mock_db):
        """Validates history list renders `/librarian/users/history` as librarian (expects 200) [TestStaffUserHistory / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_all'].return_value = self.BORROWERS
        resp = librarian_client.get('/librarian/users/history')
        assert resp.status_code == 200
        assert b'Test Student' in resp.data
        assert b'2024-0001' in resp.data
        assert b'/librarian/users/1/history' in resp.data

    def test_history_list_search_filters(self, librarian_client, mock_db):
        """Validates history list search filters `/librarian/users/history?search=Student` as librarian (expects 200) [TestStaffUserHistory / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_all'].return_value = [self.BORROWERS[0]]
        resp = librarian_client.get('/librarian/users/history?search=Student')
        assert resp.status_code == 200
        assert b'Test Student' in resp.data
        call_args = mock_db['fetch_all'].call_args_list[0]
        assert 'ILIKE' in call_args[0][0]
        assert '%Student%' in call_args[0][1]

    def test_admin_can_view_history_list(self, admin_client, mock_db):
        """Validates admin can view history list `/librarian/users/history` as admin (expects 200) [TestStaffUserHistory / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_all'].return_value = self.BORROWERS
        resp = admin_client.get('/librarian/users/history')
        assert resp.status_code == 200
        assert b'Test Student' in resp.data

    def test_history_detail_shows_full_history(self, librarian_client, mock_db):
        # get_user_by_id is mocked in conftest (user 1 exists);
        # fetch_one calls: borrower row, then total fines.
        """Validates history detail shows full history `/librarian/users/1/history` as librarian (expects 200) [TestStaffUserHistory / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (1, 1, '2024-0001', 'CS', '0917', 'active'),
            (25.0,),
        ]
        mock_db['fetch_all'].side_effect = [
            [(55, date(2026, 8, 1), date(2026, 8, 2), date(2026, 8, 2), 'overnight',
              'returned', 0, 'Intro to Algorithms', 'Cormen', '2024-00123')],
            [(11, 1, 'waiting', datetime(2026, 8, 1, 10, 0), None, 'Book A', 'Auth A'),
             (12, 2, 'claimed', datetime(2026, 8, 2, 10, 0), None, 'Book B', 'Auth B'),
             (13, 3, 'expired', datetime(2026, 8, 3, 10, 0), None, 'Book C', 'Auth C')],
            [(7, 'Wanted Book', 'Some Author', 'approved', date(2026, 8, 1), None)],
            [(55, date(2026, 8, 1), date(2026, 8, 2), date(2026, 8, 2), 25.0,
              'Intro to Algorithms', '2024-00123')],
        ]
        resp = librarian_client.get('/librarian/users/1/history')
        assert resp.status_code == 200
        assert b'Test Student' in resp.data
        assert b'Intro to Algorithms' in resp.data
        # Staff see the FULL reservation history, including finished items
        # that are auto-removed from the user's own history view.
        assert b'claimed' in resp.data
        assert b'expired' in resp.data
        assert b'Wanted Book' in resp.data

    def test_history_detail_user_not_found(self, librarian_client, mock_db):
        """Validates history detail user not found `/librarian/users/99/history` as librarian (expects 302) [TestStaffUserHistory / circulation].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        resp = librarian_client.get('/librarian/users/99/history')
        assert resp.status_code == 302
        assert '/librarian/users/history' in resp.location

    def test_history_detail_no_borrower(self, librarian_client, mock_db):
        """Validates history detail no borrower `/librarian/users/1/history` as librarian (expects 302) [TestStaffUserHistory / circulation].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].return_value = None  # no borrower row
        resp = librarian_client.get('/librarian/users/1/history')
        assert resp.status_code == 302
        assert '/librarian/users/history' in resp.location


class TestActiveReservationHistory:
    def test_user_history_hides_finished(self, student_client, mock_db):
        """Validates user history hides finished as student [TestActiveReservationHistory / circulation].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        from app.circulation import models as circ_models
        circ_models.get_reservation_history_by_borrower(1)
        call_args = mock_db['fetch_all'].call_args_list[0]
        assert "IN ('waiting', 'allocated')" in call_args[0][0]

    def test_full_history_kept_for_staff(self, student_client, mock_db):
        """Validates full history kept for staff as student [TestActiveReservationHistory / circulation].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        from app.circulation import models as circ_models
        circ_models.get_full_reservation_history_by_borrower(1)
        call_args = mock_db['fetch_all'].call_args_list[0]
        assert 'reservation_status' in call_args[0][0]
        assert 'waiting' not in call_args[0][0]  # no status filter: full history

    def test_expire_overdue_targets_deadlines(self, student_client, mock_db):
        """Validates expire overdue targets deadlines as student [TestActiveReservationHistory / circulation].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        from app.circulation import models as circ_models
        circ_models.expire_overdue_reservations()
        call_args = mock_db['execute'].call_args_list[0]
        assert "reservation_status = 'expired'" in call_args[0][0]
        assert 'claim_deadline < NOW()' in call_args[0][0]


class TestUserBorrow:
    def test_overnight_borrow_creates_reservation_not_loan(self, student_client, mock_db):
        """Validates overnight borrow creates reservation not loan `/user/borrow` as student (expects 302) [TestUserBorrow / circulation].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (5, 'Intro to Algorithms', 'Cormen'),     # get_book_by_id
            (1, 1, '2024-0001', 'CS', 'active'),       # get_borrower_by_user
            None,                                      # no active loan for this book
            None,                                      # no existing reservation
            (0,),                                      # count active loans
            (1,),                                      # next queue position
        ]
        resp = student_client.post('/user/borrow', data={
            'book_id': 5,
            'borrow_type': 'overnight',
        })
        assert resp.status_code == 302
        call_args = mock_db['execute'].call_args_list[0]
        assert 'INSERT INTO reservation_queue' in call_args[0][0]
        assert call_args[0][1] == (5, 1, 1)

    def test_overnight_borrow_rejects_duplicate_reservation(self, student_client, mock_db):
        """Validates overnight borrow rejects duplicate reservation `/user/borrow` as student (expects 302) [TestUserBorrow / circulation].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (5, 'Intro to Algorithms', 'Cormen'),
            (1, 1, '2024-0001', 'CS', 'active'),
            None,  # no active loan for this book
            (9, 5, 1, 1, '2026-08-01 10:00:00', 'waiting', None),  # existing reservation
        ]
        resp = student_client.post('/user/borrow', data={
            'book_id': 5,
            'borrow_type': 'overnight',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_overnight_borrow_over_limit_rejected(self, student_client, mock_db):
        """Validates overnight borrow over limit rejected `/user/borrow` as student (expects 302) [TestUserBorrow / circulation].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (5, 'Intro to Algorithms', 'Cormen'),
            (1, 1, '2024-0001', 'CS', 'active'),
            None,                                      # no active loan for this book
            None,                                      # no existing reservation
            (3,),                                      # count active loans == student limit (3)
        ]
        resp = student_client.post('/user/borrow', data={
            'book_id': 5,
            'borrow_type': 'overnight',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_daily_circulation_borrow_is_immediate_loan(self, student_client, mock_db):
        """Validates daily circulation borrow is immediate loan `/user/borrow` as student (expects 302) [TestUserBorrow / circulation].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (5, 'Intro to Algorithms', 'Cormen'),     # get_book_by_id
            (1, 1, '2024-0001', 'CS', 'active'),       # get_borrower_by_user
            None,                                      # no active loan for this book
            (10, '2024-00123', 5, 1, '2024-01-10', 'purchase'),  # available accession
            (0,),                                       # count active loans
            None,                                      # no active reservation for this book
            None,                                      # no waiting queue (queue-jump guard)
        ]
        resp = student_client.post('/user/borrow', data={
            'book_id': 5,
            'borrow_type': 'daily_circulation',
        })
        assert resp.status_code == 302
        call_args = mock_db['execute'].call_args_list[0]
        assert 'INSERT INTO circulation_records' in call_args[0][0]
        assert 'daily_circulation' in call_args[0][1]

    def test_borrow_requires_login(self, client, mock_db):
        """Validates borrow requires login `/user/borrow` (expects 302) [TestUserBorrow / circulation].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = client.post('/user/borrow', data={'book_id': 5})
        assert resp.status_code == 302
        assert '/login' in resp.location

    def test_faculty_over_limit_is_5(self, faculty_client, mock_db):
        """Validates faculty over limit is 5 `/user/borrow` as faculty (expects 302) [TestUserBorrow / circulation].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (5, 'Intro to Algorithms', 'Cormen'),
            (2, 2, '2024-0002', 'CS', 'active'),       # faculty borrower
            None,                                      # no active loan for this book
            None,                                      # no existing reservation
            (5,),                                      # count == faculty limit (5)
        ]
        resp = faculty_client.post('/user/borrow', data={
            'book_id': 5,
            'borrow_type': 'overnight',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_faculty_under_limit_can_borrow(self, faculty_client, mock_db):
        """Validates faculty under limit can borrow `/user/borrow` as faculty (expects 302) [TestUserBorrow / circulation].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (5, 'Intro to Algorithms', 'Cormen'),
            (2, 2, '2024-0002', 'CS', 'active'),
            None,                                      # no active loan for this book
            None,                                      # no existing reservation
            (4,),                                      # under limit
            (1,),
        ]
        resp = faculty_client.post('/user/borrow', data={
            'book_id': 5,
            'borrow_type': 'overnight',
        })
        assert resp.status_code == 302
        call_args = mock_db['execute'].call_args_list[0]
        assert 'INSERT INTO reservation_queue' in call_args[0][0]

    def test_overnight_borrow_rejected_when_already_holding_book(self, student_client, mock_db):
        """Validates overnight borrow rejected when already holding book `/user/borrow` as student (expects 302) [TestUserBorrow / circulation].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (5, 'Intro to Algorithms', 'Cormen'),
            (1, 1, '2024-0001', 'CS', 'active'),
            (55, 5, 1, 1, 1, 'daily_circulation', 'borrow', '2026-08-01', '2026-08-02', None, 0, None, False, 'active'),  # active loan for book 5
        ]
        resp = student_client.post('/user/borrow', data={
            'book_id': 5,
            'borrow_type': 'overnight',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_daily_borrow_rejected_when_already_holding_book(self, student_client, mock_db):
        """Validates daily borrow rejected when already holding book `/user/borrow` as student (expects 302) [TestUserBorrow / circulation].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (5, 'Intro to Algorithms', 'Cormen'),
            (1, 1, '2024-0001', 'CS', 'active'),
            (55, 5, 1, 1, 1, 'daily_circulation', 'borrow', '2026-08-01', '2026-08-02', None, 0, None, False, 'active'),  # active loan for book 5
        ]
        resp = student_client.post('/user/borrow', data={
            'book_id': 5,
            'borrow_type': 'daily_circulation',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0


class TestUserReserve:
    def test_student_reserves_book(self, student_client, mock_db):
        """Validates student reserves book `/user/reserve` as student (expects 302) [TestUserReserve / circulation].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (5, 'Intro to Algorithms', 'Cormen'),     # get_book_by_id
            (1, 1, '2024-0001', 'CS', 'active'),       # get_borrower_by_user
            None,                                      # no existing reservation
            None,                                      # no active loan for this book
            None,                                      # no available accession
            (1,),                                      # next queue position
        ]
        resp = student_client.post('/user/reserve', data={'book_id': 5})
        assert resp.status_code == 302
        call_args = mock_db['execute'].call_args_list[0]
        assert 'INSERT INTO reservation_queue' in call_args[0][0]

    def test_duplicate_reservation_rejected(self, student_client, mock_db):
        """Validates duplicate reservation rejected `/user/reserve` as student (expects 302) [TestUserReserve / circulation].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (5, 'Intro to Algorithms', 'Cormen'),
            (1, 1, '2024-0001', 'CS', 'active'),
            (9, 5, 1, 1, '2026-08-01 10:00:00', 'waiting', None),  # existing reservation
        ]
        resp = student_client.post('/user/reserve', data={'book_id': 5})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_reserve_when_available_redirects_to_borrow(self, student_client, mock_db):
        """Validates reserve when available redirects to borrow `/user/reserve` as student (expects 302) [TestUserReserve / circulation].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (5, 'Intro to Algorithms', 'Cormen'),
            (1, 1, '2024-0001', 'CS', 'active'),
            None,                                       # no existing reservation
            None,                                       # no active loan for this book
            (10, '2024-00123', 5, 1, '2024-01-10', 'purchase'),  # a copy is available
        ]
        resp = student_client.post('/user/reserve', data={'book_id': 5})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_reserve_rejected_when_already_holding_book(self, student_client, mock_db):
        """Validates reserve rejected when already holding book `/user/reserve` as student (expects 302) [TestUserReserve / circulation].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (5, 'Intro to Algorithms', 'Cormen'),
            (1, 1, '2024-0001', 'CS', 'active'),
            None,  # no existing reservation
            (55, 5, 1, 1, 1, 'daily_circulation', 'borrow', '2026-08-01', '2026-08-02', None, 0, None, False, 'active'),  # active loan for book 5
        ]
        resp = student_client.post('/user/reserve', data={'book_id': 5})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0


class TestUserReturn:
    def test_return_requires_login(self, client, mock_db):
        """Validates return requires login `/user/return` (expects 302) [TestUserReturn / circulation].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = client.post('/user/return', data={'circulation_id': 55})
        assert resp.status_code == 302
        assert '/login' in resp.location

    def test_returns_require_desk(self, student_client, mock_db):
        # All returns need librarian approval at the desk: self-service
        # check-in is disabled, so even a valid daily loan writes nothing.
        """Validates returns require desk `/user/return` as student (expects 302) [TestUserReturn / circulation].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (55, 10, 1, '2026-08-02', 'active', 'daily_circulation'),
        ]
        resp = student_client.post('/user/return', data={'circulation_id': 55})
        assert resp.status_code == 302
        assert '/user/profile' in resp.location
        assert mock_db['execute'].call_count == 0

    def test_overnight_self_return_blocked(self, student_client, mock_db):
        """Validates overnight self return blocked `/user/return` as student (expects 302) [TestUserReturn / circulation].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].return_value = (55, 10, 1, '2026-08-02', 'active', 'overnight')
        resp = student_client.post('/user/return', data={'circulation_id': 55})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_return_other_users_loan_rejected(self, student_client, mock_db):
        """Validates return other users loan rejected `/user/return` as student (expects 302) [TestUserReturn / circulation].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].return_value = None
        resp = student_client.post('/user/return', data={'circulation_id': 99})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_return_invalid_record_id(self, student_client, mock_db):
        """Validates return invalid record id `/user/return` as student (expects 302) [TestUserReturn / circulation].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        resp = student_client.post('/user/return', data={'circulation_id': 'not-an-int'})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_return_never_computes_fine(self, student_client, mock_db):
        # Desk-only rule: not even an overdue daily loan is touched here.
        """Validates return never computes fine `/user/return` as student (expects 302) [TestUserReturn / circulation].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].side_effect = [
            (55, 10, 1, '2026-07-01', 'overdue', 'daily_circulation'),
        ]
        resp = student_client.post('/user/return', data={'circulation_id': 55})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0


class TestUserOverview:
    def test_profile_shows_notification_button_and_no_hardcoded_alert(self, student_client, mock_db):
        """Validates profile shows notification button and no hardcoded alert `/user/profile` as student (expects 200) [TestUserOverview / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].return_value = (1, 1, '2024-0001', 'CS', 'active')  # get_borrower_by_user
        mock_db['fetch_all'].return_value = [
            (1, 'Your reserved book is ready', 'hold_ready', None, '2026-08-10 09:00:00'),
        ]
        resp = student_client.get('/user/profile')
        assert resp.status_code == 200
        assert b'Notifications' in resp.data
        assert b'The Pragmatic Programmer' not in resp.data
        assert b'was due yesterday' not in resp.data

    def test_profile_borrowing_card_has_return_button(self, student_client, mock_db):
        """Validates profile borrowing card has return button `/user/profile` as student (expects 200) [TestUserOverview / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].return_value = (1, 1, '2024-0001', 'CS', 'active')
        mock_db['fetch_all'].return_value = [
            (55, date(2026, 8, 1), date(2026, 8, 2), 'daily_circulation', 'active',
             'Intro to Algorithms', '2024-00123'),
        ]
        resp = student_client.get('/user/profile')
        assert resp.status_code == 200
        assert b'Intro to Algorithms' in resp.data
        assert b'View Details' in resp.data
        # Desk-only returns: no self-service return form anywhere; the
        # details modal points at the circulation desk instead.
        assert b'/user/return' not in resp.data
        assert b'circulation desk' in resp.data

    def test_profile_overnight_shows_no_return_button(self, student_client, mock_db):
        """Validates profile overnight shows no return button `/user/profile` as student (expects 200) [TestUserOverview / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].return_value = (1, 1, '2024-0001', 'CS', 'active')
        mock_db['fetch_all'].return_value = [
            (55, date(2026, 8, 1), date(2026, 8, 2), 'overnight', 'active',
             'Intro to Algorithms', '2024-00123'),
        ]
        resp = student_client.get('/user/profile')
        assert resp.status_code == 200
        assert b'Intro to Algorithms' in resp.data
        assert b'Return at desk' in resp.data
        assert b'View Details' not in resp.data

    def test_history_lists_transactions_and_requests(self, student_client, mock_db):
        """Validates history lists transactions and requests `/user/history` as student (expects 200) [TestUserOverview / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].return_value = (1, 1, '2024-0001', 'CS', 'active')
        mock_db['fetch_all'].return_value = [
            (55, date(2026, 8, 1), date(2026, 8, 2), None, 'overnight',
             'active', 0, 'Intro to Algorithms', 'Cormen', '2024-00123'),
        ]
        resp = student_client.get('/user/history')
        assert resp.status_code == 200
        assert b'Intro to Algorithms' in resp.data
        assert b'Borrowings &amp; Returns' in resp.data


class TestBookInfoLabels:
    def test_book_info_shows_borrow_when_available(self, client, mock_db):
        """Validates book info shows borrow when available `/book/1` (expects 200) [TestBookInfoLabels / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].return_value = (1, 'Intro to Algorithms', 'Cormen', '3rd', 'MIT Press', 2022,
                                             'CS', 'QA76', '978-x', 'Book', 'desc', 'active', '2026-01-01')
        mock_db['fetch_all'].side_effect = [
            [(10, '2024-00123', 1, 1, '2026-01-10', 'purchase')],  # accessions
            [],                                                     # no borrowed ids
            [],                                                     # no borrowers
        ]
        resp = client.get('/book/1')
        assert resp.status_code == 200
        assert b'Borrow' in resp.data
        assert b'Available in Library' in resp.data

    def test_book_info_shows_reserve_when_borrowed_by_someone_else(self, student_client, mock_db):
        """Validates book info shows reserve when borrowed by someone else `/book/1` as student (expects 200) [TestBookInfoLabels / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].return_value = (1, 'Intro to Algorithms', 'Cormen', '3rd', 'MIT Press', 2022,
                                             'CS', 'QA76', '978-x', 'Book', 'desc', 'active', '2026-01-01')
        mock_db['fetch_all'].side_effect = [
            [(10, '2024-00123', 1, 1, '2026-01-10', 'purchase')],  # accessions
            [(10,)],                                                # accession 10 is on loan
            [(10, 99)],                                             # borrowed by another user
        ]
        resp = student_client.get('/book/1')
        assert resp.status_code == 200
        assert b'Reserve' in resp.data
        assert b'Not Available' in resp.data

    def test_book_info_shows_borrowed_for_current_borrower(self, student_client, mock_db):
        """Validates book info shows borrowed for current borrower `/book/1` as student (expects 200) [TestBookInfoLabels / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].return_value = (1, 'Intro to Algorithms', 'Cormen', '3rd', 'MIT Press', 2022,
                                             'CS', 'QA76', '978-x', 'Book', 'desc', 'active', '2026-01-01')
        mock_db['fetch_all'].side_effect = [
            [(10, '2024-00123', 1, 1, '2026-01-10', 'purchase')],  # accessions
            [(10,)],                                                # accession 10 is on loan
            [(10, 1)],                                              # borrowed by the current user
        ]
        resp = student_client.get('/book/1')
        assert resp.status_code == 200
        # Current user already holds this book -> Borrowed state, no borrow/reserve actions.
        assert b'Borrowed</button>' in resp.data
        assert b'/user/reserve' not in resp.data

    def test_book_info_blocks_second_borrow_when_copy_available(self, student_client, mock_db):
        """Validates book info blocks second borrow when copy available `/book/1` as student (expects 200) [TestBookInfoLabels / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].return_value = (1, 'Intro to Algorithms', 'Cormen', '3rd', 'MIT Press', 2022,
                                             'CS', 'QA76', '978-x', 'Book', 'desc', 'active', '2026-01-01')
        mock_db['fetch_all'].side_effect = [
            [(10, '2024-00123', 1, 1, '2026-01-10', 'purchase'),
             (11, '2024-00124', 1, 1, '2026-01-10', 'purchase')],  # two copies
            [(10,)],  # copy 10 on loan (held by current user), copy 11 free
            [(10, 1)],
        ]
        resp = student_client.get('/book/1')
        assert resp.status_code == 200
        assert b'Borrowed</button>' in resp.data
        assert b'onclick="openBorrowModal' not in resp.data

    def test_book_info_has_no_header_borrow_button(self, student_client, mock_db):
        """Validates book info has no header borrow button `/book/1` as student (expects 200) [TestBookInfoLabels / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].return_value = (1, 'Intro to Algorithms', 'Cormen', '3rd', 'MIT Press', 2022,
                                             'CS', 'QA76', '978-x', 'Book', 'desc', 'active', '2026-01-01')
        mock_db['fetch_all'].side_effect = [
            [(10, '2024-00123', 1, 1, '2026-01-10', 'purchase')],  # accessions
            [],                                                     # no borrowed ids
            [],                                                     # no borrowers
        ]
        resp = student_client.get('/book/1')
        assert resp.status_code == 200
        assert b'openBorrowModalBtn' not in resp.data

class TestPayFine:
    FINE = (55, 5, 25.0, False)  # (circulation_id, borrower_id, amount, fine_paid)

    def test_mark_fine_paid_sql(self, mock_db):
        """Validates mark fine paid sql [TestPayFine / circulation].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (UPDATE).
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        from app.circulation.models import mark_fine_paid
        mark_fine_paid(55, updated_by=3)
        query, params = mock_db['execute'].call_args[0]
        assert 'UPDATE circulation_records' in query
        assert 'fine_paid = TRUE' in query
        assert 'updated_at' in query
        assert 'updated_by' in query
        assert params == (3, 55)

    def test_unpaid_filter_in_fine_queries(self, mock_db):
        """Validates unpaid filter in fine queries [TestPayFine / circulation].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        from app.circulation.models import get_fines_by_borrower, get_total_fines
        mock_db['fetch_all'].return_value = []
        mock_db['fetch_one'].return_value = (0,)
        get_fines_by_borrower(5)
        assert 'fine_paid = FALSE' in mock_db['fetch_all'].call_args[0][0]
        get_total_fines(5)
        assert 'fine_paid = FALSE' in mock_db['fetch_one'].call_args[0][0]

    def test_pay_fine_success(self, librarian_client, mock_db):
        """Validates pay fine success `/librarian/users/4/fines/55/pay` as librarian (expects 302) [TestPayFine / circulation].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        from unittest.mock import patch
        with patch('app.auth.models.get_user_by_id', return_value=(4, 'a@mcst.edu.ph', 'Admin', 'A')), \
             patch('app.circulation.routes.get_borrower_by_user', return_value=(5, 4, 'ID-1', None, None, None)), \
             patch('app.circulation.routes.get_fine_record', return_value=self.FINE), \
             patch('app.circulation.routes.log_activity') as log_act:
            resp = librarian_client.post('/librarian/users/4/fines/55/pay')
        assert resp.status_code == 302
        assert '/librarian/users/4/history' in resp.location
        update = mock_db['execute'].call_args[0]
        assert 'fine_paid = TRUE' in update[0]
        assert 'circulation:fine_paid:55' in log_act.call_args[0][1]

    def test_pay_fine_already_paid(self, librarian_client, mock_db):
        """Validates pay fine already paid `/librarian/users/4/fines/55/pay` as librarian (expects 200) [TestPayFine / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        from unittest.mock import patch
        with patch('app.auth.models.get_user_by_id', return_value=(4, 'a@mcst.edu.ph', 'Admin', 'A')), \
             patch('app.circulation.routes.get_borrower_by_user', return_value=(5, 4, 'ID-1', None, None, None)), \
             patch('app.circulation.routes.get_fine_record', return_value=(55, 5, 25.0, True)), \
             patch('app.circulation.routes.mark_fine_paid') as mark:
            resp = librarian_client.post('/librarian/users/4/fines/55/pay', follow_redirects=True)
        assert resp.status_code == 200
        mark.assert_not_called()
        assert b'already paid' in resp.data

    def test_pay_fine_wrong_borrower(self, librarian_client, mock_db):
        """Validates pay fine wrong borrower `/librarian/users/4/fines/55/pay` as librarian (expects 302) [TestPayFine / circulation].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        from unittest.mock import patch
        with patch('app.auth.models.get_user_by_id', return_value=(4, 'a@mcst.edu.ph', 'Admin', 'A')), \
             patch('app.circulation.routes.get_borrower_by_user', return_value=(5, 4, 'ID-1', None, None, None)), \
             patch('app.circulation.routes.get_fine_record', return_value=(55, 9, 25.0, False)), \
             patch('app.circulation.routes.mark_fine_paid') as mark:
            resp = librarian_client.post('/librarian/users/4/fines/55/pay')
        assert resp.status_code == 302
        mark.assert_not_called()

    def test_pay_fine_student_forbidden(self, student_client, mock_db):
        """Validates pay fine student forbidden `/librarian/users/4/fines/55/pay` as student (expects 302) [TestPayFine / circulation].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        resp = student_client.post('/librarian/users/4/fines/55/pay')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location
        # Only write is the denial audit row — the fine itself is untouched.
        assert mock_db['execute'].call_count == 1
        query, params = mock_db['execute'].call_args[0]
        assert 'INSERT INTO audit_trail' in query
        assert params[0] == '1'
        assert params[1].startswith('security:denied:')

    def test_history_detail_shows_mark_paid(self, librarian_client, mock_db):
        """Validates history detail shows mark paid `/librarian/users/4/history` as librarian (expects 200) [TestPayFine / circulation].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        fine_row = (55, '2026-08-01', '2026-08-05', '2026-08-10', 25.0, 'Book A', 'ACC-1')
        mock_db['fetch_one'].side_effect = [
            (4, 'a@mcst.edu.ph', 'Admin', 'Test Admin'),
            (5, 4, 'ID-1', 'CS', None, 'active'),
            (25.0,),
        ]
        mock_db['fetch_all'].side_effect = [[], [], [], [fine_row]]
        resp = librarian_client.get('/librarian/users/4/history')
        assert resp.status_code == 200
        assert b'Mark paid' in resp.data
        assert b'/librarian/users/4/fines/55/pay' in resp.data


class TestStaffInheritFacultySettings:
    """Admin/Librarian inherit faculty borrowing settings (max borrows, overnight due)."""

    def test_borrow_limit(self, app):
        """Validates staff borrow limit equals faculty limit [TestStaffInheritFacultySettings / circulation].
    If fails: likely _borrow_limit branching changed so Admin/Librarian no longer inherit faculty settings.
    Failure indicates staff borrowing is capped by the wrong (student) limit."""
        from app.circulation.routes import _borrow_limit
        with app.test_request_context():
            app.config['MAX_BORROW_LIMIT_STUDENT'] = 3
            app.config['MAX_BORROW_LIMIT_FACULTY'] = 5
            assert _borrow_limit('Student') == 3
            assert _borrow_limit('Faculty') == 5
            assert _borrow_limit('Admin') == 5
            assert _borrow_limit('Librarian') == 5

    def test_overnight_due_date(self, app):
        """Validates staff overnight due equals faculty due [TestStaffInheritFacultySettings / circulation].
    If fails: likely _compute_due_date branching changed so Admin/Librarian no longer inherit faculty due days.
    Failure indicates staff loans get the wrong (student) loan period."""
        from app.circulation.routes import _compute_due_date
        with app.test_request_context():
            app.config['OVERNIGHT_DUE_DAYS_STUDENT'] = 1
            app.config['OVERNIGHT_DUE_DAYS_FACULTY'] = 7
            faculty_due = _compute_due_date('overnight', 'Faculty')
            assert _compute_due_date('overnight', 'Admin') == faculty_due
            assert _compute_due_date('overnight', 'Librarian') == faculty_due
            assert _compute_due_date('overnight', 'Student') != faculty_due

    @staticmethod
    def _profile_mocks(mock_db, uid, email, role, name, borrower_id, id_number):
        """Test helper _profile_mocks: build mocked data or DB stub for the test."""
        mock_db['fetch_one'].side_effect = [
            (uid, email, role, name, borrower_id, id_number, 'HQ', '555', 'active'),  # profile
            (borrower_id, uid, id_number, 'HQ', '555', 'active', None, None),  # borrower
            (0,),  # count_active_loans
            (0,),  # count_unread_notifications
            (0,),  # get_total_fines
        ]
        mock_db['fetch_all'].return_value = []

    def test_admin_profile_shows_faculty_limit(self, admin_client, mock_db):
        """Validates admin profile shows faculty borrow limit `/user/profile` as admin (expects 200) [TestStaffInheritFacultySettings / circulation].
    If fails: likely user_profile borrow-limit branching changed so Admin falls back to the student limit.
    Failure indicates staff see (and are capped by) the wrong limit on their profile."""
        self._profile_mocks(mock_db, 4, 'admin@mcst.edu.ph', 'Admin', 'Test Admin', 9, 'ADM-001')
        resp = admin_client.get('/user/profile')
        assert resp.status_code == 200
        assert b'(0/5 books)' in resp.data

    def test_librarian_profile_shows_faculty_limit(self, librarian_client, mock_db):
        """Validates librarian profile shows faculty borrow limit `/user/profile` as librarian (expects 200) [TestStaffInheritFacultySettings / circulation].
    If fails: likely user_profile borrow-limit branching changed so Librarian falls back to the student limit.
    Failure indicates staff see (and are capped by) the wrong limit on their profile."""
        self._profile_mocks(mock_db, 3, 'librarian@mcst.edu.ph', 'Librarian', 'Test Librarian', 8, 'LIB-001')
        resp = librarian_client.get('/user/profile')
        assert resp.status_code == 200
        assert b'(0/5 books)' in resp.data

    def test_student_profile_shows_student_limit(self, student_client, mock_db):
        """Validates student profile still shows student borrow limit `/user/profile` as student (expects 200) [TestStaffInheritFacultySettings / circulation].
    If fails: likely user_profile borrow-limit branching changed so Student no longer gets the student limit.
    Failure indicates the staff-inherit-faculty change leaked into student limits."""
        self._profile_mocks(mock_db, 1, 'student@mcst.edu.ph', 'Student', 'Test Student', 1, '2024-0001')
        resp = student_client.get('/user/profile')
        assert resp.status_code == 200
        assert b'(0/3 books)' in resp.data
