import re
import urllib
from flask import Blueprint
from flask import jsonify, request, url_for
from sqlalchemy import and_, or_
from almanac_browser.modules.models import Assertion, Source, AssertionSchema, SourceSchema, Feature, FeatureSchema, \
    FeatureDefinition, FeatureDefinitionSchema, FeatureAttributeDefinition, FeatureAttributeDefinitionSchema, \
    FeatureAttribute, FeatureAttributeSchema, FeatureSet
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
feature_definition_schema = FeatureDefinitionSchema()
feature_definitions_schema = FeatureDefinitionSchema(many=True)
feature_attribute_definition_schema = FeatureAttributeDefinitionSchema()
feature_attribute_definitions_schema = FeatureAttributeDefinitionSchema(many=True)
feature_attribute_schema = FeatureAttributeSchema()
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


@api.route('/feature_definitions/<int:definition_id>', methods=['GET'])
def get_feature_definition(definition_id):
    definition = FeatureDefinition.query.get_or_404(definition_id)

    return feature_definition_schema.jsonify(definition)


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


@api.route('/attribute_definitions/<int:attribute_def_id>', methods=['GET'])
def get_attribute_definition(attribute_def_id):
    data = FeatureAttributeDefinition.query.get_or_404(attribute_def_id)

    return feature_attribute_definition_schema.jsonify(data)


@api.route('/attribute_definitions', methods=['GET'])
def get_attribute_definitions():
    data = FeatureAttributeDefinition.query.all()

    return feature_attribute_definitions_schema.jsonify(data)


@api.route('/attributes/<int:attribute_id>', methods=['GET'])
def get_attribute(attribute_id):
    data = FeatureAttribute.query.filter_by(attribute_id=attribute_id)

    return feature_attributes_schema.jsonify(data)


@api.route('/attributes', methods=['GET'])
def get_attributes():
    data = FeatureAttribute.query.all()

    return feature_attributes_schema.jsonify(data)


@api.route('/attributes_within_definition/<int:attribute_def_id>', methods=['GET'])
def get_attributes_within_definition(attribute_def_id):
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
def new_assertion():
    """Submit an assertion for consideration for inclusion in the database"""

    data = request.get_json() or {}
    print(data)
    if 'doi' not in data or 'email' not in data:
        return bad_request("Please submit gene symbol, DOI, and email fields")
    if 'implication' not in data or data['implication'] not in IMPLICATION_LEVELS:
        data['implication'] = None
    if 'cancer_type' not in data:
        return bad_request('Please select a cancer type')
    if 'feature_def_id' not in data:
        return bad_request('Please select a feature definition ID.')

    attribute_data = {}
    for key, value in data.items():
        attribute_match = re.match(r'^attribute-(\d+)$', key)
        if attribute_match:
            attribute_data[attribute_match.group(1)] = value

    if not attribute_data:
        return bad_request('Please submit at least one attribute.')

    # some fields are optional
    if 'therapy' not in data:
        data['therapy'] = ''

    assertion = Assertion()
    assertion.validated = False
    assertion.predictive_implication = data['implication']
    assertion.therapy_name = data['therapy']
    assertion.disease = data['cancer_type']
    assertion.old_disease = data['cancer_type']
    assertion.submitted_by = data['email']

    feature_set = FeatureSet(assertion=assertion)
    feature_def = FeatureDefinition.query.get(data['feature_def_id'])
    if not feature_def:
        return bad_request('Invalid feature definition ID.')

    feature = Feature(feature_set=feature_set, feature_definition=feature_def)
    for attribute_def_id, attribute_value in attribute_data.items():
        new_attribute = FeatureAttribute(
            feature_id=data['feature_def_id'],
            attribute_def_id=attribute_def_id,
            value=attribute_value
        )

        feature.attributes.append(new_attribute)

    feature_set.features.append(feature)
    assertion.feature_sets.append(feature_set)
    assertion.sources.append(add_or_fetch_source(db, data['doi']))

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

    def _make_attribute_data(attribute_rname, attribute_value, feature_rname=None):
        if feature_rname:
            id_value = '"%s"[feature] "%s":"%s"[attribute]' % (feature_rname, attribute_rname, attribute_value)
            text_value = '%s %s:%s' % (feature_rname, attribute_rname, attribute_value)
        else:
            id_value = '"%s":"%s"[attribute]' % (attribute_rname, attribute_value)
            text_value = '%s:%s' % (attribute_rname, attribute_value)

        return {'id': id_value, 'text': text_value, 'category': 'attribute'}

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

    feature_defs = db.session.query(FeatureDefinition). \
        filter(FeatureDefinition.readable_name.ilike('%%%s%%' % search_str)).distinct().all()
    for feature_def in feature_defs:
        data['features'].append({
            'id': '"%s"[feature]' % feature_def.readable_name,
            'text': feature_def.readable_name,
            'category': 'feature',
        })

        # Add all corresponding attributes and possible attribute values for this feature
        for attribute_def in feature_def.attribute_definitions:
            for attribute in attribute_def.attributes:
                new_data = _make_attribute_data(attribute_def.readable_name, attribute.value, feature_def.readable_name)
                if new_data not in data['attributes']:
                    data['attributes'].append(new_data)

    # We search for attributes twice - once assuming a fully formed Attribute:Value pair, and once assuming the user
    # has not specified a Value yet (and thus no colon is present).
    attribute_name_needle, _, attribute_value_needle = search_str.partition(':')
    if attribute_name_needle and attribute_value_needle:
        attribute_def_with_attributes = db.session. \
            query(FeatureAttributeDefinition.readable_name, FeatureAttribute.value). \
            filter(and_(FeatureAttributeDefinition.attribute_def_id == FeatureAttribute.attribute_def_id,
                        FeatureAttribute.value.ilike('%%%s%%' % attribute_value_needle))).distinct().all()

        for attribute_rname, attribute_value in attribute_def_with_attributes:
            data['attributes'].append(_make_attribute_data(attribute_rname, attribute_value))
    else:
        attribute_info = db.session.query(FeatureAttributeDefinition.readable_name, FeatureAttribute.value).filter(
            FeatureAttributeDefinition.attribute_def_id == FeatureAttribute.attribute_def_id,
            FeatureAttribute.value != None,  # "is not" operator is not allowed in SQLAlchemy
            or_(FeatureAttributeDefinition.name.ilike('%%%s%%' % attribute_name_needle),
                FeatureAttributeDefinition.readable_name.ilike('%%%s%%' % attribute_name_needle))).distinct().all()
        for attribute_rname, attribute_value in attribute_info:
            data['attributes'].append(_make_attribute_data(attribute_rname, attribute_value))

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

