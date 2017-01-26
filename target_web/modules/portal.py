from flask import Blueprint, render_template, flash, redirect, url_for

from db import db
from models import Alteration, Assertion, Source, AssertionToAlteration, AssertionToSource

portal = Blueprint('portal', __name__)

@portal.route('/')
def index():
    all_asserts = Assertion.query.all()
    all_asserts.reverse()

    return render_template('portal_index.html',
                           assertions=all_asserts)

@portal.route('/delete/<int:assert_id>')
def delete(assert_id):
    Assertion.query.filter_by(assertion_id=assert_id).delete()
    db.session.commit()

    flash('Deleted assertion.')
    return redirect(url_for('portal.index'))
