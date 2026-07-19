from flask import render_template
from flask_login import login_required
from . import analytics_bp
from app.auth.decorators import librarian_required


@analytics_bp.route('/analytics')
@login_required
@librarian_required
def analytics_page():
    return render_template('analytics/analytics.html')
