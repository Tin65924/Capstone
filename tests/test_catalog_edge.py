"""Edge-case regression tests for the Catalog surface.

Covers the public catalog (`/catalog`), book detail (`/book/<id>`), and
librarian cataloging (CRUD, accessions, export, bulk-import status):
empty database, hostile filter params (oversized/XSS input, garbage
years/pages, bogus enums), missing-book handling, archive-before-delete
enforcement, missing accession fields, XSS book data, and auth guards.
Includes regression tests for two fixed crashes: unvalidated year
filters (`ValueError` -> 500) and unguarded `None` iteration on the
detail page. Everything must degrade gracefully — never 500, never raw
HTML injection.
"""

ACTIVE_BOOK = (1, 'Clean Code', 'R. Martin', '1st', 'Pub', 2008, 'SE',
               'C1', '978', 'Book', 'Desc', 'active', '2026-01-01', None, None)
ARCHIVED_BOOK = (2, 'Old', 'A', '', '', None, '', '', '', '', '', 'archived',
                 '2026-01-01', None, None)


class TestEmptyDb:
    @staticmethod
    def _empty(mock_db):
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        mock_db['execute'].return_value = []

    def test_public_catalog_empty(self, client, mock_db):
        """Validates public catalog empty `/catalog` (expects 200) [TestEmptyDb / catalog edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        self._empty(mock_db)
        assert client.get('/catalog').status_code == 200

    def test_book_missing_redirects(self, client, mock_db):
        """Validates book missing redirects `/book/999999` (expects 302) [TestEmptyDb / catalog edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates catalog data or listing/sort is wrong."""
        self._empty(mock_db)
        resp = client.get('/book/999999')
        assert resp.status_code == 302
        assert '/catalog' in resp.location

    def test_librarian_catalog_empty(self, librarian_client, mock_db):
        """Validates librarian catalog empty `/librarian/cataloging` as librarian (expects 200) [TestEmptyDb / catalog edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        self._empty(mock_db)
        assert librarian_client.get('/librarian/cataloging').status_code == 200

    def test_export_empty(self, librarian_client, mock_db):
        """Validates export empty `/librarian/cataloging/export?format=csv` as librarian (expects 200) [TestEmptyDb / catalog edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        self._empty(mock_db)
        assert librarian_client.get(
            '/librarian/cataloging/export?format=csv').status_code == 200


class TestHostileParams:
    @staticmethod
    def _ok(mock_db):
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []

    def test_public_filters(self, client, mock_db):
        """Validates public filters (expects 200) [TestHostileParams / catalog edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        self._ok(mock_db)
        urls = ['/catalog?q=' + 'x' * 4000,
                '/catalog?q=<script>alert(1)</script>',
                '/catalog?field=drop_table&q=x',
                '/catalog?year_from=abc&year_to=--',
                '/catalog?year_from=2050&year_to=2000',
                '/catalog?sort_by=drop_table',
                '/catalog?category=<img src=x>',
                '/catalog?material_type=Nope&availability=bogus',
                '/catalog?view=bogus', '/catalog?page=abc',
                '/catalog?page=-5', '/catalog?page=999999']
        for url in urls:
            assert client.get(url).status_code == 200, url[:70]

    def test_staff_filters(self, librarian_client, mock_db):
        """Validates staff filters as librarian [TestHostileParams / catalog edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        self._ok(mock_db)
        urls = ['/librarian/cataloging?q=' + 'y' * 3000,
                '/librarian/cataloging?status=bogus',
                '/librarian/cataloging?copy_status=bogus',
                '/librarian/cataloging?page=abc',
                '/librarian/cataloging?page=-3',
                '/librarian/cataloging/export?format=bogus',
                '/librarian/cataloging/export?status=bogus',
                '/librarian/cataloging/bulk-import/status/nope']
        for url in urls:
            resp = librarian_client.get(url)
            assert resp.status_code in (200, 404), (url, resp.status_code)

    def test_book_variants(self, client, mock_db):
        """Validates book variants `/book/999999999` (expects 302) [TestHostileParams / catalog edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates catalog data or listing/sort is wrong."""
        self._ok(mock_db)
        mock_db['fetch_one'].return_value = None
        assert client.get('/book/999999999').status_code == 302


class TestWrites:
    @staticmethod
    def _ok(mock_db):
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []

    def test_add_book_validation(self, librarian_client, mock_db):
        """Validates add book validation `/librarian/cataloging/add` as librarian (expects 302) [TestWrites / catalog edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        self._ok(mock_db)
        assert librarian_client.post(
            '/librarian/cataloging/add', data={}).status_code == 302
        assert librarian_client.post(
            '/librarian/cataloging/add',
            data={'title': '', 'author': ''}).status_code == 302

    def test_edit_missing_book(self, librarian_client, mock_db):
        """Validates edit missing book `/librarian/cataloging/999999/edit` as librarian (expects 302) [TestWrites / catalog edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        self._ok(mock_db)
        assert librarian_client.post(
            '/librarian/cataloging/999999/edit',
            data={'title': 'X'}).status_code == 302

    def test_delete_active_book_refused(self, librarian_client, mock_db):
        """Validates delete active book refused `/librarian/cataloging/1/delete` as librarian (expects 302) [TestWrites / catalog edge cases].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].return_value = ACTIVE_BOOK
        resp = librarian_client.post('/librarian/cataloging/1/delete')
        assert resp.status_code == 302
        world = [c[0][0] for c in mock_db['execute'].call_args_list]
        assert not any('DELETE' in q for q in world)

    def test_delete_archived_book(self, librarian_client, mock_db):
        """Validates delete archived book `/librarian/cataloging/2/delete` as librarian (expects 302) [TestWrites / catalog edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].return_value = ARCHIVED_BOOK
        assert librarian_client.post(
            '/librarian/cataloging/2/delete').status_code == 302

    def test_toggle_bogus_status(self, librarian_client, mock_db):
        """Validates toggle bogus status `/librarian/cataloging/1/status` as librarian (expects 302) [TestWrites / catalog edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].return_value = ACTIVE_BOOK
        assert librarian_client.post(
            '/librarian/cataloging/1/status',
            data={'status': 'drop_table'}).status_code == 302

    def test_accession_missing_fields(self, librarian_client, mock_db):
        """Validates accession missing fields `/librarian/cataloging/1/accession/add` as librarian (expects 302) [TestWrites / catalog edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        self._ok(mock_db)
        assert librarian_client.post(
            '/librarian/cataloging/1/accession/add',
            data={}).status_code == 302
        assert librarian_client.post(
            '/librarian/cataloging/accession/999/edit',
            data={}).status_code == 302
        assert librarian_client.post(
            '/librarian/cataloging/accession/999/delete').status_code == 302


class TestXss:
    def test_evil_book_on_catalog(self, client, mock_db):
        """Validates evil book on catalog `/catalog` [TestXss / catalog edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates catalog data or listing/sort is wrong."""
        evil = '<script>alert(1)</script>'
        row = (1, evil, evil, '', '', None, '', '', '', '', '', 'active',
               '2026-01-01', None, None)
        mock_db['fetch_all'].return_value = [row]
        mock_db['fetch_one'].return_value = (1,)
        body = client.get('/catalog').data.decode()
        assert evil not in body

    def test_evil_book_on_detail(self, client, mock_db):
        """Validates evil book on detail `/book/1` [TestXss / catalog edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates catalog data or listing/sort is wrong."""
        evil = '<img src=x onerror=alert(1)>'
        row = (1, evil, evil, '', '', None, '', '', '', '', '', 'active',
               '2026-01-01', None, None)
        mock_db['fetch_one'].return_value = row
        mock_db['fetch_all'].return_value = []
        body = client.get('/book/1').data.decode()
        assert evil not in body


class TestAuth:
    def test_anon_staff_blocked(self, client):
        """Validates anon staff blocked `/catalog` (expects 302) [TestAuth / catalog edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        for url in ('/librarian/cataloging', '/book/1'):
            if url.startswith('/librarian'):
                resp = client.get(url)
                assert resp.status_code == 302
                assert '/login' in resp.location
        assert client.get('/catalog').status_code == 200
        assert client.get('/book/1').status_code in (200, 302)

    def test_student_cannot_write(self, student_client, mock_db):
        """Validates student cannot write `/librarian/cataloging/add` as student (expects 302) [TestAuth / catalog edge cases].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        for url in ('/librarian/cataloging',
                    '/librarian/cataloging/export?format=csv'):
            resp = student_client.get(url)
            assert resp.status_code == 302, url
        resp = student_client.post('/librarian/cataloging/add',
                                   data={'title': 'X', 'author': 'Y'})
        assert resp.status_code == 302
        # The RBAC decorator logs security:denied to audit_trail, but no
        # catalog rows change.
        writes = [c[0][0] for c in mock_db['execute'].call_args_list
                  if 'INSERT' in c[0][0] and 'audit_trail' not in c[0][0]]
        assert writes == []


class TestYearFilterHardening:
    def test_garbage_years_ignored(self, client, mock_db):
        """Validates garbage years ignored `/catalog?year_from=abc&year_to=--` (expects 200) [TestYearFilterHardening / catalog edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_all'].return_value = []
        mock_db['fetch_one'].return_value = (0,)
        resp = client.get('/catalog?year_from=abc&year_to=--')
        assert resp.status_code == 200
        query = mock_db['fetch_all'].call_args[0][0]
        assert 'year_published' not in query

    def test_valid_years_applied(self, client, mock_db):
        """Validates valid years applied `/catalog?year_from=2000&year_to=2020` (expects 200) [TestYearFilterHardening / catalog edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_all'].return_value = []
        mock_db['fetch_one'].return_value = (0,)
        assert client.get('/catalog?year_from=2000&year_to=2020').status_code == 200
        calls = [c[0] for c in mock_db['fetch_all'].call_args_list if len(c[0]) > 1]
        query, params = next(c for c in calls if 'year_published >=' in c[0])
        assert 2000 in params and 2020 in params


class TestNoneGuards:
    def test_book_detail_none_accessions(self, client, mock_db):
        """Validates book detail none accessions `/book/1` (expects 200) [TestNoneGuards / catalog edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        book = (1, 'T', 'A', '', '', None, '', '', '', '', '', 'active',
                '2026-01-01', None, None)
        mock_db['fetch_one'].return_value = book
        mock_db['fetch_all'].return_value = None
        assert client.get('/book/1').status_code == 200

    def test_loan_helpers_tolerate_none(self, mock_db):
        """Validates loan helpers tolerate none [TestNoneGuards / catalog edge cases].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates catalog data or listing/sort is wrong."""
        from app.circulation.models import (
            get_active_loan_accession_ids_by_book,
            get_active_loan_borrower_user_ids_by_book,
        )
        mock_db['fetch_all'].return_value = None
        assert get_active_loan_accession_ids_by_book(1) == set()
        assert get_active_loan_borrower_user_ids_by_book(1) == {}

    def test_accession_helpers_tolerate_none(self, mock_db):
        """Validates accession helpers tolerate none [TestNoneGuards / catalog edge cases].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        from app.cataloging.models import (
            get_accessions_by_book, get_accessions_for_books)
        mock_db['fetch_all'].return_value = None
        assert get_accessions_by_book(1) == []
        assert get_accessions_for_books([1]) == []


def _book15(title='Educated'):
    # 15-col book_catalog row on current schema: updated_at[13] is a
    # timestamp, updated_by[14] is None (never edited, like seed data).
    return (1, title, 'T. Author', '1st', 'Pub', 2018, 'Auto', 'C1',
            '978-0', 'Book', 'Desc', 'active', '2026-01-01',
            '2026-05-05 10:00:00', None)


class TestAvailabilityIndices:
    def test_public_card_uses_trailing_availability_cols(self, client, mock_db):
        """Validates public card uses trailing availability cols `/catalog?category=Autobiography` [TestAvailabilityIndices / catalog edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_all'].side_effect = [[_book15() + ('available', 1)],
                                            [('Autobiography',)]]
        mock_db['fetch_one'].return_value = (0,)
        body = client.get('/catalog?category=Autobiography').data.decode()
        assert '1 copy available' in body
        assert 'No copies available' not in body

    def test_public_card_borrowed_state(self, client, mock_db):
        """Validates public card borrowed state `/catalog?category=Autobiography` [TestAvailabilityIndices / catalog edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_all'].side_effect = [[_book15() + ('borrowed', 0)],
                                            [('Autobiography',)]]
        mock_db['fetch_one'].return_value = (0,)
        body = client.get('/catalog?category=Autobiography').data.decode()
        assert 'No copies available' in body

    def test_staff_accession_column(self, librarian_client, mock_db):
        """Validates staff accession column `/librarian/cataloging` as librarian [TestAvailabilityIndices / catalog edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_all'].side_effect = [[_book15() + ('ACC-001',)],
                                            []]
        body = librarian_client.get('/librarian/cataloging').data.decode()
        # Accession cell shows the accession numbers, not updated_at.
        assert 'title="ACC-001"' in body
        assert 'title="2026-05-05 10:00:00"' not in body

    def test_export_accession_column(self, librarian_client, mock_db):
        """Validates export accession column `/librarian/cataloging/export?format=csv` as librarian (expects 200) [TestAvailabilityIndices / catalog edge cases].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_all'].return_value = [_book15() + ('ACC-001,ACC-002',)]
        resp = librarian_client.get('/librarian/cataloging/export?format=csv')
        assert resp.status_code == 200
        body = resp.data.decode()
        assert 'ACC-001' in body
        assert '2026-05-05' not in body


class TestBorrowerColumnOrder:
    def test_no_select_star(self, mock_db):
        """Validates no select star [TestBorrowerColumnOrder / catalog edge cases].
    If fails: likely model SQL changed (SELECT).
    Failure indicates catalog data or listing/sort is wrong."""
        from app.circulation.models import (
            get_borrower_by_user, get_borrower_by_id_number)
        mock_db['fetch_one'].return_value = None
        get_borrower_by_user(1)
        q = mock_db['fetch_one'].call_args[0][0]
        assert 'SELECT *' not in q
        assert q.index('phone_number') < q.index('borrower_status')
        get_borrower_by_id_number('S1')
        q = mock_db['fetch_one'].call_args[0][0]
        assert 'SELECT *' not in q

    def test_active_borrower_passes_gate(self, student_client, mock_db):
        """Validates active borrower passes gate `/user/borrow` as student (expects 302) [TestBorrowerColumnOrder / catalog edge cases].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        borrower = (5, 1, 'S1', 'BSIS', '0917', 'active', None, None)
        mock_db['fetch_one'].side_effect = [_book15(), borrower, None,
                                            None, (0,), (1,)]
        mock_db['fetch_all'].return_value = []
        resp = student_client.post('/user/borrow',
                                   data={'book_id': 1,
                                         'borrow_type': 'overnight'})
        assert resp.status_code == 302
        stmts = [c[0][0] for c in mock_db['execute'].call_args_list]
        assert any('reservation_queue' in s for s in stmts)
