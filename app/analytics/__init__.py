from flask import Blueprint

analytics_bp = Blueprint('analytics', __name__, template_folder='../templates/analytics')

from . import routes
