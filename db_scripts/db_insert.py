import os
import sys
import argparse
import pandas as pd
from datetime import datetime

sys.path.insert(0, './')
sys.path.insert(0, 'target_web/')
sys.path.insert(0, 'target_web/modules/')
from almanac_browser.modules.models import FeatureDefinition, FeatureAttributeDefinition, Feature, FeatureAttribute,\
    FeatureSet, Assertion, Source, AssertionToSource, Version
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


parser = argparse.ArgumentParser(
    description='Convert human-generated Almanac TSV files into SQLite files for use by the Almanac Portal.'
)
parser.add_argument('features_tsv', help='TSV file containing feature definitions')
parser.add_argument('assertions_folder', help='Folder containing assertion TSV files')
parser.add_argument('db_filename', help='Output DB filename')
parser.add_argument('version_major', help='Major version number')
parser.add_argument('version_minor', help='Minor version number')
parser.add_argument('version_patch', help='Patch version number')

args = parser.parse_args()

features_tsv = args.features_tsv
assertions_folder = args.assertions_folder
db_name = args.db_filename
v_major = args.version_major
v_minor = args.version_minor
v_patch = args.version_patch

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
    'is_germline': 'is_germline',
    'attribute_name': 'attribute',
    'readable_attribute_name': 'readable_attribute',
    'type': 'type',
}

assertion_tsv_map = {
    'disease': 'disease',
    'stage': 'stage',
    'ontology': 'oncotree_ontology',
    'code': 'oncotree_code',
    'therapy': 'therapy',
    'therapy_class': 'therapy_class',
    'therapy_type': 'therapy_type',
    'sensitivity': 'sensitivity',
    'resistance': 'resistance',
    'favorable_prognosis': 'favorable_prognosis',
    'predictive_implication': 'predictive_implication',
    'description': 'description',
    'connections': 'connections',
    'ctrpv2_therapy': 'ctrpv2_therapy',
    'doi': 'doi',
    'citation': 'citation',
    'source_type': 'source_type',
    'pubmed_id': 'pubmed_id',
    'display_string': 'display_string',
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
    elif feature in ['Knockout', 'Silencing']:
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
    sensitivity = assertion_tsv_map['sensitivity']
    for boolean_attribute in [
        assertion_tsv_map['sensitivity'], assertion_tsv_map['resistance'], assertion_tsv_map['favorable_prognosis']
    ]:
        df.loc[:, boolean_attribute].fillna(0).astype(int).replace({1: True, 0: False})

    df = df.where(df.notnull(), None)
    df[assertion_tsv_map['display_string']] = create_feature_string_series(df, feature)

    return df


# Load feature & feature attribute definitions
feature_defs_df = read_tsv(features_tsv)
for index in feature_defs_df.index:
    new_attribute_definitions = []
    series = feature_defs_df.loc[index, :]

    new_feature_def = insert_if_new(
        FeatureDefinition,
        name=series.loc[features_tsv_map['feature_name']],
        readable_name=series.loc[features_tsv_map['readable_feature_name']],
        is_germline=series.loc[features_tsv_map['is_germline']],
    )

    new_attribute_def = FeatureAttributeDefinition(
        name=series.loc[features_tsv_map['attribute_name']],
        readable_name=series.loc[features_tsv_map['readable_attribute_name']],
        type=series.loc[features_tsv_map['type']]
    )

    new_attribute_def.feature_definition = new_feature_def
    session.add(new_feature_def)
    session.add(new_attribute_def)

# Load assertions within each feature
feature_defs = session.query(FeatureDefinition).all()
assertions_counter = 0
for feature_def in feature_defs:
    feature_file = '%s.tsv' % feature_def.name
    assertion_df = read_tsv(os.path.join(assertions_folder, feature_file))
    assertion_df = sanitize_assertion_df(assertion_df, feature_def.name)
    assertions_counter += len(assertion_df.index)

    for index in assertion_df.index:
        series = assertion_df.loc[index, :]

        new_assertion = Assertion(
            therapy_name=series.loc[assertion_tsv_map['therapy']],
            therapy_type=series.loc[assertion_tsv_map['therapy_type']],
            therapy_sensitivity=series.loc[assertion_tsv_map['sensitivity']],
            therapy_resistance=series.loc[assertion_tsv_map['resistance']],
            favorable_prognosis=series.loc[assertion_tsv_map['favorable_prognosis']],
            predictive_implication=series.loc[assertion_tsv_map['predictive_implication']],
            description=series.loc[assertion_tsv_map['description']],
            disease=series.loc[assertion_tsv_map['ontology']],
            old_disease=series.loc[assertion_tsv_map['disease']],
            oncotree_code=series.loc[assertion_tsv_map['code']],
            submitted_by='breardon@broadinstitute.org',
            validated=1,
            created_on=datetime.now(),
            last_updated=datetime.now()
        )
        session.add(new_assertion)

        # We could technically have multiple FeatureSets associated with one Assertion; this is difficult to implement
        # using spreadsheet input, and we only create one FeatureSet per Assertion below.
        new_feature_set = FeatureSet(assertion=new_assertion)
        new_feature = Feature(feature_set=new_feature_set, feature_definition=feature_def)
        session.add(new_feature_set)
        session.add(new_feature)

        new_attributes = []
        for attribute_def in feature_def.attribute_definitions:
            if attribute_def.name not in series:
                print('Warning: attribute "%s" not present for "%s" feature: %s' %
                      attribute_def.name, feature_def.name, series)
                continue

            this_value = series[attribute_def.name]
            new_attribute = FeatureAttribute(feature=new_feature,
                                             attribute_definition=attribute_def,
                                             value=str(this_value) if this_value else None)
            new_attributes.append(new_attribute)
            session.add(new_attribute)

            new_source = insert_if_new(
                Source,
                doi=series[assertion_tsv_map['doi']],
                cite_text=series[assertion_tsv_map['citation']],
                source_type=series[assertion_tsv_map['source_type']]
            )
            session.add(new_source)

            new_assertion_to_source = AssertionToSource(assertion=new_assertion, source=new_source)
            session.add(new_assertion_to_source)

        new_feature.attributes = new_attributes
        new_feature_set.features.append(new_feature)


session.commit()
session.flush()

version = Version(
    major=v_major,
    minor=v_minor,
    patch=v_patch
)

commit_object(version)

print('Imported %s assertions.' % assertions_counter)
