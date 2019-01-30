from flask_sqlalchemy import declarative_base
from target_portal import db, ma

from datetime import datetime

Base = declarative_base()


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
    therapy_class = db.Column('therapy_class', db.Text)
    therapy_type = db.Column('therapy_type', db.Text)
    therapy_sensitivity = db.Column('therapy_sensitivity', db.Boolean)
    therapy_resistance = db.Column('therapy_resistance', db.Boolean)
    predictive_implication = db.Column('predictive_implication', db.Enum('FDA-Approved',
                                                                         'Level A',
                                                                         'Level B',
                                                                         'Level C',
                                                                         'Level D',
                                                                         'Level E',
                                                                         'Predictive implication'))
    favorable_prognosis = db.Column('favorable_prognosis', db.Boolean)
    description = db.Column('description', db.Text)

    alterations = db.relationship('Alteration', secondary='Assertion_To_Alteration')

    sources = db.relationship('Source', secondary='Assertion_To_Source', uselist=True,
                              )
    validated = db.Column('validated', db.Boolean, default=False)
    submitted_by = db.Column('submitted_by', db.Text)


class Alteration(Base, db.Model):
    __tablename__ = 'Alteration'

    alt_id = db.Column('alt_id', db.Integer, primary_key=True)
    feature = db.Column('feature', db.Enum('Aneuploidy',
                                           'CopyNumber',
                                           'Germline',
                                           'Knockout',
                                           'MicrosatelliteStability',
                                           'Mutation',
                                           'MutationalBurden',
                                           'MutationalSignature',
                                           'NeoantigenBurden',
                                           'Rearrangement',
                                           'Silencing'))

    alt_type = db.Column('alt_type', db.Text)
    alt = db.Column('alt', db.Text)
    gene_name = db.Column('gene_name', db.Text)
    assertions = db.relationship('Assertion',  passive_deletes=True, secondary='Assertion_To_Alteration')


class AssertionToSource(Base, db.Model):
    __tablename__ = 'Assertion_To_Source'

    ats_id = db.Column('ats_id', db.Integer, primary_key=True)
    assertion_id = db.Column('assertion_id', db.Integer, db.ForeignKey('Assertion.assertion_id'))
    source_id = db.Column('source_id', db.Integer, db.ForeignKey('Source.source_id'))
    db.UniqueConstraint('source_id', 'assertion_id', name='UC_source_id_assertion_id')

    assertion = db.relationship('Assertion', foreign_keys=assertion_id)
    source = db.relationship('Source', foreign_keys=source_id)


class Source(Base, db.Model):
    __tablename__ = 'Source'

    source_id = db.Column('source_id', db.Integer, primary_key=True)
    doi = db.Column('doi', db.Text)
    cite_text = db.Column('cite_text', db.Text)
    source_type = db.Column('source_type', db.Text)

    assertions = db.relationship('Assertion',  passive_deletes=True, secondary='Assertion_To_Source')


class AssertionToAlteration(Base, db.Model):
    __tablename__ = 'Assertion_To_Alteration'

    aa_id = db.Column('aa_id', db.Integer, primary_key=True)
    assertion_id = db.Column('assertion_id', db.Integer, db.ForeignKey('Assertion.assertion_id'))
    alt_id = db.Column('alt_id', db.Integer, db.ForeignKey('Alteration.alt_id'))

    assertion = db.relationship('Assertion', foreign_keys=assertion_id)
    alteration = db.relationship('Alteration', foreign_keys=alt_id)


class Version(Base, db.Model):
    __tablename__ = 'Version'

    major = db.Column('major', db.Integer, primary_key=True)
    minor = db.Column('minor', db.Integer)
    patch = db.Column('patch', db.Integer)


class AssertionSchema(ma.ModelSchema):
    class Meta:
        model = Assertion


class AlterationSchema(ma.ModelSchema):
    class Meta:
        model = Alteration


class SourceSchema(ma.ModelSchema):
    class Meta:
        model = Source
