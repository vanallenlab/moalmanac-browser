from flask import Blueprint

errors = Blueprint('errors', __name__)

from target_portal.modules.errors import handlers
