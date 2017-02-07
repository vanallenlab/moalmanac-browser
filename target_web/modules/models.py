from flask_sqlalchemy import orm, declarative_base
from target_web import db

Base = declarative_base()

class Assertion(Base, db.Model):
    __tablename__ = 'Assertion'

    assertion_id = db.Column('assertion_id', db.Integer, primary_key=True)
    last_updated = db.Column('last_updated', db.Text)
    disease = db.Column('disease', db.Text)
    stage = db.Column('stage', db.Integer)
    therapy_name = db.Column('therapy_name', db.Text)
    therapy_type = db.Column('therapy_type', db.Text)
    therapy_sensitivity = db.Column('therapy_sensitivity', db.Boolean)
    predictive_implication = db.Column('predictive_implication', db.Text)
    favorable_prognosis = db.Column('favorable_prognosis', db.Boolean)
    description = db.Column('description', db.Text)

    alterations = orm.relationship('Alteration',
                                   #single_parent=True,
                                   secondary='Assertion_To_Alteration',
                                   )#cascade='all, delete-orphan')
    sources = orm.relationship('Source',
                               #single_parent=True,
                               secondary='Assertion_To_Source',
                               )#cascade='all, delete-orphan')

# feature = {Amplification, Biallelic Inactivation, Deletion, Mutation, Rearrangement}
# alt = Alteration specified using HGVS notation (http://varnomen.hgvs.org/recommendations/)
class Alteration(Base, db.Model):
    __tablename__ = 'Alteration'

    alt_id = db.Column('alt_id', db.Integer, primary_key=True)
    feature = db.Column('feature', db.Text)
    alt_type = db.Column('alt_type', db.Text)
    alt = db.Column('alt', db.Text)
    gene_name = db.Column('gene_name', db.Text)

    assertions = orm.relationship('Assertion', secondary='Assertion_To_Alteration')

class Source(Base, db.Model):
    __tablename__ = 'Source'

    source_id = db.Column('source_id', db.Integer, primary_key=True)
    doi = db.Column('doi', db.Text)
    cite_text = db.Column('cite_text', db.Text)
    source_type = db.Column('source_type', db.Text)

    assertions = orm.relationship('Assertion', secondary='Assertion_To_Source')

class AssertionToSource(Base, db.Model):
    __tablename__ = 'Assertion_To_Source'

    ats_id = db.Column('ats_id', db.Integer, primary_key=True)
    assertion_id = db.Column('assertion_id', db.Integer, db.ForeignKey('Assertion.assertion_id'))
    source_id = db.Column('source_id', db.Integer, db.ForeignKey('Source.source_id'))

    assertion = orm.relationship('Assertion', foreign_keys=assertion_id)
    source = orm.relationship('Source', foreign_keys=source_id)

class AssertionToAlteration(Base, db.Model):
    __tablename__ = 'Assertion_To_Alteration'

    aa_id = db.Column('aa_id', db.Integer, primary_key=True)
    assertion_id = db.Column('assertion_id', db.Integer, db.ForeignKey('Assertion.assertion_id'))
    alt_id = db.Column('alt_id', db.Integer, db.ForeignKey('Alteration.alt_id'))

    assertion = orm.relationship('Assertion', foreign_keys=assertion_id)
    alteration = orm.relationship('Alteration', foreign_keys=alt_id)