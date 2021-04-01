from flask_sqlalchemy import declarative_base
from almanac_browser import db, ma
from datetime import datetime
from marshmallow_sqlalchemy import fields

Base = declarative_base()


class FeatureDefinition(Base, db.Model):
    __tablename__ = 'Feature_Definition'

    feature_def_id = db.Column('feature_def_id', db.Integer, primary_key=True)
    name = db.Column('name', db.Text)
    readable_name = db.Column('readable_name', db.Text)

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
    feature_def_id = db.Column('feature_def_id', db.Integer, db.ForeignKey(FeatureDefinition.feature_def_id))

    attributes = db.relationship('FeatureAttribute', back_populates='feature', passive_deletes=True)
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
    disease = db.Column('disease', db.Text)
    context = db.Column('context', db.Text)
    oncotree_term = db.Column('oncotree_term', db.Text)
    oncotree_code = db.Column('oncotree_code', db.Text)
    therapy_name = db.Column('therapy_name', db.Text)
    therapy_strategy = db.Column('therapy_strategy', db.Text)
    therapy_type = db.Column('therapy_type', db.Text)
    therapy_sensitivity = db.Column('therapy_sensitivity', db.Boolean)
    therapy_resistance = db.Column('therapy_resistance', db.Boolean)
    favorable_prognosis = db.Column('favorable_prognosis', db.Boolean)
    predictive_implication = db.Column('predictive_implication', db.Enum('FDA-Approved',
                                                                         'Guideline',
                                                                         'Clinical trial',
                                                                         'Clinical evidence',
                                                                         'Preclinical',
                                                                         'Inferential',
                                                                         'Predictive implication'))
    description = db.Column('description', db.Text)
    created_on = db.Column('created_on', db.Text, default=datetime.now)
    last_updated = db.Column('last_updated', db.Text, default=datetime.now)
    validated = db.Column('validated', db.Boolean, default=False)
    submitted_by = db.Column('submitted_by', db.Text)

    features = db.relationship('Feature', secondary='Assertion_To_Feature', uselist=True)
    sources = db.relationship('Source', secondary='Assertion_To_Source', uselist=True)


class Source(Base, db.Model):
    __tablename__ = 'Source'

    source_id = db.Column('source_id', db.Integer, primary_key=True)
    source_type = db.Column('source_type', db.Text)
    citation = db.Column('citation', db.Text)
    url = db.Column('url', db.Text)
    doi = db.Column('doi', db.Text)
    pmid = db.Column('pmid', db.Text)
    nct = db.Column('nct', db.Text)

    assertions = db.relationship('Assertion', secondary='Assertion_To_Source')


class AssertionToFeature(Base, db.Model):
    __tablename__ = 'Assertion_To_Feature'

    atf_id = db.Column('atf_id', db.Integer, primary_key=True)
    assertion_id = db.Column('assertion_id', db.Integer, db.ForeignKey(Assertion.assertion_id, ondelete='CASCADE'))
    feature_id = db.Column('feature_id', db.Integer, db.ForeignKey(Feature.feature_id))

    db.UniqueConstraint('feature_id', 'assertion_id', name='UC_feature_id_assertion_id')

    assertion = db.relationship('Assertion', foreign_keys=assertion_id)
    feature = db.relationship('Feature', foreign_keys=feature_id)


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
    release = db.Column('release', db.String)


class SourceSchema(ma.Schema):
    class Meta:
        fields = ("source_id", "source_type", "citation", "url", "doi", "pmid", "nct", "assertions")


class FeatureAttributeSchema(ma.Schema):
    class Meta:
        fields = ("attribute_id", "attribute_definition", "feature", "value")


class FeatureAttributeDefinitionSchema(ma.Schema):
    class Meta:
        fields = ("attribute_def_id", "attributes", "feature_definition", "name", "readable_name", "type")
    attributes = fields.Nested(FeatureAttributeSchema, many=True)


class FeatureDefinitionSchema(ma.Schema):
    class Meta:
        fields = ("attribute_definitions", "feature_def_id", "features", "name", "readable_name")
    attribute_definitions = fields.Nested(FeatureAttributeDefinitionSchema, many=True, only=("name",))


class FeatureSchema(ma.Schema):
    class Meta:
        fields = ("attributes", "feature_definition", "feature_id")
    feature_definition = fields.Nested(FeatureDefinitionSchema, only=("name", "attribute_definitions",))
    attributes = fields.Nested(FeatureAttributeSchema, many=True, only=("value",))


class AssertionSchema(ma.Schema):
    class Meta:
        fields = ("assertion_id", "disease", "context", "oncotree_term", "oncotree_code",
                  "therapy_name", "therapy_strategy", "therapy_type", "therapy_sensitivity", "therapy_resistance",
                  "favorable_prognosis", "predictive_implication", "description", "last_updated",
                  "sources", "features")
    sources = fields.Nested(SourceSchema, many=True, exclude=("assertions",))
    features = fields.Nested(FeatureSchema, many=True)
