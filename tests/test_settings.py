"""Tests for the Library Settings module: admin-only RBAC, render, validation."""

from unittest.mock import patch

SETTINGS_URL = '/admin/settings'
UPDATE_URL = '/admin/settings/update'


class TestSettingsAccess:
    def test_settings_unauthenticated_redirects(self, client):
        resp = client.get(SETTINGS_URL)
        assert resp.status_code == 302
        assert '/login' in resp.location

    def test_settings_student_forbidden(self, student_client):
        resp = student_client.get(SETTINGS_URL)
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_settings_faculty_forbidden(self, faculty_client):
        resp = faculty_client.get(SETTINGS_URL)
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_settings_librarian_forbidden(self, librarian_client):
        resp = librarian_client.get(SETTINGS_URL)
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_settings_admin_allowed(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = admin_client.get(SETTINGS_URL)
        assert resp.status_code == 200
        assert b'Library Settings' in resp.data
        # Admins see only admin-only constants.
        assert b'BACKUP_DAY' in resp.data
        assert b'BACKUP_HOUR' in resp.data
        assert b'BACKUP_KEEP' in resp.data
        assert b'MAX_BORROW_LIMIT_STUDENT' not in resp.data

    def test_legacy_url_redirects_to_admin(self, admin_client):
        resp = admin_client.get('/librarian/settings')
        assert resp.status_code == 302
        assert SETTINGS_URL in resp.location

    def test_legacy_url_unauthenticated_redirects(self, client):
        resp = client.get('/librarian/settings')
        assert resp.status_code == 302
        assert '/login' in resp.location


class TestSettingsCategories:
    def test_sidebar_lists_only_admin_category(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = admin_client.get(SETTINGS_URL)
        assert resp.status_code == 200
        assert b'Backup Schedule' in resp.data
        for title in (b'Book Settings', b'Due Date Settings',
                      b'Fine Settings', b'Reservation Settings'):
            assert title not in resp.data

    def test_category_sections_rendered(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = admin_client.get(SETTINGS_URL)
        assert resp.status_code == 200
        assert b'id="setting-group-backup-schedule"' in resp.data
        for anchor in (b'setting-group-book', b'setting-group-due-dates',
                        b'setting-group-fines', b'setting-group-reservations'):
            assert b'id="' + anchor + b'"' not in resp.data

    def test_no_page_header_block(self, admin_client, mock_db):
        """The old h1 page header was removed in favor of the sidebar."""
        mock_db['fetch_all'].return_value = []
        resp = admin_client.get(SETTINGS_URL)
        assert resp.status_code == 200
        assert b'Changes apply immediately to new loans' not in resp.data

    def test_top_navbar_removed_on_settings(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = admin_client.get(SETTINGS_URL)
        assert resp.status_code == 200
        assert b'mobile-menu-btn' not in resp.data

    def test_top_navbar_kept_elsewhere(self, client, mock_db):
        """The base navbar block override must not leak to other pages."""
        resp = client.get('/login')
        assert resp.status_code == 200
        assert b'mobile-menu-btn' in resp.data

    def test_every_setting_appears_exactly_once(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = admin_client.get(SETTINGS_URL)
        assert resp.status_code == 200
        for key in (b'BACKUP_DAY', b'BACKUP_HOUR', b'BACKUP_KEEP'):
            # Once as the input name, once as the mono key label.
            assert resp.data.count(b'name="' + key + b'"') == 1
        for key in (b'MAX_BORROW_LIMIT_STUDENT', b'MAX_BORROW_LIMIT_FACULTY',
                    b'OVERNIGHT_DUE_DAYS_STUDENT', b'OVERNIGHT_DUE_DAYS_FACULTY',
                    b'DAILY_CIRCULATION_DUE_DAYS', b'OVERDUE_FINE_PER_DAY',
                    b'OVERDUE_GRACE_DAYS', b'RESERVATION_CLAIM_DAYS',
                    b'DUE_SOON_NOTIFY_DAYS'):
            assert b'name="' + key + b'"' not in resp.data

    def test_categories_cover_all_defs(self):
        from app.settings.models import SETTING_CATEGORIES, SETTING_DEFS
        grouped = [k for _, _, _, _, keys in SETTING_CATEGORIES for k in keys]
        assert sorted(grouped) == sorted(SETTING_DEFS.keys())

    def test_cancel_returns_to_admin_dashboard(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = admin_client.get(SETTINGS_URL)
        assert resp.status_code == 200
        # Cancel button targets the admin dashboard, not the librarian one.
        assert b'href="/admin"' in resp.data
        assert b'>Cancel</a>' in resp.data
        assert b'href="/librarian">Cancel</a>' not in resp.data

    def test_renders_admin_sidebar_not_librarian(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = admin_client.get(SETTINGS_URL)
        assert resp.status_code == 200
        assert b'/admin/audits' in resp.data
        assert b'Staff Management' in resp.data
        assert b'Cataloging' not in resp.data


class TestUpdateSettings:
    def test_update_valid_backup_day(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        with patch('app.backup.scheduler.reschedule') as mock_resched:
            resp = admin_client.post(UPDATE_URL, data={
                'BACKUP_DAY': '15',
            })
        assert resp.status_code == 302
        assert SETTINGS_URL in resp.location
        first = mock_db['execute'].call_args_list[0]
        assert 'INSERT INTO library_settings' in first[0][0]
        assert first[0][1][0] == 'BACKUP_DAY'
        assert first[0][1][1] == '15'
        mock_resched.assert_called_once()

    def test_update_rejects_circulation_keys(self, admin_client, mock_db):
        """Circulation constants have no admin UI surface — not updatable."""
        mock_db['fetch_all'].return_value = []
        resp = admin_client.post(UPDATE_URL, data={
            'MAX_BORROW_LIMIT_STUDENT': '4',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_update_rejects_day_out_of_range(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = admin_client.post(UPDATE_URL, data={'BACKUP_DAY': '99'})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_update_rejects_hour_out_of_range(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = admin_client.post(UPDATE_URL, data={'BACKUP_HOUR': '25'})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_update_rejects_zero_keep(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = admin_client.post(UPDATE_URL, data={'BACKUP_KEEP': '0'})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_update_rejects_decimal_int(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = admin_client.post(UPDATE_URL, data={
            'MAX_BORROW_LIMIT_STUDENT': '2.5',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_update_rejects_zero_limit(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = admin_client.post(UPDATE_URL, data={
            'MAX_BORROW_LIMIT_STUDENT': '0',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_update_rejects_negative(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = admin_client.post(UPDATE_URL, data={
            'OVERDUE_FINE_PER_DAY': '-5',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_update_rejects_decimal_backup_day(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = admin_client.post(UPDATE_URL, data={
            'BACKUP_DAY': '2.5',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_update_student_forbidden(self, student_client, mock_db):
        resp = student_client.post(UPDATE_URL, data={
            'MAX_BORROW_LIMIT_STUDENT': '9',
        })
        assert resp.status_code == 302
        assert '/user/profile' in resp.location
        # Only write is the denial audit row — no setting is updated.
        assert mock_db['execute'].call_count == 1
        query, params = mock_db['execute'].call_args[0]
        assert 'INSERT INTO audit_trail' in query
        assert params[1] == 'security:denied:settings.update_settings'

    def test_update_librarian_forbidden(self, librarian_client, mock_db):
        resp = librarian_client.post(UPDATE_URL, data={
            'MAX_BORROW_LIMIT_STUDENT': '9',
        })
        assert resp.status_code == 302
        assert '/user/profile' in resp.location
        # Only write is the denial audit row — no setting is updated.
        assert mock_db['execute'].call_count == 1
        query, params = mock_db['execute'].call_args[0]
        assert 'INSERT INTO audit_trail' in query
        assert params[1] == 'security:denied:settings.update_settings'


class TestFlashDismiss:
    def test_flash_renders_dismiss_markup(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = admin_client.post(UPDATE_URL, data={
            'MAX_BORROW_LIMIT_STUDENT': '4',
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'data-flash' in resp.data
        assert b'data-flash-close' in resp.data


class TestResetDbRemoved:
    def test_reset_route_gone(self, admin_client):
        assert 'reset_db' not in admin_client.application.view_functions
        resp = admin_client.get('/admin/reset-db')
        assert resp.status_code == 404

    def test_no_reset_link_in_admin_sidebar(self, admin_client, mock_db):
        mock_db['fetch_one'].side_effect = [(10,), (0,), (5,)]
        mock_db['fetch_all'].side_effect = [[], [], [], []]
        resp = admin_client.get('/admin')
        assert resp.status_code == 200
        assert b'Reset Database' not in resp.data
        assert b'reset-db' not in resp.data

    def test_no_settings_link_in_librarian_sidebar(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [
            (100,), (10,), (4,), (3,), (10,), (3,), (1,),
        ]
        from tests.test_main import TestDashboardAttention
        mock_db['fetch_all'].side_effect = [
            TestDashboardAttention.GROUPS, [], [(7,)], [], [],
            TestDashboardAttention.PENDING, TestDashboardAttention.GROUPS,
        ]
        resp = librarian_client.get('/librarian')
        assert resp.status_code == 200
        assert b'Library Settings' not in resp.data
