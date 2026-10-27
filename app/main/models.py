from app.database import db


def get_tutorial_book(is_ebook, user_id):
    """Find a real active example without creating circulation/access records."""
    return db.fetch_one(
        '''SELECT b.book_id, b.title FROM book_catalog b
           WHERE b.catalog_status = 'active'
             AND ((%s AND b.material_type = 'E-Book'
                        AND NULLIF(TRIM(b.ebook_url), '') IS NOT NULL)
                  OR (NOT %s AND b.material_type = 'Book'
                      AND EXISTS (SELECT 1 FROM accession_log a
                                  WHERE a.book_id = b.book_id
                                  AND NOT EXISTS (SELECT 1 FROM circulation_records c
                                      WHERE c.accession_id = a.accession_id
                                      AND c.transaction_status IN ('active', 'overdue')))
                      AND NOT EXISTS (SELECT 1 FROM circulation_records c
                          JOIN borrowers br ON br.borrower_id = c.borrower_id
                          WHERE c.book_id = b.book_id AND br.user_id = %s
                          AND c.transaction_status IN ('active', 'overdue'))))
           ORDER BY b.book_id LIMIT 1''',
        (is_ebook, is_ebook, user_id),
    )
from app.auth.models import get_pending_users
from app.settings.models import library_today
from app.circulation.models import (
    get_circulation_stats,
    get_reservations_grouped,
)
from app.procurement.models import get_procurement_items

import threading
import time

# Short-lived in-process cache for Overview headline counts (perf batch
# #5). The librarian/admin dashboards re-count on every hit; a 60s TTL
# absorbs repeat views without visible staleness. Single-worker safe
# (gunicorn runs one worker); disabled without an app context and under
# TESTING so mocked tests stay deterministic.
STATS_TTL_SECONDS = 60
_stats_cache = {}
_stats_lock = threading.Lock()


def _stats_cache_allowed():
    """Check whether the in-process overview stats cache may be used.

    Returns True only inside an app context when TESTING is off, so unit
    tests with mocked db calls stay deterministic and cache-free. Guards
    the librarian/admin dashboards that re-count headline stats per hit.

    Args:
        None.

    Returns:
        True when caching is allowed, False otherwise.
    """
    try:
        from flask import current_app, has_app_context
        return has_app_context() and not current_app.config.get('TESTING')
    except Exception:
        return False


def _cached_stats(key, compute):
    """Return cached overview stats or compute and store them for 60s.

    Checks the in-process _stats_cache under _stats_lock; a fresh hit
    returns immediately while a miss or expired entry runs compute and
    caches the result. Bypassed entirely when _stats_cache_allowed is
    False so tests always hit the database mocks.

    Args:
        key: Cache key string ('dashboard' or 'admin_overview').
        compute: Zero-arg callable producing the stats dict on a miss.

    Returns:
        Stats dict produced by compute or retrieved from the cache.
    """
    if not _stats_cache_allowed():
        return compute()
    now = time.monotonic()
    with _stats_lock:
        hit = _stats_cache.get(key)
        if hit is not None and now - hit[0] < STATS_TTL_SECONDS:
            return hit[1]
    value = compute()
    with _stats_lock:
        _stats_cache[key] = (time.monotonic(), value)
    return value


def clear_stats_cache():
    """Drop all cached Overview counts (tests, manual refresh).

    Clears the in-process _stats_cache under lock so the next dashboard
    or admin overview hit recomputes from the database. Used by tests
    and manual refresh paths to avoid stale headline counts.

    Args:
        None.

    Returns:
        None; empties the cache in place.
    """
    with _stats_lock:
        _stats_cache.clear()


def get_dashboard_stats():
    """Return cached librarian dashboard headline counts.

    Thin cached wrapper around _get_dashboard_stats via _cached_stats
    with a 60s TTL, so repeat dashboard views avoid five recount
    queries. Circulation-focused: collection, loans, requests, overdue.

    Args:
        None.

    Returns:
        Dict with total_collection, total_titles, total_accessions,
        active_loans, open_requests, overdue_items, reservations_waiting,
        and procurement_open counts.
    """
    return _cached_stats('dashboard', _get_dashboard_stats)


