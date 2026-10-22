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
    If fails: likely template text/context changed or mock data mismatch.
    Failure indicates notifications are missing or misrouted."""
        mock_db['fetch_all'].side_effect = [self.BOOKS, []]
        resp = client.get('/catalog?q=test&view=bogus')
        assert resp.status_code == 200
        assert b'id="catalog-results-grid"' in resp.data
        assert b'id="catalog-results-list"' not in resp.data


class TestNotifPanel:
    """Bell dropdown panel for all roles (replaces bottom-right toasts)."""

    def test_toast_poller_removed(self, student_client, mock_db):
        """Validates toast poller removed `/user/profile` as student (expects 200) [TestNotifPanel / main notifications].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates notifications are missing or misrouted."""
        mock_db['fetch_one'].return_value = (1, 'student@mcst.edu.ph', 'Student', 'Test Student')
        body = student_client.get('/user/profile').data.decode()
        assert '__mcstLiveToasts' not in body
        assert 'mcst_seen_notifs_v1' not in body
        assert 'setInterval(check, 15000)' not in body

    def test_member_panel_wired(self, student_client, mock_db):
        """Validates member panel wired `/` as student (expects 200) [TestNotifPanel / main notifications].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates notifications are missing or misrouted."""
        mock_db['fetch_all'].return_value = []
        body = student_client.get('/').data.decode()
        assert 'data-notif-root' in body
        assert 'data-feed-url="/api/notifications"' in body
        assert 'data-view-all="/user/notifications"' in body
        assert 'Mark all as read' in body
        # Exactly one badge element lives on the home bell (panel JS
        # references the attribute twice more in code).
        assert body.count('data-notif-badge class=') == 1

    def test_profile_sidebar_is_plain_link(self, student_client, mock_db):
        """Validates profile sidebar is plain link `/user/profile` as student (expects 200) [TestNotifPanel / main notifications].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates notifications are missing or misrouted."""
        mock_db['fetch_one'].return_value = (1, 'student@mcst.edu.ph', 'Student', 'Test Student')
        body = student_client.get('/user/profile').data.decode()
        assert 'data-notif-root' not in body
        assert 'href="/user/notifications"' in body

    def test_staff_dashboards_have_no_bell(self, librarian_client, admin_client, mock_db):
        """Validates staff dashboards have no bell `/librarian` as librarian (expects 200) [TestNotifPanel / main notifications].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates notifications are missing or misrouted."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        assert 'data-notif-root' not in librarian_client.get('/librarian').data.decode()
        assert 'data-notif-root' not in admin_client.get('/admin').data.decode()

    def test_feed_member_payload(self, student_client, mock_db):
        """Validates feed member payload `/api/notifications` as student (expects 200) [TestNotifPanel / main notifications].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates notifications are missing or misrouted."""
        mock_db['fetch_one'].side_effect = [
            (7, 1, 'S1', 'BSIS', '0917', 'active', None, None),
            (2,),
        ]
        mock_db['fetch_all'].return_value = [
            (1, 'Hello & <world>', 'request_update', '5', '2026-08-10 09:00:00', False),
        ]
        resp = student_client.get('/api/notifications')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['unread_count'] == 2
        assert len(data['notifications']) == 1
        item = data['notifications'][0]
        assert item['id'] == 1
        assert item['message'] == 'Hello & <world>'
        assert item['type'] == 'request_update'
        assert item['date'] == '2026-08-10 05:00 PM (PHT)'
        assert item['read'] is False
        assert item['url'] == '/user/request-book'

    def test_feed_member_urls_per_type(self, student_client, mock_db):
        """Validates feed member urls per type `/api/notifications` as student (expects 200) [TestNotifPanel / main notifications].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates notifications are missing or misrouted."""
        mock_db['fetch_one'].side_effect = [
            (7, 1, 'S1', 'BSIS', '0917', 'active', None, None),
            (0,),
        ]
        mock_db['fetch_all'].return_value = [
            (1, 'm1', 'borrow', '1', '2026-08-10 09:00:00', False),
            (2, 'm2', 'fine', '2', '2026-08-10 09:00:00', False),
            (3, 'm3', 'overdue_reminder', '3', '2026-08-10 09:00:00', False),
            (4, 'm4', 'hold_ready', '4', '2026-08-10 09:00:00', False),
            (5, 'm5', 'status_update', '5', '2026-08-10 09:00:00', False),
        ]
        data = student_client.get('/api/notifications').get_json()
        urls = {n['type']: n['url'] for n in data['notifications']}
        assert urls['borrow'] == '/user/history?tab=borrowing'
        assert urls['fine'] == '/user/history?tab=fines'
        assert urls['overdue_reminder'] == '/user/profile'
        assert urls['hold_ready'] == '/user/history?tab=reservations'
        assert urls['status_update'] == '/user/notifications'

    def test_feed_member_limit_clamped(self, student_client, mock_db):
        """Validates feed member limit clamped `/api/notifications` as student (expects 200) [TestNotifPanel / main notifications].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates notifications are missing or misrouted."""
        mock_db['fetch_one'].return_value = (7, 1, 'S1', 'BSIS', '0917', 'active', None, None)
        mock_db['fetch_all'].return_value = []
        assert student_client.get('/api/notifications?limit=999').status_code == 200
        _, params = mock_db['fetch_all'].call_args[0]
        assert params[-1] == 20
        assert student_client.get('/api/notifications?limit=bogus').status_code == 200
        _, params = mock_db['fetch_all'].call_args[0]
        assert params[-1] == 8

    def test_feed_member_no_borrower_404(self, student_client, mock_db):
        """Validates feed member no borrower 404 `/api/notifications` as student (expects 404) [TestNotifPanel / main notifications].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates notifications are missing or misrouted."""
        mock_db['fetch_one'].return_value = None
        resp = student_client.get('/api/notifications')
        assert resp.status_code == 404

    def test_feed_staff_payload(self, librarian_client, mock_db):
        """Validates feed staff payload `/api/notifications` as librarian (expects 200) [TestNotifPanel / main notifications].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates notifications are missing or misrouted."""
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = [(5, 'X', '2026-10-01 10:00:00')]
        resp = librarian_client.get('/api/notifications')
        assert resp.status_code == 200
        data = resp.get_json()
        ids = [n['id'] for n in data['notifications']]
        assert 'req-5' in ids and 'res-5' in ids and 'circ-5' in ids
        assert all(n.get('dismissible') is True for n in data['notifications'])
        urls = {n['id']: n['url'] for n in data['notifications']}
        assert urls['req-5'] == '/librarian/requests'
        assert urls['res-5'] == '/librarian/reservations'
        assert urls['circ-5'] == '/librarian/circulation'

    def test_feed_staff_with_borrower_shows_personal(self, librarian_client, mock_db):
        """Validates feed staff with borrower shows personal `/api/notifications` as librarian (expects 200) [TestNotifPanel / main notifications].
    If fails: likely staff personal-notification merge (routes) regressed.
    Failure indicates the staff bell misses notifications addressed to
    the account itself (e.g. reservation/hold-ready messages only seen
    on /profile)."""
        # get_user_by_id is patched in conftest (no DB call), so the two
        # fetch_one hits are the borrower row then the unread count.
        mock_db['fetch_one'].side_effect = [
            (7, 3, 'S1', 'BSIS', '0917', 'active', None, None),
            (2,),
        ]
        mock_db['fetch_all'].side_effect = [
            [(5, 'Needed Book', '2026-10-01 10:00:00')],  # pending requests
            [],                                           # waiting reservations
            [],                                           # recent circulation
            [(9, 'Reservation #35 allocated. Claim by Oct 20, 2026 10:00 AM.',
               'reservation', '35', '2026-10-19 18:15:00', False)],
        ]
        resp = librarian_client.get('/api/notifications')
        assert resp.status_code == 200
        data = resp.get_json()
        # Personal unread carries the badge; staff items are dismissible.
        assert data['unread_count'] == 2
        personal = data['notifications'][0]
        assert personal['id'] == 9
        assert personal.get('dismissible') is not True
        assert personal['read'] is False
        assert personal['url'] == '/user/history?tab=reservations'
        staff_ids = {n['id'] for n in data['notifications'][1:]}
        assert staff_ids == {'req-5'}

    def test_feed_staff_with_borrower_unread_seen(self, librarian_client, mock_db):
        """Validates read personal rows still appear for staff `/api/notifications` as librarian (expects 200) [TestNotifPanel / main notifications].
    If fails: likely personal-card dict shape (read flag) regressed.
    Failure indicates the staff bell hides already-read personal
    notifications instead of greying them out."""
        mock_db['fetch_one'].side_effect = [
            (7, 3, 'S1', 'BSIS', '0917', 'active', None, None),
            (0,),
        ]
        mock_db['fetch_all'].side_effect = [
            [], [], [],
            [(9, 'Old hold ready', 'hold_ready', '9',
              '2026-10-14 09:00:00', True)],
        ]
        data = librarian_client.get('/api/notifications').get_json()
        personal = data['notifications'][0]
        assert personal['id'] == 9
        assert personal['read'] is True
        assert personal.get('dismissible') is not True

    def test_feed_anonymous_401(self, client):
        """Validates feed anonymous 401 `/api/notifications` (expects 401) [TestNotifPanel / main notifications].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = client.get('/api/notifications')
        assert resp.status_code == 401

    def test_live_preserved_for_staff(self, librarian_client, mock_db):
        """Validates live preserved for staff `/api/notifications/live` as librarian (expects 200) [TestNotifPanel / main notifications].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates notifications are missing or misrouted."""
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = [(7, 'Title', '2026-10-01 10:00:00')]
        resp = librarian_client.get('/api/notifications/live')
        assert resp.status_code == 200
        data = resp.get_json()
        ids = [n['id'] for n in data['notifications']]
        assert 'req-7' in ids and 'res-7' in ids and 'circ-7' in ids

    def test_live_staff_with_borrower_merges_personal(self, librarian_client, mock_db):
        """Validates live staff with borrower merges personal `/api/notifications/live` as librarian (expects 200) [TestNotifPanel / main notifications].
    If fails: likely live endpoint personal-notification merge regressed.
    Failure indicates unread personal rows are dropped from the staff
    live poll side of the bell."""
        mock_db['fetch_one'].side_effect = [
            (7, 3, 'S1', 'BSIS', '0917', 'active', None, None),
            (1,),
        ]
        mock_db['fetch_all'].side_effect = [
            [(5, 'Needed Book', '2026-10-01 10:00:00')],
            [], [],
            [(9, 'Reminder: hold ready', 'hold_ready', '9',
              '2026-10-19 18:15:00', False)],
        ]
        data = librarian_client.get('/api/notifications/live').get_json()
        ids = [n['id'] for n in data['notifications']]
        assert data['unread_count'] == 1
        assert ids == [9, 'req-5']
