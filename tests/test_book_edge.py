"""Edge-case regression tests for the Book Detail page (/book/<id>).

Covers rendering across roles and availability states (available,
all-borrowed, user-has-book, zero copies, archived, short rows),
XSS in every catalog field, borrow/reserve server guards (bad types,
missing/archived books, no borrower, duplicates, limits, bad or missing
copies), and auth behavior. Includes the archived-state UI (badge,
disabled actions, honest messaging) and the zero-copy message fix.
Everything must degrade gracefully — never 500, never raw HTML injection.
"""

BOOK = (1, 'Clean Code', 'R. Martin', '1st', 'Pub', 2008, 'SE', 'C1',
        '978', 'Book', 'Desc', 'active', '2026-01-01', None, None)
ARCHIVED = (2, 'Old', 'A', '', '', None, '', '', '', '', '', 'archived',
            '2026-01-01', None, None)
ACC = (10, 'ACC-001', 1, 'purchase', '2026-01-02', None, None, None)
BORROWER = (5, 1, 'S1', 'BSIS', 'active', None, None, None)


def _detail_mocks(mock_db, book=BOOK, accessions=(ACC,), loans=(),
                  loan_rows=None, blocked=None):
    """Wire fetch mocks in book_info call order."""
    # fetch_one: book, then daily-block check (only when a copy is free;
    # extra values are harmless when the check is skipped).
    mock_db['fetch_one'].side_effect = [book, blocked]
    alls = [list(accessions), list(loans),
            loan_rows if loan_rows is not None else []]
    # Models iterate fetch_all directly except the map helpers (now guarded).
    mock_db['fetch_all'].side_effect = alls


