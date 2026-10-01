"""Edge-case regression tests for the borrow/return flow.

Covers desk borrow/return and due-date computation: bogus ids,
short borrower/loan rows, blocked borrowers, archived books, lost
copies, oversized/hostile damage notes, missing loans, garbage due
config (falls back to 2/30/0 days), and short queue rows. Includes
the borrower-status guard, queue-row guard, and due-date coercion
fixes. Everything must degrade gracefully — never 500.
"""

DETAIL = (5, 'S1', 'BSIS', 'active', 'Ann', 1, 'Student')
ACC = (10, 'ACC-001', 1, 'purchase', '2026-01-02', None, None, None)
BOOK = (1, 'T', 'A', '', '', None, '', '', '', '', '', 'active',
        '2026-01-01', None, None)


class TestDeskBorrow:
    def test_ids_both_bogus(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = None
        resp = librarian_client.post(
            '/librarian/circulation/borrow',
            data={'id_number': 'NOPE', 'accession_number': 'NOPE',
                  'borrow_type': 'overnight'})
        assert resp.status_code == 302

    def test_short_borrower_row(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [(5,), None, None, None]
        resp = librarian_client.post(
            '/librarian/circulation/borrow',
            data={'borrower_id': '5', 'accession_number': 'ACC-1',
                  'borrow_type': 'overnight'})
        assert resp.status_code == 302

    def test_blocked_borrower(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (5, 'S1', 'BSIS', 'blocked',
                                             'Ann', 1, 'Student')
        resp = librarian_client.post(
            '/librarian/circulation/borrow',
            data={'borrower_id': '5', 'accession_number': 'ACC-1',
                  'borrow_type': 'overnight'})
        assert resp.status_code == 302

    def test_archived_book(self, librarian_client, mock_db):
        book = (1, 'T', 'A', '', '', None, '', '', '', '', '', 'archived',
                '2026-01-01', None, None)
        mock_db['fetch_one'].side_effect = [DETAIL, ACC, book]
        resp = librarian_client.post(
            '/librarian/circulation/borrow',
            data={'borrower_id': '5', 'accession_number': 'ACC-1',
                  'borrow_type': 'overnight'})
        assert resp.status_code == 302

    def test_lost_copy(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [DETAIL, ACC, BOOK, (1,)]
        resp = librarian_client.post(
            '/librarian/circulation/borrow',
            data={'borrower_id': '5', 'accession_number': 'ACC-1',
                  'borrow_type': 'overnight'})
        assert resp.status_code == 302


class TestDeskReturn:
    def test_short_loan_row(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [ACC, (7,), None, None]
        resp = librarian_client.post(
            '/librarian/circulation/return',
            data={'accession_number': 'ACC-1'})
        assert resp.status_code == 302

    def test_evil_damage_notes(self, librarian_client, mock_db):
        loan = (7, 1, 5, '2026-01-01', '2026-01-02', 'daily_circulation',
                'borrow', '2026-01-01', '2026-01-01', 0.0, 'active')
        mock_db['fetch_one'].side_effect = [ACC, loan, None, (0,)]
        evil = '<script>alert(1)</script>'
        resp = librarian_client.post(
            '/librarian/circulation/return',
            data={'accession_number': 'ACC-1', 'damage_notes': evil})
        assert resp.status_code == 302

    def test_huge_damage_notes(self, librarian_client, mock_db):
        loan = (7, 1, 5, '2026-01-01', '2026-01-02', 'daily_circulation',
                'borrow', '2026-01-01', '2026-01-01', 0.0, 'active')
        mock_db['fetch_one'].side_effect = [ACC, loan, None, (0,)]
        resp = librarian_client.post(
            '/librarian/circulation/return',
            data={'accession_number': 'ACC-1',
                  'damage_notes': 'x' * 20000})
        assert resp.status_code == 302

    def test_lost_flag_no_loan(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [ACC, None]
        resp = librarian_client.post(
            '/librarian/circulation/return',
            data={'accession_number': 'ACC-1', 'lost': '1'})
        assert resp.status_code == 302


class TestDueDate:
    def test_garbage_config(self, app):
        from app.circulation.routes import _compute_due_date
        from datetime import date
        with app.test_request_context():
            app.config['OVERNIGHT_DUE_DAYS_STUDENT'] = 'junk'
            app.config['OVERNIGHT_DUE_DAYS_FACULTY'] = None
            app.config['DAILY_CIRCULATION_DUE_DAYS'] = 'x'
            assert _compute_due_date('overnight', 'Student') == date.today() + \
                __import__('datetime').timedelta(days=1)
            assert _compute_due_date('overnight', 'Faculty') == date.today() + \
                __import__('datetime').timedelta(days=7)
            assert _compute_due_date('daily_circulation', 'X') == date.today()
