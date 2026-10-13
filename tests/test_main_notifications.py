"""Tests for user notifications, self-service profile updates, and catalog views."""

from datetime import date


class TestUserNotificationsPage:
    def test_notifications_unauthenticated_redirects(self, client):
        """Validates notifications unauthenticated redirects `/user/notifications` (expects 302) [TestUserNotificationsPage / main notifications].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = client.get('/user/notifications')
        assert resp.status_code == 302
        assert '/login' in resp.location

    def test_notifications_student_allowed(self, student_client, mock_db):
        """Validates notifications student allowed `/user/notifications` as student (expects 200) [TestUserNotificationsPage / main notifications].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates notifications are missing or misrouted."""
        mock_db['fetch_one'].return_value = (1, 1, '2024-0001', 'CS', 'active')
        mock_db['fetch_all'].return_value = [
            (1, 'You borrowed copy X.', 'borrow', '10', '2026-08-10 09:00:00', False),
        ]
        resp = student_client.get('/user/notifications')
        assert resp.status_code == 200
        assert b'Notifications' in resp.data
        assert b'You borrowed copy X.' in resp.data

    def test_notifications_no_borrower_renders(self, student_client, mock_db):
        """Validates notifications no borrower renders `/user/notifications` as student (expects 200) [TestUserNotificationsPage / main notifications].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates notifications are missing or misrouted."""
        mock_db['fetch_one'].return_value = None
        resp = student_client.get('/user/notifications')
        assert resp.status_code == 200
        assert b'Notifications' in resp.data


class TestMarkNotificationRead:
    def test_mark_read_redirects_to_next(self, student_client, mock_db):
        """Validates mark read redirects to next `/user/notifications/1/read` as student (expects 302) [TestMarkNotificationRead / main notifications].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (UPDATE).
    Failure indicates notifications are missing or misrouted."""
        mock_db['fetch_one'].return_value = (1, 1, '2024-0001', 'CS', 'active')
        resp = student_client.post('/user/notifications/1/read',
                                   data={'next': '/user/notifications'})
        assert resp.status_code == 302
        assert '/user/notifications' in resp.location
        first = mock_db['execute'].call_args_list[0]
        assert 'UPDATE notification_log' in first[0][0]

    def test_mark_read_rejects_protocol_relative_redirect(self, student_client, mock_db):
        """Validates mark read rejects protocol relative redirect `/user/notifications/1/read` as student (expects 302) [TestMarkNotificationRead / main notifications].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates notifications are missing or misrouted."""
        mock_db['fetch_one'].return_value = (1, 1, '2024-0001', 'CS', 'active')
        resp = student_client.post('/user/notifications/1/read',
                                   data={'next': '//evil.com/phish'})
        assert resp.status_code == 302
        assert 'evil.com' not in resp.location
        assert '/user/profile' in resp.location

    def test_mark_read_rejects_absolute_url(self, student_client, mock_db):
        """Validates mark read rejects absolute url `/user/notifications/1/read?next=https://evil.com` as student (expects 302) [TestMarkNotificationRead / main notifications].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates notifications are missing or misrouted."""
        mock_db['fetch_one'].return_value = (1, 1, '2024-0001', 'CS', 'active')
        resp = student_client.post('/user/notifications/1/read?next=https://evil.com',
                                   data={})
        assert resp.status_code == 302
        assert 'evil.com' not in resp.location
        assert '/user/profile' in resp.location

    def test_mark_all_read(self, student_client, mock_db):
        """Validates mark all read `/user/notifications/read-all` as student (expects 302) [TestMarkNotificationRead / main notifications].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (UPDATE).
    Failure indicates notifications are missing or misrouted."""
        mock_db['fetch_one'].return_value = (1, 1, '2024-0001', 'CS', 'active')
        resp = student_client.post('/user/notifications/read-all',
                                   data={'next': '/user/profile'})
        assert resp.status_code == 302
        assert '/user/profile' in resp.location
        first = mock_db['execute'].call_args_list[0]
        assert 'UPDATE notification_log' in first[0][0]
        assert 'is_read = TRUE' in first[0][0]

    def test_mark_read_no_borrower_writes_nothing(self, student_client, mock_db):
        """Validates mark read no borrower writes nothing `/user/notifications/1/read` as student (expects 302) [TestMarkNotificationRead / main notifications].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates notifications are missing or misrouted."""
        mock_db['fetch_one'].return_value = None
        resp = student_client.post('/user/notifications/1/read', data={})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    JSON = {'Accept': 'application/json'}

    def test_mark_read_json_returns_unread_count(self, student_client, mock_db):
        """Validates mark read json returns unread count `/user/notifications/1/read` as student (expects 200) [TestMarkNotificationRead / main notifications].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates notifications are missing or misrouted."""
        mock_db['fetch_one'].side_effect = [
            (1, 1, '2024-0001', 'CS', 'active'),  # borrower
            (2,),  # count_unread_notifications
        ]
        resp = student_client.post('/user/notifications/1/read', headers=self.JSON)
        assert resp.status_code == 200
        assert resp.get_json() == {'read': 1, 'unread_count': 2}

    def test_mark_all_read_json(self, student_client, mock_db):
        """Validates mark all read json `/user/notifications/read-all` as student (expects 200) [TestMarkNotificationRead / main notifications].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates notifications are missing or misrouted."""
        mock_db['fetch_one'].return_value = (1, 1, '2024-0001', 'CS', 'active')
        resp = student_client.post('/user/notifications/read-all', headers=self.JSON)
        assert resp.status_code == 200
        assert resp.get_json() == {'read_all': True, 'unread_count': 0}

    def test_mark_read_json_no_borrower_404(self, student_client, mock_db):
        """Validates mark read json no borrower 404 `/user/notifications/1/read` as student (expects 404) [TestMarkNotificationRead / main notifications].
    If fails: likely template text/context changed or mock fetch_* shape mismatched; unexpected DB write (validation/pre-check bypassed).
    Failure indicates notifications are missing or misrouted."""
        mock_db['fetch_one'].return_value = None
        resp = student_client.post('/user/notifications/1/read', headers=self.JSON)
        assert resp.status_code == 404
        assert 'error' in resp.get_json()
        assert mock_db['execute'].call_count == 0

    def test_notifications_page_has_ajax_hooks(self, student_client, mock_db):
        """Validates notifications page has ajax hooks `/user/notifications` as student (expects 200) [TestMarkNotificationRead / main notifications].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates notifications are missing or misrouted."""
        mock_db['fetch_one'].return_value = (1, 1, '2024-0001', 'CS', 'active')
        mock_db['fetch_all'].return_value = [
            (1, 'You borrowed copy X.', 'borrow', '10', '2026-08-10 09:00:00', False),
        ]
        resp = student_client.get('/user/notifications')
        assert resp.status_code == 200
        assert b'data-notif-read=' in resp.data
        assert b'data-notif-card=' in resp.data
        assert b'js/ajax_ui.js' in resp.data


class TestUpdateProfile:
    PROFILE = (1, 'student@mcst.edu.ph', 'Student', 'Test Student',
               1, '2024-0001', 'CS', None, 'active')

    def test_update_profile_success(self, student_client, mock_db):
        """Validates update profile success `/user/profile/update` as student (expects 302) [TestUpdateProfile / main notifications].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (UPDATE).
    Failure indicates notifications are missing or misrouted."""
        mock_db['fetch_one'].return_value = self.PROFILE
        resp = student_client.post('/user/profile/update', data={
            'full_name': 'New Name',
            'phone_number': '+63 912 345 6789',
            'department': 'BSIS',
        })
        assert resp.status_code == 302
        assert '/user/profile' in resp.location
        first = mock_db['execute'].call_args_list[0]
        assert 'UPDATE user_accounts' in first[0][0]
        assert first[0][1][0] == 'New Name'

    def test_update_profile_rejects_unknown_department(self, student_client, mock_db):
        """Validates update profile rejects unknown department `/user/profile/update` as student (expects 302) [TestUpdateProfile / main notifications].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates notifications are missing or misrouted."""
        mock_db['fetch_one'].side_effect = lambda q, p=None: self.PROFILE if 'FROM user_accounts' in q else None
        resp = student_client.post('/user/profile/update', data={
            'full_name': 'New Name',
            'department': 'Made Up Program',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_update_profile_allows_unchanged_legacy(self, student_client, mock_db):
        """Validates update profile allows unchanged legacy `/user/profile/update` as student (expects 302) [TestUpdateProfile / main notifications].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates notifications are missing or misrouted."""
        mock_db['fetch_one'].return_value = self.PROFILE
        resp = student_client.post('/user/profile/update', data={
            'full_name': 'New Name',
            'department': 'CS',  # unchanged legacy value skips validation
        })
        assert resp.status_code == 302
        # update_user_accounts + update_borrowers + log_activity
        assert mock_db['execute'].call_count == 3

    def test_update_profile_staff_rejects_unknown(self, student_client, mock_db):
        """Validates update profile staff rejects unknown `/user/profile/update` as student (expects 302) [TestUpdateProfile / main notifications].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates notifications are missing or misrouted."""
        staff_profile = (2, 'b@mcst.edu.ph', 'Admin', 'Boss', 9, 'A-1', 'Old Dept', None, 'active')
        mock_db['fetch_one'].side_effect = lambda q, p=None: staff_profile if 'FROM user_accounts' in q else None
        resp = student_client.post('/user/profile/update', data={
            'full_name': 'Boss',
            'department': 'Junk Dept',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_update_profile_rejects_id_change(self, student_client, mock_db):
        """Validates update profile rejects id change `/user/profile/update` as student (expects 302) [TestUpdateProfile / main notifications].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates notifications are missing or misrouted."""
        resp = student_client.post('/user/profile/update', data={
            'full_name': 'New Name',
            'id_number': '9999-0000',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0
        assert mock_db['fetch_one'].call_count == 0

    def test_update_profile_rejects_bad_phone(self, student_client, mock_db):
        """Validates update profile rejects bad phone `/user/profile/update` as student (expects 302) [TestUpdateProfile / main notifications].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates notifications are missing or misrouted."""
        resp = student_client.post('/user/profile/update', data={
            'full_name': 'New Name',
            'phone_number': 'not-a-phone!!!',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_update_profile_requires_name(self, student_client, mock_db):
        """Validates update profile requires name `/user/profile/update` as student (expects 302) [TestUpdateProfile / main notifications].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates notifications are missing or misrouted."""
        resp = student_client.post('/user/profile/update', data={'full_name': ''})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0


class TestHistoryNewSections:
    def test_history_shows_tabs_without_notifications(self, student_client, mock_db):
        """Validates history shows tabs without notifications `/user/history` as student (expects 200) [TestHistoryNewSections / main notifications].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates notifications are missing or misrouted."""
        mock_db['fetch_one'].return_value = (1, 1, '2024-0001', 'CS', 'active')
        mock_db['fetch_all'].return_value = []
        resp = student_client.get('/user/history')
        assert resp.status_code == 200
        assert b'Fines' in resp.data
        assert b'Reservation History' in resp.data
        assert b'Book Requests' in resp.data
        assert b'Notification History' not in resp.data


class TestFineGraceDays:
    def test_grace_days_reduce_fine(self, mock_db):
        """Validates grace days reduce fine [TestFineGraceDays / main notifications].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates notifications are missing or misrouted."""
        from app.circulation.models import calculate_fine
        mock_db['fetch_one'].return_value = (date(2026, 7, 1), date(2026, 7, 6), 'overnight')
        assert calculate_fine(55, 10.0, 2) == 30.0

    def test_grace_days_floor_at_zero(self, mock_db):
        """Validates grace days floor at zero [TestFineGraceDays / main notifications].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates notifications are missing or misrouted."""
        from app.circulation.models import calculate_fine
        mock_db['fetch_one'].return_value = (date(2026, 7, 1), date(2026, 7, 2), 'overnight')
        assert calculate_fine(55, 10.0, 5) == 0

    def test_default_rate_is_five_pesos(self, mock_db):
        """Validates default rate is five pesos [TestFineGraceDays / main notifications].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates notifications are missing or misrouted."""
        from app.circulation.models import calculate_fine
        mock_db['fetch_one'].return_value = (date(2026, 7, 1), date(2026, 7, 3), 'overnight')
        assert calculate_fine(55) == 10.0

    def test_daily_loans_never_accrue_fines(self, mock_db):
        """Validates daily loans never accrue fines [TestFineGraceDays / main notifications].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates notifications are missing or misrouted."""
        from app.circulation.models import calculate_fine
        mock_db['fetch_one'].return_value = (date(2026, 7, 1), date(2026, 7, 20), 'daily_circulation')
        assert calculate_fine(55, 5.0, 0) == 0


class TestCatalogViews:
    BOOKS = [
        (1, 'Introduction to Algorithms', 'Cormen', '3rd', 'MIT Press', 2022,
         'Computer Science', 'QA76.73', '978-0262033848', 'Book',
         'A comprehensive textbook.', 'active', '2024-01-15', '2025-0001'),
    ]

    def test_list_view_renders(self, client, mock_db):
        """Validates list view renders `/catalog?q=test&view=list` (expects 200) [TestCatalogViews / main notifications].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates notifications are missing or misrouted."""
        mock_db['fetch_all'].side_effect = [self.BOOKS, []]
        resp = client.get('/catalog?q=test&view=list')
        assert resp.status_code == 200
        assert b'id="catalog-results-list"' in resp.data
        assert b'Introduction to Algorithms' in resp.data

    def test_invalid_view_falls_back_to_grid(self, client, mock_db):
        """Validates invalid view falls back to grid `/catalog?q=test&view=bogus` (expects 200) [TestCatalogViews / main notifications].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates notifications are missing or misrouted."""
        mock_db['fetch_all'].side_effect = [self.BOOKS, []]
        resp = client.get('/catalog?q=test&view=bogus')
        assert resp.status_code == 200
        assert b'id="catalog-results-grid"' in resp.data
        assert b'id="catalog-results-list"' not in resp.data
