from flask import render_template
from flask_login import login_required
from . import procurement_bp
from app.auth.decorators import librarian_required


@procurement_bp.route('/librarian/procurement')
@login_required
@librarian_required
def procurement_dashboard():
    return render_template('procurement/procurement.html')
