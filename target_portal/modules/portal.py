from flask import Blueprint, request, render_template, flash, redirect, url_for, make_response
import simplejson as json
import pandas as pd

from werkzeug.exceptions import BadRequest

import urllib

from db import db
from auth import basic_auth
from sqlalchemy import or_
from .models import Alteration, Assertion, Source, AssertionToAlteration, AssertionToSource
from .helper_functions import get_unapproved_assertion_rows, make_row, http404response, http200response, \
    query_distinct_column, add_or_fetch_alteration, add_or_fetch_source, delete_assertion, \
    amend_alteration_for_assertion, amend_cite_text_for_assertion, http400response, get_typeahead_genes, \
    interpret_unified_search_string

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
@basic_auth.required
def approve():
    """Render the page on which admnins can view submitted suggestions"""
    rows = get_unapproved_assertion_rows(db)
    return render_template('admin_approval.html',
                           nav_current_page='approve',
                           pred_impl_orders=IMPLICATION_LEVELS_SORT,
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
    """
    Almanac search function. Allows two search methods: Provision of a "unified search string" or individual
    specification of "search needles" using separate GET parameters (for gene, disease, etc.).

    Multiple queries are allowed within each category, and are wrapped into a boolean OR statement. Queries across
    categories are wrapped into a boolean AND statement. E.g.: A query for genes PTEN and POLE plus disease Uterine
    Leiomyoma would be interpreted as "(gene is PTEN OR POLE) AND (disease is Uterine Leiomyoma)". The results would
    be every assertion about Uterine Leiomyoma that references either the PTEN or POLE genes.
    """

    needles = {'gene': [], 'disease': [], 'pred': [], 'therapy': []}
    unified_search_string = request.args.get('s')
    if unified_search_string:
        # Note that we skip the 'unknown' needles in the interpreted query
        query = interpret_unified_search_string(db, unified_search_string)

        for key in needles.keys():
            needles[key] = query[key]
    else:
        # Fallback to individually specified needles, of which multiples may be separated by commas
        for get_key, needle_key in {'g': 'gene', 'd': 'disease', 'p': 'pred', 't': 'therapy'}.items():
            get_value = request.args.get(get_key)
            if get_value:
                needles[needle_key] = [value.strip() for value in get_value.split(',')]

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

        if needles['gene']:
            or_stmt = [Alteration.gene_name.ilike(gene) for gene in needles['gene']]
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
                   .filter(Assertion.assertion_id == AssertionToAlteration.assertion_id)
                   .filter(Alteration.alt_id == AssertionToAlteration.alt_id)
                   .filter(Assertion.validated.is_(True))
                   .filter(*filter_components).all())

        # In below, result[0] = Assertion; result[2] = Alteration
        for result in results:
            rows.append(make_row(result[2], result[0]))

    return render_template('portal_search_results.html',
                           typeahead_genes=get_typeahead_genes(db),
                           rows=rows)


@portal.route('/assertion/<int:assertion_id>')
def assertion(assertion_id):
    assertion = db.session.query(Assertion).filter(Assertion.assertion_id == assertion_id).first()

    return render_template('portal_assertion.html',
                           assertion=assertion)
