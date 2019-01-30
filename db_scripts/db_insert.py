import sys

sys.path.insert(0, './')
sys.path.insert(0, 'target_web/')
sys.path.insert(0, 'target_web/modules/')

import pandas as pd
from datetime import datetime
from target_portal.modules.models import Alteration, Assertion, Source, Version
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

if len(sys.argv) != 6:
    sys.stdout.write('Usage:\n')
    sys.stdout.write('TARGET_insert.py import_file.tsv db_name.sqlite3 1 2 3\n')
    sys.exit()

import_file = sys.argv[1]
db_name = sys.argv[2]
v_major = sys.argv[3]
v_minor = sys.argv[4]
v_patch = sys.argv[5]

engine = create_engine('sqlite:///%s' % db_name)
session = sessionmaker(bind=engine)()


def insert_if_new(model, **kwargs):
    """
    Insert db_item if it does not already exist in the database.
    **kwargs contains the list of items that must match for a database row to be considered "identical."
    Returns (db_instance, bool), where the boolean value is True if an item was inserted and False otherwise.
    Adapted from http://stackoverflow.com/questions/2546207/does-sqlalchemy-have-an-equivalent-of-djangos-get-or-create
    """

    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        return instance


def read_table(handle):
    return pd.read_csv(handle, sep='\t')


def commit_objects(objects_to_add):
    session.bulk_save_objects(objects_to_add, return_defaults=True)
    session.commit()
    session.flush()


def commit_object(object_to_add):
    session.add(object_to_add)
    session.commit()
    session.flush()


feature_type = 'feature_type'
feature = 'feature'
alt_type = 'alteration_type'
alt = 'alteration'
disease = 'disease'
stage = 'stage'
ontology = 'oncotree_ontology'
code = 'oncotree_code'
therapy = 'therapy'
therapy_class = 'therapy_class'
therapy_type = 'therapy_type'
sensitivity = 'sensitivity'
resistance = 'resistance'
favorable_prognosis = 'favorable_prognosis'
predictive_implication = 'predictive_implication'
description = 'description'
connections = 'connections'
ctrpv2_therapy = 'ctrpv2_therapy'
doi = 'doi'
citation = 'citation'
source_type = 'source_type'
pubmed_id = 'pubmed_id'

df = read_table(import_file)
for information in [sensitivity, resistance, favorable_prognosis]:
    df.loc[:, information].astype(float).replace({1.0: True, 0.0: False})
df = df.where(df.notnull(), None)

for index in df.index:
    new_alterations = []
    new_sources = []

    series = df.loc[index, :]

    # To do, rename feature and gene_name to be feature_type and feature
    new_alteration = insert_if_new(
        Alteration,
        feature=series.loc[feature_type],
        gene_name=series.loc[feature],
        alt_type=series.loc[alt_type],
        alt=series.loc[alt]
    )
    new_alterations.append(new_alteration)

    new_source = insert_if_new(
        Source,
        doi=series.loc[doi],
        cite_text=series.loc[citation],
        source_type=series.loc[source_type]
    )
    new_sources.append(new_source)

    session.bulk_save_objects(new_sources + new_alterations, return_defaults=True)
    session.commit()
    session.flush()

    new_assert = Assertion(
        therapy_name=series.loc[therapy],
        #therapy_class=series.loc[therapy_class],
        therapy_type=series.loc[therapy_type],
        therapy_sensitivity=series.loc[sensitivity],
        #therapy_resistance=series.loc[resistance],
        favorable_prognosis=series.loc[favorable_prognosis],
        predictive_implication=series.loc[predictive_implication],
        description=series.loc[description],
        disease=series.loc[ontology],
        old_disease=series.loc[disease],
        #oncotree_term=series.loc[ontology],
        oncotree_code=series.loc[code],
        submitted_by='breardon@broadinstitute.org',
        validated=1,
        created_on=datetime.now(),
        last_updated=datetime.now()
    )

    for source in new_sources:
        new_assert.sources.append(source)

    for alteration in new_alterations:
        new_assert.alterations.append(alteration)

    commit_object(new_assert)

version = Version(
    major=v_major,
    minor=v_minor,
    patch=v_patch
)

commit_object(version)
