from flask import render_template, redirect, url_for, jsonify, request, flash, current_app
from datetime import date, datetime
from flask_login import login_required, current_user
from . import main_bp
from .models import (get_dashboard_stats, get_recent_activity, get_daily_borrows,
                     get_attention_summary, get_admin_overview_stats,
                     get_tutorial_progress, save_tutorial_progress)
from app.cataloging.models import get_recent_books, suggest_book_values, suggest_books_rich, get_book_by_title_author_isbn, get_accession_by_number
from app.auth.decorators import librarian_required, admin_required
from app.settings.models import library_today

SUGGEST_FIELDS = {
    'book_title', 'book_author', 'book_publisher', 'book_subject',
    'book_isbn', 'book_search', 'student_program',
}
TUTORIAL_KEY = 'member-basics'
TUTORIAL_VERSION = 1


@main_bp.route('/tutorials/example/<kind>')
@login_required
def tutorial_example(kind):
    """Return safe catalog/detail URLs for a real tutorial example."""
    if kind not in ('borrow', 'ebook'):
        return jsonify({'error': 'Unknown guide.'}), 400
    from .models import get_tutorial_book
    book = get_tutorial_book(kind == 'ebook', current_user.id)
    if not book:
        return jsonify({'error': 'No suitable book is currently available for this guide.'}), 404
    return jsonify({
        'book_id': book[0],
        'catalog_url': url_for('cataloging.public_catalog', q=book[1], field='title', view='grid'),
        'book_url': url_for('cataloging.book_info', book_id=book[0]),
    })
BOOK_FIELD_MAP = {
    'book_title': 'title', 'book_author': 'author', 'book_publisher': 'publisher',
    'book_subject': 'subject', 'book_isbn': 'isbn', 'book_search': 'search',
}


def _safe_next(default_endpoint):
    """Return a validated redirect target for user-supplied `next`.

    Only same-origin relative paths (single leading `/`, no scheme or
    host) are honored; anything else falls back to `default_endpoint`.
    Guards POST-then-redirect handlers against open redirects.
    """
    from urllib.parse import urlparse
    fallback = url_for(default_endpoint)
    nxt = request.form.get('next') or request.args.get('next')
    if not nxt:
        return fallback
    parsed = urlparse(nxt)
    if parsed.scheme or parsed.netloc:
        return fallback
    # Backslashes are treated as slashes by browsers (open-redirect
    # bypass like /\\evil.com), so reject them outright.
    if '\\' in nxt:
        return fallback
    if not nxt.startswith('/') or nxt.startswith('//'):
        return fallback
    return nxt


@main_bp.route('/tutorials/status')
@login_required
def tutorial_status():
    """Return the current member guide status for the client-side overlay."""
    if current_user.role not in ('Student', 'Faculty'):
        return jsonify({'available': False})
    progress = get_tutorial_progress(current_user.id, TUTORIAL_KEY, TUTORIAL_VERSION)
    return jsonify({
        'available': True,
        'status': progress[0] if progress else None,
        'version': TUTORIAL_VERSION,
    })


@main_bp.route('/tutorials/progress', methods=['POST'])
@login_required
def tutorial_progress():
    """Persist an optional guide dismissal or completion without a redirect."""
    if current_user.role not in ('Student', 'Faculty'):
        return jsonify({'error': 'Tutorials are not available for this role.'}), 403
    status = request.get_json(silent=True) or {}
    state = status.get('status')
    if state not in ('dismissed', 'completed'):
        return jsonify({'error': 'Invalid tutorial status.'}), 400
    save_tutorial_progress(current_user.id, TUTORIAL_KEY, TUTORIAL_VERSION, state)
    return jsonify({'status': state})


def _safe_departments(dept_type):
    """Fetch program/department vocab tolerating DB failures.
    Wraps get_departments so a database error degrades to an empty list
    instead of breaking the profile page render. Used for the profile
    program and department dropdowns.
    Args:
        dept_type: Vocab type string ('program' or 'department').
    Returns:
        List of vocab rows, or empty list when unavailable.
    """
    try:
        from app.auth.models import get_departments
        return get_departments(dept_type) or []
    except Exception:
        return []


