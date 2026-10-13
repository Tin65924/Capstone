import pytest

from app.bloom import BloomFilter, optimal_params
from app.bloom_registry import bloom_registry, record_key, category_key

BOOK_ROWS = [
    ('The Great Gatsby', 'F. Scott Fitzgerald', '9780743273565'),
    ('To Kill a Mockingbird', 'Harper Lee', '9780061120084'),
    ('A Book Without Isbn', 'Anonymous', ''),
]
ID_ROWS = [('2024-8192',), ('2024-0001',)]
CAT_ROWS = [('Physics',), ('Computer Science',)]


def _mock_fetch_all_by_query(mock_db):
    def side_effect(query, params=None):
        if 'FROM book_catalog WHERE title IS NOT NULL' in query:
            return BOOK_ROWS
        if 'FROM borrowers WHERE id_number IS NOT NULL' in query:
            return ID_ROWS
        if 'subject_classification IS NOT NULL' in query:
            return CAT_ROWS
        return []
    mock_db['fetch_all'].side_effect = side_effect


@pytest.fixture(autouse=True)
def _fresh_bloom_registry():
    bloom_registry.mark_dirty()
    yield


class TestBloomFilter:
    def test_contains_added_values(self):
        """Validates contains added values [TestBloomFilter / bloom].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates Bloom autosuggest index is wrong (false negatives/positives)."""
        bf = BloomFilter(10)
        bf.add('The Great Gatsby')
        bf.add('Harper Lee')
        assert 'The Great Gatsby' in bf
        assert 'harper lee' in bf  # case normalization

    def test_absent_value_reported_not_present(self):
        """Validates absent value reported not present [TestBloomFilter / bloom].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates Bloom autosuggest index is wrong (false negatives/positives)."""
        bf = BloomFilter(10)
        for value in ('Alpha', 'Beta', 'Gamma'):
            bf.add(value)
        assert 'Not-In-This-Set-12345' not in bf

    def test_payload_roundtrip(self):
        """Validates payload roundtrip [TestBloomFilter / bloom].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates Bloom autosuggest index is wrong (false negatives/positives)."""
        bf = BloomFilter(10)
        for value in ('one', 'two', 'three'):
            bf.add(value)
        payload = bf.to_payload()
        restored = BloomFilter.from_payload(payload['m'], payload['k'], payload['bits'])
        for value in ('one', 'two', 'three'):
            assert value in restored

    def test_optimal_params_byte_aligned(self):
        """Validates optimal params byte aligned [TestBloomFilter / bloom].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates Bloom autosuggest index is wrong (false negatives/positives)."""
        m, k = optimal_params(1000)
        assert m % 8 == 0
        assert k >= 1
        assert optimal_params(0) == (64, 1)


class TestRecordKey:
    def test_key_normalizes(self):
        """Validates key normalizes [TestRecordKey / bloom].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates Bloom autosuggest index is wrong (false negatives/positives)."""
        assert record_key('  The Great Gatsby ', ' F. Scott Fitzgerald ', '9780743273565') == \
            record_key('the great gatsby', 'f. scott fitzgerald', '9780743273565')

    def test_blank_isbn_matches_blank(self):
        """Validates blank isbn matches blank [TestRecordKey / bloom].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates Bloom autosuggest index is wrong (false negatives/positives)."""
        assert record_key('Title', 'Author', '') == record_key('title', 'author', None)


class TestCategoryKey:
    def test_key_normalizes(self):
        """Validates key normalizes [TestCategoryKey / bloom].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates Bloom autosuggest index is wrong (false negatives/positives)."""
        assert category_key('  Physics ') == 'physics'
        assert category_key(None) == ''


class TestBloomApi:
    def test_endpoint_returns_record_filters(self, client, mock_db):
        """Validates endpoint returns record filters `/api/bloom` (expects 200) [TestBloomApi / bloom].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates Bloom autosuggest index is wrong (false negatives/positives)."""
        _mock_fetch_all_by_query(mock_db)
        resp = client.get('/api/bloom')
        assert resp.status_code == 200
        data = resp.get_json()
        for key in ('book_record', 'student_record', 'category_record'):
            assert key in data
            assert 'm' in data[key] and 'k' in data[key] and 'bits' in data[key]

    def test_book_record_reflects_db(self, client, mock_db):
        """Validates book record reflects db `/api/bloom` [TestBloomApi / bloom].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates Bloom autosuggest index is wrong (false negatives/positives)."""
        _mock_fetch_all_by_query(mock_db)
        data = client.get('/api/bloom').get_json()
        book_bf = BloomFilter.from_payload(**data['book_record'])
        assert record_key('The Great Gatsby', 'F. Scott Fitzgerald', '9780743273565') in book_bf
        assert record_key('A Book Without Isbn', 'Anonymous', '') in book_bf
        assert record_key('Never Written', 'Nobody', '0000000000000') not in book_bf

    def test_student_record_reflects_db(self, client, mock_db):
        """Validates student record reflects db `/api/bloom` [TestBloomApi / bloom].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates Bloom autosuggest index is wrong (false negatives/positives)."""
        _mock_fetch_all_by_query(mock_db)
        data = client.get('/api/bloom').get_json()
        student_bf = BloomFilter.from_payload(**data['student_record'])
        assert '2024-8192' in student_bf
        assert '2024-0001' in student_bf
        assert '9999-9999' not in student_bf

    def test_category_record_reflects_db(self, client, mock_db):
        """Validates category record reflects db `/api/bloom` [TestBloomApi / bloom].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates Bloom autosuggest index is wrong (false negatives/positives)."""
        _mock_fetch_all_by_query(mock_db)
        data = client.get('/api/bloom').get_json()
        cat_bf = BloomFilter.from_payload(**data['category_record'])
        assert 'physics' in cat_bf
        assert 'Physics' in cat_bf  # case normalization
        assert 'computer science' in cat_bf
        assert 'Never Taught 12345' not in cat_bf

    def test_rebuild_after_mark_dirty(self, client, mock_db):
        """Validates rebuild after mark dirty `/api/bloom` [TestBloomApi / bloom].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates Bloom autosuggest index is wrong (false negatives/positives)."""
        _mock_fetch_all_by_query(mock_db)
        client.get('/api/bloom')

        mock_db['fetch_all'].side_effect = lambda query, params=None: (
            [('2025-0001',)]
            if 'FROM borrowers WHERE id_number IS NOT NULL' in query else []
        )
        bloom_registry.mark_dirty()

        data = client.get('/api/bloom').get_json()
        student_bf = BloomFilter.from_payload(**data['student_record'])
        assert '2025-0001' in student_bf
