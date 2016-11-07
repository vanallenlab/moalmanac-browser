from flask import Blueprint, render_template, flash
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, validators, fields
from datetime import datetime

from db import db
from models import Alteration, Assertion, Source, AssertionToAlteration, AssertionToSource

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
    therapy_sensitivity = BooleanField(label='Alteration(s) cause sensitivity to this therapy?')
    favorable_prognosis = BooleanField(label='Alteration(s) predict favorable prognosis?')

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

@editor.route('/', methods=('GET', 'POST'))
def index():
    editor_form = EditorForm()
    alt_form = AlterationForm()
    assert_form = AssertionForm()
    source_form = SourceForm()

    if editor_form.validate_on_submit():
        new_sources = []
        for source_data in editor_form.data['source']:
            new_source = Source(doi=source_data['doi'],
                                cite_text=source_data['cite_text'],
                                source_type=source_data['source_type'])
            #db.session.add(new_source)
            #db.session.commit()
            #db.session.flush()
            new_sources.append(new_source)

        new_alterations = []
        for alt_data in editor_form.data['alteration']:
            old_alt = Alteration.query.filter_by(feature=alt_data['feature_type'],
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
                new_alterations.append(new_alt)

        db.session.bulk_save_objects(new_sources + new_alterations)
        db.session.commit()
        db.session.flush()

        new_assertions = []
        for assert_data in editor_form.data['assertion']:
            new_assert = Assertion(disease=assert_data['disease'],
                                   therapy_name=assert_data['therapy_name'],
                                   therapy_type=assert_data['therapy_type'],
                                   therapy_sensitivity=(assert_data['therapy_sensitivity'] == 'True'),
                                   predictive_implication=assert_data['pred_impl'],
                                   favorable_prognosis=(assert_data['favorable_prognosis'] == 'True'),
                                   description=assert_data['description'],
                                   last_updated=datetime.now())

            for source in new_sources:
                new_assert.sources.append(source)

            for alt in new_alterations:
                new_assert.alterations.append(alt)

            #db.session.add(new_assert)
            #db.session.commit()
            #db.session.flush()
            new_assertions.append(new_assert)

        db.session.bulk_save_objects(new_assertions)
        db.session.commit()
        db.session.flush()

        flash('Assertion added (%s).' % new_assertions[0].disease)

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
