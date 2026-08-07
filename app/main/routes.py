from flask import render_template, redirect, url_for, jsonify, request
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
    from app.auth.models import get_user_by_id
    user_data = get_user_by_id(current_user.id)
    return render_template('users/user_profile.html', user_data=user_data)


@main_bp.route('/user/history')
@login_required
def user_history():
    return render_template('users/user_history.html')


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
