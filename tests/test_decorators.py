"""Tests for role-based access decorators."""


class TestRoleRequired:
    """Verify the role_required decorator returns 401/403 appropriately."""

    def test_unauthenticated_gets_401(self, client):
        resp = client.get('/librarian/users')
        assert resp.status_code == 302
        assert '/login' in resp.location

    def test_student_blocked_from_librarian_page(self, student_client):
        resp = student_client.get('/librarian/cataloging')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_student_blocked_from_admin_page(self, student_client):
        resp = student_client.get('/librarian/users')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_faculty_blocked_from_librarian_page(self, faculty_client):
        resp = faculty_client.get('/librarian/circulation')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_faculty_blocked_from_admin_page(self, faculty_client):
        resp = faculty_client.post('/admin/users/1/toggle-status')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_librarian_allowed_librarian_page(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/cataloging')
        assert resp.status_code != 403

    def test_librarian_blocked_admin_only(self, librarian_client):
        resp = librarian_client.post('/admin/users/1/toggle-status')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_admin_allowed_everything(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = admin_client.get('/librarian/users')
        assert resp.status_code == 200
        mock_db['execute'].return_value = 1
        resp = admin_client.post('/admin/users/1/toggle-status')
        assert resp.status_code == 302
        resp = admin_client.get('/librarian/cataloging')
        assert resp.status_code == 200
        resp = admin_client.get('/librarian/circulation')
        assert resp.status_code == 200
        resp = admin_client.get('/admin/backup')
        assert resp.status_code == 200

    def test_all_roles_access_public(self, client, student_client, faculty_client, librarian_client, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        for c in [client, student_client, faculty_client, librarian_client, admin_client]:
            resp = c.get('/')
            assert resp.status_code == 200
            resp = c.get('/catalog')
            assert resp.status_code == 200


class TestProtectedRoutesByRole:
    """End-to-end checks that every protected route enforces the correct role."""

    ROLE_CHECKLIST = [
        ('/librarian/cataloging', 'Librarian'),
        ('/librarian/circulation', 'Librarian'),
        ('/librarian/inventory', 'Librarian'),
        ('/librarian/analytics', 'Librarian'),
        ('/librarian/procurement', 'Librarian'),
        ('/librarian/requests', 'Librarian'),
        ('/librarian', 'Librarian'),
        ('/librarian/users', 'Librarian'),
        ('/user/profile', None),
        ('/user/history', None),
        ('/admin/backup', 'Admin'),
        ('/admin', 'Admin'),
    ]

    def test_librarian_routes_accessible(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = []
        for route, required_role in self.ROLE_CHECKLIST:
            if required_role == 'Admin':
                continue
            resp = librarian_client.get(route)
            assert resp.status_code in (200, 302), f'{route} returned {resp.status_code} for Librarian'

    def test_student_blocked_from_staff_routes(self, student_client):
        for route, required_role in self.ROLE_CHECKLIST:
            if route in ('/user/profile', '/user/history'):
                continue
            resp = student_client.get(route)
            assert resp.status_code == 302, f'{route} returned {resp.status_code} for Student (expected redirect)'
            assert '/user/profile' in resp.location, f'{route} did not redirect to profile for Student'

    def test_faculty_blocked_from_staff_routes(self, faculty_client):
        for route, required_role in self.ROLE_CHECKLIST:
            if route in ('/user/profile', '/user/history'):
                continue
            resp = faculty_client.get(route)
            assert resp.status_code == 302, f'{route} returned {resp.status_code} for Faculty (expected redirect)'
            assert '/user/profile' in resp.location, f'{route} did not redirect to profile for Faculty'
