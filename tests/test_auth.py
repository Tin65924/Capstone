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
        mock_oauth_flow.code_verifier = 'test-verifier'
        mock_oauth_flow.authorization_url.return_value = ('https://accounts.google.com/o/oauth2/auth?state=xyz', 'xyz')
        resp = client.get('/login/google')
        assert resp.status_code == 302
        assert resp.location.startswith('https://accounts.google.com/')
        with client.session_transaction() as sess:
            assert '_oauth_state' in sess
            assert sess['_oauth_code_verifier'] == 'test-verifier'

    def test_google_login_no_verifier_not_stored(self, client, mock_oauth_flow):
        mock_oauth_flow.authorization_url.return_value = ('https://accounts.google.com/o/oauth2/auth?state=xyz', 'xyz')
        resp = client.get('/login/google')
        assert resp.status_code == 302
        with client.session_transaction() as sess:
            assert '_oauth_state' in sess
            assert '_oauth_code_verifier' not in sess

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

    def test_callback_restores_code_verifier(self, client, mock_oauth_flow):
        with client.session_transaction() as sess:
            sess['_oauth_state'] = 'test-state'
            sess['_oauth_code_verifier'] = 'test-verifier'

        mock_oauth_flow.code_verifier = None
        mock_oauth_flow.fetch_token.return_value = None
        mock_oauth_flow.credentials.id_token = 'fake-id-token'

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
                with patch('app.auth.routes.login_user'):
                    resp = client.get('/login/google/callback', query_string={'state': 'test-state', 'code': 'auth-code'})
                    assert resp.status_code == 302
                    assert mock_oauth_flow.code_verifier == 'test-verifier'
                    with client.session_transaction() as sess:
                        assert '_oauth_code_verifier' not in sess

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
                                assert '/user/profile' in resp.location

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
            mock_db['fetch_one'].side_effect = lambda q, p=None: (1, 'Student') if p and p[0] == 'Student' else (1,) if 'INSERT' in q or 'FROM departments' in q else None
            mock_db['execute'].return_value = 1

            resp = client.post('/login/role-select', data={
                'role': 'Student',
                'id_number': '2024-00001',
                'department': 'BSIS',
            })
            assert resp.status_code == 302
            assert '/user/profile' in resp.location

    def test_role_select_rejects_unknown_program(self, client, mock_db):
        with client.session_transaction() as sess:
            sess['_google_oauth_data'] = {
                'email': 'test@mcst.edu.ph',
                'oauth_sub': 'sub-123',
                'full_name': 'Test User',
            }

        from unittest.mock import patch
        with patch('app.auth.routes.get_admin_count', return_value=1):
            mock_db['fetch_one'].return_value = None

            resp = client.post('/login/role-select', data={
                'role': 'Student',
                'id_number': '2024-00001',
                'department': 'Made Up Program',
            })
            assert resp.status_code == 200
            assert b'valid program' in resp.data.lower()
            assert mock_db['execute'].call_count == 0

    def test_role_select_post_faculty_pending(self, client, mock_db):
        with client.session_transaction() as sess:
            sess['_google_oauth_data'] = {
                'email': 'faculty@mcst.edu.ph',
                'oauth_sub': 'sub-789',
                'full_name': 'Faculty User',
            }

        from unittest.mock import patch
        with patch('app.auth.routes.get_admin_count', return_value=1):
            mock_db['fetch_one'].side_effect = lambda q, p=None: (2, 'Faculty') if p and p[0] == 'Faculty' else (1,) if 'FROM departments' in q else None
            mock_db['execute'].return_value = 1

            resp = client.post('/login/role-select', data={
                'role': 'Faculty',
                'id_number': 'FAC-10001',
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

    def test_role_select_rejects_bad_student_id(self, client, mock_db):
        with client.session_transaction() as sess:
            sess['_google_oauth_data'] = {
                'email': 'test@mcst.edu.ph',
                'oauth_sub': 'sub-123',
                'full_name': 'Test User',
            }
        resp = client.post('/login/role-select', data={
            'role': 'Student',
            'id_number': '2024-0001',
            'department': 'BSIS',
        })
        assert resp.status_code == 200
        assert b'invalid id' in resp.data.lower()
        assert mock_db['execute'].call_count == 0

    def test_role_select_rejects_bad_faculty_id(self, client, mock_db):
        with client.session_transaction() as sess:
            sess['_google_oauth_data'] = {
                'email': 'faculty@mcst.edu.ph',
                'oauth_sub': 'sub-789',
                'full_name': 'Faculty User',
            }
        resp = client.post('/login/role-select', data={
            'role': 'Faculty',
            'id_number': '2024-10001',
            'department': 'CS Department',
        })
        assert resp.status_code == 200
        assert b'invalid id' in resp.data.lower()
        assert mock_db['execute'].call_count == 0

    def test_role_select_rejects_duplicate_id(self, client, mock_db):
        with client.session_transaction() as sess:
            sess['_google_oauth_data'] = {
                'email': 'test@mcst.edu.ph',
                'oauth_sub': 'sub-123',
                'full_name': 'Test User',
            }
        mock_db['fetch_one'].return_value = (9, 'other@mcst.edu.ph', 'Student', 'Other')
        resp = client.post('/login/role-select', data={
            'role': 'Student',
            'id_number': '2024-00001',
            'department': 'BSIS',
        })
        assert resp.status_code == 200
        assert b'already registered' in resp.data.lower()
        assert mock_db['execute'].call_count == 0


class TestIdNumberFormats:
    def test_patterns(self):
        from app.auth.models import is_valid_id_number
        assert is_valid_id_number('2024-00001', 'Student')
        assert not is_valid_id_number('2024-0001', 'Student')
        assert not is_valid_id_number('FAC-00001', 'Student')
        assert is_valid_id_number('FAC-00001', 'Faculty')
        assert not is_valid_id_number('0000001', 'Faculty')
        assert not is_valid_id_number('2024-00001', 'Faculty')
        assert is_valid_id_number('LIB-00001', 'Librarian')
        assert not is_valid_id_number('LIB-001', 'Librarian')
        assert is_valid_id_number('7', 'Admin')
        assert is_valid_id_number('10', 'Admin')
        assert not is_valid_id_number('11', 'Admin')
        assert not is_valid_id_number('0', 'Admin')


class TestDepartmentsManager:
    def test_librarian_adds_program(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = None  # not a duplicate
        resp = librarian_client.post('/librarian/departments/add', data={
            'name': 'BSCS',
            'dept_type': 'program',
        })
        assert resp.status_code == 302
        assert '/librarian/users' in resp.location
        call_args = mock_db['execute'].call_args_list[0]
        assert 'INSERT INTO departments' in call_args[0][0]
        assert call_args[0][1] == ('BSCS', 'program')

    def test_add_duplicate_rejected(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (1,)
        resp = librarian_client.post('/librarian/departments/add', data={
            'name': 'BSIS',
            'dept_type': 'program',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_add_invalid_type_rejected(self, librarian_client, mock_db):
        resp = librarian_client.post('/librarian/departments/add', data={
            'name': 'Whatever',
            'dept_type': 'bogus',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_admin_deletes_unused(self, admin_client, mock_db):
        mock_db['fetch_one'].side_effect = [
            (1, 'BSCS', 'program'),  # get_department_by_id
            (0,),                     # count_borrowers_in_department
        ]
        resp = admin_client.post('/admin/departments/1/delete')
        assert resp.status_code == 302
        call_args = mock_db['execute'].call_args_list[0]
        assert 'DELETE FROM departments' in call_args[0][0]

    def test_admin_delete_blocked_when_in_use(self, admin_client, mock_db):
        mock_db['fetch_one'].side_effect = [
            (1, 'BSIS', 'program'),
            (3,),
        ]
        resp = admin_client.post('/admin/departments/1/delete')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_admin_edit_user_rejects_bad_department(self, admin_client, mock_db):
        # profile: Student with current dept BSIS; submitting unknown program
        mock_db['fetch_one'].side_effect = [
            (1, 'a@mcst.edu.ph', 'Student', 'Stu', 5, '2024-1', 'BSIS', None, 'active'),
            None,  # is_valid_department -> invalid
        ]
        resp = admin_client.post('/admin/users/1/edit', data={
            'full_name': 'Stu',
            'id_number': '2024-1',
            'department': 'Made Up',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_admin_edit_user_allows_unchanged_legacy(self, admin_client, mock_db):
        mock_db['fetch_one'].return_value = (
            1, 'a@mcst.edu.ph', 'Student', 'Stu', 5, '2024-1', 'Old Variant', None, 'active')
        resp = admin_client.post('/admin/users/1/edit', data={
            'full_name': 'Stu',
            'id_number': '2024-1',
            'department': 'Old Variant',
        })
        assert resp.status_code == 302
        # update_user_accounts + update_borrowers + log_activity
        assert mock_db['execute'].call_count == 3

    def test_admin_edit_staff_rejects_unknown_department(self, admin_client, mock_db):
        mock_db['fetch_one'].side_effect = [
            (2, 'b@mcst.edu.ph', 'Admin', 'Boss', 9, 'A-1', 'Old Dept', None, 'active'),
            None,  # is_valid_any_department -> invalid
        ]
        resp = admin_client.post('/admin/users/2/edit', data={
            'full_name': 'Boss',
            'id_number': 'A-1',
            'department': 'Junk Dept',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_admin_edit_staff_accepts_combined_vocab(self, admin_client, mock_db):
        mock_db['fetch_one'].side_effect = [
            (2, 'b@mcst.edu.ph', 'Admin', 'Boss', 9, 'A-1', 'Old Dept', None, 'active'),
            (1,),  # is_valid_any_department -> valid
            (2, 'b@mcst.edu.ph', 'Admin', 'Boss', 'active'),  # audit name lookup
        ]
        resp = admin_client.post('/admin/users/2/edit', data={
            'full_name': 'Boss',
            'id_number': 'A-1',
            'department': 'BSIS',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 3

    def test_add_race_reports_exists(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = None  # pre-check passes
        mock_db['execute'].return_value = 0  # ON CONFLICT swallowed a racing insert
        resp = librarian_client.post('/librarian/departments/add', data={
            'name': 'BSCS',
            'dept_type': 'program',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 1  # no log_activity write

    def test_delete_confirm_uses_data_attribute(self, admin_client, mock_db):
        mock_db['fetch_all'].side_effect = [
            [],  # users
            [],  # pending
            [],  # roles
            [(1, 'BSIS', 'program')],
            [(2, 'HR', 'department')],
        ]
        resp = admin_client.get('/librarian/users')
        assert resp.status_code == 200
        assert b'confirmDeptDelete(this)' in resp.data
        assert b"confirm('Delete &quot;" not in resp.data
        assert b'data-dept-name="HR"' in resp.data


class TestUserCardFilters:
    USERS = [
        (1, 's@mcst.edu.ph', 'Alpha Student', 'Student', 'active', '2026-01-01', '2024-1', 'BSIS'),
        (2, 'f@mcst.edu.ph', 'Beta Faculty', 'Faculty', 'active', '2026-01-01', '2024-2', 'BSIS'),
        (3, 'x@mcst.edu.ph', 'Gamma Ex', 'Student', 'disabled', '2026-01-01', '2024-3', 'BSN'),
    ]

    def _mock_lists(self, mock_db):
        mock_db['fetch_all'].side_effect = [
            list(self.USERS),  # get_all_users
            [],                # get_pending_users
            [],                # get_roles
            [],                # programs
            [],                # departments
        ]

    def test_role_filter_shows_only_students(self, librarian_client, mock_db):
        self._mock_lists(mock_db)
        resp = librarian_client.get('/librarian/users?role=Student')
        assert resp.status_code == 200
        assert b'Alpha Student' in resp.data
        assert b'Beta Faculty' not in resp.data
        assert b'ring-2 ring-primary' in resp.data

    def test_status_filter_still_works(self, librarian_client, mock_db):
        self._mock_lists(mock_db)
        resp = librarian_client.get('/librarian/users?status=disabled')
        assert resp.status_code == 200
        assert b'Gamma Ex' in resp.data
        assert b'Alpha Student' not in resp.data

    def test_export_respects_role_filter(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = list(self.USERS)
        resp = librarian_client.get('/librarian/users/export?role=Student&format=csv')
        assert resp.status_code == 200
        body = resp.data.decode('utf-8-sig')
        assert 'Alpha Student' in body and 'Beta Faculty' not in body


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
        resp = student_client.get('/librarian/users')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_admin_users_librarian_allowed(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (4,)
        mock_db['fetch_all'].side_effect = lambda q, p=None: [] if 'pending' in q else self.USERS_TABLE
        resp = librarian_client.get('/librarian/users')
        assert resp.status_code == 200

    def test_admin_users_admin_allowed(self, admin_client, mock_db):
        mock_db['fetch_one'].return_value = (4,)
        mock_db['fetch_all'].side_effect = lambda q, p=None: [] if 'pending' in q else self.USERS_TABLE
        resp = admin_client.get('/librarian/users')
        assert resp.status_code == 200

    def test_approve_user_librarian(self, librarian_client, mock_db):
        mock_db['execute'].return_value = 1
        resp = librarian_client.post('/librarian/users/2/approve')
        assert resp.status_code == 302

    def test_approve_user_student_forbidden(self, student_client, mock_db):
        resp = student_client.post('/librarian/users/2/approve')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    @patch('app.auth.routes.log_activity')
    def test_toggle_status_admin(self, mock_log, admin_client, mock_db):
        mock_db['execute'].return_value = 1
        resp = admin_client.post('/admin/users/1/toggle-status')
        assert resp.status_code == 302

    def test_toggle_status_librarian_forbidden(self, librarian_client, mock_db):
        resp = librarian_client.post('/admin/users/1/toggle-status')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_change_role_admin(self, admin_client, mock_db):
        mock_db['execute'].return_value = 1
        resp = admin_client.post('/admin/users/1/role', data={'role_id': '3'})
        assert resp.status_code == 302

    def test_change_role_librarian_forbidden(self, librarian_client, mock_db):
        resp = librarian_client.post('/admin/users/1/role', data={'role_id': '3'})
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_archive_user_admin(self, admin_client, mock_db):
        mock_db['fetch_one'].return_value = (1, 'a@x.ph', 'Student', 'Ann')
        mock_db['execute'].return_value = 1
        resp = admin_client.post('/admin/users/1/archive')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count >= 1
        call_args = mock_db['execute'].call_args_list[0]
        assert 'UPDATE user_accounts' in call_args[0][0]

    def test_archive_user_librarian_forbidden(self, librarian_client, mock_db):
        resp = librarian_client.post('/admin/users/1/archive')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_unarchive_user_admin(self, admin_client, mock_db):
        mock_db['fetch_one'].return_value = (1, 'a@x.ph', 'Student', 'Ann')
        mock_db['execute'].return_value = 1
        resp = admin_client.post('/admin/users/1/unarchive')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count >= 1

    def test_unarchive_user_librarian_forbidden(self, librarian_client, mock_db):
        resp = librarian_client.post('/admin/users/1/unarchive')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_delete_user_archived_success(self, admin_client, mock_db):
        mock_db['fetch_one'].return_value = ('archived',)
        mock_db['execute'].return_value = 1
        resp = admin_client.post('/admin/users/1/delete')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count >= 1
        call_args = mock_db['execute'].call_args_list[0]
        assert 'DELETE FROM user_accounts' in call_args[0][0]

    def test_delete_user_not_archived_fails(self, admin_client, mock_db):
        mock_db['fetch_one'].return_value = ('active',)
        resp = admin_client.post('/admin/users/1/delete')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_delete_user_not_found(self, admin_client, mock_db):
        mock_db['fetch_one'].return_value = None
        resp = admin_client.post('/admin/users/999/delete')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    @staticmethod
    def _archived_lookup(q, p=None, status='archived'):
        """Mimic real DB semantics: the active-only lookup sees nothing
        for non-active users, while status-agnostic reads see the row."""
        if "account_status = 'active'" in q:
            return None
        if q.strip().startswith('SELECT account_status'):
            return (status,)
        return (1, 'a@mcst.edu.ph', 'Student', 'Ann', status)

    def test_delete_archived_user_succeeds(self, admin_client, mock_db):
        mock_db['fetch_one'].side_effect = self._archived_lookup
        resp = admin_client.post('/admin/users/1/delete')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count >= 1
        assert 'DELETE FROM user_accounts' in mock_db['execute'].call_args_list[0][0][0]

    def test_unarchive_archived_user_succeeds(self, admin_client, mock_db):
        mock_db['fetch_one'].side_effect = self._archived_lookup
        resp = admin_client.post('/admin/users/1/unarchive')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count >= 1
        assert 'UPDATE user_accounts' in mock_db['execute'].call_args_list[0][0][0]

    def test_archive_disabled_user_succeeds(self, admin_client, mock_db):
        import functools
        mock_db['fetch_one'].side_effect = functools.partial(
            self._archived_lookup, status='disabled')
        resp = admin_client.post('/admin/users/1/archive')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count >= 1
        assert 'UPDATE user_accounts' in mock_db['execute'].call_args_list[0][0][0]

    def test_delete_user_librarian_forbidden(self, librarian_client, mock_db):
        resp = librarian_client.post('/admin/users/1/delete')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_delete_user_unauthenticated(self, client, mock_db):
        resp = client.post('/admin/users/1/delete')
        assert resp.status_code == 302
        assert '/login' in resp.location
