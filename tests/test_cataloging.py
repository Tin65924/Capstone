"""Tests for cataloging module: CRUD, search, RBAC, pagination, bulk import."""

import io
import csv

SAMPLE_BOOKS = [
    (1, 'Introduction to Algorithms', 'Cormen', '3rd', 'MIT Press', 2022,
     'Computer Science', 'QA76.73', '978-0262033848', 'Book',
     'A comprehensive textbook.', 'active', '2024-01-15', '250001'),
    (2, 'Clean Code', 'Martin', '1st', 'Prentice Hall', 2008,
     'Software Engineering', 'QA76.76', '978-0132350884', 'Book',
     'A handbook of agile software craftsmanship.', 'active', '2024-02-10', '2025-0002, 2025-0003'),
    (3, 'The Great Gatsby', 'Fitzgerald', None, None, 1925,
     'Literature', None, None, 'Book',
     None, 'archived', '2024-03-01', ''),
]


class TestCatalogingAccess:
    def test_cataloging_student_forbidden(self, student_client):
        """Validates cataloging student forbidden `/librarian/cataloging` as student (expects 302) [TestCatalogingAccess / cataloging].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = student_client.get('/librarian/cataloging')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_cataloging_faculty_forbidden(self, faculty_client):
        """Validates cataloging faculty forbidden `/librarian/cataloging` as faculty (expects 302) [TestCatalogingAccess / cataloging].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = faculty_client.get('/librarian/cataloging')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_cataloging_librarian_allowed(self, librarian_client, mock_db):
        """Validates cataloging librarian allowed `/librarian/cataloging` as librarian (expects 200) [TestCatalogingAccess / cataloging].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_all'].return_value = SAMPLE_BOOKS
        resp = librarian_client.get('/librarian/cataloging')
        assert resp.status_code == 200
        assert b'Cataloging' in resp.data
        assert b'Accession Number' in resp.data
        assert b'250001' in resp.data
        assert b'2025-0002, 2025-0003' in resp.data

    def test_cataloging_admin_allowed(self, admin_client, mock_db):
        """Validates cataloging admin allowed `/librarian/cataloging` as admin (expects 200) [TestCatalogingAccess / cataloging].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_all'].return_value = SAMPLE_BOOKS
        resp = admin_client.get('/librarian/cataloging')
        assert resp.status_code == 200
        assert b'Cataloging' in resp.data

    def test_cataloging_unauthenticated_redirects(self, client):
        """Validates cataloging unauthenticated redirects `/librarian/cataloging` (expects 302) [TestCatalogingAccess / cataloging].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = client.get('/librarian/cataloging')
        assert resp.status_code == 302
        assert '/login' in resp.location


class TestCatalogingCRUD:
    FULL_BOOK = {
        'edition': '3rd',
        'publisher': 'Test Press',
        'year_published': '2024',
        'isbn': '978-1234567890',
        'subject_classification': 'Computer Science',
        'call_number': 'QA76.6',
    }

    def test_add_book_success(self, librarian_client, mock_db):
        """Validates add book success `/librarian/cataloging/add` as librarian (expects 302) [TestCatalogingCRUD / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['execute'].return_value = [(1,)]
        mock_db['fetch_one'].return_value = None
        resp = librarian_client.post('/librarian/cataloging/add', data={
            'title': 'New Book',
            'author': 'New Author',
            'material_type': 'Book',
            'accession_number': '250001',
            'source': 'purchase',
            **self.FULL_BOOK,
        })
        assert resp.status_code == 302
        assert '/librarian/cataloging' in resp.location
        assert mock_db['execute'].call_count >= 2
        stmts = [c[0][0] for c in mock_db['execute'].call_args_list]
        assert any('INSERT INTO book_catalog' in s for s in stmts)
        assert any('INSERT INTO categories' in s for s in stmts)
        call_args2 = next(c for c in mock_db['execute'].call_args_list
                          if 'INSERT INTO accession_log' in c[0][0])
        assert 'INSERT INTO accession_log' in call_args2[0][0]

    def test_add_book_without_accession(self, librarian_client, mock_db):
        """Validates add book without accession `/librarian/cataloging/add` as librarian (expects 302) [TestCatalogingCRUD / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['execute'].return_value = [(1,)]
        resp = librarian_client.post('/librarian/cataloging/add', data={
            'title': 'New Book',
            'author': 'New Author',
            'material_type': 'Book',
            **self.FULL_BOOK,
        })
        assert resp.status_code == 302
        assert '/librarian/cataloging' in resp.location
        assert mock_db['execute'].call_count >= 1
        stmts = [c[0][0] for c in mock_db['execute'].call_args_list]
        assert any('INSERT INTO book_catalog' in s for s in stmts)

    def test_add_book_duplicate_accession(self, librarian_client, mock_db):
        """Validates add book duplicate accession `/librarian/cataloging/add` as librarian (expects 302) [TestCatalogingCRUD / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['execute'].return_value = [(1,)]
        mock_db['fetch_one'].return_value = ('250001',)
        resp = librarian_client.post('/librarian/cataloging/add', data={
            'title': 'New Book',
            'author': 'New Author',
            'accession_number': '250001',
            **self.FULL_BOOK,
        })
        assert resp.status_code == 302
        assert '/librarian/cataloging' in resp.location

    def test_add_book_dedup_adds_copy(self, librarian_client, mock_db):
        """Validates add book dedup adds copy `/librarian/cataloging/add` as librarian (expects 302) [TestCatalogingCRUD / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        # accession lookup, book dedup hit, category lookup miss + re-read.
        mock_db['fetch_one'].side_effect = [None, (5,), None, None]
        mock_db['execute'].return_value = 1
        resp = librarian_client.post('/librarian/cataloging/add', data={
            'title': 'Existing Title',
            'author': 'Existing Author',
            'accession_number': '250099',
            'source': 'purchase',
            **self.FULL_BOOK,
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count >= 2
        first_exec = next(c[0][0] for c in mock_db['execute'].call_args_list
                          if 'INSERT INTO accession_log' in c[0][0])
        assert 'INSERT INTO accession_log' in first_exec
        assert all('INSERT INTO book_catalog' not in c[0][0]
                   for c in mock_db['execute'].call_args_list)

    def test_add_book_dedup_no_new_record(self, librarian_client, mock_db):
        """Validates add book dedup no new record `/librarian/cataloging/add` as librarian (expects 302) [TestCatalogingCRUD / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].return_value = (5,)
        mock_db['execute'].return_value = 1
        resp = librarian_client.post('/librarian/cataloging/add', data={
            'title': 'Existing Title',
            'author': 'Existing Author',
            **self.FULL_BOOK,
        })
        assert resp.status_code == 302
        assert all('INSERT INTO book_catalog' not in c[0][0]
                   for c in mock_db['execute'].call_args_list)

    def test_add_book_dedup_blank_isbn_matches(self, mock_db):
        # ISBN is required on the form, so the blank-ISBN dedup branch
        # (bulk import / legacy rows) is pinned at the model level.
        """Validates add book dedup blank isbn matches [TestCatalogingCRUD / cataloging].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        from app.cataloging.models import get_book_by_title_author_isbn
        mock_db['fetch_one'].return_value = (5,)
        assert get_book_by_title_author_isbn('T', 'A', None) == (5,)
        dedup_call = mock_db['fetch_one'].call_args_list[0][0]
        assert 'isbn IS NULL' in dedup_call[0]

    def test_add_book_missing_isbn_rejected(self, librarian_client, mock_db):
        """Validates add book missing isbn rejected `/librarian/cataloging/add` as librarian (expects 302) [TestCatalogingCRUD / cataloging].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = librarian_client.post('/librarian/cataloging/add', data={
            'title': 'No ISBN Book',
            'author': 'No ISBN Author',
            'edition': '1st',
            'publisher': 'Pub',
            'year_published': '2020',
            'subject_classification': 'Science',
            'call_number': 'Q1',
            'accession_number': '250100',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_add_book_missing_title(self, librarian_client, mock_db):
        """Validates add book missing title `/librarian/cataloging/add` as librarian (expects 302) [TestCatalogingCRUD / cataloging].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = librarian_client.post('/librarian/cataloging/add', data={
            'title': '',
            'author': 'Some Author',
        })
        assert resp.status_code == 302

    def test_add_book_missing_author(self, librarian_client, mock_db):
        """Validates add book missing author `/librarian/cataloging/add` as librarian (expects 302) [TestCatalogingCRUD / cataloging].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = librarian_client.post('/librarian/cataloging/add', data={
            'title': 'Some Title',
            'author': '',
        })
        assert resp.status_code == 302

    def test_edit_book_success(self, librarian_client, mock_db):
        """Validates edit book success `/librarian/cataloging/1/edit` as librarian (expects 302) [TestCatalogingCRUD / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (UPDATE).
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].return_value = SAMPLE_BOOKS[0]
        mock_db['execute'].return_value = 1
        resp = librarian_client.post('/librarian/cataloging/1/edit', data={
            'title': 'Updated Title',
            'author': 'Updated Author',
            **self.FULL_BOOK,
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count >= 1
        call_args = mock_db['execute'].call_args_list[0]
        assert 'UPDATE book_catalog' in call_args[0][0]

    def test_edit_book_not_found(self, librarian_client, mock_db):
        """Validates edit book not found `/librarian/cataloging/999/edit` as librarian (expects 302) [TestCatalogingCRUD / cataloging].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].return_value = None
        resp = librarian_client.post('/librarian/cataloging/999/edit', data={
            'title': 'Ghost',
            'author': 'Ghost',
        })
        assert resp.status_code == 302
        assert '/librarian/cataloging' in resp.location

    def test_toggle_book_status_archive(self, librarian_client, mock_db):
        """Validates toggle book status archive `/librarian/cataloging/1/status` as librarian (expects 302) [TestCatalogingCRUD / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (UPDATE).
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].return_value = SAMPLE_BOOKS[0]
        mock_db['execute'].return_value = 1
        resp = librarian_client.post('/librarian/cataloging/1/status')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count >= 1
        call_args = mock_db['execute'].call_args_list[0]
        assert 'UPDATE book_catalog' in call_args[0][0]
        assert 'archived' in call_args[0][1]

    def test_toggle_book_status_not_found(self, librarian_client, mock_db):
        """Validates toggle book status not found `/librarian/cataloging/999/status` as librarian (expects 302) [TestCatalogingCRUD / cataloging].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].return_value = None
        resp = librarian_client.post('/librarian/cataloging/999/status')
        assert resp.status_code == 302

    def test_delete_book_archived_success(self, librarian_client, mock_db):
        """Validates delete book archived success `/librarian/cataloging/3/delete` as librarian (expects 302) [TestCatalogingCRUD / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (DELETE FROM).
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].return_value = SAMPLE_BOOKS[2]
        mock_db['execute'].return_value = 1
        resp = librarian_client.post('/librarian/cataloging/3/delete')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count >= 1
        call_args = mock_db['execute'].call_args_list[0]
        assert 'DELETE FROM book_catalog' in call_args[0][0]

    def test_delete_book_not_archived_fails(self, librarian_client, mock_db):
        """Validates delete book not archived fails `/librarian/cataloging/1/delete` as librarian (expects 302) [TestCatalogingCRUD / cataloging].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].return_value = SAMPLE_BOOKS[0]
        resp = librarian_client.post('/librarian/cataloging/1/delete')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_delete_book_not_found(self, librarian_client, mock_db):
        """Validates delete book not found `/librarian/cataloging/999/delete` as librarian (expects 302) [TestCatalogingCRUD / cataloging].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].return_value = None
        resp = librarian_client.post('/librarian/cataloging/999/delete')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_delete_book_rbac_student_forbidden(self, student_client, mock_db):
        """Validates delete book rbac student forbidden `/librarian/cataloging/3/delete` as student (expects 302) [TestCatalogingCRUD / cataloging].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = student_client.post('/librarian/cataloging/3/delete')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_delete_book_rbac_faculty_forbidden(self, faculty_client, mock_db):
        """Validates delete book rbac faculty forbidden `/librarian/cataloging/3/delete` as faculty (expects 302) [TestCatalogingCRUD / cataloging].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = faculty_client.post('/librarian/cataloging/3/delete')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_delete_book_unauthenticated(self, client, mock_db):
        """Validates delete book unauthenticated `/librarian/cataloging/3/delete` (expects 302) [TestCatalogingCRUD / cataloging].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = client.post('/librarian/cataloging/3/delete')
        assert resp.status_code == 302
        assert '/login' in resp.location

    def test_add_accession_success(self, librarian_client, mock_db):
        """Validates add accession success `/librarian/cataloging/1/accession/add` as librarian (expects 302) [TestCatalogingCRUD / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].side_effect = [SAMPLE_BOOKS[0], None]
        mock_db['execute'].return_value = 1
        resp = librarian_client.post('/librarian/cataloging/1/accession/add', data={
            'accession_number': '250001',
            'source': 'purchase',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count >= 1
        call_args = mock_db['execute'].call_args_list[0]
        assert 'INSERT INTO accession_log' in call_args[0][0]

    def test_add_accession_duplicate(self, librarian_client, mock_db):
        """Validates add accession duplicate `/librarian/cataloging/1/accession/add` as librarian (expects 302) [TestCatalogingCRUD / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].side_effect = [SAMPLE_BOOKS[0], ('250001',)]
        mock_db['execute'].return_value = 1
        resp = librarian_client.post('/librarian/cataloging/1/accession/add', data={
            'accession_number': '250001',
        })
        assert resp.status_code == 302

    def test_add_accession_missing_number(self, librarian_client, mock_db):
        """Validates add accession missing number `/librarian/cataloging/1/accession/add` as librarian (expects 302) [TestCatalogingCRUD / cataloging].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].return_value = SAMPLE_BOOKS[0]
        resp = librarian_client.post('/librarian/cataloging/1/accession/add', data={
            'accession_number': '',
        })
        assert resp.status_code == 302


SAMPLE_COPIES = [
    (21, 'ACC-0015', 1, 'purchase', '2024-01-15'),
    (22, 'ACC-123456', 1, 'donation', '2025-06-01'),
]
SAMPLE_ACC_ROW = (21, 'ACC-0015', 1, 3, '2024-01-15', 'purchase')


class TestCatalogingCopies:
    def test_cataloging_renders_copies(self, librarian_client, mock_db):
        """Validates cataloging renders copies `/librarian/cataloging` as librarian (expects 200) [TestCatalogingCopies / cataloging].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_all'].side_effect = [SAMPLE_BOOKS, SAMPLE_COPIES]
        resp = librarian_client.get('/librarian/cataloging')
        assert resp.status_code == 200
        assert b'ACC-0015' in resp.data
        assert b'Edit Accession Copy' in resp.data
        assert b'2 copy/copies for' in resp.data

    def test_edit_accession_success(self, librarian_client, mock_db):
        """Validates edit accession success `/librarian/cataloging/accession/21/edit` as librarian (expects 302) [TestCatalogingCopies / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (UPDATE).
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].side_effect = [SAMPLE_ACC_ROW, None]
        resp = librarian_client.post('/librarian/cataloging/accession/21/edit', data={
            'accession_number': '250099',
            'source': 'donation',
        })
        assert resp.status_code == 302
        assert 'modal=editAccessionModal' in resp.location
        assert 'mstatus=success' in resp.location
        call_args = mock_db['execute'].call_args_list[0]
        assert 'UPDATE accession_log' in call_args[0][0]
        assert 'updated_at' in call_args[0][0]
        assert 'updated_by' in call_args[0][0]
        assert 'shelf_location' in call_args[0][0]
        assert call_args[0][1] == ('250099', 'donation', None, '3', 21)

    def test_edit_accession_shelf_saved(self, librarian_client, mock_db):
        """Validates edit accession shelf saved `/librarian/cataloging/accession/21/edit` as librarian (expects 302) [TestCatalogingCopies / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].side_effect = [SAMPLE_ACC_ROW, None]
        resp = librarian_client.post('/librarian/cataloging/accession/21/edit', data={
            'accession_number': '250099',
            'source': 'donation',
            'shelf_location': '2F-A3',
        })
        assert resp.status_code == 302
        assert 'mstatus=success' in resp.location
        call_args = mock_db['execute'].call_args_list[0]
        assert call_args[0][1] == ('250099', 'donation', '2F-A3', '3', 21)

    def test_edit_accession_shelf_too_long(self, librarian_client, mock_db):
        """Validates edit accession shelf too long `/librarian/cataloging/accession/21/edit` as librarian (expects 302) [TestCatalogingCopies / cataloging].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = SAMPLE_ACC_ROW
        resp = librarian_client.post('/librarian/cataloging/accession/21/edit', data={
            'accession_number': '250099',
            'shelf_location': 'S' * 51,
        })
        assert resp.status_code == 302
        assert 'mstatus=error' in resp.location
        assert all('UPDATE accession_log' not in c[0][0] for c in mock_db['execute'].call_args_list)

    def test_edit_accession_duplicate(self, librarian_client, mock_db):
        """Validates edit accession duplicate `/librarian/cataloging/accession/21/edit` as librarian (expects 302) [TestCatalogingCopies / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (UPDATE).
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].side_effect = [SAMPLE_ACC_ROW, (99, '250099', 2, 3, '2025-01-01', 'purchase')]
        resp = librarian_client.post('/librarian/cataloging/accession/21/edit', data={
            'accession_number': '250099',
        })
        assert resp.status_code == 302
        assert 'modal=editAccessionModal' in resp.location
        assert 'mstatus=error' in resp.location
        assert all('UPDATE accession_log' not in c[0][0] for c in mock_db['execute'].call_args_list)

    def test_edit_accession_missing_number(self, librarian_client, mock_db):
        """Validates edit accession missing number `/librarian/cataloging/accession/21/edit` as librarian (expects 302) [TestCatalogingCopies / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (UPDATE).
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].return_value = SAMPLE_ACC_ROW
        resp = librarian_client.post('/librarian/cataloging/accession/21/edit', data={
            'accession_number': '',
        })
        assert resp.status_code == 302
        assert 'modal=editAccessionModal' in resp.location
        assert 'mstatus=error' in resp.location
        assert all('UPDATE accession_log' not in c[0][0] for c in mock_db['execute'].call_args_list)

    def test_edit_accession_not_found(self, librarian_client, mock_db):
        """Validates edit accession not found `/librarian/cataloging/accession/999/edit` as librarian (expects 302) [TestCatalogingCopies / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (UPDATE).
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].return_value = None
        resp = librarian_client.post('/librarian/cataloging/accession/999/edit', data={
            'accession_number': '250099',
        })
        assert resp.status_code == 302
        assert all('UPDATE accession_log' not in c[0][0] for c in mock_db['execute'].call_args_list)

    def test_delete_accession_success(self, librarian_client, mock_db):
        """Validates delete accession success `/librarian/cataloging/accession/21/delete` as librarian (expects 302) [TestCatalogingCopies / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (DELETE FROM).
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].side_effect = [SAMPLE_ACC_ROW, None]
        resp = librarian_client.post('/librarian/cataloging/accession/21/delete')
        assert resp.status_code == 302
        call_args = mock_db['execute'].call_args_list[0]
        assert 'DELETE FROM accession_log' in call_args[0][0]
        assert call_args[0][1] == (21,)

    def test_delete_accession_referenced(self, librarian_client, mock_db):
        """Validates delete accession referenced `/librarian/cataloging/accession/21/delete` as librarian (expects 302) [TestCatalogingCopies / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (DELETE FROM).
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].side_effect = [SAMPLE_ACC_ROW, (1,)]
        resp = librarian_client.post('/librarian/cataloging/accession/21/delete')
        assert resp.status_code == 302
        assert all('DELETE FROM accession_log' not in c[0][0] for c in mock_db['execute'].call_args_list)


class TestCatalogingSearch:
    def test_search_by_title(self, librarian_client, mock_db):
        """Validates search by title `/librarian/cataloging?q=Algorithms&field=title` as librarian (expects 200) [TestCatalogingSearch / cataloging].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_all'].return_value = [SAMPLE_BOOKS[0]]
        mock_db['fetch_one'].return_value = (1,)
        resp = librarian_client.get('/librarian/cataloging?q=Algorithms&field=title')
        assert resp.status_code == 200
        assert b'Algorithms' in resp.data

    def test_search_by_author(self, librarian_client, mock_db):
        """Validates search by author `/librarian/cataloging?q=Martin&field=author` as librarian (expects 200) [TestCatalogingSearch / cataloging].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_all'].return_value = [SAMPLE_BOOKS[1]]
        mock_db['fetch_one'].return_value = (1,)
        resp = librarian_client.get('/librarian/cataloging?q=Martin&field=author')
        assert resp.status_code == 200

    def test_search_no_results(self, librarian_client, mock_db):
        """Validates search no results `/librarian/cataloging?q=zzzxxx` as librarian (expects 200) [TestCatalogingSearch / cataloging].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_all'].return_value = []
        mock_db['fetch_one'].return_value = (0,)
        resp = librarian_client.get('/librarian/cataloging?q=zzzxxx')
        assert resp.status_code == 200

    def test_search_all_fields_matches_accession(self, librarian_client, mock_db):
        """Validates search all fields matches accession `/librarian/cataloging?q=ACC-123456` as librarian (expects 200) [TestCatalogingSearch / cataloging].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_all'].return_value = [SAMPLE_BOOKS[0]]
        mock_db['fetch_one'].return_value = (1,)
        resp = librarian_client.get('/librarian/cataloging?q=ACC-123456')
        assert resp.status_code == 200
        search_call = next(
            c for c in mock_db['fetch_all'].call_args_list
            if 'LIMIT %s OFFSET %s' in c[0][0]
        )
        sql, args = search_call[0]
        assert 'accession_log' in sql
        assert args == ('%ACC-123456%', '%ACC-123456%', '%ACC-123456%', '%ACC-123456%', '%ACC-123456%', 20, 0)

    def test_pagination(self, librarian_client, mock_db):
        """Validates pagination `/librarian/cataloging?page=1` as librarian (expects 200) [TestCatalogingSearch / cataloging].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_all'].return_value = SAMPLE_BOOKS
        mock_db['fetch_one'].return_value = (3,)
        resp = librarian_client.get('/librarian/cataloging?page=1')
        assert resp.status_code == 200
        assert b'Showing' in resp.data


class TestCopyStatusFilter:
    def test_overdue_builds_exists_query(self, mock_db):
        """Validates overdue builds exists query [TestCopyStatusFilter / cataloging].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        from app.cataloging.models import get_books_by_copy_status
        mock_db['fetch_all'].return_value = []
        get_books_by_copy_status('overdue')
        query = mock_db['fetch_all'].call_args[0][0]
        assert 'circulation_records' in query
        assert "transaction_status = 'overdue'" in query
        assert 'accession_numbers' in query

    def test_lost_damaged_queries(self, mock_db):
        """Validates lost damaged queries [TestCopyStatusFilter / cataloging].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        from app.cataloging.models import get_books_by_copy_status
        mock_db['fetch_all'].return_value = []
        get_books_by_copy_status('lost_damaged')
        assert "'lost', 'damaged'" in mock_db['fetch_all'].call_args[0][0]

    def test_invalid_copy_status_returns_empty(self, mock_db):
        """Validates invalid copy status returns empty [TestCopyStatusFilter / cataloging].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        from app.cataloging.models import get_books_by_copy_status
        assert get_books_by_copy_status('bogus') == []
        assert mock_db['fetch_all'].call_count == 0

    def test_route_filters_overdue(self, librarian_client, mock_db):
        """Validates route filters overdue `/librarian/cataloging?copy_status=overdue` as librarian (expects 200) [TestCopyStatusFilter / cataloging].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_all'].side_effect = [SAMPLE_BOOKS, []]
        resp = librarian_client.get('/librarian/cataloging?copy_status=overdue')
        assert resp.status_code == 200
        assert b'Overdue' in resp.data
        queries = [c[0][0] for c in mock_db['fetch_all'].call_args_list]
        assert any('EXISTS' in q for q in queries)

    def test_route_invalid_copy_status_falls_back(self, librarian_client, mock_db):
        """Validates route invalid copy status falls back `/librarian/cataloging?copy_status=bogus` as librarian (expects 200) [TestCopyStatusFilter / cataloging].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_all'].side_effect = [SAMPLE_BOOKS, []]
        resp = librarian_client.get('/librarian/cataloging?copy_status=bogus')
        assert resp.status_code == 200
        queries = [c[0][0] for c in mock_db['fetch_all'].call_args_list]
        assert all('EXISTS' not in q for q in queries)

    def test_route_student_forbidden(self, student_client, mock_db):
        """Validates route student forbidden `/librarian/cataloging?copy_status=overdue` as student (expects 302) [TestCopyStatusFilter / cataloging].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = student_client.get('/librarian/cataloging?copy_status=overdue')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location


class TestSqlPagination:
    """Perf regression tests: page views must page in SQL (COUNT + LIMIT /
    OFFSET), never materialize the whole catalog in Python."""

    def test_filtered_search_pages_in_sql(self, mock_db):
        """Validates filtered search pages in sql [TestSqlPagination / cataloging].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        from app.cataloging.models import search_books_filtered
        mock_db['fetch_one'].return_value = (120,)
        mock_db['fetch_all'].return_value = SAMPLE_BOOKS[:1]
        rows, total = search_books_filtered('harry', page=2, per_page=50)
        assert total == 120
        assert rows == SAMPLE_BOOKS[:1]
        count_q = mock_db['fetch_one'].call_args[0][0]
        assert 'COUNT(*)' in count_q
        page_q, page_args = mock_db['fetch_all'].call_args[0]
        assert 'LIMIT %s OFFSET %s' in page_q
        assert page_args[-2:] == (50, 50)

    def test_filtered_search_clamps_bad_page(self, mock_db):
        """Validates filtered search clamps bad page [TestSqlPagination / cataloging].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        from app.cataloging.models import search_books_filtered
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        rows, total = search_books_filtered('x', page=-3, per_page=50)
        assert (rows, total) == ([], 0)
        assert mock_db['fetch_all'].call_args[0][1][-2:] == (50, 0)

    def test_staff_list_pages_in_sql(self, mock_db):
        """Validates staff list pages in sql [TestSqlPagination / cataloging].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        from app.cataloging.models import (
            get_all_books_paginated, get_books_by_status_paginated,
            get_books_by_copy_status_paginated,
        )
        mock_db['fetch_one'].return_value = (4500,)
        mock_db['fetch_all'].return_value = SAMPLE_BOOKS[:1]
        rows, total = get_all_books_paginated(page=1, per_page=20)
        assert total == 4500
        assert 'LIMIT %s OFFSET %s' in mock_db['fetch_all'].call_args[0][0]
        rows, total = get_books_by_status_paginated('archived', page=2, per_page=20)
        assert total == 4500
        assert mock_db['fetch_all'].call_args[0][1][-2:] == (20, 20)
        rows, total = get_books_by_copy_status_paginated('overdue', page=1, per_page=20)
        assert total == 4500
        assert 'EXISTS' in mock_db['fetch_all'].call_args[0][0]

    def test_staff_copy_status_unknown_returns_empty(self, mock_db):
        """Validates staff copy status unknown returns empty [TestSqlPagination / cataloging].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        from app.cataloging.models import get_books_by_copy_status_paginated
        assert get_books_by_copy_status_paginated('bogus') == ([], 0)
        assert mock_db['fetch_one'].call_count == 0
        assert mock_db['fetch_all'].call_count == 0

    def test_staff_route_clamps_past_end_page(self, librarian_client, mock_db):
        """Validates staff route clamps past end page `/librarian/cataloging?page=99` as librarian (expects 200) [TestSqlPagination / cataloging].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['fetch_one'].return_value = (3,)
        mock_db['fetch_all'].return_value = SAMPLE_BOOKS
        resp = librarian_client.get('/librarian/cataloging?page=99')
        assert resp.status_code == 200

    def test_public_route_clamps_past_end_page(self, client, mock_db):
        """Validates public route clamps past end page `/catalog?q=harry&page=99` (expects 200) [TestSqlPagination / cataloging].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = (3,)
        mock_db['fetch_all'].side_effect = [
            SAMPLE_BOOKS, [],  # page 99 attempt + categories
            SAMPLE_BOOKS, [],  # clamped page 1 re-fetch + categories
        ]
        resp = client.get('/catalog?q=harry&page=99')
        assert resp.status_code == 200


class TestFilterCombinations:
    """Category + type filters must AND together (AND binds tighter than OR
    in SQL, so the physical-type OR needs explicit parens)."""

    def test_physical_or_is_parenthesized(self, mock_db):
        """Validates physical or is parenthesized [TestFilterCombinations / cataloging].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        from app.cataloging.models import search_books_filtered
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        search_books_filtered('', category='Fiction', material_type='physical')
        page_q = mock_db['fetch_all'].call_args[0][0]
        assert '(material_type IS NULL OR material_type != %s)' in page_q
        count_q = mock_db['fetch_one'].call_args[0][0]
        assert '(material_type IS NULL OR material_type != %s)' in count_q

    def test_category_and_physical_both_bound(self, mock_db):
        """Validates category and physical both bound [TestFilterCombinations / cataloging].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        from app.cataloging.models import search_books_filtered
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        search_books_filtered('', category='Fiction', material_type='physical')
        _, page_args = mock_db['fetch_all'].call_args[0]
        assert 'Fiction' in page_args
        assert 'E-Book' in page_args
        assert page_args.index('Fiction') < page_args.index('E-Book')

    def test_category_ebook_combines(self, mock_db):
        """Validates category ebook combines [TestFilterCombinations / cataloging].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        from app.cataloging.models import search_books_filtered
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        search_books_filtered('', category='Fiction', material_type='ebook')
        page_q, page_args = mock_db['fetch_all'].call_args[0]
        assert 'subject_classification = %s' in page_q
        assert 'material_type = %s' in page_q
        assert tuple(page_args[:2]) == ('Fiction', 'E-Book')

    def test_category_physical_route_renders(self, client, mock_db):
        """Validates category physical route renders `/catalog?category=Fiction&material_type=physical` (expects 200) [TestFilterCombinations / cataloging].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].side_effect = [[], [], []]
        resp = client.get('/catalog?category=Fiction&material_type=physical')
        assert resp.status_code == 200
        page_args = mock_db['fetch_all'].call_args_list[0][0]
        assert 'Fiction' in page_args[1]
        assert 'E-Book' in page_args[1]


class TestBookTypes:
    """Dynamic book-type facets: sidebar/landing show only types with
    active items, and each type filters the catalog to its items."""

    def test_exact_type_filters_to_that_type(self, mock_db):
        """Validates exact book-type filter builds material_type = %s [TestBookTypes / cataloging].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates catalog data or listing/sort is wrong."""
        from app.cataloging.models import search_books_filtered
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        search_books_filtered('', material_type='Thesis')
        page_q, page_args = mock_db['fetch_all'].call_args[0]
        assert 'material_type = %s' in page_q
        assert 'Thesis' in page_args

    def test_distinct_types_only_active_nonempty(self, mock_db):
        """Validates distinct book types query scopes to active non-empty [TestBookTypes / cataloging].
    If fails: likely model SQL changed (SELECT).
    Failure indicates catalog data or listing/sort is wrong."""
        from app.cataloging.models import get_distinct_material_types
        mock_db['fetch_all'].return_value = [('Book', 5)]
        assert get_distinct_material_types() == [('Book', 5)]
        q = mock_db['fetch_all'].call_args[0][0]
        assert "catalog_status = 'active'" in q
        assert 'GROUP BY material_type' in q

    def test_sidebar_hides_types_without_items(self, client, mock_db):
        """Validates sidebar hides book types without items `/catalog?q=test` (expects 200) [TestBookTypes / cataloging].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_all'].side_effect = [
            SAMPLE_BOOKS,          # search_books_filtered books
            [],                    # get_distinct_categories
            [('Book', 2)],         # only Book has items
        ]
        body = client.get('/catalog?q=test').data.decode()
        assert 'Book Type' in body
        assert '>Book<' in body
        assert '>Thesis<' not in body
        assert '>Reference<' not in body

    def test_type_button_goes_to_filtered_catalog(self, client, mock_db):
        """Validates landing book-type button links to filtered catalog `/` (expects 200) [TestBookTypes / main].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates main is broken for this case (users see wrong page, blocked action, or bad data)."""
        mock_db['fetch_all'].side_effect = [
            [SAMPLE_BOOKS[0]],      # get_recent_books
            [('Book', 2), ('Thesis', 1)],  # get_distinct_material_types
        ]
        body = client.get('/').data.decode()
        assert 'Browse by Book Type' in body
        assert 'material_type=Thesis' in body
        assert 'material_type=Reference' not in body
        # Clicking through shows the catalogued Thesis items.
        mock_db['fetch_all'].side_effect = [
            [SAMPLE_BOOKS[0]],      # search_books_filtered books
            [],                    # get_distinct_categories
            [('Book', 2), ('Thesis', 1)],
        ]
        mock_db['fetch_one'].return_value = (1,)
        resp = client.get('/catalog?material_type=Thesis')
        assert resp.status_code == 200
        assert 'Book Type: Thesis' in resp.data.decode()


