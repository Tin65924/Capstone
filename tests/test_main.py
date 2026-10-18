"""Tests for main routes: landing page, dashboard, user profile, history."""


class TestLandingPage:
    def test_index_public(self, client, mock_db):
        """Validates index public `/` (expects 200) [TestLandingPage / main].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates main is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_all'].return_value = []
        resp = client.get('/')
        assert resp.status_code == 200
        assert b'MCST' in resp.data or b'library' in resp.data.lower() or b'Library' in resp.data

    def test_index_shows_new_arrivals(self, client, mock_db):
        """Validates index shows new arrivals `/` (expects 200) [TestLandingPage / main].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates main is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_all'].return_value = [
            (1, 'New Book Title', 'Author Name', None, None, 2025,
             None, None, None, 'Book', None, 'active', '2025-01-01'),
        ]
        resp = client.get('/')
        assert resp.status_code == 200
        assert b'New Book Title' in resp.data or b'New' in resp.data

    def test_index_side_browse_card_and_open_status(self, client, mock_db):
        """Browse by Book Type renders as a sidebar card next to the
        open/closed status pill drawn from library settings
        [TestLandingPage / main].
    If fails: the side layout or the settings-derived open label broke."""
        mock_db['fetch_all'].side_effect = [
            [],                        # get_recent_books
            [('Book', 2), ('E-Book', 1)],  # get_distinct_material_types
        ]
        resp = client.get('/')
        assert resp.status_code == 200
        body = resp.data.decode()
        assert 'Browse by Book Type' in body
        assert 'material_type=E-Book' in body
        # Status label from Library Hours / Operations Schedule settings
        # (test config has none -> fail-open "Open now").
        assert 'Open now' in body
        assert 'No hour restrictions set' in body

    def test_index_open_status_uses_configured_hours(self, client, mock_db):
        """With hours + open days configured the status comes from them
        [TestLandingPage / main].
    If fails: the label would ignore the librarian's settings."""
        from flask import current_app
        app = client.application
        saved = {k: app.config.get(k) for k in (
            'LIBRARY_OPENING_TIME', 'LIBRARY_CLOSING_TIME',
            'LIBRARY_OPEN_DAYS', 'LIBRARY_MONTH_DAYS',
            'MAX_BORROW_LIMIT_STUDENT')}
        app.config.update({
            'LIBRARY_OPENING_TIME': '08:00',
            'LIBRARY_CLOSING_TIME': '17:00',
            'LIBRARY_OPEN_DAYS': 'Monday,Tuesday,Wednesday,Thursday,Friday,Saturday',
        })
        app.config.pop('LIBRARY_MONTH_DAYS', None)
        try:
            mock_db['fetch_all'].side_effect = [[], []]
            body = client.get('/').data.decode()
            assert 'Library hours:' in body
            assert '8:00 AM' in body
            # Either state may show depending on wall clock; the label is
            # always one of the two configured-hour forms.
            assert ('Open now' in body) or ('Closed' in body)
        finally:
            for k, v in saved.items():
                if v is None:
                    app.config.pop(k, None)
                else:
                    app.config[k] = v


