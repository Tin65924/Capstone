from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from . import main_bp
from .models import get_dashboard_stats, get_recent_activity, get_daily_borrows
from app.cataloging.models import get_recent_books
from app.auth.decorators import librarian_required, admin_required


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
