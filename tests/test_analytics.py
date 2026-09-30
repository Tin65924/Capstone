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

    def test_circulation_overview_returns_tuple(self, mock_db):
        from app.analytics.models import circulation_overview
        mock_db['fetch_one'].side_effect = [(10,), (4,), (2,), (3.0,), (6,), (7,)]
        assert circulation_overview() == (10, 4, 2, 3.0, 60.0, 7)

    def test_circulation_overview_scoped_by_date(self, mock_db):
        from datetime import date
        from app.analytics.models import circulation_overview
        mock_db['fetch_one'].side_effect = [(1,), (1,), (0,), (1.0,), (1,), (1,)]
        circulation_overview(date(2026, 1, 1), date(2026, 12, 31))
        params = mock_db['fetch_one'].call_args_list[0][0][1]
        assert params == (date(2026, 1, 1), date(2026, 12, 31))

    def test_save_report_snapshot(self, mock_db):
        from app.analytics.models import save_report_snapshot
        save_report_snapshot('most_borrowed_titles', {'preset': 'all'}, [['Clean Code', 5]], 3)
        query, params = mock_db['execute'].call_args[0]
        assert 'INSERT INTO analytics_cache' in query
        assert params[0] == 'most_borrowed_titles'
        assert isinstance(params[1], str)   # filter_params serialized to JSON
        assert isinstance(params[2], str)   # kpi_data serialized to JSON


class TestAnalyticsPage:
    def test_page_embeds_dashboard_payload(self, librarian_client, mock_db):
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
        """Each tab's Export Report targets its own sections; Export All is the union."""
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
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics')
        assert resp.status_code == 200
        assert b'Inspired by Riverside' not in resp.data

    def test_attention_cards_link_to_filtered_catalog(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics')
        assert resp.status_code == 200
        for param in (b'copy_status=overdue', b'copy_status=lost_damaged',
                      b'copy_status=maintenance'):
            assert param in resp.data

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

    def test_semester_ignores_stale_dates(self, librarian_client, mock_db):
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
        mock_db['fetch_one'].side_effect = [(10,), (2,)]
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get(
            '/librarian/analytics?preset=bogus&from=2020-01-01&to=2020-12-31')
        assert resp.status_code == 200
        params = mock_db['fetch_all'].call_args_list[0][0][1]
        assert params is None


class TestKpiJson:
    def test_kpi_json_requires_login(self, client, mock_db):
        resp = client.get('/librarian/analytics/kpi?kpi_type=most_borrowed_titles')
        assert resp.status_code == 302

    def test_kpi_json_rejects_invalid_type(self, librarian_client, mock_db):
        resp = librarian_client.get('/librarian/analytics/kpi?kpi_type=bogus')
        assert resp.status_code == 400

    def test_kpi_json_returns_data(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = [('Clean Code', 50)]
        resp = librarian_client.get('/librarian/analytics/kpi?kpi_type=most_borrowed_titles&preset=year')
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['kpi_type'] == 'most_borrowed_titles'
        assert body['data'] == [['Clean Code', 50]]

    def test_kpi_json_passes_dates(self, librarian_client, mock_db):
        from datetime import date
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics/kpi?kpi_type=underutilized_titles&from=2026-01-01&to=2026-12-31')
        assert resp.status_code == 200
        params = mock_db['fetch_all'].call_args[0][1]
        assert params[:2] == (date(2026, 1, 1), date(2026, 12, 31))
        assert params[-1] == 10

    def test_kpi_json_utilization_rate(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [(10,), (2,)]
        resp = librarian_client.get('/librarian/analytics/kpi?kpi_type=utilization_rate')
        assert resp.status_code == 200
        assert resp.get_json()['data'] == 20.0


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
        """CSV format was removed — legacy csv requests now return the polished PDF."""
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
        mock_db['fetch_one'].side_effect = [(10,), (2,)]
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'utilization_rate', 'format': 'csv'})
        assert resp.status_code == 200
        assert resp.content_type == 'application/pdf'
        assert resp.data[:4] == b'%PDF'

    def test_export_csv_all_sections(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (10,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'all', 'format': 'csv'})
        assert resp.status_code == 200
        assert resp.content_type == 'application/pdf'
        assert resp.data[:4] == b'%PDF'


class TestExportXlsx:
    def test_export_xlsx_single_kpi(self, librarian_client, mock_db):
        """XLSX format was removed — legacy xlsx requests now return the polished PDF."""
        mock_db['fetch_all'].return_value = [('Clean Code', 50)]
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'most_borrowed_titles', 'format': 'xlsx'})
        assert resp.status_code == 200
        assert resp.content_type == 'application/pdf'
        assert resp.data[:4] == b'%PDF'

    def test_export_xlsx_all_has_sheet_per_kpi(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (10,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'all', 'format': 'xlsx'})
        assert resp.status_code == 200
        assert resp.content_type == 'application/pdf'
        assert resp.data[:4] == b'%PDF'

    def test_export_pdf_single_kpi(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = [('Clean Code', 50)]
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'most_borrowed_titles', 'format': 'pdf'})
        assert resp.status_code == 200
        assert resp.content_type == 'application/pdf'
        assert resp.data[:4] == b'%PDF'

    def test_export_pdf_all_sections(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (10,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'all', 'format': 'pdf'})
        assert resp.status_code == 200
        assert resp.content_type == 'application/pdf'
        assert resp.data[:4] == b'%PDF'

    def test_export_all_honors_kpi_types_list(self, librarian_client, mock_db):
        """Repeated kpi_types[] fields export only the selected KPIs."""
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
        """Trend DATEs must render as ISO YYYY-MM-DD, not RFC-2822."""
        from datetime import date
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = [(date(2026, 8, 15), 3)]
        resp = librarian_client.get('/librarian/analytics/dashboard')
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['circulation']['trend'] == [['2026-08-15', 3]]
        assert 'Aug' not in str(body['circulation']['trend'])

    def test_circulation_overview_timedelta_avg(self, mock_db):
        """timedelta AVG (interval) converts to fractional days."""
        from datetime import timedelta
        from app.analytics.models import circulation_overview
        mock_db['fetch_one'].side_effect = [
            (10,), (4,), (2,), (timedelta(days=3, hours=12),), (6,), (7,)]
        assert circulation_overview() == (10, 4, 2, 3.5, 60.0, 7)

