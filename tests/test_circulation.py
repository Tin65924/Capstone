"""Tests for the Circulation module: desk borrow/return, reservations, user borrow/reserve, RBAC, availability labels."""

from datetime import date


class TestCirculationAccess:
    def test_student_forbidden_from_circulation(self, student_client):
        resp = student_client.get('/librarian/circulation')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_faculty_forbidden_from_circulation(self, faculty_client):
        resp = faculty_client.get('/librarian/circulation')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_student_forbidden_from_reservations(self, student_client):
        resp = student_client.get('/librarian/reservations')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location


class TestCirculationPage:
    def test_librarian_circulation_renders(self, librarian_client, mock_db):
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
        mock_db['fetch_one'].return_value = (1, '2024-0001', 'CS', 'active', 'Test Student', 1, 'Student')
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/circulation?search=2024-0001')
        assert resp.status_code == 200
        assert b'Test Student' in resp.data
        assert b'bg-blue-100 text-blue-700">Student</span>' in resp.data
        assert b'Limit: 3 books' in resp.data

    def test_borrower_lookup_not_found(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/circulation?search=9999')
        assert resp.status_code == 200
        assert b'No borrower found' in resp.data


class TestDeskBorrow:
    def test_borrow_success(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [
            (1, '2024-0001', 'CS', 'active', 'Test Student', 1, 'Student'),  # borrower details
            (10, '2024-00123', 5, 1, '2024-01-10', 'purchase'),              # accession
            None,                                                            # no active loan
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
        mock_db['fetch_one'].side_effect = [
            (1, '2024-0001', 'CS', 'active', 'Test Student', 1, 'Student'),
            (10, '2024-00123', 5, 1, '2024-01-10', 'purchase'),
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
        mock_db['fetch_one'].side_effect = [
            (1, '2024-0001', 'CS', 'active', 'Test Student', 1, 'Student'),
            (10, '2024-00123', 5, 1, '2024-01-10', 'purchase'),
            None,
            (3,),  # count active loans == student limit
        ]
        resp = librarian_client.post('/librarian/circulation/borrow', data={
            'borrower_id': 1,
            'accession_number': '2024-00123',
            'borrow_type': 'overnight',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0


class TestDeskReturn:
    def test_return_computes_fine(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [
            (10, '2024-00123', 5, 1, '2024-01-10', 'purchase'),       # accession
            (55, 10, 1, 1, 5, 'overnight', 'borrow', '2026-08-01', '2026-08-02', None, 0, None, False, 'active'),  # active loan
            (date(2026, 8, 1), date(2026, 8, 5)),                     # calculate_fine due/returned
            None,                                                      # no waiting reservation
        ]
        resp = librarian_client.post('/librarian/circulation/return', data={
            'accession_number': '2024-00123',
        })
        assert resp.status_code == 302
        call_args = mock_db['execute'].call_args_list[0]
        assert 'UPDATE circulation_records' in call_args[0][0]
        assert 'returned' in call_args[0][1]

    def test_return_not_borrowed_rejected(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [
            (10, '2024-00123', 5, 1, '2024-01-10', 'purchase'),
            None,  # no active loan
        ]
        resp = librarian_client.post('/librarian/circulation/return', data={
            'accession_number': '2024-00123',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0


class TestReservationLifecycle:
    def test_allocate_writes_notification(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [
            (9, 5, 2, 1, '2026-08-01 10:00:00', 'waiting', None),  # reservation
            (10, '2024-00123', 5, 1, '2024-01-10', 'purchase'),    # available copy
            (2, '2024-0002', 'CS', 'active', 'Test Student', 1, 'Student'),  # borrower details
            (0,),                                                  # count active loans
        ]
        resp = librarian_client.post('/librarian/reservations/9/allocate')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count >= 2
        notification_call = mock_db['execute'].call_args_list[1]
        assert 'INSERT INTO notification_log' in notification_call[0][0]

    def test_allocate_rejected_when_no_available_copy(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [
            (9, 5, 2, 1, '2026-08-01 10:00:00', 'waiting', None),  # reservation
            None,                                                   # no available copy
        ]
        resp = librarian_client.post('/librarian/reservations/9/allocate')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_allocate_rejected_when_not_waiting(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (9, 5, 2, 1, '2026-08-01 10:00:00', 'claimed', None)
        resp = librarian_client.post('/librarian/reservations/9/allocate')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_claim_requires_allocated(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (9, 5, 2, 1, '2026-08-01 10:00:00', 'waiting', None)
        resp = librarian_client.post('/librarian/reservations/9/claim')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_claim_success(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [
            (9, 5, 2, 1, '2026-08-01 10:00:00', 'allocated', '2026-08-03 10:00:00'),  # reservation
            (10, '2024-00123', 5, 1, '2024-01-10', 'purchase'),                        # available copy
            (2, '2024-0002', 'CS', 'active', 'Test Student', 1, 'Student'),            # borrower details
            (0,),                                                                      # count active loans
        ]
        resp = librarian_client.post('/librarian/reservations/9/claim')
        assert resp.status_code == 302
        first_call = mock_db['execute'].call_args_list[0]
        assert 'INSERT INTO circulation_records' in first_call[0][0]
        assert 'overnight' in first_call[0][1]
        second_call = mock_db['execute'].call_args_list[1]
        assert "reservation_status = 'claimed'" in second_call[0][0]

    def test_claim_rejected_when_no_available_copy(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [
            (9, 5, 2, 1, '2026-08-01 10:00:00', 'allocated', '2026-08-03 10:00:00'),  # reservation
            None,                                                                      # no available copy
        ]
        resp = librarian_client.post('/librarian/reservations/9/claim')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_claim_rejected_when_borrower_at_limit(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [
            (9, 5, 2, 1, '2026-08-01 10:00:00', 'allocated', '2026-08-03 10:00:00'),  # reservation
            (10, '2024-00123', 5, 1, '2024-01-10', 'purchase'),                        # available copy
            (2, '2024-0002', 'CS', 'active', 'Test Student', 1, 'Student'),            # borrower details
            (3,),                                                                      # count == student limit
        ]
        resp = librarian_client.post('/librarian/reservations/9/claim')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_allocate_rejected_when_borrower_at_limit(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [
            (9, 5, 2, 1, '2026-08-01 10:00:00', 'waiting', None),  # reservation
            (10, '2024-00123', 5, 1, '2024-01-10', 'purchase'),    # available copy
            (2, '2024-0002', 'CS', 'active', 'Test Student', 1, 'Student'),  # borrower details
            (3,),                                                  # count == limit
        ]
        resp = librarian_client.post('/librarian/reservations/9/allocate')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_expire_success(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (9, 5, 2, 1, '2026-08-01 10:00:00', 'allocated', '2026-08-03 10:00:00')
        resp = librarian_client.post('/librarian/reservations/9/expire')
        assert resp.status_code == 302
        call_args = mock_db['execute'].call_args_list[0]
        assert "reservation_status = 'expired'" in call_args[0][0]

    def test_stats_sum_correct_status_columns(self, librarian_client, mock_db):
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


class TestUserBorrow:
    def test_overnight_borrow_creates_reservation_not_loan(self, student_client, mock_db):
        mock_db['fetch_one'].side_effect = [
            (5, 'Intro to Algorithms', 'Cormen'),     # get_book_by_id
            (1, 1, '2024-0001', 'CS', 'active'),       # get_borrower_by_user
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
        mock_db['fetch_one'].side_effect = [
            (5, 'Intro to Algorithms', 'Cormen'),
            (1, 1, '2024-0001', 'CS', 'active'),
            (9, 5, 1, 1, '2026-08-01 10:00:00', 'waiting', None),  # existing reservation
        ]
        resp = student_client.post('/user/borrow', data={
            'book_id': 5,
            'borrow_type': 'overnight',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_overnight_borrow_over_limit_rejected(self, student_client, mock_db):
        mock_db['fetch_one'].side_effect = [
            (5, 'Intro to Algorithms', 'Cormen'),
            (1, 1, '2024-0001', 'CS', 'active'),
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
        mock_db['fetch_one'].side_effect = [
            (5, 'Intro to Algorithms', 'Cormen'),     # get_book_by_id
            (1, 1, '2024-0001', 'CS', 'active'),       # get_borrower_by_user
            (10, '2024-00123', 5, 1, '2024-01-10', 'purchase'),  # available accession
            (0,),                                       # count active loans
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
        resp = client.post('/user/borrow', data={'book_id': 5})
        assert resp.status_code == 302
        assert '/login' in resp.location

    def test_faculty_over_limit_is_5(self, faculty_client, mock_db):
        mock_db['fetch_one'].side_effect = [
            (5, 'Intro to Algorithms', 'Cormen'),
            (2, 2, '2024-0002', 'CS', 'active'),       # faculty borrower
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
        mock_db['fetch_one'].side_effect = [
            (5, 'Intro to Algorithms', 'Cormen'),
            (2, 2, '2024-0002', 'CS', 'active'),
            None,
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


class TestUserReserve:
    def test_student_reserves_book(self, student_client, mock_db):
        mock_db['fetch_one'].side_effect = [
            (5, 'Intro to Algorithms', 'Cormen'),     # get_book_by_id
            (1, 1, '2024-0001', 'CS', 'active'),       # get_borrower_by_user
            None,                                      # no existing reservation
            None,                                      # no available accession
            (1,),                                      # next queue position
        ]
        resp = student_client.post('/user/reserve', data={'book_id': 5})
        assert resp.status_code == 302
        call_args = mock_db['execute'].call_args_list[0]
        assert 'INSERT INTO reservation_queue' in call_args[0][0]

    def test_duplicate_reservation_rejected(self, student_client, mock_db):
        mock_db['fetch_one'].side_effect = [
            (5, 'Intro to Algorithms', 'Cormen'),
            (1, 1, '2024-0001', 'CS', 'active'),
            (9, 5, 1, 1, '2026-08-01 10:00:00', 'waiting', None),  # existing reservation
        ]
        resp = student_client.post('/user/reserve', data={'book_id': 5})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_reserve_when_available_redirects_to_borrow(self, student_client, mock_db):
        mock_db['fetch_one'].side_effect = [
            (5, 'Intro to Algorithms', 'Cormen'),
            (1, 1, '2024-0001', 'CS', 'active'),
            None,                                       # no existing reservation
            (10, '2024-00123', 5, 1, '2024-01-10', 'purchase'),  # a copy is available
        ]
        resp = student_client.post('/user/reserve', data={'book_id': 5})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0


class TestUserReturn:
    def test_return_requires_login(self, client, mock_db):
        resp = client.post('/user/return', data={'circulation_id': 55})
        assert resp.status_code == 302
        assert '/login' in resp.location

    def test_returns_own_active_loan(self, student_client, mock_db):
        mock_db['fetch_one'].side_effect = [
            (55, 10, 1, '2026-08-02', 'active', 'daily_circulation'),  # get_active_loan_by_id_and_user
            (date(2026, 8, 1), date(2026, 8, 2)),                       # calculate_fine due/returned
            None,                                                        # no waiting reservation
        ]
        resp = student_client.post('/user/return', data={'circulation_id': 55})
        assert resp.status_code == 302
        assert '/user/profile' in resp.location
        call_args = mock_db['execute'].call_args_list[0]
        assert 'UPDATE circulation_records' in call_args[0][0]
        assert 'returned' in call_args[0][1]

    def test_overnight_self_return_blocked(self, student_client, mock_db):
        mock_db['fetch_one'].return_value = (55, 10, 1, '2026-08-02', 'active', 'overnight')
        resp = student_client.post('/user/return', data={'circulation_id': 55})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_return_other_users_loan_rejected(self, student_client, mock_db):
        mock_db['fetch_one'].return_value = None
        resp = student_client.post('/user/return', data={'circulation_id': 99})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_return_invalid_record_id(self, student_client, mock_db):
        resp = student_client.post('/user/return', data={'circulation_id': 'not-an-int'})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_return_computes_fine(self, student_client, mock_db):
        mock_db['fetch_one'].side_effect = [
            (55, 10, 1, '2026-07-01', 'overdue', 'daily_circulation'),  # overdue loan
            (date(2026, 7, 1), date(2026, 7, 6)),                       # 5 days late
            None,                                                        # no waiting reservation
        ]
        resp = student_client.post('/user/return', data={'circulation_id': 55})
        assert resp.status_code == 302
        call_args = mock_db['execute'].call_args_list[0]
        assert 'UPDATE circulation_records' in call_args[0][0]
        assert call_args[0][1][2] == 50.0


class TestUserOverview:
    def test_profile_shows_notification_button_and_no_hardcoded_alert(self, student_client, mock_db):
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
        mock_db['fetch_one'].return_value = (1, 1, '2024-0001', 'CS', 'active')
        mock_db['fetch_all'].return_value = [
            (55, date(2026, 8, 1), date(2026, 8, 2), 'daily_circulation', 'active',
             'Intro to Algorithms', '2024-00123'),
        ]
        resp = student_client.get('/user/profile')
        assert resp.status_code == 200
        assert b'Intro to Algorithms' in resp.data
        assert b'View Details' in resp.data
        assert b'/user/return' in resp.data

    def test_profile_overnight_shows_no_return_button(self, student_client, mock_db):
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
        mock_db['fetch_one'].return_value = (1, 'Intro to Algorithms', 'Cormen', '3rd', 'MIT Press', 2022,
                                             'CS', 'QA76', '978-x', 'Book', 'desc', 'active', '2026-01-01')
        mock_db['fetch_all'].side_effect = [
            [(10, '2024-00123', 1, 1, '2026-01-10', 'purchase')],  # accessions
            [(10,)],                                                # accession 10 is on loan
            [(10, 1)],                                              # borrowed by the current user
        ]
        resp = student_client.get('/book/1')
        assert resp.status_code == 200
        assert b'>Reserve</button>' not in resp.data
        assert b'Borrowed</button>' in resp.data

    def test_book_info_has_no_header_borrow_button(self, student_client, mock_db):
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
