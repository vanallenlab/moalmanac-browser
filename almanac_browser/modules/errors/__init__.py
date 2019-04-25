from flask import Blueprint

errors = Blueprint('errors', __name__)

from almanac_browser.modules.errors import handlers
