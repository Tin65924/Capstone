"""Tests for cataloging module: CRUD, search, RBAC, pagination, bulk import."""

import io
import csv

SAMPLE_BOOKS = [
    (1, 'Introduction to Algorithms', 'Cormen', '3rd', 'MIT Press', 2022,
     'Computer Science', 'QA76.73', '978-0262033848', 'Book',
     'A comprehensive textbook.', 'active', '2024-01-15', '2025-0001'),
    (2, 'Clean Code', 'Martin', '1st', 'Prentice Hall', 2008,
     'Software Engineering', 'QA76.76', '978-0132350884', 'Book',
     'A handbook of agile software craftsmanship.', 'active', '2024-02-10', '2025-0002, 2025-0003'),
    (3, 'The Great Gatsby', 'Fitzgerald', None, None, 1925,
     'Literature', None, None, 'Book',
     None, 'archived', '2024-03-01', ''),
]


class TestCatalogingAccess:
    def test_cataloging_student_forbidden(self, student_client):
        resp = student_client.get('/librarian/cataloging')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_cataloging_faculty_forbidden(self, faculty_client):
        resp = faculty_client.get('/librarian/cataloging')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_cataloging_librarian_allowed(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = SAMPLE_BOOKS
        resp = librarian_client.get('/librarian/cataloging')
        assert resp.status_code == 200
        assert b'Cataloging' in resp.data
        assert b'Accession Number' in resp.data
        assert b'2025-0001' in resp.data
        assert b'2025-0002, 2025-0003' in resp.data

    def test_cataloging_admin_allowed(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = SAMPLE_BOOKS
        resp = admin_client.get('/librarian/cataloging')
        assert resp.status_code == 200
        assert b'Cataloging' in resp.data

    def test_cataloging_unauthenticated_redirects(self, client):
        resp = client.get('/librarian/cataloging')
        assert resp.status_code == 302
        assert '/login' in resp.location


class TestCatalogingCRUD:
    def test_add_book_success(self, librarian_client, mock_db):
        mock_db['execute'].return_value = [(1,)]
        mock_db['fetch_one'].return_value = None
        resp = librarian_client.post('/librarian/cataloging/add', data={
            'title': 'New Book',
            'author': 'New Author',
            'isbn': '978-1234567890',
            'material_type': 'Book',
            'year_published': '2024',
            'accession_number': '2025-0001',
            'source': 'purchase',
        })
        assert resp.status_code == 302
        assert '/librarian/cataloging' in resp.location
        assert mock_db['execute'].call_count >= 2
        call_args = mock_db['execute'].call_args_list[0]
        assert 'INSERT INTO book_catalog' in call_args[0][0]
        call_args2 = mock_db['execute'].call_args_list[1]
        assert 'INSERT INTO accession_log' in call_args2[0][0]

    def test_add_book_without_accession(self, librarian_client, mock_db):
        mock_db['execute'].return_value = [(1,)]
        resp = librarian_client.post('/librarian/cataloging/add', data={
            'title': 'New Book',
            'author': 'New Author',
            'isbn': '978-1234567890',
            'material_type': 'Book',
        })
        assert resp.status_code == 302
        assert '/librarian/cataloging' in resp.location
        assert mock_db['execute'].call_count >= 1
        call_args = mock_db['execute'].call_args_list[0]
        assert 'INSERT INTO book_catalog' in call_args[0][0]

    def test_add_book_duplicate_accession(self, librarian_client, mock_db):
        mock_db['execute'].return_value = [(1,)]
        mock_db['fetch_one'].return_value = ('2025-0001',)
        resp = librarian_client.post('/librarian/cataloging/add', data={
            'title': 'New Book',
            'author': 'New Author',
            'accession_number': '2025-0001',
        })
        assert resp.status_code == 302
        assert '/librarian/cataloging' in resp.location

    def test_add_book_dedup_adds_copy(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [None, (5,)]
        mock_db['execute'].return_value = 1
        resp = librarian_client.post('/librarian/cataloging/add', data={
            'title': 'Existing Title',
            'author': 'Existing Author',
            'isbn': '978-1234567890',
            'accession_number': '2025-0099',
            'source': 'purchase',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count >= 2
        first_exec = mock_db['execute'].call_args_list[0][0][0]
        assert 'INSERT INTO accession_log' in first_exec
        assert all('INSERT INTO book_catalog' not in c[0][0]
                   for c in mock_db['execute'].call_args_list)

    def test_add_book_dedup_no_new_record(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (5,)
        mock_db['execute'].return_value = 1
        resp = librarian_client.post('/librarian/cataloging/add', data={
            'title': 'Existing Title',
            'author': 'Existing Author',
        })
        assert resp.status_code == 302
        assert all('INSERT INTO book_catalog' not in c[0][0]
                   for c in mock_db['execute'].call_args_list)

    def test_add_book_dedup_blank_isbn_matches(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [None, (5,)]
        mock_db['execute'].return_value = 1
        resp = librarian_client.post('/librarian/cataloging/add', data={
            'title': 'No ISBN Book',
            'author': 'No ISBN Author',
            'accession_number': '2025-0100',
        })
        assert resp.status_code == 302
        dedup_call = mock_db['fetch_one'].call_args_list[1][0]
        assert 'isbn IS NULL' in dedup_call[0]

    def test_add_book_missing_title(self, librarian_client, mock_db):
        resp = librarian_client.post('/librarian/cataloging/add', data={
            'title': '',
            'author': 'Some Author',
        })
        assert resp.status_code == 302

    def test_add_book_missing_author(self, librarian_client, mock_db):
        resp = librarian_client.post('/librarian/cataloging/add', data={
            'title': 'Some Title',
            'author': '',
        })
        assert resp.status_code == 302

    def test_edit_book_success(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = SAMPLE_BOOKS[0]
        mock_db['execute'].return_value = 1
        resp = librarian_client.post('/librarian/cataloging/1/edit', data={
            'title': 'Updated Title',
            'author': 'Updated Author',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count >= 1
        call_args = mock_db['execute'].call_args_list[0]
        assert 'UPDATE book_catalog' in call_args[0][0]

    def test_edit_book_not_found(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = None
        resp = librarian_client.post('/librarian/cataloging/999/edit', data={
            'title': 'Ghost',
            'author': 'Ghost',
        })
        assert resp.status_code == 302
        assert '/librarian/cataloging' in resp.location

    def test_toggle_book_status_archive(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = SAMPLE_BOOKS[0]
        mock_db['execute'].return_value = 1
        resp = librarian_client.post('/librarian/cataloging/1/status')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count >= 1
        call_args = mock_db['execute'].call_args_list[0]
        assert 'UPDATE book_catalog' in call_args[0][0]
        assert 'archived' in call_args[0][1]

    def test_toggle_book_status_not_found(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = None
        resp = librarian_client.post('/librarian/cataloging/999/status')
        assert resp.status_code == 302

    def test_delete_book_archived_success(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = SAMPLE_BOOKS[2]
        mock_db['execute'].return_value = 1
        resp = librarian_client.post('/librarian/cataloging/3/delete')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count >= 1
        call_args = mock_db['execute'].call_args_list[0]
        assert 'DELETE FROM book_catalog' in call_args[0][0]

    def test_delete_book_not_archived_fails(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = SAMPLE_BOOKS[0]
        resp = librarian_client.post('/librarian/cataloging/1/delete')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_delete_book_not_found(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = None
        resp = librarian_client.post('/librarian/cataloging/999/delete')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_delete_book_rbac_student_forbidden(self, student_client, mock_db):
        resp = student_client.post('/librarian/cataloging/3/delete')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_delete_book_rbac_faculty_forbidden(self, faculty_client, mock_db):
        resp = faculty_client.post('/librarian/cataloging/3/delete')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_delete_book_unauthenticated(self, client, mock_db):
        resp = client.post('/librarian/cataloging/3/delete')
        assert resp.status_code == 302
        assert '/login' in resp.location

    def test_add_accession_success(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [SAMPLE_BOOKS[0], None]
        mock_db['execute'].return_value = 1
        resp = librarian_client.post('/librarian/cataloging/1/accession/add', data={
            'accession_number': '2025-0001',
            'source': 'purchase',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count >= 1
        call_args = mock_db['execute'].call_args_list[0]
        assert 'INSERT INTO accession_log' in call_args[0][0]

    def test_add_accession_duplicate(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [SAMPLE_BOOKS[0], ('2025-0001',)]
        mock_db['execute'].return_value = 1
        resp = librarian_client.post('/librarian/cataloging/1/accession/add', data={
            'accession_number': '2025-0001',
        })
        assert resp.status_code == 302

    def test_add_accession_missing_number(self, librarian_client, mock_db):
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
        mock_db['fetch_all'].side_effect = [SAMPLE_BOOKS, SAMPLE_COPIES]
        resp = librarian_client.get('/librarian/cataloging')
        assert resp.status_code == 200
        assert b'ACC-0015' in resp.data
        assert b'Edit Accession Copy' in resp.data
        assert b'2 copy/copies for' in resp.data

    def test_edit_accession_success(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [SAMPLE_ACC_ROW, None]
        resp = librarian_client.post('/librarian/cataloging/accession/21/edit', data={
            'accession_number': 'ACC-0099',
            'source': 'donation',
        })
        assert resp.status_code == 302
        call_args = mock_db['execute'].call_args_list[0]
        assert 'UPDATE accession_log' in call_args[0][0]
        assert call_args[0][1] == ('ACC-0099', 'donation', 21)

    def test_edit_accession_duplicate(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [SAMPLE_ACC_ROW, (99, 'ACC-0099', 2, 3, '2025-01-01', 'purchase')]
        resp = librarian_client.post('/librarian/cataloging/accession/21/edit', data={
            'accession_number': 'ACC-0099',
        })
        assert resp.status_code == 302
        assert all('UPDATE accession_log' not in c[0][0] for c in mock_db['execute'].call_args_list)

    def test_edit_accession_missing_number(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = SAMPLE_ACC_ROW
        resp = librarian_client.post('/librarian/cataloging/accession/21/edit', data={
            'accession_number': '',
        })
        assert resp.status_code == 302
        assert all('UPDATE accession_log' not in c[0][0] for c in mock_db['execute'].call_args_list)

    def test_edit_accession_not_found(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = None
        resp = librarian_client.post('/librarian/cataloging/accession/999/edit', data={
            'accession_number': 'ACC-0099',
        })
        assert resp.status_code == 302
        assert all('UPDATE accession_log' not in c[0][0] for c in mock_db['execute'].call_args_list)

    def test_delete_accession_success(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [SAMPLE_ACC_ROW, None]
        resp = librarian_client.post('/librarian/cataloging/accession/21/delete')
        assert resp.status_code == 302
        call_args = mock_db['execute'].call_args_list[0]
        assert 'DELETE FROM accession_log' in call_args[0][0]
        assert call_args[0][1] == (21,)

    def test_delete_accession_referenced(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [SAMPLE_ACC_ROW, (1,)]
        resp = librarian_client.post('/librarian/cataloging/accession/21/delete')
        assert resp.status_code == 302
        assert all('DELETE FROM accession_log' not in c[0][0] for c in mock_db['execute'].call_args_list)


class TestCatalogingSearch:
    def test_search_by_title(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = [SAMPLE_BOOKS[0]]
        mock_db['fetch_one'].return_value = (1,)
        resp = librarian_client.get('/librarian/cataloging?q=Algorithms&field=title')
        assert resp.status_code == 200
        assert b'Algorithms' in resp.data

    def test_search_by_author(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = [SAMPLE_BOOKS[1]]
        mock_db['fetch_one'].return_value = (1,)
        resp = librarian_client.get('/librarian/cataloging?q=Martin&field=author')
        assert resp.status_code == 200

    def test_search_no_results(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = []
        mock_db['fetch_one'].return_value = (0,)
        resp = librarian_client.get('/librarian/cataloging?q=zzzxxx')
        assert resp.status_code == 200

    def test_search_all_fields_matches_accession(self, librarian_client, mock_db):
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
        mock_db['fetch_all'].return_value = SAMPLE_BOOKS
        mock_db['fetch_one'].return_value = (3,)
        resp = librarian_client.get('/librarian/cataloging?page=1')
        assert resp.status_code == 200
        assert b'Showing' in resp.data


class TestPublicCatalog:
    def test_public_catalog_all(self, client, mock_db):
        mock_db['fetch_all'].return_value = SAMPLE_BOOKS
        resp = client.get('/catalog')
        assert resp.status_code == 200
        assert b'Catalog' in resp.data or b'Search' in resp.data

    def test_public_catalog_search(self, client, mock_db):
        mock_db['fetch_all'].return_value = [SAMPLE_BOOKS[0]]
        resp = client.get('/catalog?q=Algorithms')
        assert resp.status_code == 200

    def test_public_catalog_no_results(self, client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = client.get('/catalog?q=nonexistent')
        assert resp.status_code == 200

    def test_public_catalog_filters(self, client, mock_db):
        mock_db['fetch_all'].side_effect = [
            SAMPLE_BOOKS,                # search_books_filtered books
            [('Fiction',), ('Reference',)],  # get_distinct_categories
        ]
        resp = client.get('/catalog?q=harry&sort_by=title&category=Fiction&material_type=ebook&availability=available&year_from=2000&year_to=2026')
        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        assert 'Sort by relevance' in body
        assert 'Fiction' in body
        assert 'E-Books' in body
        assert 'Physical books' in body
        assert 'Active filters' in body

    def test_public_catalog_filter_params_passed(self, client, mock_db):
        mock_db['fetch_all'].side_effect = [
            [],                            # search_books_filtered books
            [],                            # get_distinct_categories
        ]
        resp = client.get('/catalog?category=Fiction&material_type=physical&availability=borrowed&sort_by=year_desc&year_from=2010&year_to=2020')
        assert resp.status_code == 200
        assert b'No books found' in resp.data

    def test_public_catalog_sidebar_sections(self, client, mock_db):
        mock_db['fetch_all'].side_effect = [
            SAMPLE_BOOKS,                  # search_books_filtered books
            [],                            # get_distinct_categories
        ]
        resp = client.get('/catalog')
        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        for label in ['Sort', 'Category', 'Type', 'Availability', 'Year']:
            assert label in body, f'missing sidebar section: {label}'

    def test_public_catalog_pagination(self, client, mock_db):
        many_books = [
            (i, f'Book {i}', 'Author', None, None, 2000 + i,
             'Fiction', None, None, 'Book',
             None, 'active', '2024-01-01')
            for i in range(1, 121)
        ]
        mock_db['fetch_all'].side_effect = [
            many_books,                  # search_books_filtered books (120)
            [],                          # get_distinct_categories
        ]
        resp = client.get('/catalog')
        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        assert '>1 - 50</span> of <span class="font-medium text-slate-900 dark:text-slate-100">120</span>' in body
        assert 'Next' in body

        mock_db['fetch_all'].side_effect = [many_books, []]
        resp2 = client.get('/catalog?page=3')
        assert resp2.status_code == 200
        body2 = resp2.get_data(as_text=True)
        assert '>101 - 120</span> of <span class="font-medium text-slate-900 dark:text-slate-100">120</span>' in body2

    def test_book_info_found(self, client, mock_db):
        mock_db['fetch_one'].return_value = SAMPLE_BOOKS[0]
        mock_db['fetch_all'].return_value = []
        resp = client.get('/book/1')
        assert resp.status_code == 200
        assert b'Introduction to Algorithms' in resp.data

    def test_book_info_not_found(self, client, mock_db):
        mock_db['fetch_one'].return_value = None
        resp = client.get('/book/999')
        assert resp.status_code == 302

    def test_book_info_with_accessions(self, client, mock_db):
        mock_db['fetch_one'].return_value = SAMPLE_BOOKS[0]
        mock_db['fetch_all'].return_value = [
            (1, '2025-0001', 1, 4, '2025-01-10', 'purchase'),
        ]
        resp = client.get('/book/1')
        assert resp.status_code == 200
        assert b'2025-0001' in resp.data

    def test_book_info_shows_borrow_when_available(self, client, mock_db):
        mock_db['fetch_one'].return_value = SAMPLE_BOOKS[0]
        mock_db['fetch_all'].side_effect = [
            [(1, '2025-0001', 1, 4, '2025-01-10', 'purchase')],
            [],
        ]
        resp = client.get('/book/1')
        assert resp.status_code == 200
        assert b'Borrow' in resp.data
        assert b'Available in Library' in resp.data

    def test_book_info_shows_reserve_when_borrowed(self, client, mock_db):
        mock_db['fetch_one'].return_value = SAMPLE_BOOKS[0]
        mock_db['fetch_all'].side_effect = [
            [(1, '2025-0001', 1, 4, '2025-01-10', 'purchase')],
            [(1,)],
        ]
        resp = client.get('/book/1')
        assert resp.status_code == 200
        assert b'Reserve' in resp.data
        assert b'Not Available' in resp.data


def _csv_file(content, filename='books.csv'):
    """Build a Werkzeug FileStorage-like upload from a CSV string."""
    return (io.BytesIO(content.encode('utf-8')), filename)


class TestBulkImport:
    """Bulk CSV import: header detection, encoding, validation, RBAC, edge cases."""

    VALID_ROW = ('Book A', 'Author A', 'ACC-001', '978-1', '1st', 'Pub A', 2023,
                 'CS', 'QA100', 'Book', 'Desc A', 'purchase')

    @staticmethod
    def _make_csv(rows, headers=None):
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
        assert resp.status_code == expected_status
        data = resp.get_json()
        assert data is not None
        assert 'error' in data

    def _assert_job(self, resp):
        assert resp.status_code == 200
        data = resp.get_json()
        assert data is not None
        assert 'job_id' in data
        assert data['redirect'] is not None

    def test_bulk_import_rbac_student(self, student_client):
        resp = student_client.post('/librarian/cataloging/bulk-import', data={
            'file': _csv_file(self._make_csv([self.VALID_ROW])),
        })
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_bulk_import_rbac_faculty(self, faculty_client):
        resp = faculty_client.post('/librarian/cataloging/bulk-import', data={
            'file': _csv_file(self._make_csv([self.VALID_ROW])),
        })
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_bulk_import_unauthenticated(self, client):
        resp = client.post('/librarian/cataloging/bulk-import', data={
            'file': _csv_file(self._make_csv([self.VALID_ROW])),
        })
        assert resp.status_code == 302
        assert '/login' in resp.location

    def test_bulk_import_no_file(self, librarian_client):
        resp = librarian_client.post('/librarian/cataloging/bulk-import')
        self._assert_error(resp, 400)

    def test_bulk_import_empty_filename(self, librarian_client):
        resp = librarian_client.post('/librarian/cataloging/bulk-import', data={
            'file': (io.BytesIO(b''), ''),
        })
        self._assert_error(resp, 400)

    def test_bulk_import_wrong_extension(self, librarian_client):
        resp = librarian_client.post('/librarian/cataloging/bulk-import', data={
            'file': (io.BytesIO(b'a,b,c'), 'books.txt'),
        })
        self._assert_error(resp, 400)

    def test_bulk_import_empty_file(self, librarian_client, mock_db):
        resp = librarian_client.post('/librarian/cataloging/bulk-import', data={
            'file': _csv_file(''),
        })
        self._assert_error(resp, 400)

    def test_bulk_import_headers_only(self, librarian_client, mock_db):
        resp = librarian_client.post('/librarian/cataloging/bulk-import', data={
            'file': _csv_file('title,author,accession_number,year\n'),
        })
        self._assert_job(resp)

    def test_bulk_import_missing_required_columns(self, librarian_client, mock_db):
        resp = librarian_client.post('/librarian/cataloging/bulk-import', data={
            'file': _csv_file(self._make_csv([('NoAuthor',)], headers=['title'])),
        })
        self._assert_error(resp, 400)

    def test_bulk_import_missing_accession_column(self, librarian_client, mock_db):
        resp = librarian_client.post('/librarian/cataloging/bulk-import', data={
            'file': _csv_file(self._make_csv([('Title', 'Author')], headers=['title', 'author'])),
        })
        self._assert_error(resp, 400)

    def test_bulk_import_success(self, librarian_client, mock_db):
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

    def test_bulk_import_headers_random_order(self, librarian_client, mock_db):
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
        mock_db['execute'].return_value = [(1,)]
        mock_db['fetch_one'].return_value = None
        csv_content = self._make_csv([('BOM Book', 'BOM Author', 'ACC-007')])
        resp = librarian_client.post('/librarian/cataloging/bulk-import', data={
            'file': (io.BytesIO(csv_content.encode('utf-8-sig')), 'books.csv'),
        })
        self._assert_job(resp)

    def test_bulk_import_latin1_encoding(self, librarian_client, mock_db):
        mock_db['execute'].return_value = [(1,)]
        mock_db['fetch_one'].return_value = None
        csv_content = self._make_csv([('José García', 'François', 'ACC-008')],
                                     headers=['title', 'author', 'accession_number'])
        resp = librarian_client.post('/librarian/cataloging/bulk-import', data={
            'file': (io.BytesIO(csv_content.encode('latin-1')), 'books.csv'),
        })
        self._assert_job(resp)

    def test_bulk_import_unicode_titles(self, librarian_client, mock_db):
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
        csv_content = 'value1,value2,value3'
        resp = librarian_client.post('/librarian/cataloging/bulk-import', data={
            'file': _csv_file(csv_content),
        })
        self._assert_error(resp, 400)

    def test_bulk_import_whitespace_headers(self, librarian_client, mock_db):
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
        mock_db['execute'].return_value = [(1,)]
        mock_db['fetch_one'].return_value = None
        rows = [(f'Book {i}', f'Author {i}', f'ACC-{i:04d}', f'978-{i:06d}') for i in range(500)]
        csv_content = self._make_csv(rows, headers=['title', 'author', 'accession_number', 'isbn'])
        resp = librarian_client.post('/librarian/cataloging/bulk-import', data={
            'file': _csv_file(csv_content),
        })
        self._assert_job(resp)

    def test_bulk_import_extra_unknown_headers(self, librarian_client, mock_db):
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

class TestActiveLoanIncludesOverdue:
    def test_get_active_loan_by_accession_includes_overdue(self, mock_db):
        from app.circulation.models import get_active_loan_by_accession
        mock_db['fetch_one'].return_value = None

        get_active_loan_by_accession(1)

        call_args = mock_db['fetch_one'].call_args_list[0]
        assert 'overdue' in call_args[0][0]