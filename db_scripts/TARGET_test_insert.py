# hack to let us import DB models
import sys
sys.path.insert(0, './')
sys.path.insert(0, 'target_web/')
sys.path.insert(0, 'target_web/modules/')

import csv
from datetime import datetime
from models import Alteration, Assertion, Source
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///target.sqlite3')
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
        params = dict((k, v) for k, v in kwargs.iteritems())
        params.update(defaults or {})
        instance = model(**params)
        session.add(instance)
        return instance, True

with open('db_scripts/gdoc_export.txt') as tsvfile:
	tsvreader = csv.reader(tsvfile, delimiter='\t')
	for row in tsvreader:
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

		new_source, __ = insert_if_new(
				Source,
				doi=row[12] if row[12].strip() else None,
				cite_text=row[13] if row[13].strip() else None,
				source_type=row[14] if row[14].strip() else None
		)
		new_sources.append(new_source)

		session.bulk_save_objects(new_sources + new_alterations, return_defaults=True)
		session.commit()
		session.flush()

		sensitivity = None
		prognosis = None

		if row[8] == '1': sensitivity = True
		elif row[8] == '0': sensitivity = False

		if row[9] == '1': prognosis = True
		elif row[9] == '0': prognosis = False

		new_assert = Assertion(disease=row[4],
							   therapy_name=row[6],
							   therapy_type=row[7],
							   therapy_sensitivity=sensitivity,
							   predictive_implication=row[10],
							   favorable_prognosis=prognosis,
							   description=row[11],
							   last_updated=datetime.now())

		for source in new_sources:
			new_assert.sources.append(source)

		for alt in new_alterations:
			new_assert.alterations.append(alt)

		session.add(new_assert)
		session.commit()
		session.flush()
