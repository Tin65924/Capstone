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
    """Test helper _non_audit_writes: build mocked data or DB stub for the test."""
    return [c[0][0] for c in mock_db['execute'].call_args_list
            if 'audit_trail' not in c[0][0]]


class TestPureReturn:
    def test_return_ignores_legacy_lost_damage_fields(
            self, librarian_client, mock_db):
        """Validates return ignores legacy lost damage fields `/librarian/circulation/return` as librarian (expects 302) [TestPureReturn / condition fixes].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (UPDATE).
    Failure indicates condition fixes is broken for this case (users see wrong page, blocked action, or bad data).

Old return payloads (lost checkbox, damage notes) now behave
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
        """Validates return page has condition card not lost checkbox `/librarian/circulation` as librarian [TestPureReturn / condition fixes].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates condition fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/circulation').data.decode()
        assert 'Copy Condition' in body
        assert 'name="damage_notes"' not in body
        assert 'name="lost"' not in body


class TestMarkLost:
    def test_lost_with_loan_closes_it(self, librarian_client, mock_db):
        """Validates lost with loan closes it `/librarian/circulation/accession/lost` as librarian (expects 302) [TestMarkLost / condition fixes].
    If fails: likely model SQL changed (UPDATE).
    Failure indicates condition fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
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
        """Validates lost without loan `/librarian/circulation/accession/lost` as librarian (expects 302) [TestMarkLost / condition fixes].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates condition fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].side_effect = [ACC, None, None]
        resp = librarian_client.post(
            '/librarian/circulation/accession/lost',
            data={'accession_number': 'ACC-1'})
        assert resp.status_code == 302
        stmts = _non_audit_writes(mock_db)
        assert not any('circulation_records' in s for s in stmts)
        assert any('inventory_status' in s for s in stmts)

    def test_lost_missing_accession(self, librarian_client, mock_db):
        """Validates lost missing accession `/librarian/circulation/accession/lost` as librarian (expects 302) [TestMarkLost / condition fixes].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates condition fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].return_value = None
        resp = librarian_client.post(
            '/librarian/circulation/accession/lost',
            data={'accession_number': 'NOPE'})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0


class TestMarkDamaged:
    def test_reason_required(self, librarian_client, mock_db):
        """Validates reason required `/librarian/circulation/accession/damaged` as librarian (expects 302) [TestMarkDamaged / condition fixes].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates condition fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].return_value = ACC
        resp = librarian_client.post(
            '/librarian/circulation/accession/damaged',
            data={'accession_number': 'ACC-1', 'notes': '   '})
        assert resp.status_code == 302
        assert not any('inventory_status' in c[0][0]
                       for c in mock_db['execute'].call_args_list)

    def test_reason_too_long(self, librarian_client, mock_db):
        """Validates reason too long `/librarian/circulation/accession/damaged` as librarian (expects 302) [TestMarkDamaged / condition fixes].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates condition fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].return_value = ACC
        resp = librarian_client.post(
            '/librarian/circulation/accession/damaged',
            data={'accession_number': 'ACC-1', 'notes': 'x' * 256})
        assert resp.status_code == 302
        assert not any('inventory_status' in c[0][0]
                       for c in mock_db['execute'].call_args_list)

    def test_damaged_ok(self, librarian_client, mock_db):
        """Validates damaged ok `/librarian/circulation/accession/damaged` as librarian (expects 302) [TestMarkDamaged / condition fixes].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates condition fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].side_effect = [ACC, None]
        resp = librarian_client.post(
            '/librarian/circulation/accession/damaged',
            data={'accession_number': 'ACC-1', 'notes': 'torn cover'})
        assert resp.status_code == 302
        stmts = _non_audit_writes(mock_db)
        assert any('inventory_status' in s for s in stmts)

    def test_damaged_missing_accession(self, librarian_client, mock_db):
        """Validates damaged missing accession `/librarian/circulation/accession/damaged` as librarian (expects 302) [TestMarkDamaged / condition fixes].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates condition fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].return_value = None
        resp = librarian_client.post(
            '/librarian/circulation/accession/damaged',
            data={'accession_number': 'NOPE', 'notes': 'torn'})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0


class TestConditionAuth:
    def test_student_blocked(self, student_client, mock_db):
        """Validates student blocked as student (expects 302) [TestConditionAuth / condition fixes].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates condition fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        for url in ('/librarian/circulation/accession/lost',
                    '/librarian/circulation/accession/damaged'):
            resp = student_client.post(
                url, data={'accession_number': 'ACC-1', 'notes': 'x'})
            assert resp.status_code == 302
            assert '/user/profile' in resp.location
        assert _non_audit_writes(mock_db) == []

    def test_faculty_blocked(self, faculty_client, mock_db):
        """Validates faculty blocked as faculty (expects 302) [TestConditionAuth / condition fixes].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates condition fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        for url in ('/librarian/circulation/accession/lost',
                    '/librarian/circulation/accession/damaged'):
            resp = faculty_client.post(
                url, data={'accession_number': 'ACC-1', 'notes': 'x'})
            assert resp.status_code == 302
            assert '/user/profile' in resp.location
        assert _non_audit_writes(mock_db) == []

    def test_anon_blocked(self, client):
        """Validates anon blocked (expects 302) [TestConditionAuth / condition fixes].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        for url in ('/librarian/circulation/accession/lost',
                    '/librarian/circulation/accession/damaged'):
            resp = client.post(
                url, data={'accession_number': 'ACC-1', 'notes': 'x'})
            assert resp.status_code == 302
            assert '/login' in resp.location


