"""Tests for the Requests module: submission, review, RBAC."""

import re

from app.requests.models import normalize_title, check_duplicate_request


class TestTitleNormalization:
    def test_normalize_lowercases(self):
        """Validates normalize lowercases [TestTitleNormalization / requests].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates request/procurement workflow is broken."""
        assert normalize_title('HARRY POTTER') == 'harry potter'

    def test_normalize_strips_punctuation(self):
        """Validates normalize strips punctuation [TestTitleNormalization / requests].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates request/procurement workflow is broken."""
        assert normalize_title("David Jone's Locker!") == 'david jones locker'

    def test_normalize_expands_abbreviations(self):
        """Validates normalize expands abbreviations [TestTitleNormalization / requests].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates request/procurement workflow is broken."""
        assert normalize_title('Intro to Comp Sci') == 'introduction to computer science'

    def test_normalize_collapses_whitespace(self):
        """Validates normalize collapses whitespace [TestTitleNormalization / requests].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates request/procurement workflow is broken."""
        assert normalize_title('Harry   Potter') == 'harry potter'


class TestCheckDuplicateRequest:
    def test_exact_normalized_duplicate_blocked(self, mock_db):
        """Validates exact normalized duplicate blocked [TestCheckDuplicateRequest / requests].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates request/procurement workflow is broken."""
        mock_db['fetch_all'].return_value = [('1984',)]
        assert check_duplicate_request(5, '1984') is True

    def test_fuzzy_duplicate_blocked(self, mock_db):
        """Validates fuzzy duplicate blocked [TestCheckDuplicateRequest / requests].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates request/procurement workflow is broken."""
        mock_db['fetch_all'].return_value = [('Introduction to Programming',)]
        assert check_duplicate_request(5, 'Intro to Programming') is True

    def test_distinct_titles_allowed(self, mock_db):
        """Validates distinct titles allowed [TestCheckDuplicateRequest / requests].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates request/procurement workflow is broken."""
        mock_db['fetch_all'].return_value = [('Introduction to Biology',)]
        assert check_duplicate_request(5, 'Introduction to Programming') is False

    def test_no_prior_requests_allowed(self, mock_db):
        """Validates no prior requests allowed [TestCheckDuplicateRequest / requests].
    If fails: likely regression in route/model or mock setup drift.
    Failure indicates request/procurement workflow is broken."""
        mock_db['fetch_all'].return_value = []
        assert check_duplicate_request(5, 'Anything') is False


class TestCountRequestsByStatus:
    def test_returns_status_map(self, mock_db):
        """Validates returns status map [TestCountRequestsByStatus / requests].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates request/procurement workflow is broken."""
        from app.requests.models import count_requests_by_status
        mock_db['fetch_all'].return_value = [('pending_review', 3), ('approved', 1)]
        assert count_requests_by_status() == {'pending_review': 3, 'approved': 1}
        assert 'GROUP BY request_status' in mock_db['fetch_all'].call_args[0][0]

    def test_empty_table_returns_empty_map(self, mock_db):
        """Validates empty table returns empty map [TestCountRequestsByStatus / requests].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates request/procurement workflow is broken."""
        from app.requests.models import count_requests_by_status
        mock_db['fetch_all'].return_value = []
        assert count_requests_by_status() == {}


class TestRequestSubmission:
    def test_student_submits_request_success(self, student_client, mock_db):
        """Validates student submits request success `/user/request-book` as student (expects 302) [TestRequestSubmission / requests].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (INSERT INTO).
    Failure indicates request/procurement workflow is broken."""
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
        """Validates submit blank title rejected `/user/request-book` as student (expects 302) [TestRequestSubmission / requests].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates request/procurement workflow is broken."""
        mock_db['fetch_one'].return_value = (5,)

        resp = student_client.post('/user/request-book', data={
            'book-title': '',
            'author': '',
        })

        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_unauthenticated_redirects_to_login(self, client):
        """Validates unauthenticated redirects to login `/user/request-book` (expects 302) [TestRequestSubmission / requests].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates login/RBAC is broken (users locked out or wrongly allowed)."""
        resp = client.get('/user/request-book')
        assert resp.status_code == 302
        assert '/login' in resp.location


