from flask import Blueprint, render_template

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
    needle = Assertion.query.filter_by(assertion_id=assert_id).one()
    db.session.delete(needle)
    db.session.commit()

    return 'Assertion %s deleted.' % str(assert_id)
