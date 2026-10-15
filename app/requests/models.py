import re
from difflib import SequenceMatcher
from app.database import db

ABBREVIATIONS = {
    'intro': 'introduction',
    'prog': 'programming',
    'comp': 'computer',
    'sci': 'science',
    'admin': 'administration',
}

def normalize_title(title):
    """Normalize a hand-typed title for duplicate and fuzzy comparison.

    Lowercases, strips punctuation, expands common abbreviations
    (intro→introduction, prog→programming, etc.), and collapses
    whitespace so "Intro. to Prog" and "introduction to programming"
    compare equal. Pure helper with no DB access.

    Args:
        title: Raw title string.

    Returns:
        Normalized comparison string.
    """
    title = title.lower()
    title = re.sub(r'[^\w\s]', '', title)
    words = [ABBREVIATIONS.get(w, w) for w in title.split()]
    return ' '.join(words)

def create_request(requester_id, book_title, author=None):
    """File a new book acquisition request as pending_review.

    Inserts into request_records with status 'pending_review' and no
    matched book; staff triage it via update_request_status. Routes
    call the duplicate/catalog guards before reaching here.

    Args:
        requester_id: Requesting member's borrower FK.
        book_title: Requested title as typed.
        author: Optional author as typed.

    Returns:
        New request_id integer from the RETURNING clause.
    """
    rows = db.execute(
        '''INSERT INTO request_records (requester_id, book_title, author, request_status, matched_book_id)
           VALUES (%s, %s, %s, %s, %s)
           RETURNING request_id''',
        (requester_id, book_title, author, 'pending_review', None)
    )
    return rows[0][0]

def get_borrower_by_user(user_id):
    """Resolve a login user to their borrower id for request ownership.

    Request records key off borrowers.borrower_id, so every user-side
    request flow maps the Flask-Login user_id first. Returns just the
    integer (unlike circulation's full-row variant).

    Args:
        user_id: user_accounts primary key.

    Returns:
        borrower_id integer, or None when the user has no borrower row.
    """
    row = db.fetch_one(
        'SELECT borrower_id FROM borrowers WHERE user_id = %s',
        (user_id,)
    )
    return row[0] if row else None

def get_requests(status=None):
    """List requests ordered for staff triage, optionally by one status.

    A single status returns newest-first; the "All" view orders by
    actionable priority (pending_review, approved, rejected, procured)
    then newest-first so work needing action surfaces first.

    Args:
        status: Optional request_status to filter by.

    Returns:
        List of full request_records row tuples in triage order.
    """
    if status:
        return db.fetch_all(
            'SELECT * FROM request_records WHERE request_status = %s ORDER BY request_date DESC',
            (status,)
        )
    return db.fetch_all(
        'SELECT * FROM request_records '
        "ORDER BY CASE request_status "
        "WHEN 'pending_review' THEN 0 "
        "WHEN 'approved' THEN 1 "
        "WHEN 'rejected' THEN 2 "
        "WHEN 'procured' THEN 3 "
        "ELSE 4 END, request_date DESC"
    )

# "All" view prioritizes actionable statuses first.
STATUS_PRIORITY_ORDER = (
    "ORDER BY CASE r.request_status "
    "WHEN 'pending_review' THEN 0 "
    "WHEN 'approved' THEN 1 "
    "WHEN 'rejected' THEN 2 "
    "WHEN 'procured' THEN 3 "
    "ELSE 4 END, r.request_date DESC"
)

PER_PAGE = 50

