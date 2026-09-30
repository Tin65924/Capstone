"""Tests for the Requests module: submission, review, RBAC."""

import re

from app.requests.models import normalize_title, check_duplicate_request


class TestTitleNormalization:
    def test_normalize_lowercases(self):
        assert normalize_title('HARRY POTTER') == 'harry potter'

    def test_normalize_strips_punctuation(self):
        assert normalize_title("David Jone's Locker!") == 'david jones locker'

    def test_normalize_expands_abbreviations(self):
        assert normalize_title('Intro to Comp Sci') == 'introduction to computer science'

    def test_normalize_collapses_whitespace(self):
        assert normalize_title('Harry   Potter') == 'harry potter'


class TestCheckDuplicateRequest:
    def test_exact_normalized_duplicate_blocked(self, mock_db):
        mock_db['fetch_all'].return_value = [('1984',)]
        assert check_duplicate_request(5, '1984') is True

    def test_fuzzy_duplicate_blocked(self, mock_db):
        mock_db['fetch_all'].return_value = [('Introduction to Programming',)]
        assert check_duplicate_request(5, 'Intro to Programming') is True

    def test_distinct_titles_allowed(self, mock_db):
        mock_db['fetch_all'].return_value = [('Introduction to Biology',)]
        assert check_duplicate_request(5, 'Introduction to Programming') is False

    def test_no_prior_requests_allowed(self, mock_db):
        mock_db['fetch_all'].return_value = []
        assert check_duplicate_request(5, 'Anything') is False


class TestCountRequestsByStatus:
    def test_returns_status_map(self, mock_db):
        from app.requests.models import count_requests_by_status
        mock_db['fetch_all'].return_value = [('pending_review', 3), ('approved', 1)]
        assert count_requests_by_status() == {'pending_review': 3, 'approved': 1}
        assert 'GROUP BY request_status' in mock_db['fetch_all'].call_args[0][0]

    def test_empty_table_returns_empty_map(self, mock_db):
        from app.requests.models import count_requests_by_status
        mock_db['fetch_all'].return_value = []
        assert count_requests_by_status() == {}


class TestRequestSubmission:
    def test_student_submits_request_success(self, student_client, mock_db):
        mock_db['fetch_one'].side_effect = [
            (5,),   # 1st call: get_borrower_by_user -> borrower_id
            None,   # 2nd call: check_duplicate_request -> no duplicate found
        ]
        mock_db['execute'].return_value = [(7,)]

        resp = student_client.post('/user/request-book', data={
            'book-title': 'Introduction to Algorithms',
            'author': 'Cormen',
        })

        assert resp.status_code == 302
        assert '/user/request-book' in resp.location

        call_args = mock_db['execute'].call_args_list[0]
        assert 'INSERT INTO request_records' in call_args[0][0]
        assert 'pending_review' in call_args[0][1]

    def test_submit_blank_title_rejected(self, student_client, mock_db):
        mock_db['fetch_one'].return_value = (5,)

        resp = student_client.post('/user/request-book', data={
            'book-title': '',
            'author': '',
        })

        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_unauthenticated_redirects_to_login(self, client):
        resp = client.get('/user/request-book')
        assert resp.status_code == 302
        assert '/login' in resp.location


