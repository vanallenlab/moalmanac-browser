"""
Functions that abstract away basic operations with and maninpulations of models, allowing for easier testing.
"""
from .models import Alteration, Assertion, Source, AssertionToAlteration, AssertionToSource
import simplejson as json
from werkzeug.exceptions import BadRequest
import urllib
import re
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
        #'therapy_class': assertion.therapy_class,
        'therapy_type': assertion.therapy_type,
        'therapy_sensitivity': assertion.therapy_sensitivity,
        'therapy_resistance': assertion.therapy_resistance,
        'favorable_prognosis': assertion.favorable_prognosis,
        'disease': assertion.disease,
        'submitter': urllib.parse.unquote(assertion.submitted_by) if assertion.submitted_by else None,
        'predictive_implication': assertion.predictive_implication,
        'assertion_id': assertion.assertion_id,
        'sources': [s for s in assertion.sources],
        'display_string': alt.display_string
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


def check_row_exists(db, table, assertion):
    """
    Returns True if the given assertion holds true for the given column.
    E.g.: check_row_exists(Alteration, Alteration.gene_name == KRAS)

    :param db: Database connection.
    :param table: Table to search within.
    :param assertion: Assertion to test for.
    :return: True if assertion holds within the table; False otherwise.
    """

    return db.session.query((db.session.query(table).filter(assertion)).exists()).scalar()

check_row_exists.query_exists_assertions = {
    'gene': (Alteration, Alteration.gene_name),
    'disease': (Assertion, Assertion.disease),
    'pred': (Assertion, Assertion.predictive_implication),
    'therapy': (Assertion, Assertion.therapy_name),
}


def interpret_unified_search_string_informal_substr(db, search_str):
    query = {'gene': [], 'disease': [], 'pred': [], 'therapy': [], 'unknown': []}

    # The 3 regex groups below are mutually exclusive due to the OR operators; only one of the groups will ever contain
    # data. We thus collapse the groups after matching so that our list of tokens doesn't contain empty groups.
    re_groups = re.findall(r'\"([^\"]+)\"|\'([^\']+)\'|(\S+)', search_str)
    tokens = []
    for group in re_groups:
        token = group[0] or group[1] or group[2]
        tokens.append(token.strip())

    aggregate_token = []
    for token in tokens:
        new_aggregate_token = aggregate_token + [token]
        new_aggregate_token_str = ' '.join(new_aggregate_token)

        for category, assertion in check_row_exists.query_exists_assertions.items():
            tag_match = re.match(r'\[([^\[]*)]', token)
            if tag_match:
                # If the aggregate token is empty, we already assigned the token based on a DB lookup
                if aggregate_token:
                    category = tag_match.group(1)
                    if category not in check_row_exists.query_exists_assertions.keys():
                        category = 'unknown'

                    query[category].append(' '.join(aggregate_token))

                new_aggregate_token = []
                break
            elif check_row_exists(db, assertion[0], assertion[1].ilike(new_aggregate_token_str)):
                query[category].append(new_aggregate_token_str)
                new_aggregate_token = []
                break
            elif check_row_exists(db, assertion[0], assertion[1].ilike(token)):
                query[category].append(token)
                query['unknown'].extend(aggregate_token)
                new_aggregate_token = []
                break

        aggregate_token = new_aggregate_token

    # Any left-over data in aggregate token indicates the last token was not matched to a category
    if aggregate_token:
        query['unknown'].extend(aggregate_token)

    return query


def union_dictionaries(d1, d2):
    new_dict = {}
    [new_dict.setdefault(k, []).extend(v) for k, v in d1.items()]
    [new_dict.setdefault(k, []).extend(v) for k, v in d2.items()]

    return new_dict


def interpret_unified_search_string(db, search_str):
    """
    Converts a raw (user-provided) search string into a dictionary describing the specific entities in a query.
    Tokenization mimics the "PubMed style." Formally, each token is followed by a bracketed category identifier, and
    tokens containing whitespace are quoted. E.g., a query for clinical trials would be "Clinical trial"[pred].
    However, we attempt to resolve less formally specified queries. Traversing the search string from left to right,
    we build an "aggregate token" combining all tokens seen so far. At each step, the current aggregate token is checked
    against all categories (gene, disease, etc.); if a match is found, the token is added to the query and the aggregate
    token is reset. If no match is found, the current individual token is checked against all categories; if a match is
    found, the current aggregate token (not including the current individual token) is added to the query as an
    "unknown" token and the current individual token is added separately.

    Example:
    Raw search string: PIK3CA "Invasive Breast Carcinoma"[disease] Preclinical
    Query dictionary: {'genes': 'PIK3CA', 'diseases': 'Invasive Breast Carcinoma', 'preds': 'Preclinical'}

    :param db: Database connection.
    :param search_str: Raw unified search string.
    :return: Dictionary representing query in a structured format.
    """

    query = {'gene': [], 'disease': [], 'pred': [], 'therapy': [], 'unknown': []}

    # Initially assume search string is formally specified (with [category] tags).
    tag_iter = re.finditer(r'\[([^\[]*)\]', search_str)
    last_pos = 0
    for match in tag_iter:
        tag_interval = match.span(1)

        # If the token corresponding to this tag is quoted, the user may have intended the tokens to the left of the
        # quoted token to be interpreted informally (e.g.: erlotinib "Clinical trial"[pred] is likely intended to
        # find uses of erlotinib in clinical trials, not a predictive level named "erlotinib Clinical trial."
        # Find the left-most quote to the left of this category tag; interpret everything to the left of it informally.
        left_quotes = re.finditer(r'["\']', search_str[last_pos:tag_interval[0] - 1])
        quote_idxs = [quote.span(0)[0] for quote in left_quotes]
        if len(quote_idxs) > 1:
            opening_quote_pos = quote_idxs[-2]
            informal_query = interpret_unified_search_string_informal_substr(
                db, search_str[last_pos:last_pos + opening_quote_pos]
            )
            query = union_dictionaries(query, informal_query)
            last_pos += opening_quote_pos

        # March right-to-left from the category tag, until either the aggregated token matches a DB row or we run out of
        # search string. If we hit a DB match, informally evaluate the remainder of the string.
        category = search_str[tag_interval[0]:tag_interval[1]].strip()
        if category not in query.keys():
            category = 'unknown'

        search_substr = search_str[last_pos:tag_interval[0] - 1]
        search_substr_tokens = search_substr.split()
        aggregate_token = []
        formal_token = None
        for i in range(len(search_substr_tokens)-1, -1, -1):
            aggregate_token.insert(0, search_substr_tokens[i])
            if check_row_exists(
                    db,
                    check_row_exists.query_exists_assertions[category][0],
                    check_row_exists.query_exists_assertions[category][1].ilike(' '.join(aggregate_token))
            ):
                formal_token = ' '.join(aggregate_token)
                informal_query = interpret_unified_search_string_informal_substr(db, ' '.join(search_substr_tokens[:i]))
                query = union_dictionaries(query, informal_query)
                break

        # If formal_token was never assigned, we never found a DB match. Assign the entire putative token string as the
        # formal token anyway.
        if not formal_token:
            formal_token = ' '.join(aggregate_token)

        # remove quotes - they are not necessary when using category tags
        formal_token = re.sub(r'["\']', '', formal_token)
        query[category].append(formal_token)

        last_pos = tag_interval[1] + 1

    # Remainder of search string is informally specified (no further [category] tags).
    informal_query = interpret_unified_search_string_informal_substr(db, search_str[last_pos:])
    query = union_dictionaries(query, informal_query)

    return query
