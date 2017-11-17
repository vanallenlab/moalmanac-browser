# hack to let us import DB models
import sys

sys.path.insert(0, './')
sys.path.insert(0, 'target_web/')
sys.path.insert(0, 'target_web/modules/')

import csv
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


def insert_if_new(model, defaults=None, **kwargs):
    """
    Insert db_item if it does not already exist in the database.
    **kwargs contains the list of items that must match for a database row to be considered "identical."
    Returns (db_instance, bool), where the boolean value is True if an item was inserted and False otherwise.
    Adapted from http://stackoverflow.com/questions/2546207/does-sqlalchemy-have-an-equivalent-of-djangos-get-or-create
    """
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = dict((k, v) for k, v in kwargs.items())
        params.update(defaults or {})
        instance = model(**params)
        session.add(instance)
        return instance, True


with open(import_file) as tsvfile:
    tsvreader = csv.reader(tsvfile, delimiter='\t')
    for row in tsvreader:
        print(row)
        row = [cell for cell in row]

        new_alterations = []
        new_sources = []

        new_alt, __ = insert_if_new(
            Alteration,
            feature=row[0] if row[0].strip() else None,
            alt_type=row[2] if row[2].strip() else None,
            gene_name=row[1] if row[1].strip() else None,
            alt=row[3] if row[3].strip() else None
        )
        new_alterations.append(new_alt)

        dois = row[12].split('|')
        cite_texts = row[13].split('|')
        source_types = row[14].split('|')
        oncotree_term = row[17]
        oncotree_code = row[18]
        if (len(dois) != len(cite_texts)) or \
                (len(dois) != len(source_types)) or \
                (len(cite_texts) != len(source_types)):
            sys.stdout.write('Error: Mismatching source information.\n')
            sys.stdout.write('{}\n'.format(row))
            sys.exit(1)

        for i in range(0, len(dois)):
            new_source, __ = insert_if_new(
                Source,
                doi=dois[i] if dois[i].strip() else None,
                cite_text=cite_texts[i] if cite_texts[i].strip() else None,
                source_type=source_types[i] if source_types[i].strip() else None
            )

            new_sources.append(new_source)

        session.bulk_save_objects(new_sources + new_alterations, return_defaults=True)
        session.commit()
        session.flush()

        sensitivity = None
        prognosis = None

        if row[8] == '1':
            sensitivity = True
        elif row[8] == '0':
            sensitivity = False

        if row[9] == '1':
            prognosis = True
        elif row[9] == '0':
            prognosis = False

        new_assert = Assertion(disease=row[4],
                               therapy_name=row[6],
                               therapy_type=row[7],
                               therapy_sensitivity=sensitivity,
                               predictive_implication=row[10],
                               favorable_prognosis=prognosis,
                               description=row[11],
                               oncotree_term=oncotree_term,
                               oncotree_code=oncotree_code,
                               last_updated=datetime.now())

        for source in new_sources:
            new_assert.sources.append(source)

        for alt in new_alterations:
            new_assert.alterations.append(alt)

        session.add(new_assert)
        session.commit()
        session.flush()

    version = Version(
        major=v_major,
        minor=v_minor,
        patch=v_patch
    )
    session.add(version)
    session.commit()
    session.flush()
