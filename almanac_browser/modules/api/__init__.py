import urllib
from flask import Blueprint
from flask import jsonify, request, url_for
from sqlalchemy import and_, or_
from almanac_browser.modules.models import Assertion, Source, AssertionSchema, SourceSchema, Feature, FeatureSchema, \
    FeatureDefinition, FeatureDefinitionSchema, FeatureAttributeDefinition, FeatureAttributeDefinitionSchema, \
    FeatureAttribute, FeatureAttributeSchema
from almanac_browser.modules.helper_functions import add_or_fetch_source, query_distinct_column, \
    get_all_genes, get_distinct_attribute_values, flatten_sqlalchemy_singlets
from .errors import bad_request
from almanac_browser.modules.portal import IMPLICATION_LEVELS, ALTERATION_CLASSES, EFFECTS
from db import db

api = Blueprint('api', __name__)

assertion_schema = AssertionSchema()
assertions_schema = AssertionSchema(many=True)
source_schema = SourceSchema()
sources_schema = SourceSchema(many=True)
feature_schema = FeatureSchema()
features_schema = FeatureSchema(many=True)
feature_definitions_schema = FeatureDefinitionSchema(many=True)
feature_attribute_definitions_schema = FeatureAttributeDefinitionSchema(many=True)
feature_attributes_schema = FeatureAttributeSchema(many=True)


# TODO authentication for all API calls

@api.route('/assertions/<int:assertion_id>', methods=['GET'])
def get_assertion(assertion_id):
    assertion = Assertion.query.get_or_404(assertion_id)

    return assertion_schema.jsonify(assertion)


@api.route('/assertions', methods=['GET'])
def get_assertions():
    data = Assertion.query.all()

    return assertions_schema.jsonify(data)


@api.route('/feature_definitions', methods=['GET'])
def get_feature_definitions():
    data = FeatureDefinition.query.all()

    return feature_definitions_schema.jsonify(data)


@api.route('/features/<int:feature_id>', methods=['GET'])
def get_feature(feature_id):
    alteration = Feature.query.get_or_404(feature_id)

    return feature_schema.jsonify(alteration)


@api.route('/features', methods=['GET'])
def get_features():
    data = Feature.query.all()

    return features_schema.jsonify(data)


@api.route('/feature_attribute_definitions/<int:feature_def_id>', methods=['GET'])
def get_feature_attribute_definitions(feature_def_id):
    data = FeatureAttributeDefinition.query.filter_by(feature_def_id=feature_def_id)

    return feature_attribute_definitions_schema.jsonify(data)


@api.route('/attributes/<int:attribute_def_id>', methods=['GET'])
def get_attributes(attribute_def_id):
    data = FeatureAttribute.query.filter_by(attribute_def_id=attribute_def_id)

    return feature_attributes_schema.jsonify(data)


@api.route('/distinct_attribute_values/<int:attribute_def_id>', methods=['GET'])
def get_all_distinct_attribute_values(attribute_def_id):
    data = get_distinct_attribute_values(
        db=db,
        needle=attribute_def_id,
        search_column=FeatureAttributeDefinition.attribute_def_id
    )

    return jsonify(data)


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

    # some fields are optional
    if 'alt' not in data:
        data['alt'] = ""
    if 'therapy' not in data:
        data['therapy'] = ""

    alteration = add_or_fetch_feature(db, data['gene'], data['effect'], data['alt_class'], data['alt'])
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


@api.route('/genes', methods=['GET'])
def get_genes():
    data = get_all_genes(db)

    return jsonify(data)


@api.route('/diseases', methods=['GET'])
def get_diseases():
    data = flatten_sqlalchemy_singlets(
        db.session.query(Assertion.disease).distinct()
    )

    return jsonify(data)


@api.route('/predictive_implications', methods=['GET'])
def get_predictive_implications():
    data = flatten_sqlalchemy_singlets(
        db.session.query(Assertion.predictive_implication).distinct()
    )

    return jsonify(data)


@api.route('/therapies', methods=['GET'])
def get_therapies():
    data = flatten_sqlalchemy_singlets(
        db.session.query(Assertion.therapy_name).distinct()
    )

    return jsonify(data)


