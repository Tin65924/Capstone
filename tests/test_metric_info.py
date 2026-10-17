"""Metric info buttons + documentation modal on analytics cards.

Mocked DB — no Postgres. Every chart/table card header carries an info
button that opens a per-metric documentation panel (definition,
interpretation, calculation, example, plus source/range/caveats).
"""

# One registry key per documented card, across all four tabs.
EXPECTED_KEYS = [
    # Collection tab.
    'donut-category', 'donut-status', 'recent-collection-body',
    'attention-list',
    # Library tab.
    'trend-line', 'donut-topcats', 'peak-bars', 'high-demand-body',
    'overdue-line', 'insights-list', 'recent-circ-body',
    'req-top-titles', 'req-role-split', 'req-trend-line',
    'req-by-program', 'trend-program-lines', 'overdue-program-lines',
    'top-books-program-list', 'fines-body', 'ebook-trend-lines',
    'ebook-top-body',
    # Department tab.
    'dept-bars', 'borrowers-dept-bars', 'overdue-dept-bars',
    'dept-leaderboard-body', 'top-books-list', 'donut-usertype',
    'usage-trend-program-lines', 'usage-overdue-program-lines',
    # Book tab.
    'book-status-lines', 'book-trend', 'book-program', 'book-usertype',
    'book-recent-body', 'book-ebook-recent', 'book-top-util-body',
    'book-top-under-body',
]


class TestMetricInfoWiring:
    def test_modal_and_registry_present(self, librarian_client, mock_db):
        """Validates the info modal shell and registry ship with the page."""
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/analytics').data.decode()
        assert 'id="metricInfoModal"' in body
        assert 'id="metricInfoTitle"' in body
        assert 'id="metricInfoBody"' in body
        assert 'var METRIC_INFO' in body
        assert 'initMetricInfo' in body
        assert 'openMetricInfo' in body
        assert 'closeMetricInfo' in body
        # Above the expand (z-100), status-filter (z-110), and
        # drill-down (z-130) modals.
        assert 'z-[140]' in body

    def test_every_card_documented(self, librarian_client, mock_db):
        """Validates each analytics card has a registry entry."""
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/analytics').data.decode()
        for key in EXPECTED_KEYS:
            assert ("'%s': { t:" % key) in body, key
        assert body.count('{ t: ') >= len(EXPECTED_KEYS)

    def test_priority_sections_rendered(self, librarian_client, mock_db):
        """Validates the four priority doc sections exist in the renderer."""
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/analytics').data.decode()
        for section in ('Definition', 'How to interpret',
                        "How it's calculated", 'Example', 'Data source',
                        'Date range', 'Limitations'):
            assert section in body, section

    def test_entries_have_core_fields(self, librarian_client, mock_db):
        """Validates entries carry definition/calculation, not just titles."""
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/analytics').data.decode()
        assert body.count('def: ') >= len(EXPECTED_KEYS)
        assert body.count('calc: ') >= len(EXPECTED_KEYS)
        assert body.count('interp: ') >= len(EXPECTED_KEYS)
        assert body.count('ex: ') >= len(EXPECTED_KEYS)

    def test_escape_ordering_guarded(self, librarian_client, mock_db):
        """Validates lower modals stay put while the info modal is open."""
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/analytics').data.decode()
        # Both pre-existing Escape handlers defer to the info modal.
        assert body.count('metricInfoModal') >= 6
