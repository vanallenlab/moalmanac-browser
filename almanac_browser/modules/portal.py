import re
from flask import Blueprint, request, render_template
from auth import basic_auth
from werkzeug.exceptions import BadRequest
from db import db
from .models import Assertion, Feature, FeatureAttribute, FeatureDefinition, FeatureSet
from .helper_functions import get_unapproved_assertion_rows, make_rows, http404response, http200response, \
    query_distinct_column, add_or_fetch_source, delete_assertion, \
    amend_alteration_for_assertion, amend_cite_text_for_assertion, http400response, interpret_unified_search_string, \
    get_all_genes

portal = Blueprint('portal', __name__)

IMPLICATION_LEVELS_SORT = {
    'FDA-Approved': 5,
    'Guideline': 4,
    'Clinical trial': 3,
    'Clinical evidence': 2,
    'Preclinical': 1,
    'Inferential': 0
}
IMPLICATION_LEVELS = ['FDA-Approved', 'Guideline', 'Clinical trial', 'Clinical evidence', 'Preclinical', 'Inferential']

ALTERATION_CLASSES = [
    'Aneuploidy', 'Copy Number', 'Germline', 'Knockout', 'Microsatellite Stability',
    'Mutation', 'Mutational Burden', 'Mutational Signature', 'Neoantigen Burden',
    'Rearrangement', 'Silencing']

EFFECTS = [
 'Missense',
 'Amplification',
 'Nonsense',
 'Frameshift',
 'Splice Site',
 'Fusion',
 'Translocation',
 'Deletion',
 'shRNA',
 'siRNA',
 'InDel',
 'CRSPR-Cas9',
 'MSI-High'
]


@portal.route('/')
def index():
    diseases = query_distinct_column(db, Assertion, 'disease')
    therapy_names = query_distinct_column(db, Assertion, 'therapy_name')

    num_genes = get_all_genes(db)
    num_assertions = db.session.query(Assertion).count()

    return render_template('portal_index.html',
                           nav_current_page='index',
                           num_genes=num_genes,
                           num_assertions=num_assertions,
                           diseases=[d for d in sorted(diseases) if not d == 'Oncotree Term'],
                           pred_impls=IMPLICATION_LEVELS,
                           therapy_names=[t for t in sorted(therapy_names) if not t == 'Therapy name']
                           )


@portal.route('/about')
def about():
    return render_template('portal_about.html',
                           nav_current_page='about')


@portal.route('/approve_submission')
def approve_submission():
    """As an admin, approve a submission for inclusion in the searchable database"""
    assertion_id = int(request.args['assertion_id'])
    assertion_to_submit = db.session.query(Assertion).filter(Assertion.assertion_id == assertion_id,
                                                             Assertion.validated == 0).first()
    db.session.add(assertion_to_submit)
    assertion_to_submit.validated = True
    db.session.commit()

    return http200response()


@portal.route('/delete_submission')
def delete_submission():
    assertion_id = int(request.args['assertion_id'])
    assertion_to_delete = db.session.query(Assertion).filter(Assertion.assertion_id == assertion_id,
                                                             Assertion.validated == 0).first()

    if assertion_to_delete:
        delete_assertion(db, assertion_to_delete)
        db.session.commit()

        return http200response()

    return http404response()


@portal.route('/amend', methods=['POST'])
def amend():
    """As an admin, update the value for a submission before approving it"""

    amendment = request.form
    attribute_name = amendment.get('attribute_name').strip()
    assertion_id = int(amendment.get('assertion_id'))
    current_value = amendment.get('current_value').strip()
    doi = amendment.get('doi').strip()

    if current_value.lower() == 'none':
        current_value = None
    new_value = amendment.get('new_value').strip()

    assertion = db.session.query(Assertion).get(assertion_id)
    db.session.add(assertion)
    if assertion.validated:
        BadRequest("Cannot amend assertion {} as it is already validated".format(assertion_id))

    editable_attrs = ['therapy_name', 'therapy_sensitivity', 'favorable_prognosis', 'cite_text']
    if attribute_name not in editable_attrs:
        BadRequest('Attribute {} is not editable'.format(attribute_name))

    if attribute_name == 'therapy_name':
        assertion.therapy_name = new_value
        db.session.commit()

        return http200response()
    elif attribute_name == 'cite_text':
        amend_cite_text_for_assertion(db, assertion, doi, new_value)
        db.session.commit()

        return http200response()
    elif attribute_name == 'therapy_sensitivity':
        sensitivity_transformation = {
            'sensitivity': True,
            'sensitive': True,
            'resistance': False,
            'resistant': False,
            'none': None,
            'null': None
        }

        if new_value.lower() not in sensitivity_transformation:
            BadRequest("{} not one of Sensitivity, Resistance, None".format(new_value))

        assertion.therapy_sensitivity = sensitivity_transformation.get(new_value.lower(), None)
        db.session.commit()

        return http200response()
    elif attribute_name == 'favorable_prognosis':
        prognosis_transformation = {
            'good': True,
            'poor': False,
            'bad': False,
            'none': None,
            'null': None
        }

        if new_value.lower() not in prognosis_transformation:
            BadRequest("{} not one of Good, Bad, None".format(new_value))

        assertion.favorable_prognosis = prognosis_transformation.get(new_value.lower(), None)
        db.session.commit()

        return http200response()


