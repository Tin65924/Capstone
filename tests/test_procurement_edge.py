"""Edge-case regression tests for Procurement Management.

Covers `/librarian/procurement` and status updates: empty database,
`None` item lists, trailing-column reads (title/author must come from
the joined request, never audit columns), short rows, bogus/missing
statuses and records, all valid status transitions, XSS fields, and
the staff auth matrix. Everything must degrade gracefully — never 500.
"""

ITEM = (3, 7, 'for_ordering', '2026-01-05', None, None, None, None, None,
        'Data Science', 'J. Grus')


class TestEmptyDb:
    def test_page_empty(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        assert librarian_client.get('/librarian/procurement').status_code == 200

    def test_none_items(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = None
        assert librarian_client.get('/librarian/procurement').status_code == 200


class TestCardFields:
    def test_title_author_positions(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = [ITEM]
        body = librarian_client.get('/librarian/procurement').data.decode()
        assert 'Data Science' in body
        assert 'J. Grus' in body

    def test_short_row(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = [(3, 7, 'ordered')]
        assert librarian_client.get('/librarian/procurement').status_code == 200


class TestUpdateStatus:
    def test_bogus_status(self, librarian_client, mock_db):
        resp = librarian_client.post('/librarian/procurement/3/update-status',
                                     data={'order_status': 'drop_table'})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_missing_status(self, librarian_client, mock_db):
        resp = librarian_client.post('/librarian/procurement/3/update-status',
                                     data={})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_missing_record(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = []
        before = mock_db['execute'].call_count
        resp = librarian_client.post('/librarian/procurement/999/update-status',
                                     data={'order_status': 'ordered'})
        assert resp.status_code == 302
        updates = [c[0][0] for c in mock_db['execute'].call_args_list[before:]
                   if 'UPDATE procurement_log' in c[0][0]]
        assert updates == []

    def test_huge_id(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = []
        assert librarian_client.post(
            '/librarian/procurement/999999999/update-status',
            data={'order_status': 'ordered'}).status_code == 302

    def test_each_valid_status(self, librarian_client, mock_db):
        from app.procurement.models import VALID_STATUSES
        for st in VALID_STATUSES:
            mock_db['fetch_all'].return_value = [ITEM]
            mock_db['execute'].return_value = 1
            resp = librarian_client.post(
                '/librarian/procurement/3/update-status',
                data={'order_status': st})
            assert resp.status_code == 302, st


class TestXss:
    def test_evil_fields(self, librarian_client, mock_db):
        evil = '<script>alert(1)</script>'
        row = (3, 7, 'ordered', '2026-01-05', None, None, evil, None,
               None, evil, evil)
        mock_db['fetch_all'].return_value = [row]
        body = librarian_client.get('/librarian/procurement').data.decode()
        assert evil not in body


class TestAuth:
    def test_anon(self, client):
        assert client.get('/librarian/procurement').status_code == 302
        assert client.post(
            '/librarian/procurement/1/update-status').status_code == 302

    def test_student_blocked(self, student_client, mock_db):
        assert student_client.get('/librarian/procurement').status_code == 302
        resp = student_client.post('/librarian/procurement/1/update-status',
                                   data={'order_status': 'ordered'})
        assert resp.status_code == 302
        writes = [c[0][0] for c in mock_db['execute'].call_args_list
                  if 'UPDATE' in c[0][0] and 'audit_trail' not in c[0][0]]
        assert writes == []

    def test_faculty_blocked(self, faculty_client):
        assert faculty_client.get('/librarian/procurement').status_code == 302
