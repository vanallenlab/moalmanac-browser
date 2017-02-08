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

    return render_template('portal_index.html',
                           typeahead_genes=typeahead_genes,
                           diseases=diseases,
                           pred_impls=pred_impls,
                           therapy_names=therapy_names)

@portal.route('/search')
def search():
    typeahead_genes = _query_distinct_column(Alteration, 'gene_name')
    gene_needle = request.args.get('g')
    alts = db.session.query(Alteration).filter(Alteration.gene_name.like('%'+gene_needle+'%')).all()
    pred_impl_orders = {
        'FDA-Approved': 5,
        'Level A': 4,
        'Level B': 3,
        'Level C': 2,
        'Level D': 1,
    }

    return render_template('portal_search_results.html',
                           typeahead_genes=typeahead_genes,
                           alts=alts,
                           pred_impl_orders=pred_impl_orders)

@portal.route('/delete/<int:assert_id>')
def delete(assert_id):
    Assertion.query.filter_by(assertion_id=assert_id).delete()
    db.session.commit()

    flash('Deleted assertion.')
    return redirect(url_for('portal.index'))
