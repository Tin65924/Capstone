"""Tests for authentication: login, OAuth, role selection, user management."""

from unittest.mock import patch, MagicMock
from datetime import datetime


class TestLoginPage:
    def test_login_page_renders(self, client):
        resp = client.get('/login')
        assert resp.status_code == 200
        assert b'MCST' in resp.data or b'Login' in resp.data or b'login' in resp.data


class TestGoogleLogin:
    def test_google_login_redirects(self, client, mock_oauth_flow):
        mock_oauth_flow.authorization_url.return_value = ('https://accounts.google.com/o/oauth2/auth?state=xyz', 'xyz')
        resp = client.get('/login/google')
        assert resp.status_code == 302
        assert resp.location.startswith('https://accounts.google.com/')
        with client.session_transaction() as sess:
            assert '_oauth_state' in sess

    def test_google_login_handles_exception(self, client):
        from unittest.mock import patch
        with patch('app.auth.routes._build_flow', side_effect=Exception('mock error')):
            resp = client.get('/login/google')
            assert resp.status_code == 302
            assert resp.location.endswith('/login')


class TestGoogleCallback:
    def test_callback_missing_state(self, client):
        resp = client.get('/login/google/callback')
        assert resp.status_code == 302
        assert resp.location.endswith('/login')

    def test_callback_valid_user_logs_in(self, client, mock_oauth_flow):
        with client.session_transaction() as sess:
            sess['_oauth_state'] = 'test-state'

        mock_oauth_flow.fetch_token.return_value = None
        mock_oauth_flow.credentials.id_token = 'fake-id-token'

        with client.application.test_request_context():
            with client.application.app_context():
                pass

        with client.session_transaction() as sess:
            sess['_oauth_state'] = 'test-state'

        import app.auth.routes as auth_routes
        with patch.object(auth_routes, 'id_token') as mock_id_token:
            mock_id_token.verify_oauth2_token.return_value = {
                'iss': 'accounts.google.com',
                'email': 'user@mcst.edu.ph',
                'sub': 'google-sub-123',
                'name': 'Test User',
            }

            with patch('app.auth.routes.get_user_by_oauth_sub') as mock_get:
                mock_get.return_value = ('1', 'user@mcst.edu.ph', 'Student', 'Test User')

                with patch('app.auth.routes.login_user') as mock_login:
                    resp = client.get('/login/google/callback', query_string={'state': 'test-state', 'code': 'auth-code'})

                    assert resp.status_code == 302
                    assert mock_login.called

    def test_callback_blocked_domain(self, client):
        with client.session_transaction() as sess:
            sess['_oauth_state'] = 'test-state'

        mock_flow = MagicMock()
        mock_flow.fetch_token.return_value = None
        mock_flow.credentials.id_token = 'fake-id-token'

        with patch('app.auth.routes._build_flow', return_value=mock_flow):
            import app.auth.routes as auth_routes
            with patch.object(auth_routes, 'id_token') as mock_id_token:
                mock_id_token.verify_oauth2_token.return_value = {
                    'iss': 'accounts.google.com',
                    'email': 'user@gmail.com',
                    'sub': 'google-sub-123',
                    'name': 'Test User',
                }
                resp = client.get('/login/google/callback', query_string={'state': 'test-state', 'code': 'auth-code'})
                assert resp.status_code == 302
                assert resp.location.endswith('/login')

    def test_first_user_becomes_admin(self, client):
        with client.session_transaction() as sess:
            sess['_oauth_state'] = 'test-state'

        mock_flow = MagicMock()
        mock_flow.fetch_token.return_value = None
        mock_flow.credentials.id_token = 'fake-id-token'

        with patch('app.auth.routes._build_flow', return_value=mock_flow):
            import app.auth.routes as auth_routes
            with patch.object(auth_routes, 'id_token') as mock_id_token:
                mock_id_token.verify_oauth2_token.return_value = {
                    'iss': 'accounts.google.com',
                    'email': 'first@mcst.edu.ph',
                    'sub': 'google-admin-sub',
                    'name': 'First Admin',
                }

                with patch('app.auth.routes.get_admin_count', return_value=0):
                    with patch('app.auth.routes.get_role_by_name', return_value=(4, 'Admin')):
                        with patch('app.auth.routes.create_user') as mock_create:
                            with patch('app.auth.routes.create_borrower'):
                                mock_create.return_value = 1
                                resp = client.get('/login/google/callback', query_string={'state': 'test-state', 'code': 'auth-code'})
                                assert resp.status_code == 302
                                assert 'dashboard' in resp.location

    def test_second_user_goes_to_role_select(self, client):
        with client.session_transaction() as sess:
            sess['_oauth_state'] = 'test-state'

        mock_flow = MagicMock()
        mock_flow.fetch_token.return_value = None
        mock_flow.credentials.id_token = 'fake-id-token'

        with patch('app.auth.routes._build_flow', return_value=mock_flow):
            import app.auth.routes as auth_routes
            with patch.object(auth_routes, 'id_token') as mock_id_token:
                mock_id_token.verify_oauth2_token.return_value = {
                    'iss': 'accounts.google.com',
                    'email': 'second@mcst.edu.ph',
                    'sub': 'google-sub-456',
                    'name': 'Second User',
                }

                with patch('app.auth.routes.get_admin_count', return_value=1):
                    resp = client.get('/login/google/callback', query_string={'state': 'test-state', 'code': 'auth-code'})
                    assert resp.status_code == 302
                    assert 'role-select' in resp.location


