"""Tests for the Procurement module: dashboard filter, status sync to requests, RBAC."""

import io
from datetime import date


ITEM = (1, 9, 'ordered', date(2026, 5, 1), None, None, None,
        'Clean Code', 'Robert Martin')


class TestProcurementAccess:
    def test_dashboard_requires_login(self, client, mock_db):
        resp = client.get('/librarian/procurement')
        assert resp.status_code == 302
        assert '/login' in resp.location

    def test_dashboard_forbidden_for_student(self, student_client, mock_db):
        resp = student_client.get('/librarian/procurement')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_update_requires_login(self, client, mock_db):
        resp = client.post('/librarian/procurement/1/update-status',
                           data={'order_status': 'ordered'})
        assert resp.status_code == 302


class TestProcurementDashboard:
    def test_renders_items(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = [ITEM]
        resp = librarian_client.get('/librarian/procurement')
        assert resp.status_code == 200
        assert b'Clean Code' in resp.data
        assert b'Robert Martin' in resp.data

    def test_status_filter_scopes_query(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/procurement?status=ordered')
        assert resp.status_code == 200
        item_calls = [c for c in mock_db['fetch_all'].call_args_list
                      if 'procurement_log' in c[0][0]]
        assert len(item_calls) == 1
        query, params = item_calls[0][0]
        assert 'JOIN request_records' in query
        assert params == ('ordered',)

    def test_invalid_status_falls_back_to_all(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/procurement?status=bogus')
        assert resp.status_code == 200
        item_calls = [c for c in mock_db['fetch_all'].call_args_list
                      if 'procurement_log' in c[0][0]]
        assert len(item_calls) == 1
        args = item_calls[0][0]
        assert len(args) == 1 or args[1] is None


class TestProcurementStatusSync:
    def _row(self, status='ordered'):
        return (1, 9, status, date(2026, 5, 1), None, None, None)

    def test_procured_closes_request(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = self._row()
        resp = librarian_client.post('/librarian/procurement/1/update-status',
                                     data={'order_status': 'procured'})
        assert resp.status_code == 302
        assert '/librarian/procurement' in resp.location
        queries = [c[0][0] for c in mock_db['execute'].call_args_list]
        assert any('UPDATE procurement_log' in q for q in queries)
        request_updates = [c for c in mock_db['execute'].call_args_list
                           if 'UPDATE request_records' in c[0][0]]
        assert len(request_updates) == 1
        assert 'procured' in request_updates[0][0][1]

    def test_cancelled_reopens_request(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = self._row()
        resp = librarian_client.post('/librarian/procurement/1/update-status',
                                     data={'order_status': 'cancelled'})
        assert resp.status_code == 302
        request_updates = [c for c in mock_db['execute'].call_args_list
                           if 'UPDATE request_records' in c[0][0]]
        assert len(request_updates) == 1
        assert 'approved' in request_updates[0][0][1]

    def test_non_terminal_status_leaves_request_alone(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = self._row()
        resp = librarian_client.post('/librarian/procurement/1/update-status',
                                     data={'order_status': 'ordered'})
        assert resp.status_code == 302
        queries = [c[0][0] for c in mock_db['execute'].call_args_list]
        assert any('UPDATE procurement_log' in q for q in queries)
        assert not any('UPDATE request_records' in q for q in queries)

    def test_invalid_status_rejected(self, librarian_client, mock_db):
        resp = librarian_client.post('/librarian/procurement/1/update-status',
                                     data={'order_status': 'bogus'})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_missing_row_rejected(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = None
        resp = librarian_client.post('/librarian/procurement/1/update-status',
                                     data={'order_status': 'procured'})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0


class TestSupplierUpload:
    def _csv(self, text):
        return {'file': (io.BytesIO(text.encode('utf-8')), 'suppliers.csv')}

    def test_upload_forbidden_for_student(self, student_client, mock_db):
        resp = student_client.post('/librarian/procurement/supplier-upload',
                                   data=self._csv('title\nDune\n'))
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_upload_no_file_rejected(self, librarian_client, mock_db):
        resp = librarian_client.post('/librarian/procurement/supplier-upload', data={})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_upload_non_csv_rejected(self, librarian_client, mock_db):
        resp = librarian_client.post(
            '/librarian/procurement/supplier-upload',
            data={'file': (io.BytesIO(b'title\nDune\n'), 'suppliers.txt')})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_upload_missing_title_column_rejected(self, librarian_client, mock_db):
        resp = librarian_client.post('/librarian/procurement/supplier-upload',
                                     data=self._csv('author\nHerbert\n'))
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_upload_replaces_catalog(self, librarian_client, mock_db):
        resp = librarian_client.post(
            '/librarian/procurement/supplier-upload',
            data=self._csv('title,author,supplier\nDune,Herbert,Acme\n1984,Orwell,Acme\n'))
        assert resp.status_code == 302
        queries = [c[0][0] for c in mock_db['execute'].call_args_list]
        assert queries[0].startswith('DELETE FROM supplier_catalog')
        inserts = [q for q in queries if q.startswith('INSERT INTO supplier_catalog')]
        assert len(inserts) == 2

    def test_dashboard_shows_supplier_section(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = [ITEM]
        mock_db['fetch_one'].return_value = (3,)
        resp = librarian_client.get('/librarian/procurement')
        assert resp.status_code == 200
        assert b'Supplier Book List' in resp.data
        assert b'Upload List' in resp.data


class TestSupplierMatchModel:
    def test_match_by_title(self, mock_db):
        from app.procurement.models import find_supplier_match
        mock_db['fetch_all'].return_value = [('Acme', 'Dune', 'Herbert')]
        rows = find_supplier_match('dune')
        assert rows == [('Acme', 'Dune', 'Herbert')]
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'supplier_catalog' in query
        assert 'dune' in params[0].lower()

    def test_blank_title_returns_empty(self, mock_db):
        from app.procurement.models import find_supplier_match
        assert find_supplier_match('  ') == []
        assert mock_db['fetch_all'].call_count == 0
