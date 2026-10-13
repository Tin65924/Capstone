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
        """Validates librarian sees members only `/librarian/users` as librarian (expects 200) [TestScopeFiltering / staff management].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates user management/profile is broken."""
        _mock_lists(mock_db)
        resp = librarian_client.get('/librarian/users')
        assert resp.status_code == 200
        assert b'Stu One' in resp.data
        assert b'Fac One' in resp.data
        assert b'Lib One' in resp.data
        assert b'Admin One' not in resp.data

    def test_librarian_scope_staff_ignored(self, librarian_client, mock_db):
        """Validates librarian scope staff ignored `/librarian/users?scope=staff` as librarian (expects 200) [TestScopeFiltering / staff management].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates user management/profile is broken."""
        _mock_lists(mock_db)
        resp = librarian_client.get('/librarian/users?scope=staff')
        assert resp.status_code == 200
        assert b'Stu One' in resp.data
        assert b'Lib One' in resp.data
        assert b'Admin One' not in resp.data

    def test_admin_default_sees_members_like_librarian(self, admin_client, mock_db):
        """Validates admin default sees members like librarian `/librarian/users` as admin (expects 200) [TestScopeFiltering / staff management].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates user management/profile is broken.

Admin entering without an explicit scope (e.g. from the
        librarian dashboard) gets the members listing — never bounced
        to the staff view."""
        _mock_lists(mock_db)
        resp = admin_client.get('/librarian/users')
        assert resp.status_code == 200
        assert b'Stu One' in resp.data
        assert b'Fac One' in resp.data
        assert b'Lib One' in resp.data
        assert b'Admin One' not in resp.data

    def test_admin_staff_scope(self, admin_client, mock_db):
        """Validates admin staff scope `/librarian/users?scope=staff` as admin (expects 200) [TestScopeFiltering / staff management].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates user management/profile is broken.

Staff scope shows faculty + librarians + admins — never students."""
        _mock_lists(mock_db)
        resp = admin_client.get('/librarian/users?scope=staff')
        assert resp.status_code == 200
        assert b'Staff Management' in resp.data
        assert b'Stu One' not in resp.data
        assert b'Fac One' in resp.data
        assert b'Lib One' in resp.data
        assert b'Admin One' in resp.data

    def test_admin_members_scope(self, admin_client, mock_db):
        """Validates admin members scope `/librarian/users?scope=members` as admin (expects 200) [TestScopeFiltering / staff management].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates user management/profile is broken."""
        _mock_lists(mock_db)
        resp = admin_client.get('/librarian/users?scope=members')
        assert resp.status_code == 200
        assert b'Stu One' in resp.data
        assert b'Lib One' in resp.data
        assert b'Admin One' not in resp.data

    def test_invalid_scope_falls_back_to_members(self, admin_client, mock_db):
        """Validates invalid scope falls back to members `/librarian/users?scope=bogus` as admin (expects 200) [TestScopeFiltering / staff management].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates user management/profile is broken."""
        _mock_lists(mock_db)
        resp = admin_client.get('/librarian/users?scope=bogus')
        assert resp.status_code == 200
        assert b'Stu One' in resp.data
        assert b'Fac One' in resp.data
        assert b'Lib One' in resp.data
        assert b'Admin One' not in resp.data

    def test_explicit_all_scope_shows_everyone(self, admin_client, mock_db):
        """Validates explicit all scope shows everyone `/librarian/users?scope=all` as admin (expects 200) [TestScopeFiltering / staff management].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates user management/profile is broken."""
        _mock_lists(mock_db)
        resp = admin_client.get('/librarian/users?scope=all')
        assert resp.status_code == 200
        assert b'Stu One' in resp.data
        assert b'Lib One' in resp.data
        assert b'Admin One' in resp.data

    def test_admin_default_uses_librarian_sidebar(self, admin_client, mock_db):
        """Validates admin default uses librarian sidebar `/librarian/users` as admin [TestScopeFiltering / staff management].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates user management/profile is broken.

Admin without explicit scope stays in librarian space."""
        _mock_lists(mock_db)
        body = admin_client.get('/librarian/users').data.decode()
        assert '/admin/audits' not in body
        assert '/admin/settings' not in body
        assert '/admin/backup' not in body

    def test_admin_staff_view_uses_admin_sidebar(self, admin_client, mock_db):
        """Validates admin staff view uses admin sidebar `/librarian/users?scope=staff` as admin [TestScopeFiltering / staff management].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates user management/profile is broken."""
        _mock_lists(mock_db)
        body = admin_client.get('/librarian/users?scope=staff').data.decode()
        assert '/admin/audits' in body