def _get_dashboard_stats():
    """Compute uncached librarian dashboard headline counts.

    Runs five COUNT queries for active titles, active accessions, active
    loans, open requests, and overdue borrows, then adds waiting
    reservations and open procurement via helper counters. Called only
    through get_dashboard_stats so results are cached for 60s.

    Args:
        None.

    Returns:
        Dict with total_collection, total_titles, total_accessions,
        active_loans, open_requests, overdue_items, reservations_waiting,
        and procurement_open counts.
    """
    titles = db.fetch_one(
        "SELECT COUNT(*) FROM book_catalog WHERE catalog_status = 'active'"
    )
    accessions = db.fetch_one(
        '''SELECT COUNT(*) FROM accession_log a
           JOIN book_catalog b ON a.book_id = b.book_id
           WHERE b.catalog_status = 'active' '''
    )
    active_loans = db.fetch_one(
        "SELECT COUNT(*) FROM circulation_records WHERE transaction_type = 'borrow' AND transaction_status IN ('active', 'overdue')"
    )
    open_requests = db.fetch_one(
        "SELECT COUNT(*) FROM request_records WHERE request_status IN ('pending_review', 'approved')"
    )
    overdue = db.fetch_one(
        "SELECT COUNT(*) FROM circulation_records WHERE transaction_type = 'borrow' AND transaction_status IN ('active', 'overdue') AND due_date::date < (%s)::date",
        (library_today(),)
    )
    total_titles = titles[0] if titles else 0
    total_accessions = accessions[0] if accessions else 0
    return {
        'total_collection': total_titles,
        'total_titles': total_titles,
        'total_accessions': total_accessions,
        'active_loans': active_loans[0] if active_loans else 0,
        'open_requests': open_requests[0] if open_requests else 0,
        'overdue_items': overdue[0] if overdue else 0,
        'reservations_waiting': count_waiting_reservations(),
        'procurement_open': count_open_procurement(),
    }


def count_waiting_reservations():
    """Reservations still needing librarian action (waiting + allocated).

    Sums the waiting (row[4]) and allocated (row[5]) columns of every
    get_reservations_grouped row, tolerating short or malformed rows so
    one bad group never breaks the dashboard headline count.

    Args:
        None.

    Returns:
        Integer total of waiting plus allocated reservations.
    """
    total = 0
    for row in get_reservations_grouped() or []:
        try:
            total += int(row[4] or 0) + int(row[5] or 0)
        except (IndexError, TypeError, ValueError):
            continue
    return total


def get_staff_attention_counts():
    """Full (pending-review requests, waiting reservations) counts.

    The two operational numbers behind the staff bell badge — every
    pending book request and every waiting reservation, uncapped (the
    bell feed previews cap at 5 per kind, so badge math must count the
    tables directly). Each count fails open to 0 so a DB blip never
    breaks rendering; the query order matches the header context
    processor so mocked call sequences stay stable.

    Args:
        None.

    Returns:
        Tuple (pending_review_count, waiting_count), ints or readable
        count-like values (badge math coerces).
    """
    pending = waiting = 0
    try:
        r = db.fetch_one(
            "SELECT COUNT(*) FROM request_records WHERE request_status = 'pending_review'")
        pending = (r[0] or 0) if r else 0
    except Exception:
        pass
    try:
        r = db.fetch_one(
            "SELECT COUNT(*) FROM reservation_queue WHERE reservation_status = 'waiting'")
        waiting = (r[0] or 0) if r else 0
    except Exception:
        pass
    return pending, waiting


