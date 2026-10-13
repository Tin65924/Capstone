"""Edge-case regression tests for the Cataloging page.

Covers `/librarian/cataloging` CRUD and helpers beyond the baseline
suite: year bounds/garbage on add/edit, oversized input, XSS in every
field (including quote-breakout attempts against the tojson-powered
edit modals), export content correctness (headers, accession column,
XLSX, status filters), staff search oddities, missing-book accession
writes, unknown bulk-import jobs, and the archive-then-delete flow.
"""

BOOK16 = (1, 'Clean Code', 'R. Martin', '1st', 'Pub', 2008, 'SE', 'C1',
          '978', 'Book', 'Desc', 'active', '2026-01-01', '2026-05-05',
          None, 'ACC-001')


class TestFieldBounds:
    def test_year_variants(self, librarian_client, mock_db):
        """Validates year variants `/librarian/cataloging/add` as librarian (expects 302) [TestFieldBounds / cataloging edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        for year in ('-500', '99999', '9999999999', 'abc', '20.5', ''):
            resp = librarian_client.post(
                '/librarian/cataloging/add',
                data={'title': 'T', 'author': 'A', 'year_published': year})
            assert resp.status_code == 302, year

    def test_edit_year_variants(self, librarian_client, mock_db):
        """Validates edit year variants `/librarian/cataloging/1/edit` as librarian (expects 302) [TestFieldBounds / cataloging edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].return_value = BOOK16
        for year in ('-1', '3000', 'junk'):
            resp = librarian_client.post(
                '/librarian/cataloging/1/edit',
                data={'title': 'T', 'author': 'A', 'year_published': year})
            assert resp.status_code == 302, year

    def test_huge_strings(self, librarian_client, mock_db):
        """Validates huge strings `/librarian/cataloging/add` as librarian (expects 302) [TestFieldBounds / cataloging edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.post(
            '/librarian/cataloging/add',
            data={'title': 'T' * 3000, 'author': 'A' * 3000,
                  'description': 'D' * 20000})
        assert resp.status_code == 302


class TestXssModals:
    def test_evil_fields_render_escaped(self, librarian_client, mock_db):
        """Validates evil fields render escaped `/librarian/cataloging` as librarian [TestXssModals / cataloging edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        evil = '<script>alert(1)</script>'
        row = (1, evil, evil, evil, evil, 2020, evil, evil, evil, 'Book',
               evil, 'active', '2026-01-01', None, None, 'ACC-1')
        mock_db['fetch_all'].side_effect = [[row], []]
        body = librarian_client.get('/librarian/cataloging').data.decode()
        assert evil not in body

    def test_evil_quote_breakout(self, librarian_client, mock_db):
        # tojson escapes ' as \u0027 and " survives only as \" inside the
        # single-quoted data-book attr (no breakout); editBook() then assigns
        # parsed values to input.value (text, never HTML).
        """Validates evil quote breakout `/librarian/cataloging` as librarian [TestXssModals / cataloging edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates catalog data or listing/sort is wrong."""
        evil = '\'" onclick=alert(1) x="'
        row = (1, evil, 'A', '', '', None, '', '', '', 'Book', '',
               'active', '2026-01-01', None, None, 'ACC-1')
        mock_db['fetch_all'].side_effect = [[row], []]
        body = librarian_client.get('/librarian/cataloging').data.decode()
        assert evil not in body
        assert '\\u0027' in body
        assert 'onclick="editBook(this)"' in body


class TestExportContent:
    def test_csv_headers_and_accession(self, librarian_client, mock_db):
        """Validates csv headers and accession `/librarian/cataloging/export?format=csv` as librarian (expects 200) [TestExportContent / cataloging edge cases].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_all'].return_value = [BOOK16]
        resp = librarian_client.get('/librarian/cataloging/export?format=csv')
        assert resp.status_code == 200
        body = resp.data.decode()
        assert 'Accession Numbers' in body.splitlines()[0]
        assert 'ACC-001' in body
        assert '2026-05-05' not in body

    def test_xlsx_export(self, librarian_client, mock_db):
        """Validates xlsx export `/librarian/cataloging/export?format=xlsx` as librarian (expects 200) [TestExportContent / cataloging edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_all'].return_value = [BOOK16]
        resp = librarian_client.get('/librarian/cataloging/export?format=xlsx')
        assert resp.status_code == 200
        assert 'spreadsheet' in resp.content_type

    def test_export_status_filter(self, librarian_client, mock_db):
        """Validates export status filter as librarian (expects 200) [TestExportContent / cataloging edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_all'].return_value = []
        for url in ('/librarian/cataloging/export?status=archived',
                    '/librarian/cataloging/export?status=bogus&format=xlsx'):
            assert librarian_client.get(url).status_code == 200, url


class TestMiscEdges:
    def test_staff_search_bogus(self, librarian_client, mock_db):
        """Validates staff search bogus as librarian (expects 200) [TestMiscEdges / cataloging edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        for url in ('/librarian/cataloging?field=bogus&q=x',
                    '/librarian/cataloging?page=abc',
                    '/librarian/cataloging?page=-2',
                    '/librarian/cataloging?q=' + 'z' * 3000):
            assert librarian_client.get(url).status_code == 200, url[:60]

    def test_accession_missing_book(self, librarian_client, mock_db):
        """Validates accession missing book `/librarian/cataloging/999/accession/add` as librarian (expects 302) [TestMiscEdges / cataloging edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].return_value = None
        assert librarian_client.post(
            '/librarian/cataloging/999/accession/add',
            data={'accession_number': 'X-1'}).status_code == 302

    def test_bulk_status_unknown_job(self, librarian_client):
        """Validates bulk status unknown job `/librarian/cataloging/bulk-import/status/nope` as librarian (expects 404) [TestMiscEdges / cataloging edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        assert librarian_client.get(
            '/librarian/cataloging/bulk-import/status/nope').status_code == 404

    def test_toggle_then_delete_flow(self, librarian_client, mock_db):
        """Validates toggle then delete flow `/librarian/cataloging/1/status` as librarian (expects 302) [TestMiscEdges / cataloging edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].return_value = BOOK16
        assert librarian_client.post(
            '/librarian/cataloging/1/status').status_code == 302
        mock_db['fetch_one'].return_value = None
        assert librarian_client.post(
            '/librarian/cataloging/1/delete').status_code == 302
