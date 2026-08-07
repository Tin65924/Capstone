from app.procurement.models import create_procurement
from app.auth.models import log_activity
from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from . import requests_bp
from .models import (
    create_request, get_requests, get_request_by_id,
    update_request_status, get_demand_by_role, get_borrower_by_user,
    check_duplicate_request, get_requests_with_details, get_requests_by_borrower,
    count_requests, PER_PAGE
)
from app.auth.decorators import librarian_required


VALID_STATUSES = ['pending_review', 'approved', 'rejected', 'existing_in_collection', 'procured']

@requests_bp.route('/librarian/requests')
@login_required
@librarian_required
def list_requests():
    status = request.args.get('status', 'pending_review')
    if status == 'all':
        status = None
    elif status not in VALID_STATUSES:
        status = 'pending_review'

    search = request.args.get('search', '').strip() or None

    page = request.args.get('page', 1, type=int)
    if page < 1:
        page = 1

    items = get_requests_with_details(status=status, search=search, page=page)
    total = count_requests(status=status, search=search)
    total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)

    demand_rows = get_demand_by_role()
    demand_by_title = {}
    for title, role_name, count in demand_rows:
        demand_by_title.setdefault(title, {})[role_name] = count

    requests_with_demand = [
        (r, demand_by_title.get(r[2], {})) for r in items
    ]
    return render_template(
        'requests/requests.html',
        requests=requests_with_demand,
        current_status=status,
        current_search=search,
        current_page=page,
        total_pages=total_pages
    )

@requests_bp.route('/librarian/requests/<int:request_id>/<action>', methods=['POST'])
@login_required
@librarian_required
def review_request(request_id, action):
    if action not in ('approve', 'reject'):
        flash('Invalid action.', 'error')
        return redirect(url_for('requests.list_requests'))

    existing = get_request_by_id(request_id)
    if not existing:
        flash('Request not found.', 'error')
        return redirect(url_for('requests.list_requests'))

    if existing[5] != 'pending_review':
        flash('This request has already been reviewed.', 'error')
        return redirect(url_for('requests.list_requests'))

    status = 'approved' if action == 'approve' else 'rejected'
    remarks = request.form.get('remarks', '').strip() or None
    update_request_status(request_id, status, reviewer_id=current_user.id, remarks=remarks)

    if action == 'approve':
        create_procurement(request_id)

    log_activity(current_user.id, f'requests:{action}:{request_id}')
    flash(f'Request {status}.', 'success')
    return redirect(url_for('requests.list_requests'))

@requests_bp.route('/user/request-book', methods=['GET', 'POST'])
@login_required

def user_request_book():
    if request.method == 'POST':
        book_title = request.form.get('book-title', '').strip()
        author = request.form.get('author', '').strip() or None

        if not book_title:
            flash('Book title is required.', 'error')
            return redirect(url_for('requests.user_request_book'))

        borrower_id = get_borrower_by_user(current_user.id)
        if not borrower_id:
            flash('Only registered borrowers can submit requests.', 'error')
            return redirect(url_for('requests.user_request_book'))

        if check_duplicate_request(borrower_id, book_title):
            flash('You already requested this book.', 'error')
            return redirect(url_for('requests.user_request_book'))

        new_request_id = create_request(borrower_id, book_title, author)
        log_activity(current_user.id, f'requests:create:{new_request_id}')
        flash('Your request has been submitted!', 'success')
        return redirect(url_for('requests.user_request_book'))

    borrower_id = get_borrower_by_user(current_user.id)
    my_requests = get_requests_by_borrower(borrower_id) if borrower_id else []
    return render_template('requests/user_request_book.html', my_requests=my_requests)