class TestDashboardExport:
    def test_single_dashboard_section(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = [('Science', 30)]
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'top_categories', 'format': 'pdf'})
        assert resp.status_code == 200
        assert resp.data[:4] == b'%PDF'
        query = mock_db['execute'].call_args[0][0]
        assert 'INSERT INTO analytics_cache' in query

    def test_quick_report_department_usage(self, librarian_client, mock_db):
        """Quick Reports must export their own section, not the old board."""
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
        """Borrower/overdue-by-department charts are exportable sections."""
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
        """Usage-scoped breakdowns filter by the selected program."""
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
        """Department Leaderboard is an exportable department-tab section."""
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
        """9-column recent_circulation must not break the PDF table builder."""
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
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'all', 'format': 'pdf',
                                           'kpi_types': 'not_a_real_kpi'})
        assert resp.status_code == 200
        assert resp.data[:4] == b'%PDF'

    def test_export_escapes_markup_in_titles(self, librarian_client, mock_db):
        """Titles with <...>/& must not 500 the PDF (reportlab XML parse)."""
        mock_db['fetch_all'].return_value = [
            ('A <b>Bold</b> Title & More', 'Auth <X>', 5),
        ]
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'all', 'format': 'pdf',
                                           'kpi_types': 'top_books'})
        assert resp.status_code == 200
        assert resp.data[:4] == b'%PDF'

    def test_export_survives_snapshot_failure(self, librarian_client, mock_db):
        """A failing analytics_cache write must not 500 the export."""
        mock_db['fetch_all'].return_value = [('BSIT', 12)]

        orig_execute = mock_db['execute']

        def _fail_insert(query, params=None):
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
        assert librarian_client.get('/librarian/analytics/export').status_code == 405

    def test_jsonable_handles_dates_and_decimals(self):
        import decimal
        from datetime import date
        from app.analytics.routes import _jsonable
        assert _jsonable([(date(2026, 5, 1), decimal.Decimal('4.5'))]) == [['2026-05-01', 4.5]]
        assert _jsonable(20.0) == 20.0


