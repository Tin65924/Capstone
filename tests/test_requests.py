"""Tests for the Requests module: submission, review, RBAC."""


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
        resp = librarian_client.post('/librarian/requests/7/approve')

        assert resp.status_code == 302
        assert '/librarian/requests' in resp.location
        assert mock_db['execute'].call_count >= 2

        call_args = mock_db['execute'].call_args_list[0]
        assert 'UPDATE request_records' in call_args[0][0]

    def test_librarian_rejects_request_with_remarks(self, librarian_client, mock_db):
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