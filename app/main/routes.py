from flask import render_template, redirect, url_for, jsonify, request, flash, current_app
from datetime import date, datetime
from flask_login import login_required, current_user
from . import main_bp
from .models import get_dashboard_stats, get_recent_activity, get_daily_borrows, get_attention_summary, get_admin_overview_stats
from app.cataloging.models import get_recent_books, suggest_book_values, get_book_by_title_author_isbn
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
    if not nxt.startswith('/') or nxt.startswith('//'):
        return fallback
    return nxt


def _safe_departments(dept_type):
    try:
        from app.auth.models import get_departments
        return get_departments(dept_type) or []
    except Exception:
        return []


@main_bp.route('/')
def index():
    new_arrivals = get_recent_books(5)
    return render_template('public/index.html', new_arrivals=new_arrivals)


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
    )
    from app.requests.models import get_requests_by_borrower

    user_data = get_user_by_id(current_user.id)
    try:
        profile = get_profile_by_user(current_user.id)
    except Exception:
        profile = None

    borrower = get_borrower_by_user(current_user.id)
    loans = []
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
        overdue_count = sum(1 for loan in loans if len(loan) > 4 and loan[4] == 'overdue')
        try:
            active_count = count_active_loans(borrower_id)
        except Exception:
            active_count = len(loans)

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
                delta = (due - date.today()).days
                if status == 'overdue' or delta < 0:
                    if not notification_exists(borrower_id, 'overdue_reminder', str(circ_id)):
                        create_notification(
                            borrower_id,
                            f'Overdue: "{title}" was due {due}. Please return it to avoid further fines.',
                            'overdue_reminder',
                            str(circ_id),
                        )
                elif 0 <= delta <= due_soon_days:
                    if not notification_exists(borrower_id, 'due_soon', str(circ_id)):
                        create_notification(
                            borrower_id,
                            f'Reminder: "{title}" is due {due} (in {delta} day(s)).',
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

    if phone_number and not re.fullmatch(r'[+\d][\d\s\-()]{6,19}', phone_number):
        flash('Invalid phone number format.', 'error')
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

    update_own_profile(current_user.id, full_name, phone_number, department)
    log_activity(current_user.id, 'profile:update')
    flash('Profile updated.', 'success')
    return redirect(url_for('main.user_profile'))


@main_bp.route('/user/notifications')
@login_required
def user_notifications():
    from app.circulation.models import (
        get_borrower_by_user, get_notifications_by_borrower, count_unread_notifications
    )
    notifications = []
    unread_count = 0
    borrower = get_borrower_by_user(current_user.id)
    if borrower:
        try:
            notifications = get_notifications_by_borrower(borrower[0]) or []
        except Exception:
            notifications = []
        try:
            unread_count = count_unread_notifications(borrower[0])
        except Exception:
            unread_count = 0
    return render_template('users/user_notifications.html',
                           notifications=notifications, unread_count=unread_count)


@main_bp.route('/user/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read_route(notification_id):
    from app.circulation.models import get_borrower_by_user, mark_notification_read
    from app.auth.models import log_activity
    borrower = get_borrower_by_user(current_user.id)
    if not borrower:
        flash('No borrower record found.', 'error')
        return redirect(url_for('main.user_profile'))
    mark_notification_read(notification_id, borrower[0])
    log_activity(current_user.id, f'notifications:read:{notification_id}')
    return redirect(_safe_next('main.user_profile'))


@main_bp.route('/user/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications_read_route():
    from app.circulation.models import get_borrower_by_user, mark_all_notifications_read
    from app.auth.models import log_activity
    borrower = get_borrower_by_user(current_user.id)
    if not borrower:
        flash('No borrower record found.', 'error')
        return redirect(url_for('main.user_profile'))
    mark_all_notifications_read(borrower[0])
    log_activity(current_user.id, 'notifications:read_all')
    flash('All notifications marked as read.', 'success')
    return redirect(_safe_next('main.user_profile'))


@main_bp.route('/user/history')
@login_required
def user_history():
    from app.circulation.models import (
        get_borrower_by_user, get_user_loan_history,
        get_reservation_history_by_borrower, get_fines_by_borrower,
        get_total_fines, get_notifications_by_borrower,
        expire_overdue_reservations,
    )
    from app.requests.models import get_requests_by_borrower

    transactions = []
    my_requests = []
    reservations = []
    fines = []
    total_fines = 0
    notifications = []
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
        try:
            notifications = get_notifications_by_borrower(borrower[0]) or []
        except Exception:
            notifications = []
    return render_template('users/user_history.html',
                           transactions=transactions, my_requests=my_requests,
                           reservations=reservations, fines=fines,
                           total_fines=total_fines, notifications=notifications)


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
        rows = suggest_book_values(BOOK_FIELD_MAP[field], q)
    return jsonify({'suggestions': [row[0] for row in rows if row and row[0]]})


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
    completed = [b for b in backups if b[3] == 'completed']
    last_backup = completed[0] if completed else None
    from app.backup import jobs as backup_jobs
    backup_busy = (backup_jobs.active_job() is not None
                   or any(b[3] == 'in_progress' for b in backups))
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
    from app.auth.models import AUDIT_TABS, get_audit_logs
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
    return render_template('dashboard/admin_audits.html', logs=logs,
                           search=search, limit=limit, tab=tab,
                           sidebar='components/admin_sidebar_nav.html')
