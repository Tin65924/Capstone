from flask import Blueprint

resources_bp = Blueprint('resources', __name__, template_folder='../templates/resources')

from . import routes
