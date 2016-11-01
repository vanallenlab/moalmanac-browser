from flask import Blueprint, render_template
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField
from wtforms.widgets import TextArea
from wtforms.validators import DataRequired

editor = Blueprint('editor', __name__)

class EditorForm(FlaskForm):
    alt_feature_type = StringField('Feature type', validators=[DataRequired()])
    alt_gene_name = StringField('Gene name')
    alt_type = StringField('Alteration type')
    alt_alteration = StringField('Alteration')

    assert_disease = StringField('Disease', validators=[DataRequired()])
    assert_therapy_name = StringField('Therapy name')
    assert_therapy_type = StringField('Therapy type')
    assert_pred_impl = StringField('Predictive implication')
    assert_description = StringField('Description', widget=TextArea())
    assert_therapy_sensitivity = BooleanField('Therapy sensitivity')
    assert_favorable_prognosis = BooleanField('Favorable prognosis')

    source_doi = StringField('DOI')
    source_cite_text = StringField('Cite text', widget=TextArea())

@editor.route('/', methods=('GET', 'POST'))
def index():
    form = EditorForm()

    if form.validate_on_submit():
        return form

    return render_template('editor_index.html', form=form)