def get_requests_with_details(status=None, search=None, page=1):
    """List one page of requests joined to requester identity.

    Joins request_records through borrowers, users, and roles to show
    (request_id, requester_id, book_title, author, matched_book_id,
    request_status, request_date, reviewed_by, review_date, remarks,
    full_name, role_name, department). Optional status and ILIKE title
    filters apply; a single status sorts newest-first while "All" uses
    STATUS_PRIORITY_ORDER. Fixed PER_PAGE pages keep staff lists fast.

    Args:
        status: Optional request_status filter.
        search: Optional title substring (ILIKE %...%).
        page: 1-based page number.

    Returns:
        List of 13-tuple detail rows for the page.
    """
    base_query = '''
        SELECT r.request_id, r.requester_id, r.book_title, r.author,
               r.matched_book_id, r.request_status, r.request_date,
               r.reviewed_by, r.review_date, r.remarks,
               u.full_name, ro.role_name, b.department
        FROM request_records r
        JOIN borrowers b ON b.borrower_id = r.requester_id
        JOIN user_accounts u ON u.user_id = b.user_id
        JOIN roles ro ON ro.role_id = u.role_id
    '''
    conditions = []
    params = []

    if status:
        conditions.append('r.request_status = %s')
        params.append(status)

    if search:
        conditions.append('r.book_title ILIKE %s')
        params.append(f'%{search}%')

    if conditions:
        base_query += ' WHERE ' + ' AND '.join(conditions)

    if status:
        base_query += ' ORDER BY r.request_date DESC LIMIT %s OFFSET %s'
    else:
        # "All" view: Pending first, then Approved, Rejected, Procured.
        base_query += ' ' + STATUS_PRIORITY_ORDER + ' LIMIT %s OFFSET %s'
    params.append(PER_PAGE)
    params.append((page - 1) * PER_PAGE)

    return db.fetch_all(base_query, tuple(params))


def count_requests(status=None, search=None):
    """Count requests matching the list filters for pagination totals.

    Mirrors get_requests_with_details' status and title-search filters
    so the total matches the rows paging can return.

    Args:
        status: Optional request_status filter.
        search: Optional title substring filter.

    Returns:
        Integer matching-request count.
    """
    base_query = 'SELECT COUNT(*) FROM request_records r'
    conditions = []
    params = []

    if status:
        conditions.append('r.request_status = %s')
        params.append(status)

    if search:
        conditions.append('r.book_title ILIKE %s')
        params.append(f'%{search}%')

    if conditions:
        base_query += ' WHERE ' + ' AND '.join(conditions)

    row = db.fetch_one(base_query, tuple(params))
    return row[0] if row else 0


def count_requests_by_status():
    """Headline stat cards: {request_status: count} over all requests."""
    rows = db.fetch_all(
        'SELECT request_status, COUNT(*) FROM request_records GROUP BY request_status'
    )
    counts = {}
    for row in rows or []:
        try:
            counts[str(row[0])] = int(row[1] or 0)
        except (IndexError, TypeError, ValueError):
            continue
    return counts

def get_request_by_id(request_id):
    """Fetch one request row by primary key regardless of status.

    Used by review/approve/reject/procure actions to confirm the row
    exists and read its current status before transitioning it.

    Args:
        request_id: request_records primary key.

    Returns:
        Full request_records row tuple, or None if not found.
    """
    return db.fetch_one(
        'SELECT * FROM request_records WHERE request_id = %s',
        (request_id,)
    )


def update_request_status(request_id, status, reviewer_id=None, remarks=None):
    """Transition a request to a new status with reviewer audit stamps.

    Sets request_status plus remarks and updated_by always; when a
    reviewer is given it also stamps reviewed_by and review_date=NOW().
    Used for approve/reject/procure/bulk-review flows.

    Args:
        request_id: Target request_records row.
        status: New status ('approved', 'rejected', 'procured', etc.).
        reviewer_id: Staff reviewer user_id, or None.
        remarks: Staff note stored with the decision.

    Returns:
        Rowcount from the UPDATE.
    """
    if reviewer_id:
        return db.execute(
            'UPDATE request_records SET request_status = %s, reviewed_by = %s, review_date = NOW(), remarks = %s, updated_at = NOW(), updated_by = %s WHERE request_id = %s',
            (status, reviewer_id, remarks, reviewer_id, request_id)
        )
    return db.execute(
        'UPDATE request_records SET request_status = %s, remarks = %s, updated_at = NOW(), updated_by = %s WHERE request_id = %s',
        (status, remarks, None, request_id)
    )


def get_demand_count(book_title):
    """Count exact-title requests for a demand badge.

    Simple COUNT(*) where book_title matches exactly (no fuzzy
    merging); the overview chart uses get_stacked_demand instead for
    merged demand.

    Args:
        book_title: Exact title string to count.

    Returns:
        Integer request count for that spelling.
    """
    row = db.fetch_one(
        'SELECT COUNT(*) FROM request_records WHERE book_title = %s',
        (book_title,)
    )
    return row[0] if row else 0


