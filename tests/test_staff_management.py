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

    def test_admin_default_sees_members_like_librarian(self, admin_client, mock_db):
        """Admin entering without an explicit scope (e.g. from the
        librarian dashboard) gets the members listing — never bounced
        to the staff view."""
        _mock_lists(mock_db)
        resp = admin_client.get('/librarian/users')
        assert resp.status_code == 200
        assert b'Stu One' in resp.data
        assert b'Fac One' in resp.data
        assert b'Lib One' not in resp.data
        assert b'Admin One' not in resp.data

    def test_admin_staff_scope(self, admin_client, mock_db):
        """Staff scope shows faculty + librarians only — never students."""
        _mock_lists(mock_db)
        resp = admin_client.get('/librarian/users?scope=staff')
        assert resp.status_code == 200
        assert b'Staff Management' in resp.data
        assert b'Stu One' not in resp.data
        assert b'Fac One' in resp.data
        assert b'Lib One' in resp.data
        assert b'Admin One' not in resp.data

    def test_admin_members_scope(self, admin_client, mock_db):
        _mock_lists(mock_db)
        resp = admin_client.get('/librarian/users?scope=members')
        assert resp.status_code == 200
        assert b'Stu One' in resp.data
        assert b'Lib One' not in resp.data

    def test_invalid_scope_falls_back_to_members(self, admin_client, mock_db):
        _mock_lists(mock_db)
        resp = admin_client.get('/librarian/users?scope=bogus')
        assert resp.status_code == 200
        assert b'Stu One' in resp.data
        assert b'Fac One' in resp.data
        assert b'Lib One' not in resp.data

    def test_explicit_all_scope_shows_everyone(self, admin_client, mock_db):
        _mock_lists(mock_db)
        resp = admin_client.get('/librarian/users?scope=all')
        assert resp.status_code == 200
        assert b'Stu One' in resp.data
        assert b'Lib One' in resp.data
        assert b'Admin One' in resp.data

    def test_admin_default_uses_librarian_sidebar(self, admin_client, mock_db):
        """Admin without explicit scope stays in librarian space."""
        _mock_lists(mock_db)
        body = admin_client.get('/librarian/users').data.decode()
        assert '/admin/audits' not in body
        assert '/admin/settings' not in body
        assert '/admin/backup' not in body

    def test_admin_staff_view_uses_admin_sidebar(self, admin_client, mock_db):
        _mock_lists(mock_db)
        body = admin_client.get('/librarian/users?scope=staff').data.decode()
        assert '/admin/audits' in body


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

    def test_no_scope_tab_buttons(self, admin_client, mock_db):
        """All/Staff/Members tab buttons are removed; scope follows entry links."""
        _mock_lists(mock_db)
        body = admin_client.get('/librarian/users?scope=staff').data.decode()
        assert '>All</a>' not in body
        assert '>Staff</a>' not in body
        assert '>Members</a>' not in body

    def test_faculty_card_on_members_view(self, librarian_client, mock_db):
        _mock_lists(mock_db)
        body = librarian_client.get('/librarian/users').data.decode()
        assert '>Faculty</div>' in body

    def test_no_faculty_card_on_staff_view(self, admin_client, mock_db):
        _mock_lists(mock_db)
        body = admin_client.get('/librarian/users?scope=staff').data.decode()
        assert '>Faculty</div>' not in body
        assert '>Students</div>' not in body

    def test_faculty_role_filter(self, librarian_client, mock_db):
        _mock_lists(mock_db)
        resp = librarian_client.get('/librarian/users?role=Faculty')
        assert resp.status_code == 200
        assert b'Fac One' in resp.data
        assert b'Stu One' not in resp.data
        assert b'ring-2 ring-primary' in resp.data

    def test_students_card_kept_elsewhere(self, admin_client, mock_db):
        _mock_lists(mock_db)
        resp = admin_client.get('/librarian/users')
        assert resp.status_code == 200
        assert b'>Students</div>' in resp.data