@api.route('/select2_search', methods=['GET'])
def select2_search():
    """See https://select2.org/data-sources/formats for the Select2 data format."""

    search_args = request.args.getlist('s')
    if not search_args:
        return jsonify({'results': []})

    search_str = urllib.parse.unquote(' '.join(search_args))

    data = {
        'features': [],
        'attributes': [],
        'diseases': [],
        'therapies': [],
        'preds': [],
        'genes': [],
    }

    feature_defs = db.session.query(FeatureDefinition.readable_name). \
        filter(FeatureDefinition.readable_name.ilike('%%%s%%' % search_str)).distinct().all()
    for feature_def in feature_defs:
        data['features'].append({
            'id': '"%s"[feature]' % feature_def.readable_name,
            'text': feature_def.readable_name,
            'category': 'feature',
        })

    # We search for attributes twice - once assuming a fully formed Attribute:Value pair, and once assuming the user
    # has not specified a Value yet (and thus no colon is present).
    attribute_name_needle, _, attribute_value_needle = search_str.partition(':')
    if attribute_name_needle and attribute_value_needle:
        attribute_def_with_attributes = db.session. \
            query(
                FeatureDefinition.readable_name,
                FeatureAttributeDefinition.name,
                FeatureAttributeDefinition.readable_name,
                FeatureAttribute.value).\
            filter(and_(FeatureDefinition.feature_def_id == FeatureAttributeDefinition.feature_def_id,
                        FeatureAttributeDefinition.attribute_def_id == FeatureAttribute.attribute_def_id,
                        FeatureAttribute.value.ilike('%%%s%%' % attribute_value_needle), )).distinct().all()

        for feature_rname, attribute_name, attribute_rname, attribute_value in\
                attribute_def_with_attributes:
            data['attributes'].append({
                'id': '"%s"[feature] "%s":"%s"[attribute]' % (feature_rname, attribute_rname, attribute_value),
                'text': '%s %s:%s' % (feature_rname, attribute_rname, attribute_value),
                'category': 'attribute',
            })
    else:
        attribute_info = db.session.query(
            FeatureDefinition.readable_name,
            FeatureAttributeDefinition.name,
            FeatureAttributeDefinition.readable_name,
            FeatureAttribute.value
        ).filter(
            FeatureDefinition.feature_def_id == FeatureAttributeDefinition.feature_def_id,
            FeatureAttributeDefinition.attribute_def_id == FeatureAttribute.attribute_def_id,
            FeatureAttribute.value != None,  # "is not" operator is not allowed in SQLAlchemy
            or_(FeatureAttributeDefinition.name.ilike('%%%s%%' % attribute_name_needle),
                FeatureAttributeDefinition.readable_name.ilike('%%%s%%' % attribute_name_needle))).distinct().all()
        for feature_name, attribute_name, attribute_rname, attribute_value in attribute_info:
            data['attributes'].append({
                'id': '"%s"[feature] "%s:%s"[attribute]' % (feature_name, attribute_rname, attribute_value),
                'text': '%s %s:%s' % (feature_name, attribute_rname, attribute_value),
                'category': 'attribute',
            })

    disease_assertions = db.session.query(Assertion.disease). \
        filter(Assertion.disease.ilike('%%%s%%' % search_str)).distinct().all()

    for disease in disease_assertions:
        disease = disease[0]
        data['diseases'].append({
            'id': '"%s"[disease]' % disease,
            'text': disease,
            'category': 'disease',
        })

    therapy_assertions = db.session.query(Assertion.therapy_name). \
        filter(Assertion.therapy_name.ilike('%%%s%%' % search_str)).distinct().all()
    for therapy in therapy_assertions:
        therapy = therapy[0]
        data['therapies'].append({
            'id': '"%s"[therapy]' % therapy,
            'text': therapy,
            'category': 'therapy',
        })

    pred_assertions = db.session.query(Assertion.predictive_implication). \
        filter(Assertion.predictive_implication.ilike('%%%s%%' % search_str)).distinct().all()
    for pred in pred_assertions:
        pred = pred[0]
        data['preds'].append({
            'id': '"%s"[pred]' % pred,
            'text': pred,
            'category': 'pred',
        })

    # As a last ditch, we search for gene names, which "technically" should be specified as an individual attribute.
    genes = db.session.query(FeatureAttribute.value). \
        filter(FeatureAttributeDefinition.type == "gene",
               FeatureAttributeDefinition.attribute_def_id == FeatureAttribute.attribute_def_id,
               FeatureAttribute.value.ilike('%%%s%%' % search_str)).distinct().all()
    for gene in genes:
        gene = gene[0]
        data['genes'].append({
            'id': 'Gene:"%s"[attribute]' % gene,
            'text': '%s' % gene,
            'category': 'gene',
        })

    select2_data = {'results': []}
    if data['features']:
        select2_data['results'].append({'text': 'Features', 'children': data['features']})
    if data['attributes']:
        select2_data['results'].append({'text': 'Attributes', 'children': data['attributes']})
    if data['diseases']:
        select2_data['results'].append({'text': 'Diseases', 'children': data['diseases']})
    if data['therapies']:
        select2_data['results'].append({'text': 'Therapies', 'children': data['therapies']})
    if data['preds']:
        select2_data['results'].append({'text': 'Predictive Implications', 'children': data['preds']})
    if data['genes']:
        select2_data['results'].append({'text': 'Genes', 'children': data['genes']})

    return jsonify(select2_data)


@api.route('/extension', methods=['GET'])
def populate_ext():
    """Provide fields for populating the extension popup through which clients can submit Assertion suggestions"""
    diseases = query_distinct_column(db, Assertion, 'disease')
    pred_impls = query_distinct_column(db, Assertion, 'predictive_implication')
    therapy_names = query_distinct_column(db, Assertion, 'therapy_name')

    all_genes = get_all_genes(db)
    num_genes = len(all_genes)
    num_assertions = db.session.query(Assertion).count()

    return jsonify(num_genes=num_genes,
                   num_assertions=num_assertions,
                   typeahead_genes=all_genes,
                   diseases=[d for d in sorted(diseases) if not d == 'Oncotree Term'],
                   pred_impls=IMPLICATION_LEVELS,
                   alteration_classes=ALTERATION_CLASSES,
                   effects=EFFECTS,
                   therapy_names=[t for t in sorted(therapy_names) if not t == 'Therapy name']
                   )
