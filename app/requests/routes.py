from flask import render_template, request, jsonify
from flask_login import login_required
from . import requests_bp
from .models import (
    create_request, get_requests, get_request_by_id,
    update_request_status, get_demand_count
)
from app.auth.decorators import librarian_required


@requests_bp.route('/requests')
@login_required
def list_requests():
    return render_template('requests/requests.html')


@requests_bp.route('/user/request-book', methods=['GET', 'POST'])
@login_required
def user_request_book():
    return render_template('requests/user_request_book.html')