def count_overdue_loans():
    """Count loans needing attention: status 'overdue' plus active loans
    past due (the DB never flips status on its own, so date-past-due
    actives count too, same as the page badge logic). due_date holds
    naive PHT wall-clock, so the cutoff is library_now().

    Args:
        None.

    Returns:
        Integer overdue loan count (fail-open to 0).
    """
    try:
        from app.settings.models import library_now
        cutoff = library_now()
        r = db.fetch_one(
            "SELECT COUNT(*) FROM circulation_records"
            " WHERE transaction_status = 'overdue'"
            " OR (transaction_status = 'active' AND due_date < %s)",
            (cutoff,))
        return int(r[0] or 0) if r else 0
    except Exception:
        return 0


def count_unpaid_fines():
    """Count every circulation record still owing money (fine_amount
    above zero and fine_paid false, any loan state — returns included —
    so no unpaid fine escapes the bell).

    Args:
        None.

    Returns:
        Integer unpaid fine count (fail-open to 0).
    """
    try:
        r = db.fetch_one(
            "SELECT COUNT(*) FROM circulation_records"
            " WHERE fine_amount > 0 AND NOT fine_paid")
        return int(r[0] or 0) if r else 0
    except Exception:
        return 0


_COUNT_LOW_STOCK_WHERES = '''
WHERE b.catalog_status = 'active'
  AND (
    SELECT COUNT(*) FROM accession_log a
    WHERE a.book_id = b.book_id
      AND NOT EXISTS (
          SELECT 1 FROM circulation_records c
          WHERE c.accession_id = a.accession_id
            AND c.transaction_status IN ('active', 'overdue')
      )
      AND COALESCE((
            SELECT c3.lost_flag FROM circulation_records c3
            WHERE c3.accession_id = a.accession_id
            ORDER BY c3.circulation_id DESC LIMIT 1
        ), FALSE) = FALSE
      AND COALESCE((
            SELECT ist.inventory_state FROM inventory_status ist
            WHERE ist.accession_id = a.accession_id
        ), '') != 'lost'
  ) <= %s'''


def count_low_stock_titles(threshold):
    """Count active titles whose lendable copies sit at or below the
    low-stock threshold. Availability mirrors
    count_available_accessions (no active/overdue loan, not lost) as an
    aggregate, so one query covers every title.

    Args:
        threshold: Lendable-copy floor (LOW_STOCK_THRESHOLD setting).

    Returns:
        Integer low-stock title count (fail-open to 0).
    """
    try:
        r = db.fetch_one(
            f"SELECT COUNT(*) FROM book_catalog b {_COUNT_LOW_STOCK_WHERES}",
            (int(threshold),))
        return int(r[0] or 0) if r else 0
    except Exception:
        return 0


def count_recent_cancelled_requests():
    """Count member-cancelled book requests from the last 30 days
    (library clock), so old history never inflates the staff badge.

    Args:
        None.

    Returns:
        Integer recent cancellation count (fail-open to 0).
    """
    try:
        from datetime import timedelta
        from app.settings.models import library_now
        cutoff = library_now() - timedelta(days=30)
        r = db.fetch_one(
            "SELECT COUNT(*) FROM request_records r"
            " WHERE r.request_status = 'cancelled'"
            " AND COALESCE(r.updated_at, r.review_date, r.request_date) >= %s",
            (cutoff,))
        return int(r[0] or 0) if r else 0
    except Exception:
        return 0


def count_pending_faculty():
    """Count signups on the Faculty role awaiting account approval.

    Args:
        None.

    Returns:
        Integer pending faculty count (fail-open to 0).
    """
    try:
        r = db.fetch_one(
            "SELECT COUNT(*) FROM user_accounts u"
            " JOIN roles r ON u.role_id = r.role_id"
            " WHERE u.account_status = 'pending' AND r.role_name = 'Faculty'")
        return int(r[0] or 0) if r else 0
    except Exception:
        return 0


def count_system_errors():
    """Count audit rows logged by the 500 handler (system:error:*
    activity codes) — the admin 'System Errors' bell signal.

    Args:
        None.

    Returns:
        Integer system error count (fail-open to 0).
    """
    try:
        r = db.fetch_one(
            "SELECT COUNT(*) FROM audit_trail"
            " WHERE activity LIKE 'system:error%'")
        return int(r[0] or 0) if r else 0
    except Exception:
        return 0