@portal.route('/approve')
@basic_auth.required
def approve():
    """Render the page on which admins can view submitted suggestions"""

    rows = get_unapproved_assertion_rows(db)

    return render_template('admin_approval.html',
                           nav_current_page='approve',
                           pred_impl_orders=IMPLICATION_LEVELS_SORT,
                           rows=rows)


@portal.route('/submit', methods=['POST'])
def submit():
    """Submit an assertion for consideration for inclusion in the database"""

    required_data = {}
    attribute_data = {}
    for key, value in request.form.items():
        attribute_match = re.match(r'^attribute-(\d+)$', key)
        if attribute_match:
            attribute_data[attribute_match.group(1)] = value
        else:
            required_data[key] = value

    if not required_data['source']:
        return http400response('Please fill in source field')
    if not required_data['email']:
        return http400response('Please fill in email')
    if not required_data['feature_id']:
        return http400response('Please select a feature')
    if not required_data['implication'] or required_data['implication'] not in IMPLICATION_LEVELS:
        implication = None
    if not required_data['type']:
        return http400response('Please select a cancer type')

    assertion = Assertion()
    assertion.validated = False
    assertion.predictive_implication = required_data['implication']
    assertion.therapy_type = required_data['therapy']
    assertion.disease = required_data['type']
    assertion.old_disease = required_data['type']
    assertion.submitted_by = required_data['email']

    feature_set = FeatureSet(assertion=assertion)
    feature_def = FeatureDefinition.query.get(required_data['feature_id'])
    feature = Feature(feature_set=feature_set, feature_definition=feature_def)
    for attribute_def_id, attribute_value in attribute_data.items():
        feature.attributes.append(FeatureAttribute(
            feature_id=required_data['feature_id'],
            attribute_def_id=attribute_def_id,
            value=attribute_value
        ))

    feature_set.features.append(feature)
    assertion.feature_sets.append(feature_set)
    assertion.sources.append(add_or_fetch_source(db, required_data['source']))

    db.session.add(assertion)
    db.session.commit()

    return http200response(message={
        'email': required_data['email'],
        'therapy': required_data['therapy'] or 'None',
        'implication': required_data['implication'] or 'None',
        'type': required_data['type'],
        'source': required_data['source'],
        'feature_name': feature_def.name
     })


@portal.route('/add')
def add():
    """Render the page through which clients can submit Assertion suggestions"""

    features_definitions = FeatureDefinition.query.all()

    return render_template('portal_add.html',
                           feature_definitions=features_definitions,
                           nav_current_page='add',
                           )


@portal.route('/search')
def search():
    """
    Almanac search function. Allows two search methods: Provision of a "unified search string" or individual
    specification of "search needles" using separate GET parameters (for gene, disease, etc.).

    Multiple queries are allowed within each category, and are wrapped into a boolean OR statement. Queries across
    categories are wrapped into a boolean AND statement. E.g.: A query for genes PTEN and POLE plus disease Uterine
    Leiomyoma would be interpreted as "(gene is PTEN OR POLE) AND (disease is Uterine Leiomyoma)". The results would
    be every assertion about Uterine Leiomyoma that references either the PTEN or POLE genes.
    """

    needles = {'feature': [], 'disease': [], 'pred': [], 'therapy': []}
    unified_search_args = request.args.getlist('s')
    if unified_search_args:
        unified_search_str = ' '.join(unified_search_args)
        # Note that we skip the 'unknown' needles in the interpreted query
        query = interpret_unified_search_string(db, unified_search_str)

        for key in needles.keys():
            needles[key] = query[key]

    rows = []
    if any(needles.values()):
        # filter_components aggregates the filters we will apply to Assertion. No matter the search, we will always join
        # the Assertion, AssertionToAlteration, and Alteration tables together, and we will always include the assertion
        # "validated=True" filter.
        filter_components = [
            Assertion.assertion_id == AssertionToAlteration.assertion_id,
            Alteration.alt_id == AssertionToAlteration.alt_id,
            Assertion.validated.is_(True)
        ]

        if needles['feature']:
            or_stmt = [Alteration.gene_name.ilike(gene) for gene in needles['feature']]
            filter_components.append(or_(*or_stmt))

        if needles['disease']:
            or_stmt = [Assertion.disease.ilike(cancer) for cancer in needles['disease']]
            filter_components.append(or_(*or_stmt))

        if needles['pred']:
            or_stmt = [Assertion.predictive_implication.ilike(pred) for pred in needles['pred']]
            filter_components.append(or_(*or_stmt))

        if needles['therapy']:
            or_stmt = [Assertion.therapy_name.ilike(therapy) for therapy in needles['therapy']]
            filter_components.append(or_(*or_stmt))

        # The following produces a list of tuples, where each tuple contains the following table objects:
        # (Assertion, AssertionToAlteration, Alteration)
        results = (db.session.query(Assertion, AssertionToAlteration, Alteration)
                   .filter(*filter_components).all())

        # In below, result[0] = Assertion; result[2] = Alteration
        for result in results:
            rows.append(make_rows(result[2], result[0]))

    return render_template('portal_search_results.html', rows=rows)


@portal.route('/assertion/<int:assertion_id>')
def assertion(assertion_id):
    assertion = db.session.query(Assertion).filter(Assertion.assertion_id == assertion_id).first()

    return render_template('portal_assertion.html',
                           assertion=assertion)
