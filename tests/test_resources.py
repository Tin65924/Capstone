"""Tests for the Online Resources (E-Resources) module: manage, browse, visit logging."""

ROW_ACTIVE = (1, 'JSTOR', 'Provider', 'https://example.com/jstor', '', True, None)
ROW_HIDDEN = (2, 'Old DB', 'Provider', 'https://example.com/old', '', False, None)


class TestResourcesAccess:
    def test_manage_requires_login(self, client, mock_db):
        assert client.get('/librarian/online-resources').status_code == 302

    def test_manage_forbidden_for_student(self, student_client, mock_db):
        resp = student_client.get('/librarian/online-resources')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_browse_requires_login(self, client, mock_db):
        assert client.get('/resources').status_code == 302

    def test_visit_requires_login(self, client, mock_db):
        assert client.get('/resources/1/visit').status_code == 302


class TestManageResources:
    def test_page_renders(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = [ROW_ACTIVE]
        mock_db['fetch_one'].return_value = (1,)
        resp = librarian_client.get('/librarian/online-resources')
        assert resp.status_code == 200
        assert b'Online Resources' in resp.data
        assert b'JSTOR' in resp.data
        assert b'Add Resource' in resp.data

    def test_add_success(self, librarian_client, mock_db):
        resp = librarian_client.post('/librarian/online-resources/add', data={
            'title': 'JSTOR', 'url': 'https://example.com/jstor',
            'provider': 'Provider', 'description': '',
        })
        assert resp.status_code == 302
        query, params = mock_db['execute'].call_args_list[0][0]
        assert 'INSERT INTO online_resources' in query
        assert params[0] == 'JSTOR'

    def test_add_blank_title_rejected(self, librarian_client, mock_db):
        resp = librarian_client.post('/librarian/online-resources/add', data={
            'title': '  ', 'url': 'https://example.com/x'})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_add_non_http_url_rejected(self, librarian_client, mock_db):
        resp = librarian_client.post('/librarian/online-resources/add', data={
            'title': 'Evil', 'url': 'javascript:alert(1)'})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_toggle_hides_active(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = ROW_ACTIVE
        resp = librarian_client.post('/librarian/online-resources/1/toggle')
        assert resp.status_code == 302
        query, params = mock_db['execute'].call_args_list[0][0]
        assert 'UPDATE online_resources' in query
        assert params == (False, 1)

    def test_toggle_missing_row(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = None
        resp = librarian_client.post('/librarian/online-resources/9/toggle')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0


class TestBrowseAndVisit:
    def test_browse_lists_active(self, student_client, mock_db):
        mock_db['fetch_all'].return_value = [ROW_ACTIVE]
        resp = student_client.get('/resources')
        assert resp.status_code == 200
        assert b'JSTOR' in resp.data

    def test_visit_logs_and_redirects(self, student_client, mock_db):
        mock_db['fetch_one'].return_value = ROW_ACTIVE
        resp = student_client.get('/resources/1/visit')
        assert resp.status_code == 302
        assert resp.location == 'https://example.com/jstor'
        query, params = mock_db['execute'].call_args_list[0][0]
        assert 'INSERT INTO online_resource_access' in query
        assert params[0] == 1 and str(params[1]) == '1'

    def test_visit_hidden_redirects(self, student_client, mock_db):
        mock_db['fetch_one'].return_value = ROW_HIDDEN
        resp = student_client.get('/resources/1/visit')
        assert resp.status_code == 302
        assert '/resources' in resp.location
        assert mock_db['execute'].call_count == 0

    def test_visit_missing_redirects(self, student_client, mock_db):
        mock_db['fetch_one'].return_value = None
        resp = student_client.get('/resources/9/visit')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0


class TestResourceUsageModel:
    def test_usage_groups_by_resource(self, mock_db):
        from app.resources.models import resource_usage
        mock_db['fetch_all'].return_value = [('JSTOR', 'Provider', 9)]
        assert resource_usage() == [('JSTOR', 'Provider', 9)]
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'online_resource_access' in query
        assert params == (5,)

    def test_usage_scoped_by_dates(self, mock_db):
        from datetime import date
        from app.resources.models import resource_usage
        mock_db['fetch_all'].return_value = []
        resource_usage(date(2026, 1, 1), date(2026, 12, 31))
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'accessed_at >=' in query
        assert params == (date(2026, 1, 1), date(2026, 12, 31), 5)
