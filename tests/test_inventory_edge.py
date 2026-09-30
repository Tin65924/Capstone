"""Edge-case regression tests for Inventory Management.

Covers `/librarian/inventory`, sessions (start/complete/cancel),
scanning, status checks, damage/lost marking, and session export:
empty database, `None`/short model rows, hostile params (garbage
pages, bogus statuses, missing/huge ids, oversized notes), missing
accessions, XSS scan rows, string dates, and the staff auth matrix.
Includes the session-length coercion and date-format guards.
Everything must degrade gracefully — never 500.
"""

SESSION = (1, 3, 10, 4, 'active', '2026-01-05', None, None)
ACC = (10, 'ACC-001', 1, 'purchase', '2026-01-02', None, None, None)


class TestEmptyDb:
    @staticmethod
    def _empty(mock_db):
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        mock_db['execute'].return_value = []

    def test_page_empty(self, librarian_client, mock_db):
        self._empty(mock_db)
        assert librarian_client.get('/librarian/inventory').status_code == 200

    def test_page_none_models(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = None
        assert librarian_client.get('/librarian/inventory').status_code == 200

    def test_short_session_row(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (1, 3)
        mock_db['fetch_all'].return_value = []
        assert librarian_client.get(
            '/librarian/inventory?session_id=1').status_code == 200


class TestHostileParams:
    @staticmethod
    def _ok(mock_db):
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []

    def test_page_params(self, librarian_client, mock_db):
        self._ok(mock_db)
        for url in ('/librarian/inventory?page=abc',
                    '/librarian/inventory?page=-5',
                    '/librarian/inventory?page=999999',
                    '/librarian/inventory?status=bogus',
                    '/librarian/inventory?session_id=abc',
                    '/librarian/inventory?session_id=999999'):
            assert librarian_client.get(url).status_code == 200, url

    def test_complete_variants(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        for url in ('/librarian/inventory/session/999/complete',
                    '/librarian/inventory/session/999999999/complete',
                    '/librarian/inventory/session/999/cancel'):
            assert librarian_client.post(url).status_code == 302, url

    def test_complete_short_row(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (1, 3)
        assert librarian_client.post(
            '/librarian/inventory/session/1/complete').status_code == 302

    def test_scan_hostile(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        for data in ({}, {'accession_number': ''},
                     {'accession_number': 'X' * 2000},
                     {'accession_number': 'NOPE'},
                     {'accession_number': 'ACC-1', 'session_id': 'abc'},
                     {'accession_number': 'ACC-1', 'session_id': '999'}):
            assert librarian_client.post(
                '/librarian/inventory/scan', data=data).status_code == 302, data

    def test_check_hostile(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = None
        for data in ({}, {'accession_number': 'NOPE'},
                     {'accession_number': 'X' * 2000}):
            assert librarian_client.post(
                '/librarian/inventory/check', data=data).status_code == 302, data

    def test_damage_lost_missing(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = None
        for url in ('/librarian/inventory/accession/999/damage',
                    '/librarian/inventory/accession/999/lost',
                    '/librarian/inventory/accession/999999999/damage'):
            assert librarian_client.post(
                url, data={'notes': 'x'}).status_code == 302, url

    def test_damage_huge_notes(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = ACC
        assert librarian_client.post(
            '/librarian/inventory/accession/10/damage',
            data={'notes': 'x' * 10000}).status_code == 302

    def test_export_variants(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        for url in ('/librarian/inventory/session/999/export',
                    '/librarian/inventory/session/999999999/export'):
            assert librarian_client.get(url).status_code == 302, url


class TestXss:
    def test_evil_scan_rows(self, librarian_client, mock_db):
        evil = '<script>alert(1)</script>'
        row = (1, 10, evil, evil, 'available', '2026-01-05', evil)
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].side_effect = [[], [row], [(0,)]]
        body = librarian_client.get('/librarian/inventory').data.decode()
        assert evil not in body

    def test_string_dates(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = None
        row = (1, 10, 'ACC-1', 'T', 'available', '2026-01-05', '')
        mock_db['fetch_all'].side_effect = [[], [row], [(0,)]]
        assert librarian_client.get('/librarian/inventory').status_code == 200


class TestAuth:
    def test_anon(self, client):
        assert client.get('/librarian/inventory').status_code == 302
        assert client.post('/librarian/inventory/scan').status_code == 302
        assert client.post(
            '/librarian/inventory/accession/1/lost').status_code == 302

    def test_student_blocked(self, student_client, mock_db):
        assert student_client.get('/librarian/inventory').status_code == 302
        resp = student_client.post('/librarian/inventory/scan',
                                   data={'accession_number': 'X'})
        assert resp.status_code == 302
        writes = [c[0][0] for c in mock_db['execute'].call_args_list
                  if 'INSERT' in c[0][0] and 'audit_trail' not in c[0][0]]
        assert writes == []

    def test_faculty_blocked(self, faculty_client):
        assert faculty_client.get('/librarian/inventory').status_code == 302
