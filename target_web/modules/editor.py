from flask import Blueprint, render_template
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, validators, fields

editor = Blueprint('editor', __name__)

class AlterationForm(FlaskForm):
    feature_type = StringField(label='Feature type',
                                   validators=[validators.InputRequired(message='A feature type is required.')])
    gene_name = StringField(label='Gene name')
    type = StringField(label='Alteration type')
    alteration = StringField(label='Alteration')

    def __init__(self, csrf_enabled=False, *args, **kwargs):
        super(AlterationForm, self).__init__(csrf_enabled=csrf_enabled, *args, **kwargs)

class AssertionForm(FlaskForm):
    disease = StringField(label='Disease',
                                 validators=[validators.InputRequired(message='A disease is required.')])
    therapy_name = StringField(label='Therapy name')
    therapy_type = StringField(label='Therapy type')
    pred_impl = StringField(label='Predictive implication')
    description = StringField(label='Description')
    therapy_sensitivity = BooleanField(label='Alteration(s) cause sensitivity to this therapy?')
    favorable_prognosis = BooleanField(label='Alteration(s) predict favorable prognosis?')

    def __init__(self, csrf_enabled=False, *args, **kwargs):
        super(AssertionForm, self).__init__(csrf_enabled=csrf_enabled, *args, **kwargs)

class SourceForm(FlaskForm):
    doi = StringField(label='DOI')
    cite_text = StringField(label='Cite text',
                              validators=[validators.InputRequired(message='Citation text is required.')])

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
        return str(editor_form.data)

    return render_template('editor_index.html',
                           editor_form=editor_form,
                           alt_form=alt_form,
                           assert_form=assert_form,
                           source_form=source_form)
