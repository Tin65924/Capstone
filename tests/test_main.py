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


class TestDashboardAttention:
    PENDING = [(1, 'a@mcst.edu.ph', 'Pending User', 'Student', '2026-01-01', '1', 'CS')]
    GROUPS = [(1, 'T', 'A', 10, 3, 2, 0, 0)]

    def test_attention_counts(self, mock_db):
        from app.main.models import get_attention_summary
        mock_db['fetch_one'].side_effect = [(10,), (3,), (1,)]
        mock_db['fetch_all'].side_effect = [self.PENDING, self.GROUPS]
        assert get_attention_summary() == {
            'overdue_items': 3, 'due_soon': 1,
            'pending_users': 1, 'waiting_reservations': 5,
        }

    def test_dashboard_stats_extended(self, mock_db):
        from app.main.models import get_dashboard_stats
        mock_db['fetch_one'].side_effect = [(100,), (250,), (10,), (4,), (3,)]
        mock_db['fetch_all'].side_effect = [self.GROUPS, [], [(7,)]]
        stats = get_dashboard_stats()
        assert stats['reservations_waiting'] == 5
        assert stats['procurement_open'] == 1
        assert stats['total_titles'] == 100
        assert stats['total_accessions'] == 250
        assert stats['total_collection'] == 100

    def test_waiting_reservations_skips_bad_rows(self, mock_db):
        from app.main.models import count_waiting_reservations
        mock_db['fetch_all'].return_value = [
            (1, 'T', 'A', 10, 3, 2, 0, 0), ('short',), (1, 'T', 'A', 1, 'x', 0, 0, 0),
        ]
        assert count_waiting_reservations() == 5

    def test_librarian_dashboard_shows_panel(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [
            (100,), (250,), (10,), (4,), (3,), (10,), (3,), (1,),
        ]
        mock_db['fetch_all'].side_effect = [
            self.GROUPS, [], [(7,)], [], [], self.PENDING, self.GROUPS,
        ]
        resp = librarian_client.get('/librarian')
        assert resp.status_code == 200
        assert b'Needs Attention' in resp.data
        assert b'Overdue loans' in resp.data
        assert b'Due soon' in resp.data
        assert b'Pending approvals' in resp.data
        assert b'Waiting reservations' in resp.data
        assert b'Reservations' in resp.data
        assert b'To Order' in resp.data
        assert b'Total Collection per Title' in resp.data
        assert b'Total Collection per Accession' in resp.data
        assert b'/librarian/reservations' in resp.data
        assert b'/librarian/procurement' in resp.data
        assert b'/librarian/users' in resp.data

    def test_dashboard_all_clear_state(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian')
        assert resp.status_code == 200
        assert b'All clear' in resp.data

    def test_admin_dashboard_shows_panel(self, admin_client, mock_db):
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        resp = admin_client.get('/admin')
        assert resp.status_code == 200
        assert b'Needs Attention' in resp.data