class TestLibrarianReview:
    def test_librarian_approves_request(self, librarian_client, mock_db):
        """Validates librarian approves request `/librarian/requests/7/approve` as librarian (expects 302) [TestLibrarianReview / requests].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (UPDATE).
    Failure indicates request/procurement workflow is broken."""
        mock_db['fetch_one'].return_value = (7, 1, 'Some Book', None, None, 'pending_review', None, None, None, None)

        resp = librarian_client.post('/librarian/requests/7/approve')

        assert resp.status_code == 302
        assert '/librarian/requests' in resp.location
        assert mock_db['execute'].call_count >= 2

        call_args = mock_db['execute'].call_args_list[0]
        assert 'UPDATE request_records' in call_args[0][0]

    def test_librarian_rejects_request_with_remarks(self, librarian_client, mock_db):
        """Validates librarian rejects request with remarks `/librarian/requests/7/reject` as librarian (expects 302) [TestLibrarianReview / requests].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (UPDATE).
    Failure indicates request/procurement workflow is broken."""
        mock_db['fetch_one'].return_value = (7, 1, 'Some Book', None, None, 'pending_review', None, None, None, None)

        resp = librarian_client.post('/librarian/requests/7/reject', data={
            'remarks': 'Not relevant to curriculum',
        })

        assert resp.status_code == 302
        call_args = mock_db['execute'].call_args_list[0]
        assert 'UPDATE request_records' in call_args[0][0]
        assert 'Not relevant to curriculum' in call_args[0][1]

    def test_student_forbidden_from_librarian_requests(self, student_client):
        """Validates student forbidden from librarian requests `/librarian/requests` as student (expects 302) [TestLibrarianReview / requests].
    If fails: likely redirect/flash logic changed or guard misordered.
    Failure indicates request/procurement workflow is broken."""
        resp = student_client.get('/librarian/requests')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location

    def test_invalid_action_rejected(self, librarian_client, mock_db):
        """Validates invalid action rejected `/librarian/requests/7/nonsense` as librarian (expects 302) [TestLibrarianReview / requests].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates request/procurement workflow is broken."""
        resp = librarian_client.post('/librarian/requests/7/nonsense')
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_cannot_approve_already_reviewed_request(self, librarian_client, mock_db):
        """Validates cannot approve already reviewed request `/librarian/requests/7/approve` as librarian (expects 302) [TestLibrarianReview / requests].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates request/procurement workflow is broken."""
        mock_db['fetch_one'].return_value = (7, 1, 'Some Book', None, None, 'approved', None, None, None, None)

        resp = librarian_client.post('/librarian/requests/7/approve')

        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_request_not_found_returns_error(self, librarian_client, mock_db):
        """Validates request not found returns error `/librarian/requests/999/approve` as librarian (expects 302) [TestLibrarianReview / requests].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates request/procurement workflow is broken."""
        mock_db['fetch_one'].return_value = None

        resp = librarian_client.post('/librarian/requests/999/approve')

        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0


class TestStackedChartGrouping:
    def test_typo_variants_merge_into_one_bar(self):
        """Validates typo variants merge into one bar [TestStackedChartGrouping / requests].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates request/procurement workflow is broken."""
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
        """Validates staff roles fold into other [TestStackedChartGrouping / requests].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates request/procurement workflow is broken."""
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
        """Validates abbreviation variants merge [TestStackedChartGrouping / requests].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates request/procurement workflow is broken."""
        from app.requests.models import build_stacked_chart
        rows = [
            ('Intro to Programming', 'Student', 2),
            ('Introduction to Programming', 'Faculty', 1),
        ]
        chart = build_stacked_chart(rows)
        assert len(chart) == 1
        assert chart[0][4] == 3

    def test_distinct_titles_stay_separate_and_sorted(self):
        """Validates distinct titles stay separate and sorted [TestStackedChartGrouping / requests].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates request/procurement workflow is broken."""
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
        """Validates variant lookup maps typo to group [TestStackedChartGrouping / requests].
    If fails: likely model query/tuple-contract change or mock return drift.
    Failure indicates request/procurement workflow is broken."""
        from app.requests.models import build_variant_lookup
        rows = [
            ('Introductin to Computing', 'Student', 1),
            ('Introduction to Computing', 'Faculty', 1),
        ]
        lookup = build_variant_lookup(rows)
        assert lookup['Introductin to Computing'] is lookup['Introduction to Computing']
        assert lookup['Introductin to Computing']['total'] == 2


