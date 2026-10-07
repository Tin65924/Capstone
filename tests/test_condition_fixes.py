"""Regression tests for separated lost/damaged copy-condition workflows.

Return is a pure check-in now; mark-lost / mark-damaged (reason required)
are standalone librarian actions; the cataloging copies table shows Lost
vs Damaged separately with the damage reason. Mocked DB — no Postgres.
"""

from datetime import date

ACC = (10, 'ACC-001', 1, 'purchase', '2026-01-02', None, None, None)
LOAN = (7, 1, 5, '2026-01-01', '2026-01-02', 'daily_circulation', 'borrow',
        '2026-01-01', '2026-01-01', 0.0, 'active')
BOOK_ROW = (1, 'T', 'A', '', '', None, '', '', '', '', '', 'active',
            '2026-01-01', None, None)


def _non_audit_writes(mock_db):
    return [c[0][0] for c in mock_db['execute'].call_args_list
            if 'audit_trail' not in c[0][0]]


class TestPureReturn:
    def test_return_ignores_legacy_lost_damage_fields(
            self, librarian_client, mock_db):
        """Old return payloads (lost checkbox, damage notes) now behave
        as a plain check-in: loan closed, copy NOT flagged."""
        mock_db['fetch_one'].side_effect = [
            ACC,
            LOAN,
            (date(2026, 8, 1), date(2026, 8, 2), 'daily_circulation'),
            None,  # no waiting reservation
        ]
        resp = librarian_client.post(
            '/librarian/circulation/return',
            data={'accession_number': 'ACC-1',
                  'damage_notes': 'torn cover', 'lost': '1'})
        assert resp.status_code == 302
        updates = [c for c in mock_db['execute'].call_args_list
                   if 'UPDATE circulation_records' in c[0][0]]
        assert len(updates) == 1
        # return_book params: (returned, today, fine, damage, lost, by, id)
        assert updates[0][0][1][4] is False
        assert updates[0][0][1][3] is None
        inv = [c[0][0] for c in mock_db['execute'].call_args_list
               if 'inventory_status' in c[0][0]]
        assert inv == []

    def test_return_page_has_condition_card_not_lost_checkbox(
            self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/circulation').data.decode()
        assert 'Copy Condition' in body
        assert 'name="damage_notes"' not in body
        assert 'name="lost"' not in body


class TestMarkLost:
    def test_lost_with_loan_closes_it(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [
            ACC,
            LOAN,
            (date(2026, 8, 1), date(2026, 8, 2), 'daily_circulation'),
            None,  # no existing inventory row -> INSERT
        ]
        resp = librarian_client.post(
            '/librarian/circulation/accession/lost',
            data={'accession_number': 'ACC-1'})
        assert resp.status_code == 302
        stmts = _non_audit_writes(mock_db)
        assert any('UPDATE circulation_records' in s for s in stmts)
        assert any('INSERT INTO notification_log' in s for s in stmts)
        assert any('inventory_status' in s for s in stmts)

    def test_lost_without_loan(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [ACC, None, None]
        resp = librarian_client.post(
            '/librarian/circulation/accession/lost',
            data={'accession_number': 'ACC-1'})
        assert resp.status_code == 302
        stmts = _non_audit_writes(mock_db)
        assert not any('circulation_records' in s for s in stmts)
        assert any('inventory_status' in s for s in stmts)

    def test_lost_missing_accession(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = None
        resp = librarian_client.post(
            '/librarian/circulation/accession/lost',
            data={'accession_number': 'NOPE'})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0


class TestMarkDamaged:
    def test_reason_required(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = ACC
        resp = librarian_client.post(
            '/librarian/circulation/accession/damaged',
            data={'accession_number': 'ACC-1', 'notes': '   '})
        assert resp.status_code == 302
        assert not any('inventory_status' in c[0][0]
                       for c in mock_db['execute'].call_args_list)

    def test_reason_too_long(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = ACC
        resp = librarian_client.post(
            '/librarian/circulation/accession/damaged',
            data={'accession_number': 'ACC-1', 'notes': 'x' * 256})
        assert resp.status_code == 302
        assert not any('inventory_status' in c[0][0]
                       for c in mock_db['execute'].call_args_list)

    def test_damaged_ok(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [ACC, None]
        resp = librarian_client.post(
            '/librarian/circulation/accession/damaged',
            data={'accession_number': 'ACC-1', 'notes': 'torn cover'})
        assert resp.status_code == 302
        stmts = _non_audit_writes(mock_db)
        assert any('inventory_status' in s for s in stmts)

    def test_damaged_missing_accession(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = None
        resp = librarian_client.post(
            '/librarian/circulation/accession/damaged',
            data={'accession_number': 'NOPE', 'notes': 'torn'})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0


class TestConditionAuth:
    def test_student_blocked(self, student_client, mock_db):
        for url in ('/librarian/circulation/accession/lost',
                    '/librarian/circulation/accession/damaged'):
            resp = student_client.post(
                url, data={'accession_number': 'ACC-1', 'notes': 'x'})
            assert resp.status_code == 302
            assert '/user/profile' in resp.location
        assert _non_audit_writes(mock_db) == []

    def test_faculty_blocked(self, faculty_client, mock_db):
        for url in ('/librarian/circulation/accession/lost',
                    '/librarian/circulation/accession/damaged'):
            resp = faculty_client.post(
                url, data={'accession_number': 'ACC-1', 'notes': 'x'})
            assert resp.status_code == 302
            assert '/user/profile' in resp.location
        assert _non_audit_writes(mock_db) == []

    def test_anon_blocked(self, client):
        for url in ('/librarian/circulation/accession/lost',
                    '/librarian/circulation/accession/damaged'):
            resp = client.post(
                url, data={'accession_number': 'ACC-1', 'notes': 'x'})
            assert resp.status_code == 302
            assert '/login' in resp.location


class TestInventoryDamageReason:
    def test_notes_required(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = ACC
        resp = librarian_client.post(
            '/librarian/inventory/accession/10/damage', data={'notes': ''})
        assert resp.status_code == 302
        assert not any('inventory_status' in c[0][0]
                       for c in mock_db['execute'].call_args_list)


class TestCatalogConditionColumn:
    @staticmethod
    def _page(librarian_client, mock_db, conditions):
        mock_db['fetch_one'].return_value = (1,)
        mock_db['fetch_all'].side_effect = [
            [BOOK_ROW],                     # books page
            [(10, 'ACC-1', 1, 'purchase', '2026-01-02')],  # accessions
            conditions,                     # conditions lookup
        ]
        return librarian_client.get('/librarian/cataloging').data.decode()

    def test_lost_and_damaged_badges_with_reason(
            self, librarian_client, mock_db):
        body = self._page(librarian_client, mock_db, [
            (10, 'damaged', 'torn cover', False),
        ])
        assert 'Damaged' in body
        assert 'torn cover' in body

    def test_lost_badge(self, librarian_client, mock_db):
        body = self._page(librarian_client, mock_db, [
            (10, 'lost', None, False),
        ])
        assert 'Lost' in body

    def test_circ_lost_flag_counts_as_lost(
            self, librarian_client, mock_db):
        body = self._page(librarian_client, mock_db, [
            (10, None, None, True),
        ])
        assert 'Lost' in body

    def test_evil_reason_escaped(self, librarian_client, mock_db):
        evil = '<script>alert(1)</script>'
        body = self._page(librarian_client, mock_db, [
            (10, 'damaged', evil, False),
        ])
        assert evil not in body

    def test_split_filter_tabs(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/cataloging').data.decode()
        assert 'copy_status=lost' in body
        assert 'copy_status=damaged' in body


class TestAvailabilityRespectsInventoryLost:
    def test_lost_in_availability_sql(self, mock_db):
        from app.circulation import models as circ
        mock_db['fetch_one'].return_value = None
        circ.get_available_accession_by_book(1)
        query = mock_db['fetch_one'].call_args[0][0]
        assert 'inventory_state' in query

    def test_is_lost_covers_inventory(self, mock_db):
        from app.circulation import models as circ
        mock_db['fetch_one'].return_value = (True,)
        assert circ.is_accession_lost(10) is True
        mock_db['fetch_one'].return_value = None
        assert circ.is_accession_lost(10) is False
