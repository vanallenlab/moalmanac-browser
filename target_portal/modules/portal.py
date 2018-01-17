from flask import Blueprint, request, render_template, flash, redirect, url_for, make_response
import simplejson as json

from werkzeug.exceptions import BadRequest

from db import db
from .models import Alteration, Assertion, Source, AssertionToAlteration, AssertionToSource

portal = Blueprint('portal', __name__)

IMPLICATION_LEVELS = ['FDA-Approved', 'Level A', 'Level B', 'Level C', 'Level D', 'Level E']
ALTERATION_CLASSES = ['Rearrangement', 'Mutation', 'CNV', 'Germline Mutation', 'Knockout', 'Silencing', 'MSI']
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
}


def http200response():
    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


def http404response():
    return json.dumps({'success': False}), 404, {'ContentType': 'application/json'}

def _filter_row_column(query_results, column):
    return [getattr(row, column) for row in query_results if getattr(row, column) not in [None, '']]


def _query_distinct_column(model, column):
    query = db.session.query(getattr(model, column).distinct().label(column))
    return _filter_row_column(query, column)


@portal.route('/')
def index():
    typeahead_genes = _query_distinct_column(Alteration, 'gene_name')
    diseases = _query_distinct_column(Assertion, 'disease')
    pred_impls = _query_distinct_column(Assertion, 'predictive_implication')
    therapy_names = _query_distinct_column(Assertion, 'therapy_name')

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
        # Before deleting the assertion, check whether deleting it would orphan any rows in the Source or Alteration
        # tables, and delete these if so.
        for alt in assertion_to_delete.alterations:
            other_assertions_with_same_alteration = db.session.query(AssertionToAlteration)\
                .filter(AssertionToAlteration.alt_id == alt.alt_id,
                        AssertionToAlteration.assertion_id != assertion_to_delete.assertion_id).all()
            if not other_assertions_with_same_alteration:
                db.session.delete(alt)

        for s in assertion_to_delete.sources:
            other_assertions_with_same_source = db.session.query(AssertionToSource)\
                .filter(AssertionToSource.source_id == s.source_id,
                        AssertionToSource.assertion_id != assertion_to_delete.assertion_id).all()
            if not other_assertions_with_same_source:
                db.session.delete(s)

        db.session.delete(assertion_to_delete)
        db.session.commit()
        return http200response()
    return http404response()


def _get_unapproved_assertion_rows():
    unapproved_assertions = db.session.query(Assertion).filter(Assertion.validated == 0).all()
    rows = []
    for assertion in unapproved_assertions:
        for alt in assertion.alterations:
            rows.append(_make_row(alt, assertion))
    return rows


@portal.route('/approve')
def approve():
    rows = _get_unapproved_assertion_rows()
    return render_template('admin_approval.html',
                           nav_current_page='approve',
                           pred_impl_orders=pred_impl_orders,
                           rows=rows)


@portal.route('/submit', methods=['POST'])
def submit():
    submission = request.form
    therapy = submission.get('therapy').strip()
    cancer_type = submission.get('type').strip()
    implication = submission.get('implication').strip()
    gene = submission.get('gene').strip()
    doi = submission.get('source').strip()
    _class = submission.get('class').strip()
    effect = submission.get('effect').strip()
    email = submission.get('email').strip()

    if not therapy or therapy == 'Select therapy':
        raise BadRequest("Please select a therapy")
    if not implication or implication == 'Select predictive implication level':
        raise BadRequest("Please select a predictive implication level")
    if not cancer_type or cancer_type == 'Select a cancer type':
        raise BadRequest("Please select a cancer type")
    if not gene:
        raise BadRequest("Please enter a valid HGNC gene symbol")
    if not doi:
        raise BadRequest("Please enter a valid source DOI")
    if not email:
        raise BadRequest("Please enter a valid email")

    existing_alteration = db.session.query(Alteration).filter(Alteration.gene_name == gene,
                                                              Alteration.alt_type == effect,
                                                              Alteration.feature == _class).all()

    existing_source = db.session.query(Source).filter(Source.doi == doi).first()

    if not existing_alteration:
        alteration = Alteration()
        alteration.feature = _class
        alteration.alt_type = effect
        alteration.gene_name = gene
        db.session.add(alteration)
        db.session.flush()

    if existing_source:
        source = existing_source
    else:
        source = Source()
        source.doi = doi
        db.session.add(source)
        db.session.flush()

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

    return render_template('portal_add.html',
                           nav_current_page='add')


@portal.route('/add')
def add():
    typeahead_genes = _query_distinct_column(Alteration, 'gene_name')
    diseases = _query_distinct_column(Assertion, 'disease')
    pred_impls = _query_distinct_column(Assertion, 'predictive_implication')
    therapy_names = _query_distinct_column(Assertion, 'therapy_name')

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


def _make_row(alt, assertion):
    return {
        'gene_name': alt.gene_name,
        'feature': alt.feature,
        'alt_type': alt.alt_type,
        'alt': alt.alt,
        'alt_id': alt.alt_id,
        'therapy_name': assertion.therapy_name,
        'therapy_sensitivity': assertion.therapy_sensitivity,
        'disease': assertion.disease,
        'submitter': assertion.submitted_by,
        'predictive_implication': assertion.predictive_implication,
        'assertion_id': assertion.assertion_id,
        'sources': [s for s in assertion.sources]
    }


@portal.route('/search')
def search():
    typeahead_genes = _query_distinct_column(Alteration, 'gene_name')

    gene_needle = request.args.get('g')
    cancer_needle = request.args.get('d')
    pred_impl_needle = request.args.get('p')
    therapy_needle = request.args.get('t')

    rows = []
    if gene_needle:
        alts = db.session.query(Alteration).filter(Alteration.gene_name.like('%'+gene_needle+'%')).all()
        for alt in alts:
            for assertion in alt.assertions:
                rows.append(_make_row(alt, assertion))
    elif cancer_needle or pred_impl_needle or therapy_needle:
        if cancer_needle:
            assertions = db.session.query(Assertion).filter(Assertion.disease == cancer_needle).all()
        if pred_impl_needle:
            assertions = db.session.query(Assertion).filter(Assertion.predictive_implication == pred_impl_needle).all()
        if therapy_needle:
            assertions = db.session.query(Assertion).filter(Assertion.therapy_name == therapy_needle).all()

        for assertion in assertions:
            for alt in assertion.alterations:
                rows.append(_make_row(alt, assertion))

    return render_template('portal_search_results.html',
                           typeahead_genes=typeahead_genes,
                           pred_impl_orders=pred_impl_orders,
                           rows=rows)


@portal.route('/assertion/<int:assertion_id>')
def assertion(assertion_id):
    assertion = db.session.query(Assertion).filter(Assertion.assertion_id == assertion_id).first()

    return render_template('portal_assertion.html',
                           assertion=assertion)
