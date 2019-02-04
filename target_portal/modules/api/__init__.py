from flask import Blueprint
from flask import jsonify, request, url_for
from target_portal.modules.models import Assertion, Alteration, Source, AssertionSchema, AlterationSchema, SourceSchema
from target_portal.modules.helper_functions import (add_or_fetch_alteration, add_or_fetch_source, get_typeahead_genes,
    query_distinct_column, http200response, http404response, http400response)
from .errors import bad_request
from target_portal.modules.portal import IMPLICATION_LEVELS, ALTERATION_CLASSES, EFFECTS, pred_impl_orders
from db import db

api = Blueprint('api', __name__)

assertion_schema = AssertionSchema()
assertions_schema = AssertionSchema(many=True)
alteration_schema = AlterationSchema()
alterations_schema = AlterationSchema(many=True)
source_schema = SourceSchema()
sources_schema = SourceSchema(many=True)


#TODO authentication for all API calls

@api.route('/assertions/<int:assertion_id>', methods=['GET'])
def get_assertion(assertion_id):
    assertion = Assertion.query.get_or_404(assertion_id)
    return assertion_schema.jsonify(assertion)


@api.route('/assertions', methods=['GET'])
def get_assertions():
    data = Assertion.query.all()
    return assertions_schema.jsonify(data)


@api.route('/alterations/<int:alt_id>', methods=['GET'])
def get_alteration(alt_id):
    alteration = Alteration.query.get_or_404(alt_id)
    return alteration_schema.jsonify(alteration)


@api.route('/alterations', methods=['GET'])
def get_alterations():
    data = Alteration.query.all()
    return alterations_schema.jsonify(data)


@api.route('/sources/<int:source_id>', methods=['GET'])
def get_source(source_id):
    source = Source.query.get_or_404(source_id)
    return source_schema.jsonify(source)


@api.route('/sources', methods=['GET'])
def get_sources():
    data = Source.query.all()
    return sources_schema.jsonify(data)


@api.route('/new_assertion', methods=['POST'])
def submit():
    """Submit an assertion for consideration for inclusion in the database"""
    data = request.get_json() or {}
    if 'gene' not in data or 'doi' not in data or 'email' not in data:
        return bad_request("Please submit gene symbol, DOI, and email fields")
    if 'effect' not in data or data['effect'] not in EFFECTS:
        return bad_request("Please select a valid effect type")
    if 'alt_class' not in data or data['alt_class'] not in ALTERATION_CLASSES:
        return bad_request("Please select a valid alteration feature")
    if 'implication' not in data or data['implication'] not in IMPLICATION_LEVELS:
        data['implication'] = None
    if 'cancer_type' not in data:
        return bad_request("Please select a cancer type")

    #some fields are optional
    if 'alt' not in data:
        data['alt'] = ""
    if 'therapy' not in data:
        data['therapy'] = ""

    alteration = add_or_fetch_alteration(db, data['gene'], data['effect'], data['alt_class'], data['alt'])
    source = add_or_fetch_source(db, data['doi'])

    assertion = Assertion()
    assertion.validated = False
    assertion.alterations.append(alteration)
    assertion.predictive_implication = data['implication']
    assertion.therapy_type = data['therapy']
    assertion.disease = data['cancer_type']
    assertion.old_disease = data['cancer_type']
    assertion.sources.append(source)
    assertion.submitted_by = data['email']
    db.session.add(assertion)
    db.session.commit()

    response = assertion_schema.jsonify(assertion)
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_assertion', assertion_id=assertion.assertion_id)
    response.headers.add('Access-Control-Allow-Origin', '*')

    return response


@api.route('/features', methods=['GET'])
def get_genes():
    data = get_typeahead_genes(db)
    return jsonify(data)


@api.route('/extension', methods=['GET'])
def populate_ext():
    """Provide fields for populating the extension popup through which clients can submit Assertion suggestions"""
    typeahead_genes = get_typeahead_genes(db)
    diseases = query_distinct_column(db, Assertion, 'disease')
    pred_impls = query_distinct_column(db, Assertion, 'predictive_implication')
    therapy_names = query_distinct_column(db, Assertion, 'therapy_name')

    num_genes = db.session.query(Alteration.gene_name).distinct().count()
    num_assertions = db.session.query(Assertion).count()

    return jsonify(num_genes=num_genes,
                   num_assertions=num_assertions,
                   typeahead_genes=typeahead_genes,
                   diseases=[d for d in sorted(diseases) if not d == 'Oncotree Term'],
                   pred_impls=IMPLICATION_LEVELS,
                   alteration_classes=ALTERATION_CLASSES,
                   effects=EFFECTS,
                   therapy_names=[t for t in sorted(therapy_names) if not t == 'Therapy name']
                   )
