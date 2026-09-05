"""Tests for user notifications, self-service profile updates, and catalog views."""

from datetime import date


class TestUserNotificationsPage:
    def test_notifications_unauthenticated_redirects(self, client):
        resp = client.get('/user/notifications')
        assert resp.status_code == 302
        assert '/login' in resp.location

    def test_notifications_student_allowed(self, student_client, mock_db):
        mock_db['fetch_one'].return_value = (1, 1, '2024-0001', 'CS', 'active')
        mock_db['fetch_all'].return_value = [
            (1, 'You borrowed copy X.', 'borrow', '10', '2026-08-10 09:00:00', False),
        ]
        resp = student_client.get('/user/notifications')
        assert resp.status_code == 200
        assert b'Notifications' in resp.data
        assert b'You borrowed copy X.' in resp.data

    def test_notifications_no_borrower_renders(self, student_client, mock_db):
        mock_db['fetch_one'].return_value = None
        resp = student_client.get('/user/notifications')
        assert resp.status_code == 200
        assert b'Notifications' in resp.data


class TestMarkNotificationRead:
    def test_mark_read_redirects_to_next(self, student_client, mock_db):
        mock_db['fetch_one'].return_value = (1, 1, '2024-0001', 'CS', 'active')
        resp = student_client.post('/user/notifications/1/read',
                                   data={'next': '/user/notifications'})
        assert resp.status_code == 302
        assert '/user/notifications' in resp.location
        first = mock_db['execute'].call_args_list[0]
        assert 'UPDATE notification_log' in first[0][0]

    def test_mark_read_rejects_protocol_relative_redirect(self, student_client, mock_db):
        mock_db['fetch_one'].return_value = (1, 1, '2024-0001', 'CS', 'active')
        resp = student_client.post('/user/notifications/1/read',
                                   data={'next': '//evil.com/phish'})
        assert resp.status_code == 302
        assert 'evil.com' not in resp.location
        assert '/user/profile' in resp.location

    def test_mark_read_rejects_absolute_url(self, student_client, mock_db):
        mock_db['fetch_one'].return_value = (1, 1, '2024-0001', 'CS', 'active')
        resp = student_client.post('/user/notifications/1/read?next=https://evil.com',
                                   data={})
        assert resp.status_code == 302
        assert 'evil.com' not in resp.location
        assert '/user/profile' in resp.location

    def test_mark_all_read(self, student_client, mock_db):
        mock_db['fetch_one'].return_value = (1, 1, '2024-0001', 'CS', 'active')
        resp = student_client.post('/user/notifications/read-all',
                                   data={'next': '/user/profile'})
        assert resp.status_code == 302
        assert '/user/profile' in resp.location
        first = mock_db['execute'].call_args_list[0]
        assert 'UPDATE notification_log' in first[0][0]
        assert 'is_read = TRUE' in first[0][0]

    def test_mark_read_no_borrower_writes_nothing(self, student_client, mock_db):
        mock_db['fetch_one'].return_value = None
        resp = student_client.post('/user/notifications/1/read', data={})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0


class TestUpdateProfile:
    PROFILE = (1, 'student@mcst.edu.ph', 'Student', 'Test Student',
               1, '2024-0001', 'CS', None, 'active')

    def test_update_profile_success(self, student_client, mock_db):
        mock_db['fetch_one'].return_value = self.PROFILE
        resp = student_client.post('/user/profile/update', data={
            'full_name': 'New Name',
            'phone_number': '+63 912 345 6789',
            'department': 'BSIT',
        })
        assert resp.status_code == 302
        assert '/user/profile' in resp.location
        first = mock_db['execute'].call_args_list[0]
        assert 'UPDATE user_accounts' in first[0][0]
        assert first[0][1][0] == 'New Name'

    def test_update_profile_rejects_id_change(self, student_client, mock_db):
        resp = student_client.post('/user/profile/update', data={
            'full_name': 'New Name',
            'id_number': '9999-0000',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0
        assert mock_db['fetch_one'].call_count == 0

    def test_update_profile_rejects_bad_phone(self, student_client, mock_db):
        resp = student_client.post('/user/profile/update', data={
            'full_name': 'New Name',
            'phone_number': 'not-a-phone!!!',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_update_profile_requires_name(self, student_client, mock_db):
        resp = student_client.post('/user/profile/update', data={'full_name': ''})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0


class TestHistoryNewSections:
    def test_history_shows_fines_reservations_notifications(self, student_client, mock_db):
        mock_db['fetch_one'].return_value = (1, 1, '2024-0001', 'CS', 'active')
        mock_db['fetch_all'].return_value = []
        resp = student_client.get('/user/history')
        assert resp.status_code == 200
        assert b'Fines' in resp.data
        assert b'Reservation History' in resp.data
        assert b'Notification History' in resp.data


class TestFineGraceDays:
    def test_grace_days_reduce_fine(self, mock_db):
        from app.circulation.models import calculate_fine
        mock_db['fetch_one'].return_value = (date(2026, 7, 1), date(2026, 7, 6))
        assert calculate_fine(55, 10.0, 2) == 30.0

    def test_grace_days_floor_at_zero(self, mock_db):
        from app.circulation.models import calculate_fine
        mock_db['fetch_one'].return_value = (date(2026, 7, 1), date(2026, 7, 2))
        assert calculate_fine(55, 10.0, 5) == 0


class TestCatalogViews:
    BOOKS = [
        (1, 'Introduction to Algorithms', 'Cormen', '3rd', 'MIT Press', 2022,
         'Computer Science', 'QA76.73', '978-0262033848', 'Book',
         'A comprehensive textbook.', 'active', '2024-01-15', '2025-0001'),
    ]

    def test_list_view_renders(self, client, mock_db):
        mock_db['fetch_all'].side_effect = [self.BOOKS, []]
        resp = client.get('/catalog?q=test&view=list')
        assert resp.status_code == 200
        assert b'id="catalog-results-list"' in resp.data
        assert b'Introduction to Algorithms' in resp.data

    def test_invalid_view_falls_back_to_grid(self, client, mock_db):
        mock_db['fetch_all'].side_effect = [self.BOOKS, []]
        resp = client.get('/catalog?q=test&view=bogus')
        assert resp.status_code == 200
        assert b'id="catalog-results-grid"' in resp.data
        assert b'id="catalog-results-list"' not in resp.data
