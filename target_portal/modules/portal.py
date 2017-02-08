from flask import Blueprint, render_template, flash, redirect, url_for

from db import db
from models import Alteration, Assertion, Source, AssertionToAlteration, AssertionToSource

portal = Blueprint('portal', __name__)

@portal.route('/')
def index():
	query = db.session.query(Alteration.gene_name.distinct().label('gene_name'))
	typeahead_genes = [row.gene_name for row in query.all() if row.gene_name not in [None, '']]

	return render_template('portal_index.html', typeahead_genes=typeahead_genes)

@portal.route('/delete/<int:assert_id>')
def delete(assert_id):
    Assertion.query.filter_by(assertion_id=assert_id).delete()
    db.session.commit()

    flash('Deleted assertion.')
    return redirect(url_for('portal.index'))
