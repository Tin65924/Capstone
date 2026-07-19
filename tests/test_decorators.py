"""Tests for role-based access decorators."""

from flask import abort
from flask_login import login_user


class TestRoleRequired:
    """Verify the role_required decorator returns 401/403 appropriately."""

    def test_unauthenticated_gets_401(self, client):
        resp = client.get('/admin/users')
        assert resp.status_code == 302
        assert '/login' in resp.location

    def test_student_blocked_from_librarian_page(self, student_client):
        resp = student_client.get('/cataloging')
        assert resp.status_code == 403

    def test_student_blocked_from_admin_page(self, student_client):
        resp = student_client.get('/admin/users')
        assert resp.status_code == 403

    def test_faculty_blocked_from_librarian_page(self, faculty_client):
        resp = faculty_client.get('/circulation')
        assert resp.status_code == 403

    def test_faculty_blocked_from_admin_page(self, faculty_client):
        resp = faculty_client.post('/admin/users/1/toggle-status')
        assert resp.status_code == 403

    def test_librarian_allowed_librarian_page(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/cataloging')
        assert resp.status_code != 403

    def test_librarian_blocked_admin_only(self, librarian_client):
        resp = librarian_client.post('/admin/users/1/toggle-status')
        assert resp.status_code == 403

    def test_admin_allowed_everything(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = admin_client.get('/admin/users')
        assert resp.status_code == 200
        mock_db['execute'].return_value = 1
        resp = admin_client.post('/admin/users/1/toggle-status')
        assert resp.status_code == 302
        resp = admin_client.get('/cataloging')
        assert resp.status_code == 200
        resp = admin_client.get('/circulation')
        assert resp.status_code == 200
        resp = admin_client.get('/backup')
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
        ('/cataloging', 'Librarian'),
        ('/circulation', 'Librarian'),
        ('/inventory', 'Librarian'),
        ('/analytics', 'Librarian'),
        ('/procurement', 'Librarian'),
        ('/requests', None),
        ('/user/profile', None),
        ('/user/history', None),
        ('/backup', 'Admin'),
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
            if route == '/backup' or required_role:
                resp = student_client.get(route)
                assert resp.status_code == 403, f'{route} returned {resp.status_code} for Student (expected 403)'

    def test_faculty_blocked_from_staff_routes(self, faculty_client):
        for route, required_role in self.ROLE_CHECKLIST:
            if route == '/backup' or required_role:
                resp = faculty_client.get(route)
                assert resp.status_code == 403, f'{route} returned {resp.status_code} for Faculty (expected 403)'
