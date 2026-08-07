"""Tests for the Requests module: submission, review, RBAC."""

from app.requests.models import normalize_title, check_duplicate_request, check_existing_in_collection


class TestTitleNormalization:
    def test_normalize_lowercases(self):
        assert normalize_title('HARRY POTTER') == 'harry potter'

    def test_normalize_strips_punctuation(self):
        assert normalize_title("David Jone's Locker!") == 'david jones locker'

    def test_normalize_expands_abbreviations(self):
        assert normalize_title('Intro to Comp Sci') == 'introduction to computer science'

    def test_normalize_collapses_whitespace(self):
        assert normalize_title('Harry   Potter') == 'harry potter'


class TestCheckDuplicateRequest:
    def test_exact_normalized_duplicate_blocked(self, mock_db):
        mock_db['fetch_all'].return_value = [('1984',)]
        assert check_duplicate_request(5, '1984') is True

    def test_fuzzy_duplicate_blocked(self, mock_db):
        mock_db['fetch_all'].return_value = [('Introduction to Programming',)]
        assert check_duplicate_request(5, 'Intro to Programming') is True

    def test_distinct_titles_allowed(self, mock_db):
        mock_db['fetch_all'].return_value = [('Introduction to Biology',)]
        assert check_duplicate_request(5, 'Introduction to Programming') is False

    def test_no_prior_requests_allowed(self, mock_db):
        mock_db['fetch_all'].return_value = []
        assert check_duplicate_request(5, 'Anything') is False


class TestCheckExistingInCollection:
    def test_exact_match_returns_book_id(self, mock_db):
        mock_db['fetch_one'].return_value = (42,)
        result = check_existing_in_collection('1984')
        assert result == 42

    def test_fuzzy_fallback_returns_book_id(self, mock_db):
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = [(7, 'Introduction to Programming')]
        result = check_existing_in_collection('Intro to Programming')
        assert result == 7

    def test_no_match_returns_none(self, mock_db):
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        result = check_existing_in_collection('Some Totally New Book')
        assert result is None

class TestRequestSubmission:
    def test_student_submits_request_success(self, student_client, mock_db):
        mock_db['fetch_one'].side_effect = [
            (5,),   # 1st call: get_borrower_by_user -> borrower_id
            None,   # 2nd call: check_duplicate_request -> no duplicate found
            None,   # 3rd call: check_existing_in_collection -> no catalog match
        ]
        mock_db['execute'].return_value = [(7,)]

        resp = student_client.post('/user/request-book', data={
            'book-title': 'Introduction to Algorithms',
            'author': 'Cormen',
        })

        assert resp.status_code == 302
        assert '/user/request-book' in resp.location

        call_args = mock_db['execute'].call_args_list[0]
        assert 'INSERT INTO request_records' in call_args[0][0]

    def test_submit_blank_title_rejected(self, student_client, mock_db):
        mock_db['fetch_one'].return_value = (5,)

        resp = student_client.post('/user/request-book', data={
            'book-title': '',
            'author': '',
        })

        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_unauthenticated_redirects_to_login(self, client):
        resp = client.get('/user/request-book')
        assert resp.status_code == 302
        assert '/login' in resp.location


class TestLibrarianReview:
    def test_librarian_approves_request(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (7, 1, 'Some Book', None, None, 'pending_review', None, None, None, None)

        resp = librarian_client.post('/librarian/requests/7/approve')

        assert resp.status_code == 302
        assert '/librarian/requests' in resp.location
        assert mock_db['execute'].call_count >= 2

        call_args = mock_db['execute'].call_args_list[0]
        assert 'UPDATE request_records' in call_args[0][0]

    def test_librarian_rejects_request_with_remarks(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (7, 1, 'Some Book', None, None, 'pending_review', None, None, None, None)

        resp = librarian_client.post('/librarian/requests/7/reject', data={
            'remarks': 'Not relevant to curriculum',
        })

        assert resp.status_code == 302
        call_args = mock_db['execute'].call_args_list[0]
        assert 'UPDATE request_records' in call_args[0][0]
        assert 'Not relevant to curriculum' in call_args[0][1]

    def test_student_forbidden_from_librarian_requests(self, student_client):
        resp = student_client.get('/librarian/requests')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_invalid_action_rejected(self, librarian_client, mock_db):
        resp = librarian_client.post('/librarian/requests/7/nonsense')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_cannot_approve_already_reviewed_request(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (7, 1, 'Some Book', None, None, 'approved', None, None, None, None)

        resp = librarian_client.post('/librarian/requests/7/approve')

        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_request_not_found_returns_error(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = None

        resp = librarian_client.post('/librarian/requests/999/approve')

        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0