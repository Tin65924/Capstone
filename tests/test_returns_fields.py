"""Regression tests for: desk-only returns, required book fields,
and the accession live duplicate check. Mocked DB — no Postgres.
"""

FULL_BOOK = {
    'title': 'New Book',
    'author': 'New Author',
    'edition': '3rd',
    'publisher': 'Test Press',
    'year_published': '2024',
    'isbn': '978-1234567890',
    'subject_classification': 'Computer Science',
    'call_number': 'QA76.6',
}


def _post_add(client, **overrides):
    data = dict(FULL_BOOK)
    data.update(overrides)
    return client.post('/librarian/cataloging/add', data=data)


class TestDeskOnlyReturns:
    def test_user_return_writes_nothing(self, student_client, mock_db):
        resp = student_client.post('/user/return',
                                   data={'circulation_id': 55})
        assert resp.status_code == 302
        assert '/user/profile' in resp.location
        assert mock_db['execute'].call_count == 0
        assert mock_db['fetch_one'].call_count == 0

    def test_profile_has_no_self_return_form(self, student_client, mock_db):
        from datetime import date
        mock_db['fetch_one'].return_value = (1, 1, '2024-0001', 'CS', 'active')
        mock_db['fetch_all'].return_value = [
            (55, date(2026, 8, 1), date(2026, 8, 2), 'overnight',
             'active', 'Intro to Algorithms', '2024-00123'),
        ]
        body = student_client.get('/user/profile').data.decode()
        assert 'Return at desk' in body
        assert '/user/return' not in body
        assert 'borrowReturnForm' not in body


class TestRequiredBookFields:
    def test_each_required_field(self, librarian_client, mock_db):
        for field in ('title', 'author', 'edition', 'publisher',
                      'year_published', 'isbn', 'subject_classification',
                      'call_number'):
            data = dict(FULL_BOOK)
            data[field] = '   '
            resp = librarian_client.post('/librarian/cataloging/add',
                                         data=data)
            assert resp.status_code == 302, field
        assert mock_db['execute'].call_count == 0

    def test_optional_fields_stay_optional(self, librarian_client, mock_db):
        mock_db['execute'].return_value = [(1,)]
        mock_db['fetch_one'].return_value = None
        resp = _post_add(librarian_client)
        assert resp.status_code == 302
        assert mock_db['execute'].call_count >= 1
        assert 'INSERT INTO book_catalog' in \
            mock_db['execute'].call_args_list[0][0][0]

    def test_edit_requires_fields(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (
            1, 'T', 'A', '1st', 'P', 2020, 'S', 'C', '978',
            'Book', 'D', 'active', '2026-01-01', None, None)
        data = dict(FULL_BOOK)
        del data['publisher']
        resp = librarian_client.post('/librarian/cataloging/1/edit',
                                     data=data)
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_length_caps(self, librarian_client, mock_db):
        cases = [('title', 255), ('author', 150), ('edition', 30),
                 ('publisher', 150), ('isbn', 20),
                 ('subject_classification', 100), ('call_number', 50)]
        for field, cap in cases:
            data = dict(FULL_BOOK)
            data[field] = 'x' * (cap + 1)
            resp = librarian_client.post('/librarian/cataloging/add',
                                         data=data)
            assert resp.status_code == 302, field
        assert mock_db['execute'].call_count == 0

    def test_year_bounds(self, librarian_client, mock_db):
        mock_db['execute'].return_value = [(1,)]
        mock_db['fetch_one'].return_value = None
        for year, ok in (('2024', True), ('1000', True), ('9999', True),
                         ('999', False), ('10000', False), ('abc', False),
                         ('20.5', False), ('', False), ('-500', False)):
            data = dict(FULL_BOOK)
            data['year_published'] = year
            resp = librarian_client.post('/librarian/cataloging/add',
                                         data=data)
            assert resp.status_code == 302, year
        # Only the three valid years may have written.
        writes = [c for c in mock_db['execute'].call_args_list
                  if 'INSERT INTO book_catalog' in c[0][0]]
        assert len(writes) == 3

    def test_accession_too_long(self, librarian_client, mock_db):
        data = dict(FULL_BOOK)
        data['accession_number'] = 'x' * 31
        resp = librarian_client.post('/librarian/cataloging/add', data=data)
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0


class TestAccessionExistsApi:
    def test_exists_true(self, client, mock_db):
        mock_db['fetch_one'].return_value = (10, 'ACC-1', 1)
        resp = client.get('/api/accession-exists?accession_number=ACC-1')
        assert resp.status_code == 200
        assert resp.get_json() == {'exists': True}

    def test_exists_false(self, client, mock_db):
        mock_db['fetch_one'].return_value = None
        resp = client.get('/api/accession-exists?accession_number=NOPE')
        assert resp.status_code == 200
        assert resp.get_json() == {'exists': False}

    def test_missing_param(self, client, mock_db):
        resp = client.get('/api/accession-exists')
        assert resp.status_code == 200
        assert resp.get_json() == {'exists': False}
        assert mock_db['fetch_one'].call_count == 0

    def test_form_has_live_check_hooks(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/cataloging').data.decode()
        assert 'data-exists-accession' in body
        assert 'data-exists-accession-msg' in body