def get_overdue_loan_attention(limit=5):
    """Newest overdue loans for the staff bell feed.

    Args:
        limit: Maximum rows to return.

    Returns:
        List of (circulation_id, borrower_name, book_title, due_date)
        tuples for loans past due, oldest due first (most urgent).
    """
    try:
        from app.settings.models import library_now
        cutoff = library_now()
        return db.fetch_all(
            '''SELECT c.circulation_id, u.full_name, b.title, c.due_date
               FROM circulation_records c
               JOIN borrowers bo ON c.borrower_id = bo.borrower_id
               JOIN user_accounts u ON bo.user_id = u.user_id
               JOIN book_catalog b ON c.book_id = b.book_id
               WHERE c.transaction_status = 'overdue'
                  OR (c.transaction_status = 'active' AND c.due_date < %s)
               ORDER BY c.due_date ASC
               LIMIT %s''',
            (cutoff, limit)) or []
    except Exception:
        return []


def get_unpaid_fine_attention(limit=5):
    """Newest unpaid fines for the staff bell feed.

    Args:
        limit: Maximum rows to return.

    Returns:
        List of (circulation_id, fine_amount, borrower_name, book_title)
        tuples, newest loan first.
    """
    try:
        return db.fetch_all(
            '''SELECT c.circulation_id, c.fine_amount, u.full_name, b.title
               FROM circulation_records c
               JOIN borrowers bo ON c.borrower_id = bo.borrower_id
               JOIN user_accounts u ON bo.user_id = u.user_id
               JOIN book_catalog b ON c.book_id = b.book_id
               WHERE c.fine_amount > 0 AND NOT c.fine_paid
               ORDER BY c.circulation_id DESC
               LIMIT %s''',
            (limit,)) or []
    except Exception:
        return []


def get_low_stock_titles(threshold, limit=5):
    """Active titles at or below the low-stock threshold for the staff
    bell feed (same availability rule as count_low_stock_titles).

    Args:
        threshold: Lendable-copy floor (LOW_STOCK_THRESHOLD setting).
        limit: Maximum rows to return.

    Returns:
        List of (book_id, title, available_count) tuples.
    """
    try:
        return db.fetch_all(
            f'''SELECT b.book_id, b.title,
                   (SELECT COUNT(*) FROM accession_log a
                    WHERE a.book_id = b.book_id
                      AND NOT EXISTS (
                          SELECT 1 FROM circulation_records c
                          WHERE c.accession_id = a.accession_id
                            AND c.transaction_status IN ('active', 'overdue')
                      )
                      AND COALESCE((
                            SELECT c3.lost_flag FROM circulation_records c3
                            WHERE c3.accession_id = a.accession_id
                            ORDER BY c3.circulation_id DESC LIMIT 1
                        ), FALSE) = FALSE
                      AND COALESCE((
                            SELECT ist.inventory_state FROM inventory_status ist
                            WHERE ist.accession_id = a.accession_id
                        ), '') != 'lost'
                   ) AS available
               FROM book_catalog b
               WHERE b.catalog_status = 'active'
                 AND (
                   SELECT COUNT(*) FROM accession_log a
                   WHERE a.book_id = b.book_id
                     AND NOT EXISTS (
                         SELECT 1 FROM circulation_records c
                         WHERE c.accession_id = a.accession_id
                           AND c.transaction_status IN ('active', 'overdue')
                     )
                     AND COALESCE((
                           SELECT c3.lost_flag FROM circulation_records c3
                           WHERE c3.accession_id = a.accession_id
                           ORDER BY c3.circulation_id DESC LIMIT 1
                       ), FALSE) = FALSE
                     AND COALESCE((
                           SELECT ist.inventory_state FROM inventory_status ist
                           WHERE ist.accession_id = a.accession_id
                       ), '') != 'lost'
                 ) <= %s
               ORDER BY b.title
               LIMIT %s''',
            (int(threshold), limit)) or []
    except Exception:
        return []


