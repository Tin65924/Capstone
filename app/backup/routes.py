from flask import render_template
from flask_login import login_required
from . import backup_bp
from app.auth.decorators import admin_required


@backup_bp.route('/backup')
@login_required
@admin_required
def backup_page():
    return render_template('backup/backup.html')
