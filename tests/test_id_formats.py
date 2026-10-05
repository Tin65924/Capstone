"""Tests for canonical ID-number formats and input character limits."""

import re


class TestIdNumberPatterns:
    def test_student_accepts_valid(self):
        from app.auth.models import is_valid_id_number
        assert is_valid_id_number('2024-00123', 'Student')
        assert is_valid_id_number('2000-00000', 'Student')
        assert is_valid_id_number('2099-99999', 'Student')

    def test_student_rejects_bad(self):
        from app.auth.models import is_valid_id_number
        assert not is_valid_id_number('2024-0012', 'Student')   # too short
        assert not is_valid_id_number('2024-001234', 'Student')  # too long
        assert not is_valid_id_number('202400123', 'Student')  # missing dash
        assert not is_valid_id_number('24-00123', 'Student')
        assert not is_valid_id_number('abcd-efghi', 'Student')
        assert not is_valid_id_number('FAC-00123', 'Student')
        assert not is_valid_id_number('', 'Student')

    def test_faculty_accepts_valid(self):
        from app.auth.models import is_valid_id_number
        assert is_valid_id_number('123456789', 'Faculty')
        assert is_valid_id_number('000000000', 'Faculty')
        assert is_valid_id_number('  123456789  ', 'Faculty')  # stripped

    def test_faculty_rejects_bad(self):
        from app.auth.models import is_valid_id_number
        assert not is_valid_id_number('FAC-00123', 'Faculty')  # no prefix allowed
        assert not is_valid_id_number('2024-00123', 'Faculty')
        assert not is_valid_id_number('12345678', 'Faculty')   # too short
        assert not is_valid_id_number('1234567890', 'Faculty')  # too long
        assert not is_valid_id_number('12345-6789', 'Faculty')
        assert not is_valid_id_number('', 'Faculty')

    def test_librarian_accepts_valid(self):
        from app.auth.models import is_valid_id_number
        assert is_valid_id_number('LIB-00123', 'Librarian')
        assert is_valid_id_number('lib-00001', 'Librarian')

    def test_librarian_rejects_bad(self):
        from app.auth.models import is_valid_id_number
        assert not is_valid_id_number('LIB-0012', 'Librarian')
        assert not is_valid_id_number('LIB-001234', 'Librarian')
        assert not is_valid_id_number('FAC-00123', 'Librarian')
        assert not is_valid_id_number('', 'Librarian')

    def test_admin_accepts_valid(self):
        from app.auth.models import is_valid_id_number
        for valid in ('1', '2', '9', '10'):
            assert is_valid_id_number(valid, 'Admin')

    def test_admin_rejects_bad(self):
        from app.auth.models import is_valid_id_number
        for bad in ('0', '00', '11', '100', '', '01', '  '):
            assert not is_valid_id_number(bad, 'Admin')
        # surrounding whitespace is stripped, so padded valid values pass
        assert is_valid_id_number(' 7 ', 'Admin')


class TestIdNumberExamplesMatchPatterns:
    def test_examples_are_valid_for_their_role(self):
        """The example shown in error flashes must itself pass validation."""
        from app.auth.models import ID_NUMBER_EXAMPLES, is_valid_id_number
        example_values = {
            'Student': '2024-00123',
            'Faculty': '123456789',
            'Librarian': 'LIB-00123',
            'Admin': '7',
        }
        for role, value in example_values.items():
            assert is_valid_id_number(value, role), f'{role} example {value!r} invalid'
            assert value in ID_NUMBER_EXAMPLES[role]

    def test_faculty_example_is_plain_nine_digits(self):
        from app.auth.models import ID_NUMBER_EXAMPLES
        assert 'FAC-' not in ID_NUMBER_EXAMPLES['Faculty']
        assert '000000000' in ID_NUMBER_EXAMPLES['Faculty']


class TestIdNumberMaxLengths:
    def test_max_lengths_match_canonical_sizes(self):
        from app.auth.models import ID_NUMBER_MAX_LENGTHS
        assert ID_NUMBER_MAX_LENGTHS == {
            'Student': 10,    # 0000-00000
            'Faculty': 9,     # 000000000
            'Librarian': 9,   # LIB-00000
            'Admin': 2,       # 1-10
        }

    def test_valid_values_fit_max_length(self):
        from app.auth.models import ID_NUMBER_MAX_LENGTHS
        valid = {
            'Student': '2024-00123',
            'Faculty': '123456789',
            'Librarian': 'LIB-00123',
            'Admin': '10',
        }
        for role, value in valid.items():
            assert len(value) <= ID_NUMBER_MAX_LENGTHS[role]

    def test_role_select_template_enforces_limits(self, client):
        with client.session_transaction() as sess:
            sess['_google_oauth_data'] = {
                'email': 't@mcst.edu.ph',
                'oauth_sub': 'sub-x',
                'full_name': 'T',
            }
        resp = client.get('/login/role-select')
        assert resp.status_code == 200
        body = resp.data.decode()
        # base limit + per-role JS limits
        assert 'maxlength="10"' in body
        assert 'maxlength: 10' in body
        assert 'maxlength: 9' in body
        assert 'idInput.maxLength' in body or 'idInput.maxlength' in body.lower() or 'maxLength' in body

    def test_role_select_rejects_overlong_student_id(self, client, mock_db):
        with client.session_transaction() as sess:
            sess['_google_oauth_data'] = {
                'email': 't@mcst.edu.ph',
                'oauth_sub': 'sub-x',
                'full_name': 'T',
            }
        resp = client.post('/login/role-select', data={
            'role': 'Student',
            'id_number': '2024-001234',  # 11 chars > maxlength 10
            'department': 'BSIS',
        })
        assert resp.status_code == 200
        assert b'invalid id' in resp.data.lower()
        assert mock_db['execute'].call_count == 0

    def test_role_select_rejects_overlong_faculty_id(self, client, mock_db):
        with client.session_transaction() as sess:
            sess['_google_oauth_data'] = {
                'email': 'f@mcst.edu.ph',
                'oauth_sub': 'sub-y',
                'full_name': 'F',
            }
        resp = client.post('/login/role-select', data={
            'role': 'Faculty',
            'id_number': '1234567890',  # 10 chars > maxlength 9
            'department': 'CS',
        })
        assert resp.status_code == 200
        assert b'invalid id' in resp.data.lower()
        assert mock_db['execute'].call_count == 0


class TestLandingNewArrivalsClickable:
    def test_new_arrivals_link_to_book(self, client, mock_db):
        mock_db['fetch_all'].return_value = [
            (42, 'Clickable Title', 'Some Author', None, None, 2025,
             None, None, None, 'Book', None, 'active', '2025-01-01'),
        ]
        resp = client.get('/')
        assert resp.status_code == 200
        assert b'/book/42' in resp.data
        assert b'Clickable Title' in resp.data

    def test_profile_has_no_locked_message(self, student_client, mock_db):
        mock_db['fetch_one'].return_value = (
            1, 's@mcst.edu.ph', 'Student', 'Stu', 5,
            '2024-00123', 'BSIS', None, 'active')
        resp = student_client.get('/user/profile')
        assert resp.status_code == 200
        assert b'Locked' not in resp.data
        assert b'contact a librarian to correct it' not in resp.data.lower()