class TestDetailRendering:
    def test_zero_and_huge_ids(self, client, mock_db):
        """Validates zero and huge ids (expects 302) [TestDetailRendering / book edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = None
        for url in ('/book/0', '/book/999999999'):
            resp = client.get(url)
            assert resp.status_code == 302, url
            assert '/catalog' in resp.location

    def test_archived_renders(self, client, mock_db):
        """Validates archived renders `/book/2` [TestDetailRendering / book edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates catalog data or listing/sort is wrong."""
        _detail_mocks(mock_db, book=ARCHIVED)
        body = client.get('/book/2').data.decode()
        assert 'Archived' in body
        assert 'cannot be borrowed or reserved' in body

    def test_no_accessions(self, client, mock_db):
        """Validates no accessions `/book/1` [TestDetailRendering / book edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates catalog data or listing/sort is wrong."""
        _detail_mocks(mock_db, accessions=())
        body = client.get('/book/1').data.decode()
        assert 'Not Available' in body

    def test_none_accessions(self, client, mock_db):
        """Validates none accessions `/book/1` (expects 200) [TestDetailRendering / book edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = BOOK
        mock_db['fetch_all'].return_value = None
        assert client.get('/book/1').status_code == 200

    def test_short_book_row(self, client, mock_db):
        """Validates short book row `/book/1` (expects 200) [TestDetailRendering / book edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = (1, 'T', 'A')
        mock_db['fetch_all'].return_value = []
        assert client.get('/book/1').status_code == 200

    def test_roles_matrix(self, client, student_client, faculty_client,
                          librarian_client, admin_client, mock_db):
        """Validates roles matrix `/book/1` (expects 200) [TestDetailRendering / book edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        _detail_mocks(mock_db)
        assert client.get('/book/1').status_code == 200
        for c in (student_client, faculty_client, librarian_client,
                  admin_client):
            mock_db['fetch_one'].side_effect = None
            mock_db['fetch_one'].return_value = BOOK
            mock_db['fetch_all'].side_effect = None
            mock_db['fetch_all'].return_value = []
            assert c.get('/book/1').status_code == 200

    def test_user_has_book_state(self, student_client, mock_db):
        """Validates user has book state `/book/1` as student [TestDetailRendering / book edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates catalog data or listing/sort is wrong."""
        _detail_mocks(mock_db, loan_rows=[(10, 1)])
        body = student_client.get('/book/1').data.decode()
        assert 'Borrowed</button>' in body

    def test_all_borrowed_state(self, student_client, mock_db):
        """Validates all borrowed state `/book/1` as student [TestDetailRendering / book edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates catalog data or listing/sort is wrong."""
        _detail_mocks(mock_db, loans=[(10,)])
        body = student_client.get('/book/1').data.decode()
        assert 'Not Available' in body


class TestDetailXss:
    FIELDS = ('title', 'author', 'edition', 'publisher', 'subject',
              'callno', 'isbn', 'desc')

    def test_evil_every_field(self, client, mock_db):
        """Validates evil every field `/book/1` [TestDetailXss / book edge cases].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates catalog data or listing/sort is wrong."""
        evil = '<script>alert(1)</script>'
        row = (1, evil, evil, evil, evil, 2020, evil, evil, evil, 'Book',
               evil, 'active', '2026-01-01', None, None)
        mock_db['fetch_one'].return_value = row
        mock_db['fetch_all'].return_value = []
        body = client.get('/book/1').data.decode()
        assert evil not in body

    def test_evil_accession_number(self, client, mock_db):
        """Validates evil accession number `/book/1` (expects 200) [TestDetailXss / book edge cases].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = BOOK
        acc = (10, '<img src=x>', 1, 'purchase', '2026-01-02', None, None)
        mock_db['fetch_all'].side_effect = [[acc], [], {}]
        assert client.get('/book/1').status_code == 200


class TestBorrowGuards:
    @staticmethod
    def _borrow_mocks(mock_db, book=BOOK, borrower=BORROWER, loan=None,
                      res=None, count=0, accessions=(ACC,)):
        """Test helper _borrow_mocks: build mocked data or DB stub for the test."""
        mock_db['fetch_one'].side_effect = [book, borrower, loan, res,
                                            (count,)]
        mock_db['fetch_all'].return_value = [list(accessions)]

    def test_bogus_borrow_type(self, student_client, mock_db):
        """Validates bogus borrow type `/user/borrow` as student (expects 302) [TestBorrowGuards / book edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = BOOK
        resp = student_client.post('/user/borrow',
                                   data={'book_id': 1,
                                         'borrow_type': 'forever'})
        assert resp.status_code == 302

    def test_borrow_missing_book(self, student_client, mock_db):
        """Validates borrow missing book `/user/borrow` as student (expects 302) [TestBorrowGuards / book edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = None
        resp = student_client.post('/user/borrow',
                                   data={'book_id': 999,
                                         'borrow_type': 'overnight'})
        assert resp.status_code == 302
        assert '/catalog' in resp.location

    def test_borrow_archived(self, student_client, mock_db):
        """Validates borrow archived `/user/borrow` as student (expects 302) [TestBorrowGuards / book edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates catalog data or listing/sort is wrong."""
        self._borrow_mocks(mock_db, book=ARCHIVED)
        resp = student_client.post('/user/borrow',
                                   data={'book_id': 2,
                                         'borrow_type': 'overnight'})
        assert resp.status_code == 302

    def test_borrow_no_borrower(self, admin_client, mock_db):
        """Validates borrow no borrower `/user/borrow` as admin (expects 302) [TestBorrowGuards / book edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].side_effect = [BOOK, None]
        resp = admin_client.post('/user/borrow',
                                 data={'book_id': 1,
                                       'borrow_type': 'overnight'})
        assert resp.status_code == 302

    def test_borrow_already_has(self, student_client, mock_db):
        """Validates borrow already has `/user/borrow` as student (expects 302) [TestBorrowGuards / book edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates catalog data or listing/sort is wrong."""
        self._borrow_mocks(mock_db, loan=(7,))
        resp = student_client.post('/user/borrow',
                                   data={'book_id': 1,
                                         'borrow_type': 'overnight'})
        assert resp.status_code == 302

    def test_borrow_over_limit(self, student_client, mock_db):
        """Validates borrow over limit `/user/borrow` as student (expects 302) [TestBorrowGuards / book edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates catalog data or listing/sort is wrong."""
        self._borrow_mocks(mock_db, count=99)
        resp = student_client.post('/user/borrow',
                                   data={'book_id': 1,
                                         'borrow_type': 'overnight'})
        assert resp.status_code == 302

    def test_borrow_accession_wrong_book(self, student_client, mock_db):
        """Validates borrow accession wrong book `/user/borrow` as student (expects 302) [TestBorrowGuards / book edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].side_effect = [BOOK, BORROWER, None, None,
                                            (0,), (99, 'X', 999)]
        mock_db['fetch_all'].return_value = []
        resp = student_client.post(
            '/user/borrow', data={'book_id': 1,
                                  'borrow_type': 'daily_circulation',
                                  'accession_id': 99})
        assert resp.status_code == 302

    def test_borrow_no_copies(self, student_client, mock_db):
        """Validates borrow no copies `/user/borrow` as student (expects 302) [TestBorrowGuards / book edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].side_effect = [BOOK, BORROWER, None, None,
                                            (0,), None]
        mock_db['fetch_all'].return_value = []
        resp = student_client.post(
            '/user/borrow', data={'book_id': 1,
                                  'borrow_type': 'daily_circulation'})
        assert resp.status_code == 302


class TestReserveGuards:
    @staticmethod
    def _res_mocks(mock_db, book=BOOK, borrower=BORROWER, res=None,
                   loan=None, avail=(ACC,)):
        """Test helper _res_mocks: build mocked data or DB stub for the test."""
        mock_db['fetch_one'].side_effect = [book, borrower, res, loan]
        mock_db['fetch_all'].return_value = [list(avail)]

    def test_reserve_archived(self, student_client, mock_db):
        """Validates reserve archived `/user/reserve` as student (expects 302) [TestReserveGuards / book edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates catalog data or listing/sort is wrong."""
        self._res_mocks(mock_db, book=ARCHIVED)
        assert student_client.post(
            '/user/reserve', data={'book_id': 2}).status_code == 302

    def test_reserve_duplicate(self, student_client, mock_db):
        """Validates reserve duplicate `/user/reserve` as student (expects 302) [TestReserveGuards / book edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates catalog data or listing/sort is wrong."""
        self._res_mocks(mock_db, res=(3,))
        assert student_client.post(
            '/user/reserve', data={'book_id': 1}).status_code == 302

    def test_reserve_when_available_refused(self, student_client, mock_db):
        """Validates reserve when available refused `/user/reserve` as student (expects 302) [TestReserveGuards / book edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates catalog data or listing/sort is wrong."""
        self._res_mocks(mock_db)
        assert student_client.post(
            '/user/reserve', data={'book_id': 1}).status_code == 302

    def test_reserve_no_borrower(self, admin_client, mock_db):
        """Validates reserve no borrower `/user/reserve` as admin (expects 302) [TestReserveGuards / book edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].side_effect = [BOOK, None]
        assert admin_client.post(
            '/user/reserve', data={'book_id': 1}).status_code == 302

    def test_reserve_missing_book(self, student_client, mock_db):
        """Validates reserve missing book `/user/reserve` as student (expects 302) [TestReserveGuards / book edge cases].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates catalog data or listing/sort is wrong."""
        mock_db['fetch_one'].return_value = None
        assert student_client.post(
            '/user/reserve', data={'book_id': 999}).status_code == 302