class TestStaffScopeSticky:
    """Navigating inside Staff Management must never leak students."""

    def test_staff_plus_status_never_shows_students(self, admin_client, mock_db):
        """Validates staff plus status never shows students as admin (expects 200) [TestStaffScopeSticky / staff management].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates user management/profile is broken."""
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
        """Validates cards and tabs preserve scope `/librarian/users?scope=staff` as admin (expects 200) [TestStaffScopeSticky / staff management].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates user management/profile is broken."""
        _mock_lists(mock_db)
        resp = admin_client.get('/librarian/users?scope=staff')
        assert resp.status_code == 200
        assert b'scope=staff' in resp.data
        # Status tabs keep the staff scope instead of dropping to All.
        assert b'scope=staff&amp;status=' in resp.data or b'scope=staff&status=' in resp.data

    def test_role_student_inside_staff_shows_nobody(self, admin_client, mock_db):
        """Validates role student inside staff shows nobody `/librarian/users?scope=staff&role=Student` as admin (expects 200) [TestStaffScopeSticky / staff management].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates user management/profile is broken."""
        _mock_lists(mock_db)
        resp = admin_client.get('/librarian/users?scope=staff&role=Student')
        assert resp.status_code == 200
        assert b'Stu One' not in resp.data
        assert b'Lib One' not in resp.data

    def test_no_students_card_on_staff_page(self, admin_client, mock_db):
        """Validates no students card on staff page `/librarian/users?scope=staff` as admin (expects 200) [TestStaffScopeSticky / staff management].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates user management/profile is broken."""
        _mock_lists(mock_db)
        resp = admin_client.get('/librarian/users?scope=staff')
        assert resp.status_code == 200
        assert b'>Students</div>' not in resp.data

    def test_no_scope_tab_buttons(self, admin_client, mock_db):
        """Validates no scope tab buttons `/librarian/users?scope=staff` as admin [TestStaffScopeSticky / staff management].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates user management/profile is broken.

All/Staff/Members tab buttons are removed; scope follows entry links."""
        _mock_lists(mock_db)
        body = admin_client.get('/librarian/users?scope=staff').data.decode()
        assert '>All</a>' not in body
        assert '>Staff</a>' not in body
        assert '>Members</a>' not in body

    def test_faculty_card_on_members_view(self, librarian_client, mock_db):
        """Validates faculty card on members view `/librarian/users` as librarian [TestStaffScopeSticky / staff management].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates user management/profile is broken."""
        _mock_lists(mock_db)
        body = librarian_client.get('/librarian/users').data.decode()
        assert '>Faculty</div>' in body

    def test_no_faculty_card_on_staff_view(self, admin_client, mock_db):
        """Validates no faculty card on staff view `/librarian/users?scope=staff` as admin [TestStaffScopeSticky / staff management].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates user management/profile is broken."""
        _mock_lists(mock_db)
        body = admin_client.get('/librarian/users?scope=staff').data.decode()
        assert '>Faculty</div>' not in body
        assert '>Students</div>' not in body

    def test_faculty_role_filter(self, librarian_client, mock_db):
        """Validates faculty role filter `/librarian/users?role=Faculty` as librarian (expects 200) [TestStaffScopeSticky / staff management].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates user management/profile is broken."""
        _mock_lists(mock_db)
        resp = librarian_client.get('/librarian/users?role=Faculty')
        assert resp.status_code == 200
        assert b'Fac One' in resp.data
        assert b'Stu One' not in resp.data
        assert b'ring-2 ring-primary' in resp.data

    def test_students_card_kept_elsewhere(self, admin_client, mock_db):
        """Validates students card kept elsewhere `/librarian/users` as admin (expects 200) [TestStaffScopeSticky / staff management].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates user management/profile is broken."""
        _mock_lists(mock_db)
        resp = admin_client.get('/librarian/users')
        assert resp.status_code == 200
        assert b'>Students</div>' in resp.data