def _coerce_due_day(due):
    """Coerce a due-date value (date/datetime/ISO string) to a date.

    Returns None when the value is missing or unparseable so callers
    degrade gracefully instead of 500ing on malformed rows.
    """
    if due is None:
        return None
    if isinstance(due, datetime):
        return due.date()
    if isinstance(due, date):
        return due
    if isinstance(due, str):
        try:
            return datetime.fromisoformat(due).date()
        except ValueError:
            pass
        try:
            return datetime.strptime(due[:10], '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return None
    if hasattr(due, 'timetuple'):
        try:
            return date(due.year, due.month, due.day)
        except Exception:
            return None
    return None


def _overdue_loan_ids(loans, today, id_idx=0, due_idx=2, status_idx=4):
    """Ids of loans that are flagged 'overdue' or active-but-past-due.

    The DB never flips circulation status to 'overdue' on its own, so
    date-past-due active loans must also render as Overdue. Short or
    malformed rows are skipped, never fatal.
    """
    overdue = set()
    for loan in loans or []:
        try:
            if len(loan) <= status_idx:
                continue
            status = loan[status_idx]
            if status == 'overdue':
                overdue.add(loan[id_idx])
            elif status == 'active':
                due_day = _coerce_due_day(loan[due_idx] if len(loan) > due_idx else None)
                if due_day is not None and due_day < today:
                    overdue.add(loan[id_idx])
        except Exception:
            continue
    return overdue


@main_bp.route('/')
def index():
    """Render the public landing page (GET /, no login).
    Public endpoint with no RBAC guard. Fetches five recent books for the
    new-arrivals section and renders the homepage. Notifications arrive
    via global live toast popups; read-only with no audit row.
    Args:
        None.
    Returns:
        Rendered public/index.html with new arrivals.
    """
    new_arrivals = get_recent_books(5)
    try:
        from app.cataloging.models import get_distinct_material_types
        rows = get_distinct_material_types() or []
    except Exception:
        rows = []
    book_types = []
    for row in rows:
        try:
            name = row[0]
            count = int(row[1]) if len(row) > 1 else 0
        except (IndexError, TypeError, ValueError):
            continue
        if name:
            book_types.append((name, count))
    # Open/closed banner state from Library Hours + Operations Schedule
    # settings; fails open (always "Open") if anything is unconfigured.
    try:
        from app.settings.models import library_open_status
        open_status = library_open_status()
    except Exception:
        open_status = {'open': True, 'message': 'Open now',
                       'hours_label': None}
    return render_template('public/index.html', new_arrivals=new_arrivals,
                           book_types=book_types, open_status=open_status)


@main_bp.route('/health')
def health():
    """Liveness probe for Render/uptime monitors. No auth, no DB."""
    return jsonify({'status': 'ok'}), 200


@main_bp.route('/health/db')
def health_db():
    """Deep DB check (internal monitors only). Cheap SELECT 1 via the pool.

    Keep Render's healthCheckPath on /health — a transient DB blip must
    not restart a healthy web process. Point external uptime monitors
    here to distinguish 'web down' from 'DB unreachable'.
    """
    try:
        from app.database import db
        db.execute('SELECT 1')
        return jsonify({'status': 'ok', 'db': 'up'}), 200
    except Exception as e:
        current_app.logger.warning('health/db DB check failed: %s', e)
        return jsonify({'status': 'degraded', 'db': 'down'}), 503


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Redirect the legacy dashboard URL to the user profile.
    Requires login with no role restriction. Kept so old bookmarks and
    role guards landing on /dashboard forward to /user/profile instead
    of 404ing. Writes no audit row.
    Args:
        None.
    Returns:
        Redirect to the user profile page.
    """
    return redirect(url_for('main.user_profile'))


@main_bp.route('/user/profile')
@login_required
def user_profile():
    """Render the signed-in user's profile hub (GET, any login).
    Requires login with no role restriction. Loads user, profile, loans
    with overdue flags, borrow limits, allocated pickups, requests,
    notifications with auto-generated due-soon and overdue reminders,
    and fines, plus program/department vocab. Read-only aside from
    reminder notification writes.
    Args:
        None.
    Returns:
        Rendered users/user_profile.html with loans and notifications.
    """
    from app.auth.models import get_user_by_id, get_profile_by_user
    from app.circulation.models import (
        get_borrower_by_user, get_loans_by_borrower, count_active_loans,
        get_reservations_by_borrower, get_notifications_by_borrower,
        count_unread_notifications, get_fines_by_borrower, get_total_fines,
        create_notification, notification_exists, expire_overdue_reservations,
        format_due,
    )
    from app.requests.models import get_requests_by_borrower

    user_data = get_user_by_id(current_user.id)
    try:
        profile = get_profile_by_user(current_user.id)
    except Exception:
        profile = None

    borrower = get_borrower_by_user(current_user.id)
    loans = []
    overdue_ids = set()
    overdue_count = 0
    active_count = 0
    borrow_limit = 0
    pickups = []
    my_requests = []
    notifications = []
    unread_count = 0
    fines = []
    total_fines = 0

    if borrower:
        borrower_id = borrower[0]
        try:
            expire_overdue_reservations()
        except Exception:
            current_app.logger.warning('expire_overdue_reservations failed', exc_info=True)
        loans = get_loans_by_borrower(borrower_id) or []
        # PHT library calendar: due_date rows hold naive PHT values, so
        # date-past-due math uses library_today() (Asia/Manila), not the
        # host clock (UTC on Render).
        today = library_today()
        overdue_ids = _overdue_loan_ids(loans, today)
        overdue_count = sum(1 for loan in loans if len(loan) > 0 and loan[0] in overdue_ids)
        try:
            active_count = count_active_loans(borrower_id)
        except Exception:
            active_count = len(loans)
        try:
            overdue_count = min(overdue_count, int(active_count))
        except (TypeError, ValueError):
            pass

        role_name = user_data[2] if user_data else ''
        # Only Students get the student limit; Faculty, Admin, and
        # Librarian all inherit the faculty limit (mirrors
        # circulation._borrow_limit).
        if role_name == 'Student':
            borrow_limit = current_app.config.get('MAX_BORROW_LIMIT_STUDENT', 3)
        else:
            borrow_limit = current_app.config.get('MAX_BORROW_LIMIT_FACULTY', 5)

        try:
            reservations = get_reservations_by_borrower(borrower_id) or []
        except Exception:
            reservations = []
        pickups = [r for r in reservations if len(r) > 2 and r[2] == 'allocated']
        borrowing_requests = [r for r in reservations if len(r) > 2 and r[2] in ('waiting', 'allocated')]

        try:
            my_requests = get_requests_by_borrower(borrower_id) or []
        except Exception:
            my_requests = []
        try:
            notifications = get_notifications_by_borrower(borrower_id) or []
        except Exception:
            notifications = []
        # The badge is recomputed after the reminders below are generated
        # so a due-soon reminder minted by this request is counted too.
        try:
            fines = get_fines_by_borrower(borrower_id) or []
            total_fines = get_total_fines(borrower_id) or 0
        except Exception:
            fines = []
            total_fines = 0

        # Auto-generate due-soon / overdue reminders (once per day per loan).
        try:
            due_soon_days = int(current_app.config.get('DUE_SOON_NOTIFY_DAYS', 2))
        except (TypeError, ValueError):
            due_soon_days = 2
        for loan in loans:
            try:
                circ_id = loan[0]
                due = loan[2] if len(loan) > 2 else None
                status = loan[4] if len(loan) > 4 else ''
                title = loan[5] if len(loan) > 5 else f'loan #{circ_id}'
                if isinstance(due, str):
                    try:
                        due = datetime.fromisoformat(due).date()
                    except ValueError:
                        continue
                if not hasattr(due, 'timetuple'):
                    continue
                due_day = due.date() if isinstance(due, datetime) else due
                delta = (due_day - library_today()).days
                if status == 'overdue' or delta < 0:
                    if not notification_exists(borrower_id, 'overdue_reminder', str(circ_id)):
                        create_notification(
                            borrower_id,
                            f'Overdue: "{title}" was due {format_due(due)}. Please return it to avoid further fines.',
                            'overdue_reminder',
                            str(circ_id),
                        )
                elif 0 <= delta <= due_soon_days:
                    if not notification_exists(borrower_id, 'due_soon', str(circ_id)):
                        create_notification(
                            borrower_id,
                            f'Reminder: "{title}" is due {format_due(due)} (in {delta} day(s)).',
                            'due_soon',
                            str(circ_id),
                        )
            except Exception:
                continue
        try:
            unread_count = _badge_count(current_user.id, borrower_id,
                                        getattr(current_user, 'role', '') or '')
        except Exception:
            unread_count = 0
    else:
        borrowing_requests = []
        # Staff without a borrower record still carry the attention
        # badge (role counts; no personal rows to read).
        try:
            unread_count = _badge_count(current_user.id, None,
                                        getattr(current_user, 'role', '') or '')
        except Exception:
            unread_count = 0

    return render_template('users/user_profile.html', user_data=user_data,
                           profile=profile,
                           loans=loans, overdue_count=overdue_count,
                           overdue_ids=overdue_ids,
                           active_count=active_count, borrow_limit=borrow_limit,
                           pickups=pickups, my_requests=my_requests,
                           borrowing_requests=borrowing_requests,
                           notifications=notifications, unread_count=unread_count,
                           fines=fines, total_fines=total_fines,
                           programs=_safe_departments('program'),
                           departments=_safe_departments('department'))


@main_bp.route('/user/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update the signed-in user's own profile (POST, any login).
    Requires login with no role restriction. Validates full name, phone,
    and controlled-vocabulary department (ID numbers are immutable),
    updates via update_own_profile, logs profile:update, flashes the
    outcome, and redirects to the profile page (Post/Redirect/Get).
    Args:
        None (reads `full_name`, `phone_number`, `department` forms).
    Returns:
        Redirect to the user profile page with a flash message.
    """
    import re
    from app.auth.models import get_profile_by_user, update_own_profile, log_activity, is_valid_department, is_valid_any_department

    full_name = request.form.get('full_name', '').strip()
    phone_number = request.form.get('phone_number', '').strip() or None
    department = request.form.get('department', '').strip() or None

    if request.form.get('id_number', '').strip():
        if getattr(current_user, 'role', '') in ('Librarian', 'Admin'):
            flash('ID number cannot be changed. Contact the system administrator for ID corrections.', 'error')
        else:
            flash('ID number cannot be changed. Contact the librarian for ID corrections.', 'error')
        return redirect(url_for('main.user_profile'))

    if not full_name:
        flash('Full name is required.', 'error')
        return redirect(url_for('main.user_profile'))

    if len(full_name) > 150:
        flash('Full name is too long (max 150 characters).', 'error')
        return redirect(url_for('main.user_profile'))

    if phone_number and not re.fullmatch(r'[+\d][\d\s\-()]{6,19}', phone_number):
        flash('Invalid phone number format.', 'error')
        return redirect(url_for('main.user_profile'))

    if department and len(department) > 100:
        flash('Department name is too long (max 100 characters).', 'error')
        return redirect(url_for('main.user_profile'))

    try:
        profile = get_profile_by_user(current_user.id)
    except Exception:
        profile = None
    if profile is None:
        flash('Profile not found.', 'error')
        return redirect(url_for('main.user_profile'))

    role_name = profile[2] if len(profile) > 2 else None
    current_dept = profile[6] if len(profile) > 6 else None
    has_borrower = len(profile) > 4 and profile[4] is not None
    if has_borrower and department != current_dept:
        if role_name in ('Student', 'Faculty'):
            dept_type = 'program' if role_name == 'Student' else 'department'
            valid = bool(department) and is_valid_department(department, dept_type)
        else:
            # Staff with a borrower record: accept any active vocab entry.
            valid = bool(department) and is_valid_any_department(department)
        if not valid:
            flash('Please select a valid program/department from the list.', 'error')
            return redirect(url_for('main.user_profile'))

    try:
        update_own_profile(current_user.id, full_name, phone_number, department)
    except Exception:
        current_app.logger.exception('Profile update failed for user %s', current_user.id)
        flash('Profile update failed. Please try again.', 'error')
        return redirect(url_for('main.user_profile'))
    log_activity(current_user.id, 'profile:update')
    flash('Profile updated.', 'success')
    return redirect(url_for('main.user_profile'))


@main_bp.route('/user/notifications')
@login_required
def user_notifications():
    """Render the user's paginated notifications (GET, any login).
    Requires login with no role restriction. Loads all borrower
    notifications plus the unread count, slices 10 per page with clamped
    pagination, and renders the list. Read-only; writes no audit row.
    Args:
        None (reads optional `page` query arg).
    Returns:
        Rendered users/user_notifications.html with page slice and counts.
    """
    from app.circulation.models import (
        get_borrower_by_user, get_notifications_by_borrower, count_unread_notifications
    )
    NOTIFICATIONS_PER_PAGE = 10
    try:
        page = int(request.args.get('page', 1))
    except (TypeError, ValueError):
        page = 1
    if page < 1:
        page = 1
    notifications = []
    unread_count = 0
    total = 0
    total_pages = 1
    borrower = get_borrower_by_user(current_user.id)
    if borrower:
        try:
            all_notifications = get_notifications_by_borrower(borrower[0]) or []
        except Exception:
            all_notifications = []
        try:
            unread_count = _badge_count(
                current_user.id, borrower[0],
                getattr(current_user, 'role', '') or '')
        except Exception:
            unread_count = 0
        total = len(all_notifications)
        total_pages = max(1, (total + NOTIFICATIONS_PER_PAGE - 1) // NOTIFICATIONS_PER_PAGE)
        if page > total_pages:
            page = total_pages
        start = (page - 1) * NOTIFICATIONS_PER_PAGE
        notifications = all_notifications[start:start + NOTIFICATIONS_PER_PAGE]
    return render_template('users/user_notifications.html',
                           notifications=notifications, unread_count=unread_count,
                           page=page, total_pages=total_pages, total=total)


@main_bp.route('/user/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read_route(notification_id):
    """Mark one notification as read (POST, any login).
    Requires login with no role restriction. Scopes the write to the
    caller's borrower row via mark_notification_read, logs
    notifications:read:<id>, and returns JSON unread counts for AJAX or
    a safe-next redirect otherwise.
    Args:
        notification_id: Primary key of the notification to mark read.
    Returns:
        JSON read payload for AJAX, else redirect with flash handling.
    """
    from app.circulation.models import get_borrower_by_user, mark_notification_read
    from app.auth.models import log_activity
    borrower = get_borrower_by_user(current_user.id)
    if not borrower:
        if _wants_json():
            return jsonify({'error': 'No borrower record found.'}), 404
        flash('No borrower record found.', 'error')
        return redirect(url_for('main.user_profile'))
    mark_notification_read(notification_id, borrower[0], updated_by=current_user.id)
    log_activity(current_user.id, f'notifications:read:{notification_id}')
    if _wants_json():
        # Same formula as the badge on every page surface (unread
        # personal notifications plus staff attention counts).
        return jsonify({'read': notification_id,
                        'unread_count': _badge_count(
                            current_user.id, borrower[0],
                            getattr(current_user, 'role', '') or '')})
    return redirect(_safe_next('main.user_profile'))


@main_bp.route('/user/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications_read_route():
    """Mark all borrower notifications as read (POST, any login).
    Requires login with no role restriction. Marks every notification
    for the caller's borrower row via mark_all_notifications_read, logs
    notifications:read_all, and returns JSON for AJAX or flashes plus a
    safe-next redirect otherwise.
    Args:
        None.
    Returns:
        JSON read_all payload for AJAX, else redirect with a flash.
    """
    from app.circulation.models import get_borrower_by_user, mark_all_notifications_read
    from app.auth.models import log_activity
    borrower = get_borrower_by_user(current_user.id)
    if not borrower:
        if _wants_json():
            return jsonify({'error': 'No borrower record found.'}), 404
        flash('No borrower record found.', 'error')
        return redirect(url_for('main.user_profile'))
    mark_all_notifications_read(borrower[0], updated_by=current_user.id)
    log_activity(current_user.id, 'notifications:read_all')
    if _wants_json():
        # Same formula as every badge surface: after read-all this is
        # just the staff attention counts (0 for members).
        return jsonify({'read_all': True,
                        'unread_count': _badge_count(
                            current_user.id, borrower[0],
                            getattr(current_user, 'role', '') or '')})
    flash('All notifications marked as read.', 'success')
    return redirect(_safe_next('main.user_profile'))


def _wants_json():
    """True when the client asked for JSON (AJAX) instead of PRG redirect."""
    return 'application/json' in (request.headers.get('Accept') or '')


@main_bp.route('/user/history')
@login_required
def user_history():
    """Render the user's tabbed history (GET, any login).
    Requires login with no role restriction. Parses tab (borrowing,
    fines, reservations, requests) and page args, sweeps expired
    allocations, loads each history list with per-list counts, paginates
    10 per page, flags date-past-due loans as overdue, and renders the
    active tab. Read-only.
    Args:
        None (reads `tab` and `page` query args).
    Returns:
        Rendered users/user_history.html with tab records and counts.
    """
    from app.circulation.models import (
        get_borrower_by_user, get_user_loan_history,
        get_reservation_history_by_borrower, get_fines_by_borrower,
        get_total_fines,
        expire_overdue_reservations,
    )
    from app.requests.models import get_requests_by_borrower

    HISTORY_TABS = ('borrowing', 'fines', 'reservations', 'requests')
    HISTORY_PER_PAGE = 10
    tab = request.args.get('tab', 'borrowing').strip().lower()
    if tab not in HISTORY_TABS:
        tab = 'borrowing'
    try:
        page = int(request.args.get('page', 1))
    except (TypeError, ValueError):
        page = 1
    if page < 1:
        page = 1

    transactions = []
    my_requests = []
    reservations = []
    fines = []
    total_fines = 0
    borrower = get_borrower_by_user(current_user.id)
    if borrower:
        try:
            expire_overdue_reservations()
        except Exception:
            current_app.logger.warning('expire_overdue_reservations failed', exc_info=True)
        try:
            transactions = get_user_loan_history(current_user.id) or []
        except Exception:
            transactions = []
        try:
            my_requests = get_requests_by_borrower(borrower[0]) or []
        except Exception:
            my_requests = []
        try:
            reservations = get_reservation_history_by_borrower(borrower[0]) or []
        except Exception:
            reservations = []
        try:
            fines = get_fines_by_borrower(borrower[0]) or []
            total_fines = get_total_fines(borrower[0]) or 0
        except Exception:
            fines = []
            total_fines = 0
    counts = {
        'borrowing': len(transactions),
        'fines': len(fines),
        'reservations': len(reservations),
        'requests': len(my_requests),
    }
    active_list = {
        'borrowing': transactions,
        'fines': fines,
        'reservations': reservations,
        'requests': my_requests,
    }[tab]
    total = len(active_list)
    total_pages = max(1, (total + HISTORY_PER_PAGE - 1) // HISTORY_PER_PAGE)
    if page > total_pages:
        page = total_pages
    start = (page - 1) * HISTORY_PER_PAGE
    records = active_list[start:start + HISTORY_PER_PAGE]
    # History rows carry status at index 5 (see get_user_loan_history);
    # flag date-past-due actives as overdue for the badge.
    overdue_ids = _overdue_loan_ids(transactions, library_today(), status_idx=5)
    return render_template('users/user_history.html',
                           tab=tab, page=page, total_pages=total_pages,
                           total=total, counts=counts, records=records,
                           total_fines=total_fines,
                           overdue_ids=overdue_ids)


def _badge_count(user_id, borrower_id, role):
    """Bell badge for an account — one formula for every surface.

    Members: unread personal notification_log rows. Librarian/Admin:
    the uncapped role attention counts (pending review requests,
    waiting reservations, overdue loans, unpaid fines, low-stock
    titles, recent member cancellations; Admin adds pending faculty
    signups and system errors), plus unread personal notification_log
    rows when the account also holds a borrower record. Each piece
    fails open to 0 so DB blips never break a render.

    Args:
        user_id: Flask-Login account id (for the unread subquery).
        borrower_id: Notification recipient's borrower FK, or None.
        role: Role name for the current user ('Librarian'/'Admin').

    Returns:
        Non-negative int badge count.
    """
    total = 0
    if role in ('Librarian', 'Admin'):
        try:
            from app.main.models import get_role_attention_counts
            counts = get_role_attention_counts(role)
            total += _int_count((counts or {}).get('total'))
        except Exception:
            pass
        try:
            from app.database import db as _db
            r = _db.fetch_one(
                'SELECT COUNT(*) FROM notification_log'
                ' WHERE is_read IS FALSE'
                ' AND recipient_id ='
                ' (SELECT borrower_id FROM borrowers'
                '  WHERE user_id = %s)', (user_id,))
            total += _int_count(r[0] if r else 0)
        except Exception:
            pass
        try:
            return max(0, int(total))
        except (TypeError, ValueError):
            return 0
    if borrower_id:
        try:
            from app.circulation.models import count_unread_notifications
            total = _int_count(count_unread_notifications(borrower_id))
        except Exception:
            pass
    return total


def _staff_feed_items():
    """Newest librarian desk attention items (newest-first across kinds):
    pending review requests, waiting reservations, overdue loans, unpaid
    fines, low-stock titles, member cancellations, recent circulation.
    Same rows get_role_attention_counts('Librarian') sums for the badge;
    fail-open to [] so a DB blip never breaks the bell panel. IDs are
    stable feed keys (req-<id>, res-<id>, overdue-<id>, fine-<id>,
    low-<id>, cancel-<id>, circ-<id>), not notification_log rows — staff
    dismiss them client-side since there is no persistent staff inbox."""
    items = []
    try:
        from app.database import db as _db
        reqs = _db.fetch_all(
            "SELECT request_id, book_title, request_date FROM request_records"
            " WHERE request_status = 'pending_review'"
            " ORDER BY request_date DESC LIMIT 5") or []
        for r in reqs:
            items.append({'id': f"req-{r[0]}",
                          'message': f"New book request: \"{r[1]}\" needs review.",
                          'type': 'staff_request', 'date': str(r[2])})
    except Exception:
        pass
    try:
        from app.database import db as _db2
        res = _db2.fetch_all(
            "SELECT reservation_id, book_id FROM reservation_queue"
            " WHERE reservation_status = 'waiting'"
            " ORDER BY request_date DESC LIMIT 5") or []
        for r in res:
            items.append({'id': f"res-{r[0]}",
                          'message': f"Reservation #{r[0]} waiting for a copy (book {r[1]}).",
                          'type': 'staff_reservation', 'date': ''})
    except Exception:
        pass
    try:
        from app.main.models import get_overdue_loan_attention
        for r in get_overdue_loan_attention():
            items.append({'id': f"overdue-{r[0]}",
                          'message': (f"\"{r[2]}\" is overdue for {r[1]}"
                                      f" (loan #{r[0]})."),
                          'type': 'staff_overdue',
                          'date': str(r[3]) if len(r) > 3 else ''})
    except Exception:
        pass
    try:
        from app.main.models import get_unpaid_fine_attention
        for r in get_unpaid_fine_attention():
            try:
                amount = f"₱{float(r[1]):.2f}"
            except (TypeError, ValueError):
                amount = '₱0.00'
            items.append({'id': f"fine-{r[0]}",
                          'message': (f"{amount} unpaid fine for {r[2]}"
                                      f" (\"{r[3]}\", loan #{r[0]})."),
                          'type': 'staff_fine', 'date': ''})
    except Exception:
        pass
    try:
        from app.settings.models import get_low_stock_threshold
        from app.main.models import get_low_stock_titles
        for r in get_low_stock_titles(get_low_stock_threshold()):
            try:
                avail = int(r[2])
            except (TypeError, ValueError):
                avail = 0
            items.append({'id': f"low-{r[0]}",
                          'message': (f"\"{r[1]}\" is low on copies"
                                      f" ({avail} available)."),
                          'type': 'staff_low_stock', 'date': ''})
    except Exception:
        pass
    try:
        from app.main.models import get_cancelled_request_attention
        for r in get_cancelled_request_attention():
            items.append({'id': f"cancel-{r[0]}",
                          'message': (f"Book request for \"{r[1]}\" was"
                                      " cancelled by a member."),
                          'type': 'staff_cancel',
                          'date': str(r[2]) if len(r) > 2 else ''})
    except Exception:
        pass
    try:
        from app.database import db as _db3
        recent = _db3.fetch_all(
            "SELECT circulation_id, transaction_type, borrow_date, return_date"
            " FROM circulation_records"
            " ORDER BY COALESCE(return_date, borrow_date) DESC, circulation_id DESC"
            " LIMIT 5") or []
        for r in recent:
            verb = 'returned' if (len(r) > 1 and r[1] == 'return') else 'borrowed'
            items.append({'id': f"circ-{r[0]}",
                          'message': f"Copy {verb} (loan #{r[0]}).",
                          'type': 'staff_circulation', 'date': ''})
    except Exception:
        pass
    return items


def _admin_feed_items():
    """Newest admin attention items on top of the librarian feed:
    pending Faculty signups, system errors (500-handler audit rows),
    and the newest audit-trail entries ("everything in audit"). IDs are
    stable feed keys (fac-<user_id>, syserr-<log_id>, audit-<log_id>);
    fail-open to [] like the librarian feed."""
    items = []
    try:
        from app.main.models import get_pending_faculty_attention
        for r in get_pending_faculty_attention():
            items.append({'id': f"fac-{r[0]}",
                          'message': (f"Faculty account for {r[1]} is pending"
                                      " approval."),
                          'type': 'staff_faculty',
                          'date': str(r[2]) if len(r) > 2 else ''})
    except Exception:
        pass
    try:
        from app.main.models import get_system_error_attention
        for r in get_system_error_attention():
            items.append({'id': f"syserr-{r[0]}",
                          'message': f"System error: {r[1]}.",
                          'type': 'staff_system_error',
                          'date': _notif_date_pht(r[2]) if len(r) > 2 else ''})
    except Exception:
        pass
    try:
        from app.auth.models import get_audit_logs
        for row in (get_audit_logs(limit=5, tab='all') or []):
            if len(row) > 4 and str(row[4]).startswith('system:error'):
                # already shown as its own System error card above
                continue
            items.append({'id': f"audit-{row[0]}",
                          'message': f"Audit: {row[1]} — {row[4]}.",
                          'type': 'staff_audit',
                          'date': _notif_date_pht(row[5]) if len(row) > 5 else ''})
    except Exception:
        pass
    return items


def _staff_feed(role):
    """Attention feed line-up for one staff role: the librarian desk
    feed plus — for Admin — the admin governance feed."""
    items = _staff_feed_items()
    if role == 'Admin':
        items = items + _admin_feed_items()
    return items


_ATTENTION_URLS = {
    'req-': ('requests.list_requests', {}),
    'cancel-': ('requests.list_requests', {}),
    'res-': ('circulation.reservations_page', {}),
    'circ-': ('circulation.circulation_page', {}),
    'overdue-': ('circulation.circulation_page', {}),
    'fine-': ('circulation.circulation_page', {}),
    'low-': ('inventory.inventory_page', {}),
    'fac-': ('auth.admin_users', {}),
    'syserr-': ('main.admin_audits', {'tab': 'system'}),
    'audit-': ('main.admin_audits', {}),
}

# Card id prefixes that represent actionable data (the kinds whose FULL
# table counts feed the bell badge). Context cards (recent circulation,
# audit trail) never increase the badge.
_BADGE_PREFIXES = ('req-', 'res-', 'overdue-', 'fine-', 'low-',
                   'cancel-', 'fac-', 'syserr-')


def _decorate_staff_items(items):
    """Fill url/badge/dismissible for raw staff feed dicts by id prefix.

    Mutates and returns the list: every card is dismissible (staff have
    no persistent inbox), url comes from _ATTENTION_URLS, and badge is
    True only for kinds counted by the badge formula.
    """
    from urllib.parse import urlencode
    for item in items or []:
        iid = str(item.get('id') or '')
        prefix = next((p for p in _ATTENTION_URLS if iid.startswith(p)), None)
        if prefix:
            endpoint, values = _ATTENTION_URLS[prefix]
            try:
                url = url_for(endpoint)
                if values:
                    url += '?' + urlencode(values)
            except Exception:
                url = ''
            item['url'] = url
        else:
            item['url'] = ''
        item['badge'] = iid.startswith(_BADGE_PREFIXES)
        item['dismissible'] = True
    return items or []


def _notif_date_pht(value):
    """Format a notification timestamp as 'YYYY-MM-DD hh:MM AM (PHT)'.

    Tolerates datetimes, ISO strings, and garbage (falls back to str).
    Naive values are library-wall-clock already, so +8h; aware values
    convert to Asia/Manila. Mirrors the `pht` template filter.
    """
    from datetime import datetime, timedelta, timezone
    dt = None
    if hasattr(value, 'strftime'):
        try:
            dt = value
        except Exception:
            return str(value)
    else:
        s = str(value or '')
        for parser in (
                lambda v: datetime.strptime(v[:19], '%Y-%m-%d %H:%M:%S'),
                lambda v: datetime.strptime(v[:10], '%Y-%m-%d')):
            try:
                dt = parser(s)
                break
            except (ValueError, TypeError):
                continue
        if dt is None:
            return s
    try:
        if dt.tzinfo is None:
            dt = dt + timedelta(hours=8)
        else:
            dt = dt.astimezone(timezone(timedelta(hours=8)))
    except Exception:
        pass
    try:
        return dt.strftime('%Y-%m-%d %I:%M %p') + ' (PHT)'
    except Exception:
        return str(value)


def _int_count(value):
    """Coerce a COUNT(*) result (or mock junk) to a non-negative int.

    Badge math reads aggregated counts from several queries; anything
    unreadable counts as 0 so the badge can never crash a render.
    """
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _staff_personal_notes(borrower_id, limit=None):
    """Personal inbox cards for a staff account that also borrows.

    Admin/Librarian accounts can hold a borrower record and receive
    member notifications (reservations, hold-ready, reminders) — the
    same rows /profile and /user/notifications show. Returns
    (cards, unread_count): cards are the same dicts the member bell
    branch renders (numeric ids, read state, deep-link url, not
    dismissible — they mark-as-read server-side), unread_count is an
    int badge contribution. Fail-open to ([], 0) so a DB blip never
    breaks the staff bell.

    Args:
        borrower_id: Notification recipient's borrower FK.
        limit: Optional cap on cards fetched (bell preview).

    Returns:
        Tuple (list of card dicts, int unread count).
    """
    cards, unread = [], 0
    try:
        from app.circulation.models import (
            get_notifications_by_borrower, count_unread_notifications,
        )
        rows = (get_notifications_by_borrower(borrower_id, limit=limit)
                if limit else get_notifications_by_borrower(borrower_id))
        cards = [
            {'id': n[0], 'message': n[1],
             'type': n[2] if len(n) > 2 else '',
             'date': _notif_date_pht(n[4]) if len(n) > 4 else '',
             'read': bool(n[5]) if len(n) > 5 else False,
             'url': _member_notif_url(n[2] if len(n) > 2 else '')}
            for n in (rows or []) if n and len(n) > 1
        ]
        unread = _int_count(count_unread_notifications(borrower_id))
    except Exception:
        pass
    return cards, unread


@main_bp.route('/api/notifications')
def notifications_feed():
    """Bell-panel payload for every role (GET, login).

    Members get their latest notification_log rows (read state
    included); staff get the live attention feed (dismissible,
    client-side) plus — when they also hold a borrower record — their
    personal notification_log rows, so the bell shows every notification
    addressed to that account on any page (matching /profile). Honors
    ?limit= (1-20, default 8) for the personal rows. Read-only; 401
    JSON when anonymous, 404 JSON for members without a borrower row.
    """
    from flask_login import current_user as _cu
    if not getattr(_cu, 'is_authenticated', False):
        return jsonify({'error': 'Login required.'}), 401
    try:
        limit = int(request.args.get('limit', 8))
    except (TypeError, ValueError):
        limit = 8
    limit = max(1, min(limit, 20))
    role = getattr(_cu, 'role', '') or ''
    try:
        from app.auth.models import get_user_by_id as _gu
        _u = _gu(_cu.id)
        if _u and len(_u) > 2 and _u[2]:
            role = _u[2]
    except Exception:
        pass
    if role in ('Librarian', 'Admin'):
        staff_items = _decorate_staff_items(_staff_feed(role))[:limit]
        # The bell is the user's inbox: personal notification_log rows
        # first (persistent, server-side mark-as-read), then the staff
        # attention feed. unread_count is the authoritative badge: the
        # header context processor's exact formula (_badge_count) —
        # uncapped role attention counts plus personal unread — so
        # client-side recounting of capped cards can't disagree with
        # /profile, which has no bell JS.
        borrower = None
        try:
            from app.circulation.models import get_borrower_by_user
            borrower = get_borrower_by_user(_cu.id)
        except Exception:
            borrower = None
        items = list(staff_items)
        try:
            unread_count = _badge_count(_cu.id,
                                        borrower[0] if borrower else None,
                                        role)
        except Exception:
            unread_count = 0
        if borrower:
            try:
                personal, _pu = _staff_personal_notes(borrower[0],
                                                      limit=limit)
                items = personal + staff_items
            except Exception:
                pass
        return jsonify({'unread_count': unread_count,
                        'notifications': items})
    from app.circulation.models import (
        get_borrower_by_user, get_notifications_by_borrower,
        count_unread_notifications,
    )
    borrower = get_borrower_by_user(_cu.id)
    if not borrower:
        return jsonify({'error': 'No borrower record.'}), 404
    try:
        all_notes = get_notifications_by_borrower(borrower[0], limit=limit) or []
    except Exception:
        all_notes = []
    try:
        unread_count = count_unread_notifications(borrower[0]) or 0
    except Exception:
        unread_count = 0
    return jsonify({
        'unread_count': unread_count,
        'notifications': [
            {'id': n[0], 'message': n[1],
             'type': n[2] if len(n) > 2 else '',
             'date': _notif_date_pht(n[4]) if len(n) > 4 else '',
             'read': bool(n[5]) if len(n) > 5 else False,
             'url': _member_notif_url(n[2] if len(n) > 2 else '')}
            for n in all_notes if n and len(n) > 1
        ],
    })


def _member_notif_url(notif_type):
    """Deep link for one member notification type.

    Clicking a bell-panel card lands on the page holding that item:
    requests on the request page, loans/fines/reservations on their
    history tabs, due items on the profile loan list.
    """
    kind = (notif_type or '')
    if kind == 'request_update':
        return url_for('requests.user_request_book')
    if kind in ('reservation', 'hold_ready'):
        return url_for('main.user_history', tab='reservations')
    if kind in ('borrow', 'return'):
        return url_for('main.user_history', tab='borrowing')
    if kind == 'fine':
        return url_for('main.user_history', tab='fines')
    if kind in ('overdue_reminder', 'due_soon'):
        return url_for('main.user_profile')
    return url_for('main.user_notifications')


@main_bp.route('/api/notifications/live')
def notifications_live():
    """Poll endpoint for in-site live toasts on every module (GET, login).

    Students/Faculty: unread borrower notifications (request approved,
    reservation allocated, due reminders) — no page reload needed.
    Librarian/Admin: their personal unread notifications plus the role
    attention feed (pending requests, waiting reservations, overdue
    loans, unpaid fines, low-stock titles, member cancellations; Admin
    adds pending faculty signups, system errors, and audit trail) so
    staff are notified while browsing any module. Read-only; 401 JSON
    when anonymous.
    """
    from flask_login import current_user as _cu
    if not getattr(_cu, 'is_authenticated', False):
        return jsonify({'error': 'Login required.'}), 401
    role = getattr(_cu, 'role', '') or ''
    try:
        from app.auth.models import get_user_by_id as _gu
        _u = _gu(_cu.id)
        if _u and len(_u) > 2 and _u[2]:
            role = _u[2]
    except Exception:
        pass
    if role in ('Librarian', 'Admin'):
        borrower = None
        try:
            from app.circulation.models import get_borrower_by_user
            borrower = get_borrower_by_user(_cu.id)
        except Exception:
            borrower = None
        items = _decorate_staff_items(_staff_feed(role))
        try:
            unread_count = _badge_count(_cu.id,
                                        borrower[0] if borrower else None,
                                        role)
        except Exception:
            unread_count = 0
        if borrower:
            try:
                personal, _pu = _staff_personal_notes(borrower[0])
                unseen = [p for p in personal if not p.get('read')] or personal[:5]
                items = unseen[:5] + items
            except Exception:
                pass
        return jsonify({'unread_count': unread_count,
                        'notifications': items[:5]})
    from app.circulation.models import (
        get_borrower_by_user, get_notifications_by_borrower,
        count_unread_notifications,
    )
    borrower = get_borrower_by_user(_cu.id)
    if not borrower:
        return jsonify({'error': 'No borrower record.'}), 404
    try:
        all_notes = get_notifications_by_borrower(borrower[0]) or []
    except Exception:
        all_notes = []
    unread = [n for n in all_notes if len(n) > 5 and not n[5]]
    if not unread:
        # fallback when is_read column missing/legacy shape
        try:
            unread = all_notes[:5]
        except Exception:
            unread = []
    latest = unread[:5]
    try:
        unread_count = count_unread_notifications(borrower[0]) or 0
    except Exception:
        unread_count = len(unread)
    return jsonify({
        'unread_count': unread_count,
        'notifications': [
            {'id': n[0], 'message': n[1], 'type': n[2] if len(n) > 2 else '',
             'date': str(n[4]) if len(n) > 4 else ''}
            for n in latest if n and len(n) > 1
        ],
    })


@main_bp.route('/api/bloom')
def bloom_filters():
    """Serve Bloom filter payloads for client-side negative checks.
    Public endpoint with no auth or DB access. Returns the registry's
    title, author, ISBN, and accession filters so catalog forms can warn
    instantly while the server remains authoritative. Read-only.
    Args:
        None.
    Returns:
        JSON mapping of Bloom filter payloads.
    """
    from app.bloom_registry import bloom_registry
    return jsonify(bloom_registry.get_payloads())


@main_bp.route('/api/suggestions')
def suggestions():
    """Return autocomplete suggestions (GET /api/suggestions, public).
    Public endpoint with no RBAC guard. Requires a known field and at
    least 2 query characters, then queries program vocab or book values;
    book_search also attaches rich title/author pairs. Empty input
    returns an empty list. Read-only with no audit row.
    Args:
        None (reads `field` and `q` query args).
    Returns:
        JSON with suggestions list and optional rich pairs.
    """
    field = request.args.get('field', '')
    q = request.args.get('q', '').strip()
    if field not in SUGGEST_FIELDS or len(q) < 2:
        return jsonify({'suggestions': []})
    if field == 'student_program':
        from app.auth.models import suggest_programs
        rows = suggest_programs(q)
    else:
        try:
            rows = suggest_book_values(BOOK_FIELD_MAP[field], q) or []
        except Exception:
            rows = []
    payload = {'suggestions': [row[0] for row in rows if row and row[0]]}
    if field == 'book_search':
        # Rich title/author pairs for the analytics-style dropdown
        # (bold title left, author right). Plain `suggestions` is kept
        # so existing clients keep working.
        try:
            rich_rows = suggest_books_rich(q) or []
        except Exception:
            rich_rows = []
        payload['rich'] = [
            {'title': r[0], 'author': r[1] if len(r) > 1 else ''}
            for r in rich_rows if r and r[0]
        ]
    return jsonify(payload)


@main_bp.route('/api/book-exists')
def book_exists():
    """Answer whether an exact title/author/ISBN title already exists.

    Public GET used by the add-book form's duplicate warning. Requires
    title and author query args (returns exists False without them);
    optional isbn narrows to the ISBN-bearing match. Returns JSON
    {exists: bool} via get_book_by_title_author_isbn.

    Returns:
        JSON response with the exists boolean.
    """
    title = request.args.get('title', '').strip()
    author = request.args.get('author', '').strip()
    if not title or not author:
        return jsonify({'exists': False})
    isbn = request.args.get('isbn', '').strip() or None
    return jsonify({'exists': bool(get_book_by_title_author_isbn(title, author, isbn))})


@main_bp.route('/api/accession-exists')
def accession_exists():
    """Answer whether a barcode accession number already exists.

    Public GET used by the accession form's duplicate warning. Returns
    exists False for a blank number, otherwise checks via
    get_accession_by_number. Returns JSON {exists: bool}.

    Returns:
        JSON response with the exists boolean.
    """
    accession_number = request.args.get('accession_number', '').strip()
    if not accession_number:
        return jsonify({'exists': False})
    return jsonify({'exists': bool(get_accession_by_number(accession_number))})


@main_bp.route('/librarian')
@login_required
@librarian_required
def librarian_dashboard():
    """Render the librarian dashboard with stats, activity, and trends.

    GET guarded by login + Librarian/Admin. Loads cached headline
    counts (get_dashboard_stats), the 5-row activity feed, 6-day borrow
    series, and the attention panel, then renders
    dashboard/dashboard.html with the librarian sidebar.

    Returns:
        Rendered librarian dashboard template response.
    """
    stats = get_dashboard_stats()
    activity = get_recent_activity(5)
    daily = get_daily_borrows(6)
    attention = get_attention_summary()
    return render_template('dashboard/dashboard.html', stats=stats,
                           activity=activity, daily=daily,
                           attention=attention,
                           sidebar='components/librarian_sidebar_nav.html')


@main_bp.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    """Render the admin System Overview with governance and backup health.

    GET guarded by login + Admin. Loads overview counts, the 5 newest
    pending signups plus total, the 8 newest audit rows, backup history
    (newest completed as last_backup, busy flag from the worker or an
    in_progress row), schedule config, and next run time, then renders
    dashboard/admin_overview.html with the admin sidebar.

    Returns:
        Rendered admin overview template response.
    """
    from app.auth.models import get_audit_logs, get_pending_users
    from app.backup.models import get_backup_logs
    from app.backup.scheduler import next_scheduled_backup
    from flask import current_app
    stats = get_admin_overview_stats()
    pending = get_pending_users() or []
    activity = get_audit_logs(limit=8) or []
    backups = get_backup_logs() or []
    completed = [b for b in backups if len(b) > 3 and b[3] == 'completed']
    last_backup = completed[0] if completed else None
    from app.backup import jobs as backup_jobs
    backup_busy = (backup_jobs.active_job() is not None
                   or any(len(b) > 3 and b[3] == 'in_progress' for b in backups))
    backup_day = current_app.config.get('BACKUP_DAY', 1)
    backup_hour = current_app.config.get('BACKUP_HOUR', 2)
    backup_keep = current_app.config.get('BACKUP_KEEP', 12)
    return render_template('dashboard/admin_overview.html', stats=stats,
                           pending=pending[:5],
                           pending_total=len(pending),
                           activity=activity,
                           last_backup=last_backup,
                           backup_count=len(completed),
                           backup_busy=backup_busy,
                           backup_schedule={'day': backup_day,
                                            'hour': backup_hour,
                                            'keep': backup_keep},
                           next_backup=next_scheduled_backup(backup_day,
                                                             backup_hour),
                           sidebar='components/admin_sidebar_nav.html')


@main_bp.route('/admin/audits')
@login_required
@admin_required
def admin_audits():
    """Render the admin Audit Logs table with filters and chart stats.

    GET guarded by login + Admin. Parses q/tab/limit query args
    (tab allowlisted to AUDIT_TABS, limit clamped 1-200), loads newest
    audit rows via get_audit_logs and chart aggregates via
    get_audit_stats (which never breaks the table on failure), then
    renders dashboard/admin_audits.html with the describe_activity
    presenter and admin sidebar.

    Returns:
        Rendered audit logs template response.
    """
    from app.auth.models import (AUDIT_TABS, describe_activity, get_audit_logs,
                                 get_audit_stats)
    search = (request.args.get('q', '') or '').strip()
    tab = (request.args.get('tab', '') or '').strip().lower()
    if tab not in AUDIT_TABS:
        tab = 'all'
    try:
        limit = int(request.args.get('limit', '50'))
    except (TypeError, ValueError):
        limit = 50
    limit = max(1, min(limit, 200))
    logs = get_audit_logs(limit=limit, search=search or None, tab=tab) or []
    try:
        stats = get_audit_stats()
    except Exception:
        # Analytics must never break the primary table.
        current_app.logger.exception('Audit stats failed; table still renders')
        stats = None
    return render_template('dashboard/admin_audits.html', logs=logs,
                           search=search, limit=limit, tab=tab,
                           describe_activity=describe_activity, stats=stats,
                           sidebar='components/admin_sidebar_nav.html')
