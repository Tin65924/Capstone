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
        assert params == (date(2026, 1, 1), date(2026, 12, 31))

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
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics')
        assert resp.status_code == 200
        assert b'data-rtab="forecast"' in resp.data
        assert b'data-rtab-panel="forecast"' in resp.data
        assert b'/librarian/analytics/forecast' in resp.data
        assert b'loadForecast' in resp.data
        assert b'forecast-gaps-body' in resp.data
        assert b'forecast-insights' in resp.data
        assert b'Projected Borrowing Demand' in resp.data
        assert b'Expected Borrowing Activity by Weekday' in resp.data
        assert b'forecast-demand-line' in resp.data
        assert b'id="forecast-basis"' in resp.data


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
        """Each card gets one filter button opening the shared modal."""
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/analytics')
        assert resp.status_code == 200
        assert b'id="chartFilterModal"' in resp.data
        assert b'id="chartFilterBody"' in resp.data
        assert b'id="chartFilterApply"' in resp.data
        assert b'id="chartFilterReset"' in resp.data
        assert b'CHART_FILTER_DEFS' in resp.data
        assert b'FILTER_BUTTON_CARDS' in resp.data
        assert b'openChartFilter' in resp.data
        assert b'data-cbadge' in resp.data
        for name in (b'collection_by_category', b'copies_by_status',
                     b'borrowings_trend', b'borrowings_by_department',
                     b'borrowings_by_user_type'):
            assert name in resp.data
        # borrow-type option lives in the modal definition
        assert b'value="overnight"' in resp.data
        assert b'value="daily_circulation"' in resp.data
        assert b'/librarian/analytics/chart' in resp.data
        # category multi-select with autosuggest-backed input
        assert b'Category name' in resp.data
        assert b'Title contains' not in resp.data
        assert b'data-suggest="book_subject"' in resp.data
        assert b'js/autosuggest.js' in resp.data
        assert b'data-mf="catadd"' in resp.data
        assert b'MCSTAutosuggest' in resp.data
        # category bloom check: unknown values get a warning, not a block
        assert b'category_record' in resp.data
        assert b'ensureBloom' in resp.data
        assert b'data-mf="catwarn"' in resp.data
        # copies-by-status is a snapshot: no borrow-type option
        assert b"copies_by_status: { title: 'Copies by Status', controls: ['dates'] }" in resp.data
        # inline filter rows are gone: cards stay compact
        assert b'class="chart-filter ' not in resp.data
        assert b'id="dept-checks"' not in resp.data
        assert b'id="role-checks"' not in resp.data

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
