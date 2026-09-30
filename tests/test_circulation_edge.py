"""Edge-case regression tests for Circulation Management.

Covers `/librarian/circulation`, desk borrow/return helpers, user
returns, fine payment, and borrower history: empty/`None` models,
hostile ids and filters, ownership and state guards on returns,
fine validation (wrong borrower, zero, paid, missing), fine-math
edges, XSS rows, and the staff auth matrix. Includes the `recent`
None-guard, the short-loan guard, and the fine-display `float`
hardening. Everything must degrade gracefully — never 500.
"""

LOAN = (7, 1, 5, '2026-01-01', '2026-01-02', 'daily_circulation', 'borrow',
        '2026-01-01', '2026-01-01', 0.0, 'active')


class TestUserReturn:
    def test_missing_id(self, student_client):
        assert student_client.post('/user/return', data={}).status_code == 302

    def test_other_users_loan(self, student_client, mock_db):
        mock_db['fetch_one'].return_value = None
        assert student_client.post(
            '/user/return', data={'circulation_id': 7}).status_code == 302

    def test_huge_id(self, student_client, mock_db):
        mock_db['fetch_one'].return_value = None
        assert student_client.post(
            '/user/return',
            data={'circulation_id': 999999999}).status_code == 302

    def test_overnight_blocked(self, student_client, mock_db):
        loan = (7, 1, 5, '2026-01-01', '2026-01-02', 'overnight', 'borrow',
                '2026-01-01', '2026-01-01', 0.0, 'active')
        mock_db['fetch_one'].return_value = loan
        assert student_client.post(
            '/user/return', data={'circulation_id': 7}).status_code == 302

    def test_short_loan_row(self, student_client, mock_db):
        mock_db['fetch_one'].return_value = (7,)
        assert student_client.post(
            '/user/return', data={'circulation_id': 7}).status_code == 302


class TestPayFine:
    def test_wrong_borrower(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [(4, 'a@x.ph', 'Student', 'N'),
                                            (5, 1, 'S1', 'BSIS', 'a', None,
                                             None, None),
                                            (9, 999, 50.0, False)]
        resp = librarian_client.post('/librarian/users/4/fines/9/pay')
        assert resp.status_code == 302

    def test_zero_fine(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [(4, 'a@x.ph', 'Student', 'N'),
                                            (5, 1, 'S1', 'BSIS', 'a', None,
                                             None, None),
                                            (9, 5, 0.0, False)]
        assert librarian_client.post(
            '/librarian/users/4/fines/9/pay').status_code == 302

    def test_already_paid(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [(4, 'a@x.ph', 'Student', 'N'),
                                            (5, 1, 'S1', 'BSIS', 'a', None,
                                             None, None),
                                            (9, 5, 25.0, True)]
        assert librarian_client.post(
            '/librarian/users/4/fines/9/pay').status_code == 302

    def test_missing_user_or_fine(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [None]
        assert librarian_client.post(
            '/librarian/users/999/fines/1/pay').status_code == 302
        mock_db['fetch_one'].side_effect = [(4, 'a@x.ph', 'Student', 'N'),
                                            None]
        assert librarian_client.post(
            '/librarian/users/4/fines/1/pay').status_code == 302

    def test_student_cannot_pay(self, student_client, mock_db):
        resp = student_client.post('/librarian/users/1/fines/1/pay')
        assert resp.status_code == 302
        writes = [c[0][0] for c in mock_db['execute'].call_args_list
                  if 'UPDATE' in c[0][0] and 'audit_trail' not in c[0][0]]
        assert writes == []


class TestFineCalc:
    def test_negative_days_zero(self, mock_db):
        from app.circulation.models import calculate_fine
        mock_db['fetch_one'].return_value = None
        assert calculate_fine(7, 5.0, 0) == 0.0

    def test_garbage_config(self, mock_db):
        from app.circulation.models import calculate_fine
        mock_db['fetch_one'].return_value = None
        assert calculate_fine(7, 'junk', 'junk') == 0.0


class TestHistory:
    def test_list_hostile_search(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = []
        for url in ('/librarian/users/history?q=' + 'x' * 2000,
                    '/librarian/users/history?q=<script>alert(1)</script>'):
            assert librarian_client.get(url).status_code == 200, url[:60]

    def test_evil_history_rows(self, librarian_client, mock_db):
        evil = '<script>alert(1)</script>'
        mock_db['fetch_all'].return_value = [(1, evil, 'e@x.ph', 'Student')]
        mock_db['fetch_one'].return_value = (1, 'e@x.ph', 'Student', 'N')
        body = librarian_client.get('/librarian/users/history').data.decode()
        assert evil not in body

    def test_detail_none_models(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = None
        assert librarian_client.get(
            '/librarian/users/4/history').status_code == 302


class TestCirculationPage:
    def test_none_models(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = None
        assert librarian_client.get('/librarian/circulation').status_code == 200

    def test_evil_loan_rows(self, librarian_client, mock_db):
        evil = '<img src=x onerror=alert(1)>'
        row = (7, '2026-01-01', '2026-01-02', 'overnight', 'active', evil,
               1, evil, 'ACC-1', 5)
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = [row]
        body = librarian_client.get('/librarian/circulation').data.decode()
        assert evil not in body

    def test_desk_borrow_blocked_archived(self, librarian_client, mock_db):
        book = (1, 'T', 'A', '', '', None, '', '', '', '', '', 'archived',
                '2026-01-01', None, None)
        mock_db['fetch_one'].side_effect = [
            (1, 'S1', 'BSIS', 'active', 'Ann', 1, 'Student'), book, None]
        resp = librarian_client.post(
            '/librarian/circulation/borrow',
            data={'id_number': 'S1', 'accession_number': 'ACC-1',
                  'borrow_type': 'overnight'})
        assert resp.status_code == 302
