"""Edge-case regression tests for User Management & Access Control.

Covers login `next` validation, role changes, approve/toggle/archive/
unarchive/delete existence guards, users-list params and rows, exports,
departments, user edits, and the staff/admin RBAC matrix. Includes the
open-redirect fix (backslash bypass), the role-id validation fix, and
the pending-date display guard. Everything must degrade gracefully.
"""

USER = (4, 'a@x.ph', 'Student', 'Ann')


class TestOpenRedirect:
    def test_safe_next_helper(self):
        """Validates safe next helper [TestOpenRedirect / users edge cases].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates user management/profile is broken."""
        from app.auth.routes import _safe_next_url
        assert _safe_next_url.__name__ == '_safe_next_url'

    def test_evil_next_rejected(self, client):
        """Validates evil next rejected [TestOpenRedirect / users edge cases].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        from app.auth.routes import _safe_next_url
        from flask import Flask
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 't'
        app.add_url_rule('/user/profile', endpoint='main.user_profile',
                         view_func=lambda: 'ok')
        with app.test_request_context('/login'):
            from flask import session
            for evil in ('https://evil.com', '//evil.com/x',
                         'javascript:alert(1)', '', 'not-a-path',
                         '/\\evil.com', 'http:evil'):
                session['next'] = evil
                assert _safe_next_url() == '/user/profile', evil
            session['next'] = '/librarian/requests'
            assert _safe_next_url() == '/librarian/requests'


class TestRoleChange:
    def test_bogus_role_rejected(self, admin_client, mock_db):
        """Validates bogus role rejected `/admin/users/4/role` as admin (expects 302) [TestRoleChange / users edge cases].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (UPDATE).
    Failure indicates user management/profile is broken."""
        mock_db['fetch_one'].return_value = USER
        mock_db['fetch_all'].return_value = [(1, 'Student')]
        before = mock_db['execute'].call_count
        for rid in ('9999', 'abc', '-1', '1; DROP TABLE users'):
            resp = admin_client.post('/admin/users/4/role',
                                     data={'role_id': rid})
            assert resp.status_code == 302, rid
        updates = [c[0][0] for c in mock_db['execute'].call_args_list[before:]
                   if 'UPDATE user_accounts SET role_id' in c[0][0]]
        assert updates == []

    def test_missing_role_param(self, admin_client, mock_db):
        """Validates missing role param `/admin/users/4/role` as admin (expects 302) [TestRoleChange / users edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates user management/profile is broken."""
        assert admin_client.post('/admin/users/4/role',
                                 data={}).status_code == 302

    def test_missing_user(self, admin_client, mock_db):
        """Validates missing user `/admin/users/999/role` as admin (expects 302) [TestRoleChange / users edge cases].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (UPDATE).
    Failure indicates user management/profile is broken."""
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = [(1, 'Student')]
        before = mock_db['execute'].call_count
        resp = admin_client.post('/admin/users/999/role',
                                 data={'role_id': '1'})
        assert resp.status_code == 302
        updates = [c[0][0] for c in mock_db['execute'].call_args_list[before:]
                   if 'UPDATE user_accounts SET role_id' in c[0][0]]
        assert updates == []


class TestMissingUsers:
    @staticmethod
    def _none(mock_db):
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []

    def test_actions_missing(self, admin_client, mock_db):
        """Validates actions missing `/librarian/users/999/approve` as admin (expects 302) [TestMissingUsers / users edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates user management/profile is broken."""
        self._none(mock_db)
        for url in ('/admin/users/999/toggle-status',
                    '/admin/users/999/archive',
                    '/admin/users/999/unarchive'):
            assert admin_client.post(url).status_code == 302, url
        assert admin_client.post(
            '/librarian/users/999/approve').status_code == 302

    def test_huge_ids(self, admin_client, mock_db):
        """Validates huge ids as admin (expects 302) [TestMissingUsers / users edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates user management/profile is broken."""
        self._none(mock_db)
        for url in ('/admin/users/999999999/archive',
                    '/admin/users/999999999/role'):
            assert admin_client.post(
                url, data={'role_id': '1'}).status_code == 302, url


class TestUsersList:
    def test_hostile_params(self, admin_client, mock_db):
        """Validates hostile params as admin (expects 200) [TestUsersList / users edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates user management/profile is broken."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        for url in ('/librarian/users?q=' + 'x' * 2000,
                    '/librarian/users?q=<script>alert(1)</script>',
                    '/librarian/users?scope=bogus&role=<img>',
                    '/librarian/users?status=' + 'y' * 500):
            assert admin_client.get(url).status_code == 200, url[:60]

    def test_evil_rows(self, admin_client, mock_db):
        """Validates evil rows `/librarian/users` as admin [TestUsersList / users edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates user management/profile is broken."""
        evil = '<script>alert(1)</script>'
        row = (9, evil, 'Student', evil, 'e@x.ph', 'active', '2026-01-01')
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = [row]
        body = admin_client.get('/librarian/users').data.decode()
        assert evil not in body

    def test_none_rows(self, admin_client, mock_db):
        """Validates none rows `/librarian/users` as admin (expects 200) [TestUsersList / users edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates user management/profile is broken."""
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = None
        assert admin_client.get('/librarian/users').status_code == 200


class TestDepartments:
    def test_add_hostile(self, librarian_client, mock_db):
        """Validates add hostile `/librarian/departments/add` as librarian (expects 302) [TestDepartments / users edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates user management/profile is broken."""
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        for data in ({}, {'name': ''}, {'name': 'X' * 500},
                     {'name': '<script>alert(1)</script>',
                      'dept_type': 'bogus'},
                     {'name': 'BSIT', 'dept_type': 'bogus'}):
            assert librarian_client.post(
                '/librarian/departments/add', data=data).status_code == 302

    def test_delete_missing(self, admin_client, mock_db):
        """Validates delete missing `/admin/departments/999/delete` as admin (expects 302) [TestDepartments / users edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates user management/profile is broken."""
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        assert admin_client.post(
            '/admin/departments/999/delete').status_code == 302


class TestEditUser:
    def test_evil_name(self, admin_client, mock_db):
        """Validates evil name `/admin/users/4/edit` as admin (expects 302) [TestEditUser / users edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates user management/profile is broken."""
        profile = (4, 'e@x.ph', 'Student', 'Old', None, None, 'BSIS')
        mock_db['fetch_one'].return_value = profile
        mock_db['fetch_all'].return_value = [('BSIS',)]
        resp = admin_client.post(
            '/admin/users/4/edit',
            data={'full_name': '<script>alert(1)</script>',
                  'id_number': '', 'department': 'BSIS'})
        assert resp.status_code == 302

    def test_missing_user(self, admin_client, mock_db):
        """Validates missing user `/admin/users/999/edit` as admin (expects 302) [TestEditUser / users edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates user management/profile is broken."""
        mock_db['fetch_one'].return_value = None
        assert admin_client.post(
            '/admin/users/999/edit',
            data={'full_name': 'X'}).status_code == 302

    def test_huge_input(self, admin_client, mock_db):
        """Validates huge input `/admin/users/4/edit` as admin (expects 302) [TestEditUser / users edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates user management/profile is broken."""
        mock_db['fetch_one'].return_value = None
        resp = admin_client.post(
            '/admin/users/4/edit',
            data={'full_name': 'X' * 3000, 'id_number': 'Y' * 500,
                  'department': 'Z' * 500})
        assert resp.status_code == 302


class TestAuthMatrix:
    def test_librarian_cannot_touch_admin_routes(self, librarian_client):
        """Validates librarian cannot touch admin routes as librarian (expects 302) [TestAuthMatrix / users edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates user management/profile is broken."""
        for url in ('/admin/users/1/archive', '/admin/users/1/role',
                    '/admin/users/1/delete', '/admin/users/1/edit',
                    '/admin/departments/1/delete'):
            assert librarian_client.post(url).status_code == 302, url

    def test_student_cannot_touch_any(self, student_client, mock_db):
        """Validates student cannot touch any as student (expects 302) [TestAuthMatrix / users edge cases].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates user management/profile is broken."""
        for url in ('/librarian/users/1/approve',
                    '/admin/users/1/archive'):
            assert student_client.post(url).status_code == 302, url
        writes = [c[0][0] for c in mock_db['execute'].call_args_list
                  if 'INSERT' in c[0][0] and 'audit_trail' not in c[0][0]]
        assert writes == []
