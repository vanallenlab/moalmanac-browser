import flask

main_bp = flask.Blueprint('main', __name__)

from . import routes