import os
import sys
import argparse
import json
import numpy as np
import pandas as pd
from datetime import datetime

sys.path.insert(0, './')
sys.path.insert(0, 'almanac_browser/')
sys.path.insert(0, 'almanac_browser/modules/')
from almanac_browser.modules.models import FeatureDefinition, FeatureAttributeDefinition, Feature, FeatureAttribute,\
    Assertion, Source, AssertionToFeature, AssertionToSource, Version
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


parser = argparse.ArgumentParser(
    description='Convert human-generated Almanac TSV files into SQLite files for use by the Almanac Portal.'
)
parser.add_argument('--features_tsv', help='TSV file containing feature definitions')
parser.add_argument('--database', help='Database JSON')
parser.add_argument('--db_filename', help='Output DB filename')
parser.add_argument('--version_major', help='Major version number')
parser.add_argument('--version_minor', help='Minor version number')
parser.add_argument('--version_patch', help='Patch version number')
parser.add_argument('--version_data_release', help='Release date of database content')

args = parser.parse_args()
print(args)

features_tsv = args.features_tsv
database = args.database
db_name = args.db_filename
v_major = args.version_major
v_minor = args.version_minor
v_patch = args.version_patch
release = args.version_data_release

engine = create_engine('sqlite:///%s' % db_name)
session = sessionmaker(bind=engine)()

IMPLICATION_LEVELS_SORT = {
    'FDA-Approved': 5,
    'Guideline': 4,
    'Clinical trial': 3,
    'Clinical evidence': 2,
    'Preclinical': 1,
    'Inferential': 0
}

features_tsv_map = {
    'feature_name': 'feature',
    'readable_feature_name': 'readable_name',
    'attribute_name': 'attribute',
    'readable_attribute_name': 'readable_attribute',
    'type': 'type',
}

assertion_tsv_map = {
    'disease': 'disease',
    'context': 'context',
    'oncotree_term': 'oncotree_term',
    'oncotree_code': 'oncotree_code',
    'therapy_name': 'therapy_name',
    'therapy_strategy': 'therapy_strategy',
    'therapy_type': 'therapy_type',
    'therapy_sensitivity': 'therapy_sensitivity',
    'therapy_resistance': 'therapy_resistance',
    'favorable_prognosis': 'favorable_prognosis',
    'predictive_implication': 'predictive_implication',
    'description': 'description',
    'source_type': 'source_type',
    'citation': 'citation',
    'url': 'url',
    'doi': 'doi',
    'pmid': 'pmid',
    'nct': 'nct',
    'last_updated': 'last_updated'
}


def insert_if_new(model, **kwargs):
    """
    Insert db_item if it does not already exist in the database.
    **kwargs contains the list of items that must match for a database row to be considered "identical."
    Adapted from http://stackoverflow.com/questions/2546207/does-sqlalchemy-have-an-equivalent-of-djangos-get-or-create
    """

    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        return instance


def read_tsv(handle):
    return pd.read_csv(handle, sep='\t', encoding='utf-8')


def commit_objects(objects_to_add):
    session.bulk_save_objects(objects_to_add, return_defaults=True)
    session.commit()
    session.flush()


def commit_object(object_to_add):
    session.add(object_to_add)
    session.commit()
    session.flush()


def create_feature_string_series(df, feature):
    display_string = assertion_tsv_map['display_string']
    df[display_string] = ''

    if feature in ['Somatic Variant', 'Germline Variant']:
        df.loc[:, display_string] = df.loc[:, ['variant_type', 'gene', 'protein_change']].fillna('').astype(str).\
            apply(lambda x: ' '.join(x), axis=1)
    elif feature is 'Copy Number':
        df.loc[:, display_string] = df.loc[:, ['direction', 'gene', 'locus']].fillna('').astype(str).\
            apply(lambda x: ' '.join(x), axis=1)
    elif feature in ['Knockdown', 'Silencing']:
        df.loc[:, display_string] = df.loc[:, ['technique', 'gene']].fillna('').astype(str).\
            apply(lambda x: ' '.join(x), axis=1)
    elif feature is 'Rearrangement':
        df.loc[:, display_string] = df.loc[:, ['rearrangement_type', 'gene1', 'gene2', 'locus']].fillna('').astype(str)
        for display_index in df.loc[:, display_string].index:
            display_series = feature_defs_df.loc[display_index, :]
            if display_series[1] and display_series[2]:
                df.loc[:, display_string].apply(lambda x: '%s %s-%s' %
                                                          (display_series[0], display_series[1], display_series[2]))
            else:
                df.loc[:, display_string].apply(lambda x: '%s %s' % (display_series[0], display_series[3]))
    elif feature is 'Aneuploidy':
        df.loc[:, display_string] = df.loc[:, ['effect']].fillna('').astype(str)
    elif feature is 'Microsatellite Stability':
        df.loc[:, display_string] = df.loc[:, ['direction']].fillna('').astype(str)

    df.loc[:, display_string] += feature + ' '

    return df[display_string]


