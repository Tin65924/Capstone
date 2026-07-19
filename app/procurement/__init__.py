from flask import Blueprint

procurement_bp = Blueprint('procurement', __name__, template_folder='../templates/procurement')

from . import routes