def _details_row(rid, title, name, role, dept, status='pending_review', day='05'):
    """Test helper _details_row: build mocked data or DB stub for the test."""
    return (rid, rid + 100, title, '', None, status, f'2026-01-{day}',
            None, None, None, name, role, dept)


class TestListRendering:
    def test_list_shows_individual_cards_without_overview(self, librarian_client, mock_db):
        """Validates list shows individual cards without overview `/librarian/requests` as librarian (expects 200) [TestListRendering / requests].
    If fails: likely template text/context changed or mock fetch_* shape mismatched.
    Failure indicates request/procurement workflow is broken."""
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
        # Grouped cards: typo variants merge to one card with per-role demand
        # and bulk approve/reject for all pending ids in the group.
        assert 'Faculty: 1' in body
        assert 'Student: 1' in body
        assert 'request_ids' in body
        assert 'Approve' in body

    def test_sort_param_accepted(self, librarian_client, mock_db):
        """Validates sort param accepted `/librarian/requests?sort=recent` as librarian (expects 200) [TestListRendering / requests].
    If fails: likely route/template regression or mock data mismatch.
    Failure indicates request/procurement workflow is broken."""
        mock_db['fetch_all'].side_effect = [[], [], []]
        mock_db['fetch_one'].return_value = (0,)

        resp = librarian_client.get('/librarian/requests?sort=recent')

        assert resp.status_code == 200


class TestBulkReview:
    def test_bulk_approve_all_pending(self, librarian_client, mock_db):
        """Validates bulk approve all pending `/librarian/requests/bulk/approve` as librarian (expects 302) [TestBulkReview / requests].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (UPDATE).
    Failure indicates request/procurement workflow is broken."""
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
        """Validates bulk reject skips reviewed `/librarian/requests/bulk/reject` as librarian (expects 302) [TestBulkReview / requests].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (UPDATE).
    Failure indicates request/procurement workflow is broken."""
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
        """Validates bulk invalid action rejected `/librarian/requests/bulk/nonsense` as librarian (expects 302) [TestBulkReview / requests].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates request/procurement workflow is broken."""
        resp = librarian_client.post('/librarian/requests/bulk/nonsense',
                                     data={'request_ids': '7'})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_bulk_no_ids_rejected(self, librarian_client, mock_db):
        """Validates bulk no ids rejected `/librarian/requests/bulk/approve` as librarian (expects 302) [TestBulkReview / requests].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates request/procurement workflow is broken."""
        resp = librarian_client.post('/librarian/requests/bulk/approve', data={})
        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_bulk_student_forbidden(self, student_client, mock_db):
        """Validates bulk student forbidden `/librarian/requests/bulk/approve` as student (expects 302) [TestBulkReview / requests].
    If fails: likely unexpected DB write (validation/pre-check bypassed).
    Failure indicates request/procurement workflow is broken."""
        resp = student_client.post('/librarian/requests/bulk/approve',
                                   data={'request_ids': '7'})
        assert resp.status_code == 302
        assert '/user/profile' in resp.location
        # The RBAC decorator logs security:denied, but no request rows change.
        updates = [c for c in mock_db['execute'].call_args_list
                   if 'UPDATE request_records' in c[0][0]]
        assert updates == []


