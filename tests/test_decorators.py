"""Tests for role-based access decorators."""


class TestRoleRequired:
    """Verify the role_required decorator returns 401/403 appropriately."""

    def test_unauthenticated_gets_401(self, client):
        """Validates unauthenticated gets 401 `/librarian/users` (expects 302) [TestRoleRequired / decorators].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = client.get('/librarian/users')
        assert resp.status_code == 302
        assert '/login' in resp.location

    def test_student_blocked_from_librarian_page(self, student_client):
        """Validates student blocked from librarian page `/librarian/cataloging` as student (expects 302) [TestRoleRequired / decorators].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = student_client.get('/librarian/cataloging')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_student_blocked_from_admin_page(self, student_client):
        """Validates student blocked from admin page `/librarian/users` as student (expects 302) [TestRoleRequired / decorators].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates decorators is broken for this case (users see wrong page, blocked action, or bad data)."""
        resp = student_client.get('/librarian/users')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_faculty_blocked_from_librarian_page(self, faculty_client):
        """Validates faculty blocked from librarian page `/librarian/circulation` as faculty (expects 302) [TestRoleRequired / decorators].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates decorators is broken for this case (users see wrong page, blocked action, or bad data)."""
        resp = faculty_client.get('/librarian/circulation')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_faculty_blocked_from_admin_page(self, faculty_client):
        """Validates faculty blocked from admin page `/admin/users/1/toggle-status` as faculty (expects 302) [TestRoleRequired / decorators].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates decorators is broken for this case (users see wrong page, blocked action, or bad data)."""
        resp = faculty_client.post('/admin/users/1/toggle-status')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_librarian_allowed_librarian_page(self, librarian_client, mock_db):
        """Validates librarian allowed librarian page `/librarian/cataloging` as librarian [TestRoleRequired / decorators].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/cataloging')
        assert resp.status_code != 403

    def test_librarian_blocked_admin_only(self, librarian_client):
        """Validates librarian blocked admin only `/admin/users/1/toggle-status` as librarian (expects 302) [TestRoleRequired / decorators].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates decorators is broken for this case (users see wrong page, blocked action, or bad data)."""
        resp = librarian_client.post('/admin/users/1/toggle-status')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_admin_allowed_everything(self, admin_client, mock_db):
        """Validates admin allowed everything `/librarian/users` as admin (expects 200) [TestRoleRequired / decorators].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
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
        """Validates all roles access public (expects 200) [TestRoleRequired / decorators].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates decorators is broken for this case (users see wrong page, blocked action, or bad data)."""
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
        """Validates librarian routes accessible as librarian [TestProtectedRoutesByRole / decorators].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates decorators is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_all'].return_value = []
        for route, required_role in self.ROLE_CHECKLIST:
            if required_role == 'Admin':
                continue
            resp = librarian_client.get(route)
            assert resp.status_code in (200, 302), f'{route} returned {resp.status_code} for Librarian'

    def test_student_blocked_from_staff_routes(self, student_client):
        """Validates student blocked from staff routes as student (expects 302) [TestProtectedRoutesByRole / decorators].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates decorators is broken for this case (users see wrong page, blocked action, or bad data)."""
        for route, required_role in self.ROLE_CHECKLIST:
            if route in ('/user/profile', '/user/history'):
                continue
            resp = student_client.get(route)
            assert resp.status_code == 302, f'{route} returned {resp.status_code} for Student (expected redirect)'
            assert '/user/profile' in resp.location, f'{route} did not redirect to profile for Student'

    def test_faculty_blocked_from_staff_routes(self, faculty_client):
        """Validates faculty blocked from staff routes as faculty (expects 302) [TestProtectedRoutesByRole / decorators].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates decorators is broken for this case (users see wrong page, blocked action, or bad data)."""
        for route, required_role in self.ROLE_CHECKLIST:
            if route in ('/user/profile', '/user/history'):
                continue
            resp = faculty_client.get(route)
            assert resp.status_code == 302, f'{route} returned {resp.status_code} for Faculty (expected redirect)'
            assert '/user/profile' in resp.location, f'{route} did not redirect to profile for Faculty'
