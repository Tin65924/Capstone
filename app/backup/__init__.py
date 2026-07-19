from flask import Blueprint

backup_bp = Blueprint('backup', __name__, template_folder='../templates/backup')

from . import routes
