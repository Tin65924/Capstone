from flask import render_template
from flask_login import login_required
from . import inventory_bp
from app.auth.decorators import librarian_required


@inventory_bp.route('/inventory')
@login_required
@librarian_required
def inventory_page():
    return render_template('inventory/inventory.html')
