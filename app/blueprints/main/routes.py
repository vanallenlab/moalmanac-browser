import flask
import sqlalchemy

from . import main_bp
from . import requests

@main_bp.route('/', endpoint='index')
@main_bp.route('/index', methods=['GET', 'POST'])
def index():
    about = requests.Local.get_about()

    return flask.render_template(
        template_name_or_list='index.html',
        about=about
    )

@main_bp.route('/documents', methods=['GET', 'POST'])
def documents():
    return flask.render_template(
        template_name_or_list='documents.html'
    )