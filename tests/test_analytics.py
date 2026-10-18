import io
import json

import pytest
from openpyxl import load_workbook


class TestAnalyticsAccess:
    def test_analytics_requires_login(self, client, mock_db):
        """Validates analytics requires login `/librarian/analytics` (expects 302) [TestAnalyticsAccess / analytics].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = client.get('/librarian/analytics')
        assert resp.status_code == 302
        assert '/login' in resp.location

    def test_analytics_forbidden_for_student(self, student_client, mock_db):
        """Validates analytics forbidden for student `/librarian/analytics` as student (expects 302) [TestAnalyticsAccess / analytics].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates dashboard/stats shown to staff are wrong."""
        resp = student_client.get('/librarian/analytics')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_analytics_allowed_for_librarian(self, librarian_client, mock_db):
        """Validates analytics allowed for librarian `/librarian/analytics` as librarian (expects 200) [TestAnalyticsAccess / analytics].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics')
        assert resp.status_code == 200


class TestAnalyticsModels:
    def test_books_borrowed_per_program(self, mock_db):
        """Validates books borrowed per program [TestAnalyticsModels / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import books_borrowed_per_program
        mock_db['fetch_all'].return_value = [('BSIT', 12), ('BSBA', 5)]
        assert books_borrowed_per_program() == [('BSIT', 12), ('BSBA', 5)]

    def test_books_borrowed_per_program_scoped_by_date(self, mock_db):
        """Validates books borrowed per program scoped by date [TestAnalyticsModels / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import books_borrowed_per_program
        books_borrowed_per_program('2026-01-01', '2026-12-31')
        params = mock_db['fetch_all'].call_args[0][1]
        assert params == ('2026-01-01', '2026-12-31')

    def test_books_borrowed_per_program_no_dates_passes_none(self, mock_db):
        """Validates books borrowed per program no dates passes none [TestAnalyticsModels / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import books_borrowed_per_program
        books_borrowed_per_program(None, None)
        assert mock_db['fetch_all'].call_args[0][1] is None

    def test_utilization_rate(self, mock_db):
        """Validates utilization rate [TestAnalyticsModels / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import utilization_rate
        mock_db['fetch_one'].side_effect = [(10,), (2,)]
        assert utilization_rate() == 20.0

    def test_utilization_rate_guards_zero_collection(self, mock_db):
        """Validates utilization rate guards zero collection [TestAnalyticsModels / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import utilization_rate
        mock_db['fetch_one'].side_effect = [(0,), (0,)]
        assert utilization_rate() == 0.0

    def test_most_borrowed_titles(self, mock_db):
        """Validates most borrowed titles [TestAnalyticsModels / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import most_borrowed_titles
        mock_db['fetch_all'].return_value = [('Clean Code', 50)]
        result = most_borrowed_titles()
        assert result == [('Clean Code', 50)]
        params = mock_db['fetch_all'].call_args[0][1]
        assert params[-1] == 10

    def test_underutilized_titles(self, mock_db):
        """Validates underutilized titles [TestAnalyticsModels / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import underutilized_titles
        mock_db['fetch_all'].return_value = [('Rare Book',)]
        assert underutilized_titles() == [('Rare Book',)]

    def test_circulation_overview_returns_tuple(self, mock_db):
        """Validates circulation overview returns tuple [TestAnalyticsModels / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import circulation_overview
        mock_db['fetch_one'].side_effect = [(10,), (4,), (2,), (3.0,), (6,), (7,)]
        assert circulation_overview() == (10, 4, 2, 3.0, 60.0, 7)

    def test_circulation_overview_scoped_by_date(self, mock_db):
        """Validates circulation overview scoped by date [TestAnalyticsModels / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from datetime import date
        from app.analytics.models import circulation_overview
        mock_db['fetch_one'].side_effect = [(1,), (1,), (0,), (1.0,), (1,), (1,)]
        circulation_overview(date(2026, 1, 1), date(2026, 12, 31))
        params = mock_db['fetch_one'].call_args_list[0][0][1]
        assert params == (date(2026, 1, 1), date(2026, 12, 31))

    def test_save_report_snapshot(self, mock_db):
        """Validates save report snapshot [TestAnalyticsModels / analytics].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import save_report_snapshot
        save_report_snapshot('most_borrowed_titles', {'preset': 'all'}, [['Clean Code', 5]], 3)
        query, params = mock_db['execute'].call_args[0]
        assert 'INSERT INTO analytics_cache' in query
        assert params[0] == 'most_borrowed_titles'
        assert isinstance(params[1], str)   # filter_params serialized to JSON
        assert isinstance(params[2], str)   # kpi_data serialized to JSON


class TestAnalyticsPage:
    def test_page_embeds_dashboard_payload(self, librarian_client, mock_db):
        """Validates page embeds dashboard payload `/librarian/analytics` as librarian (expects 200) [TestAnalyticsPage / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].return_value = [('BSIT', 12)]
        resp = librarian_client.get('/librarian/analytics')
        assert resp.status_code == 200
        assert b'id="dashboard-data"' in resp.data
        assert b'Export All' in resp.data
        # custom KPI board is removed: no board markup, payload, or modals
        assert b'Custom KPI Board' not in resp.data
        assert b'id="kpi-data"' not in resp.data
        assert b'id="board"' not in resp.data
        assert b'exportDashboard' in resp.data

    def test_export_buttons_use_per_tab_sections(self, librarian_client, mock_db):
        """Validates export buttons use per tab sections `/librarian/analytics` as librarian (expects 200) [TestAnalyticsPage / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong.

Each tab's Export Report targets its own sections; Export All is the union."""
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics')
        assert resp.status_code == 200
        assert b'exportDashboard(COLLECTION_SECTIONS)' in resp.data
        assert b'exportDashboard(LIBRARY_SECTIONS)' in resp.data
        assert b'exportDashboard(DEPARTMENT_SECTIONS)' in resp.data
        assert b'exportDashboard(ALL_DASHBOARD_SECTIONS)' in resp.data
        assert b'borrowers_by_department' in resp.data
        assert b'overdue_by_department' in resp.data

    def test_no_riverside_credit_line(self, librarian_client, mock_db):
        """Validates no riverside credit line `/librarian/analytics` as librarian (expects 200) [TestAnalyticsPage / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics')
        assert resp.status_code == 200
        assert b'Inspired by Riverside' not in resp.data

    def test_attention_cards_link_to_filtered_catalog(self, librarian_client, mock_db):
        """Validates attention cards link to filtered catalog `/librarian/analytics` as librarian (expects 200) [TestAnalyticsPage / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics')
        assert resp.status_code == 200
        for param in (b'copy_status=overdue', b'copy_status=lost_damaged'):
            assert param in resp.data
        assert b'copy_status=maintenance' not in resp.data

    def test_page_skips_query_when_collection_nonzero(self, librarian_client, mock_db):
        """Validates page skips query when collection nonzero `/librarian/analytics` as librarian (expects 200) [TestAnalyticsPage / analytics].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = (10,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics')
        assert resp.status_code == 200

    def test_invalid_date_falls_back_to_all_time(self, librarian_client, mock_db):
        """Validates invalid date falls back to all time `/librarian/analytics?from=not-a-date&to=also-bad` as librarian (expects 200) [TestAnalyticsPage / analytics].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = (1,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics?from=not-a-date&to=also-bad')
        assert resp.status_code == 200

    def test_semester_ignores_stale_dates(self, librarian_client, mock_db):
        """Validates semester ignores stale dates `/librarian/analytics?preset=semester&from=2020-01-01&to=2020-12-31` as librarian (expects 200) [TestAnalyticsPage / analytics].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from datetime import date
        mock_db['fetch_one'].side_effect = [(10,), (2,)]
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get(
            '/librarian/analytics?preset=semester&from=2020-01-01&to=2020-12-31')
        assert resp.status_code == 200
        today = date.today()
        if today.month >= 8:
            expected = (date(today.year, 8, 1), date(today.year, 12, 31))
        else:
            expected = (date(today.year, 1, 1), date(today.year, 5, 31))
        params = mock_db['fetch_all'].call_args_list[0][0][1]
        assert params == expected

    def test_invalid_preset_ignores_dates(self, librarian_client, mock_db):
        """Validates invalid preset ignores dates `/librarian/analytics?preset=bogus&from=2020-01-01&to=2020-12-31` as librarian (expects 200) [TestAnalyticsPage / analytics].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].side_effect = [(10,), (2,)]
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get(
            '/librarian/analytics?preset=bogus&from=2020-01-01&to=2020-12-31')
        assert resp.status_code == 200
        params = mock_db['fetch_all'].call_args_list[0][0][1]
        assert params is None


class TestKpiJson:
    def test_kpi_json_requires_login(self, client, mock_db):
        """Validates kpi json requires login `/librarian/analytics/kpi?kpi_type=most_borrowed_titles` (expects 302) [TestKpiJson / analytics].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = client.get('/librarian/analytics/kpi?kpi_type=most_borrowed_titles')
        assert resp.status_code == 302

    def test_kpi_json_rejects_invalid_type(self, librarian_client, mock_db):
        """Validates kpi json rejects invalid type `/librarian/analytics/kpi?kpi_type=bogus` as librarian (expects 400) [TestKpiJson / analytics].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        resp = librarian_client.get('/librarian/analytics/kpi?kpi_type=bogus')
        assert resp.status_code == 400

    def test_kpi_json_returns_data(self, librarian_client, mock_db):
        """Validates kpi json returns data `/librarian/analytics/kpi?kpi_type=most_borrowed_titles&preset=year` as librarian (expects 200) [TestKpiJson / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_all'].return_value = [('Clean Code', 50)]
        resp = librarian_client.get('/librarian/analytics/kpi?kpi_type=most_borrowed_titles&preset=year')
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['kpi_type'] == 'most_borrowed_titles'
        assert body['data'] == [['Clean Code', 50]]

    def test_kpi_json_passes_dates(self, librarian_client, mock_db):
        """Validates kpi json passes dates `/librarian/analytics/kpi?kpi_type=underutilized_titles&from=2026-01-01&to=2026-12-31` as librarian (expects 200) [TestKpiJson / analytics].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from datetime import date
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics/kpi?kpi_type=underutilized_titles&from=2026-01-01&to=2026-12-31')
        assert resp.status_code == 200
        params = mock_db['fetch_all'].call_args[0][1]
        assert params[:2] == (date(2026, 1, 1), date(2026, 12, 31))
        assert params[-1] == 10

    def test_kpi_json_utilization_rate(self, librarian_client, mock_db):
        """Validates kpi json utilization rate `/librarian/analytics/kpi?kpi_type=utilization_rate` as librarian (expects 200) [TestKpiJson / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].side_effect = [(10,), (2,)]
        resp = librarian_client.get('/librarian/analytics/kpi?kpi_type=utilization_rate')
        assert resp.status_code == 200
        assert resp.get_json()['data'] == 20.0


class TestExportCsv:
    def test_export_requires_login(self, client, mock_db):
        """Validates export requires login `/librarian/analytics/export` (expects 302) [TestExportCsv / analytics].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = client.post('/librarian/analytics/export', data={'kpi_type': 'most_borrowed_titles'})
        assert resp.status_code == 302

    def test_export_rejects_invalid_kpi(self, librarian_client, mock_db):
        """Validates export rejects invalid kpi `/librarian/analytics/export` as librarian (expects 302) [TestExportCsv / analytics].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates dashboard/stats shown to staff are wrong."""
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'not_a_kpi'})
        assert resp.status_code == 302
        assert '/librarian/analytics' in resp.location

    def test_export_csv_single_kpi(self, librarian_client, mock_db):
        """Validates export csv single kpi `/librarian/analytics/export` as librarian (expects 200) [TestExportCsv / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched; wrong/absent SQL call or placeholder mismatch.
    Failure indicates dashboard/stats shown to staff are wrong.

CSV format was removed — legacy csv requests now return the polished PDF."""
        mock_db['fetch_all'].return_value = [('Clean Code', 50), ('Refactoring', 30)]
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'most_borrowed_titles', 'format': 'csv'})
        assert resp.status_code == 200
        assert resp.content_type == 'application/pdf'
        assert resp.data[:4] == b'%PDF'
        assert 'attachment' in resp.headers['Content-Disposition']
        # snapshot row recorded
        query = mock_db['execute'].call_args[0][0]
        assert 'INSERT INTO analytics_cache' in query

    def test_export_utilization_rate(self, librarian_client, mock_db):
        """Validates export utilization rate `/librarian/analytics/export` as librarian (expects 200) [TestExportCsv / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].side_effect = [(10,), (2,)]
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'utilization_rate', 'format': 'csv'})
        assert resp.status_code == 200
        assert resp.content_type == 'application/pdf'
        assert resp.data[:4] == b'%PDF'

    def test_export_csv_all_sections(self, librarian_client, mock_db):
        """Validates export csv all sections `/librarian/analytics/export` as librarian (expects 200) [TestExportCsv / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = (10,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'all', 'format': 'csv'})
        assert resp.status_code == 200
        assert resp.content_type == 'application/pdf'
        assert resp.data[:4] == b'%PDF'


class TestExportXlsx:
    def test_export_xlsx_single_kpi(self, librarian_client, mock_db):
        """Validates export xlsx single kpi `/librarian/analytics/export` as librarian (expects 200) [TestExportXlsx / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong.

XLSX format was removed — legacy xlsx requests now return the polished PDF."""
        mock_db['fetch_all'].return_value = [('Clean Code', 50)]
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'most_borrowed_titles', 'format': 'xlsx'})
        assert resp.status_code == 200
        assert resp.content_type == 'application/pdf'
        assert resp.data[:4] == b'%PDF'

    def test_export_xlsx_all_has_sheet_per_kpi(self, librarian_client, mock_db):
        """Validates export xlsx all has sheet per kpi `/librarian/analytics/export` as librarian (expects 200) [TestExportXlsx / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = (10,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'all', 'format': 'xlsx'})
        assert resp.status_code == 200
        assert resp.content_type == 'application/pdf'
        assert resp.data[:4] == b'%PDF'

    def test_export_pdf_single_kpi(self, librarian_client, mock_db):
        """Validates export pdf single kpi `/librarian/analytics/export` as librarian (expects 200) [TestExportXlsx / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_all'].return_value = [('Clean Code', 50)]
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'most_borrowed_titles', 'format': 'pdf'})
        assert resp.status_code == 200
        assert resp.content_type == 'application/pdf'
        assert resp.data[:4] == b'%PDF'

    def test_export_pdf_all_sections(self, librarian_client, mock_db):
        """Validates export pdf all sections `/librarian/analytics/export` as librarian (expects 200) [TestExportXlsx / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = (10,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'all', 'format': 'pdf'})
        assert resp.status_code == 200
        assert resp.content_type == 'application/pdf'
        assert resp.data[:4] == b'%PDF'

    def test_export_all_honors_kpi_types_list(self, librarian_client, mock_db):
        """Validates export all honors kpi types list `/librarian/analytics/export` as librarian (expects 200) [TestExportXlsx / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched; wrong/absent SQL call or placeholder mismatch.
    Failure indicates dashboard/stats shown to staff are wrong.

Repeated kpi_types[] fields export only the selected KPIs."""
        mock_db['fetch_one'].side_effect = [(10,), (2,)]
        mock_db['fetch_all'].return_value = [('Clean Code', 50)]
        resp = librarian_client.post(
            '/librarian/analytics/export',
            data={'kpi_type': 'all', 'format': 'pdf',
                  'kpi_types[]': ['most_borrowed_titles', 'utilization_rate']})
        assert resp.status_code == 200
        assert resp.data[:4] == b'%PDF'
        snapshots = [c[0][1][0] for c in mock_db['execute'].call_args_list
                     if 'INSERT INTO analytics_cache' in c[0][0]]
        assert sorted(snapshots) == ['most_borrowed_titles', 'utilization_rate']


class TestDashboardNormalization:
    def test_pair_normalizes_dates_to_iso(self, librarian_client, mock_db):
        """Validates pair normalizes dates to iso `/librarian/analytics/dashboard` as librarian (expects 200) [TestDashboardNormalization / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong.

Trend DATEs must render as ISO YYYY-MM-DD, not RFC-2822."""
        from datetime import date
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = [(date(2026, 8, 15), 3)]
        resp = librarian_client.get('/librarian/analytics/dashboard')
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['circulation']['trend'] == [['2026-08-15', 3]]
        assert 'Aug' not in str(body['circulation']['trend'])

    def test_circulation_overview_timedelta_avg(self, mock_db):
        """Validates circulation overview timedelta avg [TestDashboardNormalization / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong.

timedelta AVG (interval) converts to fractional days."""
        from datetime import timedelta
        from app.analytics.models import circulation_overview
        mock_db['fetch_one'].side_effect = [
            (10,), (4,), (2,), (timedelta(days=3, hours=12),), (6,), (7,)]
        assert circulation_overview() == (10, 4, 2, 3.5, 60.0, 7)

class TestDashboardExport:
    def test_single_dashboard_section(self, librarian_client, mock_db):
        """Validates single dashboard section `/librarian/analytics/export` as librarian (expects 200) [TestDashboardExport / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched; wrong/absent SQL call or placeholder mismatch.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_all'].return_value = [('Science', 30)]
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'top_categories', 'format': 'pdf'})
        assert resp.status_code == 200
        assert resp.data[:4] == b'%PDF'
        query = mock_db['execute'].call_args[0][0]
        assert 'INSERT INTO analytics_cache' in query

    def test_quick_report_department_usage(self, librarian_client, mock_db):
        """Validates quick report department usage `/librarian/analytics/export` as librarian (expects 200) [TestDashboardExport / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched; wrong/absent SQL call or placeholder mismatch.
    Failure indicates dashboard/stats shown to staff are wrong.

Quick Reports must export their own section, not the old board."""
        mock_db['fetch_all'].return_value = [('BSIT', 12)]
        resp = librarian_client.post(
            '/librarian/analytics/export',
            data={'kpi_type': 'all', 'format': 'pdf',
                  'kpi_types': 'books_borrowed_per_program'})
        assert resp.status_code == 200
        assert resp.data[:4] == b'%PDF'
        snapshots = [c[0][1][0] for c in mock_db['execute'].call_args_list
                     if 'INSERT INTO analytics_cache' in c[0][0]]
        assert snapshots == ['books_borrowed_per_program']

    def test_export_department_breakdowns(self, librarian_client, mock_db):
        """Validates export department breakdowns `/librarian/analytics/export` as librarian (expects 200) [TestDashboardExport / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched; wrong/absent SQL call or placeholder mismatch.
    Failure indicates dashboard/stats shown to staff are wrong.

Borrower/overdue-by-department charts are exportable sections."""
        mock_db['fetch_all'].return_value = [('BSIT', 12)]
        resp = librarian_client.post(
            '/librarian/analytics/export',
            data={'kpi_type': 'all', 'format': 'pdf',
                  'kpi_types': 'borrowers_by_department,overdue_by_department'})
        assert resp.status_code == 200
        assert resp.data[:4] == b'%PDF'
        snapshots = [c[0][1][0] for c in mock_db['execute'].call_args_list
                     if 'INSERT INTO analytics_cache' in c[0][0]]
        assert snapshots == ['borrowers_by_department', 'overdue_by_department']

    def test_export_department_breakdowns_honor_program_filter(self, librarian_client, mock_db):
        """Validates export department breakdowns honor program filter `/librarian/analytics/export` as librarian (expects 200) [TestDashboardExport / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong.

Usage-scoped breakdowns filter by the selected program."""
        mock_db['fetch_all'].return_value = [('BSIT', 12)]
        resp = librarian_client.post(
            '/librarian/analytics/export',
            data={'kpi_type': 'all', 'format': 'pdf',
                  'kpi_types': 'borrowers_by_department',
                  'department': 'BSIT'})
        assert resp.status_code == 200
        assert resp.data[:4] == b'%PDF'
        params = [c[0][1] for c in mock_db['fetch_all'].call_args_list]
        assert any(p and 'BSIT' in p for p in params)

    def test_export_department_leaderboard(self, librarian_client, mock_db):
        """Validates export department leaderboard `/librarian/analytics/export` as librarian (expects 200) [TestDashboardExport / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched; wrong/absent SQL call or placeholder mismatch.
    Failure indicates dashboard/stats shown to staff are wrong.

Department Leaderboard is an exportable department-tab section."""
        mock_db['fetch_all'].return_value = [('BSIT', 12, 5, 1)]
        resp = librarian_client.post(
            '/librarian/analytics/export',
            data={'kpi_type': 'all', 'format': 'pdf',
                  'kpi_types': 'department_leaderboard'})
        assert resp.status_code == 200
        assert resp.data[:4] == b'%PDF'
        snapshots = [c[0][1][0] for c in mock_db['execute'].call_args_list
                     if 'INSERT INTO analytics_cache' in c[0][0]]
        assert snapshots == ['department_leaderboard']

    def test_export_department_leaderboard_honors_program_filter(
            self, librarian_client, mock_db):
        """Validates export department leaderboard honors program filter `/librarian/analytics/export` as librarian (expects 200) [TestDashboardExport / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_all'].return_value = [('BSIT', 12, 5, 1)]
        resp = librarian_client.post(
            '/librarian/analytics/export',
            data={'kpi_type': 'all', 'format': 'pdf',
                  'kpi_types': 'department_leaderboard',
                  'department': 'BSIT'})
        assert resp.status_code == 200
        assert resp.data[:4] == b'%PDF'
        params = [c[0][1] for c in mock_db['fetch_all'].call_args_list]
        assert any(p and 'BSIT' in p for p in params)

    def test_tab_style_export_list(self, librarian_client, mock_db):
        """Validates tab style export list `/librarian/analytics/export` as librarian (expects 200) [TestDashboardExport / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched; wrong/absent SQL call or placeholder mismatch.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = (10,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.post(
            '/librarian/analytics/export',
            data={'kpi_type': 'all', 'format': 'pdf',
                  'kpi_types': 'circulation_summary,trend_borrowings,top_books'})
        assert resp.status_code == 200
        assert resp.data[:4] == b'%PDF'
        snapshots = [c[0][1][0] for c in mock_db['execute'].call_args_list
                     if 'INSERT INTO analytics_cache' in c[0][0]]
        assert sorted(snapshots) == ['circulation_summary', 'top_books', 'trend_borrowings']

    def test_wide_table_section_renders(self, librarian_client, mock_db):
        """Validates wide table section renders `/librarian/analytics/export` as librarian (expects 200) [TestDashboardExport / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong.

9-column recent_circulation must not break the PDF table builder."""
        from datetime import date
        mock_db['fetch_all'].return_value = [
            (date(2026, 5, 1), 7, 'A U', 'Student', 'T', 'A', 'borrow',
             date(2026, 5, 15), 'active'),
        ]
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'recent_circulation', 'format': 'pdf'})
        assert resp.status_code == 200
        assert resp.data[:4] == b'%PDF'

    def test_empty_selection_still_returns_pdf(self, librarian_client, mock_db):
        """Validates empty selection still returns pdf `/librarian/analytics/export` as librarian (expects 200) [TestDashboardExport / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'all', 'format': 'pdf',
                                           'kpi_types': 'not_a_real_kpi'})
        assert resp.status_code == 200
        assert resp.data[:4] == b'%PDF'

    def test_export_escapes_markup_in_titles(self, librarian_client, mock_db):
        """Validates export escapes markup in titles `/librarian/analytics/export` as librarian (expects 200) [TestDashboardExport / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong.

Titles with <...>/& must not 500 the PDF (reportlab XML parse)."""
        mock_db['fetch_all'].return_value = [
            ('A <b>Bold</b> Title & More', 'Auth <X>', 5),
        ]
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'all', 'format': 'pdf',
                                           'kpi_types': 'top_books'})
        assert resp.status_code == 200
        assert resp.data[:4] == b'%PDF'

    def test_export_survives_snapshot_failure(self, librarian_client, mock_db):
        """Validates export survives snapshot failure `/librarian/analytics/export` as librarian (expects 200) [TestDashboardExport / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched; wrong/absent SQL call or placeholder mismatch.
    Failure indicates dashboard/stats shown to staff are wrong.

A failing analytics_cache write must not 500 the export."""
        mock_db['fetch_all'].return_value = [('BSIT', 12)]

        orig_execute = mock_db['execute']

        def _fail_insert(query, params=None):
            """Test helper _fail_insert: build mocked data or DB stub for the test."""
            if 'INSERT INTO analytics_cache' in query:
                raise Exception('cache db down')
            return orig_execute(query, params) if callable(orig_execute) else []

        mock_db['execute'].side_effect = _fail_insert
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'books_borrowed_per_program',
                                           'format': 'pdf'})
        assert resp.status_code == 200
        assert resp.data[:4] == b'%PDF'

    def test_export_rejects_get(self, librarian_client, mock_db):
        """Validates export rejects get `/librarian/analytics/export` as librarian (expects 405) [TestDashboardExport / analytics].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        assert librarian_client.get('/librarian/analytics/export').status_code == 405

    def test_jsonable_handles_dates_and_decimals(self):
        """Validates jsonable handles dates and decimals [TestDashboardExport / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        import decimal
        from datetime import date
        from app.analytics.routes import _jsonable
        assert _jsonable([(date(2026, 5, 1), decimal.Decimal('4.5'))]) == [['2026-05-01', 4.5]]
        assert _jsonable(20.0) == 20.0


class TestReportCharts:
    def _export(self, librarian_client, kpi_type, **overrides):
        """Test helper _export: build mocked data or DB stub for the test."""
        data = {'kpi_type': kpi_type, 'format': 'pdf'}
        data.update(overrides)
        resp = librarian_client.post('/librarian/analytics/export', data=data)
        assert resp.status_code == 200
        assert resp.content_type == 'application/pdf'
        assert resp.data[:4] == b'%PDF'
        return resp.data

    def test_pie_sections(self, librarian_client, mock_db):
        """Validates pie sections as librarian [TestReportCharts / analytics].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_all'].return_value = [('A', 10), ('B', 5), ('C', 0)]
        mock_db['fetch_one'].return_value = (20,)
        for kpi in ('copies_by_status', 'top_categories', 'by_user_type',
                    'collection_by_category'):
            self._export(librarian_client, kpi)

    def test_pie_all_zero_skipped(self, librarian_client, mock_db):
        """Validates pie all zero skipped as librarian [TestReportCharts / analytics].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_all'].return_value = [('A', 0)]
        mock_db['fetch_one'].return_value = (0,)
        self._export(librarian_client, 'copies_by_status')

    def test_pie_many_slices_capped(self, librarian_client, mock_db):
        """Validates pie many slices capped as librarian [TestReportCharts / analytics].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_all'].return_value = [(f'Cat {i}', i + 1) for i in range(15)]
        self._export(librarian_client, 'top_categories')

    def test_line_sections(self, librarian_client, mock_db):
        """Validates line sections as librarian [TestReportCharts / analytics].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from datetime import date, timedelta
        base = date(2026, 5, 1)
        mock_db['fetch_all'].return_value = [
            (base + timedelta(days=i), (i * 7) % 13) for i in range(10)]
        self._export(librarian_client, 'trend_borrowings')
        self._export(librarian_client, 'trend_overdue')

    def test_line_long_trend_strided(self, librarian_client, mock_db):
        """Validates line long trend strided as librarian [TestReportCharts / analytics].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from datetime import date, timedelta
        base = date(2026, 1, 1)
        mock_db['fetch_all'].return_value = [
            (base + timedelta(days=i), i % 7 + 1) for i in range(200)]
        self._export(librarian_client, 'trend_borrowings')

    def test_bar_sections(self, librarian_client, mock_db):
        """Validates bar sections as librarian [TestReportCharts / analytics].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_all'].return_value = [
            ('Some Very Long Book Title That Overflows', 'Author Name Here', 42),
            ('B', 'C', 7),
        ]
        for kpi in ('top_books', 'high_demand'):
            self._export(librarian_client, kpi)
        mock_db['fetch_all'].return_value = [(f'Program {i}', i + 1) for i in range(12)]
        self._export(librarian_client, 'books_borrowed_per_program')
        mock_db['fetch_all'].return_value = [('Clean Code', 50)]
        self._export(librarian_client, 'most_borrowed_titles')

    def test_non_numeric_values_do_not_crash(self, librarian_client, mock_db):
        """Validates non numeric values do not crash as librarian [TestReportCharts / analytics].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_all'].return_value = [('A', 'oops'), (None, None)]
        self._export(librarian_client, 'top_categories')
        self._export(librarian_client, 'trend_borrowings')

    def test_empty_section_no_chart(self, librarian_client, mock_db):
        """Validates empty section no chart as librarian [TestReportCharts / analytics].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_all'].return_value = []
        mock_db['fetch_one'].return_value = (0,)
        self._export(librarian_client, 'top_books')

    def test_charts_embedded_in_pdf(self, librarian_client, mock_db):
        """Validates charts embedded in pdf as librarian [TestReportCharts / analytics].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates dashboard/stats shown to staff are wrong.

A charted section must produce vector drawing ops in the PDF."""
        mock_db['fetch_all'].return_value = [('Science', 30), ('Arts', 10)]
        with_charts = self._export(librarian_client, 'top_categories')
        mock_db['fetch_all'].return_value = []
        mock_db['fetch_one'].return_value = (0,)
        without_charts = self._export(librarian_client, 'underutilized_titles')
        assert len(with_charts) > len(without_charts)


class TestChartFilterModels:
    def test_borrowed_per_program_department_filter(self, mock_db):
        """Validates borrowed per program department filter [TestChartFilterModels / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import books_borrowed_per_program
        mock_db['fetch_all'].return_value = [('BSIT', 12)]
        assert books_borrowed_per_program('2026-01-01', '2026-12-31', ['BSIT', 'BSBA']) == [('BSIT', 12)]
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'b.department IN (%s, %s)' in query
        assert params == ('2026-01-01', '2026-12-31', 'BSIT', 'BSBA')

    def test_borrowed_per_program_blank_departments_ignored(self, mock_db):
        """Validates borrowed per program blank departments ignored [TestChartFilterModels / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import books_borrowed_per_program
        mock_db['fetch_all'].return_value = []
        books_borrowed_per_program(None, None, ['', '  '])
        assert 'b.department IN' not in mock_db['fetch_all'].call_args[0][0]

    def test_user_type_role_filter(self, mock_db):
        """Validates user type role filter [TestChartFilterModels / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import borrowings_by_user_type
        mock_db['fetch_all'].return_value = [('Student', 40)]
        assert borrowings_by_user_type(None, None, ['Student']) == [('Student', 40)]
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'r.role_name IN (%s)' in query
        assert params == ('Student',)

    def test_collection_category_multi_select(self, mock_db):
        """Validates collection category multi select [TestChartFilterModels / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import collection_by_category
        mock_db['fetch_all'].return_value = [('Science', 3)]
        assert collection_by_category(None, None, ['Science', 'Arts']) == [('Science', 3)]
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'LOWER(COALESCE(ct.name, b.subject_classification)) IN (%s, %s)' in query
        assert params == ('science', 'arts')

    def test_collection_category_case_insensitive_and_others(self, mock_db):
        """Validates collection category case insensitive and others [TestChartFilterModels / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import collection_by_category
        mock_db['fetch_all'].return_value = []
        collection_by_category(None, None, ['PHYSICS', 'Others', '  '])
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'LOWER(COALESCE(ct.name, b.subject_classification)) IN (%s)' in query
        assert "b.subject_classification = ''" in query
        assert params == ('physics',)

    def test_collection_category_no_filter_unchanged(self, mock_db):
        """Validates collection category no filter unchanged [TestChartFilterModels / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import collection_by_category
        mock_db['fetch_all'].return_value = []
        collection_by_category()
        assert mock_db['fetch_all'].call_args[0][1] is None

    def test_copies_by_status_summary(self, mock_db):
        """Validates copies by status summary [TestChartFilterModels / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import copies_by_status_summary
        mock_db['fetch_one'].side_effect = [(100,), (5,), (0,)]
        mock_db['fetch_all'].side_effect = [
            [('active', 20), ('overdue', 3)],
            [('available', 60), ('borrowed', 20), ('lost', 1)],
        ]
        rows = dict(copies_by_status_summary())
        assert rows['Available'] == 100 - 20 - 3 - 5 - 1
        assert rows['Borrowed'] == 20
        assert rows['Reserved'] == 5

    def test_circulation_overview_no_crash(self, mock_db):
        """Validates circulation overview no crash [TestChartFilterModels / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong.

Regression: the overview query builder must not raise IndexError."""
        from app.analytics.models import circulation_overview
        mock_db['fetch_one'].side_effect = [
            (100,), (40,), (5,), (4.5,), (90,), (12,),
        ]
        assert circulation_overview('2026-05-01', '2026-05-31') == (100, 40, 5, 4.5, 90.0, 12)

    def test_borrow_type_filter_applies(self, mock_db):
        """Validates borrow type filter applies [TestChartFilterModels / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics import models
        cases = [
            (models.borrowings_trend, 'borrow_type = %s'),
            (models.overdue_trend, 'borrow_type = %s'),
            (models.top_borrowed_categories, 'c.borrow_type = %s'),
            (models.top_borrowed_books_detailed, 'c.borrow_type = %s'),
            (models.high_demand_titles, 'c.borrow_type = %s'),
            (models.borrowings_by_user_type, 'c.borrow_type = %s'),
            (models.books_borrowed_per_program, 'c.borrow_type = %s'),
            (models.count_circulation_status, 'borrow_type = %s'),
        ]
        for fn, clause in cases:
            mock_db['fetch_all'].return_value = []
            fn(None, None, borrow_type='overnight')
            query, params = mock_db['fetch_all'].call_args[0]
            assert clause in query, fn.__name__
            assert 'overnight' in params, fn.__name__

    def test_borrow_type_absent_without_filter(self, mock_db):
        """Validates borrow type absent without filter [TestChartFilterModels / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import borrowings_trend
        mock_db['fetch_all'].return_value = []
        borrowings_trend()
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'borrow_type' not in query
        assert params is None


class TestForecastModels:
    def test_borrowings_by_weekday_monday_first(self, mock_db):
        """Validates borrowings by weekday monday first [TestForecastModels / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import borrowings_by_weekday
        mock_db['fetch_all'].return_value = [(0, 4), (6, 9)]
        rows = borrowings_by_weekday('2026-05-01', '2026-05-31')
        assert rows[0][0] == 'Monday'
        assert rows[-1] == ('Sunday', 4)
        assert rows[5] == ('Saturday', 9)
        assert len(rows) == 7
        assert mock_db['fetch_all'].call_args[0][1] == ('2026-05-01', '2026-05-31')

    def test_title_demand_gaps_shape(self, mock_db):
        """Validates title demand gaps shape [TestForecastModels / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import title_demand_gaps
        mock_db['fetch_all'].return_value = [('T', 'A', 5, 2)]
        assert title_demand_gaps() == [('T', 'A', 5, 2)]
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'reservation_queue' in query
        assert params == (8,)

    def test_count_accessions(self, mock_db):
        """Validates count accessions [TestForecastModels / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import count_accessions
        mock_db['fetch_one'].return_value = (15,)
        assert count_accessions('2026-05-01', '2026-05-31') == 15
        assert mock_db['fetch_one'].call_args[0][1] == ('2026-05-01', '2026-05-31')

    def test_trend_direction(self):
        """Validates trend direction [TestForecastModels / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.routes import _trend_direction
        assert _trend_direction([1, 1, 5, 5]) == 'up'
        assert _trend_direction([5, 5, 1, 1]) == 'down'
        assert _trend_direction([3, 3, 3, 3]) == 'flat'
        assert _trend_direction([1]) == 'flat'


class TestForecastJson:
    def _payload_calls(self, mock_db, trend, cats, overdue, accessions, weekday, gaps):
        """Test helper _payload_calls: build mocked data or DB stub for the test."""
        mock_db['fetch_all'].side_effect = [trend, cats, overdue, weekday, gaps]
        mock_db['fetch_one'].return_value = (accessions,)

    def test_requires_login(self, client, mock_db):
        """Validates requires login `/librarian/analytics/forecast` (expects 302) [TestForecastJson / analytics].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        assert client.get('/librarian/analytics/forecast').status_code == 302

    def test_student_forbidden(self, student_client, mock_db):
        """Validates student forbidden `/librarian/analytics/forecast` as student (expects 302) [TestForecastJson / analytics].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates dashboard/stats shown to staff are wrong."""
        assert student_client.get('/librarian/analytics/forecast').status_code == 302

    def test_projections_math(self, librarian_client, mock_db):
        """Validates projections math `/librarian/analytics/forecast?preset=all` as librarian (expects 200) [TestForecastJson / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from datetime import date
        trend = [(date(2026, 5, 1 + i), 2) for i in range(30)]
        self._payload_calls(
            mock_db, trend, [('Sci', 40), ('Arts', 20)],
            [(date(2026, 5, 1), 0)], 15,
            [(1, 5), (2, 5), (3, 5), (4, 5), (5, 5), (6, 12), (0, 2)],
            [('Hot Title', 'Some Author', 5, 2)],
        )
        resp = librarian_client.get('/librarian/analytics/forecast?preset=all')
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['daily_avg'] == 2.0
        assert body['next_30'] == 60
        assert body['by_category'][0] == ['Sci', 40, 40]
        assert body['overdue_direction'] == 'flat'
        assert body['busiest_weekday'] == 'Saturday'
        assert body['demand_gaps'] == [['Hot Title', 'Some Author', 5, 2, 3]]
        assert body['additions_next_30'] == 15
        warn = [i for i in body['insights'] if i['severity'] == 'warn']
        assert warn and 'procurement' in warn[0]['action_url']
        assert all(i['action_url'].startswith('/') for i in body['insights'])

    def test_empty_data_fallback(self, librarian_client, mock_db):
        """Validates empty data fallback `/librarian/analytics/forecast` as librarian (expects 200) [TestForecastJson / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_all'].return_value = []
        mock_db['fetch_one'].return_value = None
        resp = librarian_client.get('/librarian/analytics/forecast')
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['next_30'] == 0
        assert body['busiest_weekday'] == '-'
        assert body['demand_gaps'] == []
        assert len(body['insights']) == 1

    def test_overdue_rising_flagged(self, librarian_client, mock_db):
        """Validates overdue rising flagged `/librarian/analytics/forecast` as librarian [TestForecastJson / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from datetime import date
        trend = [(date(2026, 5, 1), 1)]
        overdue = [(date(2026, 5, 1 + i), v) for i, v in enumerate([0, 0, 4, 4])]
        self._payload_calls(mock_db, trend, [], overdue, 0, [], [])
        body = librarian_client.get('/librarian/analytics/forecast').get_json()
        assert body['overdue_direction'] == 'up'
        assert any('circulation' in i['action_url'] for i in body['insights'])

    def test_invalid_preset_still_json(self, librarian_client, mock_db):
        """Validates invalid preset still json `/librarian/analytics/forecast?preset=bogus&from=x` as librarian (expects 200) [TestForecastJson / analytics].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_all'].return_value = []
        mock_db['fetch_one'].return_value = None
        resp = librarian_client.get('/librarian/analytics/forecast?preset=bogus&from=x')
        assert resp.status_code == 200

    def test_projected_trend_weekday_shaped(self, librarian_client, mock_db):
        """Validates projected trend weekday shaped `/librarian/analytics/forecast` as librarian [TestForecastJson / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from datetime import date, timedelta
        trend = [(date(2026, 5, 1 + i), 10) for i in range(14)]
        weekday = [(1, 10), (2, 10), (3, 10), (4, 10), (5, 10), (6, 50), (0, 0)]
        self._payload_calls(mock_db, trend, [], [], 0, weekday, [])
        body = librarian_client.get('/librarian/analytics/forecast').get_json()
        proj = body['projected_trend']
        assert len(proj) == 30
        days = [date.fromisoformat(p[0]) for p in proj]
        assert days[0] == date.today() + timedelta(days=1)
        assert all((b - a).days == 1 for a, b in zip(days, days[1:]))
        by_dow = {}
        for iso, val in proj:
            by_dow.setdefault(date.fromisoformat(iso).weekday(), []).append(val)
        assert min(by_dow[5]) > max(by_dow[0])  # Saturdays beat Mondays
        assert body['trend_tail'][-1][0] == '2026-05-14'

    def test_projected_trend_flat_without_mix(self, librarian_client, mock_db):
        """Validates projected trend flat without mix `/librarian/analytics/forecast?preset=all` as librarian [TestForecastJson / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from datetime import date
        trend = [(date(2026, 5, 1), 4)]
        self._payload_calls(mock_db, trend, [], [], 0, [], [])
        body = librarian_client.get(
            '/librarian/analytics/forecast?preset=all').get_json()
        assert [p[1] for p in body['projected_trend']] == [4.0] * 30

    def test_basis_and_generated_at(self, librarian_client, mock_db):
        """Validates basis and generated at `/librarian/analytics/forecast?preset=custom&from=2026-05-01&to=2026-05-31` as librarian [TestForecastJson / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_all'].return_value = []
        mock_db['fetch_one'].return_value = None
        body = librarian_client.get(
            '/librarian/analytics/forecast?preset=custom&from=2026-05-01&to=2026-05-31'
        ).get_json()
        assert body['basis'] == 'May 01, 2026 – May 31, 2026'
        assert body['generated_at']


class TestForecastTab:
    def test_page_embeds_forecast_tab(self, librarian_client, mock_db):
        """Validates page embeds forecast tab `/librarian/analytics` as librarian (expects 200) [TestForecastTab / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong.

Insights tab was removed: all cards share the global time filter."""
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics')
        assert resp.status_code == 200
        assert b'data-rtab="forecast"' not in resp.data
        assert b'data-rtab-panel="forecast"' not in resp.data
        assert b'loadForecast' not in resp.data
        assert b'forecast-gaps-body' not in resp.data
        assert b'forecast-insights' not in resp.data
        assert b'Projected Borrowing Demand' not in resp.data
        assert b'>Insights</button>' not in resp.data
        assert b'Insights Dashboard' not in resp.data


class TestChartJson:
    def test_chart_requires_login(self, client, mock_db):
        """Validates chart requires login `/librarian/analytics/chart?name=top_books` (expects 302) [TestChartJson / analytics].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        assert client.get('/librarian/analytics/chart?name=top_books').status_code == 302

    def test_chart_student_forbidden(self, student_client, mock_db):
        """Validates chart student forbidden `/librarian/analytics/chart?name=top_books` as student (expects 302) [TestChartJson / analytics].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates dashboard/stats shown to staff are wrong."""
        assert student_client.get('/librarian/analytics/chart?name=top_books').status_code == 302

    def test_chart_rejects_unknown_name(self, librarian_client, mock_db):
        """Validates chart rejects unknown name `/librarian/analytics/chart?name=bogus` as librarian (expects 400) [TestChartJson / analytics].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        assert librarian_client.get('/librarian/analytics/chart?name=bogus').status_code == 400
        assert librarian_client.get('/librarian/analytics/chart').status_code == 400

    def test_chart_top_books(self, librarian_client, mock_db):
        """Validates chart top books `/librarian/analytics/chart?name=top_books` as librarian (expects 200) [TestChartJson / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_all'].return_value = [('Clean Code', 'Robert Martin', 9)]
        resp = librarian_client.get('/librarian/analytics/chart?name=top_books')
        assert resp.status_code == 200
        assert resp.get_json() == {'chart': 'top_books',
                                   'data': [['Clean Code', 'Robert Martin', 9]],
                                   'filters': {}}

    def test_chart_trend_dates_serialize_iso(self, librarian_client, mock_db):
        """Validates chart trend dates serialize iso `/librarian/analytics/chart?name=borrowings_trend` as librarian [TestChartJson / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from datetime import date
        mock_db['fetch_all'].return_value = [(date(2026, 5, 1), 3)]
        resp = librarian_client.get('/librarian/analytics/chart?name=borrowings_trend')
        assert resp.get_json()['data'] == [['2026-05-01', 3]]

    def test_chart_department_filter(self, librarian_client, mock_db):
        """Validates chart department filter `/librarian/analytics/chart?name=borrowings_by_department&department=BSIT&department=BSBA` as librarian (expects 200) [TestChartJson / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_all'].return_value = [('BSIT', 12)]
        resp = librarian_client.get(
            '/librarian/analytics/chart?name=borrowings_by_department&department=BSIT&department=BSBA')
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['filters'] == {'departments': ['BSIT', 'BSBA']}
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'b.department IN (%s, %s)' in query
        assert params[-2:] == ('BSIT', 'BSBA')

    def test_chart_role_and_category_filters(self, librarian_client, mock_db):
        """Validates chart role and category filters `/librarian/analytics/chart?name=borrowings_by_user_type&role=Student&role=&preset=all` as librarian [TestChartJson / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_all'].return_value = [('Student', 40)]
        resp = librarian_client.get(
            '/librarian/analytics/chart?name=borrowings_by_user_type&role=Student&role=&preset=all')
        assert resp.get_json()['filters'] == {'roles': ['Student']}
        mock_db['fetch_all'].return_value = [('Science', 2)]
        resp = librarian_client.get(
            '/librarian/analytics/chart?name=collection_by_category&category=Science&category= &preset=all')
        assert resp.get_json()['filters'] == {'categories': ['Science']}
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'LOWER(COALESCE(ct.name, b.subject_classification)) IN (%s)' in query
        assert params == ('science',)

    def test_chart_custom_dates(self, librarian_client, mock_db):
        """Validates chart custom dates `/librarian/analytics/chart?name=overdue_trend&preset=custom&from=2026-05-01&to=2026-05-31` as librarian (expects 200) [TestChartJson / analytics].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from datetime import date
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get(
            '/librarian/analytics/chart?name=overdue_trend&preset=custom&from=2026-05-01&to=2026-05-31')
        assert resp.status_code == 200
        assert mock_db['fetch_all'].call_args[0][1] == (date(2026, 5, 1), date(2026, 5, 31))

    def test_chart_invalid_dates_fall_back(self, librarian_client, mock_db):
        """Validates chart invalid dates fall back `/librarian/analytics/chart?name=top_categories&from=nope` as librarian (expects 200) [TestChartJson / analytics].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics/chart?name=top_categories&from=nope')
        assert resp.status_code == 200

    def test_chart_copies_by_status(self, librarian_client, mock_db):
        """Validates chart copies by status `/librarian/analytics/chart?name=copies_by_status` as librarian (expects 200) [TestChartJson / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].side_effect = [(50,), (2,), (0,)]
        mock_db['fetch_all'].side_effect = [[('active', 10)], [('available', 30)]]
        resp = librarian_client.get('/librarian/analytics/chart?name=copies_by_status')
        assert resp.status_code == 200
        data = dict(resp.get_json()['data'])
        assert data['Borrowed'] == 10
        assert data['Available'] == 50 - 10 - 0 - 2 - 0 - 0

    def test_chart_borrow_type_filter(self, librarian_client, mock_db):
        """Validates chart borrow type filter `/librarian/analytics/chart?name=borrowings_trend&borrow_type=overnight` as librarian (expects 200) [TestChartJson / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_all'].return_value = [(1, 2)]
        resp = librarian_client.get(
            '/librarian/analytics/chart?name=borrowings_trend&borrow_type=overnight')
        assert resp.status_code == 200
        assert resp.get_json()['filters'] == {'borrow_type': 'overnight'}
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'borrow_type = %s' in query
        assert params[-1] == 'overnight'

    def test_chart_borrow_type_combines_with_department(self, librarian_client, mock_db):
        """Validates chart borrow type combines with department `/librarian/analytics/chart?name=borrowings_by_department` as librarian (expects 200) [TestChartJson / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_all'].return_value = [('BSIT', 12)]
        resp = librarian_client.get(
            '/librarian/analytics/chart?name=borrowings_by_department'
            '&department=BSIT&borrow_type=daily_circulation')
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['filters'] == {'departments': ['BSIT'],
                                   'borrow_type': 'daily_circulation'}
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'b.department IN (%s)' in query
        assert 'c.borrow_type = %s' in query
        assert params[-2:] == ('BSIT', 'daily_circulation')

    def test_chart_invalid_borrow_type_ignored(self, librarian_client, mock_db):
        """Validates chart invalid borrow type ignored `/librarian/analytics/chart?name=top_books&borrow_type=weekly` as librarian (expects 200) [TestChartJson / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get(
            '/librarian/analytics/chart?name=top_books&borrow_type=weekly')
        assert resp.status_code == 200
        assert resp.get_json()['filters'] == {}
        assert 'borrow_type' not in mock_db['fetch_all'].call_args[0][0]


class TestChartFilterControls:
    def test_page_embeds_filter_modal(self, librarian_client, mock_db):
        """Validates page embeds filter modal `/librarian/analytics` as librarian (expects 200) [TestChartFilterControls / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong.

Per-card filters were removed: all cards share the global filter."""
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics')
        assert resp.status_code == 200
        assert b'id="chartFilterModal"' not in resp.data
        assert b'id="chartFilterBody"' not in resp.data
        assert b'id="chartFilterApply"' not in resp.data
        assert b'id="chartFilterReset"' not in resp.data
        assert b'CHART_FILTER_DEFS' not in resp.data
        assert b'FILTER_BUTTON_CARDS' not in resp.data
        assert b'openChartFilter' not in resp.data
        assert b'data-cbadge' not in resp.data
        # global time filter remains the single source of truth
        assert b'id="globalFilterModal"' in resp.data
        assert b'applyGlobalFilter' in resp.data

    def test_collection_table_controls_work(self, librarian_client, mock_db):
        """Validates collection table controls work `/librarian/analytics` as librarian (expects 200) [TestChartFilterControls / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong.

Search + status filter are real inputs; View All links go somewhere."""
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics')
        assert resp.status_code == 200
        assert b'id="collection-search"' in resp.data
        assert b'id="collection-status-filter"' in resp.data
        assert b'filterCollectionTable' in resp.data
        # dead spans are gone: no placeholder-only controls remain
        assert b'Search by title, author, or ID\xe2\x80\xa6</span>' not in resp.data
        assert b'rounded-lg px-3 py-1.5">Filters</span>' not in resp.data
        assert b'rounded-lg px-3 py-1.5">View All</span>' not in resp.data
        # View All destinations resolve to real pages
        assert b'/librarian/cataloging' in resp.data
        assert b'/librarian/circulation' in resp.data



class TestReviewFeedbackRegression:
    def test_copies_available_includes_reserved_and_lost_flagged(self, mock_db):
        """Validates copies available includes reserved and lost flagged [TestReviewFeedbackRegression / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong.

KPI card and Copies-by-Status chart must use one Available formula."""
        from app.analytics.models import copies_by_status_summary
        mock_db['fetch_one'].side_effect = [(100,), (5,), (4,)]
        mock_db['fetch_all'].side_effect = [
            [('active', 20), ('overdue', 3)],
            [('available', 60), ('borrowed', 20), ('lost', 1), ('damaged', 2)],
        ]
        rows = dict(copies_by_status_summary())
        # total - borrowed - overdue - reserved - (lost+damaged+missing+flagged)
        assert rows['Available'] == 100 - 20 - 3 - 5 - (1 + 2 + 4) - 0
        assert rows['Lost / Damaged'] == 1 + 2 + 4

    def test_dashboard_initial_paint_trend_labels_are_iso(self, mock_db):
        """Validates dashboard initial paint trend labels are iso [TestReviewFeedbackRegression / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong.

Initial page-load trend labels must be ISO dates, not RFC-2822."""
        from datetime import date
        from app.analytics import routes
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        real_trend = routes.models.borrowings_trend
        try:
            routes.models.borrowings_trend = lambda *a, **k: [(date(2026, 8, 15), 7)]
            dashboard = routes.compute_dashboard(None, None)
        finally:
            routes.models.borrowings_trend = real_trend
        assert dashboard['usage']['trend'][0][0] == '2026-08-15'

    def test_autosuggest_loads_category_record(self):
        """Validates autosuggest loads category record [TestReviewFeedbackRegression / analytics].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates dashboard/stats shown to staff are wrong.

Category bloom warning is dead unless the loader decodes it."""
        import pathlib
        js = pathlib.Path('app/static/js/autosuggest.js').read_text(encoding='utf-8')
        assert 'data.category_record' in js


class TestUsageDepartmentFilter:
    def test_trend_department_filter(self, mock_db):
        """Validates trend department filter [TestUsageDepartmentFilter / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import borrowings_trend
        mock_db['fetch_all'].return_value = []
        borrowings_trend(None, None, None, ['BSIT'])
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'JOIN borrowers' in query
        assert params == ('BSIT',)

    def test_trend_no_department_unchanged(self, mock_db):
        """Validates trend no department unchanged [TestUsageDepartmentFilter / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import borrowings_trend
        mock_db['fetch_all'].return_value = []
        borrowings_trend()
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'JOIN borrowers' not in query
        assert params is None

    def test_overview_department_scopes(self, mock_db):
        """Validates overview department scopes [TestUsageDepartmentFilter / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import circulation_overview
        mock_db['fetch_one'].side_effect = [
            (10,), (4,), (2,), (3.0,), (6,), (7,)]
        circulation_overview(None, None, ['BSIT'])
        query, params = mock_db['fetch_one'].call_args_list[0][0]
        assert 'JOIN borrowers' in query
        assert params == ('BSIT',)

    def test_top_books_department(self, mock_db):
        """Validates top books department [TestUsageDepartmentFilter / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import top_borrowed_books_detailed
        mock_db['fetch_all'].return_value = []
        top_borrowed_books_detailed(None, None, 5, None, ['BSIT'])
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'JOIN borrowers' in query
        assert 'BSIT' in params

    def test_no_program_pseudo_label(self, mock_db):
        """Validates no program pseudo label [TestUsageDepartmentFilter / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import books_borrowed_per_program
        mock_db['fetch_all'].return_value = []
        books_borrowed_per_program(None, None, ['No program'])
        query = mock_db['fetch_all'].call_args[0][0]
        assert 'NOT IN' in query
        assert 'b.department IN' not in query

    def test_dashboard_json_scopes_usage_only(self, librarian_client, mock_db):
        """Validates dashboard json scopes usage only `/librarian/analytics/dashboard?department=BSIT` as librarian (expects 200) [TestUsageDepartmentFilter / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics/dashboard?department=BSIT')
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['usage']['department'] == 'BSIT'
        assert body['usage']['departments'] == ['BSIT']
        assert body['usage']['by_department_all'] == []
        # collection tab ignores the program filter
        assert body['collection']['total_titles'] == 0

    def test_dashboard_json_multi_departments(self, librarian_client, mock_db):
        """Validates dashboard json multi departments `/librarian/analytics/dashboard?department=BSIT&department=BSBA` as librarian (expects 200) [TestUsageDepartmentFilter / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get(
            '/librarian/analytics/dashboard?department=BSIT&department=BSBA')
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['usage']['departments'] == ['BSIT', 'BSBA']
        assert body['usage']['department'] == 'BSIT, BSBA'

    def test_page_renders_program_select(self, librarian_client, mock_db):
        """Validates page renders program select `/librarian/analytics` as librarian (expects 200) [TestUsageDepartmentFilter / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].return_value = [('BSIT', 12)]
        resp = librarian_client.get('/librarian/analytics')
        assert resp.status_code == 200
        assert b'id="usage-dept-dropdown"' in resp.data
        assert b'id="usage-dept-options"' in resp.data
        assert b'onUsageDeptApply' in resp.data
        assert b'by_department_all' in resp.data
        assert b'BSIT' in resp.data

    def test_page_preselects_department(self, librarian_client, mock_db):
        """Validates page preselects department `/librarian/analytics?department=BSIT&department=BSBA` as librarian (expects 200) [TestUsageDepartmentFilter / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].return_value = [('BSIT', 12), ('BSBA', 7)]
        resp = librarian_client.get(
            '/librarian/analytics?department=BSIT&department=BSBA')
        assert resp.status_code == 200
        assert b'value="BSIT" checked' in resp.data
        assert b'value="BSBA" checked' in resp.data

    def test_overview_sql_has_valid_spacing(self, mock_db):
        """Validates overview sql has valid spacing [TestUsageDepartmentFilter / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong.

Regression: every overview query must keep whitespace after the
        FROM table (a missing space is a syntax error on real Postgres,
        swallowed by _safe -> all KPIs render 0)."""
        import re
        from app.analytics.models import circulation_overview
        mock_db['fetch_one'].side_effect = [
            (10,), (4,), (2,), (3.0,), (6,), (7,)]
        assert circulation_overview(None, None) == (10, 4, 2, 3.0, 60.0, 7)
        queries = [c[0][0] for c in mock_db['fetch_one'].call_args_list
                   if 'circulation_records' in c[0][0]]
        assert len(queries) == 5
        for q in queries:
            assert 'recordsWHERE' not in q
            assert re.search(r'circulation_records(\s|$)', q), q

    def test_overview_department_sql_unambiguous(self, mock_db):
        """Validates overview department sql unambiguous [TestUsageDepartmentFilter / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong.

Regression: dept-scoped overview joins borrowers, so borrower_id
        must be table-qualified (ambiguous column -> exception -> KPIs 0)."""
        import re
        from app.analytics.models import circulation_overview
        mock_db['fetch_one'].side_effect = [
            (10,), (4,), (2,), (3.0,), (6,), (7,)]
        circulation_overview(None, None, ['BSIT'])
        queries = [c[0][0] for c in mock_db['fetch_one'].call_args_list]
        assert any('JOIN borrowers' in q for q in queries)
        for q in queries:
            if 'JOIN borrowers' in q:
                assert re.search(r'(?<!\.)\bborrower_id\b', q) is None, q

    def test_overview_multi_departments_or_clause(self, mock_db):
        """Validates overview multi departments or clause [TestUsageDepartmentFilter / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import circulation_overview
        mock_db['fetch_one'].side_effect = [
            (10,), (4,), (2,), (3.0,), (6,), (7,)]
        circulation_overview(None, None, ['BSIT', 'BSBA'])
        query, params = mock_db['fetch_one'].call_args_list[0][0]
        assert 'OR' in query
        assert params == ('BSIT', 'BSBA')

    def test_export_honors_department(self, librarian_client, mock_db):
        """Validates export honors department `/librarian/analytics/export` as librarian (expects 200) [TestUsageDepartmentFilter / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_all'].return_value = [('BSIT', 12)]
        resp = librarian_client.post(
            '/librarian/analytics/export',
            data={'kpi_type': 'books_borrowed_per_program', 'format': 'pdf',
                  'department': 'BSIT'})
        assert resp.status_code == 200
        assert resp.data[:4] == b'%PDF'
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'BSIT' in params

    def test_export_honors_multi_departments(self, librarian_client, mock_db):
        """Validates export honors multi departments `/librarian/analytics/export` as librarian (expects 200) [TestUsageDepartmentFilter / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_all'].return_value = [('BSIT', 12), ('BSBA', 7)]
        resp = librarian_client.post(
            '/librarian/analytics/export',
            data={'kpi_type': 'books_borrowed_per_program', 'format': 'pdf',
                  'department': ['BSIT', 'BSBA']})
        assert resp.status_code == 200
        assert resp.data[:4] == b'%PDF'
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'BSIT' in params and 'BSBA' in params


class TestBookAnalyticsTab:
    def test_tab_present_without_sidebar_page(self, librarian_client, mock_db):
        """Validates tab present without sidebar page `/librarian/analytics` as librarian (expects 200) [TestBookAnalyticsTab / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong.

Book Analytics lives inside Reports & Analytics: a tab button and
        panel, with no standalone book page or sidebar entry."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics')
        assert resp.status_code == 200
        assert b'data-rtab="book"' in resp.data
        assert b'data-rtab-panel="book"' in resp.data
        assert b'book_analytics_page' not in resp.data
        assert librarian_client.get('/librarian/analytics/book').status_code == 404

    def test_empty_until_book_picked(self, librarian_client, mock_db):
        """Validates empty until book picked `/librarian/analytics?tab=book` as librarian (expects 200) [TestBookAnalyticsTab / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong.

No book_id -> empty state, and no per-book queries run."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics?tab=book')
        assert resp.status_code == 200
        assert b'id="book-empty"' in resp.data
        assert b'id="book-status-lines"' not in resp.data
        for c in mock_db['fetch_all'].call_args_list:
            assert 'OR b.author ILIKE' not in c[0][0]
            assert 'c.book_id = %s' not in c[0][0]

    def test_blank_search_runs_no_book_query(self, librarian_client, mock_db):
        """Validates blank search runs no book query `/librarian/analytics?q=++&tab=book` as librarian (expects 200) [TestBookAnalyticsTab / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics?q=++&tab=book')
        assert resp.status_code == 200
        assert b'id="book-empty"' in resp.data
        for c in mock_db['fetch_all'].call_args_list:
            assert 'OR b.author ILIKE' not in c[0][0]

    def test_search_lists_books(self, librarian_client, mock_db):
        """Validates search lists books `/librarian/analytics?q=clean&tab=book` as librarian (expects 200) [TestBookAnalyticsTab / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = [(1, 'Clean Code', 'Robert Martin', 'Science', 2008)]
        resp = librarian_client.get('/librarian/analytics?q=clean&tab=book')
        assert resp.status_code == 200
        assert b'Clean Code' in resp.data
        assert b'Show Analytics' in resp.data
        assert b'Copyright Date' in resp.data
        assert b'2008' in resp.data
        assert b'id="book-empty"' not in resp.data
        # results grid + live suggestions are scrollable
        assert b'max-h-[420px] overflow-y-auto' in resp.data
        assert b'max-h-72 overflow-y-auto' in resp.data

    def test_selected_book_shows_graphs_only(self, librarian_client, mock_db):
        """Validates selected book shows graphs only `/librarian/analytics?q=clean&book_id=1&tab=book` as librarian (expects 200) [TestBookAnalyticsTab / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong.

Selected book renders graphs (status lines + bars), no KPI cards."""
        mock_db['fetch_one'].return_value = (1, 'Clean Code', 'Robert Martin', 'Science', 3)
        mock_db['fetch_all'].return_value = [(1, 'Clean Code', 'Robert Martin', 'Science')]
        resp = librarian_client.get('/librarian/analytics?q=clean&book_id=1&tab=book')
        assert resp.status_code == 200
        assert b'id="book-status-lines"' in resp.data
        assert b'renderBookStatusLines' in resp.data
        assert b'Clean Code' in resp.data
        # KPI cards are gone: graphs only (Return Rate still exists on the
        # dashboard tabs, so assert on the removed book KPI grid instead)
        assert b'id="book-traffic"' not in resp.data
        assert b'Total Borrows' not in resp.data
        assert b'Unique Borrowers' not in resp.data

    def test_unknown_book_flashes_error(self, librarian_client, mock_db):
        """Validates unknown book flashes error `/librarian/analytics?book_id=999&tab=book` as librarian (expects 200) [TestBookAnalyticsTab / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics?book_id=999&tab=book')
        assert resp.status_code == 200
        assert b'Book not found' in resp.data

    def test_tab_deep_link_script(self, librarian_client, mock_db):
        """Validates tab deep link script `/librarian/analytics` as librarian (expects 200) [TestBookAnalyticsTab / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong.

?tab=<name> reopens that tab after filter/export round-trips."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics')
        assert resp.status_code == 200
        assert b'book-traffic-data' in resp.data
        assert b'renderBookTraffic' in resp.data
        assert b"deepTab === 'usage'" in resp.data
        assert b"activateRtab(deepTab)" in resp.data


class TestBookAnalyticsJson:
    def test_search_requires_login(self, client, mock_db):
        """Validates search requires login `/librarian/analytics/book/search?q=x` (expects 302) [TestBookAnalyticsJson / analytics].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        assert client.get('/librarian/analytics/book/search?q=x').status_code == 302

    def test_search_returns_results(self, librarian_client, mock_db):
        """Validates search returns results `/librarian/analytics/book/search?q=clean` as librarian [TestBookAnalyticsJson / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_all'].return_value = [(1, 'Clean Code', 'Robert Martin', 'Science')]
        body = librarian_client.get('/librarian/analytics/book/search?q=clean').get_json()
        assert body == {'results': [
            {'book_id': 1, 'title': 'Clean Code',
             'author': 'Robert Martin', 'category': 'Science'}]}

    def test_search_blank_returns_empty(self, librarian_client, mock_db):
        """Validates search blank returns empty `/librarian/analytics/book/search?q=` as librarian [TestBookAnalyticsJson / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        body = librarian_client.get('/librarian/analytics/book/search?q=').get_json()
        assert body == {'results': []}
        assert mock_db['fetch_all'].call_count == 0

    def test_data_requires_login(self, client, mock_db):
        """Validates data requires login `/librarian/analytics/book/data?book_id=1` (expects 302) [TestBookAnalyticsJson / analytics].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        assert client.get('/librarian/analytics/book/data?book_id=1').status_code == 302

    def test_data_rejects_bad_id(self, librarian_client, mock_db):
        """Validates data rejects bad id `/librarian/analytics/book/data` as librarian (expects 400) [TestBookAnalyticsJson / analytics].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        assert librarian_client.get('/librarian/analytics/book/data').status_code == 400
        assert librarian_client.get(
            '/librarian/analytics/book/data?book_id=abc').status_code == 400

    def test_data_404_for_missing_book(self, librarian_client, mock_db):
        """Validates data 404 for missing book `/librarian/analytics/book/data?book_id=999` as librarian (expects 404) [TestBookAnalyticsJson / analytics].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = None
        resp = librarian_client.get('/librarian/analytics/book/data?book_id=999')
        assert resp.status_code == 404

    def test_data_returns_traffic(self, librarian_client, mock_db):
        """Validates data returns traffic `/librarian/analytics/book/data?book_id=1` as librarian (expects 200) [TestBookAnalyticsJson / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].side_effect = [
            (1, 'Clean Code', 'Robert Martin', 'Science', 3),
            (10,), (4,), (2,), (6,), (5,), (4.0,),
            (2,),
        ]
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics/book/data?book_id=1')
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['book']['title'] == 'Clean Code'
        assert body['overview']['total'] == 10
        assert body['overview']['waiting'] == 2

    def test_data_status_trends_aligned(self, librarian_client, mock_db):
        """Validates data status trends aligned `/librarian/analytics/book/data?book_id=1&preset=all` as librarian [TestBookAnalyticsJson / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong.

Per-status rows pivot into zero-filled series over shared dates."""
        from datetime import date
        mock_db['fetch_one'].side_effect = [
            (1, 'Clean Code', 'Robert Martin', 'Science', 3),
            (10,), (4,), (2,), (6,), (5,), (4.0,),
            (0,),
        ]
        mock_db['fetch_all'].side_effect = [
            [],  # trend
            [],  # by program
            [],  # by user type
            [],  # copies
            [],  # recent
            [  # status rows
                (date(2026, 5, 1), 'borrowed', 3),
                (date(2026, 5, 2), 'borrowed', 1),
                (date(2026, 5, 1), 'claimed', 2),
                (date(2026, 5, 1), 'bogus', 9),
            ],
        ]
        body = librarian_client.get(
            '/librarian/analytics/book/data?book_id=1&preset=all').get_json()
        trends = body['status_trends']
        assert trends['dates'] == ['2026-05-01', '2026-05-02']
        by_key = {s['key']: s for s in trends['series']}
        assert sorted(by_key) == ['allocated', 'borrowed', 'claimed', 'expired',
                                  'overdue', 'returned', 'waiting']
        assert by_key['borrowed']['values'] == [3, 1]
        assert by_key['claimed']['values'] == [2, 0]
        assert by_key['waiting']['values'] == [0, 0]
        assert all('label' in s and 'color' in s for s in trends['series'])

    def test_data_bounded_range_fills_empty_days(self, librarian_client, mock_db):
        """Validates data bounded range fills empty days `/librarian/analytics/book/data?book_id=1&preset=custom` as librarian [TestBookAnalyticsJson / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong.

Custom range: lone spikes render on the full daily axis, zero-filled."""
        from datetime import date
        mock_db['fetch_one'].side_effect = [
            (1, 'Clean Code', 'Robert Martin', 'Science', 3),
            (10,), (4,), (2,), (6,), (5,), (4.0,),
            (0,),
        ]
        mock_db['fetch_all'].side_effect = [
            [],  # trend
            [],  # by program
            [],  # by user type
            [],  # copies
            [],  # recent
            [(date(2026, 5, 2), 'borrowed', 3)],  # status rows
        ]
        body = librarian_client.get(
            '/librarian/analytics/book/data?book_id=1&preset=custom'
            '&from=2026-05-01&to=2026-05-03').get_json()
        trends = body['status_trends']
        assert trends['dates'] == ['2026-05-01', '2026-05-02', '2026-05-03']
        by_key = {s['key']: s for s in trends['series']}
        assert by_key['borrowed']['values'] == [0, 3, 0]

    def test_data_huge_range_falls_back_to_observed(self, librarian_client, mock_db):
        """Validates data huge range falls back to observed `/librarian/analytics/book/data?book_id=1&preset=custom` as librarian [TestBookAnalyticsJson / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong.

Absurd ranges skip the fill and keep observed dates only."""
        from datetime import date
        mock_db['fetch_one'].side_effect = [
            (1, 'Clean Code', 'Robert Martin', 'Science', 3),
            (10,), (4,), (2,), (6,), (5,), (4.0,),
            (0,),
        ]
        mock_db['fetch_all'].side_effect = [
            [], [], [], [], [],
            [(date(2026, 5, 2), 'borrowed', 3)],
        ]
        body = librarian_client.get(
            '/librarian/analytics/book/data?book_id=1&preset=custom'
            '&from=2020-01-01&to=2026-12-31').get_json()
        assert body['status_trends']['dates'] == ['2026-05-02']

    def test_sparse_hint_in_template(self, librarian_client, mock_db):
        """Validates sparse hint in template `/librarian/analytics` as librarian (expects 200) [TestBookAnalyticsJson / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics')
        assert resp.status_code == 200
        assert b'Only one day with activity' in resp.data


class TestBookAnalyticsModels:
    def test_search_blank_runs_no_query(self, mock_db):
        """Validates search blank runs no query [TestBookAnalyticsModels / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import search_books_for_analytics
        assert search_books_for_analytics('   ') == []
        assert mock_db['fetch_all'].call_count == 0

    def test_search_filters_active_titles(self, mock_db):
        """Validates search filters active titles [TestBookAnalyticsModels / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import search_books_for_analytics
        mock_db['fetch_all'].return_value = []
        search_books_for_analytics('code')
        query, params = mock_db['fetch_all'].call_args[0]
        assert "catalog_status = 'active'" in query
        assert params == ('%code%', '%code%', '%code%', '%code%', '%code%', 10)
        assert 'b.subject_classification ILIKE' in query
        assert 'a.accession_number ILIKE' in query
        assert 'b.year_published' in query

    def test_overview_bad_id_returns_zeros(self, mock_db):
        """Validates overview bad id returns zeros [TestBookAnalyticsModels / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import book_traffic_overview
        assert book_traffic_overview('nope') == (0, 0, 0, 0, 0, 0.0, 0.0)
        assert mock_db['fetch_one'].call_count == 0

    def test_overview_returns_tuple(self, mock_db):
        """Validates overview returns tuple [TestBookAnalyticsModels / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import book_traffic_overview
        mock_db['fetch_one'].side_effect = [
            (10,), (4,), (2,), (6,), (5,), (4.0,)]
        assert book_traffic_overview(1) == (10, 4, 2, 6, 5, 4.0, 60.0)

    def test_book_trend_scoped_to_book(self, mock_db):
        """Validates book trend scoped to book [TestBookAnalyticsModels / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from datetime import date
        from app.analytics.models import book_borrowings_trend
        mock_db['fetch_all'].return_value = [(date(2026, 5, 1), 3)]
        assert book_borrowings_trend(1) == [(date(2026, 5, 1), 3)]
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'c.book_id = %s' in query
        assert params[0] == 1

    def test_recent_circulation_shows_accession_number(self, mock_db):
        """Validates recent circulation shows accession number [TestBookAnalyticsModels / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong.

Recent circulation exposes Accession No., not the TXN id."""
        from app.analytics.models import recent_circulation
        mock_db['fetch_all'].return_value = []
        recent_circulation()
        query = mock_db['fetch_all'].call_args[0][0]
        assert 'a.accession_number' in query
        assert 'JOIN accession_log a ON a.accession_id = c.accession_id' in query
        assert 'c.circulation_id' not in query

    def test_book_status_trends_unions_circulation_and_reservations(self, mock_db):
        """Validates book status trends unions circulation and reservations [TestBookAnalyticsModels / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from datetime import date
        from app.analytics.models import book_status_trends
        mock_db['fetch_all'].return_value = [(date(2026, 5, 1), 'borrowed', 3)]
        assert book_status_trends(1) == [(date(2026, 5, 1), 'borrowed', 3)]
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'UNION ALL' in query
        assert "transaction_type = 'borrow'" in query
        assert "transaction_status = 'returned'" in query
        assert 'c.return_date' in query
        assert "transaction_status = 'overdue'" in query
        assert 'reservation_queue' in query
        assert 'reservation_status' in query
        # book_id scopes all four legs (3 circulation + 1 reservation)
        assert params[:4] == (1, 1, 1, 1)
        assert 'ORDER BY day' in query

    def test_book_status_trends_bad_id_runs_no_query(self, mock_db):
        """Validates book status trends bad id runs no query [TestBookAnalyticsModels / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import book_status_trends
        assert book_status_trends('nope') == []
        assert mock_db['fetch_all'].call_count == 0


class TestAnalyticsTabRefresh:
    def test_circulation_tracking_rename(self, librarian_client, mock_db):
        """Validates circulation tracking rename `/librarian/analytics` as librarian (expects 200) [TestAnalyticsTabRefresh / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics')
        assert resp.status_code == 200
        assert b'Circulation Tracking' in resp.data
        assert b'Collection Tracking' not in resp.data

    def test_hbars_show_top_10(self, librarian_client, mock_db):
        """Validates hbars show top 10 `/librarian/analytics` as librarian (expects 200) [TestAnalyticsTabRefresh / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics')
        assert resp.status_code == 200
        assert b'slice(0, 10)' in resp.data

    def test_expand_modal_present_on_all_tabs(self, librarian_client, mock_db):
        """Validates expand modal present on all tabs `/librarian/analytics` as librarian (expects 200) [TestAnalyticsTabRefresh / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong.

Every non-pie graph card gets an expand (open_in_full) button
        popping the whole card + data into a modal."""
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics')
        assert resp.status_code == 200
        assert b'id="chartExpandModal"' in resp.data
        assert b'id="chartExpandBody"' in resp.data
        assert b'expandAnalyticsCard' in resp.data
        assert b'closeChartExpand' in resp.data
        assert b'initChartExpand' in resp.data
        assert b'open_in_full' in resp.data
        # expandable list covers bar/line/table cards on every tab ...
        assert b"var ids = ['condition-bars'," in resp.data
        assert b"'book-top-under-body'" in resp.data
        # ... but no donut (pie) container is in that expandable list
        ids_start = resp.data.index(b'var ids = [')
        ids_end = resp.data.index(b'];', ids_start)
        assert b'donut' not in resp.data[ids_start:ids_end]
        # recent collection status table is intentionally not expandable
        assert b"'recent-collection-body'" not in resp.data[ids_start:ids_end]
        # expanded modal drops the cloned card title (header already shows it)
        # and scales charts/tables up
        assert b"clone.querySelector('h3')" in resp.data
        assert b'#chartExpandBody svg.w-full' in resp.data

    def test_expand_modal_shows_full_data_scrollable(self, librarian_client, mock_db):
        """Validates expand modal shows full data scrollable `/librarian/analytics` as librarian (expects 200) [TestAnalyticsTabRefresh / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong.

Expanded modal re-renders full datasets with scrollable bars/tables."""
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics')
        assert resp.status_code == 200
        assert b'function renderExpandFull' in resp.data
        assert b'EXPAND_FULL_CAP' in resp.data
        assert b'expand-scroll' in resp.data
        assert b'recentCollectionHTML' in resp.data
        assert b'recentCircHTML' in resp.data
        assert b'renderConditionBarsInto' in resp.data

    def test_status_trends_filter_present(self, librarian_client, mock_db):
        """Validates status trends filter present `/librarian/analytics?q=clean&book_id=1&tab=book` as librarian (expects 200) [TestAnalyticsTabRefresh / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched; model SQL changed (SELECT).
    Failure indicates dashboard/stats shown to staff are wrong.

Status Trends card offers a filter button opening a checkbox modal."""
        mock_db['fetch_one'].return_value = (1, 'Clean Code', 'Robert Martin', 'Science', 3)
        mock_db['fetch_all'].return_value = [(1, 'Clean Code', 'Robert Martin', 'Science')]
        resp = librarian_client.get('/librarian/analytics?q=clean&book_id=1&tab=book')
        assert resp.status_code == 200
        assert b'id="book-status-filter-btn"' in resp.data
        assert b'id="statusFilterModal"' in resp.data
        assert b'id="status-filter-list"' in resp.data
        assert b'function openStatusFilterModal' in resp.data
        assert b'function toggleBookStatus' in resp.data
        assert b'function drawStatusLines' in resp.data
        assert b'BOOK_STATUS_SELECTION' in resp.data
        assert b'type="checkbox"' in resp.data


class TestRequestAnalytics:
    def test_top_requested_titles(self, mock_db):
        """Validates top requested titles [TestRequestAnalytics / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import top_requested_titles
        mock_db['fetch_all'].return_value = [('Data Science', 5)]
        assert top_requested_titles() == [('Data Science', 5)]
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'FROM request_records' in query
        assert params[-1] == 10

    def test_top_requested_titles_scoped_by_date(self, mock_db):
        """Validates top requested titles scoped by date [TestRequestAnalytics / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import top_requested_titles
        top_requested_titles('2026-01-01', '2026-12-31')
        params = mock_db['fetch_all'].call_args[0][1]
        assert params == ('2026-01-01', '2026-12-31', 10)

    def test_requests_by_role_split(self, mock_db):
        """Validates requests by role split [TestRequestAnalytics / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import requests_by_role_split
        mock_db['fetch_all'].return_value = [('Data Science', 3, 2, 0, 5)]
        assert requests_by_role_split() == [('Data Science', 3, 2, 0, 5)]
        query = mock_db['fetch_all'].call_args[0][0]
        assert 'JOIN roles r' in query
        assert "FILTER (WHERE r.role_name = 'Student')" in query

    def test_requests_trend(self, mock_db):
        """Validates requests trend [TestRequestAnalytics / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import requests_trend
        from datetime import date
        mock_db['fetch_all'].return_value = [(date(2026, 1, 5), 2)]
        assert requests_trend() == [(date(2026, 1, 5), 2)]
        query = mock_db['fetch_all'].call_args[0][0]
        assert 'request_date::date' in query

    def test_requests_by_program(self, mock_db):
        """Validates requests by program [TestRequestAnalytics / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import requests_by_program
        mock_db['fetch_all'].return_value = [('BSIS', 4)]
        assert requests_by_program() == [('BSIS', 4)]
        query = mock_db['fetch_all'].call_args[0][0]
        assert 'program_label' in query

    def test_requests_by_program_scoped_by_department(self, mock_db):
        """Validates requests by program scoped by department [TestRequestAnalytics / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import requests_by_program
        requests_by_program(departments=['BSIS'])
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'BSIS' in params

    def test_requests_by_status(self, mock_db):
        """Validates requests by status [TestRequestAnalytics / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import requests_by_status
        mock_db['fetch_all'].return_value = [('pending_review', 3), ('approved', 1)]
        assert requests_by_status() == [('pending_review', 3), ('approved', 1)]

    def test_dashboard_json_includes_requests(self, librarian_client, mock_db):
        """Validates dashboard json includes requests `/librarian/analytics/dashboard` as librarian (expects 200) [TestRequestAnalytics / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics/dashboard')
        assert resp.status_code == 200
        body = resp.get_json()
        assert 'requests' in body
        for key in ('total', 'pending', 'approved', 'rejected', 'procured',
                    'top_titles', 'by_role', 'trend', 'by_program'):
            assert key in body['requests']

    def test_kpi_json_new_types(self, librarian_client, mock_db):
        # kpi_json is intentionally limited to board-era VALID_KPIS, so the
        # new request sections 400 there; they are served via chart_json,
        # dashboard_json, and export instead.
        """Validates kpi json new types as librarian (expects 400) [TestRequestAnalytics / analytics].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_all'].return_value = []
        for kpi in ('top_requested_titles', 'requests_by_role',
                    'requests_trend', 'requests_by_program'):
            resp = librarian_client.get(f'/librarian/analytics/kpi?kpi_type={kpi}')
            assert resp.status_code == 400

    def test_chart_json_new_names(self, librarian_client, mock_db):
        """Validates chart json new names as librarian (expects 200) [TestRequestAnalytics / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_all'].return_value = []
        for name in ('top_requested_titles', 'requests_by_role',
                     'requests_trend', 'requests_by_program'):
            resp = librarian_client.get(f'/librarian/analytics/chart?name={name}')
            assert resp.status_code == 200
            assert resp.get_json()['chart'] == name

    def test_export_new_kpi_returns_pdf(self, librarian_client, mock_db):
        """Validates export new kpi returns pdf `/librarian/analytics/export` as librarian (expects 200) [TestRequestAnalytics / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_all'].return_value = [('Data Science', 3, 2, 0, 5)]
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'requests_by_role', 'format': 'pdf'})
        assert resp.status_code == 200
        assert resp.content_type == 'application/pdf'
        assert resp.data[:4] == b'%PDF'

    def test_page_has_requests_tab(self, librarian_client, mock_db):
        """Validates page has requests tab `/librarian/analytics` as librarian (expects 200) [TestRequestAnalytics / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics')
        assert resp.status_code == 200
        # Request charts live inside the Library Analytics tab (no separate tab,
        # no "Book Requests" header card — headline counts live on the requests page).
        assert b'data-rtab="requests"' not in resp.data
        assert b'>Book Requests</h2>' not in resp.data
        assert b'data-rtab-panel="library"' in resp.data
        assert b'id="req-top-titles"' in resp.data
        assert b'id="req-role-split"' in resp.data
        assert b'id="req-trend-line"' in resp.data
        assert b'id="req-by-program"' in resp.data
        assert b'function paintRequests' in resp.data

    def test_requests_cards_link_to_filtered_requests(self, librarian_client, mock_db):
        """Validates requests cards link to filtered requests `/librarian/analytics` as librarian (expects 200) [TestRequestAnalytics / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong.

Top requested-title bars navigate to the requests page pre-searched."""
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics')
        assert resp.status_code == 200
        # No KPI card row in analytics — headline counts live on the requests page.
        assert b'id="requests-kpis"' not in resp.data
        # url_for('requests.list_requests') resolves server-side into the JS const.
        assert b'/librarian/requests' in resp.data
        assert b'function reqTitleSearchLink' in resp.data
        # hbars accepts optional link wiring (other callers unaffected).
        assert b'limit, linkFn' in resp.data


class TestBookHeaderDetails:
    FULL_ROW = (1, 'Clean Code', 'Robert C. Martin', 'Software Engineering',
                2008, 3, 'Prentice Hall', '1st', '978-0132350884',
                'QA76.76.R63', 'Book', 'Agile craftsmanship handbook.')

    def test_traffic_payload_carries_full_details(self, mock_db):
        """Validates traffic payload carries full details [TestBookHeaderDetails / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.routes import compute_book_traffic
        mock_db['fetch_one'].return_value = self.FULL_ROW
        mock_db['fetch_all'].return_value = []
        traffic = compute_book_traffic(1, None, None)
        assert traffic is not None
        book = traffic['book']
        assert book['publisher'] == 'Prentice Hall'
        assert book['edition'] == '1st'
        assert book['isbn'] == '978-0132350884'
        assert book['call_number'] == 'QA76.76.R63'
        assert book['material_type'] == 'Book'
        assert book['description'] == 'Agile craftsmanship handbook.'
        assert book['copies'] == 3

    def test_short_legacy_rows_still_work(self, mock_db):
        """Validates short legacy rows still work [TestBookHeaderDetails / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.routes import compute_book_traffic
        mock_db['fetch_one'].return_value = (1, 'Clean Code', 'R. Martin', 'SE', 2008, 1)
        mock_db['fetch_all'].return_value = []
        traffic = compute_book_traffic(1, None, None)
        assert traffic is not None
        assert traffic['book']['publisher'] is None
        assert traffic['book']['copies'] == 1

    def test_header_renders_details_without_logo(self, librarian_client, mock_db):
        """Validates header renders details without logo `/librarian/analytics?q=clean&book_id=1` as librarian (expects 200) [TestBookHeaderDetails / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = self.FULL_ROW
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics?q=clean&book_id=1')
        assert resp.status_code == 200
        body = resp.data.decode()
        assert 'insights</span>' not in body
        for text in ('Prentice Hall', '978-0132350884', 'QA76.76.R63',
                     'Agile craftsmanship handbook.', 'Call Number', 'ISBN'):
            assert text in body, text


class TestRequestChartsHostile:
    @staticmethod
    def _empty(mock_db):
        """Test helper _empty: build mocked data or DB stub for the test."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []

    def test_chart_new_names_hostile(self, librarian_client, mock_db):
        """Validates chart new names hostile as librarian (expects 200) [TestRequestChartsHostile / analytics].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates dashboard/stats shown to staff are wrong."""
        self._empty(mock_db)
        urls = ['/librarian/analytics/chart?name=requests_by_role&department=<script>',
                '/librarian/analytics/chart?name=requests_trend&preset=bogus',
                '/librarian/analytics/chart?name=requests_by_program&department=' + 'x' * 500,
                '/librarian/analytics/chart?name=top_requested_titles&preset=custom&from=zzz']
        for url in urls:
            assert librarian_client.get(url).status_code == 200, url[:80]

    def test_export_new_sections_empty(self, librarian_client, mock_db):
        """Validates export new sections empty `/librarian/analytics/export` as librarian (expects 200) [TestRequestChartsHostile / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        self._empty(mock_db)
        for kpi in ('top_requested_titles', 'requests_by_role',
                    'requests_trend', 'requests_by_program',
                    'department_leaderboard'):
            resp = librarian_client.post('/librarian/analytics/export',
                                         data={'kpi_type': kpi})
            assert resp.status_code == 200, kpi
            assert resp.data[:4] == b'%PDF'

    def test_leaderboard_malformed_rows(self, librarian_client, mock_db):
        """Validates leaderboard malformed rows `/librarian/analytics/export` as librarian (expects 200) [TestRequestChartsHostile / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_all'].return_value = [('BSIT', 5)]
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'department_leaderboard'})
        assert resp.status_code == 200
        assert resp.data[:4] == b'%PDF'

    def test_dashboard_requests_partial(self, librarian_client, mock_db):
        """Validates dashboard requests partial `/librarian/analytics/dashboard` as librarian (expects 200) [TestRequestChartsHostile / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].side_effect = [
            [('pending_review', None)], [('T', None)], [('T', 1, None, 0, 1)],
            [], [],
        ]
        resp = librarian_client.get('/librarian/analytics/dashboard')
        assert resp.status_code == 200
        assert 'requests' in resp.get_json()

    def test_requests_by_program_pseudo(self, librarian_client, mock_db):
        """Validates requests by program pseudo as librarian (expects 200) [TestRequestChartsHostile / analytics].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from urllib.parse import quote
        mock_db['fetch_all'].return_value = []
        for dept in ('Admin', 'Librarian', 'No program', '', '   ',
                     'BSIS', 'Nope'):
            url = ('/librarian/analytics/chart?name=requests_by_program'
                   '&department=' + quote(dept))
            resp = librarian_client.get(url)
            assert resp.status_code == 200, dept


class TestHeaderEdges:
    FULL = (1, 'Clean Code', 'R. Martin', 'SE', 2008, 2, None, None,
            None, None, None, None)

    def test_null_new_columns(self, librarian_client, mock_db):
        """Validates null new columns `/librarian/analytics?q=c&book_id=1` as librarian (expects 200) [TestHeaderEdges / analytics].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = self.FULL
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics?q=c&book_id=1')
        assert resp.status_code == 200
        assert '—'.encode() in resp.data

    def test_evil_description(self, librarian_client, mock_db):
        """Validates evil description `/librarian/analytics?q=t&book_id=1` as librarian [TestHeaderEdges / analytics].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        evil = '<script>alert(1)</script>'
        row = (1, 'T', 'A', 'C', 2020, 1, 'P', 'E', 'I', 'CN', 'B', evil)
        mock_db['fetch_one'].return_value = row
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/analytics?q=t&book_id=1').data.decode()
        assert evil not in body

    def test_evil_new_fields(self, librarian_client, mock_db):
        """Validates evil new fields `/librarian/analytics?q=t&book_id=1` as librarian [TestHeaderEdges / analytics].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        evil = '"><img src=x onerror=alert(1)>'
        row = (1, 'T', 'A', 'C', 2020, 1, evil, evil, evil, evil, 'B', 'D')
        mock_db['fetch_one'].return_value = row
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/analytics?q=t&book_id=1').data.decode()
        assert evil not in body


class TestDashboardCache:
    def test_fresh_hit_returns_payload(self, mock_db):
        """Validates fresh hit returns payload [TestDashboardCache / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from datetime import datetime
        from app.analytics.models import get_dashboard_cache
        payload = {'usage': {'total': 5}}
        mock_db['fetch_one'].return_value = (payload, datetime.now())
        assert get_dashboard_cache({'start': None, 'end': None, 'departments': []}) == payload
        query = mock_db['fetch_one'].call_args[0][0]
        assert 'analytics_cache' in query
        assert 'circulation_summary' in mock_db['fetch_one'].call_args[0][1][0]

    def test_stale_and_missing_return_none(self, mock_db):
        """Validates stale and missing return none [TestDashboardCache / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from datetime import datetime, timedelta
        from app.analytics.models import get_dashboard_cache
        mock_db['fetch_one'].return_value = ({'a': 1}, datetime.now() - timedelta(hours=1))
        assert get_dashboard_cache({}) is None
        mock_db['fetch_one'].return_value = None
        assert get_dashboard_cache({}) is None
        mock_db['fetch_one'].return_value = ('not-json{{{', datetime.now())
        assert get_dashboard_cache({}) is None

    def test_set_prunes_then_inserts(self, mock_db):
        """Validates set prunes then inserts [TestDashboardCache / analytics].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (DELETE FROM).
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import set_dashboard_cache
        set_dashboard_cache({'start': None}, {'usage': {}}, generated_by=4)
        queries = [c[0][0] for c in mock_db['execute'].call_args_list]
        assert any(q.strip().startswith('DELETE FROM analytics_cache') for q in queries)
        assert any('INSERT INTO analytics_cache' in q for q in queries)

    def test_wrapper_uses_cache_on_hit(self, mock_db):
        """Validates wrapper uses cache on hit [TestDashboardCache / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from unittest.mock import patch
        from app.analytics import routes
        payload = {'usage': {'total': 9}}
        with patch.object(routes, '_dashboard_cache_allowed', return_value=True):
            with patch.object(routes.models, 'get_dashboard_cache', return_value=payload) as mock_get:
                with patch.object(routes.models, 'set_dashboard_cache') as mock_set:
                    assert routes.compute_dashboard(None, None) == payload
                    mock_get.assert_called_once()
                    mock_set.assert_not_called()
        assert mock_db['fetch_all'].call_count == 0

    def test_wrapper_falls_back_and_stores(self, mock_db):
        """Validates wrapper falls back and stores [TestDashboardCache / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from unittest.mock import patch
        from app.analytics import routes
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        stored = {}
        with patch.object(routes, '_dashboard_cache_allowed', return_value=True):
            with patch.object(routes.models, 'get_dashboard_cache', return_value=None):
                with patch.object(routes.models, 'set_dashboard_cache',
                                  side_effect=lambda k, p, g=None: stored.update(payload=p)):
                    out = routes.compute_dashboard(None, None)
                    assert out == routes._compute_dashboard(None, None)
                    assert stored['payload'] == out

    def test_wrapper_bypassed_in_testing(self, mock_db):
        """Validates wrapper bypassed in testing [TestDashboardCache / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics import routes
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        assert routes.compute_dashboard(None, None) == routes._compute_dashboard(None, None)


class TestDatePresets:
    """Overall filter offers Custom dates / This year / This month only."""

    def test_month_resolves_to_calendar_month(self):
        """Validates month resolves to calendar month [TestDatePresets / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        import calendar
        from datetime import date
        from app.analytics.routes import resolve_dates
        today = date.today()
        last_day = calendar.monthrange(today.year, today.month)[1]
        assert resolve_dates('month', None, None) == (
            date(today.year, today.month, 1),
            date(today.year, today.month, last_day))

    def test_month_ignores_stale_dates(self, librarian_client, mock_db):
        """Validates month ignores stale dates `/librarian/analytics?preset=month&from=2020-01-01&to=2020-12-31` as librarian (expects 200) [TestDatePresets / analytics].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates dashboard/stats shown to staff are wrong."""
        import calendar
        from datetime import date
        mock_db['fetch_one'].side_effect = [(10,), (2,)]
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get(
            '/librarian/analytics?preset=month&from=2020-01-01&to=2020-12-31')
        assert resp.status_code == 200
        today = date.today()
        last_day = calendar.monthrange(today.year, today.month)[1]
        expected = (date(today.year, today.month, 1),
                    date(today.year, today.month, last_day))
        params = mock_db['fetch_all'].call_args_list[0][0][1]
        assert params == expected

    def test_semester_still_honored_for_bookmarks(
            self, librarian_client, mock_db):
        """Validates semester still honored for bookmarks `/librarian/analytics?preset=semester` as librarian (expects 200) [TestDatePresets / analytics].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from datetime import date
        mock_db['fetch_one'].side_effect = [(10,), (2,)]
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics?preset=semester')
        assert resp.status_code == 200
        today = date.today()
        if today.month >= 8:
            expected = (date(today.year, 8, 1), date(today.year, 12, 31))
        else:
            expected = (date(today.year, 1, 1), date(today.year, 5, 31))
        params = mock_db['fetch_all'].call_args_list[0][0][1]
        assert params == expected

    def test_only_three_presets_offered(self, librarian_client, mock_db):
        """Validates only three presets offered `/librarian/analytics` as librarian [TestDatePresets / analytics].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = (1,)
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/analytics').data.decode()
        assert 'value="semester"' not in body
        assert 'This semester' not in body
        assert 'value="month"' in body
        assert 'This month' in body
        assert 'value="year"' in body
        assert 'value="custom"' in body

    def test_default_preset_is_this_year(self, librarian_client, mock_db):
        """Validates default preset is this year `/librarian/analytics` as librarian [TestDatePresets / analytics].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = (1,)
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/analytics').data.decode()
        assert "preset: 'year'" in body

    def test_tabs_persist_through_filter(self, librarian_client, mock_db):
        """Validates tabs persist through filter `/librarian/analytics` as librarian [TestDatePresets / analytics].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = (1,)
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/analytics').data.decode()
        # Active tab mirrors into the URL so apply/reset reloads land back.
        assert 'replaceState' in body
        assert "'usage'" in body
        assert 'preset=year&tab=' in body


class TestExportAliasRegression:
    """Duplicate-alias 500s: program queries must not reuse the `b` alias.

    Postgres rejects `JOIN book_catalog b` alongside the shared
    `borrowers b` program join (DuplicateAlias), and mocks never catch
    it — these tests pin the emitted SQL shape instead."""

    @staticmethod
    def _last_query(mock_db):
        return mock_db['fetch_all'].call_args[0][0]

    def test_top_books_breakdown_aliases(self, mock_db):
        """Validates top books breakdown aliases [TestExportAliasRegression / analytics].
    If fails: likely model SQL changed (SELECT).
    Failure indicates dashboard/stats shown to staff are wrong."""
        import re
        from app.analytics.models import top_books_program_breakdown
        mock_db['fetch_all'].return_value = []
        top_books_program_breakdown(None, None, 20, None, ['BSIS'])
        q = self._last_query(mock_db)
        assert 'JOIN book_catalog bk ON' in q
        assert 'JOIN borrowers b ON' in q
        assert 'JOIN book_catalog b ' not in q
        assert not re.search(r'\bbr\.', q)
        assert 'b.department = %s' in q

    def test_top_categories_breakdown_aliases(self, mock_db):
        """Validates top categories breakdown aliases [TestExportAliasRegression / analytics].
    If fails: likely model SQL changed (SELECT).
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import top_categories_by_program
        mock_db['fetch_all'].return_value = []
        top_categories_by_program()
        q = self._last_query(mock_db)
        assert 'JOIN book_catalog bk ON' in q
        assert 'JOIN borrowers b ON' in q
        assert 'JOIN book_catalog b ' not in q

    def test_trend_breakdown_dept_alias(self, mock_db):
        """Validates trend breakdown dept alias [TestExportAliasRegression / analytics].
    If fails: likely model SQL changed (SELECT).
    Failure indicates dashboard/stats shown to staff are wrong."""
        import re
        from app.analytics.models import borrowings_trend_by_program
        mock_db['fetch_all'].return_value = []
        borrowings_trend_by_program(None, None, None, ['BSIS'])
        q = self._last_query(mock_db)
        assert not re.search(r'\bbr\.', q)
        assert 'b.department = %s' in q

    def test_report_types_cover_exportable(self):
        """Validates report types cover exportable [TestExportAliasRegression / analytics].
    If fails: likely model SQL changed (SELECT).
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import ANALYTICS_REPORT_TYPES
        from app.analytics.routes import EXPORTABLE_KPIS
        assert set(EXPORTABLE_KPIS) <= set(ANALYTICS_REPORT_TYPES)

    def test_schema_check_lists_report_types(self):
        """Validates schema check lists report types [TestExportAliasRegression / analytics].
    If fails: likely model SQL changed (SELECT).
    Failure indicates dashboard/stats shown to staff are wrong."""
        import os
        from app.analytics.models import ANALYTICS_REPORT_TYPES
        schema_path = os.path.join(os.path.dirname(__file__), '..',
                                   'app', 'schema.sql')
        with open(schema_path, encoding='utf-8') as f:
            schema_text = f.read()
        for report_type in ANALYTICS_REPORT_TYPES:
            assert f"'{report_type}'" in schema_text, report_type

    def test_export_degrades_on_kpi_failure(
            self, librarian_client, mock_db):
        """Validates export degrades on kpi failure `/librarian/analytics/export` as librarian (expects 200) [TestExportAliasRegression / analytics].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from unittest.mock import patch
        from app.analytics import routes as analytics_routes
        mock_db['fetch_all'].return_value = []
        mock_db['fetch_one'].return_value = (0,)
        real_run_kpi = analytics_routes._run_kpi

        def _flaky(kt, *args, **kwargs):
            if kt == 'top_books':
                raise RuntimeError('boom')
            return real_run_kpi(kt, *args, **kwargs)

        with patch.object(analytics_routes, '_run_kpi', side_effect=_flaky):
            resp = librarian_client.post(
                '/librarian/analytics/export',
                data={'kpi_type': 'all',
                      'kpi_types': 'top_books,most_borrowed_titles'})
        assert resp.status_code == 200
        assert resp.mimetype == 'application/pdf'


class TestCanonicalCategories:
    """Analytics groups by the canonical category vocabulary."""

    @staticmethod
    def _query(mock_db):
        return mock_db['fetch_all'].call_args[0][0]

    def test_top_borrowed_categories_uses_vocabulary(self, mock_db):
        """Validates top borrowed categories uses vocabulary [TestCanonicalCategories / analytics].
    If fails: likely model SQL changed (SELECT).
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import top_borrowed_categories
        mock_db['fetch_all'].return_value = []
        top_borrowed_categories()
        query = self._query(mock_db)
        assert 'LEFT JOIN categories ct' in query
        assert 'ct.name' in query

    def test_top_categories_by_program_uses_vocabulary(self, mock_db):
        """Validates top categories by program uses vocabulary [TestCanonicalCategories / analytics].
    If fails: likely model SQL changed (SELECT).
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import top_categories_by_program
        mock_db['fetch_all'].return_value = []
        top_categories_by_program()
        query = self._query(mock_db)
        assert 'LEFT JOIN categories ct' in query
        assert 'ct.name' in query
        assert 'JOIN book_catalog bk ON' in query

    def test_category_drilldown_uses_vocabulary(self, mock_db):
        """Validates category drilldown uses vocabulary [TestCanonicalCategories / analytics].
    If fails: likely model SQL changed (SELECT).
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import category_borrowings_by_program
        mock_db['fetch_all'].return_value = []
        category_borrowings_by_program('Computer Science')
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'LEFT JOIN categories ct' in query
        assert 'ct.name' in query
        assert params[0] == 'Computer Science'

    def test_collection_by_category_uses_vocabulary(self, mock_db):
        """Validates collection by category uses vocabulary [TestCanonicalCategories / analytics].
    If fails: likely model SQL changed (SELECT).
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import collection_by_category
        mock_db['fetch_all'].return_value = []
        collection_by_category()
        query = self._query(mock_db)
        assert 'LEFT JOIN categories ct' in query
        assert 'ct.name' in query


class TestSchemaGate:
    """Unmigrated databases degrade to legacy shapes instead of 500ing."""

    @staticmethod
    def _reset_gate():
        from app.cataloging import models as _cm
        _cm._multi_cat_state['ok'] = None
        _cm._multi_cat_state['at'] = 0.0

    @staticmethod
    def _missing_table():
        err = Exception('relation "book_categories" does not exist')
        err.pgcode = '42P01'
        return err

    def test_gate_false_on_missing_table(self, mock_db):
        """Validates gate false on missing table [TestSchemaGate / analytics].
    If fails: likely gate logic changed.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.cataloging.models import multi_cat_available
        self._reset_gate()
        try:
            mock_db['fetch_one'].side_effect = self._missing_table()
            assert multi_cat_available() is False
            # Cached: no second probe.
            assert multi_cat_available() is False
            assert mock_db['fetch_one'].call_count == 1
        finally:
            self._reset_gate()

    def test_gate_true_on_other_errors(self, mock_db):
        """Validates gate true on other errors [TestSchemaGate / analytics].
    If fails: likely gate logic changed (masks real bugs).
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.cataloging.models import multi_cat_available
        self._reset_gate()
        try:
            mock_db['fetch_one'].side_effect = RuntimeError('boom')
            assert multi_cat_available() is True
        finally:
            self._reset_gate()

    def test_analytics_falls_back_without_tables(self, mock_db):
        """Validates analytics falls back without tables [TestSchemaGate / analytics].
    If fails: likely gate wiring changed.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from unittest.mock import patch
        from app.analytics.models import (
            collection_by_category, top_borrowed_categories,
            category_borrowings_by_program,
        )
        mock_db['fetch_all'].return_value = []
        with patch('app.cataloging.models.multi_cat_available', return_value=False):
            collection_by_category()
            query = mock_db['fetch_all'].call_args[0][0]
            assert 'categories ct' not in query
            assert 'subject_classification' in query
            top_borrowed_categories()
            query = mock_db['fetch_all'].call_args[0][0]
            assert 'categories ct' not in query
            category_borrowings_by_program('Science')
            query = mock_db['fetch_all'].call_args[0][0]
            assert 'categories ct' not in query

    def test_catalog_filter_falls_back_without_tables(self, mock_db):
        """Validates catalog filter falls back without tables [TestSchemaGate / cataloging].
    If fails: likely gate wiring changed.
    Failure indicates catalog data or listing/sort is wrong."""
        from unittest.mock import patch
        from app.cataloging.models import search_books_filtered
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        with patch('app.cataloging.models.multi_cat_available', return_value=False):
            search_books_filtered('', category='Fiction')
            query, params = mock_db['fetch_all'].call_args[0]
            assert 'book_categories' not in query
            assert 'subject_classification = %s' in query

    def test_distinct_falls_back_without_tables(self, mock_db):
        """Validates distinct falls back without tables [TestSchemaGate / cataloging].
    If fails: likely fallback removed or error misclassified.
    Failure indicates catalog data or listing/sort is wrong."""
        from app.cataloging.models import get_distinct_categories
        mock_db['fetch_all'].side_effect = [
            self._missing_table(), [('Fiction',)],
        ]
        assert get_distinct_categories() == [('Fiction',)]

    def test_export_omits_extra_column_without_tables(self, mock_db):
        """Validates export omits extra column without tables [TestSchemaGate / cataloging].
    If fails: likely gate wiring changed.
    Failure indicates catalog data or listing/sort is wrong."""
        from unittest.mock import patch
        from app.cataloging.models import get_all_books
        mock_db['fetch_all'].return_value = []
        with patch('app.cataloging.models.multi_cat_available', return_value=False):
            get_all_books()
            assert 'extra_categories' not in mock_db['fetch_all'].call_args[0][0]

    def test_export_queries_have_valid_commas(self, mock_db):
        """Validates export queries have valid commas [TestSchemaGate / cataloging].
    If fails: likely column gating broke SELECT syntax (double comma).
    Failure indicates catalog data or listing/sort is wrong."""
        from unittest.mock import patch
        from app.cataloging.models import get_all_books, get_books_by_status
        mock_db['fetch_all'].return_value = []
        for gated in (True, False):
            with patch('app.cataloging.models.multi_cat_available', return_value=gated):
                get_all_books()
                query = mock_db['fetch_all'].call_args[0][0]
                assert ',,' not in query.replace(' ', '')
                assert ('extra_categories' in query) == gated
                get_books_by_status('active')
                query = mock_db['fetch_all'].call_args[0][0]
                assert ',,' not in query.replace(' ', '')
                assert ('extra_categories' in query) == gated


class TestEbookAnalytics:
    def test_ebook_access_trend_passes_rows(self, mock_db):
        """Validates ebook access trend passes rows [TestEbookAnalytics / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from datetime import date
        from app.analytics.models import ebook_access_trend
        rows = [(date(2026, 1, 5), 'BSIT', 3), (date(2026, 1, 5), 'Offline Reader', 1)]
        mock_db['fetch_all'].return_value = rows
        assert ebook_access_trend() == rows
        query = mock_db['fetch_all'].call_args[0][0]
        assert 'ebook_access_log' in query
        assert "WHEN e.user_id IS NULL THEN 'Offline Reader'" in query
        assert 'LEFT JOIN user_accounts u' in query
        assert 'LEFT JOIN borrowers b' in query
        assert 'LEFT JOIN roles r' in query
        assert 'GROUP BY day' in query

    def test_ebook_access_trend_range_params(self, mock_db):
        """Validates ebook access trend range params [TestEbookAnalytics / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import ebook_access_trend
        mock_db['fetch_all'].return_value = []
        ebook_access_trend('2026-01-01', '2026-12-31')
        params = mock_db['fetch_all'].call_args[0][1]
        assert params == ('2026-01-01', '2026-12-31')

    def test_ebook_day_drilldown_rows(self, mock_db):
        """Validates ebook day drilldown rows [TestEbookAnalytics / analytics].
    If fails: likely the dot drill-down model changed shape.
    Failure indicates the E-book trend modal shows wrong program counts."""
        from app.analytics.models import ebook_access_by_program_on_date
        rows = (('BSIT', 4), ('Offline Reader', 2))
        mock_db['fetch_all'].return_value = rows
        assert ebook_access_by_program_on_date('2026-10-18') == rows
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'ebook_access_log' in query
        assert "->date = %s::date" in query or '= %s::date' in query
        assert "WHEN e.user_id IS NULL THEN 'Offline Reader'" in query
        assert params == ('2026-10-18',)

    def test_ebook_day_drilldown_endpoint(self, librarian_client, mock_db):
        """Validates ebook day drilldown endpoint `/librarian/analytics/drilldown?type=ebook_day&date=2026-01-05` as librarian (expects 200) [TestEbookAnalytics / analytics].
    If fails: likely the drilldown route branch changed.
    Failure indicates E-book trend dots cannot open a modal breakdown."""
        rows = [('BSIT', 4), ('Offline Reader', 2)]
        mock_db['fetch_all'].return_value = rows
        resp = librarian_client.get('/librarian/analytics/drilldown?type=ebook_day&date=2026-01-05')
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['type'] == 'ebook_day'
        assert body['key'] == '2026-01-05'
        assert body['unit'] == 'e-book accesses'
        assert body['total'] == 6
        assert body['by_program'] == [['BSIT', 4], ['Offline Reader', 2]]

    def test_ebook_day_drilldown_bad_date(self, librarian_client, mock_db):
        """Validates ebook day drilldown bad date `/librarian/analytics/drilldown?type=ebook_day&date=nope` as librarian (expects 400) [TestEbookAnalytics / analytics].
    If fails: likely the date guard was removed.
    Failure indicates malformed dates reach the model queries."""
        resp = librarian_client.get('/librarian/analytics/drilldown?type=ebook_day&date=nope')
        assert resp.status_code == 400

    def test_top_ebooks_passes_rows(self, mock_db):
        """Validates top ebooks passes rows [TestEbookAnalytics / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import top_ebooks
        rows = [('T', 'A', 5, 2, 7)]
        mock_db['fetch_all'].return_value = rows
        assert top_ebooks(limit=8) == rows
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'ebook_access_log' in query
        assert params == (8,)

    def test_top_ebooks_bad_limit_falls_back(self, mock_db):
        """Validates top ebooks bad limit falls back [TestEbookAnalytics / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import top_ebooks
        mock_db['fetch_all'].return_value = []
        top_ebooks(limit='nope')
        assert mock_db['fetch_all'].call_args[0][1] == (8,)

    def test_book_ebook_accesses_sums_kinds(self, mock_db):
        """Validates book ebook accesses sums kinds [TestEbookAnalytics / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import book_ebook_accesses
        mock_db['fetch_one'].return_value = (5, 2, 7)
        assert book_ebook_accesses(1) == (5, 2, 7)
        query, params = mock_db['fetch_one'].call_args[0]
        assert 'ebook_access_log' in query
        assert params == (1,)

    def test_book_ebook_accesses_bad_id_no_query(self, mock_db):
        """Validates book ebook accesses bad id no query [TestEbookAnalytics / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import book_ebook_accesses
        assert book_ebook_accesses('nope') == (0, 0, 0)
        assert mock_db['fetch_one'].called is False

    def test_book_ebook_recent_lists_reader(self, mock_db):
        """Validates book ebook recent lists reader [TestEbookAnalytics / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from datetime import datetime
        from app.analytics.models import book_ebook_recent
        rows = [(datetime(2026, 1, 5, 9, 30), 'read', 'Juan'),
                (datetime(2026, 1, 4, 10, 0), 'download', 'Anonymous')]
        mock_db['fetch_all'].return_value = rows
        assert book_ebook_recent(2) == rows
        query = mock_db['fetch_all'].call_args[0][0]
        assert "COALESCE(u.full_name, 'Anonymous')" in query
        assert 'LEFT JOIN user_accounts' in query
        assert mock_db['fetch_all'].call_args[0][1] == (2, 10)

    def test_book_ebook_recent_bad_id_no_query(self, mock_db):
        """Validates book ebook recent bad id no query [TestEbookAnalytics / analytics].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates dashboard/stats shown to staff are wrong."""
        from app.analytics.models import book_ebook_recent
        assert book_ebook_recent('zz') == []
        assert mock_db['fetch_all'].called is False

    def test_chart_serves_new_names(self, librarian_client, mock_db):
        """Validates chart serves new names `/librarian/analytics/chart` as librarian (expects 200) [TestEbookAnalytics / analytics].
    If fails: likely route/model wiring changed.
    Failure indicates e-book cards cannot refresh their data."""
        mock_db['fetch_all'].return_value = []
        for name in ('ebook_trend', 'top_ebooks'):
            resp = librarian_client.get(f'/librarian/analytics/chart?name={name}')
            assert resp.status_code == 200, name
            assert resp.get_json()['chart'] == name

    def test_export_serves_new_kpis(self, librarian_client, mock_db):
        """Validates export serves new kpis `/librarian/analytics/export` as librarian (expects 200) [TestEbookAnalytics / analytics].
    If fails: likely export table mapping changed.
    Failure indicates e-book sections cannot be exported as PDF."""
        mock_db['fetch_one'].return_value = []
        mock_db['fetch_all'].return_value = []
        for kpi in ('ebook_trend', 'top_ebooks'):
            resp = librarian_client.post('/librarian/analytics/export',
                                         data={'kpi_type': kpi})
            assert resp.status_code == 200, kpi
            assert resp.data[:4] == b'%PDF'

    def test_dashboard_json_includes_ebook(self, librarian_client, mock_db):
        """Validates dashboard json includes ebook `/librarian/analytics/dashboard` as librarian (expects 200) [TestEbookAnalytics / analytics].
    If fails: likely _compute_dashboard payload changed.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics/dashboard')
        assert resp.status_code == 200
        body = resp.get_json()
        assert 'ebook' in body
        for key in ('trend', 'top_titles'):
            assert key in body['ebook'], key

    def test_page_renders_ebook_cards(self, librarian_client, mock_db):
        """Validates page renders ebook cards `/librarian/analytics` as librarian (expects 200) [TestEbookAnalytics / analytics].
    If fails: likely template regression or section wiring changed.
    Failure indicates dashboard/stats shown to staff are wrong."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/analytics').data.decode()
        assert 'Resource Analytics' in body
        for frag in ('ebook-trend-lines', 'ebook-top-body',
                     '16. E-Book Reads', '17. Top E-Books'):
            assert frag in body, frag

    def test_book_tab_shows_ebook_card(self, librarian_client, mock_db):
        """Validates book tab shows ebook card `/librarian/analytics?q=e&book_id=1` as librarian (expects 200) [TestEbookAnalytics / analytics].
    If fails: likely template regression or traffic payload changed.
    Failure indicates dashboard/stats shown to staff are wrong."""
        row = (1, 'E Title', 'A', 'SE', 2020, 1, 'P', None, None, None,
               'E-Book', 'D')
        mock_db['fetch_one'].return_value = row
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/analytics?q=e&book_id=1').data.decode()
        assert 'E-Book Activity' in body
        assert 'book-ebook-recent' in body

    def test_book_tab_hides_circulation_for_ebook(self, librarian_client, mock_db):
        """Validates book tab hides circulation for ebook `/librarian/analytics?q=e&book_id=1` as librarian (expects 200) [TestEbookAnalytics / analytics].
    If fails: likely template regression or the e-book guard changed.
    Failure indicates e-books show meaningless physical-loan charts."""
        row = (1, 'E Title', 'A', 'SE', 2020, 1, 'P', None, None, None,
               'E-Book', 'D')
        mock_db['fetch_one'].return_value = row
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/analytics?q=e&book_id=1').data.decode()
        for frag in ('id="book-status-lines"', 'id="book-trend"',
                     'id="book-program"', 'id="book-usertype"',
                     'id="book-recent-body"'):
            assert frag not in body, frag

    def test_book_tab_keeps_circulation_for_print(self, librarian_client, mock_db):
        """Validates book tab keeps circulation for print `/librarian/analytics?q=c&book_id=1` as librarian (expects 200) [TestEbookAnalytics / analytics].
    If fails: likely template regression or the e-book guard inverted.
    Failure indicates print titles lose their traffic charts."""
        row = (1, 'Clean Code', 'A', 'SE', 2008, 3, 'P', None, None, None,
               'Book', 'D')
        mock_db['fetch_one'].return_value = row
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/analytics?q=c&book_id=1').data.decode()
        assert 'id="book-status-lines"' in body
        assert 'id="book-trend"' in body
        assert 'id="book-ebook-recent"' not in body