class TestPublicCatalog:
    def test_public_catalog_all(self, client, mock_db):
        # Bare /catalog is empty by default: only facet queries run, no book search.
        """Validates public catalog all `/catalog` (expects 200) [TestPublicCatalog / cataloging].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_all'].return_value = []
        resp = client.get('/catalog')
        assert resp.status_code == 200
        assert mock_db['fetch_all'].call_count == 2
        body = resp.get_data(as_text=True)
        assert 'Search to explore the catalog' in body

    def test_public_catalog_search(self, client, mock_db):
        """Validates public catalog search `/catalog?q=Algorithms` (expects 200) [TestPublicCatalog / cataloging].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_all'].return_value = [SAMPLE_BOOKS[0]]
        resp = client.get('/catalog?q=Algorithms')
        assert resp.status_code == 200

    def test_public_catalog_no_results(self, client, mock_db):
        """Validates public catalog no results `/catalog?q=nonexistent` (expects 200) [TestPublicCatalog / cataloging].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_all'].return_value = []
        resp = client.get('/catalog?q=nonexistent')
        assert resp.status_code == 200

    def test_public_catalog_filters(self, client, mock_db):
        """Validates public catalog filters `/catalog?q=harry&sort_by=title&category=Fiction&material_type=ebook&availability=available&year_from=2000&year_to=2026` (expects 200) [TestPublicCatalog / cataloging].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_all'].side_effect = [
            SAMPLE_BOOKS,                # search_books_filtered books
            [('Fiction',), ('Reference',)],  # get_distinct_categories
            [('Book', 2), ('E-Book', 1)],  # get_distinct_material_types
        ]
        resp = client.get('/catalog?q=harry&sort_by=title&category=Fiction&material_type=ebook&availability=available&year_from=2000&year_to=2026')
        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        assert 'Sort by relevance' in body
        assert 'Fiction' in body
        assert 'Book Type' in body
        assert 'E-Book' in body
        assert 'Active filters' in body

    def test_public_catalog_filter_params_passed(self, client, mock_db):
        """Validates public catalog filter params passed `/catalog?category=Fiction&material_type=physical&availability=borrowed&sort_by=year_desc&year_from=2010&year_to=2020` (expects 200) [TestPublicCatalog / cataloging].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_all'].side_effect = [
            [],                            # search_books_filtered books
            [],                            # get_distinct_categories
            [],                            # get_distinct_material_types
        ]
        resp = client.get('/catalog?category=Fiction&material_type=physical&availability=borrowed&sort_by=year_desc&year_from=2010&year_to=2020')
        assert resp.status_code == 200
        assert b'No books found' in resp.data

    def test_public_catalog_sidebar_sections(self, client, mock_db):
        """Validates public catalog sidebar sections `/catalog?q=test` (expects 200) [TestPublicCatalog / cataloging].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_all'].side_effect = [
            SAMPLE_BOOKS,                  # search_books_filtered books
            [],                            # get_distinct_categories
            [('Book', 2)],                 # get_distinct_material_types
        ]
        resp = client.get('/catalog?q=test')
        assert resp.status_code == 200
        assert mock_db['fetch_all'].call_count == 3
        body = resp.get_data(as_text=True)
        for label in ['Sort', 'Category', 'Book Type', 'Year']:
            assert label in body, f'missing sidebar section: {label}'
        assert 'Availability' not in body

    def test_public_catalog_pagination(self, client, mock_db):
        """Validates public catalog pagination `/catalog?q=Book` (expects 200) [TestPublicCatalog / cataloging].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        many_books = [
            (i, f'Book {i}', 'Author', None, None, 2000 + i,
             'Fiction', None, None, 'Book',
             None, 'active', '2024-01-01')
            for i in range(1, 121)
        ]
        mock_db['fetch_one'].return_value = (120,)
        mock_db['fetch_all'].side_effect = [
            many_books[:50],             # search_books_filtered page 1
            [],                          # get_distinct_categories
            [],                          # get_distinct_material_types
        ]
        # Empty catalog by default — must provide a search/filter to paginate
        resp = client.get('/catalog?q=Book')
        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        assert '>1 - 50</span> of <span class="font-medium text-slate-900 dark:text-slate-100">120</span>' in body
        assert 'Next' in body

        mock_db['fetch_all'].side_effect = [many_books[100:], [], []]
        mock_db['fetch_one'].return_value = (120,)
        resp2 = client.get('/catalog?q=Book&page=3')
        assert resp2.status_code == 200
        body2 = resp2.get_data(as_text=True)
        assert '>101 - 120</span> of <span class="font-medium text-slate-900 dark:text-slate-100">120</span>' in body2

    def test_public_catalog_empty_by_default(self, client, mock_db):
        # Visiting /catalog with no search term or filter should show empty prompt, no DB search
        """Validates public catalog empty by default `/catalog` (expects 200) [TestPublicCatalog / cataloging].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_all'].return_value = []  # facet queries -> []
        resp = client.get('/catalog')
        assert resp.status_code == 200
        assert mock_db['fetch_all'].call_count == 2
        body = resp.get_data(as_text=True)
        assert 'Search to explore the catalog' in body or 'Start searching' in body
        # Should not show pagination or footer counts when empty
        assert 'Next' not in body

    def test_public_catalog_sort_only_shows_results(self, client, mock_db):
        # Bookmarked sorted view: sort_by alone counts as a search (no empty state).
        """Validates public catalog sort only shows results `/catalog?sort_by=title` (expects 200) [TestPublicCatalog / cataloging].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_all'].side_effect = [
            SAMPLE_BOOKS,  # search_books_filtered books
            [],            # get_distinct_categories
            [],            # get_distinct_material_types
        ]
        resp = client.get('/catalog?sort_by=title')
        assert resp.status_code == 200
        assert mock_db['fetch_all'].call_count == 3
        body = resp.get_data(as_text=True)
        assert SAMPLE_BOOKS[0][1] in body
        assert 'Sort: Title A-Z' in body

    def test_public_catalog_availability_pill(self, client, mock_db):
        """Validates public catalog availability pill `/catalog?availability=available` (expects 200) [TestPublicCatalog / cataloging].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_all'].side_effect = [
            SAMPLE_BOOKS,  # search_books_filtered books
            [],            # get_distinct_categories
            [],            # get_distinct_material_types
        ]
        resp = client.get('/catalog?availability=available')
        assert resp.status_code == 200
        assert b'Availability: Available' not in resp.data

    def test_year_filter_options_are_dynamic(self, client, mock_db):
        """Validates year filter options are dynamic `/catalog` [TestPublicCatalog / cataloging].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates catalog data or listing/sort is wrong."""
        from datetime import datetime
        mock_db['fetch_all'].return_value = []
        body = client.get('/catalog').data.decode()
        current = datetime.now().year
        assert 'Year Published' in body
        assert '>Year</h3>' not in body
        for i, year in enumerate(range(current, current - 4, -1)):
            assert f'value="{year}"' in body, year
        positions = [body.index(f'Since {current - i}') for i in range(4)]
        assert positions == sorted(positions)
        assert 'Custom Year Range' in body
        assert 'value="since_2023"' not in body
        assert 'Any time' not in body

    def test_year_preset_filters_from_year(self, client, mock_db):
        """Validates year preset filters from year (expects 200) [TestPublicCatalog / cataloging].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        from datetime import datetime
        current = datetime.now().year
        mock_db['fetch_all'].side_effect = [[], [], []]
        resp = client.get(f'/catalog?year_preset={current}')
        assert resp.status_code == 200
        params = mock_db['fetch_all'].call_args_list[0][0][1]
        assert current in params

    def test_legacy_year_presets_still_work(self, client, mock_db):
        """Validates legacy year presets still work `/catalog?year_preset=since_last_year` (expects 200) [TestPublicCatalog / cataloging].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        from datetime import datetime
        current = datetime.now().year
        mock_db['fetch_all'].side_effect = [[], [], []]
        resp = client.get('/catalog?year_preset=since_last_year')
        assert resp.status_code == 200
        params = mock_db['fetch_all'].call_args_list[0][0][1]
        assert (current - 1) in params

    def test_custom_year_range(self, client, mock_db):
        """Validates custom year range `/catalog?year_preset=custom&year_from=2000&year_to=2010` (expects 200) [TestPublicCatalog / cataloging].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_all'].side_effect = [[], [], []]
        resp = client.get(
            '/catalog?year_preset=custom&year_from=2000&year_to=2010')
        assert resp.status_code == 200
        params = mock_db['fetch_all'].call_args_list[0][0][1]
        assert 2000 in params and 2010 in params

    def test_relevance_tiers_in_order(self, mock_db):
        """Validates relevance tiers in order [TestPublicCatalog / cataloging].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        from app.cataloging.models import _relevance_order
        order, params = _relevance_order('harry')
        tiers = [i for i in range(7)]
        positions = [order.index(f'THEN {i}') for i in tiers]
        assert positions == sorted(positions)
        assert 'LOWER(title) = LOWER(%s)' in order
        assert order.index('title ILIKE') < order.index('author ILIKE')
        assert order.index('author ILIKE') < order.index('isbn ILIKE')
        assert order.index('isbn ILIKE') < order.index(
            'subject_classification ILIKE')
        assert 'title ASC, author ASC' in order
        assert params == ('harry', 'harry%', '% harry%', '%harry%',
                          '%harry%', '%harry%', '%harry%')

    def test_relevance_needs_a_term(self, mock_db):
        """Validates relevance needs a term [TestPublicCatalog / cataloging].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        from app.cataloging.models import _relevance_order
        assert _relevance_order('') == (None, ())
        assert _relevance_order(None) == (None, ())
        assert _relevance_order('   ') == (None, ())

    def test_relevance_scores_a_search(self, mock_db):
        """Validates relevance scores a search [TestPublicCatalog / cataloging].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        from app.cataloging.models import search_books_filtered
        mock_db['fetch_one'].return_value = (0,)
        search_books_filtered('harry', None, page=1, per_page=50)
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'ORDER BY CASE' in query
        assert params == ('%harry%', '%harry%', '%harry%', '%harry%',
                          'harry', 'harry%', '% harry%', '%harry%',
                          '%harry%', '%harry%', '%harry%', 50, 0)

    def test_no_query_means_alpha_not_scored(self, mock_db):
        """Validates no query means alpha not scored [TestPublicCatalog / cataloging].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        from app.cataloging.models import search_books_filtered
        mock_db['fetch_one'].return_value = (0,)
        search_books_filtered('', None, page=1, per_page=50)
        query = mock_db['fetch_all'].call_args[0][0]
        assert 'ORDER BY CASE' not in query

    def test_explicit_sort_beats_relevance(self, mock_db):
        """Validates explicit sort beats relevance [TestPublicCatalog / cataloging].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        from app.cataloging.models import search_books_filtered
        mock_db['fetch_one'].return_value = (0,)
        search_books_filtered('harry', None, page=1, per_page=50,
                              sort_by='title')
        query = mock_db['fetch_all'].call_args[0][0]
        assert 'ORDER BY CASE' not in query
        assert 'ORDER BY title ASC' in query

    def test_default_search_hits_relevance_path(self, client, mock_db):
        """Validates default search hits relevance path `/catalog?q=harry` (expects 200) [TestPublicCatalog / cataloging].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_all'].side_effect = [
            SAMPLE_BOOKS,  # search_books_filtered books
            [],            # get_distinct_categories
            [],            # get_distinct_material_types
        ]
        resp = client.get('/catalog?q=harry')
        assert resp.status_code == 200
        query = mock_db['fetch_all'].call_args_list[0][0][0]
        assert 'ORDER BY CASE' in query

    def test_book_info_found(self, client, mock_db):
        """Validates book info found `/book/1` (expects 200) [TestPublicCatalog / cataloging].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = SAMPLE_BOOKS[0]
        mock_db['fetch_all'].return_value = []
        resp = client.get('/book/1')
        assert resp.status_code == 200
        assert b'Introduction to Algorithms' in resp.data

    def test_book_info_not_found(self, client, mock_db):
        """Validates book info not found `/book/999` (expects 302) [TestPublicCatalog / cataloging].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = None
        resp = client.get('/book/999')
        assert resp.status_code == 302

    def test_book_info_with_accessions(self, client, mock_db):
        """Validates book info with accessions `/book/1` (expects 200) [TestPublicCatalog / cataloging].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = SAMPLE_BOOKS[0]
        mock_db['fetch_all'].side_effect = [
            [(1, '250001', 1, 4, '2025-01-10', 'purchase')],  # accessions
            [],  # no active loans -> copy available
            [],  # borrower map
        ]
        resp = client.get('/book/1')
        assert resp.status_code == 200
        assert b'1 of 1' in resp.data
        assert b'Borrow' in resp.data
        assert b'Reserve' in resp.data

    def test_book_info_all_borrowed(self, client, mock_db):
        """Validates book info all borrowed `/book/1` (expects 200) [TestPublicCatalog / cataloging].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = SAMPLE_BOOKS[0]
        mock_db['fetch_all'].side_effect = [
            [(1, '250001', 1, 4, '2025-01-10', 'purchase')],  # accessions
            [(1,)],  # active loan on accession 1 -> none available
            [(1, 1)],  # borrower map
        ]
        resp = client.get('/book/1')
        assert resp.status_code == 200
        assert b'No copies available' in resp.data
        assert b'Borrow' in resp.data
        assert b'Reserve' in resp.data


def _csv_file(content, filename='books.csv'):
    """Build a Werkzeug FileStorage-like upload from a CSV string."""
    return (io.BytesIO(content.encode('utf-8')), filename)


class TestBulkImport:
    """Bulk CSV import: header detection, encoding, validation, RBAC, edge cases."""

    VALID_ROW = ('Book A', 'Author A', 'ACC-001', '978-1', '1st', 'Pub A', 2023,
                 'CS', 'QA100', 'Book', 'Desc A', 'purchase')

    @staticmethod
    def _make_csv(rows, headers=None):
        """Test helper _make_csv: build mocked data or DB stub for the test."""
        if headers is None:
            headers = ['title', 'author', 'accession_number', 'isbn', 'edition', 'publisher',
                       'year', 'subject', 'call_number', 'material_type', 'description',
                       'source']
        out = io.StringIO()
        w = csv.writer(out)
        w.writerow(headers)
        for r in rows:
            w.writerow(r)
        return out.getvalue()

    def _assert_error(self, resp, expected_status=400):
        """Test helper _assert_error: build mocked data or DB stub for the test."""
        assert resp.status_code == expected_status
        data = resp.get_json()
        assert data is not None
        assert 'error' in data

    def _assert_job(self, resp):
        """Test helper _assert_job: build mocked data or DB stub for the test."""
        assert resp.status_code == 200
        data = resp.get_json()
        assert data is not None
        assert 'job_id' in data
        assert data['redirect'] is not None

    def test_bulk_import_rbac_student(self, student_client):
        """Validates bulk import rbac student `/librarian/cataloging/bulk-import` as student (expects 302) [TestBulkImport / cataloging].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = student_client.post('/librarian/cataloging/bulk-import', data={
            'file': _csv_file(self._make_csv([self.VALID_ROW])),
        })
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_bulk_import_rbac_faculty(self, faculty_client):
        """Validates bulk import rbac faculty `/librarian/cataloging/bulk-import` as faculty (expects 302) [TestBulkImport / cataloging].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = faculty_client.post('/librarian/cataloging/bulk-import', data={
            'file': _csv_file(self._make_csv([self.VALID_ROW])),
        })
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_bulk_import_unauthenticated(self, client):
        """Validates bulk import unauthenticated `/librarian/cataloging/bulk-import` (expects 302) [TestBulkImport / cataloging].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = client.post('/librarian/cataloging/bulk-import', data={
            'file': _csv_file(self._make_csv([self.VALID_ROW])),
        })
        assert resp.status_code == 302
        assert '/login' in resp.location

    def test_bulk_import_no_file(self, librarian_client):
        """Validates bulk import no file `/librarian/cataloging/bulk-import` as librarian [TestBulkImport / cataloging].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = librarian_client.post('/librarian/cataloging/bulk-import')
        self._assert_error(resp, 400)

    def test_bulk_import_empty_filename(self, librarian_client):
        """Validates bulk import empty filename `/librarian/cataloging/bulk-import` as librarian [TestBulkImport / cataloging].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = librarian_client.post('/librarian/cataloging/bulk-import', data={
            'file': (io.BytesIO(b''), ''),
        })
        self._assert_error(resp, 400)

    def test_bulk_import_wrong_extension(self, librarian_client):
        """Validates bulk import wrong extension `/librarian/cataloging/bulk-import` as librarian [TestBulkImport / cataloging].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = librarian_client.post('/librarian/cataloging/bulk-import', data={
            'file': (io.BytesIO(b'a,b,c'), 'books.txt'),
        })
        self._assert_error(resp, 400)

    def test_bulk_import_empty_file(self, librarian_client, mock_db):
        """Validates bulk import empty file `/librarian/cataloging/bulk-import` as librarian [TestBulkImport / cataloging].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = librarian_client.post('/librarian/cataloging/bulk-import', data={
            'file': _csv_file(''),
        })
        self._assert_error(resp, 400)

    def test_bulk_import_headers_only(self, librarian_client, mock_db):
        """Validates bulk import headers only `/librarian/cataloging/bulk-import` as librarian [TestBulkImport / cataloging].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = librarian_client.post('/librarian/cataloging/bulk-import', data={
            'file': _csv_file('title,author,accession_number,year\n'),
        })
        self._assert_job(resp)

    def test_bulk_import_missing_required_columns(self, librarian_client, mock_db):
        """Validates bulk import missing required columns `/librarian/cataloging/bulk-import` as librarian [TestBulkImport / cataloging].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = librarian_client.post('/librarian/cataloging/bulk-import', data={
            'file': _csv_file(self._make_csv([('NoAuthor',)], headers=['title'])),
        })
        self._assert_error(resp, 400)

    def test_bulk_import_missing_accession_column(self, librarian_client, mock_db):
        """Validates bulk import missing accession column `/librarian/cataloging/bulk-import` as librarian [TestBulkImport / cataloging].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = librarian_client.post('/librarian/cataloging/bulk-import', data={
            'file': _csv_file(self._make_csv([('Title', 'Author')], headers=['title', 'author'])),
        })
        self._assert_error(resp, 400)

    def test_bulk_import_success(self, librarian_client, mock_db):
        """Validates bulk import success `/librarian/cataloging/bulk-import` as librarian [TestBulkImport / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['execute'].return_value = [(1,)]
        mock_db['fetch_one'].return_value = None
        csv_content = self._make_csv([
            ('Title One', 'Author One', 'ACC-001', '978-111', '2nd', 'Pub1', 2020,
             'Science', 'Q1', 'Book', 'First book', 'purchase'),
            ('Title Two', 'Author Two', 'ACC-002', '978-222', '', 'Pub2', 2021,
             'Math', 'Q2', 'Book', '', ''),
        ])
        resp = librarian_client.post('/librarian/cataloging/bulk-import', data={
            'file': _csv_file(csv_content),
        })
        self._assert_job(resp)

    def test_bulk_import_runs_inline_without_worker_thread(
            self, librarian_client, mock_db):
        """Validates bulk import runs inline without worker thread `/librarian/cataloging/bulk-import` as librarian [TestBulkImport / cataloging].
    If fails: likely template text/context changed or mock fetch_* shape mismatched; wrong/absent SQL call or placeholder mismatch.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed).

No stray worker threads: under TESTING the import runs inline so
        no thread outlives the mocked database (post-teardown crashes)."""
        import threading
        mock_db['execute'].return_value = [(1,)]
        mock_db['fetch_one'].return_value = None
        before = set(threading.enumerate())
        resp = librarian_client.post('/librarian/cataloging/bulk-import', data={
            'file': _csv_file(self._make_csv([self.VALID_ROW])),
        })
        self._assert_job(resp)
        job_id = resp.get_json()['job_id']
        status = librarian_client.get(
            f'/librarian/cataloging/bulk-import/status/{job_id}').get_json()
        assert status['status'] == 'done'
        assert status['done'] == status['total'] == 1
        assert set(threading.enumerate()) <= before

    def test_bulk_import_headers_random_order(self, librarian_client, mock_db):
        """Validates bulk import headers random order `/librarian/cataloging/bulk-import` as librarian [TestBulkImport / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['execute'].return_value = [(1,)]
        mock_db['fetch_one'].return_value = None
        csv_content = self._make_csv(
            [('Author X', 'Title X', 'ACC-003', '2022', '978-333')],
            headers=['author', 'title', 'accession_number', 'year', 'isbn'],
        )
        resp = librarian_client.post('/librarian/cataloging/bulk-import', data={
            'file': _csv_file(csv_content),
        })
        self._assert_job(resp)

    def test_bulk_import_header_synonyms(self, librarian_client, mock_db):
        """Validates bulk import header synonyms `/librarian/cataloging/bulk-import` as librarian [TestBulkImport / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['execute'].return_value = [(1,)]
        mock_db['fetch_one'].return_value = None
        csv_content = self._make_csv(
            [('Synonym Book', 'Synonym Author', 'ACC-004')],
            headers=['Book Title', 'Author(s)', 'Accession Number'],
        )
        resp = librarian_client.post('/librarian/cataloging/bulk-import', data={
            'file': _csv_file(csv_content),
        })
        self._assert_job(resp)

    def test_bulk_import_partial_errors(self, librarian_client, mock_db):
        """Validates bulk import partial errors `/librarian/cataloging/bulk-import` as librarian [TestBulkImport / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['execute'].return_value = [(1,)]
        mock_db['fetch_one'].return_value = None
        csv_content = self._make_csv([
            ('Valid Title', 'Valid Author', 'ACC-005', '978-555'),
            ('', 'NoTitleAuthor', '', ''),
            ('OnlyTitle', '', '', ''),
            ('Another Valid', 'Another Author', 'ACC-006', '978-666'),
        ])
        resp = librarian_client.post('/librarian/cataloging/bulk-import', data={
            'file': _csv_file(csv_content),
        })
        self._assert_job(resp)

    def test_bulk_import_utf8_bom(self, librarian_client, mock_db):
        """Validates bulk import utf8 bom `/librarian/cataloging/bulk-import` as librarian [TestBulkImport / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['execute'].return_value = [(1,)]
        mock_db['fetch_one'].return_value = None
        csv_content = self._make_csv([('BOM Book', 'BOM Author', 'ACC-007')])
        resp = librarian_client.post('/librarian/cataloging/bulk-import', data={
            'file': (io.BytesIO(csv_content.encode('utf-8-sig')), 'books.csv'),
        })
        self._assert_job(resp)

    def test_bulk_import_latin1_encoding(self, librarian_client, mock_db):
        """Validates bulk import latin1 encoding `/librarian/cataloging/bulk-import` as librarian [TestBulkImport / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['execute'].return_value = [(1,)]
        mock_db['fetch_one'].return_value = None
        csv_content = self._make_csv([('José García', 'François', 'ACC-008')],
                                     headers=['title', 'author', 'accession_number'])
        resp = librarian_client.post('/librarian/cataloging/bulk-import', data={
            'file': (io.BytesIO(csv_content.encode('latin-1')), 'books.csv'),
        })
        self._assert_job(resp)

    def test_bulk_import_unicode_titles(self, librarian_client, mock_db):
        """Validates bulk import unicode titles `/librarian/cataloging/bulk-import` as librarian [TestBulkImport / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['execute'].return_value = [(1,)]
        mock_db['fetch_one'].return_value = None
        csv_content = self._make_csv([
            ('日本語の本', '著者名', 'ACC-009'),
            ('Русская книга', 'Автор', 'ACC-010'),
            ('中文图书', '作者', 'ACC-011'),
        ])
        resp = librarian_client.post('/librarian/cataloging/bulk-import', data={
            'file': _csv_file(csv_content),
        })
        self._assert_job(resp)

    def test_bulk_import_no_headers(self, librarian_client, mock_db):
        """Validates bulk import no headers `/librarian/cataloging/bulk-import` as librarian [TestBulkImport / cataloging].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        csv_content = 'value1,value2,value3'
        resp = librarian_client.post('/librarian/cataloging/bulk-import', data={
            'file': _csv_file(csv_content),
        })
        self._assert_error(resp, 400)

    def test_bulk_import_whitespace_headers(self, librarian_client, mock_db):
        """Validates bulk import whitespace headers `/librarian/cataloging/bulk-import` as librarian [TestBulkImport / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['execute'].return_value = [(1,)]
        mock_db['fetch_one'].return_value = None
        csv_content = self._make_csv(
            [('Whitespace Book', 'Whitespace Author', 'ACC-012')],
            headers=['  title  ', '  author  ', '  accession_number  '],
        )
        resp = librarian_client.post('/librarian/cataloging/bulk-import', data={
            'file': _csv_file(csv_content),
        })
        self._assert_job(resp)

    def test_bulk_import_large_file(self, librarian_client, mock_db):
        """Validates bulk import large file `/librarian/cataloging/bulk-import` as librarian [TestBulkImport / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['execute'].return_value = [(1,)]
        mock_db['fetch_one'].return_value = None
        rows = [(f'Book {i}', f'Author {i}', f'ACC-{i:04d}', f'978-{i:06d}') for i in range(500)]
        csv_content = self._make_csv(rows, headers=['title', 'author', 'accession_number', 'isbn'])
        resp = librarian_client.post('/librarian/cataloging/bulk-import', data={
            'file': _csv_file(csv_content),
        })
        self._assert_job(resp)

    def test_bulk_import_extra_unknown_headers(self, librarian_client, mock_db):
        """Validates bulk import extra unknown headers `/librarian/cataloging/bulk-import` as librarian [TestBulkImport / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        mock_db['execute'].return_value = [(1,)]
        mock_db['fetch_one'].return_value = None
        csv_content = self._make_csv(
            [('Extra Book', 'Extra Author', 'ACC-013', 'ShelfA', 'Donated')],
            headers=['title', 'author', 'accession_number', 'location', 'source'],
        )
        resp = librarian_client.post('/librarian/cataloging/bulk-import', data={
            'file': _csv_file(csv_content),
        })
        self._assert_job(resp)

    def test_bulk_import_accepts_others_source(self, app, mock_db):
        """Validates bulk import accepts others source [TestBulkImport / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        from app.cataloging.routes import _bulk_import_worker, _import_jobs
        mock_db['execute'].return_value = [(1,)]
        mock_db['fetch_one'].return_value = None
        _import_jobs['test-others-job'] = {
            'status': 'processing', 'total': 1, 'done': 0,
            'errors': [], 'message': None,
        }
        try:
            _bulk_import_worker(
                app, 'test-others-job',
                [{'title': 'Other Book', 'author': 'Other Author',
                  'accession_number': 'ACC-099', 'source': 'Others'}],
                {'title': 'title', 'author': 'author',
                 'accession_number': 'accession_number', 'source': 'source'},
                3,
            )
        finally:
            _import_jobs.pop('test-others-job', None)
        acc_calls = [c for c in mock_db['execute'].call_args_list
                     if 'INSERT INTO accession_log' in c[0][0]]
        assert acc_calls, 'expected an accession INSERT'
        assert 'others' in acc_calls[0][0][1]


class TestShelfLocation:
    """Per-copy shelf locators on accession rows."""

    def test_create_accession_stores_shelf(self, mock_db):
        """Validates create accession stores shelf [TestShelfLocation / cataloging].
    If fails: likely model SQL changed (INSERT INTO).
    Failure indicates catalog data or listing/sort is wrong."""
        from app.cataloging.models import create_accession
        mock_db['execute'].return_value = 1
        create_accession('250001', 1, 3, 'purchase', '2F-A3')
        query, params = mock_db['execute'].call_args[0]
        assert 'shelf_location' in query
        assert params == ('250001', 1, 3, 'purchase', '2F-A3')

    def test_update_accession_stores_shelf(self, mock_db):
        """Validates update accession stores shelf [TestShelfLocation / cataloging].
    If fails: likely model SQL changed (UPDATE).
    Failure indicates catalog data or listing/sort is wrong."""
        from app.cataloging.models import update_accession
        mock_db['execute'].return_value = 1
        update_accession(21, '250099', 'donation', '2F-A3', updated_by='3')
        query, params = mock_db['execute'].call_args[0]
        assert 'shelf_location' in query
        assert params == ('250099', 'donation', '2F-A3', '3', 21)

    def test_for_books_selects_shelf(self, mock_db):
        """Validates for books selects shelf [TestShelfLocation / cataloging].
    If fails: likely model SQL changed (SELECT).
    Failure indicates catalog data or listing/sort is wrong."""
        from app.cataloging.models import get_accessions_for_books
        mock_db['fetch_all'].return_value = []
        get_accessions_for_books([1])
        query = mock_db['fetch_all'].call_args[0][0]
        assert 'shelf_location' in query

    def test_add_accession_passes_shelf(self, librarian_client, mock_db):
        """Validates add accession passes shelf `/librarian/cataloging/1/accession/add` as librarian (expects 302) [TestShelfLocation / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].side_effect = [SAMPLE_BOOKS[0], None]
        resp = librarian_client.post('/librarian/cataloging/1/accession/add', data={
            'accession_number': '250099',
            'shelf_location': '2F-A3',
        })
        assert resp.status_code == 302
        assert 'mstatus=success' in resp.location
        acc_calls = [c for c in mock_db['execute'].call_args_list
                     if 'INSERT INTO accession_log' in c[0][0]]
        assert acc_calls[0][0][1] == ('250099', 1, '3', None, '2F-A3')

    def test_add_accession_shelf_too_long(self, librarian_client, mock_db):
        """Validates add accession shelf too long `/librarian/cataloging/1/accession/add` as librarian (expects 302) [TestShelfLocation / cataloging].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = SAMPLE_BOOKS[0]
        resp = librarian_client.post('/librarian/cataloging/1/accession/add', data={
            'accession_number': '250099',
            'shelf_location': 'S' * 51,
        })
        assert resp.status_code == 302
        assert 'mstatus=error' in resp.location
        assert all('INSERT INTO accession_log' not in c[0][0]
                   for c in mock_db['execute'].call_args_list)

    def test_bulk_import_maps_shelf_header(self, librarian_client, mock_db):
        """Validates bulk import maps shelf header `/librarian/cataloging/bulk-import` as librarian (expects 200) [TestShelfLocation / cataloging].
    If fails: likely header mapping changed or column dropped.
    Failure indicates catalog data or listing/sort is wrong."""
        from app.cataloging.routes import _map_headers
        assert _map_headers(['shelf location']) == {'shelf location': 'shelf_location'}
        assert _map_headers(['shelf']) == {'shelf': 'shelf_location'}

    def test_staff_page_shows_shelf(self, librarian_client, mock_db):
        """Validates staff page shows shelf `/librarian/cataloging` as librarian (expects 200) [TestShelfLocation / cataloging].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates catalog data or listing/sort is wrong."""
        book = SAMPLE_BOOKS[0] + ('ACC-001',)
        mock_db['fetch_one'].return_value = (1,)
        mock_db['fetch_all'].side_effect = [
            [book],                                                    # books page
            [(1, 'ACC-001', 1, 'purchase', '2024-01-15', '2F-A3')],     # accessions
            [],                                                        # conditions
            [],                                                        # categories
        ]
        body = librarian_client.get('/librarian/cataloging').data.decode()
        assert 'Shelf' in body
        assert '2F-A3' in body
        assert 'name="shelf_location"' in body
        assert 'edit_acc_shelf' in body


class TestCategories:
    """Controlled category vocabulary with case-insensitive convergence."""

    def test_resolve_existing_case_insensitive(self, mock_db):
        """Validates resolve existing case insensitive [TestCategories / cataloging].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates catalog data or listing/sort is wrong."""
        from app.cataloging.models import resolve_category
        mock_db['fetch_one'].return_value = (3, 'Computer Science')
        assert resolve_category('computer science') == (3, 'Computer Science')
        query, params = mock_db['fetch_one'].call_args[0]
        assert 'LOWER(name) = LOWER(%s)' in query
        assert mock_db['execute'].call_count == 0

    def test_resolve_creates_missing(self, mock_db):
        """Validates resolve creates missing [TestCategories / cataloging].
    If fails: likely model SQL changed (INSERT INTO).
    Failure indicates catalog data or listing/sort is wrong."""
        from app.cataloging.models import resolve_category
        mock_db['fetch_one'].return_value = None
        mock_db['execute'].return_value = [(4, 'New Subject')]
        assert resolve_category('New Subject') == (4, 'New Subject')
        query = mock_db['execute'].call_args[0][0]
        assert 'INSERT INTO categories' in query

    def test_resolve_blank(self, mock_db):
        """Validates resolve blank [TestCategories / cataloging].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates catalog data or listing/sort is wrong."""
        from app.cataloging.models import resolve_category
        assert resolve_category('   ') == (None, None)
        assert mock_db['fetch_one'].call_count == 0
        assert mock_db['execute'].call_count == 0

    def test_create_book_links_category(self, mock_db):
        """Validates create book links category [TestCategories / cataloging].
    If fails: likely model SQL changed (INSERT INTO).
    Failure indicates catalog data or listing/sort is wrong."""
        from app.cataloging.models import create_book
        mock_db['fetch_one'].return_value = (3, 'Computer Science')
        mock_db['execute'].return_value = [(9,)]
        book_id = create_book('T', 'A', None, None, None, 'computer science',
                              None, None, 'Book', None)
        assert book_id == 9
        query, params = mock_db['execute'].call_args[0]
        assert 'category_id' in query
        assert params[-2:] == ('active', 3)

    def test_add_book_canonicalizes_subject(self, librarian_client, mock_db):
        """Validates add book canonicalizes subject `/librarian/cataloging/add` as librarian (expects 302) [TestCategories / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['execute'].return_value = [(1,)]
        # accession lookup miss, book dedup miss, category hit (canonical).
        mock_db['fetch_one'].side_effect = [None, None, (3, 'Computer Science')]
        resp = librarian_client.post('/librarian/cataloging/add', data={
            'title': 'New Book',
            'author': 'New Author',
            'material_type': 'Book',
            'accession_number': '250001',
            'edition': '3rd',
            'publisher': 'Test Press',
            'year_published': '2024',
            'isbn': '978-1234567890',
            'subject_classification': 'computer science',
            'call_number': 'QA76.6',
        })
        assert resp.status_code == 302
        book_calls = [c for c in mock_db['execute'].call_args_list
                      if 'INSERT INTO book_catalog' in c[0][0]]
        assert book_calls, 'expected a book INSERT'
        params = book_calls[0][0][1]
        assert 'Computer Science' in params
        assert 'computer science' not in params

    def test_cataloging_page_offers_datalist(self, librarian_client, mock_db):
        """Validates cataloging page offers datalist `/librarian/cataloging` as librarian (expects 200) [TestCategories / cataloging].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = (1,)
        mock_db['fetch_all'].side_effect = [
            [SAMPLE_BOOKS[0] + ('ACC-001',)],  # books page
            [],                                # accessions (empty: no conditions query)
            [(1, 'Computer Science')],         # categories
        ]
        body = librarian_client.get('/librarian/cataloging').data.decode()
        assert 'categoryListAdd' in body
        assert 'categoryListEdit' in body
        assert '<option value="Computer Science">' in body


class TestMaterialTypes:
    """Per-type required fields on add/edit (dynamic modal mirrors this)."""

    MINIMAL = {
        'Book': {'title': 'B', 'author': 'A', 'edition': '1st',
                 'publisher': 'P', 'year_published': '2020',
                 'isbn': '978-1234567890',
                 'subject_classification': 'Fiction', 'call_number': 'QA1'},
        'E-Book': {'title': 'E', 'author': 'A', 'year_published': '2021',
                   'subject_classification': 'Tech'},
        'Reference': {'title': 'R', 'author': 'A', 'edition': '2nd',
                      'publisher': 'P', 'year_published': '2019',
                      'subject_classification': 'Science',
                      'call_number': 'Q5'},
        'Periodical': {'title': 'J', 'publisher': 'P', 'year_published': '2024',
                       'isbn': '1234-567X',
                       'subject_classification': 'News'},
        'Thesis': {'title': 'T', 'author': 'A', 'year_published': '2023',
                   'subject_classification': 'Research'},
        'Multimedia': {'title': 'M', 'year_published': '2022',
                       'subject_classification': 'Media'},
    }

    def _post_minimal(self, client, mtype, **overrides):
        data = dict(self.MINIMAL[mtype])
        data['material_type'] = mtype
        data['accession_number'] = '250001'
        data.update(overrides)
        return client.post('/librarian/cataloging/add', data=data)

    def test_each_type_accepts_minimal(self, librarian_client, mock_db):
        """Validates each type accepts minimal `/librarian/cataloging/add` as librarian (expects 302) [TestMaterialTypes / cataloging].
    If fails: likely validation matrix changed or mock return drift.
    Failure indicates catalog data or listing/sort is wrong."""
        for mtype in ('Book', 'E-Book', 'Reference', 'Periodical', 'Thesis', 'Multimedia'):
            mock_db['execute'].return_value = [(1,)]
            mock_db['fetch_one'].return_value = None
            resp = self._post_minimal(librarian_client, mtype)
            assert resp.status_code == 302, mtype
            assert 'mstatus=success' in resp.location, mtype

    def test_missing_required_per_type_rejected(self, librarian_client, mock_db):
        """Validates missing required per type rejected `/librarian/cataloging/add` as librarian (expects 302) [TestMaterialTypes / cataloging].
    If fails: likely validation matrix changed or mock return drift.
    Failure indicates catalog data or listing/sort is wrong."""
        cases = [('Thesis', 'author'), ('Periodical', 'publisher'),
                 ('Multimedia', 'title'), ('Reference', 'call_number'),
                 ('E-Book', 'author'), ('Book', 'isbn')]
        for mtype, drop in cases:
            mock_db['execute'].return_value = [(1,)]
            mock_db['fetch_one'].return_value = None
            data = dict(self.MINIMAL[mtype])
            data['material_type'] = mtype
            data['accession_number'] = '250001'
            del data[drop]
            resp = librarian_client.post('/librarian/cataloging/add', data=data)
            assert resp.status_code == 302, (mtype, drop)
            assert 'mstatus=error' in resp.location, (mtype, drop)
            assert all('INSERT INTO book_catalog' not in c[0][0]
                       for c in mock_db['execute'].call_args_list), (mtype, drop)
            mock_db['execute'].reset_mock()

    def test_unknown_material_type_rejected(self, librarian_client, mock_db):
        """Validates unknown material type rejected `/librarian/cataloging/add` as librarian (expects 302) [TestMaterialTypes / cataloging].
    If fails: likely validation matrix changed or mock return drift.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['execute'].return_value = [(1,)]
        mock_db['fetch_one'].return_value = None
        resp = self._post_minimal(librarian_client, 'Book', material_type='Comic')
        assert resp.status_code == 302
        assert 'mstatus=error' in resp.location
        assert mock_db['execute'].call_count == 0

    def test_material_type_stored_from_selection(self, librarian_client, mock_db):
        """Validates material type stored from selection `/librarian/cataloging/add` as librarian (expects 302) [TestMaterialTypes / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['execute'].return_value = [(1,)]
        mock_db['fetch_one'].return_value = None
        resp = self._post_minimal(librarian_client, 'Thesis')
        assert 'mstatus=success' in resp.location
        book_calls = [c for c in mock_db['execute'].call_args_list
                      if 'INSERT INTO book_catalog' in c[0][0]]
        assert book_calls and 'Thesis' in book_calls[0][0][1]

    def test_add_modal_material_first_with_all_types(self, librarian_client, mock_db):
        """Validates add modal material first with all types `/librarian/cataloging` as librarian (expects 200) [TestMaterialTypes / cataloging].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/cataloging').data.decode()
        assert 'id="add_material_type"' in body
        assert 'onchange="applyMaterialType(' in body
        assert 'MATERIAL_REQUIRED' in body
        for mtype in ('Book', 'E-Book', 'Reference', 'Periodical', 'Thesis', 'Multimedia'):
            assert f'<option value="{mtype}">{mtype}</option>' in body, mtype
        # Material select precedes the title input in the add form.
        assert body.index('id="add_material_type"') < body.index('name="title"')
        # Conditionally-required inputs carry no static required attribute.
        assert 'name="author" maxlength=' in body
        assert 'name="author" required' not in body
