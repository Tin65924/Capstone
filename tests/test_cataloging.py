"""Tests for cataloging module: CRUD, search, RBAC, pagination, bulk import."""

import io
import csv

SAMPLE_BOOKS = [
    (1, 'Introduction to Algorithms', 'Cormen', '3rd', 'MIT Press', 2022,
     'Computer Science', 'QA76.73', '978-0262033848', 'Book',
     'A comprehensive textbook.', 'active', '2024-01-15'),
    (2, 'Clean Code', 'Martin', '1st', 'Prentice Hall', 2008,
     'Software Engineering', 'QA76.76', '978-0132350884', 'Book',
     'A handbook of agile software craftsmanship.', 'active', '2024-02-10'),
    (3, 'The Great Gatsby', 'Fitzgerald', None, None, 1925,
     'Literature', None, None, 'Book',
     None, 'archived', '2024-03-01'),
]


class TestCatalogingAccess:
    def test_cataloging_student_forbidden(self, student_client):
        resp = student_client.get('/cataloging')
        assert resp.status_code == 403

    def test_cataloging_faculty_forbidden(self, faculty_client):
        resp = faculty_client.get('/cataloging')
        assert resp.status_code == 403

    def test_cataloging_librarian_allowed(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = SAMPLE_BOOKS
        resp = librarian_client.get('/cataloging')
        assert resp.status_code == 200
        assert b'Cataloging' in resp.data

    def test_cataloging_admin_allowed(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = SAMPLE_BOOKS
        resp = admin_client.get('/cataloging')
        assert resp.status_code == 200
        assert b'Cataloging' in resp.data

    def test_cataloging_unauthenticated_redirects(self, client):
        resp = client.get('/cataloging')
        assert resp.status_code == 302
        assert '/login' in resp.location


class TestCatalogingCRUD:
    def test_add_book_success(self, librarian_client, mock_db):
        mock_db['execute'].return_value = 1
        resp = librarian_client.post('/cataloging/add', data={
            'title': 'New Book',
            'author': 'New Author',
            'isbn': '978-1234567890',
            'material_type': 'Book',
            'year_published': '2024',
        })
        assert resp.status_code == 302
        assert '/cataloging' in resp.location
        assert mock_db['execute'].call_count >= 1
        call_args = mock_db['execute'].call_args_list[0]
        assert 'INSERT INTO book_catalog' in call_args[0][0]

    def test_add_book_missing_title(self, librarian_client, mock_db):
        resp = librarian_client.post('/cataloging/add', data={
            'title': '',
            'author': 'Some Author',
        })
        assert resp.status_code == 302

    def test_add_book_missing_author(self, librarian_client, mock_db):
        resp = librarian_client.post('/cataloging/add', data={
            'title': 'Some Title',
            'author': '',
        })
        assert resp.status_code == 302

    def test_edit_book_success(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = SAMPLE_BOOKS[0]
        mock_db['execute'].return_value = 1
        resp = librarian_client.post('/cataloging/1/edit', data={
            'title': 'Updated Title',
            'author': 'Updated Author',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count >= 1
        call_args = mock_db['execute'].call_args_list[0]
        assert 'UPDATE book_catalog' in call_args[0][0]

    def test_edit_book_not_found(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = None
        resp = librarian_client.post('/cataloging/999/edit', data={
            'title': 'Ghost',
            'author': 'Ghost',
        })
        assert resp.status_code == 302
        assert '/cataloging' in resp.location

    def test_toggle_book_status_archive(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = SAMPLE_BOOKS[0]
        mock_db['execute'].return_value = 1
        resp = librarian_client.post('/cataloging/1/status')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count >= 1
        call_args = mock_db['execute'].call_args_list[0]
        assert 'UPDATE book_catalog' in call_args[0][0]
        assert 'archived' in call_args[0][1]

    def test_toggle_book_status_not_found(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = None
        resp = librarian_client.post('/cataloging/999/status')
        assert resp.status_code == 302

    def test_add_accession_success(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [SAMPLE_BOOKS[0], None]
        mock_db['execute'].return_value = 1
        resp = librarian_client.post('/cataloging/1/accession/add', data={
            'accession_number': '2025-0001',
            'copy_number': '1',
            'source': 'purchase',
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count >= 1
        call_args = mock_db['execute'].call_args_list[0]
        assert 'INSERT INTO accession_log' in call_args[0][0]

    def test_add_accession_duplicate(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [SAMPLE_BOOKS[0], ('2025-0001',)]
        mock_db['execute'].return_value = 1
        resp = librarian_client.post('/cataloging/1/accession/add', data={
            'accession_number': '2025-0001',
        })
        assert resp.status_code == 302

    def test_add_accession_missing_number(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = SAMPLE_BOOKS[0]
        resp = librarian_client.post('/cataloging/1/accession/add', data={
            'accession_number': '',
        })
        assert resp.status_code == 302


class TestCatalogingSearch:
    def test_search_by_title(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = [SAMPLE_BOOKS[0]]
        mock_db['fetch_one'].return_value = (1,)
        resp = librarian_client.get('/cataloging?q=Algorithms&field=title')
        assert resp.status_code == 200
        assert b'Algorithms' in resp.data

    def test_search_by_author(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = [SAMPLE_BOOKS[1]]
        mock_db['fetch_one'].return_value = (1,)
        resp = librarian_client.get('/cataloging?q=Martin&field=author')
        assert resp.status_code == 200

    def test_search_no_results(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = []
        mock_db['fetch_one'].return_value = (0,)
        resp = librarian_client.get('/cataloging?q=zzzxxx')
        assert resp.status_code == 200

    def test_pagination(self, librarian_client, mock_db):
        mock_db['fetch_all'].return_value = SAMPLE_BOOKS
        mock_db['fetch_one'].return_value = (3,)
        resp = librarian_client.get('/cataloging?page=1')
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
            (1, '2025-0001', 1, 1, 4, '2025-01-10', 'purchase'),
        ]
        resp = client.get('/book/1')
        assert resp.status_code == 200
        assert b'2025-0001' in resp.data


def _csv_file(content, filename='books.csv'):
    """Build a Werkzeug FileStorage-like upload from a CSV string."""
    return (io.BytesIO(content.encode('utf-8')), filename)


class TestBulkImport:
    """Bulk CSV import: header detection, encoding, validation, RBAC, edge cases."""

    VALID_ROW = ('Book A', 'Author A', '978-1', '1st', 'Pub A', 2023,
                 'CS', 'QA100', 'Book', 'Desc A')

    @staticmethod
    def _make_csv(rows, headers=None):
        if headers is None:
            headers = ['title', 'author', 'isbn', 'edition', 'publisher',
                       'year', 'subject', 'call_number', 'material_type', 'description']
        out = io.StringIO()
        w = csv.writer(out)
        w.writerow(headers)
        for r in rows:
            w.writerow(r)
        return out.getvalue()

    def test_bulk_import_rbac_student(self, student_client):
        resp = student_client.post('/cataloging/bulk-import', data={
            'file': _csv_file(self._make_csv([self.VALID_ROW])),
        })
        assert resp.status_code == 403

    def test_bulk_import_rbac_faculty(self, faculty_client):
        resp = faculty_client.post('/cataloging/bulk-import', data={
            'file': _csv_file(self._make_csv([self.VALID_ROW])),
        })
        assert resp.status_code == 403

    def test_bulk_import_unauthenticated(self, client):
        resp = client.post('/cataloging/bulk-import', data={
            'file': _csv_file(self._make_csv([self.VALID_ROW])),
        })
        assert resp.status_code == 302
        assert '/login' in resp.location

    def test_bulk_import_no_file(self, librarian_client):
        resp = librarian_client.post('/cataloging/bulk-import')
        assert resp.status_code == 302
        assert '/cataloging' in resp.location

    def test_bulk_import_empty_filename(self, librarian_client):
        resp = librarian_client.post('/cataloging/bulk-import', data={
            'file': (io.BytesIO(b''), ''),
        })
        assert resp.status_code == 302
        assert '/cataloging' in resp.location

    def test_bulk_import_wrong_extension(self, librarian_client):
        resp = librarian_client.post('/cataloging/bulk-import', data={
            'file': (io.BytesIO(b'a,b,c'), 'books.txt'),
        })
        assert resp.status_code == 302
        assert '/cataloging' in resp.location

    def test_bulk_import_empty_file(self, librarian_client, mock_db):
        resp = librarian_client.post('/cataloging/bulk-import', data={
            'file': _csv_file(''),
        })
        assert resp.status_code == 302
        assert '/cataloging' in resp.location

    def test_bulk_import_headers_only(self, librarian_client, mock_db):
        resp = librarian_client.post('/cataloging/bulk-import', data={
            'file': _csv_file('title,author,year\n'),
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 1  # log_activity only

    def test_bulk_import_missing_required_columns(self, librarian_client, mock_db):
        resp = librarian_client.post('/cataloging/bulk-import', data={
            'file': _csv_file(self._make_csv([('NoAuthor',)], headers=['title'])),
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_bulk_import_success(self, librarian_client, mock_db):
        mock_db['execute'].return_value = 1
        csv_content = self._make_csv([
            ('Title One', 'Author One', '978-111', '2nd', 'Pub1', 2020,
             'Science', 'Q1', 'Book', 'First book'),
            ('Title Two', 'Author Two', '978-222', '', 'Pub2', 2021,
             'Math', 'Q2', 'Book', ''),
        ])
        resp = librarian_client.post('/cataloging/bulk-import', data={
            'file': _csv_file(csv_content),
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count >= 2
        calls = mock_db['execute'].call_args_list
        for call in calls[:2]:
            assert 'INSERT INTO book_catalog' in call[0][0]

    def test_bulk_import_headers_random_order(self, librarian_client, mock_db):
        mock_db['execute'].return_value = 1
        csv_content = self._make_csv(
            [('Author X', 'Title X', '2022', '978-333')],
            headers=['author', 'title', 'year', 'isbn'],
        )
        resp = librarian_client.post('/cataloging/bulk-import', data={
            'file': _csv_file(csv_content),
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count >= 1
        call = mock_db['execute'].call_args_list[0]
        assert b'Title X' in call[0][1][0].encode() if isinstance(call[0][1][0], str) else \
            'Title X' in call[0][1][0]

    def test_bulk_import_header_synonyms(self, librarian_client, mock_db):
        mock_db['execute'].return_value = 1
        csv_content = self._make_csv(
            [('Synonym Book', 'Synonym Author')],
            headers=['Book Title', 'Author(s)'],
        )
        resp = librarian_client.post('/cataloging/bulk-import', data={
            'file': _csv_file(csv_content),
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count >= 1

    def test_bulk_import_partial_errors(self, librarian_client, mock_db):
        mock_db['execute'].return_value = 1
        csv_content = self._make_csv([
            ('Valid Title', 'Valid Author', '978-555'),
            ('', 'NoTitleAuthor', ''),
            ('OnlyTitle', '', ''),
            ('Another Valid', 'Another Author', '978-666'),
        ])
        resp = librarian_client.post('/cataloging/bulk-import', data={
            'file': _csv_file(csv_content),
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 3  # 2 books + 1 log_activity
        first_call = mock_db['execute'].call_args_list[0]
        assert 'INSERT INTO book_catalog' in first_call[0][0]

    def test_bulk_import_utf8_bom(self, librarian_client, mock_db):
        mock_db['execute'].return_value = 1
        csv_content = self._make_csv([('BOM Book', 'BOM Author')])
        resp = librarian_client.post('/cataloging/bulk-import', data={
            'file': (io.BytesIO(csv_content.encode('utf-8-sig')), 'books.csv'),
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count >= 1

    def test_bulk_import_latin1_encoding(self, librarian_client, mock_db):
        mock_db['execute'].return_value = 1
        csv_content = self._make_csv([('José García', 'François')],
                                     headers=['title', 'author'])
        resp = librarian_client.post('/cataloging/bulk-import', data={
            'file': (io.BytesIO(csv_content.encode('latin-1')), 'books.csv'),
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count >= 1

    def test_bulk_import_unicode_titles(self, librarian_client, mock_db):
        mock_db['execute'].return_value = 1
        csv_content = self._make_csv([
            ('日本語の本', '著者名'),
            ('Русская книга', 'Автор'),
            ('中文图书', '作者'),
        ])
        resp = librarian_client.post('/cataloging/bulk-import', data={
            'file': _csv_file(csv_content),
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 4  # 3 books + 1 log_activity

    def test_bulk_import_no_headers(self, librarian_client, mock_db):
        csv_content = 'value1,value2,value3'
        resp = librarian_client.post('/cataloging/bulk-import', data={
            'file': _csv_file(csv_content),
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_bulk_import_whitespace_headers(self, librarian_client, mock_db):
        mock_db['execute'].return_value = 1
        csv_content = self._make_csv(
            [('Whitespace Book', 'Whitespace Author')],
            headers=['  title  ', '  author  '],
        )
        resp = librarian_client.post('/cataloging/bulk-import', data={
            'file': _csv_file(csv_content),
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 2  # 1 book + 1 log_activity

    def test_bulk_import_large_file(self, librarian_client, mock_db):
        mock_db['execute'].return_value = 1
        rows = [(f'Book {i}', f'Author {i}', f'978-{i:06d}') for i in range(500)]
        csv_content = self._make_csv(rows, headers=['title', 'author', 'isbn'])
        resp = librarian_client.post('/cataloging/bulk-import', data={
            'file': _csv_file(csv_content),
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 501  # 500 books + 1 log_activity

    def test_bulk_import_extra_unknown_headers(self, librarian_client, mock_db):
        mock_db['execute'].return_value = 1
        csv_content = self._make_csv(
            [('Extra Book', 'Extra Author', 'ShelfA', 'Donated')],
            headers=['title', 'author', 'location', 'source'],
        )
        resp = librarian_client.post('/cataloging/bulk-import', data={
            'file': _csv_file(csv_content),
        })
        assert resp.status_code == 302
        assert mock_db['execute'].call_count >= 1
