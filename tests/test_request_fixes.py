"""Regression tests for POST /user/request-book fixes (mocked DB).

1. Punctuation-only titles ("!!!") normalize to "" -> rejected, no write.
2. Rejected prior rows no longer block re-request (check_duplicate_request
   is scoped to open statuses); pending rows still block.
3. Double-submit race: UniqueViolation from create_request -> 302, no 500.
4. Boundary 255/150 lengths still accepted.
"""

from unittest.mock import patch

from psycopg2 import errors as pg_errors

from app.requests.models import check_duplicate_request


def _request_inserts(mock_db):
    return [c for c in mock_db['execute'].call_args_list
            if 'INSERT INTO request_records' in c[0][0]]


def _flashes(student_client):
    with student_client.session_transaction() as sess:
        return sess.get('_flashes', []) or []


class TestPunctuationOnlyTitle:
    def test_punctuation_only_rejected_no_insert(self, student_client, mock_db):
        """Validates punctuation only rejected no insert `/user/request-book` as student (expects 302) [TestPunctuationOnlyTitle / request fixes].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates request/procurement workflow is broken."""
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].return_value = []
        mock_db['execute'].return_value = [(7,)]

        resp = student_client.post('/user/request-book',
                                   data={'book-title': '!!!', 'author': ''})

        assert resp.status_code == 302
        assert '/user/request-book' in resp.location
        assert _request_inserts(mock_db) == []
        assert mock_db['execute'].call_count == 0
        assert any('Book title is required.' in msg
                   for _cat, msg in _flashes(student_client))


class TestRejectedRerequest:
    def test_duplicate_check_scoped_to_open_statuses(self, mock_db):
        """Validates duplicate check scoped to open statuses [TestRejectedRerequest / request fixes].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates request/procurement workflow is broken."""
        mock_db['fetch_all'].return_value = []
        assert check_duplicate_request(5, 'Clean Code') is False
        sql = mock_db['fetch_all'].call_args[0][0]
        assert 'request_status' in sql
        assert 'pending_review' in sql
        assert 'approved' in sql

    def test_rejected_prior_row_allows_rerequest(self, student_client, mock_db):
        # The rejected row is filtered by the DB (status-scoped query),
        # so the duplicate check sees no open rows -> one INSERT.
        """Validates rejected prior row allows rerequest `/user/request-book` as student (expects 302) [TestRejectedRerequest / request fixes].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates request/procurement workflow is broken."""
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].side_effect = [[], [], []]
        mock_db['execute'].return_value = [(7,)]

        resp = student_client.post('/user/request-book',
                                   data={'book-title': 'Clean Code',
                                         'author': 'Martin'})

        assert resp.status_code == 302
        assert len(_request_inserts(mock_db)) == 1

    def test_pending_prior_row_still_blocks(self, student_client, mock_db):
        """Validates pending prior row still blocks `/user/request-book` as student (expects 302) [TestRejectedRerequest / request fixes].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates request/procurement workflow is broken."""
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].return_value = [('Clean Code',)]

        resp = student_client.post('/user/request-book',
                                   data={'book-title': 'Clean Code'})

        assert resp.status_code == 302
        assert _request_inserts(mock_db) == []


class TestDoubleSubmitRace:
    def test_unique_violation_returns_302(self, student_client, mock_db):
        """Validates unique violation returns 302 `/user/request-book` as student (expects 302) [TestDoubleSubmitRace / request fixes].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates request/procurement workflow is broken."""
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].return_value = []

        with patch('app.requests.routes.create_request',
                   side_effect=pg_errors.UniqueViolation('duplicate')):
            resp = student_client.post('/user/request-book',
                                       data={'book-title': 'Clean Code'})

        assert resp.status_code == 302
        assert '/user/request-book' in resp.location
        assert _request_inserts(mock_db) == []
        assert any('Already submitted' in msg
                   for _cat, msg in _flashes(student_client))

    def test_non_unique_error_still_raises(self, student_client, mock_db):
        """Validates non unique error still raises `/user/request-book` as student [TestDoubleSubmitRace / request fixes].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates request/procurement workflow is broken."""
        import pytest

        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].return_value = []

        with patch('app.requests.routes.create_request',
                   side_effect=RuntimeError('boom')):
            with pytest.raises(RuntimeError):
                student_client.post('/user/request-book',
                                    data={'book-title': 'Clean Code'})


class TestBoundaryLengths:
    def test_boundary_255_150_accepted(self, student_client, mock_db):
        """Validates boundary 255 150 accepted `/user/request-book` as student (expects 302) [TestBoundaryLengths / request fixes].
    If fails: likely wrong/absent SQL call or placeholder mismatch.
    Failure indicates request/procurement workflow is broken."""
        mock_db['fetch_one'].return_value = (5,)
        mock_db['fetch_all'].side_effect = [[], [], []]
        mock_db['execute'].return_value = [(9,)]

        resp = student_client.post('/user/request-book',
                                   data={'book-title': 'T' * 255,
                                         'author': 'A' * 150})

        assert resp.status_code == 302
        assert len(_request_inserts(mock_db)) == 1


class TestReviewPendingGuards:
    """Confirm review_request/bulk_review already skip non-pending rows."""

    def test_single_double_approval_skipped(self, librarian_client, mock_db):
        """Validates single double approval skipped `/librarian/requests/7/approve` as librarian (expects 302) [TestReviewPendingGuards / request fixes].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates request/procurement workflow is broken."""
        mock_db['fetch_one'].return_value = (
            7, 1, 'Some Book', None, None, 'approved', None, None, None, None)
        resp = librarian_client.post('/librarian/requests/7/approve')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_bulk_double_approval_skipped(self, librarian_client, mock_db):
        """Validates bulk double approval skipped `/librarian/requests/bulk/approve` as librarian (expects 302) [TestReviewPendingGuards / request fixes].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (UPDATE).
    Failure indicates request/procurement workflow is broken."""
        mock_db['fetch_one'].side_effect = [
            (7, 1, 'Book A', None, None, 'approved', None, None, None, None),
        ]
        resp = librarian_client.post('/librarian/requests/bulk/approve',
                                     data={'request_ids': '7'})
        assert resp.status_code == 302
        updates = [c for c in mock_db['execute'].call_args_list
                   if 'UPDATE request_records' in c[0][0]]
        assert updates == []
