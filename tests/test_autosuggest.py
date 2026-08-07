import pytest


def _mock_fetch_all_by_query(mock_db):
    def side_effect(query, params=None):
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
        _mock_fetch_all_by_query(mock_db)
        resp = client.get('/api/suggestions?field=book_title&q=the')
        assert resp.status_code == 200
        assert resp.get_json()['suggestions'] == ['The Great Gatsby', 'The Catcher in the Rye']

    def test_book_author_suggestions(self, client, mock_db):
        _mock_fetch_all_by_query(mock_db)
        resp = client.get('/api/suggestions?field=book_author&q=f.')
        assert resp.get_json()['suggestions'] == ['F. Scott Fitzgerald', 'Harper Lee']

    def test_student_program_suggestions(self, client, mock_db):
        _mock_fetch_all_by_query(mock_db)
        resp = client.get('/api/suggestions?field=student_program&q=bs')
        assert resp.get_json()['suggestions'] == ['BSIT', 'BSBA']

    def test_short_query_returns_empty_without_query(self, client, mock_db):
        resp = client.get('/api/suggestions?field=book_title&q=a')
        assert resp.get_json() == {'suggestions': []}
        mock_db['fetch_all'].assert_not_called()

    def test_unknown_field_returns_empty(self, client, mock_db):
        resp = client.get('/api/suggestions?field=book_foo&q=abc')
        assert resp.get_json() == {'suggestions': []}

    def test_book_search_suggestions(self, client, mock_db):
        _mock_fetch_all_by_query(mock_db)
        resp = client.get('/api/suggestions?field=book_search&q=the')
        assert resp.get_json()['suggestions'] == ['The Great Gatsby', 'F. Scott Fitzgerald', 'Literature']

    def test_empty_db_returns_empty(self, client, mock_db):
        resp = client.get('/api/suggestions?field=book_isbn&q=978')
        assert resp.get_json() == {'suggestions': []}

    def test_autosuggest_js_served(self, client):
        resp = client.get('/static/js/autosuggest.js')
        assert resp.status_code == 200


class TestBookExists:
    def test_book_exists_true(self, client, mock_db):
        mock_db['fetch_one'].return_value = (42,)
        resp = client.get('/api/book-exists?title=The%20Great%20Gatsby&author=F.%20Scott%20Fitzgerald&isbn=9780743273565')
        assert resp.get_json() == {'exists': True}

    def test_book_exists_false(self, client, mock_db):
        mock_db['fetch_one'].return_value = None
        resp = client.get('/api/book-exists?title=New%20Book&author=New%20Author')
        assert resp.get_json() == {'exists': False}

    def test_book_exists_requires_title_and_author(self, client, mock_db):
        resp = client.get('/api/book-exists?title=Only%20Title')
        assert resp.get_json() == {'exists': False}
        mock_db['fetch_one'].assert_not_called()

    def test_book_exists_blank_isbn_uses_null_match(self, client, mock_db):
        client.get('/api/book-exists?title=T&author=A')
        assert 'isbn IS NULL' in mock_db['fetch_one'].call_args[0][0]

    def test_book_exists_isbn_present_uses_isbn_match(self, client, mock_db):
        client.get('/api/book-exists?title=T&author=A&isbn=978')
        assert 'isbn = %s' in mock_db['fetch_one'].call_args[0][0]


class TestStudentExists:
    def test_student_exists_true(self, client, mock_db):
        mock_db['fetch_one'].return_value = (1, 'x@mcst.edu.ph', 'Student', 'X')
        resp = client.get('/api/student-exists?id_number=2024-8192')
        assert resp.get_json() == {'exists': True}

    def test_student_exists_false(self, client, mock_db):
        mock_db['fetch_one'].return_value = None
        resp = client.get('/api/student-exists?id_number=2024-9999')
        assert resp.get_json() == {'exists': False}

    def test_student_exists_requires_id(self, client, mock_db):
        resp = client.get('/api/student-exists?id_number=')
        assert resp.get_json() == {'exists': False}
        mock_db['fetch_one'].assert_not_called()
