from flask import Blueprint, request, render_template, flash, redirect, url_for, make_response
import simplejson as json

from werkzeug.exceptions import BadRequest

from db import db
from .models import Alteration, Assertion, Source, AssertionToAlteration, AssertionToSource
from .helper_functions import get_unapproved_assertion_rows, make_row, http404response, http200response, \
    query_distinct_column, add_or_fetch_alteration, add_or_fetch_source

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



@portal.route('/')
def index():
    typeahead_genes = query_distinct_column(db, Alteration, 'gene_name')
    diseases = query_distinct_column(db, Assertion, 'disease')
    pred_impls = query_distinct_column(db, Assertion, 'predictive_implication')
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


@portal.route('/approve')
def approve():
    rows = get_unapproved_assertion_rows(db)
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
    alt_class = submission.get('class').strip()
    effect = submission.get('effect').strip()
    alt = submission.get('alteration').strip()
    email = submission.get('email').strip()

    if not therapy or therapy == 'Select therapy':
        raise BadRequest("Please select a therapy")
    if not implication or implication == 'Select predictive implication level':
        raise BadRequest("Please select a predictive implication level")
    if not cancer_type or cancer_type == 'Select a cancer type':
        raise BadRequest("Please select a cancer type")
    if not (gene and doi and email):
        raise BadRequest("Missing gene, doi, or email")

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

    return render_template('portal_add.html',
                           nav_current_page='add')


@portal.route('/add')
def add():
    typeahead_genes = query_distinct_column(db, Alteration, 'gene_name')
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
    typeahead_genes = query_distinct_column(db, Alteration, 'gene_name')

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
                                                            Assertion.validated is True).all()
        if pred_impl_needle:
            assertions = db.session.query(Assertion).filter(Assertion.predictive_implication == pred_impl_needle,
                                                            Assertion.validated is True).all()
        if therapy_needle:
            assertions = db.session.query(Assertion).filter(Assertion.therapy_name == therapy_needle,
                                                            Assertion.validated is True).all()

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
