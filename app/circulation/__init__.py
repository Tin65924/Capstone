from flask import Blueprint

circulation_bp = Blueprint('circulation', __name__, template_folder='../templates/circulation')

from . import routes
