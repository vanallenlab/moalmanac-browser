from flask import Blueprint
from target_portal.modules.helper_functions import get_unapproved_assertion_rows, make_row, http404response, \
    http200response, \
    query_distinct_column, add_or_fetch_alteration, add_or_fetch_source, delete_assertion, \
    amend_alteration_for_assertion, amend_cite_text_for_assertion, http400response, get_typeahead_genes
from flask import jsonify, request, url_for
from target_portal.modules.models import Assertion, Alteration, Source

api = Blueprint('api', __name__)


@api.route('/assertions/<int:assertion_id>', methods=['GET'])
def get_assertion(assertion_id):
    if request.method == 'GET':
        return jsonify(Assertion.query.get_or_404(assertion_id).to_dict())


@api.route('/alterations/<int:alt_id>', methods=['GET'])
def get_alteration(alt_id):
    if request.method == 'GET':
        return jsonify(Alteration.query.get_or_404(alt_id).to_dict())


@api.route('/sources/<int:source_id>', methods=['GET'])
def get_source(source_id):
    if request.method == 'GET':
        return jsonify(Source.query.get_or_404(source_id).to_dict())
