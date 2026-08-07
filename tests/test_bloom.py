import pytest

from app.bloom import BloomFilter, optimal_params
from app.bloom_registry import bloom_registry, record_key

BOOK_ROWS = [
    ('The Great Gatsby', 'F. Scott Fitzgerald', '9780743273565'),
    ('To Kill a Mockingbird', 'Harper Lee', '9780061120084'),
    ('A Book Without Isbn', 'Anonymous', ''),
]
ID_ROWS = [('2024-8192',), ('2024-0001',)]


def _mock_fetch_all_by_query(mock_db):
    def side_effect(query, params=None):
        if 'FROM book_catalog WHERE title IS NOT NULL' in query:
            return BOOK_ROWS
        if 'FROM borrowers WHERE id_number IS NOT NULL' in query:
            return ID_ROWS
        return []
    mock_db['fetch_all'].side_effect = side_effect


@pytest.fixture(autouse=True)
def _fresh_bloom_registry():
    bloom_registry.mark_dirty()
    yield


class TestBloomFilter:
    def test_contains_added_values(self):
        bf = BloomFilter(10)
        bf.add('The Great Gatsby')
        bf.add('Harper Lee')
        assert 'The Great Gatsby' in bf
        assert 'harper lee' in bf  # case normalization

    def test_absent_value_reported_not_present(self):
        bf = BloomFilter(10)
        for value in ('Alpha', 'Beta', 'Gamma'):
            bf.add(value)
        assert 'Not-In-This-Set-12345' not in bf

    def test_payload_roundtrip(self):
        bf = BloomFilter(10)
        for value in ('one', 'two', 'three'):
            bf.add(value)
        payload = bf.to_payload()
        restored = BloomFilter.from_payload(payload['m'], payload['k'], payload['bits'])
        for value in ('one', 'two', 'three'):
            assert value in restored

    def test_optimal_params_byte_aligned(self):
        m, k = optimal_params(1000)
        assert m % 8 == 0
        assert k >= 1
        assert optimal_params(0) == (64, 1)


class TestRecordKey:
    def test_key_normalizes(self):
        assert record_key('  The Great Gatsby ', ' F. Scott Fitzgerald ', '9780743273565') == \
            record_key('the great gatsby', 'f. scott fitzgerald', '9780743273565')

    def test_blank_isbn_matches_blank(self):
        assert record_key('Title', 'Author', '') == record_key('title', 'author', None)


class TestBloomApi:
    def test_endpoint_returns_record_filters(self, client, mock_db):
        _mock_fetch_all_by_query(mock_db)
        resp = client.get('/api/bloom')
        assert resp.status_code == 200
        data = resp.get_json()
        for key in ('book_record', 'student_record'):
            assert key in data
            assert 'm' in data[key] and 'k' in data[key] and 'bits' in data[key]

    def test_book_record_reflects_db(self, client, mock_db):
        _mock_fetch_all_by_query(mock_db)
        data = client.get('/api/bloom').get_json()
        book_bf = BloomFilter.from_payload(**data['book_record'])
        assert record_key('The Great Gatsby', 'F. Scott Fitzgerald', '9780743273565') in book_bf
        assert record_key('A Book Without Isbn', 'Anonymous', '') in book_bf
        assert record_key('Never Written', 'Nobody', '0000000000000') not in book_bf

    def test_student_record_reflects_db(self, client, mock_db):
        _mock_fetch_all_by_query(mock_db)
        data = client.get('/api/bloom').get_json()
        student_bf = BloomFilter.from_payload(**data['student_record'])
        assert '2024-8192' in student_bf
        assert '2024-0001' in student_bf
        assert '9999-9999' not in student_bf

    def test_rebuild_after_mark_dirty(self, client, mock_db):
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