def get_demand_by_role():
    """Fetch raw per-title per-role demand rows for chart clustering.

    Returns (book_title, role_name, count) over pending_review +
    approved rows only, grouped by exact title spelling. Routes feed
    these into build_stacked_chart/_cluster_demand to merge typo
    variants before rendering.

    Returns:
        List of (book_title, role_name, count) tuples.
    """
    return db.fetch_all(
        '''SELECT rr.book_title, r.role_name, COUNT(*) AS count
           FROM request_records rr
           JOIN borrowers b ON rr.requester_id = b.borrower_id
           JOIN user_accounts u ON b.user_id = u.user_id
           JOIN roles r ON u.role_id = r.role_id
           WHERE rr.request_status IN ('pending_review', 'approved')
           GROUP BY rr.book_title, r.role_name'''
    )


def get_stacked_demand(limit=10):
    """Per-title Student vs Faculty (+Other staff) demand for the overview.

    Returns positional tuples (contract):
    (display_title, student_count, faculty_count, other_count, total_count)
    ordered by total_count DESC. Groups case-insensitively so
    "Clean Code" and "clean code" land in one bar; display_title is
    MIN(book_title) for a stable label. Only pending_review + approved
    rows count toward acquisition demand. ``other_count`` covers Admin /
    Librarian / any non-Student/Faculty role so the bar never renders
    empty when a title has requests but zero Student/Faculty split.
    """
    return db.fetch_all(
        '''SELECT MIN(rr.book_title) AS display_title,
                  COUNT(*) FILTER (WHERE r.role_name = 'Student') AS student_count,
                  COUNT(*) FILTER (WHERE r.role_name = 'Faculty') AS faculty_count,
                  COUNT(*) FILTER (WHERE r.role_name NOT IN ('Student', 'Faculty')) AS other_count,
                  COUNT(*) AS total_count
           FROM request_records rr
           JOIN borrowers b ON rr.requester_id = b.borrower_id
           JOIN user_accounts u ON b.user_id = u.user_id
           JOIN roles r ON u.role_id = r.role_id
           WHERE rr.request_status IN ('pending_review', 'approved')
           GROUP BY LOWER(TRIM(rr.book_title))
           ORDER BY total_count DESC, display_title ASC
           LIMIT %s''',
        (limit,)
    )


# Titles typed by hand fragment ("Introductin" vs "Introduction",
# "Intro to ..." vs "Introduction to ..."). The overview chart and the
# grouped cards must merge those variants or demand splits into
# misleading 1-request bars. Pure helpers (no DB) so routes can cluster
# both the global demand rows and the current page items identically.
TITLE_FUZZY_RATIO = 0.85


def _cluster_demand(demand_rows):
    """Cluster (book_title, role_name, count) rows into title groups.

    Returns a list of dicts:
    {'display': str, 'variants': [str], 'counts': {role: int}, 'total': int}
    sorted by total DESC, display ASC. Canonical display is the variant
    with the highest backing count (most common spelling wins).
    """
    exact = {}
    for row in demand_rows or []:
        try:
            title, role_name, count = row[0], row[1], int(row[2] or 0)
        except (IndexError, TypeError, ValueError):
            continue
        if not title:
            continue
        bucket = exact.setdefault(title, {})
        bucket[role_name] = bucket.get(role_name, 0) + count

    groups = []
    order = sorted(exact.items(), key=lambda kv: (-sum(kv[1].values()), kv[0].lower()))
    for title, counts in order:
        norm = normalize_title(title)
        target = None
        for g in groups:
            if norm == g['norm']:
                target = g
                break
            try:
                if SequenceMatcher(None, norm, g['norm']).ratio() >= TITLE_FUZZY_RATIO:
                    target = g
                    break
            except Exception:
                continue
        if target is None:
            groups.append({
                'display': title,
                'variants': [title],
                'norm': norm,
                'counts': dict(counts),
                'total': sum(counts.values()),
            })
        else:
            target['variants'].append(title)
            for role_name, count in counts.items():
                target['counts'][role_name] = target['counts'].get(role_name, 0) + count
            target['total'] = sum(target['counts'].values())

    groups.sort(key=lambda g: (-g['total'], g['display'].lower()))
    return groups


def build_stacked_chart(demand_rows, limit=10):
    """Build overview bars from raw get_demand_by_role() rows.

    Returns positional tuples (contract):
    (display_title, student_count, faculty_count, other_count, total_count)
    with typo variants merged and staff roles folded into other_count.
    """
    out = []
    for g in _cluster_demand(demand_rows)[:limit]:
        student = int(g['counts'].get('Student', 0) or 0)
        faculty = int(g['counts'].get('Faculty', 0) or 0)
        total = int(g['total'] or 0)
        other = max(total - student - faculty, 0)
        out.append((g['display'], student, faculty, other, total))
    return out


