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

    def test_complete_session_wrong_owner(self, librarian_client, mock_db):
        """Validates complete session wrong owner `/librarian/inventory/session/7/complete` as librarian (expects 302) [TestSessionLifecycle / inventory].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_one'].return_value = (7, 99, 10, 5, 'active', None, None)

        resp = librarian_client.post('/librarian/inventory/session/7/complete')

        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_cancel_session_success(self, librarian_client, mock_db):
        """Validates cancel session success `/librarian/inventory/session/7/cancel` as librarian (expects 302) [TestSessionLifecycle / inventory].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_one'].return_value = (7, 3, 10, 5, 'active', None, None)

        resp = librarian_client.post('/librarian/inventory/session/7/cancel')

        assert resp.status_code == 302
        call_args = mock_db['execute'].call_args_list[0]
        assert 'cancelled' in call_args[0][0]

    def test_cancel_session_wrong_owner(self, librarian_client, mock_db):
        """Validates cancel session wrong owner `/librarian/inventory/session/7/cancel` as librarian (expects 302) [TestSessionLifecycle / inventory].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_one'].return_value = (7, 99, 10, 5, 'active', None, None)

        resp = librarian_client.post('/librarian/inventory/session/7/cancel')

        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0


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

        resp = librarian_client.post('/librarian/inventory/accession/1/lost')

        assert resp.status_code == 302
        call_args = mock_db['execute'].call_args_list[0]
        assert 'lost' in call_args[0][1]


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

    def test_export_wrong_owner(self, librarian_client, mock_db):
        """Validates export wrong owner `/librarian/inventory/session/7/export` as librarian (expects 302) [TestExport / inventory].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_one'].return_value = (7, 99, 10, 10, 'completed', None, None)

        resp = librarian_client.get('/librarian/inventory/session/7/export')

        assert resp.status_code == 302

class TestReconcileInventory:
    def test_damaged_copy_preserved_through_reconcile(self, mock_db):
        """Validates damaged copy preserved through reconcile [TestReconcileInventory / inventory].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_all'].return_value = [
            (1, '2026-00001', 'damaged'),
        ]
        mock_db['fetch_one'].return_value = None

        reconcile_inventory(session_id=1, scanned_accessions=set())

        for call in mock_db['execute'].call_args_list:
            assert 'damaged' not in call[0][1] or 'inventory_status' not in call[0][0]

    def test_lost_copy_preserved_through_reconcile(self, mock_db):
        """Validates lost copy preserved through reconcile [TestReconcileInventory / inventory].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_all'].return_value = [
            (1, '2026-00001', 'lost'),
        ]
        mock_db['fetch_one'].return_value = None

        reconcile_inventory(session_id=1, scanned_accessions=set())

        for call in mock_db['execute'].call_args_list:
            assert 'INSERT INTO inventory_status' not in call[0][0]
            assert 'UPDATE inventory_status' not in call[0][0]

    def test_unscanned_unloaned_copy_marked_missing(self, mock_db):
        """Validates unscanned unloaned copy marked missing [TestReconcileInventory / inventory].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_all'].return_value = [
            (1, '2026-00001', 'available'),
        ]
        mock_db['fetch_one'].return_value = None

        discrepancies = reconcile_inventory(session_id=1, scanned_accessions=set())

        assert len(discrepancies) == 1
        assert discrepancies[0]['issue'] == 'Missing'


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

class TestScanSessionOwnership:
    def test_scan_rejects_unowned_session(self, librarian_client, mock_db):
        """Validates scan rejects unowned session `/librarian/inventory/scan` as librarian (expects 302) [TestScanSessionOwnership / inventory].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates inventory counts/actions are wrong."""
        mock_db['fetch_one'].return_value = (5, 99, 10, 3, 'active', None, None)

        resp = librarian_client.post('/librarian/inventory/scan', data={
            'accession_number': '2026-00001',
            'session_id': 5,
        })

        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_scan_rejects_inactive_session(self, librarian_client, mock_db):
        """Validates scan rejects inactive session `/librarian/inventory/scan` as librarian (expects 302) [TestScanSessionOwnership / inventory].
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
        """Validates scan without session id still works `/librarian/inventory/scan` as librarian (expects 302) [TestScanSessionOwnership / inventory].
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