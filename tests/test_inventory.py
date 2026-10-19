"""Tests for the Inventory module: sessions, scanning, quick-check, damage/lost, export."""
from app.inventory.models import reconcile_inventory, update_session_scan


class TestInventoryAccess:
    def test_student_forbidden(self, student_client):
        """Validates student forbidden `/librarian/inventory` as student (expects 302) [TestInventoryAccess / inventory].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates inventory counts/actions are wrong."""
        resp = student_client.get('/librarian/inventory')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location


class TestSessionLifecycle:
    def test_start_session_success(self, librarian_client, mock_db):
        """Validates start session success `/librarian/inventory/session/start` as librarian (expects 302) [TestSessionLifecycle / inventory].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_one'].side_effect = [
            None,     # get_active_session -> none active
            (12,),    # count_accessions
            (99,),    # create_inventory_session RETURNING session_id
        ]
        resp = librarian_client.post('/librarian/inventory/session/start')

        assert resp.status_code == 302
        assert 'session_id=99' in resp.location

    def test_start_session_blocks_if_active_exists(self, librarian_client, mock_db):
        """Validates start session blocks if active exists `/librarian/inventory/session/start` as librarian (expects 302) [TestSessionLifecycle / inventory].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_one'].return_value = (5, 3, 20, 3, 'active', None, None)

        resp = librarian_client.post('/librarian/inventory/session/start')

        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_complete_session_success(self, librarian_client, mock_db):
        """Validates complete session success `/librarian/inventory/session/7/complete` as librarian (expects 302) [TestSessionLifecycle / inventory].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_one'].return_value = (7, 3, 10, 5, 'active', None, None)
        mock_db['fetch_all'].return_value = []

        resp = librarian_client.post('/librarian/inventory/session/7/complete')

        assert resp.status_code == 302
        assert mock_db['execute'].call_count >= 1

    def test_complete_session_any_librarian_allowed(self, librarian_client, mock_db):
        """Validates any librarian may complete a session started by someone else [TestSessionLifecycle / inventory].
    If fails: likely ownership check reappeared (sessions are shared, not owned).
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_one'].return_value = (7, 99, 10, 5, 'active', None, None)
        mock_db['fetch_all'].return_value = []

        resp = librarian_client.post('/librarian/inventory/session/7/complete')

        assert resp.status_code == 302
        assert mock_db['execute'].call_count >= 1

    def test_cancel_session_success(self, librarian_client, mock_db):
        """Validates cancel session success `/librarian/inventory/session/7/cancel` as librarian (expects 302) [TestSessionLifecycle / inventory].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_one'].return_value = (7, 3, 10, 5, 'active', None, None)

        resp = librarian_client.post('/librarian/inventory/session/7/cancel')

        assert resp.status_code == 302
        call_args = mock_db['execute'].call_args_list[0]
        assert 'cancelled' in call_args[0][0]

    def test_cancel_session_any_librarian_allowed(self, librarian_client, mock_db):
        """Validates any librarian may cancel a session started by someone else [TestSessionLifecycle / inventory].
    If fails: likely ownership check reappeared (sessions are shared, not owned).
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_one'].return_value = (7, 99, 10, 5, 'active', None, None)

        resp = librarian_client.post('/librarian/inventory/session/7/cancel')

        assert resp.status_code == 302
        call_args = mock_db['execute'].call_args_list[0]
        assert 'cancelled' in call_args[0][0]


class TestScanning:
    def test_scan_available_no_active_loan(self, librarian_client, mock_db):
        """Validates scan available no active loan `/librarian/inventory/scan` as librarian (expects 302) [TestScanning / inventory].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_one'].side_effect = [
            (1, '2026-00001', 5, 1, 3, None, None),  # get_accession_by_number
            None,  # get_active_loan_by_accession -> no loan
            None,  # upsert_inventory_record's existing-row check -> insert path
        ]

        resp = librarian_client.post('/librarian/inventory/scan', data={'accession_number': '2026-00001'})

        assert resp.status_code == 302
        call_args = mock_db['execute'].call_args_list[0]
        assert 'INSERT INTO inventory_status' in call_args[0][0]

    def test_scan_marks_borrowed_if_active_loan(self, librarian_client, mock_db):
        """Validates scan marks borrowed if active loan `/librarian/inventory/scan` as librarian (expects 302) [TestScanning / inventory].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_one'].side_effect = [
            (1, '2026-00001', 5, 1, 3, None, None),
            (55, 1, 2, 'active', None, None),  # a truthy active loan row
            None,
        ]

        resp = librarian_client.post('/librarian/inventory/scan', data={'accession_number': '2026-00001'})

        assert resp.status_code == 302
        call_args = mock_db['execute'].call_args_list[0]
        assert 'borrowed' in call_args[0][1]

    def test_scan_accession_not_found(self, librarian_client, mock_db):
        """Validates scan accession not found `/librarian/inventory/scan` as librarian (expects 302) [TestScanning / inventory].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_one'].return_value = None

        resp = librarian_client.post('/librarian/inventory/scan', data={'accession_number': 'nonexistent'})

        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_scan_blank_accession_rejected(self, librarian_client, mock_db):
        """Validates scan blank accession rejected `/librarian/inventory/scan` as librarian (expects 302) [TestScanning / inventory].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates inventory counts/actions are wrong."""
        resp = librarian_client.post('/librarian/inventory/scan', data={'accession_number': ''})

        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0


class TestQuickCheck:
    def test_check_is_read_only(self, librarian_client, mock_db):
        """Validates check is read only `/librarian/inventory/check` as librarian (expects 302) [TestQuickCheck / inventory].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_one'].side_effect = [
            (1, '2026-00001', 5, 1, 3, None, None),
            ('2026-00001', 'Some Book', 'available', None),
        ]

        resp = librarian_client.post('/librarian/inventory/check', data={'accession_number': '2026-00001'})

        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0


