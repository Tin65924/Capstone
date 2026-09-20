"""Tests for Staff vs Member split on /librarian/users and export."""

from datetime import datetime

USERS = [
    (1, 's@mcst.edu.ph', 'Stu One', 'Student', 'active', datetime(2026, 1, 1), '2024-1', 'BSIS'),
    (2, 'f@mcst.edu.ph', 'Fac One', 'Faculty', 'active', datetime(2026, 1, 1), '2024-2', 'Dept'),
    (3, 'l@mcst.edu.ph', 'Lib One', 'Librarian', 'active', datetime(2026, 1, 1), 'L-1', 'Library'),
    (4, 'a@mcst.edu.ph', 'Admin One', 'Admin', 'active', datetime(2026, 1, 1), 'A-1', 'Admin'),
]
PENDING = [
    (5, 'f2@mcst.edu.ph', 'Fac Pending', 'Faculty', datetime(2026, 1, 2), '2024-9', 'Dept'),
]
ROLES = [(1, 'Student'), (2, 'Faculty'), (3, 'Librarian'), (4, 'Admin')]


def _mock_lists(mock_db, users=None, pending=None):
    mock_db['fetch_all'].side_effect = [
        list(users if users is not None else USERS),  # get_all_users
        list(pending if pending is not None else PENDING),  # get_pending_users
        list(ROLES),  # get_roles
        [],  # programs
        [],  # departments
    ]


class TestScopeFiltering:
    def test_librarian_sees_members_only(self, librarian_client, mock_db):
        _mock_lists(mock_db)
        resp = librarian_client.get('/librarian/users')
        assert resp.status_code == 200
        assert b'Stu One' in resp.data
        assert b'Fac One' in resp.data
        assert b'Lib One' not in resp.data
        assert b'Admin One' not in resp.data

    def test_librarian_scope_staff_ignored(self, librarian_client, mock_db):
        _mock_lists(mock_db)
        resp = librarian_client.get('/librarian/users?scope=staff')
        assert resp.status_code == 200
        assert b'Stu One' in resp.data
        assert b'Lib One' not in resp.data

    def test_admin_default_sees_all(self, admin_client, mock_db):
        _mock_lists(mock_db)
        resp = admin_client.get('/librarian/users')
        assert resp.status_code == 200
        assert b'Stu One' in resp.data
        assert b'Lib One' in resp.data
        assert b'Admin One' in resp.data

    def test_admin_staff_scope(self, admin_client, mock_db):
        _mock_lists(mock_db)
        resp = admin_client.get('/librarian/users?scope=staff')
        assert resp.status_code == 200
        assert b'Staff Management' in resp.data
        assert b'Stu One' not in resp.data
        assert b'Fac One' in resp.data
        assert b'Lib One' in resp.data
        assert b'Admin One' in resp.data

    def test_admin_members_scope(self, admin_client, mock_db):
        _mock_lists(mock_db)
        resp = admin_client.get('/librarian/users?scope=members')
        assert resp.status_code == 200
        assert b'Stu One' in resp.data
        assert b'Lib One' not in resp.data

    def test_invalid_scope_falls_back_to_all(self, admin_client, mock_db):
        _mock_lists(mock_db)
        resp = admin_client.get('/librarian/users?scope=bogus')
        assert resp.status_code == 200
        assert b'Stu One' in resp.data
        assert b'Lib One' in resp.data


