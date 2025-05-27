import sqlalchemy
from sqlalchemy.orm import DeclarativeBase


class Base(sqlalchemy.orm.DeclarativeBase):
    pass

class About(Base):
    __tablename__ = "about"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    last_updated = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    release = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    documents_count = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    propositions_count = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    statements_count = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)

class Biomarkers(Base):
    __tablename__ = "biomarkers"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    type = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    propositions_count = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    statements_count = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)

class Diseases(Base):
    __tablename__ = "diseases"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    propositions_count = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    statements_count = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)

class Documents(Base):
    __tablename__ = "documents"

    id = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    citation = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    url = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    organization_id = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    organization_name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    indications_count = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    statements_count = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)

class Genes(Base):
    __tablename__ = "genes"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    biomarkers_count = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    propositions_count = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    statements_count = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)

class Indications(Base):
    __tablename__ = "indications"

    id = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    document_id = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    document_name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    organization_id = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    organization_name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    statements_count = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)

class Organizations(Base):
    __tablename__ = "organizations"

    id = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    last_updated = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    documents_count = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    indications_count = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    statements_count = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)

class Therapies(Base):
    __tablename__ = "therapies"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    # therapy_strategy
    therapy_type = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    propositions_count = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    statements_count = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)

class Terms(Base):
    __tablename__ = "terms"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    table = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    record_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    record_name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