class TestDamageAndLost:
    def test_mark_damaged(self, librarian_client, mock_db):
        """Validates mark damaged `/librarian/inventory/accession/1/damage` as librarian (expects 302) [TestDamageAndLost / inventory].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_one'].side_effect = [(10, 'ACC-001', 1), None]

        resp = librarian_client.post('/librarian/inventory/accession/1/damage', data={'notes': 'torn cover'})

        assert resp.status_code == 302
        call_args = mock_db['execute'].call_args_list[0]
        assert 'INSERT INTO inventory_status' in call_args[0][0]

    def test_mark_lost(self, librarian_client, mock_db):
        """Validates mark lost `/librarian/inventory/accession/1/lost` as librarian (expects 302) [TestDamageAndLost / inventory].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_one'].return_value = (10, 'ACC-001', 1)

        resp = librarian_client.post('/librarian/inventory/accession/1/lost', data={'notes': 'not on shelf'})

        assert resp.status_code == 302
        call_args = mock_db['execute'].call_args_list[0]
        assert 'lost' in call_args[0][1]

    def test_mark_lost_requires_note(self, librarian_client, mock_db):
        """Validates mark lost without a note is rejected with no write [TestDamageAndLost / inventory].
    If fails: likely the required-note guard was removed.
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_one'].return_value = (10, 'ACC-001', 1)

        resp = librarian_client.post('/librarian/inventory/accession/1/lost', data={})

        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0


class TestExport:
    def test_export_success(self, librarian_client, mock_db):
        """Validates export success `/librarian/inventory/session/7/export` as librarian (expects 200) [TestExport / inventory].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_one'].return_value = (7, 3, 10, 10, 'completed', None, None)
        mock_db['fetch_all'].return_value = []

        resp = librarian_client.get('/librarian/inventory/session/7/export')

        assert resp.status_code == 200
        assert resp.mimetype == 'text/csv'

    def test_export_any_librarian_allowed(self, librarian_client, mock_db):
        """Validates any librarian may export a session started by someone else [TestExport / inventory].
    If fails: likely ownership check reappeared (sessions are shared, not owned).
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_one'].return_value = (7, 99, 10, 10, 'completed', None, None)
        mock_db['fetch_all'].return_value = []

        resp = librarian_client.get('/librarian/inventory/session/7/export')

        assert resp.status_code == 200
        assert resp.mimetype == 'text/csv'

class TestReconcileInventory:
    def test_closes_session_and_returns_missing(self, mock_db):
        """Validates reconcile closes the session and maps missing rows [TestReconcileInventory / inventory].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_all'].return_value = [
            (1, '2026-00001'),
        ]

        discrepancies = reconcile_inventory(session_id=1, scanned_accessions={2}, checked_by=3)

        assert discrepancies == [
            {'accession_id': 1, 'accession': '2026-00001', 'issue': 'Missing'},
        ]
        closed = [c for c in mock_db['execute'].call_args_list if 'session_status' in c[0][0]]
        assert closed and 'completed' in closed[0][0][1]

    def test_guards_damaged_lost_and_overdue(self, mock_db):
        """Validates reconcile SQL skips damaged/lost and counts overdue loans [TestReconcileInventory / inventory].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_all'].return_value = []

        reconcile_inventory(session_id=1, scanned_accessions=set())

        sql = ' '.join(c[0][0] for c in mock_db['execute'].call_args_list)
        assert "NOT IN ('damaged', 'lost')" in sql
        assert "transaction_status IN ('active', 'overdue')" in sql

    def test_empty_and_none_results_are_safe(self, mock_db):
        """Validates reconcile tolerates empty/None driver results [TestReconcileInventory / inventory].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_all'].return_value = []
        assert reconcile_inventory(session_id=1, scanned_accessions=set()) == []

        mock_db['fetch_all'].return_value = None
        assert reconcile_inventory(session_id=1, scanned_accessions=set()) == []


class TestDuplicateScanPrevention:
    def test_first_scan_increments_counter(self, mock_db):
        """Validates first scan increments counter [TestDuplicateScanPrevention / inventory].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_one'].return_value = None

        update_session_scan(session_id=1, accession_id=5)

        assert mock_db['execute'].call_count == 1
        call_args = mock_db['execute'].call_args_list[0]
        assert 'scanned_count = scanned_count + 1' in call_args[0][0]

    def test_repeat_scan_does_not_increment(self, mock_db):
        """Validates repeat scan does not increment [TestDuplicateScanPrevention / inventory].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_one'].return_value = (10,)

        update_session_scan(session_id=1, accession_id=5)

        assert mock_db['execute'].call_count == 0

