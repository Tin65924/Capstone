"""Sorting on the staff cataloging page: title A-Z/Z-A, accession
up/down, newest first. Mocked DB — no Postgres.
"""

from app.cataloging import models as cat


def _last_query(mock_db):
    """Test helper _last_query: build mocked data or DB stub for the test."""
    return mock_db['fetch_all'].call_args[0][0]


class TestSortClauses:
    def test_allowlist(self):
        """Validates allowlist [TestSortClauses / catalog sort].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates catalog data or listing/sort is wrong."""
        assert cat._catalog_sort_clause('title_desc').startswith('title DESC')
        assert cat._catalog_sort_clause('accession_asc') == 'accession_numbers ASC'
        assert cat._catalog_sort_clause('accession_desc') == 'accession_numbers DESC'
        assert cat._catalog_sort_clause('newest').startswith('date_added DESC')

    def test_invalid_and_empty_fall_back(self):
        """Validates invalid and empty fall back [TestSortClauses / catalog sort].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates catalog data or listing/sort is wrong."""
        for bad in (None, '', 'drop_table', 'title; DROP', 'TITLE_DESC'):
            assert cat._catalog_sort_clause(bad) is None


class TestAllBooksSort:
    def test_default_unchanged(self, mock_db):
        """Validates default unchanged [TestAllBooksSort / catalog sort].
    If fails: likely model SQL changed (SELECT).
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = (0,)
        cat.get_all_books_paginated(1, 20)
        query = _last_query(mock_db)
        assert 'SELECT DISTINCT ON' in query
        assert 'SELECT * FROM (SELECT DISTINCT ON' not in query

    def test_each_sort_wraps(self, mock_db):
        """Validates each sort wraps [TestAllBooksSort / catalog sort].
    If fails: likely model SQL changed (SELECT).
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = (0,)
        for sort, frag in (('title_desc', 'title DESC'),
                           ('accession_asc', 'accession_numbers ASC'),
                           ('accession_desc', 'accession_numbers DESC'),
                           ('newest', 'date_added DESC')):
            cat.get_all_books_paginated(1, 20, sort)
            query = _last_query(mock_db)
            assert 'SELECT * FROM (SELECT DISTINCT ON' in query, sort
            assert frag in query, sort

    def test_bogus_sort_behaves_like_default(self, mock_db):
        """Validates bogus sort behaves like default [TestAllBooksSort / catalog sort].
    If fails: likely model SQL changed (SELECT).
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = (0,)
        cat.get_all_books_paginated(1, 20, 'drop_table')
        assert 'SELECT * FROM (SELECT DISTINCT ON' not in _last_query(mock_db)


class TestOtherListingsSort:
    def test_status_uses_direct_order(self, mock_db):
        """Validates status uses direct order [TestOtherListingsSort / catalog sort].
    If fails: likely model SQL changed (SELECT).
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = (0,)
        cat.get_books_by_status_paginated('active', 1, 20, 'newest')
        query = _last_query(mock_db)
        assert 'ORDER BY date_added DESC' in query
        assert 'SELECT * FROM (SELECT' not in query

    def test_status_default_unchanged(self, mock_db):
        """Validates status default unchanged [TestOtherListingsSort / catalog sort].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = (0,)
        cat.get_books_by_status_paginated('active', 1, 20)
        assert 'ORDER BY title LIMIT' in _last_query(mock_db)

    def test_copy_status_wraps(self, mock_db):
        """Validates copy status wraps [TestOtherListingsSort / catalog sort].
    If fails: likely model SQL changed (SELECT).
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = (0,)
        cat.get_books_by_copy_status_paginated('lost', 1, 20, 'title_desc')
        query = _last_query(mock_db)
        assert 'SELECT * FROM (SELECT DISTINCT ON' in query
        assert 'title DESC' in query

    def test_copy_status_default_unchanged(self, mock_db):
        """Validates copy status default unchanged [TestOtherListingsSort / catalog sort].
    If fails: likely model SQL changed (SELECT).
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = (0,)
        cat.get_books_by_copy_status_paginated('lost', 1, 20)
        assert 'SELECT * FROM (SELECT DISTINCT ON' not in _last_query(mock_db)

    def test_search_wraps(self, mock_db):
        """Validates search wraps [TestOtherListingsSort / catalog sort].
    If fails: likely model SQL changed (SELECT).
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = (0,)
        cat.search_books_paginated('x', '', 1, 20, 'accession_desc')
        query = _last_query(mock_db)
        assert 'SELECT * FROM (SELECT DISTINCT ON' in query
        assert 'accession_numbers DESC' in query

    def test_search_default_unchanged(self, mock_db):
        """Validates search default unchanged [TestOtherListingsSort / catalog sort].
    If fails: likely model SQL changed (SELECT).
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = (0,)
        cat.search_books_paginated('x', '', 1, 20)
        assert 'SELECT * FROM (SELECT DISTINCT ON' not in _last_query(mock_db)


class TestSortRoute:
    @staticmethod
    def _page(client, mock_db, query=''):
        """Test helper _page: build mocked data or DB stub for the test."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        return client.get('/librarian/cataloging' + query)

    def test_each_sort_renders(self, librarian_client, mock_db):
        """Validates each sort renders as librarian (expects 200) [TestSortRoute / catalog sort].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates catalog data or listing/sort is wrong."""
        for sort in ('title_desc', 'accession_asc', 'accession_desc',
                     'newest'):
            resp = self._page(librarian_client, mock_db,
                              f'?sort_by={sort}')
            assert resp.status_code == 200, sort
            assert f'value="{sort}"'.encode() in resp.data, sort

    def test_bogus_sort_falls_back(self, librarian_client, mock_db):
        """Validates bogus sort falls back as librarian (expects 200) [TestSortRoute / catalog sort].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        resp = self._page(librarian_client, mock_db,
                          '?sort_by=drop_table&q=x')
        assert resp.status_code == 200

    def test_sort_control_present(self, librarian_client, mock_db):
        """Validates sort control present as librarian [TestSortRoute / catalog sort].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates catalog data or listing/sort is wrong."""
        body = self._page(librarian_client, mock_db).data.decode()
        assert 'name="sort_by"' in body
        for label in ('Title A–Z', 'Title Z–A', 'Accession',
                      'Newest first'):
            assert label in body, label

    def test_pager_and_tabs_keep_sort(self, librarian_client, mock_db):
        """Validates pager and tabs keep sort as librarian [TestSortRoute / catalog sort].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates catalog data or listing/sort is wrong."""
        body = self._page(
            librarian_client, mock_db, '?sort_by=newest&page=2').data.decode()
        assert 'sort_by=newest' in body
