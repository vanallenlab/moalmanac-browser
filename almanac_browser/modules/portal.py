import re
import io
import csv
import urllib
from zipfile import ZipFile
from flask import Blueprint, request, render_template, send_file, Markup, redirect, url_for
from auth import basic_auth
from werkzeug.exceptions import BadRequest
from db import db
from .models import Assertion, Feature, FeatureAttribute, FeatureDefinition, AssertionToFeature, Version
from .helper_functions import IMPLICATION_LEVELS_SORT, get_unapproved_assertion_rows, make_rows, http404response, \
    http200response, query_distinct_column, add_or_fetch_source, delete_assertion, amend_cite_text_for_assertion, \
    http400response, \
    get_all_genes, unified_search, make_display_string

portal = Blueprint('portal', __name__)

IMPLICATION_LEVELS = ['FDA-Approved', 'Guideline', 'Clinical trial', 'Clinical evidence', 'Preclinical', 'Inferential']

ALTERATION_CLASSES = [
    'Aneuploidy', 'Copy Number', 'Germline', 'Knockdown', 'Microsatellite Stability',
    'Variant', 'Mutational Burden', 'Mutational Signature', 'Neoantigen Burden',
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

RESPONSES = [
    'Sensitivity',
    'Resistance',
    'Good prognosis',
    'Poor prognosis',
    'Not sensitive'
]


@portal.route('/')
def index():
    diseases = query_distinct_column(db, Assertion, 'disease')
    therapy_names = query_distinct_column(db, Assertion, 'therapy_name')

    num_genes = len(get_all_genes(db))
    num_assertions = db.session.query(Assertion).count()

    major = query_distinct_column(db, Version, 'major')
    minor = query_distinct_column(db, Version, 'minor')
    patch = query_distinct_column(db, Version, 'patch')
    release = query_distinct_column(db, Version, 'release')
    version_string = str(major[0]) + '.' + str(minor[0]) + '.' + str(patch[0])
    release_string = str(release[0])

    return render_template('portal_index.html',
                           nav_current_page='index',
                           num_genes=num_genes,
                           num_assertions=num_assertions,
                           diseases=[d for d in sorted(diseases) if not d == 'Oncotree Term'],
                           pred_impls=IMPLICATION_LEVELS,
                           therapy_names=[t for t in sorted(therapy_names) if not t == 'Therapy name'],
                           version_string=version_string,
                           release_string=release_string
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
    if assertion_to_submit:
        db.session.add(assertion_to_submit)
        assertion_to_submit.validated = True
        db.session.commit()

        return http200response(message='Assertion %s added.' % request.args['assertion_id'])

    return http400response(message='Assertion not found or already validated.')


@portal.route('/delete_submission')
def delete_submission():
    assertion_id = int(request.args['assertion_id'])
    assertion_to_delete = db.session.query(Assertion).filter(Assertion.assertion_id == assertion_id,
                                                             Assertion.validated == 0).first()

    if assertion_to_delete:
        delete_assertion(db, assertion_to_delete)
        db.session.commit()

        return http200response(message='Assertion %s deleted.' % request.args['assertion_id'])

    return http404response(message='Assertion %s not found or already validated.' % request.args['assertion_id'])


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
        return http400response('Please select an implication')
    if not required_data['type']:
        return http400response('Please select a cancer type')

    assertion = Assertion()
    assertion.validated = False
    assertion.predictive_implication = required_data['implication']
    assertion.therapy_name = required_data['therapy']
    assertion.disease = required_data['type']
    assertion.old_disease = required_data['type']
    assertion.submitted_by = required_data['email']

    feature_def = FeatureDefinition.query.get(required_data['feature_id'])
    feature = Feature(feature_definition=feature_def)
    for attribute_def_id, attribute_value in attribute_data.items():
        feature.attributes.append(FeatureAttribute(
            feature_id=required_data['feature_id'],
            attribute_def_id=attribute_def_id,
            value=attribute_value
        ))

    assertion.features.append(feature)
    assertion.sources.append(add_or_fetch_source(db, required_data['source']))

    db.session.add(assertion)
    db.session.commit()

    return http200response(message={
        'email': required_data['email'],
        'therapy': required_data['therapy'] or 'None',
        'implication': required_data['implication'],
        'type': required_data['type'],
        'source': required_data['source'],
        'feature_name': feature_def.name
    })


@portal.route('/add')
def add():
    """Render the page through which clients can submit Assertion suggestions"""

    feature_definitions = FeatureDefinition.query.all()

    return render_template('portal_add.html',
                           feature_definitions=feature_definitions,
                           nav_current_page='add',
                           )


@portal.route('/search')
def search():
    rows = []
    unified_search_args = request.args.getlist('s')
    if unified_search_args:
        unified_search_str = urllib.parse.unquote(' '.join(unified_search_args))

        # In below, result[0] = Assertion; result[1] = Feature
        results = unified_search(db, unified_search_str)
        for result in results:
            rows.extend(make_rows(result[0], result[1].feature))

    return render_template('portal_search_results.html', rows=rows)


@portal.route('/assertion/')
@portal.route('/assertion/<int:assertion_id>')
def assertion(assertion_id=None):
    if assertion_id is None:
        return redirect(url_for('portal.index'))

    assertion = db.session.query(Assertion).filter(Assertion.assertion_id == assertion_id).first()
    features = []
    for feature in assertion.features:
        string = Markup(make_display_string(feature))
        features.append((feature, string))

    return render_template('portal_assertion.html',
                           assertion=assertion, features=features)


@portal.route('/privacy_policy')
def privacy_policy():
    return render_template('portal_privacy_policy.html')


@portal.route('/terms')
def terms():
    return render_template('portal_terms.html')


@portal.route('/export', methods=['GET'])
def export():
    feature_defs = FeatureDefinition.query.all()

    zip_output = io.BytesIO()
    zip_file = ZipFile(zip_output, 'w')

    for feature_def in feature_defs:
        tsv_output = io.StringIO()
        tsv_writer = csv.writer(tsv_output, delimiter='\t')

        row = []
        # Write headers
        for attribute_definition in feature_def.attribute_definitions:
            row.append(attribute_definition.name)

        row.extend([
            'disease',
            'oncotree_code',
            'context',
            'therapy_name',
            'therapy_type',
            'therapy_sensitivity',
            'therapy_resistance',
            'favorable_prognosis',
            'predictive_implication',
            'description',
            'source_type',
            'citation',
            'url',
            'doi',
            'pmid',
            'nct',
            'last_updated'
        ])
        tsv_writer.writerow(row)

        for feature in feature_def.features:
            for assertion in (db.session.query(Assertion).join(AssertionToFeature).join(Feature).filter(
                    Feature.feature_id == feature.feature_id,
                    FeatureAttribute.feature_id == Feature.feature_id,
                    AssertionToFeature.feature_id == Feature.feature_id)):

                row = []
                for attribute in feature.attributes:
                    row.append(attribute.value)

                row.extend([
                    assertion.disease,
                    assertion.oncotree_code,
                    assertion.context,
                    assertion.therapy_name,
                    assertion.therapy_type,
                    assertion.therapy_sensitivity,
                    assertion.therapy_resistance,
                    assertion.favorable_prognosis,
                    assertion.predictive_implication,
                    assertion.description
                ])

                for source in assertion.sources:
                    row_per_source = row.copy()
                    row_per_source.append(source.source_type if source.source_type else '')
                    row_per_source.append(source.citation if source.citation else '')
                    row_per_source.append(source.url if source.url else '')
                    row_per_source.append(source.doi if source.doi else '')
                    row_per_source.append(source.pmid if source.pmid else '')
                    row_per_source.append(source.nct if source.nct else '')
                    row_per_source.append(assertion.last_updated)
                    tsv_writer.writerow(row_per_source)

        zip_file.writestr('%s.tsv' % feature_def.name, tsv_output.getvalue().encode('utf-8'))
        tsv_output.close()

    zip_file.close()
    zip_output.seek(0)

    major = query_distinct_column(db, Version, 'major')
    minor = query_distinct_column(db, Version, 'minor')
    patch = query_distinct_column(db, Version, 'patch')
    release = query_distinct_column(db, Version, 'release')
    version_string = str(major[0]) + '.' + str(minor[0]) + '.' + str(patch[0])
    release_string = str(release[0])

    zip_name = 'almanac.' + version_string + '.' + release_string  + '.zip'
    return send_file(zip_output, mimetype='application/zip', attachment_filename=zip_name, as_attachment=True)
