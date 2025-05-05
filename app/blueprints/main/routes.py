import flask
import sqlalchemy

from . import main_bp

@main_bp.route('/', endpoint='index')
@main_bp.route('/index', methods=['GET', 'POST'])
def index():
    return flask.render_template(
        template_name_or_list='index.html'
    )
