"""Audit Logs info buttons + documentation modal (admin).

Mocked DB — no Postgres. Every KPI tile and chart header carries an
info button opening a per-metric documentation panel.
"""

EXPECTED_KEYS = [
    'kpi-logins-today', 'kpi-logins-7d', 'kpi-active-now',
    'kpi-failed-logins', 'kpi-denials', 'kpi-server-errors',
    'chart-logins-day', 'chart-errors-day', 'chart-categories',
    'chart-roles', 'top-error-paths',
]


class TestAuditInfoWiring:
    def test_modal_and_registry_present(self, admin_client, mock_db):
        """Validates the info modal shell and registry ship with the page."""
        mock_db['fetch_all'].return_value = []
        mock_db['fetch_one'].return_value = None
        body = admin_client.get('/admin/audits').data.decode()
        assert 'id="auditInfoModal"' in body
        assert 'id="auditInfoTitle"' in body
        assert 'id="auditInfoBody"' in body
        assert 'var AUDIT_INFO' in body
        assert 'initAuditInfo' in body
        assert 'openAuditInfo' in body
        assert 'closeAuditInfo' in body
        assert 'audit-info-btn' in body
        assert 'data-audit-info' in body

    def test_every_card_documented(self, admin_client, mock_db):
        """Validates each KPI tile and chart has a registry entry."""
        mock_db['fetch_all'].return_value = []
        mock_db['fetch_one'].return_value = None
        body = admin_client.get('/admin/audits').data.decode()
        for key in EXPECTED_KEYS:
            assert ("'%s': { t:" % key) in body, key
        assert body.count('{ t: ') >= len(EXPECTED_KEYS)

    def test_entries_have_core_fields(self, admin_client, mock_db):
        """Validates entries carry definition/calculation, not just titles."""
        mock_db['fetch_all'].return_value = []
        mock_db['fetch_one'].return_value = None
        body = admin_client.get('/admin/audits').data.decode()
        assert body.count('def: ') >= len(EXPECTED_KEYS)
        assert body.count('calc: ') >= len(EXPECTED_KEYS)
        assert body.count('interp: ') >= len(EXPECTED_KEYS)
        assert body.count('ex: ') >= len(EXPECTED_KEYS)

    def test_priority_sections_rendered(self, admin_client, mock_db):
        """Validates the doc section headings exist in the renderer."""
        mock_db['fetch_all'].return_value = []
        mock_db['fetch_one'].return_value = None
        body = admin_client.get('/admin/audits').data.decode()
        for section in ('Definition', 'How to interpret',
                        "How it's calculated", 'Example', 'Data source',
                        'Date range', 'Limitations'):
            assert section in body, section

    def test_charts_still_hoverable(self, admin_client, mock_db):
        """Validates the chart painters and tooltips are untouched."""
        mock_db['fetch_all'].return_value = []
        mock_db['fetch_one'].return_value = None
        body = admin_client.get('/admin/audits').data.decode()
        assert 'AuditCharts.line' in body
        assert 'AuditCharts.hbars' in body
        assert 'AuditCharts.donut' in body
        assert 'audit-chart-tip' in body
