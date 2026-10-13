import pytest


def _mock_fetch_all_by_query(mock_db):
    def side_effect(query, params=None):
        if 'SELECT DISTINCT title, author' in query:
            return [('The Great Gatsby', 'F. Scott Fitzgerald')]
        if 'UNION SELECT author' in query:
            return [('The Great Gatsby',), ('F. Scott Fitzgerald',), ('Literature',)]
        if 'WHERE title ILIKE' in query:
            return [('The Great Gatsby',), ('The Catcher in the Rye',)]
        if 'WHERE author ILIKE' in query:
            return [('F. Scott Fitzgerald',), ('Harper Lee',)]
        if 'department ILIKE' in query:
            return [('BSIT',), ('BSBA',)]
        return []
    mock_db['fetch_all'].side_effect = side_effect


class TestSuggestions:
    def test_book_title_suggestions(self, client, mock_db):
        """Validates book title suggestions `/api/suggestions?field=book_title&q=the` (expects 200) [TestSuggestions / autosuggest].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates autosuggest is broken for this case (users see wrong page, blocked action, or bad data)."""
        _mock_fetch_all_by_query(mock_db)
        resp = client.get('/api/suggestions?field=book_title&q=the')
        assert resp.status_code == 200
        assert resp.get_json()['suggestions'] == ['The Great Gatsby', 'The Catcher in the Rye']

    def test_book_author_suggestions(self, client, mock_db):
        """Validates book author suggestions `/api/suggestions?field=book_author&q=f.` [TestSuggestions / autosuggest].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates autosuggest is broken for this case (users see wrong page, blocked action, or bad data)."""
        _mock_fetch_all_by_query(mock_db)
        resp = client.get('/api/suggestions?field=book_author&q=f.')
        assert resp.get_json()['suggestions'] == ['F. Scott Fitzgerald', 'Harper Lee']

    def test_student_program_suggestions(self, client, mock_db):
        """Validates student program suggestions `/api/suggestions?field=student_program&q=bs` [TestSuggestions / autosuggest].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates autosuggest is broken for this case (users see wrong page, blocked action, or bad data)."""
        _mock_fetch_all_by_query(mock_db)
        resp = client.get('/api/suggestions?field=student_program&q=bs')
        assert resp.get_json()['suggestions'] == ['BSIT', 'BSBA']

    def test_short_query_returns_empty_without_query(self, client, mock_db):
        """Validates short query returns empty without query `/api/suggestions?field=book_title&q=a` [TestSuggestions / autosuggest].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates autosuggest is broken for this case (users see wrong page, blocked action, or bad data)."""
        resp = client.get('/api/suggestions?field=book_title&q=a')
        assert resp.get_json() == {'suggestions': []}
        mock_db['fetch_all'].assert_not_called()

    def test_unknown_field_returns_empty(self, client, mock_db):
        """Validates unknown field returns empty `/api/suggestions?field=book_foo&q=abc` [TestSuggestions / autosuggest].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates autosuggest is broken for this case (users see wrong page, blocked action, or bad data)."""
        resp = client.get('/api/suggestions?field=book_foo&q=abc')
        assert resp.get_json() == {'suggestions': []}

    def test_book_search_suggestions(self, client, mock_db):
        """Validates book search suggestions `/api/suggestions?field=book_search&q=the` [TestSuggestions / autosuggest].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates autosuggest is broken for this case (users see wrong page, blocked action, or bad data)."""
        _mock_fetch_all_by_query(mock_db)
        resp = client.get('/api/suggestions?field=book_search&q=the')
        body = resp.get_json()
        assert body['suggestions'] == ['The Great Gatsby', 'F. Scott Fitzgerald', 'Literature']
        assert body['rich'] == [{'title': 'The Great Gatsby', 'author': 'F. Scott Fitzgerald'}]

    def test_book_search_rich_empty_when_no_pairs(self, client, mock_db):
        """Validates book search rich empty when no pairs `/api/suggestions?field=book_search&q=the` [TestSuggestions / autosuggest].
    If fails: likely template text/context changed or mock fetch_* shape mismatched; model SQL changed (SELECT).
    Failure indicates autosuggest is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_all'].side_effect = lambda q, p=None: (
            [('Plain Title',)] if 'UNION SELECT author' in q else []
        )
        resp = client.get('/api/suggestions?field=book_search&q=the')
        body = resp.get_json()
        assert body['suggestions'] == ['Plain Title']
        assert body['rich'] == []

    def test_non_search_fields_have_no_rich_key(self, client, mock_db):
        """Validates non search fields have no rich key `/api/suggestions?field=book_title&q=the` [TestSuggestions / autosuggest].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates autosuggest is broken for this case (users see wrong page, blocked action, or bad data)."""
        _mock_fetch_all_by_query(mock_db)
        resp = client.get('/api/suggestions?field=book_title&q=the')
        assert resp.get_json() == {'suggestions': ['The Great Gatsby', 'The Catcher in the Rye']}

    def test_empty_db_returns_empty(self, client, mock_db):
        """Validates empty db returns empty `/api/suggestions?field=book_isbn&q=978` [TestSuggestions / autosuggest].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates autosuggest is broken for this case (users see wrong page, blocked action, or bad data)."""
        resp = client.get('/api/suggestions?field=book_isbn&q=978')
        assert resp.get_json() == {'suggestions': []}

    def test_autosuggest_js_served(self, client):
        """Validates autosuggest js served `/static/js/autosuggest.js` (expects 200) [TestSuggestions / autosuggest].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates autosuggest is broken for this case (users see wrong page, blocked action, or bad data)."""
        resp = client.get('/static/js/autosuggest.js')
        assert resp.status_code == 200

    def test_autosuggest_js_matches_analytics_style(self, client):
        """Validates autosuggest js matches analytics style `/static/js/autosuggest.js` [TestSuggestions / autosuggest].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates autosuggest is broken for this case (users see wrong page, blocked action, or bad data)."""
        body = client.get('/static/js/autosuggest.js').data.decode()
        assert 'rounded-xl shadow-xl' in body
        assert 'hover:bg-blue-50/60' in body
        assert 'font-bold' in body and 'truncate' in body

    def test_home_search_has_suggest(self, client, mock_db):
        """Validates home search has suggest `/` [TestSuggestions / autosuggest].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates autosuggest is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        body = client.get('/').data.decode()
        assert 'data-suggest="book_search"' in body
        assert 'js/autosuggest.js' in body


