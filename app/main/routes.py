from flask import render_template, redirect, url_for, jsonify, request, flash, current_app
from datetime import date, datetime
from flask_login import login_required, current_user
from . import main_bp
from .models import get_dashboard_stats, get_recent_activity, get_daily_borrows, get_attention_summary, get_admin_overview_stats
from app.cataloging.models import get_recent_books, suggest_book_values, suggest_books_rich, get_book_by_title_author_isbn, get_accession_by_number
from app.auth.decorators import librarian_required, admin_required

SUGGEST_FIELDS = {
    'book_title', 'book_author', 'book_publisher', 'book_subject',
    'book_isbn', 'book_search', 'student_program',
}
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


def _safe_departments(dept_type):
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
    new_arrivals = get_recent_books(5)
    return render_template('public/index.html', new_arrivals=new_arrivals)


@main_bp.route('/health')
def health():
    """Liveness probe for Render/uptime monitors. No auth, no DB."""
    return jsonify({'status': 'ok'}), 200


@main_bp.route('/dashboard')
@login_required
def dashboard():
    return redirect(url_for('main.user_profile'))


@main_bp.route('/user/profile')
@login_required
def user_profile():
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
        today = date.today()
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
        if role_name == 'Faculty':
            borrow_limit = current_app.config.get('MAX_BORROW_LIMIT_FACULTY', 5)
        else:
            borrow_limit = current_app.config.get('MAX_BORROW_LIMIT_STUDENT', 3)

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
        try:
            unread_count = count_unread_notifications(borrower_id)
        except Exception:
            unread_count = 0
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
                delta = (due_day - date.today()).days
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
    else:
        borrowing_requests = []

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
    import re
    from app.auth.models import get_profile_by_user, update_own_profile, log_activity, is_valid_department, is_valid_any_department

    full_name = request.form.get('full_name', '').strip()
    phone_number = request.form.get('phone_number', '').strip() or None
    department = request.form.get('department', '').strip() or None

    if request.form.get('id_number', '').strip():
        flash('Student ID cannot be changed. Contact the librarian for ID corrections.', 'error')
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
            unread_count = count_unread_notifications(borrower[0])
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
        from app.circulation.models import count_unread_notifications
        return jsonify({'read': notification_id,
                        'unread_count': count_unread_notifications(borrower[0]) or 0})
    return redirect(_safe_next('main.user_profile'))


@main_bp.route('/user/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications_read_route():
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
        return jsonify({'read_all': True, 'unread_count': 0})
    flash('All notifications marked as read.', 'success')
    return redirect(_safe_next('main.user_profile'))


def _wants_json():
    """True when the client asked for JSON (AJAX) instead of PRG redirect."""
    return 'application/json' in (request.headers.get('Accept') or '')


@main_bp.route('/user/history')
@login_required
def user_history():
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
    overdue_ids = _overdue_loan_ids(transactions, date.today(), status_idx=5)
    return render_template('users/user_history.html',
                           tab=tab, page=page, total_pages=total_pages,
                           total=total, counts=counts, records=records,
                           total_fines=total_fines,
                           overdue_ids=overdue_ids)


@main_bp.route('/api/bloom')
def bloom_filters():
    from app.bloom_registry import bloom_registry
    return jsonify(bloom_registry.get_payloads())


@main_bp.route('/api/suggestions')
def suggestions():
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
    title = request.args.get('title', '').strip()
    author = request.args.get('author', '').strip()
    if not title or not author:
        return jsonify({'exists': False})
    isbn = request.args.get('isbn', '').strip() or None
    return jsonify({'exists': bool(get_book_by_title_author_isbn(title, author, isbn))})


@main_bp.route('/api/student-exists')
def student_exists():
    id_number = request.args.get('id_number', '').strip()
    if not id_number:
        return jsonify({'exists': False})
    from app.auth.models import get_user_by_id_number
    return jsonify({'exists': bool(get_user_by_id_number(id_number))})


@main_bp.route('/api/accession-exists')
def accession_exists():
    accession_number = request.args.get('accession_number', '').strip()
    if not accession_number:
        return jsonify({'exists': False})
    return jsonify({'exists': bool(get_accession_by_number(accession_number))})


@main_bp.route('/librarian')
@login_required
@librarian_required
def librarian_dashboard():
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
