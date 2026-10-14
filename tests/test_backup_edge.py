"""Edge-case regression tests for Backup & Recovery.

Covers `/admin/backup` and create/download/restore/delete: empty
database, `None`/short/mistyped rows (padded centrally so template
reads never crash), hostile ids, missing files, non-completed
restores, XSS filenames and reflected params, and the admin-only auth
matrix. Everything must degrade gracefully — never 500.
"""

FULL = (1, 'b.sql', 100, 'completed', 'manual', None, '2026-01-01')


class TestPageEdges:
    @staticmethod
    def _empty(mock_db):
        """Test helper _empty: build mocked data or DB stub for the test."""
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        mock_db['execute'].return_value = []

    def test_page_empty(self, admin_client, mock_db):
        """Validates page empty `/admin/backup` as admin (expects 200) [TestPageEdges / backup edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates backup/restore safety net is broken (data-loss risk)."""
        self._empty(mock_db)
        assert admin_client.get('/admin/backup').status_code == 200

    def test_none_logs(self, admin_client, mock_db):
        """Validates none logs `/admin/backup` as admin (expects 200) [TestPageEdges / backup edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates backup/restore safety net is broken (data-loss risk)."""
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = None
        assert admin_client.get('/admin/backup').status_code == 200

    def test_short_rows(self, admin_client, mock_db):
        """Validates short rows `/admin/backup` as admin (expects 200) [TestPageEdges / backup edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates backup/restore safety net is broken (data-loss risk)."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = [(1,), (1, 'b.sql')]
        assert admin_client.get('/admin/backup').status_code == 200

    def test_string_size_and_date(self, admin_client, mock_db):
        """Validates string size and date `/admin/backup` as admin (expects 200) [TestPageEdges / backup edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates backup/restore safety net is broken (data-loss risk)."""
        mock_db['fetch_one'].return_value = (0,)
        row = (1, 'b.sql', 'huge', 'completed', 'manual', None,
               '2026-01-01')
        mock_db['fetch_all'].return_value = [row]
        assert admin_client.get('/admin/backup').status_code == 200

    def test_evil_filename(self, admin_client, mock_db):
        """Validates evil filename `/admin/backup` as admin [TestPageEdges / backup edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates backup/restore safety net is broken (data-loss risk)."""
        evil = '<script>alert(1)</script>'
        mock_db['fetch_one'].return_value = (0,)
        row = (1, evil, 100, 'failed', 'manual', evil, '2026-01-01')
        mock_db['fetch_all'].return_value = [row]
        body = admin_client.get('/admin/backup').data.decode()
        assert evil not in body

    def test_evil_restore_started(self, admin_client, mock_db):
        """Validates evil restore started `/admin/backup?restore_started=<script>alert(1)</script>` as admin [TestPageEdges / backup edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates backup/restore safety net is broken (data-loss risk)."""
        self._empty(mock_db)
        body = admin_client.get(
            '/admin/backup?restore_started=<script>alert(1)</script>'
        ).data.decode()
        assert '<script>alert(1)</script>' not in body


class TestActions:
    def test_download_short_row(self, admin_client, mock_db):
        """Validates download short row `/admin/backup/1/download` as admin (expects 302) [TestActions / backup edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates backup/restore safety net is broken (data-loss risk)."""
        mock_db['fetch_one'].return_value = (1,)
        assert admin_client.get('/admin/backup/1/download').status_code == 302

    def test_download_huge_id(self, admin_client, mock_db):
        """Validates download huge id `/admin/backup/999999999/download` as admin (expects 302) [TestActions / backup edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates backup/restore safety net is broken (data-loss risk)."""
        mock_db['fetch_one'].return_value = None
        assert admin_client.get(
            '/admin/backup/999999999/download').status_code == 302

    def test_restore_short_row(self, admin_client, mock_db):
        """Validates restore short row `/admin/backup/1/restore` as admin (expects 302) [TestActions / backup edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates backup/restore safety net is broken (data-loss risk)."""
        mock_db['fetch_one'].return_value = (1,)
        assert admin_client.post(
            '/admin/backup/1/restore').status_code == 302

    def test_restore_non_completed(self, admin_client, mock_db):
        """Validates restore non completed `/admin/backup/1/restore` as admin (expects 302) [TestActions / backup edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates backup/restore safety net is broken (data-loss risk)."""
        mock_db['fetch_one'].return_value = (1, 'b.sql', 100, 'failed',
                                             'manual', None, '2026-01-01')
        assert admin_client.post(
            '/admin/backup/1/restore').status_code == 302

    def test_delete_short_row(self, admin_client, mock_db):
        """Validates delete short row `/admin/backup/1/delete` as admin (expects 404) [TestActions / backup edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates backup/restore safety net is broken (data-loss risk)."""
        mock_db['fetch_one'].side_effect = [None, (1,)]
        resp = admin_client.post('/admin/backup/1/delete')
        assert resp.status_code == 404

    def test_delete_missing(self, admin_client, mock_db):
        """Validates delete missing `/admin/backup/999/delete` as admin (expects 404) [TestActions / backup edge cases].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates backup/restore safety net is broken (data-loss risk)."""
        mock_db['fetch_one'].return_value = None
        resp = admin_client.post('/admin/backup/999/delete')
        assert resp.status_code == 404
        assert resp.get_json() == {'error': 'Backup not found.'}


class TestAuth:
    def test_matrix(self, client, student_client, librarian_client):
        """Validates matrix `/admin/backup` (expects 302) [TestAuth / backup edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates backup/restore safety net is broken (data-loss risk)."""
        assert client.get('/admin/backup').status_code == 302
        assert student_client.get('/admin/backup').status_code == 302
        assert librarian_client.get('/admin/backup').status_code == 302
        assert librarian_client.post(
            '/admin/backup/create').status_code == 302
        assert student_client.post(
            '/admin/backup/1/delete').status_code == 302