class TestBookExists:
    def test_book_exists_true(self, client, mock_db):
        """Validates book exists true `/api/book-exists?title=The%20Great%20Gatsby&author=F.%20Scott%20Fitzgerald&isbn=9780743273565` [TestBookExists / autosuggest].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates autosuggest is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].return_value = (42,)
        resp = client.get('/api/book-exists?title=The%20Great%20Gatsby&author=F.%20Scott%20Fitzgerald&isbn=9780743273565')
        assert resp.get_json() == {'exists': True}

    def test_book_exists_false(self, client, mock_db):
        """Validates book exists false `/api/book-exists?title=New%20Book&author=New%20Author` [TestBookExists / autosuggest].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates autosuggest is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].return_value = None
        resp = client.get('/api/book-exists?title=New%20Book&author=New%20Author')
        assert resp.get_json() == {'exists': False}

    def test_book_exists_requires_title_and_author(self, client, mock_db):
        """Validates book exists requires title and author `/api/book-exists?title=Only%20Title` [TestBookExists / autosuggest].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates autosuggest is broken for this case (users see wrong page, blocked action, or bad data)."""
        resp = client.get('/api/book-exists?title=Only%20Title')
        assert resp.get_json() == {'exists': False}
        mock_db['fetch_one'].assert_not_called()

    def test_book_exists_blank_isbn_uses_null_match(self, client, mock_db):
        """Validates book exists blank isbn uses null match `/api/book-exists?title=T&author=A` [TestBookExists / autosuggest].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates autosuggest is broken for this case (users see wrong page, blocked action, or bad data)."""
        client.get('/api/book-exists?title=T&author=A')
        assert 'isbn IS NULL' in mock_db['fetch_one'].call_args[0][0]

    def test_book_exists_isbn_present_uses_isbn_match(self, client, mock_db):
        """Validates book exists isbn present uses isbn match `/api/book-exists?title=T&author=A&isbn=978` [TestBookExists / autosuggest].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates autosuggest is broken for this case (users see wrong page, blocked action, or bad data)."""
        client.get('/api/book-exists?title=T&author=A&isbn=978')
        assert 'isbn = %s' in mock_db['fetch_one'].call_args[0][0]


class TestStudentExists:
    def test_student_exists_true(self, client, mock_db):
        """Validates student exists true `/api/student-exists?id_number=2024-8192` [TestStudentExists / autosuggest].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates autosuggest is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].return_value = (1, 'x@mcst.edu.ph', 'Student', 'X')
        resp = client.get('/api/student-exists?id_number=2024-8192')
        assert resp.get_json() == {'exists': True}

    def test_student_exists_false(self, client, mock_db):
        """Validates student exists false `/api/student-exists?id_number=2024-9999` [TestStudentExists / autosuggest].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates autosuggest is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].return_value = None
        resp = client.get('/api/student-exists?id_number=2024-9999')
        assert resp.get_json() == {'exists': False}

    def test_student_exists_requires_id(self, client, mock_db):
        """Validates student exists requires id `/api/student-exists?id_number=` [TestStudentExists / autosuggest].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates autosuggest is broken for this case (users see wrong page, blocked action, or bad data)."""
        resp = client.get('/api/student-exists?id_number=')
        assert resp.get_json() == {'exists': False}
        mock_db['fetch_one'].assert_not_called()