def build_variant_lookup(demand_rows):
    """Map every exact title variant to its clustered group.

    Lets per-card lookups hit merged demand even when the card's own
    spelling differs ("Introductin" still shows the merged bar).
    Returns {exact_title: group_dict} sharing objects with _cluster_demand.
    """
    lookup = {}
    for g in _cluster_demand(demand_rows):
        for variant in g['variants']:
            lookup[variant] = g
    return lookup

def get_requests_by_borrower(borrower_id):
    """List one member's own requests newest-first for their requests page.

    Returns the narrow user-facing shape (request_id, book_title,
    author, request_status, request_date, remarks) so members can track
    triage without seeing staff reviewer internals.

    Args:
        borrower_id: Requesting member's borrower FK.

    Returns:
        List of 6-tuple request rows.
    """
    return db.fetch_all(
        'SELECT request_id, book_title, author, request_status, request_date, remarks FROM request_records WHERE requester_id = %s ORDER BY request_date DESC',
        (borrower_id,)
    )

def check_duplicate_request(requester_id, book_title):
    """Check whether a member already has a live request for a title.

    Compares the normalized new title against the member's
    pending_review + approved rows using exact match plus fuzzy
    SequenceMatcher (>= 0.85), so "Introductin" still collides with
    "Introduction". Prevents double-filing the same want.

    Args:
        requester_id: Member's borrower FK.
        book_title: Newly typed title to test.

    Returns:
        True when a live duplicate exists.
    """
    normalized = normalize_title(book_title)
    rows = db.fetch_all(
        "SELECT book_title FROM request_records WHERE requester_id = %s AND request_status IN ('pending_review', 'approved')",
        (requester_id,)
    ) or []

    for (title,) in rows:
        existing_normalized = normalize_title(title)
        if existing_normalized == normalized:
            return True
        if len(existing_normalized) >= 10 and len(normalized) >= 10:
            try:
                if SequenceMatcher(None, existing_normalized, normalized).ratio() >= 0.85:
                    return True
            except Exception:
                continue

    return False


def _title_matches(existing_title, normalized):
    """Test one catalog/request title against a normalized query title.

    Shared exact-plus-fuzzy comparison behind the existence guards:
    normalized exact equality always wins; SequenceMatcher ratio >=
    TITLE_FUZZY_RATIO only counts for longer titles (both sides >= 10
    chars) so short test-like titles differing by one character
    ("test_01" vs "test_02", ratio 0.857) do not false-positive.
    Never raises — bad inputs simply return False.

    Args:
        existing_title: Title string from the DB row.
        normalized: Already-normalized query title to compare.

    Returns:
        True when the titles match exactly or fuzzily.
    """
    try:
        existing_normalized = normalize_title(existing_title or '')
    except Exception:
        return False
    if not existing_normalized or not normalized:
        return False
    if existing_normalized == normalized:
        return True
    if len(existing_normalized) < 10 or len(normalized) < 10:
        return False
    try:
        return SequenceMatcher(None, existing_normalized, normalized).ratio() >= TITLE_FUZZY_RATIO
    except Exception:
        return False


def check_catalog_exists(book_title):
    """True when an active (not archived/inactive) catalog book matches.

    Only rows with catalog_status = 'active' block a new request;
    archived (or inactive) books are requestable again.
    """
    normalized = normalize_title(book_title or '')
    if not normalized:
        return False
    rows = db.fetch_all(
        "SELECT title FROM book_catalog WHERE catalog_status = 'active'"
    ) or []
    for row in rows:
        try:
            title = row[0]
        except (IndexError, TypeError):
            continue
        if _title_matches(title, normalized):
            return True
    return False


def check_approved_request_exists(book_title):
    """True when an already-approved (or procured) request matches the title."""
    normalized = normalize_title(book_title or '')
    if not normalized:
        return False
    rows = db.fetch_all(
        "SELECT book_title FROM request_records "
        "WHERE request_status IN ('approved', 'procured')"
    ) or []
    for row in rows:
        try:
            title = row[0]
        except (IndexError, TypeError):
            continue
        if _title_matches(title, normalized):
            return True
    return False