class TestDashboard:
    def test_dashboard_unauthenticated_redirects(self, client):
        """Validates dashboard unauthenticated redirects `/dashboard` (expects 302) [TestDashboard / main].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = client.get('/dashboard')
        assert resp.status_code == 302
        assert '/login' in resp.location

    def test_dashboard_redirects_student_to_profile(self, student_client):
        """Validates dashboard redirects student to profile `/dashboard` as student (expects 302) [TestDashboard / main].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates main is broken for this case (users see wrong page, blocked action, or bad data)."""
        resp = student_client.get('/dashboard')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_dashboard_redirects_faculty_to_profile(self, faculty_client):
        """Validates dashboard redirects faculty to profile `/dashboard` as faculty (expects 302) [TestDashboard / main].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates main is broken for this case (users see wrong page, blocked action, or bad data)."""
        resp = faculty_client.get('/dashboard')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_dashboard_redirects_librarian_to_profile(self, librarian_client):
        """Validates dashboard redirects librarian to profile `/dashboard` as librarian (expects 302) [TestDashboard / main].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates main is broken for this case (users see wrong page, blocked action, or bad data)."""
        resp = librarian_client.get('/dashboard')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_dashboard_redirects_admin_to_profile(self, admin_client):
        """Validates dashboard redirects admin to profile `/dashboard` as admin (expects 302) [TestDashboard / main].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates main is broken for this case (users see wrong page, blocked action, or bad data)."""
        resp = admin_client.get('/dashboard')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location


class TestUserProfile:
    def test_profile_unauthenticated_redirects(self, client):
        """Validates profile unauthenticated redirects `/user/profile` (expects 302) [TestUserProfile / main].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = client.get('/user/profile')
        assert resp.status_code == 302
        assert '/login' in resp.location

    def test_profile_student_allowed(self, student_client, mock_db):
        """Validates profile student allowed `/user/profile` as student (expects 200) [TestUserProfile / main].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates main is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].return_value = (1, 'student@mcst.edu.ph', 'Student', 'Test Student')
        resp = student_client.get('/user/profile')
        assert resp.status_code == 200

    def test_profile_faculty_allowed(self, faculty_client, mock_db):
        """Validates profile faculty allowed `/user/profile` as faculty (expects 200) [TestUserProfile / main].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates main is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].return_value = (2, 'faculty@mcst.edu.ph', 'Faculty', 'Test Faculty')
        resp = faculty_client.get('/user/profile')
        assert resp.status_code == 200

    def test_profile_librarian_allowed(self, librarian_client, mock_db):
        """Validates profile librarian allowed `/user/profile` as librarian (expects 200) [TestUserProfile / main].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates main is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].return_value = (3, 'librarian@mcst.edu.ph', 'Librarian', 'Test Librarian')
        resp = librarian_client.get('/user/profile')
        assert resp.status_code == 200

    def test_profile_admin_allowed(self, admin_client, mock_db):
        """Validates profile admin allowed `/user/profile` as admin (expects 200) [TestUserProfile / main].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates main is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].return_value = (4, 'admin@mcst.edu.ph', 'Admin', 'Test Admin')
        resp = admin_client.get('/user/profile')
        assert resp.status_code == 200

    def test_profile_does_not_show_admin_tools(self, admin_client, mock_db):
        """Validates profile does not show admin tools `/user/profile` as admin [TestUserProfile / main].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].return_value = (4, 'admin@mcst.edu.ph', 'Admin', 'Test Admin')
        resp = admin_client.get('/user/profile')
        assert b'Backup' not in resp.data
        assert b'Cataloging' not in resp.data

    def test_profile_shows_admin_dashboard_button(self, admin_client, mock_db):
        """Validates profile shows admin dashboard button `/user/profile` as admin [TestUserProfile / main].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates main is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].return_value = (4, 'admin@mcst.edu.ph', 'Admin', 'Test Admin')
        resp = admin_client.get('/user/profile')
        assert b'Admin Dashboard' in resp.data
        assert b'Librarian Dashboard' in resp.data

    def test_profile_shows_librarian_dashboard_button(self, librarian_client, mock_db):
        """Validates profile shows librarian dashboard button `/user/profile` as librarian [TestUserProfile / main].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates main is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].return_value = (3, 'librarian@mcst.edu.ph', 'Librarian', 'Test Librarian')
        resp = librarian_client.get('/user/profile')
        assert b'Librarian Dashboard' in resp.data
        assert b'Admin Dashboard' not in resp.data

    def test_profile_student_has_no_dashboard_buttons(self, student_client, mock_db):
        """Validates profile student has no dashboard buttons `/user/profile` as student [TestUserProfile / main].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates main is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].return_value = (1, 'student@mcst.edu.ph', 'Student', 'Test Student')
        resp = student_client.get('/user/profile')
        assert b'Admin Dashboard' not in resp.data
        assert b'Librarian Dashboard' not in resp.data