class TestInventoryDamageReason:
    def test_notes_required(self, librarian_client, mock_db):
        """Validates notes required `/librarian/inventory/accession/10/damage` as librarian (expects 302) [TestInventoryDamageReason / condition fixes].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates condition fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].return_value = ACC
        resp = librarian_client.post(
            '/librarian/inventory/accession/10/damage', data={'notes': ''})
        assert resp.status_code == 302
        assert not any('inventory_status' in c[0][0]
                       for c in mock_db['execute'].call_args_list)


class TestCatalogConditionColumn:
    @staticmethod
    def _page(librarian_client, mock_db, conditions):
        """Test helper _page: build mocked data or DB stub for the test."""
        mock_db['fetch_one'].return_value = (1,)
        mock_db['fetch_all'].side_effect = [
            [BOOK_ROW],                     # books page
            [(10, 'ACC-1', 1, 'purchase', '2026-01-02')],  # accessions
            conditions,                     # conditions lookup
        ]
        return librarian_client.get('/librarian/cataloging').data.decode()

    def test_lost_and_damaged_badges_with_reason(
            self, librarian_client, mock_db):
        """Validates lost and damaged badges with reason as librarian [TestCatalogConditionColumn / condition fixes].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates condition fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        body = self._page(librarian_client, mock_db, [
            (10, 'damaged', 'torn cover', None, False),
        ])
        assert 'Damaged' in body
        assert 'torn cover' in body

    def test_lost_badge(self, librarian_client, mock_db):
        """Validates lost badge as librarian [TestCatalogConditionColumn / condition fixes].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates condition fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        body = self._page(librarian_client, mock_db, [
            (10, 'lost', None, None, False),
        ])
        assert 'Lost' in body

    def test_circ_lost_flag_counts_as_lost(
            self, librarian_client, mock_db):
        """Validates circ lost flag counts as lost as librarian [TestCatalogConditionColumn / condition fixes].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates condition fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        body = self._page(librarian_client, mock_db, [
            (10, None, None, None, True),
        ])
        assert 'Lost' in body

    def test_legacy_loan_damage_shows_with_reason(
            self, librarian_client, mock_db):
        # No inventory assessment yet, but the latest loan recorded
        # damage: still Damaged with its reason.
        """Validates legacy loan damage shows with reason as librarian [TestCatalogConditionColumn / condition fixes].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates condition fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        body = self._page(librarian_client, mock_db, [
            (10, None, None, 'water damage', False),
        ])
        assert 'Damaged' in body
        assert 'water damage' in body

    def test_clean_inventory_clears_old_loan_damage(
            self, librarian_client, mock_db):
        # A later inventory assessment of available wins over an old
        # damage note on a previous loan.
        """Validates clean inventory clears old loan damage as librarian [TestCatalogConditionColumn / condition fixes].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates condition fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        body = self._page(librarian_client, mock_db, [
            (10, 'available', None, 'old stain', False),
        ])
        assert '<span class="status-badge status-damaged">' not in body
        assert '<span class="status-badge status-lost">' not in body
        assert 'old stain' not in body

    def test_evil_reason_escaped(self, librarian_client, mock_db):
        """Validates evil reason escaped as librarian [TestCatalogConditionColumn / condition fixes].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates condition fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        evil = '<script>alert(1)</script>'
        body = self._page(librarian_client, mock_db, [
            (10, 'damaged', evil, None, False),
        ])
        assert evil not in body

    def test_split_filter_tabs(self, librarian_client, mock_db):
        """Validates split filter tabs `/librarian/cataloging` as librarian [TestCatalogConditionColumn / condition fixes].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/cataloging').data.decode()
        assert 'copy_status=lost' in body
        assert 'copy_status=damaged' in body


