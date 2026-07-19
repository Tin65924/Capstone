from flask import Blueprint

cataloging_bp = Blueprint('cataloging', __name__, template_folder='../templates/cataloging')

from . import routes
