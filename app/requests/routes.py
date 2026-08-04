from app.procurement.models import create_procurement
from app.auth.models import log_activity
from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from . import requests_bp
from .models import (
    create_request, get_requests, get_request_by_id,
    update_request_status, get_demand_count, get_borrower_by_user,
    check_duplicate_request
)
from app.auth.decorators import librarian_required


@requests_bp.route('/librarian/requests')
@login_required
@librarian_required
def list_requests():
    pending = get_requests(status='pending_review')
    requests_with_demand = [
        (r, get_demand_count(r[2])) for r in pending
    ]
    return render_template('requests/requests.html', requests=requests_with_demand)

@requests_bp.route('/librarian/requests/<int:request_id>/<action>', methods=['POST'])
@login_required
@librarian_required
def review_request(request_id, action):
    if action not in ('approve', 'reject'):
        flash('Invalid action.', 'error')
        return redirect(url_for('requests.list_requests'))

    status = 'approved' if action == 'approve' else 'rejected'
    update_request_status(request_id, status, reviewer_id=current_user.id)

    if action == 'approve':
        create_procurement(request_id)

    log_activity(current_user.id, f'requests:{action}:{request_id}')
    flash(f'Request {status}.', 'success')
    return redirect(url_for('requests.list_requests'))

from flask import redirect, url_for, flash
from .models import get_borrower_by_user

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

    return render_template('requests/user_request_book.html')