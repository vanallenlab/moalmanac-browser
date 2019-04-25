from flask_sqlalchemy import declarative_base
from almanac_browser import db, ma
from datetime import datetime

Base = declarative_base()


class FeatureSet(Base, db.Model):
    __tablename__ = 'Feature_Set'

    feature_set_id = db.Column('feature_set_id', db.Integer, primary_key=True)
    assertion_id = db.Column('assertion_id', db.Integer, db.ForeignKey('Assertion.assertion_id', ondelete='CASCADE'))

    assertion = db.relationship('Assertion')
    features = db.relationship('Feature', back_populates='feature_set', passive_deletes=True)


class FeatureDefinition(Base, db.Model):
    __tablename__ = 'Feature_Definition'

    feature_def_id = db.Column('feature_def_id', db.Integer, primary_key=True)
    name = db.Column('name', db.Text)
    readable_name = db.Column('readable_name', db.Text)
    is_germline = db.Column('is_germline', db.Boolean)

    attribute_definitions = db.relationship('FeatureAttributeDefinition')


class FeatureAttributeDefinition(Base, db.Model):
    __tablename__ = 'Feature_Attribute_Definition'

    attribute_def_id = db.Column('attribute_def_id', db.Integer, primary_key=True)
    feature_def_id = db.Column('feature_def_id', db.Integer,
                               db.ForeignKey(FeatureDefinition.feature_def_id, ondelete='CASCADE'))
    name = db.Column('name', db.Text)
    readable_name = db.Column('readable_name', db.Text)
    type = db.Column('type', db.Text)

    db.UniqueConstraint('feature_def_id', 'name', name='UC_feature_def_id_name')

    feature_definition = db.relationship('FeatureDefinition', back_populates='attribute_definitions')


class Feature(Base, db.Model):
    __tablename__ = 'Feature'

    feature_id = db.Column('feature_id', db.Integer, primary_key=True)
    feature_set_id = db.Column('feature_set_id', db.Integer,
                               db.ForeignKey(FeatureSet.feature_set_id, ondelete='CASCADE'))
    feature_def_id = db.Column('feature_def_id', db.Integer, db.ForeignKey(FeatureDefinition.feature_def_id))

    attributes = db.relationship('FeatureAttribute', back_populates='feature', passive_deletes=True)
    feature_set = db.relationship('FeatureSet', back_populates='features')
    feature_definition = db.relationship('FeatureDefinition', foreign_keys=feature_def_id, backref='features')


class FeatureAttribute(Base, db.Model):
    __tablename__ = 'Feature_Attribute'

    attribute_id = db.Column('attribute_id', db.Integer, primary_key=True)
    feature_id = db.Column('feature_id', db.Integer, db.ForeignKey(Feature.feature_id, ondelete='CASCADE'))
    attribute_def_id = db.Column('attribute_def_id', db.Integer,
                                 db.ForeignKey(FeatureAttributeDefinition.attribute_def_id))
    value = db.Column('value', db.Text)

    feature = db.relationship('Feature', back_populates='attributes')
    attribute_definition = db.relationship('FeatureAttributeDefinition', foreign_keys=attribute_def_id,
                                           backref='attributes')


class Assertion(Base, db.Model):
    __tablename__ = 'Assertion'

    assertion_id = db.Column('assertion_id', db.Integer, primary_key=True)
    created_on = db.Column('created_on', db.Text, default=datetime.now)
    last_updated = db.Column('last_updated', db.Text, default=datetime.now)
    disease = db.Column('oncotree_term', db.Text)
    old_disease = db.Column('disease', db.Text)
    oncotree_code = db.Column('oncotree_code', db.Text)
    stage = db.Column('stage', db.Integer)
    therapy_name = db.Column('therapy_name', db.Text)
    therapy_type = db.Column('therapy_type', db.Text)
    therapy_sensitivity = db.Column('therapy_sensitivity', db.Boolean)
    therapy_resistance = db.Column('therapy_resistance', db.Boolean)
    predictive_implication = db.Column('predictive_implication', db.Enum('FDA-Approved',
                                                                         'Guideline',
                                                                         'Clinical trial',
                                                                         'Clinical evidence',
                                                                         'Preclinical',
                                                                         'Inferential',
                                                                         'Predictive implication'))
    validated = db.Column('validated', db.Boolean, default=False)
    submitted_by = db.Column('submitted_by', db.Text)
    favorable_prognosis = db.Column('favorable_prognosis', db.Boolean)
    description = db.Column('description', db.Text)

    feature_sets = db.relationship('FeatureSet', back_populates='assertion', passive_deletes=True)
    sources = db.relationship('Source', secondary='Assertion_To_Source', uselist=True)


class Source(Base, db.Model):
    __tablename__ = 'Source'

    source_id = db.Column('source_id', db.Integer, primary_key=True)
    doi = db.Column('doi', db.Text)
    cite_text = db.Column('cite_text', db.Text)
    source_type = db.Column('source_type', db.Text)

    assertions = db.relationship('Assertion', secondary='Assertion_To_Source')


class AssertionToSource(Base, db.Model):
    __tablename__ = 'Assertion_To_Source'

    ats_id = db.Column('ats_id', db.Integer, primary_key=True)
    assertion_id = db.Column('assertion_id', db.Integer, db.ForeignKey(Assertion.assertion_id, ondelete='CASCADE'))
    source_id = db.Column('source_id', db.Integer, db.ForeignKey(Source.source_id))

    db.UniqueConstraint('source_id', 'assertion_id', name='UC_source_id_assertion_id')

    assertion = db.relationship('Assertion', foreign_keys=assertion_id)
    source = db.relationship('Source', foreign_keys=source_id)


class Version(Base, db.Model):
    __tablename__ = 'Version'

    major = db.Column('major', db.Integer, primary_key=True)
    minor = db.Column('minor', db.Integer)
    patch = db.Column('patch', db.Integer)


class AssertionSchema(ma.ModelSchema):
    class Meta:
        model = Assertion


class SourceSchema(ma.ModelSchema):
    class Meta:
        model = Source


class FeatureSchema(ma.ModelSchema):
    class Meta:
        model = Feature


class FeatureDefinitionSchema(ma.ModelSchema):
    class Meta:
        model = FeatureDefinition


class FeatureAttributeDefinitionSchema(ma.ModelSchema):
    class Meta:
        model = FeatureAttributeDefinition


class FeatureAttributeSchema(ma.ModelSchema):
    class Meta:
        model = FeatureAttribute