class TestUserCancelRequest:
    def test_user_cancels_pending_request(self, student_client, mock_db):
        """Validates user cancels pending request `/user/requests/7/cancel` as student (expects 302) [TestUserCancelRequest / requests].
    If fails: likely wrong/absent SQL call or placeholder mismatch; model SQL changed (UPDATE).
    Failure indicates member self-service cancellation is broken."""
        mock_db['fetch_one'].side_effect = [
            (7, 5, 'Some Book', None, None, 'pending_review', None, None, None, None),  # get_request_by_id
            (5,),   # get_borrower_by_user -> borrower_id
        ]

        resp = student_client.post('/user/requests/7/cancel')

        assert resp.status_code == 302
        assert '/user/profile' in resp.location
        writes = [c for c in mock_db['execute'].call_args_list
                  if 'UPDATE request_records' in c[0][0]]
        assert len(writes) == 1
        assert 'cancelled' in writes[0][0][1]
        # Pending requests carry no procurement row to touch.
        assert not any('UPDATE procurement_log' in c[0][0]
                       for c in mock_db['execute'].call_args_list)

    def test_user_cancels_approved_request_cancels_order(self, student_client, mock_db):
        """Validates user cancels approved request with pending order `/user/requests/7/cancel` as student (expects 302) [TestUserCancelRequest / requests].
    If fails: likely procurement cancellation missing or wrong order status written.
    Failure indicates withdrawn requests leave orphaned procurement orders."""
        mock_db['fetch_one'].side_effect = [
            (7, 5, 'Some Book', None, None, 'approved', None, None, None, None),
            (5,),
        ]
        mock_db['fetch_all'].return_value = [
            (901, 7, 'for_ordering', None, None, None, None, None, None, 'Some Book', None)
        ]

        resp = student_client.post('/user/requests/7/cancel')

        assert resp.status_code == 302
        by_sql = {c[0][0]: c for c in mock_db['execute'].call_args_list}
        proc_calls = [s for s in by_sql if 'UPDATE procurement_log' in s]
        assert proc_calls, 'approved request without order must still cancel the procurement row'
        assert 'cancelled' in by_sql[proc_calls[0]][0][1]
        req_calls = [s for s in by_sql if 'UPDATE request_records' in s]
        assert req_calls and 'cancelled' in by_sql[req_calls[0]][0][1]

    def test_cannot_cancel_once_ordered(self, student_client, mock_db):
        """Validates cannot cancel once ordered `/user/requests/7/cancel` as student (expects 302) [TestUserCancelRequest / requests].
    If fails: likely the ordered guard is missing/loose (unexpected UPDATE below).
    Failure indicates orders in flight can be killed by members."""
        mock_db['fetch_one'].side_effect = [
            (7, 5, 'Some Book', None, None, 'approved', None, None, None, None),
            (5,),
        ]
        mock_db['fetch_all'].return_value = [
            (901, 7, 'ordered', None, None, None, None, None, None, 'Some Book', None)
        ]

        resp = student_client.post('/user/requests/7/cancel')

        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_cannot_cancel_others_request(self, student_client, mock_db):
        """Validates cannot cancel others request `/user/requests/7/cancel` as student (expects 302) [TestUserCancelRequest / requests].
    If fails: likely ownership check bypassed (unexpected UPDATE below).
    Failure indicates members can cancel borrowed book requests"""
        mock_db['fetch_one'].side_effect = [
            (7, 9, 'Some Book', None, None, 'pending_review', None, None, None, None),
            (5,),
        ]

        resp = student_client.post('/user/requests/7/cancel')

        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_cannot_cancel_reviewed_request(self, student_client, mock_db):
        """Validates cannot cancel reviewed request `/user/requests/7/cancel` as student (expects 302) [TestUserCancelRequest / requests].
    If fails: likely lifecycle guard missing (unexpected UPDATE below).
    Failure indicates finished requests can be rewritten by members."""
        mock_db['fetch_one'].side_effect = [
            (7, 5, 'Some Book', None, None, 'rejected', None, None, None, None),
            (5,),
        ]

        resp = student_client.post('/user/requests/7/cancel')

        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_cannot_cancel_missing_request(self, student_client, mock_db):
        """Validates cannot cancel missing request `/user/requests/7/cancel` as student (expects 302) [TestUserCancelRequest / requests].
    If fails: likely existence pre-check bypassed.
    Failure indicates ghost ids flash success instead of an error."""
        mock_db['fetch_one'].side_effect = [None]

        resp = student_client.post('/user/requests/7/cancel')

        assert resp.status_code == 302
        assert mock_db['execute'].call_count == 0

    def test_unauthenticated_cancel_redirects_to_login(self, client):
        """Validates unauthenticated cancel redirects to login `/user/requests/7/cancel` (expects 302) [TestUserCancelRequest / requests].
    If fails: likely login_required guard removed.
    Failure indicates cancellation is open to anonymous visitors."""
        resp = client.post('/user/requests/7/cancel')
        assert resp.status_code == 302
        assert '/login' in resp.location