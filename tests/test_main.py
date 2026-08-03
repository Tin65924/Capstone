"""Tests for main routes: landing page, dashboard, user profile, history."""


class TestLandingPage:
    def test_index_public(self, client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = client.get('/')
        assert resp.status_code == 200
        assert b'MCST' in resp.data or b'library' in resp.data.lower() or b'Library' in resp.data

    def test_index_shows_new_arrivals(self, client, mock_db):
        mock_db['fetch_all'].return_value = [
            (1, 'New Book Title', 'Author Name', None, None, 2025,
             None, None, None, 'Book', None, 'active', '2025-01-01'),
        ]
        resp = client.get('/')
        assert resp.status_code == 200
        assert b'New Book Title' in resp.data or b'New' in resp.data


class TestDashboard:
    def test_dashboard_unauthenticated_redirects(self, client):
        resp = client.get('/dashboard')
        assert resp.status_code == 302
        assert '/login' in resp.location

    def test_dashboard_redirects_student_to_profile(self, student_client):
        resp = student_client.get('/dashboard')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_dashboard_redirects_faculty_to_profile(self, faculty_client):
        resp = faculty_client.get('/dashboard')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_dashboard_redirects_librarian_to_profile(self, librarian_client):
        resp = librarian_client.get('/dashboard')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_dashboard_redirects_admin_to_profile(self, admin_client):
        resp = admin_client.get('/dashboard')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location


class TestUserProfile:
    def test_profile_unauthenticated_redirects(self, client):
        resp = client.get('/user/profile')
        assert resp.status_code == 302
        assert '/login' in resp.location

    def test_profile_student_allowed(self, student_client, mock_db):
        mock_db['fetch_one'].return_value = (1, 'student@mcst.edu.ph', 'Student', 'Test Student')
        resp = student_client.get('/user/profile')
        assert resp.status_code == 200

    def test_profile_faculty_allowed(self, faculty_client, mock_db):
        mock_db['fetch_one'].return_value = (2, 'faculty@mcst.edu.ph', 'Faculty', 'Test Faculty')
        resp = faculty_client.get('/user/profile')
        assert resp.status_code == 200

    def test_profile_librarian_allowed(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (3, 'librarian@mcst.edu.ph', 'Librarian', 'Test Librarian')
        resp = librarian_client.get('/user/profile')
        assert resp.status_code == 200

    def test_profile_admin_allowed(self, admin_client, mock_db):
        mock_db['fetch_one'].return_value = (4, 'admin@mcst.edu.ph', 'Admin', 'Test Admin')
        resp = admin_client.get('/user/profile')
        assert resp.status_code == 200

    def test_profile_does_not_show_admin_tools(self, admin_client, mock_db):
        mock_db['fetch_one'].return_value = (4, 'admin@mcst.edu.ph', 'Admin', 'Test Admin')
        resp = admin_client.get('/user/profile')
        assert b'Backup' not in resp.data
        assert b'Cataloging' not in resp.data

    def test_profile_shows_admin_dashboard_button(self, admin_client, mock_db):
        mock_db['fetch_one'].return_value = (4, 'admin@mcst.edu.ph', 'Admin', 'Test Admin')
        resp = admin_client.get('/user/profile')
        assert b'Admin Dashboard' in resp.data
        assert b'Librarian Dashboard' in resp.data

    def test_profile_shows_librarian_dashboard_button(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (3, 'librarian@mcst.edu.ph', 'Librarian', 'Test Librarian')
        resp = librarian_client.get('/user/profile')
        assert b'Librarian Dashboard' in resp.data
        assert b'Admin Dashboard' not in resp.data

    def test_profile_student_has_no_dashboard_buttons(self, student_client, mock_db):
        mock_db['fetch_one'].return_value = (1, 'student@mcst.edu.ph', 'Student', 'Test Student')
        resp = student_client.get('/user/profile')
        assert b'Admin Dashboard' not in resp.data
        assert b'Librarian Dashboard' not in resp.data


class TestUserHistory:
    def test_history_unauthenticated_redirects(self, client):
        resp = client.get('/user/history')
        assert resp.status_code == 302
        assert '/login' in resp.location

    def test_history_authenticated_allowed(self, student_client):
        resp = student_client.get('/user/history')
        assert resp.status_code == 200

    def test_history_admin_allowed(self, admin_client):
        resp = admin_client.get('/user/history')
        assert resp.status_code == 200


class TestRoleDashboards:
    def test_librarian_dashboard_librarian_allowed(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian')
        assert resp.status_code == 200

    def test_librarian_dashboard_admin_allowed(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = admin_client.get('/librarian')
        assert resp.status_code == 200
        assert b'Admin Dashboard' in resp.data

    def test_librarian_dashboard_student_forbidden(self, student_client):
        resp = student_client.get('/librarian')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_admin_dashboard_admin_allowed(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = admin_client.get('/admin')
        assert resp.status_code == 200

    def test_admin_dashboard_librarian_forbidden(self, librarian_client):
        resp = librarian_client.get('/admin')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_admin_dashboard_student_forbidden(self, student_client):
        resp = student_client.get('/admin')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_admin_dashboard_unauthenticated_redirects(self, client):
        resp = client.get('/admin')
        assert resp.status_code == 302
        assert '/login' in resp.location
