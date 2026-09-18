"""Tests for the Library Settings module: RBAC, page render, update validation."""


class TestSettingsAccess:
    def test_settings_unauthenticated_redirects(self, client):
        resp = client.get('/librarian/settings')
        assert resp.status_code == 302
        assert '/login' in resp.location

    def test_settings_student_forbidden(self, student_client):
        resp = student_client.get('/librarian/settings')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_settings_faculty_forbidden(self, faculty_client):
        resp = faculty_client.get('/librarian/settings')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_settings_librarian_allowed(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/settings')
        assert resp.status_code == 200
        assert b'Library Settings' in resp.data
        assert b'MAX_BORROW_LIMIT_STUDENT' in resp.data

    def test_settings_admin_allowed(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = admin_client.get('/librarian/settings')
        assert resp.status_code == 200
        assert b'Library Settings' in resp.data


class TestSettingsCategories:
    def test_sidebar_lists_all_categories(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/settings')
        assert resp.status_code == 200
        for title in (b'Book Settings', b'Due Date Settings',
                      b'Fine Settings', b'Reservation Settings'):
            assert title in resp.data

    def test_category_anchors_match_sidebar_links(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/settings')
        assert resp.status_code == 200
        for anchor in (b'setting-group-book', b'setting-group-due-dates',
                       b'setting-group-fines', b'setting-group-reservations'):
            assert b'href="#' + anchor + b'"' in resp.data
            assert b'id="' + anchor + b'"' in resp.data

    def test_no_page_header_block(self, librarian_client, mock_db):
        """The old h1 page header was removed in favor of the sidebar."""
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/settings')
        assert resp.status_code == 200
        assert b'Changes apply immediately to new loans' not in resp.data

    def test_top_navbar_removed_on_settings(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/settings')
        assert resp.status_code == 200
        assert b'mobile-menu-btn' not in resp.data

    def test_top_navbar_kept_elsewhere(self, client, mock_db):
        """The base navbar block override must not leak to other pages."""
        resp = client.get('/login')
        assert resp.status_code == 200
        assert b'mobile-menu-btn' in resp.data

    def test_every_setting_appears_exactly_once(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.get('/librarian/settings')
        assert resp.status_code == 200
        for key in (b'MAX_BORROW_LIMIT_STUDENT', b'MAX_BORROW_LIMIT_FACULTY',
                    b'OVERNIGHT_DUE_DAYS_STUDENT', b'OVERNIGHT_DUE_DAYS_FACULTY',
                    b'DAILY_CIRCULATION_DUE_DAYS', b'OVERDUE_FINE_PER_DAY',
                    b'OVERDUE_GRACE_DAYS', b'RESERVATION_CLAIM_DAYS',
                    b'DUE_SOON_NOTIFY_DAYS'):
            # Once as the input name, once as the mono key label.
            assert resp.data.count(b'name="' + key + b'"') == 1

    def test_categories_cover_all_defs(self):
        from app.settings.models import SETTING_CATEGORIES, SETTING_DEFS
        grouped = [k for _, _, _, _, keys in SETTING_CATEGORIES for k in keys]
        assert sorted(grouped) == sorted(SETTING_DEFS.keys())


class TestUpdateSettings:
    def test_update_valid_int(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.post('/librarian/settings/update', data={
            'MAX_BORROW_LIMIT_STUDENT': '4',
        })
        assert resp.status_code == 302
        assert '/librarian/settings' in resp.location
        first = mock_db['execute'].call_args_list[0]
        assert 'INSERT INTO library_settings' in first[0][0]
        assert first[0][1][0] == 'MAX_BORROW_LIMIT_STUDENT'
        assert first[0][1][1] == '4'

    def test_update_rejects_decimal_int(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.post('/librarian/settings/update', data={
            'MAX_BORROW_LIMIT_STUDENT': '2.5',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_update_rejects_zero_limit(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.post('/librarian/settings/update', data={
            'MAX_BORROW_LIMIT_STUDENT': '0',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_update_rejects_negative(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.post('/librarian/settings/update', data={
            'OVERDUE_FINE_PER_DAY': '-5',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_update_accepts_float_fine(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = librarian_client.post('/librarian/settings/update', data={
            'OVERDUE_FINE_PER_DAY': '15.50',
        })
        assert resp.status_code == 302
        first = mock_db['execute'].call_args_list[0]
        assert 'INSERT INTO library_settings' in first[0][0]
        assert first[0][1][0] == 'OVERDUE_FINE_PER_DAY'
        assert first[0][1][1] == '15.5'

    def test_update_student_forbidden(self, student_client, mock_db):
        resp = student_client.post('/librarian/settings/update', data={
            'MAX_BORROW_LIMIT_STUDENT': '9',
        })
        assert resp.status_code == 302
        assert '/user/profile' in resp.location
        assert mock_db['execute'].call_count == 0