class TestScanSessionState:
    def test_scan_into_other_librarian_session_allowed(self, librarian_client, mock_db):
        """Validates any librarian may scan into a session started by someone else [TestScanSessionState / inventory].
    If fails: likely ownership check reappeared (sessions are shared, not owned).
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_one'].side_effect = [
            (5, 99, 10, 3, 'active', None, None),  # get_session -> shared/active
            (1, '2026-00001', 5, 1, 3, None, None),  # get_accession_by_number
            None,  # get_active_loan_by_accession -> no loan
            None,  # update_session_scan existing-row check -> increments
            None,  # upsert existing-row check -> insert path
        ]

        resp = librarian_client.post('/librarian/inventory/scan', data={
            'accession_number': '2026-00001',
            'session_id': 5,
        })

        assert resp.status_code == 302
        assert mock_db['execute'].call_count >= 1

    def test_scan_rejects_inactive_session(self, librarian_client, mock_db):
        """Validates scan rejects inactive session `/librarian/inventory/scan` as librarian (expects 302) [TestScanSessionState / inventory].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_one'].return_value = (5, 3, 10, 3, 'completed', None, None)

        resp = librarian_client.post('/librarian/inventory/scan', data={
            'accession_number': '2026-00001',
            'session_id': 5,
        })

        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_scan_without_session_id_still_works(self, librarian_client, mock_db):
        """Validates scan without session id still works `/librarian/inventory/scan` as librarian (expects 302) [TestScanSessionState / inventory].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_one'].side_effect = [
            (1, '2026-00001', 5, 1, 3, None, None),  # get_accession_by_number
            None,  # get_active_loan_by_accession
            None,  # upsert existing-row check
        ]

        resp = librarian_client.post('/librarian/inventory/scan', data={
            'accession_number': '2026-00001',
        })

        assert resp.status_code == 302
        call_args = mock_db['execute'].call_args_list[0]
        assert 'INSERT INTO inventory_status' in call_args[0][0]


class TestExportGuard:
    def test_export_rejects_active_session(self, librarian_client, mock_db):
        """Validates export rejects active session `/librarian/inventory/session/7/export` as librarian (expects 302) [TestExportGuard / inventory].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_one'].return_value = (7, 3, 10, 5, 'active', None, None)

        resp = librarian_client.get('/librarian/inventory/session/7/export')

        assert resp.status_code == 302


class TestPastSessions:
    def test_past_sessions_listed_with_links(self, librarian_client, mock_db):
        """Validates the dashboard lists past sessions with read-only links [TestPastSessions / inventory].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates inventory counts/actions are wrong."""
        row = (3, 3, 'Test Librarian', 10, 10, 'completed', None, None)
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].side_effect = [[], [], [row]]

        body = librarian_client.get('/librarian/inventory').data.decode()

        assert 'Past Sessions' in body
        assert 'Session #3' in body
        assert 'session_id=3' in body

    def test_past_sessions_malformed_rows_ignored(self, librarian_client, mock_db):
        """Validates short/None session rows never crash the dashboard [TestPastSessions / inventory].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].side_effect = [[], [], [(0,), None]]

        assert librarian_client.get('/librarian/inventory').status_code == 200

    def test_owner_sees_manage_controls(self, librarian_client, mock_db):
        """Validates the session owner is offered Complete/Cancel [TestPastSessions / inventory].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_one'].return_value = (7, 3, 10, 5, 'active', None, None)

        body = librarian_client.get('/librarian/inventory').data.decode()

        assert 'Complete Session' in body
        assert 'Cancel Session' in body

    def test_landing_shows_shared_active_session(self, librarian_client, mock_db):
        """Validates the landing view opens the shared active session regardless of starter [TestPastSessions / inventory].
    If fails: likely get_active_session no longer returns the global newest active session.
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_one'].return_value = (7, 99, 10, 5, 'active', None, None)

        body = librarian_client.get('/librarian/inventory').data.decode()

        assert 'Complete Session' in body
        assert 'Start New Session' not in body

    def test_any_librarian_sees_manage_controls(self, librarian_client, mock_db):
        """Validates any librarian viewing another librarian's session is offered controls [TestPastSessions / inventory].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_one'].return_value = (7, 99, 10, 5, 'active', None, None)

        body = librarian_client.get('/librarian/inventory?session_id=7').data.decode()

        assert 'Complete Session' in body
        assert 'Cancel Session' in body

    def test_any_librarian_can_complete(self, librarian_client, mock_db):
        """Validates any librarian may complete a session they did not start [TestPastSessions / inventory].
    If fails: likely ownership check reappeared (sessions are shared, not owned).
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_one'].return_value = (7, 99, 10, 5, 'active', None, None)
        mock_db['fetch_all'].return_value = []

        resp = librarian_client.post('/librarian/inventory/session/7/complete')

        assert resp.status_code == 302
        assert mock_db['execute'].call_count >= 1