def get_cancelled_request_attention(limit=5):
    """Newest member-cancelled book requests (last 30 days) for the
    staff bell feed.

    Args:
        limit: Maximum rows to return.

    Returns:
        List of (request_id, book_title, cancelled_at) tuples, newest
        cancellation first.
    """
    try:
        from datetime import timedelta
        from app.settings.models import library_now
        cutoff = library_now() - timedelta(days=30)
        return db.fetch_all(
            '''SELECT r.request_id, r.book_title,
                      COALESCE(r.updated_at, r.review_date, r.request_date)
               FROM request_records r
               WHERE r.request_status = 'cancelled'
                 AND COALESCE(r.updated_at, r.review_date, r.request_date) >= %s
               ORDER BY 3 DESC
               LIMIT %s''',
            (cutoff, limit)) or []
    except Exception:
        return []


def get_pending_faculty_attention(limit=5):
    """Oldest-waiting pending Faculty signups for the admin bell feed.

    Args:
        limit: Maximum rows to return.

    Returns:
        List of (user_id, full_name, created_at) tuples.
    """
    try:
        return db.fetch_all(
            '''SELECT u.user_id, u.full_name, u.created_at
               FROM user_accounts u
               JOIN roles r ON u.role_id = r.role_id
               WHERE u.account_status = 'pending' AND r.role_name = 'Faculty'
               ORDER BY u.created_at ASC
               LIMIT %s''',
            (limit,)) or []
    except Exception:
        return []


def get_system_error_attention(limit=5):
    """Newest 500-handler audit rows for the admin bell feed.

    Args:
        limit: Maximum rows to return.

    Returns:
        List of (log_id, activity, log_timestamp) tuples, newest first.
    """
    try:
        return db.fetch_all(
            '''SELECT log_id, activity, log_timestamp
               FROM audit_trail
               WHERE activity LIKE 'system:error%'
               ORDER BY log_id DESC
               LIMIT %s''',
            (limit,)) or []
    except Exception:
        return []


def get_role_attention_counts(role):
    """Uncapped role attention counts behind the staff bell badge.

    Librarian: pending-review requests, waiting reservations, overdue
    loans, unpaid fines, low-stock titles, and member-cancelled
    requests (last 30 days). Admin: all of the librarian counts plus
    pending faculty signups and system errors — the same sources the
    role's bell feed lists, so badge math can never disagree with card
    counts in kind. Every piece fails open to 0; role is a fixed
    internal value ('Librarian'/'Admin'), never user input.

    Args:
        role: Role name from the logged-in account.

    Returns:
        Dict with keys pending, waiting, overdue, fines, low_stock,
        cancelled, faculty_pending, system_errors, and total (the
        admin-inclusive sum for that role).
    """
    try:
        from app.settings.models import get_low_stock_threshold
        threshold = get_low_stock_threshold()
    except Exception:
        threshold = 2
    counts = {'pending': 0, 'waiting': 0, 'overdue': 0, 'fines': 0,
              'low_stock': 0, 'cancelled': 0, 'faculty_pending': 0,
              'system_errors': 0}
    try:
        pending, waiting = get_staff_attention_counts()
        counts['pending'] = int(pending or 0)
        counts['waiting'] = int(waiting or 0)
    except Exception:
        pass
    try:
        counts['overdue'] = count_overdue_loans()
    except Exception:
        pass
    try:
        counts['fines'] = count_unpaid_fines()
    except Exception:
        pass
    try:
        counts['low_stock'] = count_low_stock_titles(threshold)
    except Exception:
        pass
    try:
        counts['cancelled'] = count_recent_cancelled_requests()
    except Exception:
        pass
    counts['total'] = (counts['pending'] + counts['waiting']
                       + counts['overdue'] + counts['fines']
                       + counts['low_stock'] + counts['cancelled'])
    if role == 'Admin':
        try:
            counts['faculty_pending'] = count_pending_faculty()
        except Exception:
            pass
        try:
            counts['system_errors'] = count_system_errors()
        except Exception:
            pass
        counts['total'] += (counts['faculty_pending']
                            + counts['system_errors'])
    return counts


