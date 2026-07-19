from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from . import main_bp
from app.cataloging.models import get_recent_books


@main_bp.route('/')
def index():
    new_arrivals = get_recent_books(5)
    return render_template('public/index.html', new_arrivals=new_arrivals)


@main_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role in ('Student', 'Faculty'):
        return redirect(url_for('main.user_profile'))
    return render_template('dashboard/dashboard.html')


@main_bp.route('/users')
@login_required
def user_management():
    return redirect(url_for('auth.admin_users'))


@main_bp.route('/user/profile')
@login_required
def user_profile():
    if current_user.role in ('Librarian', 'Admin'):
        return redirect(url_for('main.dashboard'))
    from app.auth.models import get_user_by_id
    user_data = get_user_by_id(current_user.id)
    return render_template('users/user_profile.html', user_data=user_data)


@main_bp.route('/user/history')
@login_required
def user_history():
    return render_template('users/user_history.html')
