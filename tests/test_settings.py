"""Tests for the Library Settings module: RBAC, page render, update validation."""


class TestSettingsAccess:
    def test_settings_unauthenticated_redirects(self, client):
        resp = client.get('/librarian/settings')
        assert resp.status_code == 302
        assert '/login' in resp.location

    def test_settings_student_forbidden(self, student_client):
        resp = student_client.get('/librarian/settings')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_settings_faculty_forbidden(self, faculty_client):
        resp = faculty_client.get('/librarian/settings')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_settings_librarian_allowed(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/settings')
        assert resp.status_code == 200
        assert b'Library Settings' in resp.data
        assert b'MAX_BORROW_LIMIT_STUDENT' in resp.data

    def test_settings_admin_allowed(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = admin_client.get('/librarian/settings')
        assert resp.status_code == 200
        assert b'Library Settings' in resp.data


class TestUpdateSettings:
    def test_update_valid_int(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.post('/librarian/settings/update', data={
            'MAX_BORROW_LIMIT_STUDENT': '4',
        })
        assert resp.status_code == 302
        assert '/librarian/settings' in resp.location
        first = mock_db['execute'].call_args_list[0]
        assert 'INSERT INTO library_settings' in first[0][0]
        assert first[0][1][0] == 'MAX_BORROW_LIMIT_STUDENT'
        assert first[0][1][1] == '4'

    def test_update_rejects_decimal_int(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.post('/librarian/settings/update', data={
            'MAX_BORROW_LIMIT_STUDENT': '2.5',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_update_rejects_zero_limit(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.post('/librarian/settings/update', data={
            'MAX_BORROW_LIMIT_STUDENT': '0',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_update_rejects_negative(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.post('/librarian/settings/update', data={
            'OVERDUE_FINE_PER_DAY': '-5',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_update_accepts_float_fine(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.post('/librarian/settings/update', data={
            'OVERDUE_FINE_PER_DAY': '15.50',
        })
        assert resp.status_code == 302
        first = mock_db['execute'].call_args_list[0]
        assert 'INSERT INTO library_settings' in first[0][0]
        assert first[0][1][0] == 'OVERDUE_FINE_PER_DAY'
        assert first[0][1][1] == '15.5'

    def test_update_student_forbidden(self, student_client, mock_db):
        resp = student_client.post('/librarian/settings/update', data={
            'MAX_BORROW_LIMIT_STUDENT': '9',
        })
        assert resp.status_code == 302
        assert '/user/profile' in resp.location
        assert mock_db['execute'].call_count == 0


class TestFlashDismiss:
    def test_flash_renders_dismiss_markup(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.post('/librarian/settings/update', data={
            'MAX_BORROW_LIMIT_STUDENT': '4',
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'data-flash' in resp.data
        assert b'data-flash-close' in resp.data