class TestCatalogEditModal:
    def test_edit_fields_have_suggest(self, librarian_client, mock_db):
        """Validates edit fields have suggest `/librarian/cataloging` as librarian [TestCatalogEditModal / autosuggest].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/cataloging').data.decode()
        for field in ('book_title', 'book_author', 'book_publisher',
                      'book_isbn', 'book_subject'):
            assert f'data-suggest="{field}"' in body, field
        assert 'js/autosuggest.js' in body


class TestRequestsSearch:
    def test_librarian_search_has_suggest(self, librarian_client, mock_db):
        """Validates librarian search has suggest `/librarian/requests` as librarian [TestRequestsSearch / autosuggest].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates autosuggest is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/requests').data.decode()
        assert 'data-suggest="book_search"' in body
        assert 'js/autosuggest.js' in body

    def test_user_request_fields_have_suggest(self, student_client, mock_db):
        """Validates user request fields have suggest `/user/request-book` as student [TestRequestsSearch / autosuggest].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates autosuggest is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].return_value = []
        body = student_client.get('/user/request-book').data.decode()
        assert 'data-suggest="book_title"' in body
        assert 'data-suggest="book_author"' in body
        assert 'js/autosuggest.js' in body


class TestCirculationSearch:
    def test_loan_search_has_suggest(self, librarian_client, mock_db):
        """Validates loan search has suggest `/librarian/circulation` as librarian [TestCirculationSearch / autosuggest].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates autosuggest is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/circulation').data.decode()
        assert 'data-suggest="book_search"' in body
        assert 'js/autosuggest.js' in body


class TestSuggestionsApi:
    def test_returns_matches(self, client, mock_db):
        """Validates returns matches `/api/suggestions?field=book_title&q=clean` (expects 200) [TestSuggestionsApi / autosuggest].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates autosuggest is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_all'].return_value = [('Clean Code',)]
        resp = client.get('/api/suggestions?field=book_title&q=clean')
        assert resp.status_code == 200
        assert resp.get_json() == {'suggestions': ['Clean Code']}

    def test_rejects_short_and_unknown(self, client, mock_db):
        """Validates rejects short and unknown (expects 200) [TestSuggestionsApi / autosuggest].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates autosuggest is broken for this case (users see wrong page, blocked action, or bad data)."""
        for url in ('/api/suggestions?field=book_title&q=x',
                    '/api/suggestions?field=drop_table&q=clean',
                    '/api/suggestions'):
            resp = client.get(url)
            assert resp.status_code == 200
            assert resp.get_json() == {'suggestions': []}, url

    def test_xss_neutralized_client_side(self, client, mock_db):
        # Server returns raw strings; the shared component HTML-escapes
        # before injecting (escHtml). Assert transport shape only.
        """Validates xss neutralized client side `/api/suggestions?field=book_title&q=script` (expects 200) [TestSuggestionsApi / autosuggest].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates autosuggest is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_all'].return_value = [('<script>alert(1)</script>',)]
        resp = client.get('/api/suggestions?field=book_title&q=script')
        assert resp.status_code == 200
        assert resp.get_json()['suggestions'] == ['<script>alert(1)</script>']


class TestBookAnalyticsIntact:
    def test_picker_markup_and_logic_present(self, librarian_client, mock_db):
        """Validates picker markup and logic present `/librarian/analytics` as librarian [TestBookAnalyticsIntact / autosuggest].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates autosuggest is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/analytics').data.decode()
        assert 'id="book-search"' in body
        assert 'id="book-suggest"' in body
        assert 'BOOK_SEARCH_URL' in body
        assert 'book_id' in body

    def test_search_endpoint_works(self, librarian_client, mock_db):
        """Validates search endpoint works `/librarian/analytics/book/search?q=clean` as librarian (expects 200) [TestBookAnalyticsIntact / autosuggest].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates autosuggest is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_all'].return_value = [
            (1, 'Clean Code', 'R. Martin', 'SE', 2008)]
        resp = librarian_client.get('/librarian/analytics/book/search?q=clean')
        assert resp.status_code == 200
        results = resp.get_json()['results']
        assert results[0]['title'] == 'Clean Code'

    def test_intentionally_unchanged_pages(self, librarian_client, mock_db):
        """Validates intentionally unchanged pages `/librarian/inventory` as librarian [TestBookAnalyticsIntact / autosuggest].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates autosuggest is broken for this case (users see wrong page, blocked action, or bad data).

Pages with no suggestible backend field stay as-is."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/inventory').data.decode()
        assert 'data-suggest' not in body
