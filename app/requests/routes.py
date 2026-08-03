from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from . import requests_bp
from .models import (
    create_request, get_requests, get_request_by_id,
    update_request_status, get_demand_count
)
from app.auth.decorators import librarian_required


@requests_bp.route('/librarian/requests')
@login_required
@librarian_required
def list_requests():
    return render_template('requests/requests.html')


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

        create_request(borrower_id, book_title, author)
        flash('Your request has been submitted!', 'success')
        return redirect(url_for('requests.user_request_book'))

    return render_template('requests/user_request_book.html')