class TestActionGating:
    def test_librarian_has_edit_but_no_admin_actions(self, librarian_client, mock_db):
        """Validates librarian has edit but no admin actions `/librarian/users` as librarian (expects 200) [TestActionGating / staff management].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates user management/profile is broken.

Librarians can modify member info, but not roles/statuses."""
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
        """Validates admin has admin actions `/librarian/users` as admin (expects 200) [TestActionGating / staff management].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates user management/profile is broken."""
        _mock_lists(mock_db)
        resp = admin_client.get('/librarian/users')
        assert resp.status_code == 200
        assert b'toggle-status' in resp.data
        assert b'openEditModal' in resp.data
        assert b'Change Role' in resp.data

    def test_sidebar_librarian(self, librarian_client, mock_db):
        """Validates sidebar librarian `/librarian/users` as librarian [TestActionGating / staff management].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        _mock_lists(mock_db)
        resp = librarian_client.get('/librarian/users')
        assert b'Cataloging' in resp.data

    def test_sidebar_admin(self, admin_client, mock_db):
        """Validates sidebar admin `/librarian/users?scope=staff` as admin [TestActionGating / staff management].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates user management/profile is broken."""
        _mock_lists(mock_db)
        resp = admin_client.get('/librarian/users?scope=staff')
        assert b'/admin/audits' in resp.data


class TestExportScope:
    def test_librarian_export_members_only(self, librarian_client, mock_db):
        """Validates librarian export members only `/librarian/users/export?role=Librarian&format=csv` as librarian (expects 200) [TestExportScope / staff management].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates user management/profile is broken."""
        mock_db['fetch_all'].return_value = list(USERS)
        resp = librarian_client.get('/librarian/users/export?role=Librarian&format=csv')
        assert resp.status_code == 200
        body = resp.data.decode('utf-8-sig')
        assert 'Lib One' in body
        assert 'Admin One' not in body

    def test_admin_export_staff_scope(self, admin_client, mock_db):
        """Validates admin export staff scope `/librarian/users/export?scope=staff&format=csv` as admin (expects 200) [TestExportScope / staff management].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates user management/profile is broken."""
        mock_db['fetch_all'].return_value = list(USERS)
        resp = admin_client.get('/librarian/users/export?scope=staff&format=csv')
        assert resp.status_code == 200
        body = resp.data.decode('utf-8-sig')
        assert 'Stu One' not in body
        assert 'Lib One' in body
        assert 'Fac One' in body
        assert 'Admin One' in body

    def test_admin_export_filename_has_scope(self, admin_client, mock_db):
        """Validates admin export filename has scope `/librarian/users/export?scope=staff&format=csv` as admin [TestExportScope / staff management].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates user management/profile is broken."""
        mock_db['fetch_all'].return_value = list(USERS)
        resp = admin_client.get('/librarian/users/export?scope=staff&format=csv')
        assert 'staff' in resp.headers['Content-Disposition']

    def test_admin_export_default_is_members(self, admin_client, mock_db):
        """Validates admin export default is members `/librarian/users/export?format=csv` as admin (expects 200) [TestExportScope / staff management].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates user management/profile is broken."""
        mock_db['fetch_all'].return_value = list(USERS)
        resp = admin_client.get('/librarian/users/export?format=csv')
        assert resp.status_code == 200
        body = resp.data.decode('utf-8-sig')
        assert 'Stu One' in body and 'Fac One' in body
        assert 'Lib One' in body and 'Admin One' not in body

    def test_admin_export_all_scope(self, admin_client, mock_db):
        """Validates admin export all scope `/librarian/users/export?scope=all&format=csv` as admin (expects 200) [TestExportScope / staff management].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates user management/profile is broken."""
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
        """Validates librarian can edit student `/admin/users/2/edit` as librarian (expects 302) [TestLibrarianEditRights / staff management].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (UPDATE).
    Failure indicates user management/profile is broken."""
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
        """Validates librarian can edit faculty `/admin/users/3/edit` as librarian (expects 302) [TestLibrarianEditRights / staff management].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates user management/profile is broken."""
        profile = (3, 'f@mcst.edu.ph', 'Faculty', 'Fac', 9, 'F9', 'Dept')
        mock_db['fetch_one'].return_value = profile
        resp = librarian_client.post(
            '/admin/users/3/edit',
            data={'full_name': 'Fac New', 'id_number': '',
                  'department': 'Dept'})
        assert resp.status_code == 302

    def test_librarian_cannot_edit_librarian(self, librarian_client, mock_db):
        """Validates librarian cannot edit librarian `/admin/users/4/edit` as librarian (expects 302) [TestLibrarianEditRights / staff management].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (UPDATE).
    Failure indicates user management/profile is broken."""
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
        """Validates librarian cannot edit admin `/admin/users/5/edit` as librarian (expects 302) [TestLibrarianEditRights / staff management].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates user management/profile is broken."""
        profile = (5, 'a@mcst.edu.ph', 'Admin', 'Adm', None, None, None)
        mock_db['fetch_one'].return_value = profile
        before = mock_db['execute'].call_count
        resp = librarian_client.post(
            '/admin/users/5/edit', data={'full_name': 'X'})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == before

    def test_student_cannot_edit_anyone(self, student_client, mock_db):
        """Validates student cannot edit anyone `/admin/users/2/edit` as student (expects 302) [TestLibrarianEditRights / staff management].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates user management/profile is broken."""
        resp = student_client.post('/admin/users/2/edit',
                                   data={'full_name': 'X'})
        assert resp.status_code == 302
        assert '/user/profile' in resp.location


class TestUserPagination:
    def test_pager_hidden_on_single_page(self, admin_client, mock_db):
        """Validates pager hidden on single page `/librarian/users` as admin [TestUserPagination / staff management].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates user management/profile is broken."""
        _mock_lists(mock_db)
        body = admin_client.get('/librarian/users').data.decode()
        assert 'Page 1 of 1' not in body

    def test_pager_shows_on_second_page(self, admin_client, mock_db):
        """Validates pager shows on second page `/librarian/users?page=2` as admin [TestUserPagination / staff management].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates user management/profile is broken."""
        _mock_lists(mock_db, users=_many_users())
        body = admin_client.get('/librarian/users?page=2').data.decode()
        assert 'Page 2 of ' in body
        assert 'Previous' in body and 'Next' in body

    def test_invalid_page_clamped(self, admin_client, mock_db):
        """Validates invalid page clamped as admin (expects 200) [TestUserPagination / staff management].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates user management/profile is broken."""
        for url in ('/librarian/users?page=abc',
                    '/librarian/users?page=-3',
                    '/librarian/users?page=999'):
            _mock_lists(mock_db, users=_many_users())
            assert admin_client.get(url).status_code == 200, url

    def test_page_preserves_filters(self, admin_client, mock_db):
        """Validates page preserves filters `/librarian/users?status=active&page=2` as admin [TestUserPagination / staff management].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates user management/profile is broken."""
        _mock_lists(mock_db, users=_many_users())
        body = admin_client.get(
            '/librarian/users?status=active&page=2').data.decode()
        assert 'status=active' in body


class TestNoCrossDashboardRedirects:
    def test_librarian_page_links_no_admin_dashboard(self, librarian_client,
                                                     mock_db):
        """Validates librarian page links no admin dashboard `/librarian/users` as librarian [TestNoCrossDashboardRedirects / staff management].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates user management/profile is broken."""
        _mock_lists(mock_db)
        body = librarian_client.get('/librarian/users').data.decode()
        assert '/admin' not in body or '/admin/users' in body.replace(
            '/admin/audits', '').replace('/admin/users', '')
        assert 'admin_dashboard' not in body

    def test_admin_page_links_no_librarian_dashboard(self, admin_client,
                                                     mock_db):
        """Validates admin page links no librarian dashboard `/librarian/users` as admin (expects 302) [TestNoCrossDashboardRedirects / staff management].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates user management/profile is broken.

Admin entering from the librarian side stays in librarian
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