class TestStaffScopeSticky:
    """Navigating inside Staff Management must never leak students."""

    def test_staff_plus_status_never_shows_students(self, admin_client, mock_db):
        from datetime import datetime
        users = [
            (1, 's@mcst.edu.ph', 'Stu One', 'Student', 'active', datetime(2026, 1, 1), '2024-1', 'BSIS'),
            (2, 's2@mcst.edu.ph', 'Stu Two', 'Student', 'disabled', datetime(2026, 1, 1), '2024-2', 'BSN'),
            (3, 'l@mcst.edu.ph', 'Lib One', 'Librarian', 'active', datetime(2026, 1, 1), 'L-1', 'Library'),
            (4, 'a@mcst.edu.ph', 'Admin One', 'Admin', 'archived', datetime(2026, 1, 1), 'A-1', 'Admin'),
        ]
        for status in ('active', 'disabled', 'archived', 'pending'):
            _mock_lists(mock_db, users=users)
            resp = admin_client.get(f'/librarian/users?scope=staff&status={status}')
            assert resp.status_code == 200
            assert b'Stu One' not in resp.data
            assert b'Stu Two' not in resp.data

    def test_cards_and_tabs_preserve_scope(self, admin_client, mock_db):
        _mock_lists(mock_db)
        resp = admin_client.get('/librarian/users?scope=staff')
        assert resp.status_code == 200
        assert b'scope=staff' in resp.data
        # Status tabs keep the staff scope instead of dropping to All.
        assert b'scope=staff&amp;status=' in resp.data or b'scope=staff&status=' in resp.data

    def test_role_student_inside_staff_shows_nobody(self, admin_client, mock_db):
        _mock_lists(mock_db)
        resp = admin_client.get('/librarian/users?scope=staff&role=Student')
        assert resp.status_code == 200
        assert b'Stu One' not in resp.data
        assert b'Lib One' not in resp.data

    def test_no_students_card_on_staff_page(self, admin_client, mock_db):
        _mock_lists(mock_db)
        resp = admin_client.get('/librarian/users?scope=staff')
        assert resp.status_code == 200
        assert b'>Students</div>' not in resp.data

    def test_students_card_kept_elsewhere(self, admin_client, mock_db):
        _mock_lists(mock_db)
        resp = admin_client.get('/librarian/users')
        assert resp.status_code == 200
        assert b'>Students</div>' in resp.data


class TestActionGating:
    def test_librarian_has_no_admin_actions(self, librarian_client, mock_db):
        _mock_lists(mock_db)
        resp = librarian_client.get('/librarian/users')
        assert resp.status_code == 200
        assert b'toggle-status' not in resp.data
        assert b'/archive' not in resp.data
        assert b'/delete' not in resp.data
        assert b'openEditModal' not in resp.data
        assert b'Change Role' not in resp.data
        # Librarians keep approve + history + export.
        assert b'approve' in resp.data
        assert b'history' in resp.data.lower()

    def test_admin_has_admin_actions(self, admin_client, mock_db):
        _mock_lists(mock_db)
        resp = admin_client.get('/librarian/users')
        assert resp.status_code == 200
        assert b'toggle-status' in resp.data
        assert b'openEditModal' in resp.data
        assert b'Change Role' in resp.data

    def test_sidebar_librarian(self, librarian_client, mock_db):
        _mock_lists(mock_db)
        resp = librarian_client.get('/librarian/users')
        assert b'Cataloging' in resp.data

    def test_sidebar_admin(self, admin_client, mock_db):
        _mock_lists(mock_db)
        resp = admin_client.get('/librarian/users')
        assert b'/admin/audits' in resp.data


class TestExportScope:
    def test_librarian_export_members_only(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = list(USERS)
        resp = librarian_client.get('/librarian/users/export?role=Librarian&format=csv')
        assert resp.status_code == 200
        body = resp.data.decode('utf-8-sig')
        assert 'Lib One' not in body

    def test_admin_export_staff_scope(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = list(USERS)
        resp = admin_client.get('/librarian/users/export?scope=staff&format=csv')
        assert resp.status_code == 200
        body = resp.data.decode('utf-8-sig')
        assert 'Stu One' not in body
        assert 'Lib One' in body
        assert 'Fac One' in body

    def test_admin_export_filename_has_scope(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = list(USERS)
        resp = admin_client.get('/librarian/users/export?scope=staff&format=csv')
        assert 'staff' in resp.headers['Content-Disposition']
