import re
import urllib
from flask import Blueprint
from flask import jsonify, request, url_for
from sqlalchemy import and_, or_
from almanac_browser.modules.models import \
    Assertion, AssertionSchema, \
    Source, SourceSchema, \
    Feature, FeatureSchema, \
    FeatureDefinition, FeatureDefinitionSchema, \
    FeatureAttributeDefinition, FeatureAttributeDefinitionSchema, \
    FeatureAttribute, FeatureAttributeSchema
from almanac_browser.modules.helper_functions import add_or_fetch_source, query_distinct_column, \
    get_all_genes, get_distinct_attribute_values, flatten_sqlalchemy_singlets
from .errors import bad_request
from almanac_browser.modules.portal import IMPLICATION_LEVELS, ALTERATION_CLASSES, EFFECTS
from db import db

api = Blueprint('api', __name__)


def pop_assertions(list_of_assertions):
    for assertion in list_of_assertions:
        assertion.pop("_sa_instance_state", None)


def pop_sources(list_of_assertions):
    sources = []
    for assertion in list_of_assertions:
        for source in assertion['sources']:
            if source not in sources:
                sources.append(source)
    [item.pop("_sa_instance_state", None) for item in sources]


def reformat_assertion(assertion, pop=True):
    dictionary = assertion.__dict__
    new_dictionary = {}
    for key, value in dictionary.items():
        new_dictionary[key] = value
    if pop:
        new_dictionary.pop("_sa_instance_state", None)

    sources = [item.__dict__ for item in assertion.sources]
    if pop:
        [item.pop("_sa_instance_state", None) for item in sources]
    new_dictionary['sources'] = sources

    features = [reformat_feature(item) for item in assertion.features]
    new_dictionary['features'] = features
    return new_dictionary


def reformat_assertions(list_assertions):
    reformatted_assertions = [reformat_assertion(assertion, pop=False) for assertion in list_assertions]
    pop_sources(reformatted_assertions)
    pop_assertions(reformatted_assertions)
    return reformatted_assertions


def reformat_attributes(feature_definition, attributes):
    new_dictionary = {}
    for i in range(0, len(attributes)):
        key = feature_definition.attribute_definitions[i].name
        value = attributes[i].value
        new_dictionary[key] = value
    new_dictionary['feature_type'] = feature_definition.name
    return new_dictionary


def reformat_feature(feature):
    return {
        'feature_id': feature.feature_id,
        'feature_type': feature.feature_definition.name,
        'attributes': [reformat_attributes(feature.feature_definition, feature.attributes)]
    }


def reformat_features(list_features):
    attributes = []
    unique_features = []
    for item in list_features:
        if item['attributes'] not in attributes:
            unique_features.append(item)
            attributes.append(item['attributes'])
    return unique_features


@api.route('/assertions/<int:assertion_id>', methods=['GET'])
def get_assertion(assertion_id):
    raw_data = Assertion.query.get_or_404(assertion_id)
    data = reformat_assertion(raw_data)
    return jsonify(data)


@api.route('/assertions', methods=['GET'])
def get_assertions():
    raw_data = Assertion.query.all()
    data = reformat_assertions(raw_data)
    return jsonify(data)


@api.route('/feature_definitions/<int:definition_id>', methods=['GET'])
def get_feature_definition(definition_id):
    data = FeatureDefinition.query.get_or_404(definition_id)
    return FeatureDefinitionSchema(exclude=("features",)).jsonify(data)


@api.route('/feature_definitions', methods=['GET'])
def get_feature_definitions():
    data = FeatureDefinition.query.all()
    return FeatureDefinitionSchema(exclude=("features",), many=True).jsonify(data)


@api.route('/features/<int:feature_id>', methods=['GET'])
def get_feature(feature_id):
    raw_data = Feature.query.get_or_404(feature_id)
    data = reformat_feature(raw_data)
    return jsonify(data)


@api.route('/features', methods=['GET'])
def get_features():
    raw_data = Feature.query.all()
    duplicate_data = [reformat_feature(item) for item in raw_data]
    data = reformat_features(duplicate_data)
    return jsonify(data)


@api.route('/attribute_definitions/<int:attribute_def_id>', methods=['GET'])
def get_attribute_definition(attribute_def_id):
    data = FeatureAttributeDefinition.query.get_or_404(attribute_def_id)
    return FeatureAttributeDefinitionSchema(only=("name", "attribute_def_id",)).jsonify(data)


@api.route('/attribute_definitions', methods=['GET'])
def get_attribute_definitions():
    data = FeatureAttributeDefinition.query.all()
    return FeatureAttributeDefinitionSchema(only=("name", "attribute_def_id",), many=True).jsonify(data)


@api.route('/attributes/<int:attribute_id>', methods=['GET'])
def get_attribute(attribute_id):
    data = FeatureAttribute.query.filter_by(attribute_id=attribute_id)
    return FeatureAttributeSchema().jsonify(data)


@api.route('/attributes', methods=['GET'])
def get_attributes():
    data = FeatureAttribute.query.all()
    return FeatureAttributeSchema(many=True).jsonify(data)


@api.route('/attributes_within_definition/<int:attribute_def_id>', methods=['GET'])
def get_attributes_within_definition(attribute_def_id):
    data = FeatureAttribute.query.filter_by(attribute_def_id=attribute_def_id)
    return FeatureAttributeSchema(many=True).jsonify(data)


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
    data = Source.query.get_or_404(source_id)
    return SourceSchema(exclude=['assertions']).jsonify(data)


@api.route('/sources', methods=['GET'])
def get_sources():
    data = Source.query.all()
    return SourceSchema(exclude=['assertions'], many=True).jsonify(data)


@api.route('/genes', methods=['GET'])
def get_genes():
    data = get_all_genes(db)
    return jsonify(sorted(data))


@api.route('/diseases', methods=['GET'])
def get_diseases():
    data = flatten_sqlalchemy_singlets(db.session.query(Assertion.disease).distinct())
    return jsonify(sorted(data))


@api.route('/predictive_implications', methods=['GET'])
def get_predictive_implications():
    data = flatten_sqlalchemy_singlets(db.session.query(Assertion.predictive_implication).distinct())
    return jsonify(data)


@api.route('/therapies', methods=['GET'])
def get_therapies():
    data = flatten_sqlalchemy_singlets(db.session.query(Assertion.therapy_name).distinct())
    return jsonify(sorted(data))


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
