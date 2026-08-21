from flask import render_template, redirect, url_for, jsonify, request
from datetime import date
from flask_login import login_required, current_user
from . import main_bp
from .models import get_dashboard_stats, get_recent_activity, get_daily_borrows
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
    from flask import current_app
    from app.auth.models import get_user_by_id
    from app.circulation.models import (
        get_borrower_by_user, get_loans_by_borrower, count_active_loans,
        get_reservations_by_borrower, get_notifications_by_borrower
    )
    from app.requests.models import get_requests_by_borrower

    user_data = get_user_by_id(current_user.id)

    borrower = get_borrower_by_user(current_user.id)
    loans = []
    overdue_count = 0
    active_count = 0
    borrow_limit = 0
    pickups = []
    my_requests = []
    notifications = []

    if borrower:
        borrower_id = borrower[0]
        loans = get_loans_by_borrower(borrower_id)
        overdue_count = sum(1 for loan in loans if loan[4] == 'overdue')
        active_count = count_active_loans(borrower_id)

        role_name = user_data[2] if user_data else ''
        if role_name == 'Faculty':
            borrow_limit = current_app.config.get('MAX_BORROW_LIMIT_FACULTY', 5)
        else:
            borrow_limit = current_app.config.get('MAX_BORROW_LIMIT_STUDENT', 3)

        reservations = get_reservations_by_borrower(borrower_id)
        pickups = [r for r in reservations if r[2] == 'allocated']
        borrowing_requests = [r for r in reservations if r[2] in ('waiting', 'allocated')]

        my_requests = get_requests_by_borrower(borrower_id)
        notifications = get_notifications_by_borrower(borrower_id)
    else:
        borrowing_requests = []

    return render_template('users/user_profile.html', user_data=user_data,
                           loans=loans, overdue_count=overdue_count,
                           active_count=active_count, borrow_limit=borrow_limit,
                           pickups=pickups, my_requests=my_requests,
                           borrowing_requests=borrowing_requests,
                           notifications=notifications)


@main_bp.route('/user/history')
@login_required
def user_history():
    from app.circulation.models import get_borrower_by_user, get_user_loan_history
    from app.requests.models import get_requests_by_borrower

    transactions = []
    my_requests = []
    borrower = get_borrower_by_user(current_user.id)
    if borrower:
        transactions = get_user_loan_history(current_user.id)
        my_requests = get_requests_by_borrower(borrower[0])
    return render_template('users/user_history.html',
                           transactions=transactions, my_requests=my_requests)


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
    return render_template('dashboard/dashboard.html', stats=stats,
                           activity=activity, daily=daily,
                           sidebar='components/librarian_sidebar_nav.html')


@main_bp.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    stats = get_dashboard_stats()
    activity = get_recent_activity(5)
    daily = get_daily_borrows(6)
    return render_template('dashboard/dashboard.html', stats=stats,
                           activity=activity, daily=daily,
                           sidebar='components/admin_sidebar_nav.html')
