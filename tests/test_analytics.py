import io
import json

import pytest
from openpyxl import load_workbook


class TestAnalyticsAccess:
    def test_analytics_requires_login(self, client, mock_db):
        resp = client.get('/librarian/analytics')
        assert resp.status_code == 302
        assert '/login' in resp.location

    def test_analytics_forbidden_for_student(self, student_client, mock_db):
        resp = student_client.get('/librarian/analytics')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_analytics_allowed_for_librarian(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics')
        assert resp.status_code == 200


class TestAnalyticsModels:
    def test_books_borrowed_per_program(self, mock_db):
        from app.analytics.models import books_borrowed_per_program
        mock_db['fetch_all'].return_value = [('BSIT', 12), ('BSBA', 5)]
        assert books_borrowed_per_program() == [('BSIT', 12), ('BSBA', 5)]

    def test_books_borrowed_per_program_scoped_by_date(self, mock_db):
        from app.analytics.models import books_borrowed_per_program
        books_borrowed_per_program('2026-01-01', '2026-12-31')
        params = mock_db['fetch_all'].call_args[0][1]
        assert params == ('2026-01-01', '2026-12-31')

    def test_books_borrowed_per_program_no_dates_passes_none(self, mock_db):
        from app.analytics.models import books_borrowed_per_program
        books_borrowed_per_program(None, None)
        assert mock_db['fetch_all'].call_args[0][1] is None

    def test_utilization_rate(self, mock_db):
        from app.analytics.models import utilization_rate
        mock_db['fetch_one'].side_effect = [(10,), (2,)]
        assert utilization_rate() == 20.0

    def test_utilization_rate_guards_zero_collection(self, mock_db):
        from app.analytics.models import utilization_rate
        mock_db['fetch_one'].side_effect = [(0,), (0,)]
        assert utilization_rate() == 0.0

    def test_most_borrowed_titles(self, mock_db):
        from app.analytics.models import most_borrowed_titles
        mock_db['fetch_all'].return_value = [('Clean Code', 50)]
        result = most_borrowed_titles()
        assert result == [('Clean Code', 50)]
        params = mock_db['fetch_all'].call_args[0][1]
        assert params[-1] == 10

    def test_underutilized_titles(self, mock_db):
        from app.analytics.models import underutilized_titles
        mock_db['fetch_all'].return_value = [('Rare Book',)]
        assert underutilized_titles() == [('Rare Book',)]

    def test_save_report_snapshot(self, mock_db):
        from app.analytics.models import save_report_snapshot
        save_report_snapshot('most_borrowed_titles', {'preset': 'all'}, [['Clean Code', 5]], 3)
        query, params = mock_db['execute'].call_args[0]
        assert 'INSERT INTO analytics_cache' in query
        assert params[0] == 'most_borrowed_titles'
        assert isinstance(params[1], str)   # filter_params serialized to JSON
        assert isinstance(params[2], str)   # kpi_data serialized to JSON


class TestAnalyticsPage:
    def test_page_embeds_kpi_payload(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].return_value = [('BSIT', 12)]
        resp = librarian_client.get('/librarian/analytics')
        assert resp.status_code == 200
        assert b'id="kpi-data"' in resp.data
        assert b'Add KPI' in resp.data
        assert b'Export All' in resp.data

    def test_page_skips_query_when_collection_nonzero(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (10,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics')
        assert resp.status_code == 200

    def test_invalid_date_falls_back_to_all_time(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (1,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics?from=not-a-date&to=also-bad')
        assert resp.status_code == 200


class TestExportCsv:
    def test_export_requires_login(self, client, mock_db):
        resp = client.post('/librarian/analytics/export', data={'kpi_type': 'most_borrowed_titles'})
        assert resp.status_code == 302

    def test_export_rejects_invalid_kpi(self, librarian_client, mock_db):
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'not_a_kpi'})
        assert resp.status_code == 302
        assert '/librarian/analytics' in resp.location

    def test_export_csv_single_kpi(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = [('Clean Code', 50), ('Refactoring', 30)]
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'most_borrowed_titles', 'format': 'csv'})
        assert resp.status_code == 200
        assert 'text/csv' in resp.content_type
        assert 'attachment' in resp.headers['Content-Disposition']
        body = resp.data.decode('utf-8-sig')
        assert 'Title' in body and 'Borrow Count' in body
        assert 'Clean Code' in body and '50' in body
        # snapshot row recorded
        query = mock_db['execute'].call_args[0][0]
        assert 'INSERT INTO analytics_cache' in query

    def test_export_utilization_rate(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [(10,), (2,)]
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'utilization_rate', 'format': 'csv'})
        assert resp.status_code == 200
        body = resp.data.decode('utf-8-sig')
        assert 'Utilization Rate' in body and '20' in body

    def test_export_csv_all_sections(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (10,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'all', 'format': 'csv'})
        assert resp.status_code == 200
        body = resp.data.decode('utf-8-sig')
        assert 'Books Borrowed per Program' in body
        assert 'Most Borrowed Titles' in body
        assert 'Underutilized Titles' in body


class TestExportXlsx:
    def test_export_xlsx_single_kpi(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = [('Clean Code', 50)]
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'most_borrowed_titles', 'format': 'xlsx'})
        assert resp.status_code == 200
        assert 'spreadsheetml' in resp.content_type
        wb = load_workbook(io.BytesIO(resp.data))
        ws = wb.active
        assert ws['A1'].value == 'Title'
        assert ws['A2'].value == 'Clean Code'
        assert ws['B2'].value == 50

    def test_export_xlsx_all_has_sheet_per_kpi(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (10,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'all', 'format': 'xlsx'})
        assert resp.status_code == 200
        wb = load_workbook(io.BytesIO(resp.data))
        assert 'Books Borrowed per Program' in wb.sheetnames
        assert 'Most Borrowed Titles' in wb.sheetnames