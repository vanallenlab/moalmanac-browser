from flask import Blueprint
from flask import jsonify, request, url_for
from target_portal.modules.models import Assertion, Alteration, Source, AssertionSchema, AlterationSchema, SourceSchema

api = Blueprint('api', __name__)


assertion_schema = AssertionSchema()
assertions_schema = AssertionSchema(many=True)
alteration_schema = AlterationSchema()
alterations_schema = AlterationSchema(many=True)
source_schema = SourceSchema()
sources_schema = SourceSchema(many=True)


@api.route('/assertions/<int:assertion_id>', methods=['GET'])
def get_assertion(assertion_id):
    assertion = Assertion.query.get_or_404(assertion_id)
    return assertion_schema.jsonify(assertion)

        # pre-Marshmallow:
        #  return jsonify(Assertion.query.get_or_404(assertion_id).to_dict())


@api.route('/assertions', methods=['GET'])
def assertions():
    if request.method == 'GET':
        data = Assertion.query.all()
        return assertions_schema.jsonify(data)

@api.route('new_assertion', methods=['POST'])
    if request.method == 'POST':
        data = request.get_json() or {}




@api.route('/alterations/<int:alt_id>', methods=['GET'])
def get_alteration(alt_id):
    alteration = Alteration.query.get_or_404(alt_id)
    return alteration_schema.jsonify(alteration)

        # pre-Marshmallow
        # return jsonify(Alteration.query.get_or_404(alt_id).to_dict())


@api.route('/alterations', methods=['GET'])
def get_alterations():
    if request.method == 'GET':
        data = Alteration.query.all()
        return alterations_schema.jsonify(data)


@api.route('/sources/<int:source_id>', methods=['GET'])
def get_source(source_id):
    source = Source.query.get_or_404(source_id)
    return source_schema.jsonify(source)

        # pre-Marshmallow
        # return jsonify(Source.query.get_or_404(source_id).to_dict())


@api.route('/sources', methods=['GET'])
def get_sources():
    if request.method == 'GET':
        data = Source.query.all()
        return sources_schema.jsonify(data)
