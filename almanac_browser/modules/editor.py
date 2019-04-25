from flask import Blueprint, render_template, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, validators, fields
from datetime import datetime

from db import db
from .models import Assertion, Source, AssertionToSource

editor = Blueprint('editor', __name__)

class AlterationForm(FlaskForm):
    feature_type = StringField(label='Feature type',
                                   validators=[validators.InputRequired(message='A feature type is required.')])
    alt_type = StringField(label='Alteration type')
    gene_name = StringField(label='Gene name')
    alteration = StringField(label='Alteration')

    def __init__(self, csrf_enabled=False, *args, **kwargs):
        super(AlterationForm, self).__init__(csrf_enabled=csrf_enabled, *args, **kwargs)

class AssertionForm(FlaskForm):
    disease = StringField(label='Disease',
                          validators=[validators.InputRequired(message='A disease is required.')])
    stage = StringField(label='Stage')
    therapy_name = StringField(label='Therapy name')
    therapy_type = StringField(label='Therapy type')
    pred_impl = StringField(label='Predictive implication')
    description = StringField(label='Description')
    therapy_sensitivity = SelectField(label='Therapeutic implication',
                                      choices=[('null', 'N/A'), ('sensitive', 'Sensitivity'), ('resistant', 'Resistance')])
    favorable_prognosis = SelectField(label='Prognostic implication',
                                      choices=[('null', 'N/A'), ('favorable', 'Favorable'), ('negative', 'Negative')])

    def __init__(self, csrf_enabled=False, *args, **kwargs):
        super(AssertionForm, self).__init__(csrf_enabled=csrf_enabled, *args, **kwargs)

class SourceForm(FlaskForm):
    cite_text = StringField(label='Cite text',
                            validators=[validators.InputRequired(message='Citation text is required.')])
    doi = StringField(label='DOI')
    source_type = StringField(label='Source type')

    def __init__(self, csrf_enabled=False, *args, **kwargs):
        super(SourceForm, self).__init__(csrf_enabled=csrf_enabled, *args, **kwargs)

class EditorForm(FlaskForm):
    alteration = fields.FieldList(fields.FormField(AlterationForm))
    assertion = fields.FieldList(fields.FormField(AssertionForm))
    source = fields.FieldList(fields.FormField(SourceForm))

def insert_if_new(model, defaults=None, **kwargs):
    """
    Insert db_item if it does not already exist in the database.
    **kwargs contains the list of items that must match for a database row to be considered "identical."
    Returns (db_instance, bool), where the boolean value is True if an item was inserted and False otherwise.
    Adapted from http://stackoverflow.com/questions/2546207/does-sqlalchemy-have-an-equivalent-of-djangos-get-or-create
    """

    instance = db.session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = dict((k, v) for k, v in kwargs.iteritems())
        params.update(defaults or {})
        instance = model(**params)
        db.session.add(instance)
        return instance, True

@editor.route('/', methods=('GET', 'POST'))
def index():
    editor_form = EditorForm()
    alt_form = AlterationForm()
    assert_form = AssertionForm()
    source_form = SourceForm()

    if request.method == 'POST':
        if editor_form.validate_on_submit():
            new_sources = []
            for source_data in editor_form.data['source']:
                new_source, __ = insert_if_new(
                    Source,
                    doi=source_data['doi'],
                    cite_text=source_data['cite_text'],
                    source_type=source_data['source_type']
                )
                #new_source = Source(doi=source_data['doi'],
                #                    cite_text=source_data['cite_text'],
                #                    source_type=source_data['source_type'])
                #db.session.add(new_source)
                #db.session.commit()
                #db.session.flush()
                new_sources.append(new_source)

            new_alterations = []
            for alt_data in editor_form.data['alteration']:
                new_alt, __ = insert_if_new(
                    Alteration,
                    feature=alt_data['feature_type'],
                    alt_type=alt_data['alt_type'],
                    gene_name=alt_data['gene_name'],
                    alt=alt_data['alteration']
                )

                new_alterations.append(new_alt)
                """old_alt = Alteration.query.filter_by(feature=alt_data['feature_type'],
                                                     alt_type=alt_data['alt_type'],
                                                     gene_name=alt_data['gene_name'],
                                                     alt=alt_data['alteration']).first()

                if old_alt is not None:
                    new_alterations.append(old_alt)
                else:
                    new_alt = Alteration(feature=alt_data['feature_type'],
                                         alt_type=alt_data['alt_type'],
                                         gene_name=alt_data['gene_name'],
                                         alt=alt_data['alteration'])
                    #db.session.add(new_alt)
                    #db.session.commit()
                    #db.session.flush()
                    new_alterations.append(new_alt)"""

            db.session.bulk_save_objects(new_sources + new_alterations, return_defaults=True)
            db.session.commit()
            db.session.flush()

            assert_data = editor_form.data['assertion'][0]

            sensitivity = None
            if assert_data['therapy_sensitivity'] == 'sensitive': sensitivity = True
            elif assert_data['therapy_sensitivity'] == 'resistant': sensitivity = False

            prognosis = None
            if assert_data['favorable_prognosis'] == 'favorable': prognosis = True
            elif assert_data['favorable_prognosis'] == 'negative': prognosis = False
            new_assert = Assertion(disease=assert_data['disease'],
                                   therapy_name=assert_data['therapy_name'],
                                   therapy_type=assert_data['therapy_type'],
                                   therapy_sensitivity=sensitivity,
                                   predictive_implication=assert_data['pred_impl'],
                                   favorable_prognosis=prognosis,
                                   description=assert_data['description'],
                                   last_updated=datetime.now())

            for source in new_sources:
                new_assert.sources.append(source)

            for alt in new_alterations:
                new_assert.alterations.append(alt)

            db.session.add(new_assert)
            db.session.commit()
            db.session.flush()

            flash('Assertion added (%s).' % assert_data['therapy_sensitivity'])#new_assert.disease)
        else:
            flash('Error')

            """new_objs = []
            for assertion in new_assertions:
                for source in new_sources:
                    new_objs.append(AssertionToSource(assertion_id=assertion.assertion_id,
                                                      source_id=source.source_id))

                for alteration in new_alterations:
                    new_objs.append(AssertionToAlteration(assertion_id=assertion.assertion_id,
                                                          alt_id=alteration.alt_id))

            db.session.bulk_save_objects(new_objs)
            db.session.commit()"""


    return render_template('editor_index.html',
                           editor_form=editor_form,
                           alt_form=alt_form,
                           assert_form=assert_form,
                           source_form=source_form)