class TestRoleSelect:
    def test_role_select_no_session_redirects(self, client):
        resp = client.get('/login/role-select')
        assert resp.status_code == 302
        assert resp.location.endswith('/login')

    def test_role_select_renders(self, client):
        with client.session_transaction() as sess:
            sess['_google_oauth_data'] = {
                'email': 'test@mcst.edu.ph',
                'oauth_sub': 'sub-123',
                'full_name': 'Test User',
            }
        resp = client.get('/login/role-select')
        assert resp.status_code == 200

    def test_role_select_post_student(self, client, mock_db):
        with client.session_transaction() as sess:
            sess['_google_oauth_data'] = {
                'email': 'test@mcst.edu.ph',
                'oauth_sub': 'sub-123',
                'full_name': 'Test User',
            }

        from unittest.mock import patch
        with patch('app.auth.routes.get_admin_count', return_value=1):
            mock_db['fetch_one'].side_effect = lambda q, p=None: (1, 'Student') if p and p[0] == 'Student' else (1,) if 'INSERT' in q else None
            mock_db['execute'].return_value = 1

            resp = client.post('/login/role-select', data={
                'role': 'Student',
                'id_number': '2024-0001',
                'department': 'BSIT',
            })
            assert resp.status_code == 302
            assert 'dashboard' in resp.location

    def test_role_select_post_faculty_pending(self, client, mock_db):
        with client.session_transaction() as sess:
            sess['_google_oauth_data'] = {
                'email': 'faculty@mcst.edu.ph',
                'oauth_sub': 'sub-789',
                'full_name': 'Faculty User',
            }

        from unittest.mock import patch
        with patch('app.auth.routes.get_admin_count', return_value=1):
            mock_db['fetch_one'].side_effect = lambda q, p=None: (2, 'Faculty') if p and p[0] == 'Faculty' else None
            mock_db['execute'].return_value = 1

            resp = client.post('/login/role-select', data={
                'role': 'Faculty',
                'id_number': '2024-1001',
                'department': 'CS Department',
            })
            assert resp.status_code == 200
            assert b'approval' in resp.data.lower() or b'pending' in resp.data.lower()

    def test_role_select_invalid_role(self, client):
        with client.session_transaction() as sess:
            sess['_google_oauth_data'] = {
                'email': 'test@mcst.edu.ph',
                'oauth_sub': 'sub-123',
                'full_name': 'Test User',
            }
        resp = client.post('/login/role-select', data={
            'role': 'Admin',
            'id_number': '',
            'department': '',
        })
        assert resp.status_code == 200
        assert b'valid' in resp.data.lower() or b'error' in resp.data.lower()


class TestLogout:
    @patch('app.auth.routes.log_activity')
    def test_logout(self, mock_log_activity, student_client, client):
        resp = student_client.get('/logout')
        assert resp.status_code == 302
        assert resp.location.endswith('/login')

    def test_logout_unauthenticated_redirects(self, client):
        resp = client.get('/logout')
        assert resp.status_code == 302
        assert '/login' in resp.location


class TestUserManagement:
    USERS_TABLE = [
        (1, 'alice@mcst.edu.ph', 'Alice', 'Student', 'active', datetime(2024, 1, 15), '2024-0001', 'BSIT'),
        (2, 'bob@mcst.edu.ph', 'Bob', 'Faculty', 'pending', datetime(2024, 2, 20), '2024-1001', 'CS'),
        (3, 'carol@mcst.edu.ph', 'Carol', 'Librarian', 'active', datetime(2024, 3, 10), '2024-2001', 'Library'),
    ]
    ROLES = [(1, 'Student'), (2, 'Faculty'), (3, 'Librarian'), (4, 'Admin')]

    def test_admin_users_student_forbidden(self, student_client, mock_db):
        mock_db['fetch_all'].return_value = self.USERS_TABLE
        resp = student_client.get('/admin/users')
        assert resp.status_code == 403

    def test_admin_users_librarian_allowed(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (4,)
        mock_db['fetch_all'].side_effect = lambda q, p=None: [] if 'pending' in q else self.USERS_TABLE
        resp = librarian_client.get('/admin/users')
        assert resp.status_code == 200

    def test_admin_users_admin_allowed(self, admin_client, mock_db):
        mock_db['fetch_one'].return_value = (4,)
        mock_db['fetch_all'].side_effect = lambda q, p=None: [] if 'pending' in q else self.USERS_TABLE
        resp = admin_client.get('/admin/users')
        assert resp.status_code == 200

    def test_approve_user_librarian(self, librarian_client, mock_db):
        mock_db['execute'].return_value = 1
        resp = librarian_client.post('/admin/users/2/approve')
        assert resp.status_code == 302

    def test_approve_user_student_forbidden(self, student_client, mock_db):
        resp = student_client.post('/admin/users/2/approve')
        assert resp.status_code == 403

    @patch('app.auth.routes.log_activity')
    def test_toggle_status_admin(self, mock_log, admin_client, mock_db):
        mock_db['execute'].return_value = 1
        resp = admin_client.post('/admin/users/1/toggle-status')
        assert resp.status_code == 302

    def test_toggle_status_librarian_forbidden(self, librarian_client, mock_db):
        resp = librarian_client.post('/admin/users/1/toggle-status')
        assert resp.status_code == 403

    def test_change_role_admin(self, admin_client, mock_db):
        mock_db['execute'].return_value = 1
        resp = admin_client.post('/admin/users/1/role', data={'role_id': '3'})
        assert resp.status_code == 302

    def test_change_role_librarian_forbidden(self, librarian_client, mock_db):
        resp = librarian_client.post('/admin/users/1/role', data={'role_id': '3'})
        assert resp.status_code == 403
