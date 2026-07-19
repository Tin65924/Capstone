from flask import Blueprint

requests_bp = Blueprint('requests', __name__, template_folder='../templates/requests')

from . import routes
