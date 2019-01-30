"""
Functions that abstract away basic operations with and maninpulations of models, allowing for easier testing.
"""
from .models import Alteration, Assertion, Source, AssertionToAlteration, AssertionToSource
import simplejson as json
from werkzeug.exceptions import BadRequest
import urllib
from flask import request
from target_portal.modules.api.errors import error_response as api_error_response


def add_or_fetch_alteration(db, gene=None, effect=None, feature=None, alt=None):
    """Given a gene, effect, and class of alteration, either fetch an existing corresponding alteration, or create a
    new one if none exists with the given attributes."""
    alteration = db.session.query(Alteration).filter(Alteration.gene_name == gene,
                                                     Alteration.alt_type == effect,
                                                     Alteration.feature == feature,
                                                     Alteration.alt == alt).first()

    if not alteration:
        alteration = Alteration()
        alteration.feature = feature
        alteration.alt_type = effect
        alteration.gene_name = gene
        alteration.alt = alt
        db.session.add(alteration)
        db.session.flush()

    return alteration


def add_or_fetch_source(db, doi, cite_text=""):
    """Given a DOI, either fetch an exisiting corresponding source, or create a new one if none exists yet with the
    given attributes"""
    source = db.session.query(Source).filter(Source.doi == doi).first()
    if not source:
        source = Source()
        source.doi = doi
        source.source_type = 'Journal'
        source.cite_text = cite_text
        db.session.add(source)
        db.session.flush()

    return source


def amend_alteration_for_assertion(db, assertion, current_alt_value, new_alt_value):
    current_alteration = [a for a in assertion.alterations if a.alt == current_alt_value][0] \
        if [a for a in assertion.alterations if a.alt == current_alt_value] \
        else None
    if not current_alteration:
        BadRequest("Alteration of value {} not found".format(current_alt_value))

    # Remove this alteration from this assertion so we can make room for the new one.
    remove_alteration_from_assertion(db, assertion, current_alteration)
    new_alteration = add_or_fetch_alteration(db,
                                             gene=current_alteration.gene_name,
                                             feature=current_alteration.feature,
                                             effect=current_alteration.alt_type,
                                             alt=new_alt_value)
    assertion.alterations.append(new_alteration)


def amend_cite_text_for_assertion(db, assertion, doi, new_cite_text):
    current_source = [s for s in assertion.sources if s.doi == doi][0] \
        if [s for s in assertion.sources if s.doi == doi] \
        else None
    if not current_source:
        BadRequest("Source with doi {} not found".format(doi))

    db.session.add(current_source)
    current_source.cite_text = new_cite_text


def remove_alteration_from_assertion(db, assertion=None, alteration=None):
    """Remove an Alteration from an Assertion's list of alterations. If there are other Assertions that depend on
    this Alteration, simply remove it from the Assertion in question. Otherwise, if this is the only Assertion that
    this Alteration is linked to, simply delete the Alteration."""
    assert(assertion is not None)
    assert(alteration is not None)

    other_assertions_with_same_alteration = db.session.query(AssertionToAlteration) \
        .filter(AssertionToAlteration.alt_id == alteration.alt_id,
                AssertionToAlteration.assertion_id != assertion.assertion_id).all()
    if not other_assertions_with_same_alteration:
        db.session.delete(alteration)
    else:
        current_alterations = assertion.alterations
        new_alterations = [a for a in current_alterations if a.alt_id != alteration.alt_id]
        assertion.alterations = new_alterations
        db.session.add(assertion)


def delete_assertion(db, assertion_to_delete):
    """Delete an assertion. Before deleting the assertion, check whether deleting it would orphan any rows in the
    Source or Alteration tables, and delete these as well if so. No database children left behind."""
    for s in assertion_to_delete.sources:
        other_assertions_with_same_source = db.session.query(AssertionToSource) \
            .filter(AssertionToSource.source_id == s.source_id,
                    AssertionToSource.assertion_id != assertion_to_delete.assertion_id).all()
        if not other_assertions_with_same_source:
            # Delete the assertionToSource association, then the source
            a2s = db.session.query(AssertionToSource).filter(AssertionToSource.assertion_id == assertion_to_delete.assertion_id,
                                                             AssertionToSource.source_id == s.source_id).first()
            db.session.delete(a2s)
            db.session.delete(s)

    for alt in assertion_to_delete.alterations:
        remove_alteration_from_assertion(db, assertion_to_delete, alt)

    db.session.delete(assertion_to_delete)


def get_unapproved_assertion_rows(db):
    unapproved_assertions = db.session.query(Assertion).filter(Assertion.validated == 0).all()
    rows = []
    for assertion in unapproved_assertions:
        for alt in assertion.alterations:
            rows.append(make_row(alt, assertion))
    return rows


def make_row(alt, assertion):
    return {
        'gene_name': urllib.parse.unquote(alt.gene_name) if alt.gene_name else None,
        'feature': alt.feature,
        'alt_type': alt.alt_type,
        'alt': alt.alt,
        'alt_id': alt.alt_id,
        'therapy_name': assertion.therapy_name,
        'therapy_sensitivity': assertion.therapy_sensitivity,
        'therapy_resistance': assertion.therapy_resistance,
        'favorable_prognosis': assertion.favorable_prognosis,
        'disease': assertion.disease,
        'submitter': urllib.parse.unquote(assertion.submitted_by) if assertion.submitted_by else None,
        'predictive_implication': assertion.predictive_implication,
        'assertion_id': assertion.assertion_id,
        'sources': [s for s in assertion.sources]
    }

def http200response(message=None):
    return json.dumps({'success': True, 'message': '{}'.format(json.dumps(message))}), 200, {'ContentType': 'application/json'}


def http404response():
    return json.dumps({'success': False}), 404, {'ContentType': 'application/json'}


def http400response(message=None):
    return json.dumps({'success': False, 'message': '{}'.format(message)}), 400, {'ContentType': 'application/json'}


def filter_row_column(query_results, column):
    return [getattr(row, column) for row in query_results if getattr(row, column) not in [None, '']]


def query_distinct_column(db, model, column):
    query = db.session.query(getattr(model, column).distinct().label(column))
    return filter_row_column(query, column)


def get_typeahead_genes(db):
    alterations = db.session.query(Alteration).all()
    typeahead_genes = list(set([a.gene_name for a in alterations if all([assertion.validated == 1 for assertion in a.assertions])]))
    return typeahead_genes

