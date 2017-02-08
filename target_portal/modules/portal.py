from flask import Blueprint, request, render_template, flash, redirect, url_for

from db import db
from models import Alteration, Assertion, Source, AssertionToAlteration, AssertionToSource

portal = Blueprint('portal', __name__)

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

    num_genes = db.session.query(Alteration).distinct(Alteration.gene_name).count()
    num_assertions = db.session.query(Assertion).count()

    return render_template('portal_index.html',
                           nav_current_page='index',
                           num_genes=num_genes,
                           num_assertions=num_assertions,
                           typeahead_genes=typeahead_genes,
                           diseases=diseases,
                           pred_impls=pred_impls,
                           therapy_names=therapy_names)

@portal.route('/search')
def search():
    def _make_row(alt, assertion):
        return {
            'gene_name': alt.gene_name,
            'feature': alt.feature,
            'alt_type': alt.alt_type,
            'alt': alt.alt,
            'therapy_name': assertion.therapy_name,
            'therapy_sensitivity': assertion.therapy_sensitivity,
            'disease': assertion.disease,
            'predictive_implication': assertion.predictive_implication,
            'assertion_id': assertion.assertion_id
        }

    typeahead_genes = _query_distinct_column(Alteration, 'gene_name')
    pred_impl_orders = {
        'FDA-Approved': 5,
        'Level A': 4,
        'Level B': 3,
        'Level C': 2,
        'Level D': 1,
    }


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

@portal.route('/delete/<int:assert_id>')
def delete(assert_id):
    Assertion.query.filter_by(assertion_id=assert_id).delete()
    db.session.commit()

    flash('Deleted assertion.')
    return redirect(url_for('portal.index'))