class TestActionGating:
    def test_librarian_has_edit_but_no_admin_actions(self, librarian_client, mock_db):
        """Librarians can modify member info, but not roles/statuses."""
        _mock_lists(mock_db)
        resp = librarian_client.get('/librarian/users')
        assert resp.status_code == 200
        assert b'toggle-status' not in resp.data
        assert b'/archive' not in resp.data
        assert b'/delete' not in resp.data
        assert b'Change Role' not in resp.data
        # Edit is available to librarians (members view only).
        assert b'openEditModal' in resp.data
        assert b'id="editModal"' in resp.data
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
        resp = admin_client.get('/librarian/users?scope=staff')
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

    def test_admin_export_default_is_members(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = list(USERS)
        resp = admin_client.get('/librarian/users/export?format=csv')
        assert resp.status_code == 200
        body = resp.data.decode('utf-8-sig')
        assert 'Stu One' in body and 'Fac One' in body
        assert 'Lib One' not in body and 'Admin One' not in body

    def test_admin_export_all_scope(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = list(USERS)
        resp = admin_client.get('/librarian/users/export?scope=all&format=csv')
        assert resp.status_code == 200
        body = resp.data.decode('utf-8-sig')
        assert 'Stu One' in body and 'Admin One' in body


def _many_users(n=45):
    rows = []
    for i in range(n):
        role = 'Student' if i % 2 else 'Faculty'
        rows.append((100 + i, f'u{i}@mcst.edu.ph', f'User {i}', role,
                     'active', datetime(2026, 1, 1), f'ID-{i}', 'Dept'))
    return rows


class TestLibrarianEditRights:
    def test_librarian_can_edit_student(self, librarian_client, mock_db):
        profile = (2, 'f@mcst.edu.ph', 'Student', 'Stu', 9, 'S9', 'BSIS')
        mock_db['fetch_one'].return_value = profile
        resp = librarian_client.post(
            '/admin/users/2/edit',
            data={'full_name': 'Stu New', 'id_number': '',
                  'department': 'BSIS'})
        assert resp.status_code == 302
        updates = [c[0][0] for c in mock_db['execute'].call_args_list
                   if 'UPDATE user_accounts SET full_name' in c[0][0]]
        assert len(updates) == 1

    def test_librarian_can_edit_faculty(self, librarian_client, mock_db):
        profile = (3, 'f@mcst.edu.ph', 'Faculty', 'Fac', 9, 'F9', 'Dept')
        mock_db['fetch_one'].return_value = profile
        resp = librarian_client.post(
            '/admin/users/3/edit',
            data={'full_name': 'Fac New', 'id_number': '',
                  'department': 'Dept'})
        assert resp.status_code == 302

    def test_librarian_cannot_edit_librarian(self, librarian_client, mock_db):
        profile = (4, 'l@mcst.edu.ph', 'Librarian', 'Lib', None, None, None)
        mock_db['fetch_one'].return_value = profile
        before = mock_db['execute'].call_count
        resp = librarian_client.post(
            '/admin/users/4/edit', data={'full_name': 'X'})
        assert resp.status_code == 302
        updates = [c[0][0] for c in mock_db['execute'].call_args_list[before:]
                   if 'UPDATE user_accounts SET full_name' in c[0][0]]
        assert updates == []

    def test_librarian_cannot_edit_admin(self, librarian_client, mock_db):
        profile = (5, 'a@mcst.edu.ph', 'Admin', 'Adm', None, None, None)
        mock_db['fetch_one'].return_value = profile
        before = mock_db['execute'].call_count
        resp = librarian_client.post(
            '/admin/users/5/edit', data={'full_name': 'X'})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == before

    def test_student_cannot_edit_anyone(self, student_client, mock_db):
        resp = student_client.post('/admin/users/2/edit',
                                   data={'full_name': 'X'})
        assert resp.status_code == 302
        assert '/user/profile' in resp.location


class TestUserPagination:
    def test_pager_hidden_on_single_page(self, admin_client, mock_db):
        _mock_lists(mock_db)
        body = admin_client.get('/librarian/users').data.decode()
        assert 'Page 1 of 1' not in body

    def test_pager_shows_on_second_page(self, admin_client, mock_db):
        _mock_lists(mock_db, users=_many_users())
        body = admin_client.get('/librarian/users?page=2').data.decode()
        assert 'Page 2 of ' in body
        assert 'Previous' in body and 'Next' in body

    def test_invalid_page_clamped(self, admin_client, mock_db):
        for url in ('/librarian/users?page=abc',
                    '/librarian/users?page=-3',
                    '/librarian/users?page=999'):
            _mock_lists(mock_db, users=_many_users())
            assert admin_client.get(url).status_code == 200, url

    def test_page_preserves_filters(self, admin_client, mock_db):
        _mock_lists(mock_db, users=_many_users())
        body = admin_client.get(
            '/librarian/users?status=active&page=2').data.decode()
        assert 'status=active' in body


class TestNoCrossDashboardRedirects:
    def test_librarian_page_links_no_admin_dashboard(self, librarian_client,
                                                     mock_db):
        _mock_lists(mock_db)
        body = librarian_client.get('/librarian/users').data.decode()
        assert '/admin' not in body or '/admin/users' in body.replace(
            '/admin/audits', '').replace('/admin/users', '')
        assert 'admin_dashboard' not in body

    def test_admin_page_links_no_librarian_dashboard(self, admin_client,
                                                     mock_db):
        """Admin entering from the librarian side stays in librarian
        space (librarian sidebar, members listing); actions redirect
        back to the shared users page, never to a dashboard."""
        _mock_lists(mock_db)
        body = admin_client.get('/librarian/users').data.decode()
        assert '/admin/audits' not in body
        assert 'Stu One' in body
        mock_db['fetch_one'].return_value = (2, 'f@mcst.edu.ph', 'Faculty',
                                             'Fac')
        resp = admin_client.post('/admin/users/2/archive')
        assert resp.status_code == 302
        assert resp.location.endswith('/librarian/users')