class TestReportCharts:
    def _export(self, librarian_client, kpi_type, **overrides):
        data = {'kpi_type': kpi_type, 'format': 'pdf'}
        data.update(overrides)
        resp = librarian_client.post('/librarian/analytics/export', data=data)
        assert resp.status_code == 200
        assert resp.content_type == 'application/pdf'
        assert resp.data[:4] == b'%PDF'
        return resp.data

    def test_pie_sections(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = [('A', 10), ('B', 5), ('C', 0)]
        mock_db['fetch_one'].return_value = (20,)
        for kpi in ('copies_by_status', 'top_categories', 'by_user_type',
                    'collection_by_category'):
            self._export(librarian_client, kpi)

    def test_pie_all_zero_skipped(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = [('A', 0)]
        mock_db['fetch_one'].return_value = (0,)
        self._export(librarian_client, 'copies_by_status')

    def test_pie_many_slices_capped(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = [(f'Cat {i}', i + 1) for i in range(15)]
        self._export(librarian_client, 'top_categories')

    def test_line_sections(self, librarian_client, mock_db):
        from datetime import date, timedelta
        base = date(2026, 5, 1)
        mock_db['fetch_all'].return_value = [
            (base + timedelta(days=i), (i * 7) % 13) for i in range(10)]
        self._export(librarian_client, 'trend_borrowings')
        self._export(librarian_client, 'trend_overdue')

    def test_line_long_trend_strided(self, librarian_client, mock_db):
        from datetime import date, timedelta
        base = date(2026, 1, 1)
        mock_db['fetch_all'].return_value = [
            (base + timedelta(days=i), i % 7 + 1) for i in range(200)]
        self._export(librarian_client, 'trend_borrowings')

    def test_bar_sections(self, librarian_client, mock_db):
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
        mock_db['fetch_all'].return_value = [('A', 'oops'), (None, None)]
        self._export(librarian_client, 'top_categories')
        self._export(librarian_client, 'trend_borrowings')

    def test_empty_section_no_chart(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = []
        mock_db['fetch_one'].return_value = (0,)
        self._export(librarian_client, 'top_books')

    def test_charts_embedded_in_pdf(self, librarian_client, mock_db):
        """A charted section must produce vector drawing ops in the PDF."""
        mock_db['fetch_all'].return_value = [('Science', 30), ('Arts', 10)]
        with_charts = self._export(librarian_client, 'top_categories')
        mock_db['fetch_all'].return_value = []
        mock_db['fetch_one'].return_value = (0,)
        without_charts = self._export(librarian_client, 'underutilized_titles')
        assert len(with_charts) > len(without_charts)


class TestChartFilterModels:
    def test_borrowed_per_program_department_filter(self, mock_db):
        from app.analytics.models import books_borrowed_per_program
        mock_db['fetch_all'].return_value = [('BSIT', 12)]
        assert books_borrowed_per_program('2026-01-01', '2026-12-31', ['BSIT', 'BSBA']) == [('BSIT', 12)]
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'b.department IN (%s, %s)' in query
        assert params == ('2026-01-01', '2026-12-31', 'BSIT', 'BSBA')

    def test_borrowed_per_program_blank_departments_ignored(self, mock_db):
        from app.analytics.models import books_borrowed_per_program
        mock_db['fetch_all'].return_value = []
        books_borrowed_per_program(None, None, ['', '  '])
        assert 'b.department IN' not in mock_db['fetch_all'].call_args[0][0]

    def test_user_type_role_filter(self, mock_db):
        from app.analytics.models import borrowings_by_user_type
        mock_db['fetch_all'].return_value = [('Student', 40)]
        assert borrowings_by_user_type(None, None, ['Student']) == [('Student', 40)]
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'r.role_name IN (%s)' in query
        assert params == ('Student',)

    def test_collection_category_multi_select(self, mock_db):
        from app.analytics.models import collection_by_category
        mock_db['fetch_all'].return_value = [('Science', 3)]
        assert collection_by_category(None, None, ['Science', 'Arts']) == [('Science', 3)]
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'LOWER(b.subject_classification) IN (%s, %s)' in query
        assert params == ('science', 'arts')

    def test_collection_category_case_insensitive_and_others(self, mock_db):
        from app.analytics.models import collection_by_category
        mock_db['fetch_all'].return_value = []
        collection_by_category(None, None, ['PHYSICS', 'Others', '  '])
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'LOWER(b.subject_classification) IN (%s)' in query
        assert "b.subject_classification = ''" in query
        assert params == ('physics',)

    def test_collection_category_no_filter_unchanged(self, mock_db):
        from app.analytics.models import collection_by_category
        mock_db['fetch_all'].return_value = []
        collection_by_category()
        assert mock_db['fetch_all'].call_args[0][1] is None

    def test_copies_by_status_summary(self, mock_db):
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
        """Regression: the overview query builder must not raise IndexError."""
        from app.analytics.models import circulation_overview
        mock_db['fetch_one'].side_effect = [
            (100,), (40,), (5,), (4.5,), (90,), (12,),
        ]
        assert circulation_overview('2026-05-01', '2026-05-31') == (100, 40, 5, 4.5, 90.0, 12)

    def test_borrow_type_filter_applies(self, mock_db):
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
        from app.analytics.models import borrowings_trend
        mock_db['fetch_all'].return_value = []
        borrowings_trend()
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'borrow_type' not in query
        assert params is None


class TestForecastModels:
    def test_borrowings_by_weekday_monday_first(self, mock_db):
        from app.analytics.models import borrowings_by_weekday
        mock_db['fetch_all'].return_value = [(0, 4), (6, 9)]
        rows = borrowings_by_weekday('2026-05-01', '2026-05-31')
        assert rows[0][0] == 'Monday'
        assert rows[-1] == ('Sunday', 4)
        assert rows[5] == ('Saturday', 9)
        assert len(rows) == 7
        assert mock_db['fetch_all'].call_args[0][1] == ('2026-05-01', '2026-05-31')

    def test_title_demand_gaps_shape(self, mock_db):
        from app.analytics.models import title_demand_gaps
        mock_db['fetch_all'].return_value = [('T', 'A', 5, 2)]
        assert title_demand_gaps() == [('T', 'A', 5, 2)]
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'reservation_queue' in query
        assert params == (8,)

    def test_count_accessions(self, mock_db):
        from app.analytics.models import count_accessions
        mock_db['fetch_one'].return_value = (15,)
        assert count_accessions('2026-05-01', '2026-05-31') == 15
        assert mock_db['fetch_one'].call_args[0][1] == ('2026-05-01', '2026-05-31')

    def test_trend_direction(self):
        from app.analytics.routes import _trend_direction
        assert _trend_direction([1, 1, 5, 5]) == 'up'
        assert _trend_direction([5, 5, 1, 1]) == 'down'
        assert _trend_direction([3, 3, 3, 3]) == 'flat'
        assert _trend_direction([1]) == 'flat'


class TestForecastJson:
    def _payload_calls(self, mock_db, trend, cats, overdue, accessions, weekday, gaps):
        mock_db['fetch_all'].side_effect = [trend, cats, overdue, weekday, gaps]
        mock_db['fetch_one'].return_value = (accessions,)

    def test_requires_login(self, client, mock_db):
        assert client.get('/librarian/analytics/forecast').status_code == 302

    def test_student_forbidden(self, student_client, mock_db):
        assert student_client.get('/librarian/analytics/forecast').status_code == 302

    def test_projections_math(self, librarian_client, mock_db):
        from datetime import date
        trend = [(date(2026, 5, 1 + i), 2) for i in range(30)]
        self._payload_calls(
            mock_db, trend, [('Sci', 40), ('Arts', 20)],
            [(date(2026, 5, 1), 0)], 15,
            [(1, 5), (2, 5), (3, 5), (4, 5), (5, 5), (6, 12), (0, 2)],
            [('Hot Title', 'Some Author', 5, 2)],
        )
        resp = librarian_client.get('/librarian/analytics/forecast')
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
        from datetime import date
        trend = [(date(2026, 5, 1), 1)]
        overdue = [(date(2026, 5, 1 + i), v) for i, v in enumerate([0, 0, 4, 4])]
        self._payload_calls(mock_db, trend, [], overdue, 0, [], [])
        body = librarian_client.get('/librarian/analytics/forecast').get_json()
        assert body['overdue_direction'] == 'up'
        assert any('circulation' in i['action_url'] for i in body['insights'])

    def test_invalid_preset_still_json(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = []
        mock_db['fetch_one'].return_value = None
        resp = librarian_client.get('/librarian/analytics/forecast?preset=bogus&from=x')
        assert resp.status_code == 200

    def test_projected_trend_weekday_shaped(self, librarian_client, mock_db):
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
        from datetime import date
        trend = [(date(2026, 5, 1), 4)]
        self._payload_calls(mock_db, trend, [], [], 0, [], [])
        body = librarian_client.get('/librarian/analytics/forecast').get_json()
        assert [p[1] for p in body['projected_trend']] == [4.0] * 30

    def test_basis_and_generated_at(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = []
        mock_db['fetch_one'].return_value = None
        body = librarian_client.get(
            '/librarian/analytics/forecast?preset=custom&from=2026-05-01&to=2026-05-31'
        ).get_json()
        assert body['basis'] == 'May 01, 2026 – May 31, 2026'
        assert body['generated_at']


class TestForecastTab:
    def test_page_embeds_forecast_tab(self, librarian_client, mock_db):
        """Insights tab was removed: all cards share the global time filter."""
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
        assert client.get('/librarian/analytics/chart?name=top_books').status_code == 302

    def test_chart_student_forbidden(self, student_client, mock_db):
        assert student_client.get('/librarian/analytics/chart?name=top_books').status_code == 302

    def test_chart_rejects_unknown_name(self, librarian_client, mock_db):
        assert librarian_client.get('/librarian/analytics/chart?name=bogus').status_code == 400
        assert librarian_client.get('/librarian/analytics/chart').status_code == 400

    def test_chart_top_books(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = [('Clean Code', 'Robert Martin', 9)]
        resp = librarian_client.get('/librarian/analytics/chart?name=top_books')
        assert resp.status_code == 200
        assert resp.get_json() == {'chart': 'top_books',
                                   'data': [['Clean Code', 'Robert Martin', 9]],
                                   'filters': {}}

    def test_chart_trend_dates_serialize_iso(self, librarian_client, mock_db):
        from datetime import date
        mock_db['fetch_all'].return_value = [(date(2026, 5, 1), 3)]
        resp = librarian_client.get('/librarian/analytics/chart?name=borrowings_trend')
        assert resp.get_json()['data'] == [['2026-05-01', 3]]

    def test_chart_department_filter(self, librarian_client, mock_db):
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
        mock_db['fetch_all'].return_value = [('Student', 40)]
        resp = librarian_client.get(
            '/librarian/analytics/chart?name=borrowings_by_user_type&role=Student&role=')
        assert resp.get_json()['filters'] == {'roles': ['Student']}
        mock_db['fetch_all'].return_value = [('Science', 2)]
        resp = librarian_client.get(
            '/librarian/analytics/chart?name=collection_by_category&category=Science&category= ')
        assert resp.get_json()['filters'] == {'categories': ['Science']}
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'LOWER(b.subject_classification) IN (%s)' in query
        assert params == ('science',)

    def test_chart_custom_dates(self, librarian_client, mock_db):
        from datetime import date
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get(
            '/librarian/analytics/chart?name=overdue_trend&preset=custom&from=2026-05-01&to=2026-05-31')
        assert resp.status_code == 200
        assert mock_db['fetch_all'].call_args[0][1] == (date(2026, 5, 1), date(2026, 5, 31))

    def test_chart_invalid_dates_fall_back(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics/chart?name=top_categories&from=nope')
        assert resp.status_code == 200

    def test_chart_copies_by_status(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [(50,), (2,), (0,)]
        mock_db['fetch_all'].side_effect = [[('active', 10)], [('available', 30)]]
        resp = librarian_client.get('/librarian/analytics/chart?name=copies_by_status')
        assert resp.status_code == 200
        data = dict(resp.get_json()['data'])
        assert data['Borrowed'] == 10
        assert data['Available'] == 50 - 10 - 0 - 2 - 0 - 0

    def test_chart_borrow_type_filter(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = [(1, 2)]
        resp = librarian_client.get(
            '/librarian/analytics/chart?name=borrowings_trend&borrow_type=overnight')
        assert resp.status_code == 200
        assert resp.get_json()['filters'] == {'borrow_type': 'overnight'}
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'borrow_type = %s' in query
        assert params[-1] == 'overnight'

    def test_chart_borrow_type_combines_with_department(self, librarian_client, mock_db):
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
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get(
            '/librarian/analytics/chart?name=top_books&borrow_type=weekly')
        assert resp.status_code == 200
        assert resp.get_json()['filters'] == {}
        assert 'borrow_type' not in mock_db['fetch_all'].call_args[0][0]


class TestChartFilterControls:
    def test_page_embeds_filter_modal(self, librarian_client, mock_db):
        """Per-card filters were removed: all cards share the global filter."""
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
        """Search + status filter are real inputs; View All links go somewhere."""
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
        """KPI card and Copies-by-Status chart must use one Available formula."""
        from app.analytics.models import copies_by_status_summary
        mock_db['fetch_one'].side_effect = [(100,), (5,), (4,)]
        mock_db['fetch_all'].side_effect = [
            [('active', 20), ('overdue', 3)],
            [('available', 60), ('borrowed', 20), ('lost', 1), ('damaged', 2)],
        ]
        rows = dict(copies_by_status_summary())
        # total - borrowed - overdue - reserved - (lost+damaged+flagged) - missing
        assert rows['Available'] == 100 - 20 - 3 - 5 - (1 + 2 + 4) - 0
        assert rows['Lost / Damaged'] == 1 + 2 + 4

    def test_dashboard_initial_paint_trend_labels_are_iso(self, mock_db):
        """Initial page-load trend labels must be ISO dates, not RFC-2822."""
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
        """Category bloom warning is dead unless the loader decodes it."""
        import pathlib
        js = pathlib.Path('app/static/js/autosuggest.js').read_text(encoding='utf-8')
        assert 'data.category_record' in js


class TestUsageDepartmentFilter:
    def test_trend_department_filter(self, mock_db):
        from app.analytics.models import borrowings_trend
        mock_db['fetch_all'].return_value = []
        borrowings_trend(None, None, None, ['BSIT'])
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'JOIN borrowers' in query
        assert params == ('BSIT',)

    def test_trend_no_department_unchanged(self, mock_db):
        from app.analytics.models import borrowings_trend
        mock_db['fetch_all'].return_value = []
        borrowings_trend()
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'JOIN borrowers' not in query
        assert params is None

    def test_overview_department_scopes(self, mock_db):
        from app.analytics.models import circulation_overview
        mock_db['fetch_one'].side_effect = [
            (10,), (4,), (2,), (3.0,), (6,), (7,)]
        circulation_overview(None, None, ['BSIT'])
        query, params = mock_db['fetch_one'].call_args_list[0][0]
        assert 'JOIN borrowers' in query
        assert params == ('BSIT',)

    def test_top_books_department(self, mock_db):
        from app.analytics.models import top_borrowed_books_detailed
        mock_db['fetch_all'].return_value = []
        top_borrowed_books_detailed(None, None, 5, None, ['BSIT'])
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'JOIN borrowers' in query
        assert 'BSIT' in params

    def test_no_program_pseudo_label(self, mock_db):
        from app.analytics.models import books_borrowed_per_program
        mock_db['fetch_all'].return_value = []
        books_borrowed_per_program(None, None, ['No program'])
        query = mock_db['fetch_all'].call_args[0][0]
        assert 'NOT IN' in query
        assert 'b.department IN' not in query

    def test_dashboard_json_scopes_usage_only(self, librarian_client, mock_db):
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
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get(
            '/librarian/analytics/dashboard?department=BSIT&department=BSBA')
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['usage']['departments'] == ['BSIT', 'BSBA']
        assert body['usage']['department'] == 'BSIT, BSBA'

    def test_page_renders_program_select(self, librarian_client, mock_db):
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
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].return_value = [('BSIT', 12), ('BSBA', 7)]
        resp = librarian_client.get(
            '/librarian/analytics?department=BSIT&department=BSBA')
        assert resp.status_code == 200
        assert b'value="BSIT" checked' in resp.data
        assert b'value="BSBA" checked' in resp.data

    def test_overview_sql_has_valid_spacing(self, mock_db):
        """Regression: every overview query must keep whitespace after the
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
        """Regression: dept-scoped overview joins borrowers, so borrower_id
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
        from app.analytics.models import circulation_overview
        mock_db['fetch_one'].side_effect = [
            (10,), (4,), (2,), (3.0,), (6,), (7,)]
        circulation_overview(None, None, ['BSIT', 'BSBA'])
        query, params = mock_db['fetch_one'].call_args_list[0][0]
        assert 'OR' in query
        assert params == ('BSIT', 'BSBA')

    def test_export_honors_department(self, librarian_client, mock_db):
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
        """Book Analytics lives inside Reports & Analytics: a tab button and
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
        """No book_id -> empty state, and no per-book queries run."""
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
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics?q=++&tab=book')
        assert resp.status_code == 200
        assert b'id="book-empty"' in resp.data
        for c in mock_db['fetch_all'].call_args_list:
            assert 'OR b.author ILIKE' not in c[0][0]

    def test_search_lists_books(self, librarian_client, mock_db):
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
        """Selected book renders graphs (status lines + bars), no KPI cards."""
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
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics?book_id=999&tab=book')
        assert resp.status_code == 200
        assert b'Book not found' in resp.data

    def test_tab_deep_link_script(self, librarian_client, mock_db):
        """?tab=book reopens the tab after picker round-trips."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics')
        assert resp.status_code == 200
        assert b'book-traffic-data' in resp.data
        assert b'renderBookTraffic' in resp.data
        assert b"get('tab') === 'book'" in resp.data


class TestBookAnalyticsJson:
    def test_search_requires_login(self, client, mock_db):
        assert client.get('/librarian/analytics/book/search?q=x').status_code == 302

    def test_search_returns_results(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = [(1, 'Clean Code', 'Robert Martin', 'Science')]
        body = librarian_client.get('/librarian/analytics/book/search?q=clean').get_json()
        assert body == {'results': [
            {'book_id': 1, 'title': 'Clean Code',
             'author': 'Robert Martin', 'category': 'Science'}]}

    def test_search_blank_returns_empty(self, librarian_client, mock_db):
        body = librarian_client.get('/librarian/analytics/book/search?q=').get_json()
        assert body == {'results': []}
        assert mock_db['fetch_all'].call_count == 0

    def test_data_requires_login(self, client, mock_db):
        assert client.get('/librarian/analytics/book/data?book_id=1').status_code == 302

    def test_data_rejects_bad_id(self, librarian_client, mock_db):
        assert librarian_client.get('/librarian/analytics/book/data').status_code == 400
        assert librarian_client.get(
            '/librarian/analytics/book/data?book_id=abc').status_code == 400

    def test_data_404_for_missing_book(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = None
        resp = librarian_client.get('/librarian/analytics/book/data?book_id=999')
        assert resp.status_code == 404

    def test_data_returns_traffic(self, librarian_client, mock_db):
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
        """Per-status rows pivot into zero-filled series over shared dates."""
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
        body = librarian_client.get('/librarian/analytics/book/data?book_id=1').get_json()
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
        """Custom range: lone spikes render on the full daily axis, zero-filled."""
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
        """Absurd ranges skip the fill and keep observed dates only."""
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
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics')
        assert resp.status_code == 200
        assert b'Only one day with activity' in resp.data


class TestBookAnalyticsModels:
    def test_search_blank_runs_no_query(self, mock_db):
        from app.analytics.models import search_books_for_analytics
        assert search_books_for_analytics('   ') == []
        assert mock_db['fetch_all'].call_count == 0

    def test_search_filters_active_titles(self, mock_db):
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
        from app.analytics.models import book_traffic_overview
        assert book_traffic_overview('nope') == (0, 0, 0, 0, 0, 0.0, 0.0)
        assert mock_db['fetch_one'].call_count == 0

    def test_overview_returns_tuple(self, mock_db):
        from app.analytics.models import book_traffic_overview
        mock_db['fetch_one'].side_effect = [
            (10,), (4,), (2,), (6,), (5,), (4.0,)]
        assert book_traffic_overview(1) == (10, 4, 2, 6, 5, 4.0, 60.0)

    def test_book_trend_scoped_to_book(self, mock_db):
        from datetime import date
        from app.analytics.models import book_borrowings_trend
        mock_db['fetch_all'].return_value = [(date(2026, 5, 1), 3)]
        assert book_borrowings_trend(1) == [(date(2026, 5, 1), 3)]
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'c.book_id = %s' in query
        assert params[0] == 1

    def test_recent_circulation_shows_accession_number(self, mock_db):
        """Recent circulation exposes Accession No., not the TXN id."""
        from app.analytics.models import recent_circulation
        mock_db['fetch_all'].return_value = []
        recent_circulation()
        query = mock_db['fetch_all'].call_args[0][0]
        assert 'a.accession_number' in query
        assert 'JOIN accession_log a ON a.accession_id = c.accession_id' in query
        assert 'c.circulation_id' not in query

    def test_book_status_trends_unions_circulation_and_reservations(self, mock_db):
        from datetime import date
        from app.analytics.models import book_status_trends
        mock_db['fetch_all'].return_value = [(date(2026, 5, 1), 'borrowed', 3)]
        assert book_status_trends(1) == [(date(2026, 5, 1), 'borrowed', 3)]
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'UNION ALL' in query
        assert "transaction_type = 'borrow'" in query
        assert "transaction_type = 'return'" in query
        assert "transaction_status = 'overdue'" in query
        assert 'reservation_queue' in query
        assert 'reservation_status' in query
        # book_id scopes all four legs (3 circulation + 1 reservation)
        assert params[:4] == (1, 1, 1, 1)
        assert 'ORDER BY day' in query

    def test_book_status_trends_bad_id_runs_no_query(self, mock_db):
        from app.analytics.models import book_status_trends
        assert book_status_trends('nope') == []
        assert mock_db['fetch_all'].call_count == 0


class TestAnalyticsTabRefresh:
    def test_circulation_tracking_rename(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics')
        assert resp.status_code == 200
        assert b'Circulation Tracking' in resp.data
        assert b'Collection Tracking' not in resp.data

    def test_hbars_show_top_10(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics')
        assert resp.status_code == 200
        assert b'slice(0, 10)' in resp.data

    def test_expand_modal_present_on_all_tabs(self, librarian_client, mock_db):
        """Every non-pie graph card gets an expand (open_in_full) button
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
        """Expanded modal re-renders full datasets with scrollable bars/tables."""
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
        """Status Trends card offers a filter button opening a checkbox modal."""
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
        from app.analytics.models import top_requested_titles
        mock_db['fetch_all'].return_value = [('Data Science', 5)]
        assert top_requested_titles() == [('Data Science', 5)]
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'FROM request_records' in query
        assert params[-1] == 10

    def test_top_requested_titles_scoped_by_date(self, mock_db):
        from app.analytics.models import top_requested_titles
        top_requested_titles('2026-01-01', '2026-12-31')
        params = mock_db['fetch_all'].call_args[0][1]
        assert params == ('2026-01-01', '2026-12-31', 10)

    def test_requests_by_role_split(self, mock_db):
        from app.analytics.models import requests_by_role_split
        mock_db['fetch_all'].return_value = [('Data Science', 3, 2, 0, 5)]
        assert requests_by_role_split() == [('Data Science', 3, 2, 0, 5)]
        query = mock_db['fetch_all'].call_args[0][0]
        assert 'JOIN roles r' in query
        assert "FILTER (WHERE r.role_name = 'Student')" in query

    def test_requests_trend(self, mock_db):
        from app.analytics.models import requests_trend
        from datetime import date
        mock_db['fetch_all'].return_value = [(date(2026, 1, 5), 2)]
        assert requests_trend() == [(date(2026, 1, 5), 2)]
        query = mock_db['fetch_all'].call_args[0][0]
        assert 'request_date::date' in query

    def test_requests_by_program(self, mock_db):
        from app.analytics.models import requests_by_program
        mock_db['fetch_all'].return_value = [('BSIS', 4)]
        assert requests_by_program() == [('BSIS', 4)]
        query = mock_db['fetch_all'].call_args[0][0]
        assert 'program_label' in query

    def test_requests_by_program_scoped_by_department(self, mock_db):
        from app.analytics.models import requests_by_program
        requests_by_program(departments=['BSIS'])
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'BSIS' in params

    def test_requests_by_status(self, mock_db):
        from app.analytics.models import requests_by_status
        mock_db['fetch_all'].return_value = [('pending_review', 3), ('approved', 1)]
        assert requests_by_status() == [('pending_review', 3), ('approved', 1)]

    def test_dashboard_json_includes_requests(self, librarian_client, mock_db):
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
        mock_db['fetch_all'].return_value = []
        for kpi in ('top_requested_titles', 'requests_by_role',
                    'requests_trend', 'requests_by_program'):
            resp = librarian_client.get(f'/librarian/analytics/kpi?kpi_type={kpi}')
            assert resp.status_code == 400

    def test_chart_json_new_names(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = []
        for name in ('top_requested_titles', 'requests_by_role',
                     'requests_trend', 'requests_by_program'):
            resp = librarian_client.get(f'/librarian/analytics/chart?name={name}')
            assert resp.status_code == 200
            assert resp.get_json()['chart'] == name

    def test_export_new_kpi_returns_pdf(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = [('Data Science', 3, 2, 0, 5)]
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'requests_by_role', 'format': 'pdf'})
        assert resp.status_code == 200
        assert resp.content_type == 'application/pdf'
        assert resp.data[:4] == b'%PDF'

    def test_page_has_requests_tab(self, librarian_client, mock_db):
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
        """Top requested-title bars navigate to the requests page pre-searched."""
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
        from app.analytics.routes import compute_book_traffic
        mock_db['fetch_one'].return_value = (1, 'Clean Code', 'R. Martin', 'SE', 2008, 1)
        mock_db['fetch_all'].return_value = []
        traffic = compute_book_traffic(1, None, None)
        assert traffic is not None
        assert traffic['book']['publisher'] is None
        assert traffic['book']['copies'] == 1

    def test_header_renders_details_without_logo(self, librarian_client, mock_db):
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
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []

    def test_chart_new_names_hostile(self, librarian_client, mock_db):
        self._empty(mock_db)
        urls = ['/librarian/analytics/chart?name=requests_by_role&department=<script>',
                '/librarian/analytics/chart?name=requests_trend&preset=bogus',
                '/librarian/analytics/chart?name=requests_by_program&department=' + 'x' * 500,
                '/librarian/analytics/chart?name=top_requested_titles&preset=custom&from=zzz']
        for url in urls:
            assert librarian_client.get(url).status_code == 200, url[:80]

    def test_export_new_sections_empty(self, librarian_client, mock_db):
        self._empty(mock_db)
        for kpi in ('top_requested_titles', 'requests_by_role',
                    'requests_trend', 'requests_by_program',
                    'department_leaderboard'):
            resp = librarian_client.post('/librarian/analytics/export',
                                         data={'kpi_type': kpi})
            assert resp.status_code == 200, kpi
            assert resp.data[:4] == b'%PDF'

    def test_leaderboard_malformed_rows(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = [('BSIT', 5)]
        resp = librarian_client.post('/librarian/analytics/export',
                                     data={'kpi_type': 'department_leaderboard'})
        assert resp.status_code == 200
        assert resp.data[:4] == b'%PDF'

    def test_dashboard_requests_partial(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].side_effect = [
            [('pending_review', None)], [('T', None)], [('T', 1, None, 0, 1)],
            [], [],
        ]
        resp = librarian_client.get('/librarian/analytics/dashboard')
        assert resp.status_code == 200
        assert 'requests' in resp.get_json()

    def test_requests_by_program_pseudo(self, librarian_client, mock_db):
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
        mock_db['fetch_one'].return_value = self.FULL
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics?q=c&book_id=1')
        assert resp.status_code == 200
        assert '—'.encode() in resp.data

    def test_evil_description(self, librarian_client, mock_db):
        evil = '<script>alert(1)</script>'
        row = (1, 'T', 'A', 'C', 2020, 1, 'P', 'E', 'I', 'CN', 'B', evil)
        mock_db['fetch_one'].return_value = row
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/analytics?q=t&book_id=1').data.decode()
        assert evil not in body

    def test_evil_new_fields(self, librarian_client, mock_db):
        evil = '"><img src=x onerror=alert(1)>'
        row = (1, 'T', 'A', 'C', 2020, 1, evil, evil, evil, evil, 'B', 'D')
        mock_db['fetch_one'].return_value = row
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/analytics?q=t&book_id=1').data.decode()
        assert evil not in body