def sanitize_assertion_df(df, feature):
    for boolean_attribute in [
        assertion_tsv_map['therapy_sensitivity'],
        assertion_tsv_map['therapy_resistance'],
        assertion_tsv_map['favorable_prognosis']
    ]:
        df.loc[:, boolean_attribute].replace({1: True, 0: False})

    df = df.where(df.notnull(), None)
    #df[assertion_tsv_map['display_string']] = create_feature_string_series(df, feature)
    return df


# Load feature & feature attribute definitions
feature_defs_df = read_tsv(features_tsv)
for index in feature_defs_df.index:
    new_attribute_definitions = []
    series = feature_defs_df.loc[index, :]

    new_feature_def = insert_if_new(
        FeatureDefinition,
        name=series.loc[features_tsv_map['feature_name']],
        readable_name=series.loc[features_tsv_map['readable_feature_name']]
    )

    new_attribute_def = FeatureAttributeDefinition(
        name=series.loc[features_tsv_map['attribute_name']],
        readable_name=series.loc[features_tsv_map['readable_attribute_name']],
        type=series.loc[features_tsv_map['type']]
    )

    new_attribute_def.feature_definition = new_feature_def
    session.add(new_feature_def)
    session.add(new_attribute_def)

# Load assertions
f = open(database)
assertions = json.load(f)
assertions_counter = 0
for assertion in assertions:
    assertions_counter += 1

    series = pd.Series(assertion)
    new_assertion = Assertion(
            disease=series.loc[assertion_tsv_map['oncotree_term']],
            oncotree_term=series.loc[assertion_tsv_map['oncotree_term']],
            oncotree_code=series.loc[assertion_tsv_map['oncotree_code']],
            context=series.loc[assertion_tsv_map['context']],
            therapy_name=series.loc[assertion_tsv_map['therapy_name']],
            therapy_strategy=series.loc[assertion_tsv_map['therapy_strategy']],
            therapy_type=series.loc[assertion_tsv_map['therapy_type']],
            therapy_sensitivity=series.loc[assertion_tsv_map['therapy_sensitivity']],
            therapy_resistance=series.loc[assertion_tsv_map['therapy_resistance']],
            favorable_prognosis=series.loc[assertion_tsv_map['favorable_prognosis']],
            predictive_implication=series.loc[assertion_tsv_map['predictive_implication']],
            description=series.loc[assertion_tsv_map['description']],
            submitted_by='breardon@broadinstitute.org',
            validated=1,
            created_on=datetime.now().strftime("%D"),
            last_updated=datetime.strptime(series.loc[assertion_tsv_map['last_updated']], "%m/%d/%y").date()
        )
    session.add(new_assertion)

    feature_type = series.loc["feature_type"]
    feature_definition = session.query(FeatureDefinition).filter(FeatureDefinition.readable_name == feature_type).all()
    if len(feature_definition) > 1:
        print(f"More than one feature type match for assertion")
        print(f"{series}")
        print(f", ".join([definition.readable_name for definition in feature_definition]))
        sys.exit(0)
    feature_def = feature_definition[0]

    new_feature = Feature(feature_definition=feature_def)
    session.add(new_feature)

    new_assertion_to_feature = AssertionToFeature(assertion=new_assertion, feature=new_feature)
    session.add(new_assertion_to_feature)

    new_attributes = []
    for attribute_def in feature_def.attribute_definitions:
        if attribute_def.name not in series:
            print(f'Warning: attribute {attribute_def.name} not present for {feature_def.name} feature: {series}')
            continue

        value = series.loc[attribute_def.name]
        new_attribute = FeatureAttribute(
            feature=new_feature,
            attribute_definition=attribute_def,
            value=str(value) if value else None
        )
        new_attributes.append(new_attribute)
        session.add(new_attribute)

    new_source = insert_if_new(
        Source,
        source_type=series.loc[assertion_tsv_map['source_type']],
        citation=series.loc[assertion_tsv_map['citation']],
        url=series.loc[assertion_tsv_map['url']],
        doi=series.loc[assertion_tsv_map['doi']],
        pmid=str(series.loc[assertion_tsv_map['pmid']]),
        nct=str(series.loc[assertion_tsv_map['nct']])
    )
    session.add(new_source)

    new_assertion_to_source = AssertionToSource(assertion=new_assertion, source=new_source)
    session.add(new_assertion_to_source)
    new_feature.attributes = new_attributes

session.commit()
session.flush()

version = Version(
    major=v_major,
    minor=v_minor,
    patch=v_patch,
    release=release
)

commit_object(version)

print(f'Imported {assertions_counter} assertions')