class TestLibrarianReview:
    def test_librarian_approves_request(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (7, 1, 'Some Book', None, None, 'pending_review', None, None, None, None)

        resp = librarian_client.post('/librarian/requests/7/approve')

        assert resp.status_code == 302
        assert '/librarian/requests' in resp.location
        assert mock_db['execute'].call_count >= 2

        call_args = mock_db['execute'].call_args_list[0]
        assert 'UPDATE request_records' in call_args[0][0]

    def test_librarian_rejects_request_with_remarks(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (7, 1, 'Some Book', None, None, 'pending_review', None, None, None, None)

        resp = librarian_client.post('/librarian/requests/7/reject', data={
            'remarks': 'Not relevant to curriculum',
        })

        assert resp.status_code == 302
        call_args = mock_db['execute'].call_args_list[0]
        assert 'UPDATE request_records' in call_args[0][0]
        assert 'Not relevant to curriculum' in call_args[0][1]

    def test_student_forbidden_from_librarian_requests(self, student_client):
        resp = student_client.get('/librarian/requests')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_invalid_action_rejected(self, librarian_client, mock_db):
        resp = librarian_client.post('/librarian/requests/7/nonsense')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_cannot_approve_already_reviewed_request(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = (7, 1, 'Some Book', None, None, 'approved', None, None, None, None)

        resp = librarian_client.post('/librarian/requests/7/approve')

        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_request_not_found_returns_error(self, librarian_client, mock_db):
        mock_db['fetch_one'].return_value = None

        resp = librarian_client.post('/librarian/requests/999/approve')

        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0


class TestStackedChartGrouping:
    def test_typo_variants_merge_into_one_bar(self):
        from app.requests.models import build_stacked_chart
        rows = [
            ('Introductin to Computing', 'Student', 1),
            ('Introduction to Computing', 'Faculty', 1),
        ]
        chart = build_stacked_chart(rows)
        assert len(chart) == 1
        display, student, faculty, other, total = chart[0]
        assert total == 2
        assert student == 1
        assert faculty == 1
        assert other == 0

    def test_staff_roles_fold_into_other(self):
        from app.requests.models import build_stacked_chart
        rows = [('Mathematics', 'Admin', 1)]
        chart = build_stacked_chart(rows)
        assert len(chart) == 1
        display, student, faculty, other, total = chart[0]
        assert total == 1
        assert student == 0
        assert faculty == 0
        assert other == 1

    def test_abbreviation_variants_merge(self):
        from app.requests.models import build_stacked_chart
        rows = [
            ('Intro to Programming', 'Student', 2),
            ('Introduction to Programming', 'Faculty', 1),
        ]
        chart = build_stacked_chart(rows)
        assert len(chart) == 1
        assert chart[0][4] == 3

    def test_distinct_titles_stay_separate_and_sorted(self):
        from app.requests.models import build_stacked_chart
        rows = [
            ('Biology Basics', 'Student', 1),
            ('Chemistry Basics', 'Student', 3),
        ]
        chart = build_stacked_chart(rows)
        assert len(chart) == 2
        assert chart[0][0] == 'Chemistry Basics'
        assert chart[0][4] == 3

    def test_variant_lookup_maps_typo_to_group(self):
        from app.requests.models import build_variant_lookup
        rows = [
            ('Introductin to Computing', 'Student', 1),
            ('Introduction to Computing', 'Faculty', 1),
        ]
        lookup = build_variant_lookup(rows)
        assert lookup['Introductin to Computing'] is lookup['Introduction to Computing']
        assert lookup['Introductin to Computing']['total'] == 2


def _details_row(rid, title, name, role, dept, status='pending_review', day='05'):
    return (rid, rid + 100, title, '', None, status, f'2026-01-{day}',
            None, None, None, name, role, dept)


class TestListRendering:
    def test_list_shows_individual_cards_without_overview(self, librarian_client, mock_db):
        mock_db['fetch_all'].side_effect = [
            [_details_row(1, 'Introductin to Computing', 'Student A', 'Student', 'BSIS'),
             _details_row(2, 'Introduction to Computing', 'Faculty B', 'Faculty', 'Computing', day='06')],
            [('pending_review', 1), ('approved', 1)],
            [('Introductin to Computing', 'Student', 1),
             ('Introduction to Computing', 'Faculty', 1)],
        ]
        mock_db['fetch_one'].return_value = (2,)

        resp = librarian_client.get('/librarian/requests')

        assert resp.status_code == 200
        body = resp.data.decode()
        assert 'Demand Overview' not in body
        # All five headline stat cards render as filter links.
        for label in ('Total Requests', 'Pending Review', 'Approved', 'Rejected', 'Procured'):
            assert label in body
        hrefs = re.findall(r'href="([^"]*status=[^"]*)"', body)
        statuses = set()
        for h in hrefs:
            m = re.search(r'status=([a-z_]+)', h)
            if m:
                statuses.add(m.group(1))
        assert {'all', 'pending_review', 'approved', 'rejected', 'procured'} <= statuses
        # Default view is Pending, so its card carries the active highlight.
        assert 'ring-primary' in body
        # Original individual cards: one Approve/Reject pair per request row.
        assert body.count('reject-form-1') >= 1
        assert body.count('reject-form-2') >= 1
        assert 'Approve all' not in body

    def test_sort_param_accepted(self, librarian_client, mock_db):
        mock_db['fetch_all'].side_effect = [[], [], []]
        mock_db['fetch_one'].return_value = (0,)

        resp = librarian_client.get('/librarian/requests?sort=recent')

        assert resp.status_code == 200


class TestBulkReview:
    def test_bulk_approve_all_pending(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [
            (7, 1, 'Book A', None, None, 'pending_review', None, None, None, None),
            (9, 2, 'Book A', None, None, 'pending_review', None, None, None, None),
            (2,),  # count_requests (unused here, defensive)
        ]

        resp = librarian_client.post('/librarian/requests/bulk/approve',
                                     data={'request_ids': '7,9'})

        assert resp.status_code == 302
        assert '/librarian/requests' in resp.location
        updates = [c for c in mock_db['execute'].call_args_list
                   if 'UPDATE request_records' in c[0][0]]
        assert len(updates) == 2
        procurements = [c for c in mock_db['execute'].call_args_list
                        if 'INSERT INTO procurement_log' in c[0][0]]
        assert len(procurements) == 2

    def test_bulk_reject_skips_reviewed(self, librarian_client, mock_db):
        mock_db['fetch_one'].side_effect = [
            (7, 1, 'Book A', None, None, 'pending_review', None, None, None, None),
            (9, 2, 'Book A', None, None, 'approved', None, None, None, None),
        ]

        resp = librarian_client.post('/librarian/requests/bulk/reject',
                                     data={'request_ids': '7,9', 'remarks': 'Dup'})

        assert resp.status_code == 302
        updates = [c for c in mock_db['execute'].call_args_list
                   if 'UPDATE request_records' in c[0][0]]
        assert len(updates) == 1
        assert 'Dup' in updates[0][0][1]

    def test_bulk_invalid_action_rejected(self, librarian_client, mock_db):
        resp = librarian_client.post('/librarian/requests/bulk/nonsense',
                                     data={'request_ids': '7'})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_bulk_no_ids_rejected(self, librarian_client, mock_db):
        resp = librarian_client.post('/librarian/requests/bulk/approve', data={})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_bulk_student_forbidden(self, student_client, mock_db):
        resp = student_client.post('/librarian/requests/bulk/approve',
                                   data={'request_ids': '7'})
        assert resp.status_code == 302
        assert '/user/profile' in resp.location
        # The RBAC decorator logs security:denied, but no request rows change.
        updates = [c for c in mock_db['execute'].call_args_list
                   if 'UPDATE request_records' in c[0][0]]
        assert updates == []