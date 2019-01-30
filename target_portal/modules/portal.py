from flask import Blueprint, request, render_template, flash, redirect, url_for, make_response
import simplejson as json

from werkzeug.exceptions import BadRequest

import urllib

from db import db
from .models import Alteration, Assertion, Source, AssertionToAlteration, AssertionToSource
from .helper_functions import get_unapproved_assertion_rows, make_row, http404response, http200response, \
    query_distinct_column, add_or_fetch_alteration, add_or_fetch_source, delete_assertion, \
    amend_alteration_for_assertion, amend_cite_text_for_assertion, http400response, get_typeahead_genes

portal = Blueprint('portal', __name__)

IMPLICATION_LEVELS = ['FDA-Approved', 'Level A', 'Level B', 'Level C', 'Level D', 'Level E']
ALTERATION_CLASSES = [
    'Aneuploidy', 'CopyNumber', 'Germline', 'Knockout', 'MicrosatelliteStability',
    'Mutation', 'MutationalBurden', 'MutationalSignature', 'NeoantigenBurden',
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

pred_impl_orders = {
    'FDA-Approved': 5,
    'Level A': 4,
    'Level B': 3,
    'Level C': 2,
    'Level D': 1,
    'Level E': 0
}


@portal.route('/')
def index():
    typeahead_genes = get_typeahead_genes(db)
    diseases = query_distinct_column(db, Assertion, 'disease')
    therapy_names = query_distinct_column(db, Assertion, 'therapy_name')

    num_genes = db.session.query(Alteration.gene_name).distinct().count()
    num_assertions = db.session.query(Assertion).count()

    return render_template('portal_index.html',
                           nav_current_page='index',
                           num_genes=num_genes,
                           num_assertions=num_assertions,
                           typeahead_genes=typeahead_genes,
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

    editable_attrs = ['alt', 'therapy_name', 'cite_text', 'therapy_sensitivity', 'favorable_prognosis']
    if attribute_name not in editable_attrs:
        BadRequest('Attribute {} is not editable'.format(attribute_name))

    if attribute_name == 'alt':
        # Edit alteration. Doing this will mean that the assertion is tied to either a) a different Alteration that
        # already exists using this newly specified alteration, or b) a brand new one that we create now if no existing
        # Alterations would match this updated Alteration
        new_alt_value = new_value
        current_alt_value = current_value
        amend_alteration_for_assertion(db, assertion, current_alt_value, new_alt_value)
        db.session.commit()
        return http200response()
    elif attribute_name == 'therapy_name':
        # Edit the therapy name.
        assertion.therapy_name = new_value
        db.session.commit()
        return http200response()
    elif attribute_name == 'cite_text':
        # Edit the source citation text
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
def approve():
    """Render the page on which admnins can view submitted suggestions"""
    rows = get_unapproved_assertion_rows(db)
    return render_template('admin_approval.html',
                           nav_current_page='approve',
                           pred_impl_orders=pred_impl_orders,
                           rows=rows)


@portal.route('/submit', methods=['POST'])
def submit():
    """Submit an assertion for consideration for inclusion in the database"""
    submission = request.form
    therapy = submission.get('therapy').strip()
    cancer_type = submission.get('type').strip()
    implication = submission.get('implication').strip()
    gene = submission.get('gene').strip()
    doi = submission.get('source').strip()
    alt_class = submission.get('class').strip()
    effect = submission.get('effect').strip()
    alt = submission.get('alteration').strip()
    email = submission.get('email').strip()

    if not (gene and doi and email):
        return http400response("Please fill in gene symbol, DOI, and email fields")
    if not effect or effect not in EFFECTS:
        return http400response("Please select an effect type")
    if not alt_class or alt_class not in ALTERATION_CLASSES:
        return http400response("Please select an alteration feature")
    if not implication or implication not in IMPLICATION_LEVELS:
        implication = None
    if not cancer_type or cancer_type == 'Select a cancer type':
        return http400response("Please select a cancer type")

    alteration = add_or_fetch_alteration(db, gene, effect, alt_class, alt)
    source = add_or_fetch_source(db, doi)

    assertion = Assertion()
    assertion.validated = False
    assertion.alterations.append(alteration)
    assertion.predictive_implication = implication
    assertion.therapy_type = therapy
    assertion.disease = cancer_type
    assertion.old_disease = cancer_type
    assertion.sources.append(source)
    assertion.submitted_by = email
    db.session.add(assertion)
    db.session.commit()

    return http200response(message={'email': email,
                                    'therapy': therapy or 'None',
                                    'implication': implication or 'None',
                                    'gene': gene,
                                    'type': cancer_type,
                                    'alt_class': alt_class or 'None',
                                    'effect': effect or 'None',
                                    'alteration': alt or 'None',
                                    'source': doi})


@portal.route('/add')
def add():
    """Render the page through which clients can submit Assertion suggestions"""
    typeahead_genes = get_typeahead_genes(db)
    diseases = query_distinct_column(db, Assertion, 'disease')
    pred_impls = query_distinct_column(db, Assertion, 'predictive_implication')
    therapy_names = query_distinct_column(db, Assertion, 'therapy_name')

    num_genes = db.session.query(Alteration.gene_name).distinct().count()
    num_assertions = db.session.query(Assertion).count()

    return render_template('portal_add.html',
                           nav_current_page='add',
                           num_genes=num_genes,
                           num_assertions=num_assertions,
                           typeahead_genes=typeahead_genes,
                           diseases=[d for d in sorted(diseases) if not d == 'Oncotree Term'],
                           pred_impls=IMPLICATION_LEVELS,
                           alteration_classes=ALTERATION_CLASSES,
                           effects=EFFECTS,
                           therapy_names=[t for t in sorted(therapy_names) if not t == 'Therapy name']
                           )


@portal.route('/search')
def search():
    typeahead_genes = get_typeahead_genes(db)
    gene_needle = request.args.get('g')
    cancer_needle = request.args.get('d')
    pred_impl_needle = request.args.get('p')
    therapy_needle = request.args.get('t')

    rows = []
    if gene_needle:
        alts = db.session.query(Alteration).filter(Alteration.gene_name.like('%'+gene_needle+'%')).all()
        for alt in alts:
            for assertion in alt.assertions:
                if assertion.validated is True:
                    rows.append(make_row(alt, assertion))

    elif cancer_needle or pred_impl_needle or therapy_needle:
        assertions = []
        if cancer_needle:
            assertions = db.session.query(Assertion).filter(Assertion.disease == cancer_needle,
                                                            Assertion.validated.is_(True)).all()
        if pred_impl_needle:
            assertions = db.session.query(Assertion).filter(Assertion.predictive_implication == pred_impl_needle,
                                                            Assertion.validated.is_(True)).all()
        if therapy_needle:
            assertions = db.session.query(Assertion).filter(Assertion.therapy_name == therapy_needle,
                                                            Assertion.validated.is_(True)).all()

        for assertion in assertions:
            for alt in assertion.alterations:
                rows.append(make_row(alt, assertion))

    return render_template('portal_search_results.html',
                           typeahead_genes=typeahead_genes,
                           pred_impl_orders=pred_impl_orders,
                           rows=rows)


@portal.route('/assertion/<int:assertion_id>')
def assertion(assertion_id):
    assertion = db.session.query(Assertion).filter(Assertion.assertion_id == assertion_id).first()

    return render_template('portal_assertion.html',
                           assertion=assertion)
