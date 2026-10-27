from app.database import db
from app.auth.models import get_pending_users
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
        "SELECT COUNT(*) FROM circulation_records WHERE transaction_type = 'borrow' AND transaction_status IN ('active', 'overdue') AND due_date::date < CURRENT_DATE"
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
    datetime, and ISO-string day keys from mocks.

    Args:
        days: Trailing window length in days (defaults to 6, max 31).

    Returns:
        List of (day_date, borrow_count) tuples oldest-first, one per
        day in the window.
    """
    from datetime import date, timedelta
    try:
        days = int(days)
    except (TypeError, ValueError):
        days = 6
    days = max(1, min(days, 31))
    rows = db.fetch_all(
        '''SELECT DATE(borrow_date) AS d, COUNT(*) AS cnt
           FROM circulation_records
           WHERE transaction_type = 'borrow'
             AND borrow_date >= CURRENT_DATE - INTERVAL '%s days'
           GROUP BY DATE(borrow_date)
           ORDER BY d''',
        (days,)
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
    today = date.today()
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
           WHERE user_id = %s AND tutorial_key = %s AND tutorial_version = %s''',
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
