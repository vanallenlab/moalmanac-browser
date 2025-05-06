import flask
import sqlalchemy

from . import main_bp
from . import requests

@main_bp.route('/', endpoint='index')
@main_bp.route('/index', methods=['GET', 'POST'])
def index():
    about = requests.Local.get_about()
    terms = requests.Local.get_terms()
    return flask.render_template(
        template_name_or_list='index.html',
        about=about,
        terms=terms
    )

@main_bp.route('/documents', defaults={'document_id': None}, methods=['GET', 'POST'])
@main_bp.route('/documents/<document_id>', endpoint='documents')
def documents(document_id: str = None):
    records = requests.Local.get_documents()
    return flask.render_template(
        template_name_or_list='documents.html',
        documents=records
    )