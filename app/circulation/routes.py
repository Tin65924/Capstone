from flask import render_template
from flask_login import login_required
from . import circulation_bp
from app.auth.decorators import librarian_required


@circulation_bp.route('/librarian/circulation')
@login_required
@librarian_required
def circulation_page():
    return render_template('circulation/circulation.html')


@circulation_bp.route('/librarian/reservations')
@login_required
@librarian_required
def reservations_page():
    return render_template('reservations/reservations.html')