def count_open_procurement():
    """Procurement items not yet delivered (for ordering + ordered).

    Counts rows in the for_ordering and ordered procurement buckets via
    get_procurement_items, giving the dashboard the number of titles
    still in the acquisition pipeline.

    Args:
        None.

    Returns:
        Integer total of for_ordering plus ordered procurement items.
    """
    return len(get_procurement_items('for_ordering') or []) + \
        len(get_procurement_items('ordered') or [])


def get_attention_summary():
    """Action-needed counts for the dashboard attention panel.

    Combines circulation stats (overdue and due-soon loans) with pending
    user approvals and waiting reservations, so librarians see every
    queue needing action in one panel without extra queries per card.

    Args:
        None.

    Returns:
        Dict with overdue_items, due_soon, pending_users, and
        waiting_reservations integer counts.
    """
    circ = get_circulation_stats()
    return {
        'overdue_items': circ.get('overdue_items', 0),
        'due_soon': circ.get('due_in_days', 0),
        'pending_users': len(get_pending_users() or []),
        'waiting_reservations': count_waiting_reservations(),
    }


def get_admin_overview_stats():
    """Governance-focused counts for the admin System Overview.

    Cached per _cached_stats (60s TTL); see _get_admin_overview_stats.
    Unlike get_dashboard_stats (circulation-focused for librarians),
    this answers: how many accounts exist, who is waiting for approval,
    and how is staff distributed. Backup health is rendered separately
    from backup_log so this stays cheap to mock and test.

    Args:
        None.

    Returns:
        Dict with total_users, pending_users, active_librarians,
        active_faculty, active_students, active_admins, total_collection,
        total_titles, and total_accessions counts.
    """
    return _cached_stats('admin_overview', _get_admin_overview_stats)


def _get_admin_overview_stats():
    """Uncached admin overview counts (see get_admin_overview_stats).

    Counts total and pending users, groups active users by role, and
    counts active titles plus active accessions. Called only through
    get_admin_overview_stats so results are cached for 60s.

    Args:
        None.

    Returns:
        Dict with total_users, pending_users, active_librarians,
        active_faculty, active_students, active_admins, total_collection,
        total_titles, and total_accessions counts.
    """
    from app.auth.models import (
        count_active_users_by_role,
        count_pending_users,
        count_total_users,
    )

    total = count_total_users()
    pending = count_pending_users()
    by_role_rows = count_active_users_by_role() or []
    by_role = {}
    for row in by_role_rows:
        try:
            by_role[row[0]] = int(row[1] or 0)
        except (IndexError, TypeError, ValueError):
            continue
    collection = db.fetch_one(
        "SELECT COUNT(*) FROM book_catalog WHERE catalog_status = 'active'"
    )
    accessions = db.fetch_one(
        '''SELECT COUNT(*) FROM accession_log a
           JOIN book_catalog b ON a.book_id = b.book_id
           WHERE b.catalog_status = 'active' '''
    )
    total_titles = collection[0] if collection else 0
    total_accessions = accessions[0] if accessions else 0
    return {
        'total_users': total,
        'pending_users': pending,
        'active_librarians': by_role.get('Librarian', 0),
        'active_faculty': by_role.get('Faculty', 0),
        'active_students': by_role.get('Student', 0),
        'active_admins': by_role.get('Admin', 0),
        'total_collection': total_titles,
        'total_titles': total_titles,
        'total_accessions': total_accessions,
    }