class TestUserHistory:
    def test_history_unauthenticated_redirects(self, client):
        """Validates history unauthenticated redirects `/user/history` (expects 302) [TestUserHistory / main].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = client.get('/user/history')
        assert resp.status_code == 302
        assert '/login' in resp.location

    def test_history_authenticated_allowed(self, student_client):
        """Validates history authenticated allowed `/user/history` as student (expects 200) [TestUserHistory / main].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates main is broken for this case (users see wrong page, blocked action, or bad data)."""
        resp = student_client.get('/user/history')
        assert resp.status_code == 200

    def test_history_admin_allowed(self, admin_client):
        """Validates history admin allowed `/user/history` as admin (expects 200) [TestUserHistory / main].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates main is broken for this case (users see wrong page, blocked action, or bad data)."""
        resp = admin_client.get('/user/history')
        assert resp.status_code == 200


class TestRoleDashboards:
    def test_librarian_dashboard_librarian_allowed(self, librarian_client, mock_db):
        """Validates librarian dashboard librarian allowed `/librarian` as librarian (expects 200) [TestRoleDashboards / main].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates main is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian')
        assert resp.status_code == 200

    def test_librarian_dashboard_admin_allowed(self, admin_client, mock_db):
        """Validates librarian dashboard admin allowed `/librarian` as admin (expects 200) [TestRoleDashboards / main].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates main is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_all'].return_value = []
        resp = admin_client.get('/librarian')
        assert resp.status_code == 200
        assert b'Admin Dashboard' in resp.data

    def test_librarian_dashboard_student_forbidden(self, student_client):
        """Validates librarian dashboard student forbidden `/librarian` as student (expects 302) [TestRoleDashboards / main].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates main is broken for this case (users see wrong page, blocked action, or bad data)."""
        resp = student_client.get('/librarian')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_admin_dashboard_admin_allowed(self, admin_client, mock_db):
        """Validates admin dashboard admin allowed `/admin` as admin (expects 200) [TestRoleDashboards / main].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates main is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_all'].return_value = []
        resp = admin_client.get('/admin')
        assert resp.status_code == 200

    def test_admin_dashboard_librarian_forbidden(self, librarian_client):
        """Validates admin dashboard librarian forbidden `/admin` as librarian (expects 302) [TestRoleDashboards / main].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates main is broken for this case (users see wrong page, blocked action, or bad data)."""
        resp = librarian_client.get('/admin')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_admin_dashboard_student_forbidden(self, student_client):
        """Validates admin dashboard student forbidden `/admin` as student (expects 302) [TestRoleDashboards / main].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates main is broken for this case (users see wrong page, blocked action, or bad data)."""
        resp = student_client.get('/admin')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_admin_dashboard_unauthenticated_redirects(self, client):
        """Validates admin dashboard unauthenticated redirects `/admin` (expects 302) [TestRoleDashboards / main].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = client.get('/admin')
        assert resp.status_code == 302
        assert '/login' in resp.location


class TestDashboardAttention:
    PENDING = [(1, 'a@mcst.edu.ph', 'Pending User', 'Student', '2026-01-01', '1', 'CS')]
    GROUPS = [(1, 'T', 'A', 10, 3, 2, 0, 0)]

    def test_attention_counts(self, mock_db):
        """Validates attention counts [TestDashboardAttention / main].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates main is broken for this case (users see wrong page, blocked action, or bad data)."""
        from app.main.models import get_attention_summary
        mock_db['fetch_one'].side_effect = [(10,), (3,), (1,)]
        mock_db['fetch_all'].side_effect = [self.PENDING, self.GROUPS]
        assert get_attention_summary() == {
            'overdue_items': 3, 'due_soon': 1,
            'pending_users': 1, 'waiting_reservations': 5,
        }

    def test_dashboard_stats_extended(self, mock_db):
        """Validates dashboard stats extended [TestDashboardAttention / main].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates main is broken for this case (users see wrong page, blocked action, or bad data)."""
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
        """Validates waiting reservations skips bad rows [TestDashboardAttention / main].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates main is broken for this case (users see wrong page, blocked action, or bad data)."""
        from app.main.models import count_waiting_reservations
        mock_db['fetch_all'].return_value = [
            (1, 'T', 'A', 10, 3, 2, 0, 0), ('short',), (1, 'T', 'A', 1, 'x', 0, 0, 0),
        ]
        assert count_waiting_reservations() == 5

    def test_stats_bypassed_without_app_context(self, mock_db):
        """Validates stats bypassed without app context [TestDashboardAttention / main].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates main is broken for this case (users see wrong page, blocked action, or bad data).

Direct model calls (no app context) always hit the DB so unit
        tests stay deterministic and never leak cached values."""
        from app.main.models import get_dashboard_stats
        mock_db['fetch_one'].side_effect = [(100,), (250,), (10,), (4,), (3,)]
        mock_db['fetch_all'].side_effect = [self.GROUPS, [], [(7,)]]
        first = get_dashboard_stats()
        mock_db['fetch_one'].side_effect = [(1,), (2,), (3,), (4,), (5,)]
        mock_db['fetch_all'].side_effect = [self.GROUPS, [], [(7,)]]
        second = get_dashboard_stats()
        assert first['total_titles'] == 100
        assert second['total_titles'] == 1

    def test_stats_cached_in_requests(self, app, mock_db):
        """Validates stats cached in requests [TestDashboardAttention / main].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates main is broken for this case (users see wrong page, blocked action, or bad data).

Inside a non-testing request the second call is served from
        cache (no extra DB hits) until cleared."""
        from app.main.models import get_dashboard_stats, clear_stats_cache
        clear_stats_cache()
        mock_db['fetch_one'].side_effect = [(100,), (250,), (10,), (4,), (3,)]
        mock_db['fetch_all'].side_effect = [self.GROUPS, [], [(7,)]]
        old_testing = app.config.get('TESTING')
        app.config['TESTING'] = False
        try:
            with app.app_context():
                first = get_dashboard_stats()
                calls_after_first = mock_db['fetch_one'].call_count
                second = get_dashboard_stats()
                assert second == first
                assert mock_db['fetch_one'].call_count == calls_after_first
                clear_stats_cache()
                mock_db['fetch_one'].side_effect = [(7,), (8,), (9,), (10,), (11,)]
                mock_db['fetch_all'].side_effect = [self.GROUPS, [], [(7,)]]
                third = get_dashboard_stats()
                assert third['total_titles'] == 7
        finally:
            app.config['TESTING'] = old_testing
            clear_stats_cache()

    def test_librarian_dashboard_shows_panel(self, librarian_client, mock_db):
        """Validates librarian dashboard shows panel `/librarian` as librarian (expects 200) [TestDashboardAttention / main].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates main is broken for this case (users see wrong page, blocked action, or bad data)."""
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
        """Validates dashboard all clear state `/librarian` as librarian (expects 200) [TestDashboardAttention / main].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates main is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian')
        assert resp.status_code == 200
        assert b'All clear' in resp.data

    def test_admin_dashboard_shows_panel(self, admin_client, mock_db):
        """Validates admin dashboard shows panel `/admin` as admin (expects 200) [TestDashboardAttention / main].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates main is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        resp = admin_client.get('/admin')
        assert resp.status_code == 200
        assert b'Needs Attention' in resp.data
