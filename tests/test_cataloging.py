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

    def test_delete_book_with_dependencies_is_refused(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = SAMPLE_BOOKS[2]
        mock_db['fetch_all'].return_value = [('accession copies',)]

        resp = librarian_client.post('/librarian/cataloging/3/delete')

        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

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
        assert 'shelf_location' not in call_args[0][0]
        assert call_args[0][1] == ('250099', 'donation', '3', 21)

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
        # The isbn arm compares de-hyphenated (stored ISBNs are normalized).
        assert args == ('%ACC-123456%', '%ACC-123456%', '%ACC123456%', '%ACC-123456%', '%ACC-123456%', 20, 0)

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
        assert tuple(page_args[:3]) == ('Fiction', 'Fiction', 'E-Book')

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


class TestStaffMaterialTypeFilter:
    """The staff cataloging list can be narrowed by material type, and the
    filter composes with search/status/copy-status while paging in SQL."""

    def test_model_appends_material_type_filter(self, mock_db):
        """Validates material type filter appended to listing SQL [TestStaffMaterialTypeFilter / cataloging].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates catalog data or listing/sort is wrong."""
        from app.cataloging.models import get_all_books_paginated
        mock_db['fetch_one'].return_value = (2,)
        mock_db['fetch_all'].return_value = []
        get_all_books_paginated(1, 20, None, 'Book')
        page_q, page_args = mock_db['fetch_all'].call_args[0]
        assert 'material_type = %s' in page_q
        assert 'Book' in page_args
        count_q, count_args = mock_db['fetch_one'].call_args[0]
        assert 'material_type = %s' in count_q
        assert 'Book' in count_args

    def test_model_no_material_type_by_default(self, mock_db):
        """Validates listing SQL omits material type when unset [TestStaffMaterialTypeFilter / cataloging].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates catalog data or listing/sort is wrong."""
        from app.cataloging.models import get_all_books_paginated
        mock_db['fetch_one'].return_value = (2,)
        mock_db['fetch_all'].return_value = []
        get_all_books_paginated(1, 20)
        assert 'material_type = %s' not in mock_db['fetch_all'].call_args[0][0]

    def test_status_model_appends_material_type(self, mock_db):
        """Validates material type filter composes with status tab [TestStaffMaterialTypeFilter / cataloging].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates catalog data or listing/sort is wrong."""
        from app.cataloging.models import get_books_by_status_paginated
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        get_books_by_status_paginated('archived', 1, 20, None, 'Thesis')
        page_q, page_args = mock_db['fetch_all'].call_args[0]
        assert 'material_type = %s' in page_q
        assert 'Thesis' in page_args

    def test_copy_status_model_appends_material_type(self, mock_db):
        """Validates material type filter composes with copy-status tab [TestStaffMaterialTypeFilter / cataloging].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates catalog data or listing/sort is wrong."""
        from app.cataloging.models import get_books_by_copy_status_paginated
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        get_books_by_copy_status_paginated('lost', 1, 20, None, 'Reference')
        page_q, page_args = mock_db['fetch_all'].call_args[0]
        assert 'material_type = %s' in page_q
        assert 'Reference' in page_args

    def test_search_model_parenthesizes_and_binds_material_type(self, mock_db):
        """Validates search AND-chain is parenthesized before material type [TestStaffMaterialTypeFilter / cataloging].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates catalog data or listing/sort is wrong."""
        from app.cataloging.models import search_books_paginated
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        search_books_paginated('harry', '', 1, 20, None, 'E-Book')
        page_q, page_args = mock_db['fetch_all'].call_args[0]
        assert '(title ILIKE %s' in page_q
        assert 'material_type = %s' in page_q
        assert page_args[-3] == 'E-Book'

    def test_route_passes_material_type(self, librarian_client, mock_db):
        """Validates route forwards material_type `/librarian/cataloging?material_type=Book` as librarian (expects 200) [TestStaffMaterialTypeFilter / cataloging].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = (1,)
        mock_db['fetch_all'].return_value = SAMPLE_BOOKS
        resp = librarian_client.get('/librarian/cataloging?material_type=Book')
        assert resp.status_code == 200
        page_q, page_args = mock_db['fetch_all'].call_args_list[0][0]
        assert 'material_type = %s' in page_q
        assert 'Book' in page_args

    def test_route_ignores_unknown_material_type(self, librarian_client, mock_db):
        """Validates unknown material_type is dropped `/librarian/cataloging?material_type=Banana` as librarian (expects 200) [TestStaffMaterialTypeFilter / cataloging].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = (1,)
        mock_db['fetch_all'].return_value = SAMPLE_BOOKS
        resp = librarian_client.get('/librarian/cataloging?material_type=Banana')
        assert resp.status_code == 200
        assert 'material_type = %s' not in mock_db['fetch_all'].call_args_list[0][0][0]

    def test_template_offers_material_type_filter(self, librarian_client, mock_db):
        """Validates filter control and persistence render [TestStaffMaterialTypeFilter / cataloging].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = (1,)
        mock_db['fetch_all'].return_value = SAMPLE_BOOKS
        body = librarian_client.get(
            '/librarian/cataloging?material_type=Book').data.decode()
        assert 'name="material_type"' in body
        assert 'Filter by material type' in body
        assert 'All Types' in body
        assert 'material_type=Book' in body


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
        assert b'Available in Library' in resp.data
        assert b'Borrow' in resp.data

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
        assert b'Not Available' in resp.data
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

    def test_resolve_missing_table_keeps_spelling(self, mock_db):
        """Validates resolve missing table keeps spelling [TestCategories / cataloging].
    If fails: likely fallback removed or error misclassified.
    Failure indicates catalog data or listing/sort is wrong."""
        from app.cataloging.models import resolve_category
        missing = Exception('relation "categories" does not exist')
        missing.pgcode = '42P01'
        mock_db['fetch_one'].side_effect = missing
        assert resolve_category('Physics') == (None, 'Physics')

    def test_resolve_reraises_other_errors(self, mock_db):
        """Validates resolve reraises other errors [TestCategories / cataloging].
    If fails: likely fallback over-broadened (masks real bugs).
    Failure indicates catalog data or listing/sort is wrong."""
        import pytest
        from app.cataloging.models import resolve_category
        mock_db['fetch_one'].side_effect = RuntimeError('boom')
        with pytest.raises(RuntimeError):
            resolve_category('Physics')

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
        assert 'ebook_url' in query
        assert 'ebook_allow_download' in query
        assert params[-3:] == (3, None, True)

    def test_create_book_degrades_when_ebook_url_missing(self, mock_db):
        """Validates create_book drops a missing optional column instead of 500ing [TestSchemaGate / cataloging].
    If fails: likely write-path schema fallback removed (unmigrated DB 500s).
    Failure indicates cataloging writes break on a lagging database."""
        from app.cataloging.models import create_book
        missing = Exception(
            'column "ebook_url" of relation "book_catalog" does not exist')
        missing.pgcode = '42703'
        mock_db['execute'].side_effect = [missing, [(9,)]]
        book_id = create_book('T', 'A', None, None, None, 'Physics',
                              None, None, 'Book', None,
                              category_id=3, ebook_url='http://example.com/e')
        assert book_id == 9
        first_sql, _ = mock_db['execute'].call_args_list[0][0]
        retry_sql, retry_params = mock_db['execute'].call_args_list[1][0]
        assert 'ebook_url' in first_sql
        assert 'ebook_url' not in retry_sql
        assert 'category_id' in retry_sql
        assert 'ebook_allow_download' in retry_sql
        assert retry_params[-3:] == ('active', 3, True)

    def test_update_book_skips_toggle_when_none(self, mock_db):
        """Validates update_book leaves ebook_allow_download untouched when None [TestSchemaGate / cataloging].
    If fails: likely update_book gained an unconditional toggle assignment.
    Failure indicates callers without the flag would wipe librarian toggles."""
        from app.cataloging.models import update_book
        mock_db['execute'].return_value = 1
        result = update_book(7, 'T', 'A', None, None, None, 'Physics',
                             None, None, 'Book', None,
                             category_id=3, ebook_url='http://example.com/e')
        assert result == 1
        query, _ = mock_db['execute'].call_args[0]
        assert 'ebook_allow_download' not in query

    def test_update_book_degrades_when_category_id_missing(self, mock_db):
        """Validates update_book drops a missing optional column instead of 500ing [TestSchemaGate / cataloging].
    If fails: likely write-path schema fallback removed (unmigrated DB 500s).
    Failure indicates cataloging writes break on a lagging database."""
        from app.cataloging.models import update_book
        missing = Exception(
            'column "category_id" of relation "book_catalog" does not exist')
        missing.pgcode = '42703'
        mock_db['execute'].side_effect = [missing, 1]
        result = update_book(7, 'T', 'A', None, None, None, 'Physics',
                             None, None, 'Book', None,
                             category_id=3, ebook_url='http://example.com/e')
        assert result == 1
        retry_sql, retry_params = mock_db['execute'].call_args_list[1][0]
        assert 'category_id' not in retry_sql
        assert 'ebook_url' in retry_sql
        assert 7 in retry_params

    def test_book_write_reraises_non_schema_errors(self, mock_db):
        """Validates book writes re-raise non-schema DB errors [TestSchemaGate / cataloging].
    If fails: likely fallback over-broadened (masks real bugs).
    Failure indicates cataloging writes hide genuine failures."""
        import pytest
        from app.cataloging.models import create_book
        mock_db['execute'].side_effect = RuntimeError('boom')
        with pytest.raises(RuntimeError):
            create_book('T', 'A', None, None, None, 'Physics',
                        None, None, 'Book', None, category_id=3)

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

    def test_cataloging_page_offers_category_dropdowns(self, librarian_client, mock_db):
        """Validates cataloging page offers category dropdowns `/librarian/cataloging` as librarian (expects 200) [TestCategories / cataloging].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = (1,)
        mock_db['fetch_all'].side_effect = [
            [SAMPLE_BOOKS[0] + ('ACC-001',)],  # books page
            [],                                # accessions (empty: no conditions query)
            [(1, 'Computer Science')],         # categories
            [],                                # secondaries batch
        ]
        body = librarian_client.get('/librarian/cataloging').data.decode()
        assert 'name="subject_classification"' in body
        # One custom dropdown per book modal (JS references the hook once more).
        assert body.count('<div class="relative flex-1 min-w-0" data-cat-dropdown=') == 2
        assert body.count('data-cat-manage="') == 2
        assert 'id="categoryManagerModal"' in body
        assert 'id="catManagerSearch"' in body
        assert 'id="catManagerNew"' in body
        assert 'BOOK_CATS' in body
        assert 'syncCatDropdown' in body

    def test_add_modal_rechecks_stashed_extras(self, librarian_client, mock_db):
        """Validates add modal rechecks stashed extras `/librarian/cataloging` as librarian (expects 200) [TestCategories / cataloging].
    If fails: likely template value bindings changed.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        librarian_client.post('/librarian/cataloging/add', data={
            'title': 'Typed Title', 'material_type': 'Thesis',
            'year_published': '2024', 'subject_classification': 'Fiction',
            'extra_categories': ['2'],
        })
        mock_db['fetch_all'].side_effect = [
            [],                                          # books
            [(1, 'Fiction'), (2, 'Arts')],               # categories
        ]
        body = librarian_client.get('/librarian/cataloging?modal=addBookModal').data.decode()
        assert 'name="subject_classification" value="Fiction"' in body
        # Both the primary match and the stashed extra come back checked.
        assert 'value="1" data-cat-name="Fiction" class="accent-blue-900 rounded shrink-0" checked' in body
        assert 'value="2" data-cat-name="Arts" class="accent-blue-900 rounded shrink-0" checked' in body


class TestMultiCategory:
    """Several categories on one title (primary + extras)."""

    def test_set_replaces_links_skipping_junk(self, mock_db):
        """Validates set replaces links skipping junk [TestMultiCategory / cataloging].
    If fails: likely model SQL changed (INSERT INTO).
    Failure indicates catalog data or listing/sort is wrong."""
        from app.cataloging.models import set_book_categories
        mock_db['execute'].return_value = 1
        set_book_categories(7, ['2', 'nope', 2, None, 3])
        stmts = [c[0][0] for c in mock_db['execute'].call_args_list]
        assert stmts[0].startswith('DELETE FROM book_categories')
        assert 'INSERT INTO book_categories' in stmts[1]
        assert 'WHERE category_id = ANY(%s)' in stmts[1]
        assert 'IS DISTINCT FROM' in stmts[1]
        assert mock_db['execute'].call_args_list[1][0][1] == (7, [2, 3], 7)

    def test_set_empty_clears_links(self, mock_db):
        """Validates set empty clears links [TestMultiCategory / cataloging].
    If fails: likely model SQL changed (DELETE FROM).
    Failure indicates catalog data or listing/sort is wrong."""
        from app.cataloging.models import set_book_categories
        mock_db['execute'].return_value = 1
        set_book_categories(7, [])
        assert mock_db['execute'].call_count == 1
        assert mock_db['execute'].call_args[0][0].startswith('DELETE FROM book_categories')

    def test_get_book_categories_shape(self, mock_db):
        """Validates get book categories shape [TestMultiCategory / cataloging].
    If fails: likely model SQL changed (SELECT).
    Failure indicates catalog data or listing/sort is wrong."""
        from app.cataloging.models import get_book_categories, get_categories_for_books
        mock_db['fetch_all'].return_value = [(2, 'Arts')]
        assert get_book_categories(7) == [(2, 'Arts')]
        assert get_book_categories('bogus') == []
        mock_db['fetch_all'].return_value = [(7, 2, 'Arts')]
        assert get_categories_for_books([7]) == {7: [(2, 'Arts')]}
        assert get_categories_for_books([]) == {}

    def test_add_book_saves_extras(self, librarian_client, mock_db):
        """Validates add book saves extras `/librarian/cataloging/add` as librarian (expects 302) [TestMultiCategory / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['execute'].return_value = [(1,)]
        mock_db['fetch_one'].return_value = None
        resp = librarian_client.post('/librarian/cataloging/add', data={
            'title': 'New Book', 'author': 'New Author', 'material_type': 'Book',
            'accession_number': '250001', 'edition': '3rd', 'publisher': 'P',
            'year_published': '2024', 'isbn': '978-1234567890',
            'subject_classification': 'Fiction', 'call_number': 'QA1',
            'extra_categories': ['2', '3'],
        })
        assert resp.status_code == 302
        assert 'mstatus=success' in resp.location
        link_calls = [c for c in mock_db['execute'].call_args_list
                      if 'INSERT INTO book_categories' in c[0][0]]
        assert link_calls, 'expected secondary-category links'

    def test_edit_book_replaces_extras(self, librarian_client, mock_db):
        """Validates edit book replaces extras `/librarian/cataloging/1/edit` as librarian (expects 302) [TestMultiCategory / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].side_effect = [SAMPLE_BOOKS[0], (2, 'Fiction')]
        mock_db['execute'].return_value = 1
        resp = librarian_client.post('/librarian/cataloging/1/edit', data={
            'title': 'T', 'author': 'A', 'edition': '1st', 'publisher': 'P',
            'year_published': '2020', 'isbn': '978-1234567890',
            'subject_classification': 'Fiction', 'call_number': 'C1',
            'extra_categories': ['5'],
        })
        assert resp.status_code == 302
        assert 'mstatus=success' in resp.location
        stmts = [c[0][0] for c in mock_db['execute'].call_args_list]
        assert any('DELETE FROM book_categories' in s for s in stmts)
        assert any('INSERT INTO book_categories' in s for s in stmts)

    def test_public_filter_matches_secondary(self, client, mock_db):
        """Validates public filter matches secondary `/catalog?category=Fiction` (expects 200) [TestMultiCategory / cataloging].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].side_effect = [[], [], []]
        resp = client.get('/catalog?category=Fiction')
        assert resp.status_code == 200
        query, params = mock_db['fetch_all'].call_args_list[0][0]
        assert 'book_categories' in query
        assert params[:2] == ('Fiction', 'Fiction')

    def test_bookinfo_shows_extras(self, client, mock_db):
        """Validates bookinfo shows extras `/book/1` (expects 200) [TestMultiCategory / cataloging].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = SAMPLE_BOOKS[0]
        mock_db['fetch_all'].side_effect = [
            [],                    # accessions
            [],                    # active loans
            [],                    # borrower map
            [(2, 'Arts')],         # extra categories
        ]
        body = client.get('/book/1').data.decode()
        assert resp_ok_extra(body)

    def test_export_has_other_categories(self, librarian_client, mock_db):
        """Validates export has other categories `/librarian/cataloging/export?format=csv` as librarian (expects 200) [TestMultiCategory / cataloging].
    If fails: likely export headers/columns changed.
    Failure indicates catalog data or listing/sort is wrong."""
        row16 = (1, 'T', 'A', '1st', 'P', 2020, 'Fiction', 'C1',
                 '978-0', 'Book', 'D', 'active', '2024-01-01', None, None)
        mock_db['fetch_all'].return_value = [row16 + ('Arts, Media', 'ACC-001')]
        resp = librarian_client.get('/librarian/cataloging/export?format=csv')
        assert resp.status_code == 200
        text = resp.data.decode()
        assert 'Other Categories' in text.splitlines()[0]
        assert 'Arts, Media' in text

    def test_bulk_import_splits_secondaries(self, app, mock_db):
        """Validates bulk import splits secondaries [TestMultiCategory / cataloging].
    If fails: likely bulk worker changed or mock return drift.
    Failure indicates catalog data or listing/sort is wrong."""
        from app.cataloging.routes import _bulk_import_worker, _import_jobs
        # book dedup miss, accession miss, Fiction lookup miss, Arts lookup miss.
        mock_db['fetch_one'].side_effect = [None, None, None, None]
        # Fiction category insert -> 10, book insert -> 1, Arts insert -> 20,
        # then the secondary-links DELETE + INSERT.
        mock_db['execute'].side_effect = [[(10,)], [(1,)], [(20,)], 1, 1]
        _import_jobs['test-multi-cat'] = {
            'status': 'processing', 'total': 1, 'done': 0,
            'errors': [], 'message': None,
        }
        try:
            _bulk_import_worker(
                app, 'test-multi-cat',
                [{'title': 'Multi Cat', 'author': 'A', 'accession_number': 'ACC-777',
                  'subject_classification': 'Fiction; Arts'}],
                {'title': 'title', 'author': 'author',
                 'accession_number': 'accession_number',
                 'subject_classification': 'subject_classification'},
                3,
            )
        finally:
            _import_jobs.pop('test-multi-cat', None)
        link_calls = [c for c in mock_db['execute'].call_args_list
                      if 'INSERT INTO book_categories' in c[0][0]]
        assert link_calls, 'expected secondary-category links from ;-split'


def resp_ok_extra(body):
    """Extra-category rendering assertion for the book detail page."""
    assert 'Categories' in body
    assert 'Arts' in body
    return True


class TestMaterialTypes:
    """Per-type required fields on add/edit (dynamic modal mirrors this)."""

    MINIMAL = {
        'Book': {'title': 'B', 'author': 'A', 'edition': '1st',
                 'publisher': 'P', 'year_published': '2020',
                 'isbn': '978-1234567890',
                 'subject_classification': 'Fiction', 'call_number': 'QA1'},
        'E-Book': {'title': 'E', 'author': 'A', 'year_published': '2021',
                   'subject_classification': 'Tech',
                   'ebook_url': 'https://drive.google.com/file/d/ABC123/view'},
        'Reference': {'title': 'R', 'author': 'A', 'edition': '2nd',
                      'publisher': 'P', 'year_published': '2019',
                      'subject_classification': 'Science',
                      'call_number': 'Q5'},
        'Periodical': {'title': 'J', 'publisher': 'P', 'year_published': '2024',
                       'isbn': '1234-567X',
                       'subject_classification': 'News'},
        'Thesis': {'title': 'T', 'author': 'A', 'year_published': '2023',
                   'subject_classification': 'Research'},
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
        for mtype in ('Book', 'E-Book', 'Reference', 'Periodical', 'Thesis'):
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
                 ('Reference', 'call_number'),
                 ('E-Book', 'author'), ('E-Book', 'ebook_url'), ('Book', 'isbn')]
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
        # Retired type behaves the same way.
        resp = self._post_minimal(librarian_client, 'Book', material_type='Multimedia')
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

    def test_isbn_checksums_accepted(self, mock_db):
        """Validates isbn checksums accepted [TestMaterialTypes / cataloging].
    If fails: likely ISBN validation changed.
    Failure indicates catalog data or listing/sort is wrong."""
        from app.cataloging.routes import _validate_isbn_issn
        assert _validate_isbn_issn('9780306406157', 'Book') is None
        assert _validate_isbn_issn('978-0-306-40615-7', 'Reference') is None
        assert _validate_isbn_issn('0306406152', 'Book') is None
        assert _validate_isbn_issn('080442957X', 'E-Book') is None
        assert _validate_isbn_issn('1234-567X', 'Periodical') is None
        assert _validate_isbn_issn('', 'Thesis') is None
        assert _validate_isbn_issn('', 'E-Book') is None
        assert _validate_isbn_issn('9780306406158', 'Book') == 'Invalid ISBN-13 check digit.'
        assert _validate_isbn_issn('0306406153', 'Book') == 'Invalid ISBN-10 check digit.'
        assert _validate_isbn_issn('123', 'Book') == 'ISBN must be 10 or 13 digits.'
        assert _validate_isbn_issn('', 'Book') == 'ISBN is required for this material type.'
        assert _validate_isbn_issn('123', 'Periodical') == 'ISSN must be 8 characters (e.g. 1234-567X).'

    def test_isbn_helpers(self, mock_db):
        """Validates isbn helpers [TestMaterialTypes / cataloging].
    If fails: likely ISBN helpers changed.
    Failure indicates catalog data or listing/sort is wrong."""
        from app.cataloging.models import normalize_isbn, is_valid_isbn10, is_valid_isbn13
        assert normalize_isbn('978-0-306-40615-7') == '9780306406157'
        assert normalize_isbn('080442957x') == '080442957X'
        assert normalize_isbn(None) == ''
        assert is_valid_isbn10('0306406152') is True
        assert is_valid_isbn10('080442957X') is True
        assert is_valid_isbn10('0306406153') is False
        assert is_valid_isbn13('9780306406157') is True
        assert is_valid_isbn13('9780306406158') is False

    def test_isbn_normalized_on_save(self, librarian_client, mock_db):
        """Validates isbn normalized on save `/librarian/cataloging/add` as librarian (expects 302) [TestMaterialTypes / cataloging].
    If fails: likely ISBN normalization changed.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['execute'].return_value = [(1,)]
        mock_db['fetch_one'].return_value = None
        resp = self._post_minimal(librarian_client, 'Book', isbn='978-0-306-40615-7')
        assert 'mstatus=success' in resp.location
        book_calls = [c for c in mock_db['execute'].call_args_list
                      if 'INSERT INTO book_catalog' in c[0][0]]
        assert book_calls and '9780306406157' in book_calls[0][0][1]
        assert all('978-0-306-40615-7' not in str(c[0][1]) for c in book_calls)

    def test_dedup_normalizes_isbn(self, mock_db):
        """Validates dedup normalizes isbn [TestMaterialTypes / cataloging].
    If fails: likely dedup lookup changed.
    Failure indicates catalog data or listing/sort is wrong."""
        from app.cataloging.models import get_book_by_title_author_isbn
        mock_db['fetch_one'].return_value = (5,)
        assert get_book_by_title_author_isbn('T', 'A', '978-0-306-40615-7') == (5,)
        assert mock_db['fetch_one'].call_args[0][1] == ('T', 'A', '9780306406157')

    def test_isbn_search_normalizes_pattern(self, mock_db):
        """Validates isbn search normalizes pattern [TestMaterialTypes / cataloging].
    If fails: likely search pattern changed.
    Failure indicates catalog data or listing/sort is wrong."""
        from app.cataloging.models import search_books
        mock_db['fetch_all'].return_value = []
        search_books('978-0-306', field='isbn')
        assert mock_db['fetch_all'].call_args[0][1] == ('%9780306%',)


class TestFormPersistence:
    """Typed Add/Edit values survive validation-error redirects."""

    def test_add_error_stashes_typed_values(self, librarian_client, mock_db):
        """Validates add error stashes typed values `/librarian/cataloging/add` as librarian (expects 302) [TestFormPersistence / cataloging].
    If fails: likely stash helper changed or session unavailable.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = None
        resp = librarian_client.post('/librarian/cataloging/add', data={
            'title': 'Typed Title', 'material_type': 'Thesis',
            'year_published': '2024', 'subject_classification': 'Research',
            'description': 'Typed blurb',
        })
        assert resp.status_code == 302
        assert 'mstatus=error' in resp.location
        with librarian_client.session_transaction() as sess:
            stashed = sess.get('book_form_data')
        assert stashed and stashed['_modal'] == 'addBookModal'
        assert stashed['title'] == 'Typed Title'
        assert stashed['material_type'] == 'Thesis'

    def test_add_modal_repopulates_after_error(self, librarian_client, mock_db):
        """Validates add modal repopulates after error `/librarian/cataloging` as librarian (expects 200) [TestFormPersistence / cataloging].
    If fails: likely template value bindings changed.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        librarian_client.post('/librarian/cataloging/add', data={
            'title': 'Typed Title', 'material_type': 'Thesis',
            'year_published': '2024', 'subject_classification': 'Research',
            'description': 'Typed blurb', 'source': 'donation',
        })
        body = librarian_client.get('/librarian/cataloging?modal=addBookModal').data.decode()
        assert 'value="Typed Title"' in body
        assert 'name="material_type" id="add_material_type" value="Thesis"' in body
        assert 'name="source" value="donation"' in body
        assert 'Typed blurb' in body
        assert 'value="2024"' in body

    def test_stash_consumed_once(self, librarian_client, mock_db):
        """Validates stash consumed once `/librarian/cataloging` as librarian (expects 200) [TestFormPersistence / cataloging].
    If fails: likely pop logic changed (stale values leak across visits).
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = None
        mock_db['fetch_all'].return_value = []
        librarian_client.post('/librarian/cataloging/add', data={'title': 'Once Title'})
        first = librarian_client.get('/librarian/cataloging?modal=addBookModal').data.decode()
        assert 'value="Once Title"' in first
        second = librarian_client.get('/librarian/cataloging?modal=addBookModal').data.decode()
        assert 'value="Once Title"' not in second

    def test_edit_error_stashes_with_book_id(self, librarian_client, mock_db):
        """Validates edit error stashes with book id `/librarian/cataloging/1/edit` as librarian (expects 302) [TestFormPersistence / cataloging].
    If fails: likely stash helper changed or session unavailable.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = SAMPLE_BOOKS[0]
        resp = librarian_client.post('/librarian/cataloging/1/edit', data={
            'title': 'Typed ETitle', 'material_type': 'Book',
        })
        assert resp.status_code == 302
        assert 'mstatus=error' in resp.location
        with librarian_client.session_transaction() as sess:
            stashed = sess.get('book_form_data')
        assert stashed and stashed['_modal'] == 'editBookModal'
        assert stashed['_book_id'] == '1'
        assert stashed['title'] == 'Typed ETitle'

    def test_edit_modal_repopulates_stashed(self, librarian_client, mock_db):
        """Validates edit modal repopulates stashed `/librarian/cataloging` as librarian (expects 200) [TestFormPersistence / cataloging].
    If fails: likely stashed-override JS or JSON embedding changed.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = SAMPLE_BOOKS[0]
        mock_db['fetch_all'].return_value = []
        librarian_client.post('/librarian/cataloging/1/edit', data={
            'title': 'Typed ETitle', 'material_type': 'Book',
        })
        mock_db['fetch_one'].return_value = SAMPLE_BOOKS[0]
        mock_db['fetch_all'].side_effect = [
            [SAMPLE_BOOKS[0] + ('ACC-001',)],
            [],
            [],
        ]
        body = librarian_client.get(
            '/librarian/cataloging?modal=editBookModal&book_id=1').data.decode()
        assert '"_modal": "editBookModal"' in body
        assert '"title": "Typed ETitle"' in body
        assert '"_book_id": "1"' in body

    def test_add_modal_material_first_with_all_types(self, librarian_client, mock_db):
        """Validates add modal material first with all types `/librarian/cataloging` as librarian (expects 200) [TestMaterialTypes / cataloging].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = (0,)
        mock_db['fetch_all'].return_value = []
        body = librarian_client.get('/librarian/cataloging').data.decode()
        assert 'id="add_material_type"' in body
        # Material type renders as an in-modal custom dropdown (no native
        # <select>, whose OS popup overlaps the fields below it).
        assert 'data-dd-after="applyMaterialType"' in body
        assert 'data-dd-prefix="add"' in body
        assert 'MATERIAL_REQUIRED' in body
        for mtype in ('Book', 'E-Book', 'Reference', 'Periodical', 'Thesis'):
            assert f'data-dd-value="{mtype}"' in body, mtype
        assert 'data-dd-value="Multimedia"' not in body
        # Material select precedes the title input in the add form.
        assert body.index('id="add_material_type"') < body.index('name="title"')
        # Conditionally-required inputs carry no static required attribute.
        assert 'name="author" maxlength=' in body
        assert 'name="author" required' not in body
        # Live ISBN feedback hooks in both modals (inputs + hint spots + JS selectors).
        assert body.count('data-isbn-input') == 3
        assert body.count('data-isbn-hint') == 3
        assert 'validateIsbnInput' in body
        # E-Book Link box hides unless E-Book is selected.
        assert body.count('name="ebook_url"') == 3
        assert "lcell.style.display = linkNeed ? '' : 'none'" in body
        # Live E-Book link feedback: inputs + hint spots, Google-only whitelist JS.
        assert body.count('data-ebook-input') == 3
        assert body.count('data-ebook-hint') == 4
        assert 'validateEbookInput' in body
        assert 'classifyEbookUrl' in body
        assert 'Only Google Drive or Google Docs links are accepted.' in body
        # ISBN info buttons + explainer modal (one per book modal).
        assert body.count("openModal('isbnInfoModal')") == 2
        assert 'id="isbnInfoModal"' in body
        assert 'ISBN-13 — 13 digits' in body
        assert 'ISBN-10 — 10 characters' in body
        # Accession duplicate note is slim small text like the ISBN hint.
        assert body.count('data-exists-accession-msg class="hidden mt-1 text-[11px] font-medium text-red-700 dark:text-red-400"') == 2


class TestCategoryManager:
    """In-modal vocabulary management (add/search/toggle)."""

    def test_create_category_new(self, librarian_client, mock_db):
        """Validates create category new `/librarian/cataloging/categories` as librarian (expects 200) [TestCategoryManager / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = None
        mock_db['execute'].return_value = [(9, 'Marine Biology')]
        resp = librarian_client.post('/librarian/cataloging/categories',
                                     data={'name': 'Marine Biology'})
        assert resp.status_code == 200
        assert resp.get_json() == {'id': 9, 'name': 'Marine Biology'}

    def test_create_category_duplicate_returns_existing(self, librarian_client, mock_db):
        """Validates create category duplicate returns existing `/librarian/cataloging/categories` as librarian (expects 200) [TestCategoryManager / cataloging].
    If fails: likely resolve logic changed.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = (3, 'Computer Science')
        resp = librarian_client.post('/librarian/cataloging/categories',
                                     data={'name': 'computer science'})
        assert resp.status_code == 200
        assert resp.get_json() == {'id': 3, 'name': 'Computer Science'}
        assert all('INSERT INTO categories' not in c[0][0]
                   for c in mock_db['execute'].call_args_list)

    def test_create_category_blank_rejected(self, librarian_client, mock_db):
        """Validates create category blank rejected `/librarian/cataloging/categories` as librarian (expects 400) [TestCategoryManager / cataloging].
    If fails: likely validation bypassed.
    Failure indicates catalog data or listing/sort is wrong."""
        resp = librarian_client.post('/librarian/cataloging/categories', data={'name': '   '})
        assert resp.status_code == 400
        assert 'error' in resp.get_json()
        assert mock_db['execute'].call_count == 0

    def test_create_category_too_long_rejected(self, librarian_client, mock_db):
        """Validates create category too long rejected `/librarian/cataloging/categories` as librarian (expects 400) [TestCategoryManager / cataloging].
    If fails: likely validation bypassed.
    Failure indicates catalog data or listing/sort is wrong."""
        resp = librarian_client.post('/librarian/cataloging/categories',
                                     data={'name': 'C' * 101})
        assert resp.status_code == 400
        assert mock_db['execute'].call_count == 0

    def test_create_category_student_forbidden(self, student_client, mock_db):
        """Validates create category student forbidden `/librarian/cataloging/categories` as student (expects 302) [TestCategoryManager / cataloging].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = student_client.post('/librarian/cataloging/categories', data={'name': 'X'})
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_create_category_unauthenticated(self, client, mock_db):
        """Validates create category unauthenticated `/librarian/cataloging/categories` (expects 302) [TestCategoryManager / cataloging].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = client.post('/librarian/cataloging/categories', data={'name': 'X'})
        assert resp.status_code == 302
        assert '/login' in resp.location


class TestEbookUrl:
    """E-book access links: validation, Drive detection, surfaces."""

    def test_validate_ebook_url(self, mock_db):
        """Validates validate ebook url [TestEbookUrl / cataloging].
    If fails: likely URL validation changed.
    Failure indicates catalog data or listing/sort is wrong."""
        from app.cataloging.models import validate_ebook_url
        assert validate_ebook_url('', 'E-Book') == (None, 'E-Book link is required for E-Book.')
        assert validate_ebook_url('', 'Book') == (None, None)
        assert validate_ebook_url('not a url', 'Book') == (None, 'E-Book link must be a valid http(s) URL.')
        assert validate_ebook_url('ftp://x.com/f', 'Book') == (None, 'E-Book link must be a valid http(s) URL.')
        assert validate_ebook_url('https://example.com/ebook.pdf', 'Reference') == (
            None, 'E-Book link must be a Google Drive or Google Docs link.')
        assert validate_ebook_url('https://drive.google.com/drive/folders/ABC123', 'Book') == (
            None, 'E-Book link must be a Google Drive or Google Docs link.')
        assert validate_ebook_url('https://docs.google.com', 'Book') == (
            None, 'E-Book link must be a Google Drive or Google Docs link.')
        assert validate_ebook_url('  https://drive.google.com/file/d/ABC123/view  ', 'Book') == (
            'https://drive.google.com/file/d/ABC123/view', None)
        assert validate_ebook_url('https://docs.google.com/document/d/DOC123/edit', 'E-Book') == (
            'https://docs.google.com/document/d/DOC123/edit', None)
        too_long = 'https://example.com/' + 'a' * 500
        assert validate_ebook_url(too_long, 'Book')[1] == 'E-Book link is too long (max 500 characters).'

    def test_ebook_link_info(self, mock_db):
        """Validates ebook link info [TestEbookUrl / cataloging].
    If fails: likely Drive/Docs detection changed.
    Failure indicates catalog data or listing/sort is wrong."""
        from app.cataloging.models import ebook_link_info, drive_preview_url, docs_preview_url, validate_ebook_url
        assert ebook_link_info('https://drive.google.com/file/d/ABC123/view') == ('drive', 'ABC123')
        assert ebook_link_info('https://drive.google.com/open?id=XYZ789') == ('drive', 'XYZ789')
        assert ebook_link_info('https://drive.google.com/uc?id=QWE123') == ('drive', 'QWE123')
        assert ebook_link_info('https://drive.google.com/drive/folders/ABC123') == ('external', None)
        assert ebook_link_info('https://docs.google.com/document/d/DOC123/edit') == ('docs', 'DOC123')
        assert ebook_link_info(
            'https://docs.google.com/document/d/DOC123/preview') == ('docs', 'DOC123')
        # Real-world share shape: /edit plus sharing query params.
        shared = ('https://docs.google.com/document/d/1ekPEknmkae6q2KBCACQaPeeoJhF5aE57'
                  '/edit?usp=sharing&ouid=108913924297114452491&rtpof=true&sd=true')
        assert ebook_link_info(shared) == ('docs', '1ekPEknmkae6q2KBCACQaPeeoJhF5aE57')
        assert validate_ebook_url(shared, 'E-Book') == (shared, None)
        assert ebook_link_info('https://docs.google.com') == ('external', None)
        assert ebook_link_info('https://publisher.com/book.pdf') == ('external', None)
        assert ebook_link_info('') == (None, None)
        assert drive_preview_url('ABC123') == 'https://drive.google.com/file/d/ABC123/preview'
        assert docs_preview_url('https://docs.google.com/document/d/DOC123/edit') == (
            'https://docs.google.com/document/d/DOC123/preview')
        assert docs_preview_url('https://docs.google.com/document/d/DOC123/preview') == (
            'https://docs.google.com/document/d/DOC123/preview')
        assert docs_preview_url(
            'https://docs.google.com/document/d/1ekPEknmkae6q2KBCACQaPeeoJhF5aE57'
            '/edit?usp=sharing&ouid=108913924297114452491&rtpof=true&sd=true') == (
            'https://docs.google.com/document/d/1ekPEknmkae6q2KBCACQaPeeoJhF5aE57/preview')
        assert docs_preview_url('https://drive.google.com/file/d/ABC123/view') == ''
        assert docs_preview_url('') == ''

    def test_add_publisher_link_rejected(self, librarian_client, mock_db):
        """Validates add publisher link rejected `/librarian/cataloging/add` as librarian (expects 302) [TestEbookUrl / cataloging].
    If fails: likely the Google-only whitelist changed.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = None
        resp = librarian_client.post('/librarian/cataloging/add', data={
            'title': 'E', 'author': 'A', 'year_published': '2021',
            'subject_classification': 'Tech', 'material_type': 'Reference',
            'accession_number': '250001',
            'ebook_url': 'https://publisher.com/e.pdf',
        })
        assert resp.status_code == 302
        assert 'mstatus=error' in resp.location
        assert mock_db['execute'].call_count == 0

    def test_add_docs_link_stored(self, librarian_client, mock_db):
        """Validates add docs link stored `/librarian/cataloging/add` as librarian (expects 302) [TestEbookUrl / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['execute'].return_value = [(1,)]
        mock_db['fetch_one'].return_value = None
        resp = librarian_client.post('/librarian/cataloging/add', data={
            'title': 'E', 'author': 'A', 'year_published': '2021',
            'subject_classification': 'Tech', 'material_type': 'E-Book',
            'accession_number': '250001',
            'ebook_url': 'https://docs.google.com/document/d/DOC123/edit',
        })
        assert 'mstatus=success' in resp.location
        book_calls = [c for c in mock_db['execute'].call_args_list
                      if 'INSERT INTO book_catalog' in c[0][0]]
        assert book_calls
        assert 'https://docs.google.com/document/d/DOC123/edit' in book_calls[0][0][1]

    def test_add_ebook_without_link_rejected(self, librarian_client, mock_db):
        """Validates add ebook without link rejected `/librarian/cataloging/add` as librarian (expects 302) [TestEbookUrl / cataloging].
    If fails: likely E-Book link requirement changed.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = None
        resp = librarian_client.post('/librarian/cataloging/add', data={
            'title': 'E', 'author': 'A', 'year_published': '2021',
            'subject_classification': 'Tech', 'material_type': 'E-Book',
            'accession_number': '250001',
        })
        assert resp.status_code == 302
        assert 'mstatus=error' in resp.location
        assert mock_db['execute'].call_count == 0

    def test_add_ebook_bad_link_rejected(self, librarian_client, mock_db):
        """Validates add ebook bad link rejected `/librarian/cataloging/add` as librarian (expects 302) [TestEbookUrl / cataloging].
    If fails: likely E-Book link validation changed.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = None
        resp = librarian_client.post('/librarian/cataloging/add', data={
            'title': 'E', 'author': 'A', 'year_published': '2021',
            'subject_classification': 'Tech', 'material_type': 'E-Book',
            'accession_number': '250001', 'ebook_url': 'notaurl',
        })
        assert resp.status_code == 302
        assert 'mstatus=error' in resp.location
        assert mock_db['execute'].call_count == 0

    def test_add_ebook_link_stored(self, librarian_client, mock_db):
        """Validates add ebook link stored `/librarian/cataloging/add` as librarian (expects 302) [TestEbookUrl / cataloging].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['execute'].return_value = [(1,)]
        mock_db['fetch_one'].return_value = None
        resp = librarian_client.post('/librarian/cataloging/add', data={
            'title': 'E', 'author': 'A', 'year_published': '2021',
            'subject_classification': 'Tech', 'material_type': 'E-Book',
            'accession_number': '250001',
            'ebook_url': 'https://drive.google.com/file/d/ABC123/view',
        })
        assert 'mstatus=success' in resp.location
        book_calls = [c for c in mock_db['execute'].call_args_list
                      if 'INSERT INTO book_catalog' in c[0][0]]
        assert book_calls
        assert 'ebook_url' in book_calls[0][0][0]
        assert 'https://drive.google.com/file/d/ABC123/view' in book_calls[0][0][1]

    def test_bookinfo_embeds_drive_preview(self, client, mock_db):
        """Validates bookinfo embeds drive preview `/book/1` (expects 200) [TestEbookUrl / cataloging].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        book = (1, 'E Title', 'A', None, None, 2021, 'Tech', None, None,
                'E-Book', 'D', 'active', '2024-01-01', None, None, None,
                'https://drive.google.com/file/d/ABC123/view')
        mock_db['fetch_one'].return_value = book
        mock_db['fetch_all'].return_value = []
        body = client.get('/book/1').data.decode()
        assert 'https://drive.google.com/file/d/ABC123/preview' in body
        # Preview opens inside the modal, not inline, and loads on demand:
        # no live src on page render (a live src fetched the Google preview
        # on every /book view even while the modal was hidden — slow).
        assert '<iframe' not in body.split('ebookPreviewModal')[0]
        assert 'data-src="https://drive.google.com/file/d/ABC123/preview"' in body
        assert "frame.src = frame.getAttribute('data-src')" in body
        assert 'openEbookPreview()' in body
        assert 'Embedded preview — Google Drive' in body
        assert 'Open in new tab' not in body
        assert 'Download' in body

    def test_bookinfo_embeds_docs_preview(self, client, mock_db):
        """Validates bookinfo embeds docs preview `/book/1` (expects 200) [TestEbookUrl / cataloging].
    If fails: likely Docs detection or preview normalization changed.
    Failure indicates catalog data or listing/sort is wrong."""
        book = (1, 'E Title', 'A', None, None, 2021, 'Tech', None, None,
                'E-Book', 'D', 'active', '2024-01-01', None, None, None,
                'https://docs.google.com/document/d/DOC123/edit')
        mock_db['fetch_one'].return_value = book
        mock_db['fetch_all'].return_value = []
        body = client.get('/book/1').data.decode()
        # The edit variant is normalized to the embeddable /preview form.
        assert 'data-src="https://docs.google.com/document/d/DOC123/preview"' in body
        assert 'openEbookPreview()' in body
        assert 'Embedded preview — Google Docs' in body

    def test_bookinfo_external_link_button(self, client, mock_db):
        """Validates bookinfo external link button `/book/1` (expects 200) [TestEbookUrl / cataloging].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        book = (1, 'E Title', 'A', None, None, 2021, 'Tech', None, None,
                'E-Book', 'D', 'active', '2024-01-01', None, None, None,
                'https://publisher.com/e.pdf')
        mock_db['fetch_one'].return_value = book
        mock_db['fetch_all'].return_value = []
        body = client.get('/book/1').data.decode()
        assert 'Read Online' in body
        assert 'drive.google.com/file/d' not in body

    def test_bookinfo_hides_download_when_disabled(self, client, mock_db):
        """We hide the Download button when ebook_allow_download is False `/book/1` (expects 200) [TestEbookUrl / cataloging].
    If fails: likely the toggle column/guard or template gate changed.
    Failure indicates users can download e-books a librarian disabled."""
        book = (1, 'E Title', 'A', None, None, 2021, 'Tech', None, None,
                'E-Book', 'D', 'active', '2024-01-01', None, None, None,
                'https://drive.google.com/file/d/ABC123/view', False)
        mock_db['fetch_one'].return_value = book
        mock_db['fetch_all'].return_value = []
        body = client.get('/book/1').data.decode()
        assert 'openEbookPreview()' in body
        assert '/book/1/download' not in body

    def test_bookinfo_shows_download_when_allowed(self, client, mock_db):
        """We keep the Download button when ebook_allow_download is True `/book/1` (expects 200) [TestEbookUrl / cataloging].
    If fails: likely the toggle column/guard or template gate changed.
    Failure indicates e-book downloads disappeared from the book page."""
        book = (1, 'E Title', 'A', None, None, 2021, 'Tech', None, None,
                'E-Book', 'D', 'active', '2024-01-01', None, None, None,
                'https://drive.google.com/file/d/ABC123/view', True)
        mock_db['fetch_one'].return_value = book
        mock_db['fetch_all'].return_value = []
        body = client.get('/book/1').data.decode()
        assert '/book/1/download' in body

    def test_download_blocked_when_disabled(self, client, mock_db):
        """We block /book/1/download when ebook_allow_download is False `/book/1/download` (expects 302) [TestEbookUrl / cataloging].
    If fails: likely the download toggle guard changed.
    Failure indicates a direct URL bypasses the librarian's download toggle."""
        from unittest.mock import patch
        book = (1, 'E Title', 'A', None, None, 2021, 'Tech', None, None,
                'E-Book', 'D', 'active', '2024-01-01', None, None, None,
                'https://drive.google.com/file/d/ABC123/view', False)
        mock_db['fetch_one'].return_value = book
        with patch('app.cataloging.models.open_ebook_stream') as opener:
            resp = client.get('/book/1/download')
        assert resp.status_code == 302
        assert '/book/1' in resp.location
        assert opener.call_count == 0

    def test_download_allowed_when_enabled_streams(self, client, mock_db):
        """We stream /book/1/download when ebook_allow_download is True `/book/1/download` (expects 200) [TestEbookUrl / cataloging].
    If fails: likely the download toggle guard changed.
    Failure indicates enabled e-books stopped downloading."""
        from unittest.mock import patch
        class FakeResp:
            headers = {'Content-Type': 'application/pdf', 'Content-Length': '2'}
            def iter_content(self, chunk_size):
                yield b'ok'
            def close(self):
                pass
        book = (1, 'E Title', 'A', None, None, 2021, 'Tech', None, None,
                'E-Book', 'D', 'active', '2024-01-01', None, None, None,
                'https://drive.google.com/file/d/ABC123/view', True)
        mock_db['fetch_one'].return_value = book
        with patch('app.cataloging.models.open_ebook_stream',
                   return_value=(FakeResp(), None)):
            resp = client.get('/book/1/download')
        assert resp.status_code == 200
        assert resp.data == b'ok'

    def test_add_ebook_checked_toggle_stored_true(self, librarian_client, mock_db):
        """We store ebook_allow_download TRUE when the add checkbox is ticked `/librarian/cataloging/add` as librarian (expects 302) [TestEbookUrl / cataloging].
    If fails: likely form parsing or create_book wiring changed.
    Failure indicates the new-book download toggle never reaches the DB."""
        mock_db['execute'].return_value = [(1,)]
        mock_db['fetch_one'].return_value = None
        resp = librarian_client.post('/librarian/cataloging/add', data={
            'title': 'E', 'author': 'A', 'year_published': '2021',
            'subject_classification': 'Tech', 'material_type': 'E-Book',
            'ebook_url': 'https://drive.google.com/file/d/ABC123/view',
            'ebook_allow_download': '1',
        })
        assert 'mstatus=success' in resp.location
        book_calls = [c for c in mock_db['execute'].call_args_list
                      if 'INSERT INTO book_catalog' in c[0][0]]
        assert 'ebook_allow_download' in book_calls[0][0][0]
        assert book_calls[0][0][1][-1] is True

    def test_add_ebook_unchecked_toggle_stored_false(self, librarian_client, mock_db):
        """We store ebook_allow_download FALSE when the add checkbox is unticked `/librarian/cataloging/add` as librarian (expects 302) [TestEbookUrl / cataloging].
    If fails: likely form parsing or create_book wiring changed.
    Failure indicates a missing checkbox silently re-enables downloads."""
        mock_db['execute'].return_value = [(1,)]
        mock_db['fetch_one'].return_value = None
        resp = librarian_client.post('/librarian/cataloging/add', data={
            'title': 'E', 'author': 'A', 'year_published': '2021',
            'subject_classification': 'Tech', 'material_type': 'E-Book',
            'ebook_url': 'https://drive.google.com/file/d/ABC123/view',
        })
        assert 'mstatus=success' in resp.location
        book_calls = [c for c in mock_db['execute'].call_args_list
                      if 'INSERT INTO book_catalog' in c[0][0]]
        assert 'ebook_allow_download' in book_calls[0][0][0]
        assert book_calls[0][0][1][-1] is False

    def test_edit_book_toggle_stored(self, librarian_client, mock_db):
        """We write ebook_allow_download on edit of an existing book title `/librarian/cataloging/1/edit` as librarian (expects 302) [TestEbookUrl / cataloging].
    If fails: likely edit form parsing or update_book wiring changed.
    Failure indicates unticking the toggle never unticks the stored value."""
        mock_db['fetch_one'].return_value = SAMPLE_BOOKS[0]
        mock_db['execute'].return_value = 1
        resp = librarian_client.post('/librarian/cataloging/1/edit', data={
            'title': 'Updated Title',
            'author': 'Updated Author',
            'material_type': 'E-Book',
            'year_published': '2021',
            'subject_classification': 'Tech',
            'ebook_url': 'https://drive.google.com/file/d/ABC123/view',
        })
        assert resp.status_code == 302
        upd_calls = [c for c in mock_db['execute'].call_args_list
                     if 'UPDATE book_catalog' in c[0][0]]
        assert upd_calls
        assert 'ebook_allow_download' in upd_calls[0][0][0]
        assert upd_calls[0][0][1][-3] is False
        assert upd_calls[0][0][1][-1] == 1

    def test_download_helpers(self, mock_db):
        """Validates download source urls and filenames [TestEbookUrl / cataloging].
    If fails: likely Google download endpoint or filename helper changed.
    Failure indicates downloads break or leak a bad filename."""
        from app.cataloging.models import (
            download_source_url, ebook_download_filename, MAX_EBOOK_DOWNLOAD_BYTES,
        )
        assert download_source_url('drive', 'ABC123', None) == (
            'https://drive.usercontent.google.com/download?id=ABC123&export=download&confirm=t')
        shared = ('https://docs.google.com/document/d/1ekPEknmkae6q2KBCACQaPeeoJhF5aE57'
                  '/edit?usp=sharing&ouid=108913924297114452491&rtpof=true&sd=true')
        assert download_source_url('docs', None, shared) == (
            'https://docs.google.com/document/d/1ekPEknmkae6q2KBCACQaPeeoJhF5aE57/export?format=pdf')
        assert download_source_url('external', None, 'https://x.com/f') == ''
        assert download_source_url(None, None, None) == ''
        assert ebook_download_filename('Algebra Made Easy! (2nd ed)') == 'algebra-made-easy-2nd-ed.pdf'
        assert ebook_download_filename('') == 'ebook.pdf'
        assert len(ebook_download_filename('x' * 200)) <= 84
        assert MAX_EBOOK_DOWNLOAD_BYTES == 100 * 1024 * 1024

    def test_download_streams_drive_file(self, client, mock_db):
        """Validates download streams drive file `/book/1/download` (expects 200) [TestEbookUrl / cataloging].
    If fails: likely proxy route or streaming generator changed.
    Failure indicates downloads fail or leak the raw Google URL."""
        from unittest.mock import patch
        class FakeResp:
            headers = {'Content-Type': 'application/pdf', 'Content-Length': '5'}
            def iter_content(self, chunk_size):
                yield b'12345'
            def close(self):
                pass
        book = (1, 'E Title', 'A', None, None, 2021, 'Tech', None, None,
                'E-Book', 'D', 'active', '2024-01-01', None, None, None,
                'https://drive.google.com/file/d/ABC123/view')
        mock_db['fetch_one'].return_value = book
        with patch('app.cataloging.models.open_ebook_stream', return_value=(FakeResp(), None)) as opener:
            resp = client.get('/book/1/download')
        assert resp.status_code == 200
        assert resp.data == b'12345'
        assert resp.headers['Content-Disposition'] == 'attachment; filename="e-title.pdf"'
        args, _ = opener.call_args
        assert 'drive.usercontent.google.com/download' in args[0]
        assert 'id=ABC123' in args[0]
        assert 'https://drive.google.com/file/d/ABC123' not in resp.headers['Content-Disposition']

    def test_download_streams_docs_pdf(self, client, mock_db):
        """Validates download streams docs pdf `/book/1/download` (expects 200) [TestEbookUrl / cataloging].
    If fails: likely the Docs export endpoint changed.
    Failure indicates Docs downloads fail."""
        from unittest.mock import patch
        class FakeResp:
            headers = {'Content-Type': 'application/pdf'}
            def iter_content(self, chunk_size):
                yield b'PAA'
            def close(self):
                pass
        book = (1, 'E Title', 'A', None, None, 2021, 'Tech', None, None,
                'E-Book', 'D', 'active', '2024-01-01', None, None, None,
                'https://docs.google.com/document/d/DOC123/edit')
        mock_db['fetch_one'].return_value = book
        with patch('app.cataloging.models.open_ebook_stream', return_value=(FakeResp(), None)) as opener:
            resp = client.get('/book/1/download')
        assert resp.status_code == 200
        assert resp.data == b'PAA'
        args, _ = opener.call_args
        assert args[0] == 'https://docs.google.com/document/d/DOC123/export?format=pdf'

    def test_download_rejects_unshared_file(self, client, mock_db):
        """Validates download rejects unshared file `/book/1/download` (expects 302) [TestEbookUrl / cataloging].
    If fails: likely refusal handling changed.
    Failure indicates confusing output when the file is not link-shared."""
        from unittest.mock import patch
        book = (1, 'E Title', 'A', None, None, 2021, 'Tech', None, None,
                'E-Book', 'D', 'active', '2024-01-01', None, None, None,
                'https://drive.google.com/file/d/ABC123/view')
        mock_db['fetch_one'].return_value = book
        warn = ('The source file is not publicly downloadable — check it '
                'is shared as "Anyone with the link can view".')
        with patch('app.cataloging.models.open_ebook_stream', return_value=(None, warn)):
            resp = client.get('/book/1/download')
        assert resp.status_code == 302
        assert '/book/1' in resp.location

    def test_download_rejects_oversize_file(self, client, mock_db):
        """Validates download rejects oversize file `/book/1/download` (expects 302) [TestEbookUrl / cataloging].
    If fails: likely the size cap changed.
    Failure indicates unbounded downloads reach the server."""
        from unittest.mock import patch
        from app.cataloging.models import MAX_EBOOK_DOWNLOAD_BYTES
        book = (1, 'E Title', 'A', None, None, 2021, 'Tech', None, None,
                'E-Book', 'D', 'active', '2024-01-01', None, None, None,
                'https://drive.google.com/file/d/ABC123/view')
        mock_db['fetch_one'].return_value = book
        class FakeResp:
            headers = {'Content-Type': 'application/pdf',
                       'Content-Length': str(MAX_EBOOK_DOWNLOAD_BYTES + 1)}
            def close(self):
                pass
        with patch('app.cataloging.models.open_ebook_stream', return_value=(FakeResp(), None)):
            with patch('app.cataloging.models.parse_size_bytes',
                       return_value=MAX_EBOOK_DOWNLOAD_BYTES + 1):
                resp = client.get('/book/1/download')
        assert resp.status_code == 302
        assert '/book/1' in resp.location

    def test_download_rejects_non_ebook(self, client, mock_db):
        """Validates download rejects non ebook `/book/1/download` (expects 302) [TestEbookUrl / cataloging].
    If fails: likely the no-link guard changed.
    Failure indicates downloads hit Google without a link."""
        from unittest.mock import patch
        book = (1, 'Plain Book', 'A', None, None, 2021, 'Tech', None, None,
                'Book', 'D', 'active', '2024-01-01', None, None, None,
                None)
        mock_db['fetch_one'].return_value = book
        with patch('app.cataloging.models.open_ebook_stream') as opener:
            resp = client.get('/book/1/download')
        assert resp.status_code == 302
        assert '/book/1' in resp.location
        assert opener.call_count == 0

    def test_download_missing_book_404(self, client, mock_db):
        """Validates download missing book 404 `/book/1/download` (expects 404) [TestEbookUrl / cataloging].
    If fails: likely the book lookup guard changed.
    Failure indicates downloads serve nonexistent titles."""
        mock_db['fetch_one'].return_value = None
        resp = client.get('/book/1/download')
        assert resp.status_code == 404

    def test_download_logs_access(self, client, mock_db):
        """Validates download logs access `/book/1/download` (expects 200) [TestEbookUrl / cataloging].
    If fails: likely the analytics logging hook moved or changed.
    Failure indicates downloads are invisible to Resource Analytics."""
        from unittest.mock import patch
        class FakeResp:
            headers = {'Content-Type': 'application/pdf'}
            def iter_content(self, chunk_size):
                yield b'12345'
            def close(self):
                pass
        book = (1, 'E Title', 'A', None, None, 2021, 'Tech', None, None,
                'E-Book', 'D', 'active', '2024-01-01', None, None, None,
                'https://drive.google.com/file/d/ABC123/view')
        mock_db['fetch_one'].return_value = book
        with patch('app.cataloging.models.open_ebook_stream',
                   return_value=(FakeResp(), None)):
            with patch('app.cataloging.models.create_ebook_access') as log:
                resp = client.get('/book/1/download')
        assert resp.status_code == 200
        assert log.call_count == 1
        assert log.call_args[0] == (1, 'download', None)

    def test_download_log_failure_still_serves(self, client, mock_db):
        """Validates download log failure still serves `/book/1/download` (expects 200) [TestEbookUrl / cataloging].
    If fails: likely the best-effort try/except was removed.
    Failure indicates readers lose downloads when analytics logging errors."""
        from unittest.mock import patch
        class FakeResp:
            headers = {'Content-Type': 'application/pdf'}
            def iter_content(self, chunk_size):
                yield b'ok'
            def close(self):
                pass
        book = (1, 'E Title', 'A', None, None, 2021, 'Tech', None, None,
                'E-Book', 'D', 'active', '2024-01-01', None, None, None,
                'https://drive.google.com/file/d/ABC123/view')
        mock_db['fetch_one'].return_value = book
        with patch('app.cataloging.models.open_ebook_stream',
                   return_value=(FakeResp(), None)):
            with patch('app.cataloging.models.create_ebook_access',
                       side_effect=RuntimeError('boom')):
                resp = client.get('/book/1/download')
        assert resp.status_code == 200
        assert resp.data == b'ok'

    def test_read_logs_access(self, client, mock_db):
        """Validates read logs access `POST /book/1/read` (expects 204) [TestEbookUrl / cataloging].
    If fails: likely the read postback route changed.
    Failure indicates Read Online opens are invisible to Resource Analytics."""
        from unittest.mock import patch
        book = (1, 'E Title', 'A', None, None, 2021, 'Tech', None, None,
                'E-Book', 'D', 'active', '2024-01-01', None, None, None,
                'https://drive.google.com/file/d/ABC123/view')
        mock_db['fetch_one'].return_value = book
        with patch('app.cataloging.models.create_ebook_access') as log:
            resp = client.post('/book/1/read')
        assert resp.status_code == 204
        assert resp.data == b''
        assert log.call_count == 1
        assert log.call_args[0] == (1, 'read', None)

    def test_read_rejects_non_ebook(self, client, mock_db):
        """Validates read rejects non ebook `POST /book/1/read` (expects 404) [TestEbookUrl / cataloging].
    If fails: likely the e-book link guard changed.
    Failure indicates physical titles are logged as e-book reads."""
        from unittest.mock import patch
        book = (1, 'Plain Book', 'A', None, None, 2021, 'Tech', None, None,
                'Book', 'D', 'active', '2024-01-01', None, None, None, None)
        mock_db['fetch_one'].return_value = book
        with patch('app.cataloging.models.create_ebook_access') as log:
            resp = client.post('/book/1/read')
        assert resp.status_code == 404
        assert log.call_count == 0

    def test_read_missing_book_404(self, client, mock_db):
        """Validates read missing book 404 `POST /book/999/read` (expects 404) [TestEbookUrl / cataloging].
    If fails: likely the book lookup guard changed.
    Failure indicates phantom titles are logged as e-book reads."""
        mock_db['fetch_one'].return_value = None
        resp = client.post('/book/999/read')
        assert resp.status_code == 404

    def test_read_archived_book_404(self, client, mock_db):
        """Validates read archived book 404 `POST /book/1/read` (expects 404) [TestEbookUrl / cataloging].
    If fails: likely the catalog_status guard changed.
    Failure indicates archived titles are logged as e-book reads."""
        book = (1, 'Old Title', 'A', None, None, 2019, 'Tech', None, None,
                'E-Book', 'D', 'archived', '2024-01-01', None, None, None,
                'https://drive.google.com/file/d/ABC123/view')
        mock_db['fetch_one'].return_value = book
        resp = client.post('/book/1/read')
        assert resp.status_code == 404

    def test_read_logs_user_when_signed_in(self, librarian_client, mock_db):
        """Validates read logs user when signed in `POST /book/1/read` as librarian (expects 204) [TestEbookUrl / cataloging].
    If fails: likely the signed-in user attribution changed.
    Failure indicates reads cannot be attributed to members."""
        from unittest.mock import patch
        book = (1, 'E Title', 'A', None, None, 2021, 'Tech', None, None,
                'E-Book', 'D', 'active', '2024-01-01', None, None, None,
                'https://drive.google.com/file/d/ABC123/view')
        mock_db['fetch_one'].return_value = book
        with patch('app.cataloging.models.create_ebook_access') as log:
            resp = librarian_client.post('/book/1/read')
        assert resp.status_code == 204
        assert log.call_args[0][0] == 1
        assert log.call_args[0][1] == 'read'
        assert log.call_args[0][2] is not None

    def test_catalog_card_read_online(self, client, mock_db):
        """Validates catalog card read online `/catalog?q=E` (expects 200) [TestEbookUrl / cataloging].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates catalog data or listing/sort is wrong."""
        book = (1, 'E Title', 'A', None, None, 2021, 'Tech', None, None,
                'E-Book', 'D', 'active', '2024-01-01', None, None, None,
                'https://drive.google.com/file/d/ABC123/view', 'available', 1)
        mock_db['fetch_one'].return_value = (1,)
        mock_db['fetch_all'].side_effect = [[book], [], []]
        body = client.get('/catalog?q=E').data.decode()
        # E-Book cards route readers to the book page (modal preview lives
        # there); the raw link is never emitted on the list page.
        assert 'Read Online' in body
        assert '/book/1' in body
        assert 'target="_blank" rel="noopener"' not in body
        assert 'https://drive.google.com/file/d/ABC123/view' not in body


class TestBookSelectShape:
    """book_catalog reads name their columns so positional indices hold."""

    def test_get_book_by_id_selects_columns_by_name(self, mock_db):
        """Validates get_book_by_id selects columns explicitly [TestBookSelectShape / cataloging].
    If fails: likely projection reverted to SELECT * (ebook_url index drifts).
    Failure indicates the /book e-book link breaks on migrated databases."""
        from app.cataloging.models import get_book_by_id
        mock_db['fetch_one'].return_value = (1,)
        get_book_by_id(1)
        query = mock_db['fetch_one'].call_args[0][0]
        assert query.startswith('SELECT book_id')
        assert 'category_id' in query and 'ebook_url' in query
        assert 'SELECT *' not in query

    def test_get_book_by_id_falls_back_on_missing_columns(self, mock_db):
        """Validates get_book_by_id falls back to SELECT * when columns are missing [TestBookSelectShape / cataloging].
    If fails: likely unmigrated-DB fallback removed (reads 500).
    Failure indicates reads break on a database without the new columns."""
        from app.cataloging.models import get_book_by_id
        missing = Exception(
            'column "ebook_url" of relation "book_catalog" does not exist')
        missing.pgcode = '42703'
        mock_db['fetch_one'].side_effect = [missing, (1,)]
        assert get_book_by_id(1) == (1,)
        fallback = mock_db['fetch_one'].call_args_list[1][0][0]
        assert fallback == 'SELECT * FROM book_catalog WHERE book_id = %s'


class TestMaterialTypeFields:
    """Book detail fields adapt to the material type."""

    @staticmethod
    def _book(mtype, identifier=None, ebook_url=None):
        return (1, 'Title', 'Author', '1st', 'Pub', 2024, 'Cat', 'QA1',
                identifier, mtype, 'D', 'active', '2024-01-01', None, None,
                None, ebook_url)

    def test_periodical_shows_issn_not_isbn(self, client, mock_db):
        """Validates periodical detail labels the identifier ISSN [TestMaterialTypeFields / cataloging].
    If fails: likely per-type field logic removed.
    Failure indicates /book shows the wrong label for a periodical."""
        mock_db['fetch_one'].return_value = self._book('Periodical', '1234-567X')
        mock_db['fetch_all'].return_value = []
        body = client.get('/book/1').data.decode()
        assert 'ISSN</h4>' in body
        assert 'ISBN</h4>' not in body
        assert 'Edition</h4>' not in body
        assert 'LOC Classification</h4>' not in body
        assert 'Publisher</h4>' in body

    def test_thesis_hides_inapplicable_fields(self, client, mock_db):
        """Validates thesis detail hides edition/publisher/identifier/LOC [TestMaterialTypeFields / cataloging].
    If fails: likely per-type field logic removed.
    Failure indicates /book shows inapplicable fields for a thesis."""
        mock_db['fetch_one'].return_value = self._book('Thesis')
        mock_db['fetch_all'].return_value = []
        body = client.get('/book/1').data.decode()
        assert 'Edition</h4>' not in body
        assert 'Publisher</h4>' not in body
        assert 'ISBN</h4>' not in body
        assert 'LOC Classification</h4>' not in body

    def test_ebook_without_link_shows_note(self, client, mock_db):
        """Validates e-book detail always shows an Online Access note [TestMaterialTypeFields / cataloging].
    If fails: likely e-book Online Access branch removed.
    Failure indicates /book hides online access for a link-less e-book."""
        mock_db['fetch_one'].return_value = self._book('E-Book')
        mock_db['fetch_all'].return_value = []
        body = client.get('/book/1').data.decode()
        assert 'Online Access' in body
        assert 'No online access link' in body
        assert 'Edition</h4>' not in body
        assert "openBorrowModal('')" not in body
        assert '>Reserve<' not in body

    def test_book_shows_full_field_set(self, client, mock_db):
        """Validates a plain book still shows every detail field [TestMaterialTypeFields / cataloging].
    If fails: likely per-type logic over-hid book fields.
    Failure indicates /book hides fields for a normal book."""
        mock_db['fetch_one'].return_value = self._book('Book', '9780306406157')
        mock_db['fetch_all'].return_value = []
        body = client.get('/book/1').data.decode()
        for label in ('Edition</h4>', 'Publisher</h4>', 'ISBN</h4>',
                      'LOC Classification</h4>'):
            assert label in body
        assert '>Reserve<' in body

    def test_catalog_hides_borrow_for_ebook_without_link(self, client, mock_db):
        """Validates catalog omits borrow/reserve for a link-less e-book [TestMaterialTypeFields / cataloging].
    If fails: likely e-book borrow suppression removed in catalog.html.
    Failure indicates catalog cards offer Borrow on an e-book."""
        book = (1, 'E Title', 'A', None, None, 2021, 'Tech', None, None,
                'E-Book', 'D', 'active', '2024-01-01', None, None, None,
                '', 'available', 1)
        mock_db['fetch_one'].return_value = (1,)
        mock_db['fetch_all'].side_effect = [[book], [], []]
        body = client.get('/catalog?q=E').data.decode()
        assert 'Read Online' not in body
        assert '>Borrow<' not in body
        assert '/user/reserve' not in body