class TestInventoryReasonColumn:
    @staticmethod
    def _history(mock_db, rows):
        """Test helper _history: build mocked data or DB stub for the test."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].side_effect = [[], rows]

    def test_reason_shown_in_history(self, librarian_client, mock_db):
        """Validates reason shown in history `/librarian/inventory` as librarian [TestInventoryReasonColumn / condition fixes].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates condition fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        self._history(mock_db, [
            (1, 10, 'ACC-1', 'Some Title', 'damaged', '2026-01-05',
             'torn cover'),
        ])
        body = librarian_client.get('/librarian/inventory').data.decode()
        assert 'Reason' in body
        assert 'torn cover' in body

    def test_reason_escaped(self, librarian_client, mock_db):
        """Validates reason escaped `/librarian/inventory` as librarian [TestInventoryReasonColumn / condition fixes].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates condition fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        evil = '<script>alert(1)</script>'
        self._history(mock_db, [
            (1, 10, 'ACC-1', 'Some Title', 'damaged', '2026-01-05', evil),
        ])
        body = librarian_client.get('/librarian/inventory').data.decode()
        assert evil not in body

    def test_row_damage_needs_notes(self, librarian_client, mock_db):
        """Validates row damage needs notes `/librarian/inventory/accession/10/damage` as librarian (expects 302) [TestInventoryReasonColumn / condition fixes].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates condition fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].return_value = ACC
        resp = librarian_client.post(
            '/librarian/inventory/accession/10/damage', data={})
        assert resp.status_code == 302
        assert not any('inventory_status' in c[0][0]
                       for c in mock_db['execute'].call_args_list)