def get_recent_activity(limit=5):
    """Fetch recent borrow/return activity for the dashboard feed.

    Joins circulation_records to book_catalog, borrowers, and
    user_accounts to resolve who did what to which title, ordered by the
    latest return or borrow date. Powers the librarian dashboard feed.

    Args:
        limit: Maximum rows to return (defaults to 5).

    Returns:
        List of positional tuples (full_name, user_id, action, title,
        borrow_date, return_date, due_date) ordered newest first.
    """
    return db.fetch_all(
        '''SELECT u.full_name, u.user_id,
                  CASE WHEN c.transaction_type = 'borrow' THEN 'Borrowed' ELSE 'Returned' END AS action,
                  b.title, c.borrow_date, c.return_date, c.due_date
           FROM circulation_records c
           JOIN book_catalog b ON c.book_id = b.book_id
           JOIN borrowers br ON c.borrower_id = br.borrower_id
           JOIN user_accounts u ON br.user_id = u.user_id
           ORDER BY COALESCE(c.return_date, c.borrow_date) DESC
           LIMIT %s''',
        (limit,)
    )


def get_daily_borrows(days=6):
    """Fetch per-day borrow counts for the trailing window chart.

    Aggregates borrow transactions by date over the last days window,
    then zero-fills quiet days so the dashboard axis always spans the
    full trailing period. Clamps days to 1-31 and tolerates DATE,
    datetime, and ISO-string day keys from mocks. Anchored to the PHT
    library calendar: borrow_date rows hold naive PHT dates, while
    Render's Postgres CURRENT_DATE and the host clock are UTC.

    Args:
        days: Trailing window length in days (defaults to 6, max 31).

    Returns:
        List of (day_date, borrow_count) tuples oldest-first, one per
        day in the window.
    """
    from datetime import timedelta
    from app.settings.models import library_today
    try:
        days = int(days)
    except (TypeError, ValueError):
        days = 6
    days = max(1, min(days, 31))
    # PHT wall clock (Asia/Manila): the SQL cutoff is a bound date so
    # Postgres's UTC CURRENT_DATE cannot drift the trailing window.
    today = library_today()
    rows = db.fetch_all(
        '''SELECT DATE(borrow_date) AS d, COUNT(*) AS cnt
           FROM circulation_records
           WHERE transaction_type = 'borrow'
             AND borrow_date >= %s
           GROUP BY DATE(borrow_date)
           ORDER BY d''',
        (today - timedelta(days=days - 1),)
    )
    if not rows:
        return []
    # Zero-fill quiet days so the axis always spans the trailing window.
    # Keys tolerate DATEs, datetimes, and ISO strings (mocked/test rows).
    by_day = {}
    for row in rows or []:
        try:
            key = row[0].isoformat()[:10] if hasattr(row[0], 'isoformat') else str(row[0])[:10]
            by_day[key] = by_day.get(key, 0) + int(row[1] or 0)
        except (IndexError, TypeError, ValueError):
            continue
    filled = []
    for back in range(days - 1, -1, -1):
        day = today - timedelta(days=back)
        filled.append((day, by_day.get(day.isoformat(), 0)))
    return filled


def get_tutorial_progress(user_id, tutorial_key, tutorial_version):
    """Return one member's saved optional-tutorial status, if any."""
    return db.fetch_one(
        '''SELECT status
           FROM tutorial_progress
           WHERE user_id = %s AND tutorial_key = %s AND tutorial_version <= %s
           ORDER BY tutorial_version DESC LIMIT 1''',
        (user_id, tutorial_key, tutorial_version),
    )


def save_tutorial_progress(user_id, tutorial_key, tutorial_version, status):
    """Record that a member dismissed or completed an optional tutorial."""
    return db.execute(
        '''INSERT INTO tutorial_progress (user_id, tutorial_key, tutorial_version, status)
           VALUES (%s, %s, %s, %s)
           ON CONFLICT (user_id, tutorial_key, tutorial_version)
           DO UPDATE SET status = EXCLUDED.status, updated_at = NOW()''',
        (user_id, tutorial_key, tutorial_version, status),
    )
