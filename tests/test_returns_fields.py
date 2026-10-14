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
    """Test helper _post_add: build mocked data or DB stub for the test."""
    data = dict(FULL_BOOK)
    data.update(overrides)
    return client.post('/librarian/cataloging/add', data=data)


class TestDeskOnlyReturns:
    def test_user_return_writes_nothing(self, student_client, mock_db):
        """Validates user return writes nothing `/user/return` as student (expects 302) [TestDeskOnlyReturns / returns fields].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        resp = student_client.post('/user/return',
                                   data={'circulation_id': 55})
        assert resp.status_code == 302
        assert '/user/profile' in resp.location
        assert mock_db['execute'].call_count == 0
        assert mock_db['fetch_one'].call_count == 0

    def test_profile_has_no_self_return_form(self, student_client, mock_db):
        """Validates profile has no self return form `/user/profile` as student [TestDeskOnlyReturns / returns fields].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
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
        """Validates each required field `/librarian/cataloging/add` as librarian (expects 302) [TestRequiredBookFields / returns fields].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
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
        """Validates optional fields stay optional as librarian (expects 302) [TestRequiredBookFields / returns fields].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['execute'].return_value = [(1,)]
        mock_db['fetch_one'].return_value = None
        resp = _post_add(librarian_client)
        assert resp.status_code == 302
        assert mock_db['execute'].call_count >= 1
        assert 'INSERT INTO book_catalog' in \
            mock_db['execute'].call_args_list[0][0][0]

    def test_edit_requires_fields(self, librarian_client, mock_db):
        """Validates edit requires fields `/librarian/cataloging/1/edit` as librarian (expects 302) [TestRequiredBookFields / returns fields].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
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
        """Validates length caps `/librarian/cataloging/add` as librarian (expects 302) [TestRequiredBookFields / returns fields].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
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
        """Validates year bounds `/librarian/cataloging/add` as librarian (expects 302) [TestRequiredBookFields / returns fields].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
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
        """Validates accession too long `/librarian/cataloging/add` as librarian (expects 302) [TestRequiredBookFields / returns fields].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        data = dict(FULL_BOOK)
        data['accession_number'] = 'x' * 31
        resp = librarian_client.post('/librarian/cataloging/add', data=data)
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_accession_must_be_six_digits(self, librarian_client, mock_db):
        """Validates accession must be six digits `/librarian/cataloging/add` as librarian (expects 302) [TestRequiredBookFields / returns fields].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['execute'].return_value = [(1,)]
        mock_db['fetch_one'].return_value = None
        for number in ('12345', '1234567', 'ABC123', '12345a', ' 250001 ',
                       '250001'):
            data = dict(FULL_BOOK)
            data['accession_number'] = number
            resp = librarian_client.post('/librarian/cataloging/add',
                                         data=data)
            assert resp.status_code == 302, number
        writes = [c for c in mock_db['execute'].call_args_list
                  if 'INSERT INTO accession_log' in c[0][0]]
        # Only the two valid forms (one whitespace-padded) wrote a copy.
        assert len(writes) == 2

    def test_add_accession_rejects_bad_format(self, librarian_client, mock_db):
        """Validates add accession rejects bad format `/librarian/cataloging/1/accession/add` as librarian (expects 302) [TestRequiredBookFields / returns fields].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].return_value = (
            1, 'T', 'A', '1st', 'Pub', 2008, 'S', 'C1', '978', 'Book',
            'D', 'active', '2026-01-01', None, None)
        resp = librarian_client.post('/librarian/cataloging/1/accession/add',
                                     data={'accession_number': 'ABC-1'})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_edit_accession_rejects_bad_format(self, librarian_client, mock_db):
        """Validates edit accession rejects bad format `/librarian/cataloging/accession/21/edit` as librarian (expects 302) [TestRequiredBookFields / returns fields].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].return_value = (
            21, '250015', 1, 3, '2024-01-15', 'purchase')
        resp = librarian_client.post('/librarian/cataloging/accession/21/edit',
                                     data={'accession_number': '12345'})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0


class TestAccessionExistsApi:
    def test_exists_true(self, client, mock_db):
        """Validates exists true `/api/accession-exists?accession_number=ACC-1` (expects 200) [TestAccessionExistsApi / returns fields].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].return_value = (10, 'ACC-1', 1)
        resp = client.get('/api/accession-exists?accession_number=ACC-1')
        assert resp.status_code == 200
        assert resp.get_json() == {'exists': True}

    def test_exists_false(self, client, mock_db):
        """Validates exists false `/api/accession-exists?accession_number=NOPE` (expects 200) [TestAccessionExistsApi / returns fields].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        mock_db['fetch_one'].return_value = None
        resp = client.get('/api/accession-exists?accession_number=NOPE')
        assert resp.status_code == 200
        assert resp.get_json() == {'exists': False}

    def test_missing_param(self, client, mock_db):
        """Validates missing param `/api/accession-exists` (expects 200) [TestAccessionExistsApi / returns fields].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates borrow/reserve/return flow is broken (over-booking or stuck queue)."""
        resp = client.get('/api/accession-exists')
        assert resp.status_code == 200
        assert resp.get_json() == {'exists': False}
        assert mock_db['fetch_one'].call_count == 0

    def test_form_has_live_check_hooks(self, librarian_client, mock_db):
        """Validates form has live check hooks `/librarian/cataloging` as librarian [TestAccessionExistsApi / returns fields].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/cataloging').data.decode()
        assert 'data-exists-accession' in body
        assert 'data-exists-accession-msg' in body