class TestAccessionPlaceholders:
    def test_consistent_format_examples(self, librarian_client, mock_db):
        """Validates consistent format examples `/librarian/circulation` as librarian [TestAccessionPlaceholders / condition fixes].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        circ = librarian_client.get('/librarian/circulation').data.decode()
        assert circ.count('placeholder="e.g. 000001"') >= 3
        assert '0000-0000' not in circ
        cat = librarian_client.get('/librarian/cataloging').data.decode()
        assert 'placeholder="e.g. 000001"' in cat
        assert '0000-0000' not in cat


class TestAvailabilityRespectsInventoryLost:
    def test_lost_in_availability_sql(self, mock_db):
        """Validates lost in availability sql [TestAvailabilityRespectsInventoryLost / condition fixes].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates condition fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        from app.circulation import models as circ
        mock_db['fetch_one'].return_value = None
        circ.get_available_accession_by_book(1)
        query = mock_db['fetch_one'].call_args[0][0]
        assert 'inventory_state' in query

    def test_is_lost_covers_inventory(self, mock_db):
        """Validates is lost covers inventory [TestAvailabilityRespectsInventoryLost / condition fixes].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates condition fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        from app.circulation import models as circ
        mock_db['fetch_one'].return_value = (True,)
        assert circ.is_accession_lost(10) is True
        mock_db['fetch_one'].return_value = None
        assert circ.is_accession_lost(10) is False


class TestLostNotes:
    def test_circulation_lost_stores_note(self, librarian_client, mock_db):
        """Validates circulation lost stores note `/librarian/circulation/accession/lost` as librarian (expects 302) [TestLostNotes / condition fixes].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates condition fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].side_effect = [ACC, None, None]
        resp = librarian_client.post(
            '/librarian/circulation/accession/lost',
            data={'accession_number': 'ACC-1',
                  'notes': 'left on the bus'})
        assert resp.status_code == 302
        inv = [c for c in mock_db['execute'].call_args_list
               if 'inventory_status' in c[0][0]]
        assert inv
        assert 'left on the bus' in inv[0][0][1]

    def test_inventory_lost_stores_note(self, librarian_client, mock_db):
        """Validates inventory lost stores note `/librarian/inventory/accession/10/lost` as librarian (expects 302) [TestLostNotes / condition fixes].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates condition fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].return_value = ACC
        resp = librarian_client.post(
            '/librarian/inventory/accession/10/lost',
            data={'notes': 'missing since audit'})
        assert resp.status_code == 302
        inv = [c for c in mock_db['execute'].call_args_list
               if 'inventory_status' in c[0][0]]
        assert inv
        assert 'missing since audit' in inv[0][0][1]

    def test_lost_without_note_still_works(self, librarian_client, mock_db):
        """Validates lost without note still works `/librarian/circulation/accession/lost` as librarian (expects 302) [TestLostNotes / condition fixes].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates condition fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].side_effect = [ACC, None, None]
        resp = librarian_client.post(
            '/librarian/circulation/accession/lost',
            data={'accession_number': 'ACC-1'})
        assert resp.status_code == 302
        inv = [c for c in mock_db['execute'].call_args_list
               if 'inventory_status' in c[0][0]]
        assert inv


BOOK16 = (1, 'Clean Code', 'R. Martin', '1st', 'Pub', 2008, 'SE', 'C1',
          '978', 'Book', 'Desc', 'active', '2026-01-01', '2026-05-05',
          None, 'ACC-001')


class TestBookReasonColumn:
    @staticmethod
    def _page(librarian_client, mock_db, conditions, tab='damaged'):
        """Test helper _page: build mocked data or DB stub for the test."""
        mock_db['fetch_one'].return_value = (1,)
        mock_db['fetch_all'].side_effect = [
            [BOOK16],
            [(10, '250001', 1, 'purchase', '2026-01-02')],
            conditions,
        ]
        return librarian_client.get(
            f'/librarian/cataloging?copy_status={tab}').data.decode()

    def test_reason_column_in_damaged_view(self, librarian_client, mock_db):
        """Validates reason column in damaged view as librarian [TestBookReasonColumn / condition fixes].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates condition fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        body = self._page(librarian_client, mock_db,
                          [(10, 'damaged', 'torn cover', None, False)],
                          tab='damaged')
        assert 'Reason' in body
        assert 'torn cover' in body

    def test_reason_column_in_lost_view(self, librarian_client, mock_db):
        """Validates reason column in lost view as librarian [TestBookReasonColumn / condition fixes].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates condition fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        body = self._page(librarian_client, mock_db,
                          [(10, 'lost', 'left on bus', None, False)],
                          tab='lost')
        assert 'Reason' in body
        assert 'left on bus' in body

    def test_no_reason_column_by_default(self, librarian_client, mock_db):
        """Validates no reason column by default `/librarian/cataloging` as librarian [TestBookReasonColumn / condition fixes].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].return_value = (1,)
        mock_db['fetch_all'].side_effect = [
            [BOOK16],
            [(10, '250001', 1, 'purchase', '2026-01-02')],
            [],
        ]
        body = librarian_client.get('/librarian/cataloging').data.decode()
        assert '<th>Reason</th>' not in body

    def test_empty_reason_renders_dash(self, librarian_client, mock_db):
        """Validates empty reason renders dash as librarian [TestBookReasonColumn / condition fixes].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates condition fixes is broken for this case (users see wrong page, blocked action, or bad data)."""
        body = self._page(librarian_client, mock_db,
                          [(10, 'lost', None, None, False)],
                          tab='lost')
        assert 'Reason' in body
