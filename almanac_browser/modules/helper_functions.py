"""
Functions that abstract away basic operations with and manipulations of models, allowing for easier testing.
"""
import simplejson as json
import urllib
import re
from sqlalchemy import or_, and_
from flask import Markup, url_for, request
from werkzeug.exceptions import BadRequest
from .models import Assertion, Source, Feature, FeatureDefinition, FeatureAttribute, \
    FeatureAttributeDefinition, AssertionToFeature

IMPLICATION_LEVELS_SORT = {
    'FDA-Approved': 5,
    'Guideline': 4,
    'Clinical trial': 3,
    'Clinical evidence': 2,
    'Preclinical': 1,
    'Inferential': 0
}


def flatten_sqlalchemy_singlets(l):
    """In some uses cases, SQLAlchemy returns a list of 1-tuples. This function flattens these lists."""

    return [item[0] for item in l if item[0]]


def get_distinct_attribute_values(db, needle, search_column=FeatureAttributeDefinition.name):
    """
    It's often useful to get a list of all the possible distinct values an attribute has been created with; e.g.,
    all the unique genes that have been created. This function performs this for any attribute.
    By default, the FeatureAttributeDefinition.name column is used as the search space for the needle parameter.
    However, the user may specify a different FeatureAttributeDefinition column (such as type or attribute_def_id) to
    search within.
    """

    values = db.session.query(FeatureAttribute.value).filter(
        FeatureAttribute.attribute_def_id == FeatureAttributeDefinition.attribute_def_id,
        search_column == needle
    ).distinct().all()

    return [value for value in flatten_sqlalchemy_singlets(values) if value.lower() != 'none']


def get_all_genes(db):
    return get_distinct_attribute_values(db, 'gene', FeatureAttributeDefinition.type)


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
    new_alteration = add_or_fetch_feature(db,
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


def remove_alteration_from_assertion(db, assertion=None, feature=None):
    """Remove an Alteration from an Assertion's list of alterations. If there are other Assertions that depend on
    this Alteration, simply remove it from the Assertion in question. Otherwise, if this is the only Assertion that
    this Alteration is linked to, simply delete the Alteration."""

    assert(assertion is not None)
    assert(feature is not None)

    other_assertions_with_same_alteration = db.session.query(AssertionToFeature) \
        .filter(AssertionToFeature.feature_id == feature.feature_id,
                AssertionToFeature.assertion_id != assertion.assertion_id).all()
    if not other_assertions_with_same_alteration:
        db.session.delete(feature)
    else:
        current_alterations = assertion.alterations
        new_alterations = [a for a in current_alterations if a.alt_id != feature.alt_id]
        assertion.alterations = new_alterations
        db.session.add(assertion)


def delete_assertion(db, assertion_to_delete):
    """
    Delete an assertion.  Note that the CASCADEs settings in models.py and the SQL table definitions handles deletion
    of most child tables automatically. However, we must manually ensure Sources are orphaned before deleting them.
    """

    sources_to_delete = []
    for source in assertion_to_delete.sources:
        if len(source.assertions) == 1:
            sources_to_delete.append(source)

    db.session.delete(assertion_to_delete)
    db.session.commit()

    for source in sources_to_delete:
        db.session.delete(source)

    db.session.commit()


def get_unapproved_assertion_rows(db):
    unapproved_assertions = db.session.query(Assertion).filter(Assertion.validated == 0).all()
    rows = []
    for assertion in unapproved_assertions:
        for feature in assertion.features:
            rows.extend(make_rows(assertion, feature))
    return rows


def find_attribute_by_name(attributes, name):
    for attribute in attributes:
        if attribute.attribute_definition.name == name:
            return attribute.value

    return None


def make_gene_link(gene):
    gene_token = 'Gene:"%s"[attribute]' % gene
    return '<a href="%s">%s</a>' % (url_for('portal.search', s=gene_token), gene)


def make_display_string(feature):
    """
    Creates HTML-friendly version of a feature. Adds search links to genes.
    """

    feature_name = feature.feature_definition.name
    if feature_name == 'rearrangement':
        rearrangement_type = find_attribute_by_name(feature.attributes, 'rearrangement_type')
        gene1 = find_attribute_by_name(feature.attributes, 'gene1')
        gene2 = find_attribute_by_name(feature.attributes, 'gene2')
        locus = find_attribute_by_name(feature.attributes, 'locus')

        if gene1 and gene2 and locus:
            return '%s--%s %s %s' % (make_gene_link(gene1), make_gene_link(gene2), locus, rearrangement_type)
        elif gene1 and gene2:
            return '%s--%s %s' % (make_gene_link(gene1), make_gene_link(gene2), rearrangement_type)
        elif gene1 and locus:
            return '%s %s %s' % (make_gene_link(gene1), locus, rearrangement_type)
        elif gene1 and rearrangement_type:
            return '%s %s' % (make_gene_link(gene1), rearrangement_type)
        elif gene1:
            return '%s' % (make_gene_link(gene1))
        elif locus:
            return '%s %s' % (locus, rearrangement_type)
        else:
            return rearrangement_type if rearrangement_type else ''
    elif feature_name in ['somatic_variant', 'germline_variant']:
        variant_type = find_attribute_by_name(feature.attributes, 'variant_type')
        gene = find_attribute_by_name(feature.attributes, 'gene')
        protein_change = find_attribute_by_name(feature.attributes, 'protein_change')
        exon = find_attribute_by_name(feature.attributes, 'exon')

        if gene:
            gene = make_gene_link(gene)

        # Any of variant_type, gene, or protein_change may be None. With None as the first parameter to filter(),
        # all False/None values are skipped in the final join() call.
        return ' '.join(filter(None, [gene, variant_type, protein_change]))
    elif feature_name == 'copy_number':
        gene = find_attribute_by_name(feature.attributes, 'gene')
        direction = find_attribute_by_name(feature.attributes, 'direction')
        locus = find_attribute_by_name(feature.attributes, 'locus')

        if gene:
            gene = make_gene_link(gene)

        return ' '.join(filter(None, [gene, direction, locus]))
    elif feature_name == 'microsatellite_stability':
        direction = find_attribute_by_name(feature.attributes, 'direction')

        return direction if direction else ''
    elif feature_name == 'mutational_signature':
        signature_number = find_attribute_by_name(feature.attributes, 'signature_number')

        return ('COSMIC Signature {}'.format(signature_number)) if signature_number else ''
    elif feature_name in ['mutational_burden', 'neoantigen_burden']:
        burden = find_attribute_by_name(feature.attributes, 'burden')

        return burden if burden else ''
    elif feature_name in ['knockdown', 'silencing']:
        gene = find_attribute_by_name(feature.attributes, 'gene')
        technique = find_attribute_by_name(feature.attributes, 'technique')

        if gene:
            gene = make_gene_link(gene)

        return ('%s (%s)' % (gene, technique)) if gene and technique else (gene or technique)
    elif feature_name == 'aneuploidy':
        effect = find_attribute_by_name(feature.attributes, 'effect')

        return effect if effect else ''
    else:
        return 'Unknown feature (%s)' % feature_name


def make_rows(assertion, feature):
    rows = []
    rows.append({
            'feature': feature.feature_definition.readable_name,
            'display_string': Markup(make_display_string(feature)),
            'therapy_name': assertion.therapy_name,
            'therapy_type': assertion.therapy_type,
            'therapy_sensitivity': assertion.therapy_sensitivity,
            'therapy_resistance': assertion.therapy_resistance,
            'favorable_prognosis': assertion.favorable_prognosis,
            'disease': assertion.disease,
            'submitter': urllib.parse.unquote(assertion.submitted_by) if assertion.submitted_by else None,
            'predictive_implication': assertion.predictive_implication,
            'predictive_implication_sort': IMPLICATION_LEVELS_SORT[assertion.predictive_implication],
            'assertion_id': assertion.assertion_id,
            'sources': [s for s in assertion.sources],
    })

    return rows


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


def check_row_exists(db, table, assertion):
    """
    Returns True if the given assertion holds true for the given column.

    :param db: Database connection.
    :param table: Table to search within.
    :param assertion: Assertion to test for.
    :return: True if assertion holds within the table; False otherwise.
    """

    return db.session.query((db.session.query(table).filter(assertion)).exists()).scalar()


check_row_exists.category_table_map = {
    'feature': (FeatureDefinition, FeatureDefinition.readable_name),
    'disease': (Assertion, Assertion.disease),
    'pred': (Assertion, Assertion.predictive_implication),
    'therapy': (Assertion, Assertion.therapy_name),
    'attribute': (FeatureAttributeDefinition, FeatureAttributeDefinition.name)
}


def walk_tokens_right_to_left(tokens):
    token_index = len(tokens) - 1

    while token_index >= 0:
        aggregate_token = tokens[token_index:]
        yield aggregate_token

        token_index -= 1


def sanitize_token_value(token_value):
    return re.sub(r'["\']', '', token_value.strip())


def interpret_unified_search_string(db, search_str):
    """
    Converts a raw (user-provided) search string into a dictionary describing the specific entities in a query.
    Tokenization mimics the "PubMed style." Formally, each token is followed by a bracketed category identifier, and
    tokens containing whitespace are quoted. E.g., a query for clinical trials would be "Clinical trial"[pred].
    However, we attempt to resolve less formally specified queries. Traversing the search string from left to right,
    we build an "aggregate token" combining all tokens seen so far. At each step, the current aggregate token is checked
    against all categories (feature, disease, etc.); if a match is found, the token is added to the query and the
    aggregate token is reset. If no match is found, the current individual token is checked against all categories; if a
    match is found, the current aggregate token (not including the current individual token) is added to the query as an
    "unknown" token and the current individual token is added separately.
    Colons (:) are used to search for attribute values, with the attribute definition given first and the needle value
    given second; e.g., Gene:EGFR[attribute] would add a condition that the attribute Gene must equal "EGFR." Once a
    colon is detected, the token to the left of the colon is used as the attribute definition and the token to the right
    as the attribute needle value. The entire string (with colon) is returned in the query['attribute'] list.

    Example:
    Raw search string: PIK3CA "Invasive Breast Carcinoma"[disease] Preclinical
    Query dictionary: {'feature': 'PIK3CA', 'disease': 'Invasive Breast Carcinoma', 'pred': 'Preclinical'}

    :param db: Database connection.
    :param search_str: Raw unified search string.
    :return: Dictionary representing query in a structured format.
    """

    query = {'feature': [], 'disease': [], 'pred': [], 'therapy': [], 'attribute': [], 'unknown': []}

    # The tokenizing regex contains 3 non-matching groups (the (?:) sections). The first matches either a quoted string
    # or a string of non-whitespace characters, and must occur. The second group differs only in two ways: it must
    # begin with a colon (:) character, and is optional. It matches attribute search strings (Attribute:Value). The
    # final group matches an optional value in [brackets], which correspond to formal category tags.
    token_regex = r'((?:\"[^\"]+\"|[^:\s]+)(?:\:\"[^\"]+\"|[^:\s]+)?(?:\s*\[[^]]+\])?)'
    search_tokens = re.findall(token_regex, search_str)
    unmatched_tokens = []
    for token in search_tokens:
        # The "value-category form" represents a search needle followed by a [category] tag. In the regex below, the
        # first matching group collects all characters before the first [ symbol. The second group matches within the
        # [category tag].
        value_category_form = re.match(r'([^[]+)\[([^]]+)\]', token)
        if value_category_form:
            this_token_needle = sanitize_token_value(value_category_form.group(1))
            this_token_category = value_category_form.group(2).strip()

            if this_token_category in check_row_exists.category_table_map.keys():
                # Begin attempting to match the token(s) left of the [category tag] from right to left. We start with
                # the current token; unmatched_tokens[len(unmatched_tokens):] returns the empty string, leaving only the
                # current token. We then progressively work from right to left until a match is found.
                unmatched_tokens.append(this_token_needle)
                for aggregate_token in walk_tokens_right_to_left(unmatched_tokens):
                    aggregate_token_str = ' '.join(aggregate_token)

                    token_needle = aggregate_token_str
                    check_category = this_token_category
                    check_assertion = check_row_exists.category_table_map[this_token_category][1].ilike(token_needle)

                    # If the token is an Attribute:Value pair, we only want to search using the Attribute name
                    attribute_name, _, attribute_needle = this_token_needle.partition(':')
                    if attribute_needle:
                        token_needle = attribute_name
                        check_category = 'attribute'
                        check_assertion = or_(FeatureAttributeDefinition.name.ilike(token_needle),
                                              FeatureAttributeDefinition.readable_name.ilike(token_needle))

                    if check_row_exists(db, check_category, check_assertion):
                        query[this_token_category].append(aggregate_token_str)
                        unmatched_tokens = unmatched_tokens[:len(unmatched_tokens) - len(aggregate_token)]
                        break
            else:
                query['unknown'].append(this_token_needle)

            continue

        # The "attribute-value form" represents the name of an attribute followed by a colon and the desired value of
        # that attribute (e.g., Gene:EGFR).
        attribute_value_form = re.match(r'(.+):(?:.+)', token)
        if attribute_value_form:
            # Note that we use the entire Attribute:Value pair as the token value to return in the query dict, not
            # the Value string alone; this is for later interpretation by the search engine.
            this_token_attribute = sanitize_token_value(attribute_value_form.group(1))
            this_token_pair = sanitize_token_value(attribute_value_form.group(0))
            unmatched_tokens.append(this_token_pair)

            for aggregate_token in walk_tokens_right_to_left(unmatched_tokens):
                aggregate_token_str = ' '.join(aggregate_token)
                if check_row_exists(db,
                                    FeatureAttributeDefinition,
                                    or_(FeatureAttributeDefinition.name.ilike(this_token_attribute),
                                        FeatureAttributeDefinition.readable_name.ilike(this_token_attribute))):
                    query['attribute'].append(aggregate_token_str)
                    unmatched_tokens = unmatched_tokens[:len(unmatched_tokens) - len(aggregate_token)]
                    break

            continue
        # If this point is reached, the token is neither formally specified with a [category tag] nor an
        # Attribute:Value pair. We will try to determine whether the token (plus or minus the preceding unmatched
        # tokens) informally matches a database entry.
        unmatched_tokens.append(token)
        for aggregate_token in walk_tokens_right_to_left(unmatched_tokens):
            aggregate_token_str = sanitize_token_value(' '.join(aggregate_token))
            # query_info[0] = table, query_info[1] = column
            for category, query_info in check_row_exists.category_table_map.items():
                if check_row_exists(db, query_info[0], query_info[1].ilike(aggregate_token_str)):
                    query[category].append(aggregate_token_str)
                    unmatched_tokens = unmatched_tokens[:len(unmatched_tokens) - len(aggregate_token)]
                    break

    # Dump remaining unmatched tokens into unknown category
    query['unknown'].extend(unmatched_tokens)

    return query


def unified_search(db, search_str):
    """
    Almanac search function. Allows two search methods: Provision of a "unified search string" or individual
    specification of "search needles" using separate GET parameters (for gene, disease, etc.).

    Multiple queries are allowed within each category, and are wrapped into a boolean OR statement. Queries across
    categories are wrapped into a boolean AND statement. E.g.: A query for genes PTEN and POLE plus disease Uterine
    Leiomyoma would be interpreted as "(gene is PTEN OR POLE) AND (disease is Uterine Leiomyoma)". The results would
    be every assertion about Uterine Leiomyoma that references either the PTEN or POLE genes.

    Returns a list of 2-tuples, in which each 2-tuple contains an Assertion and corresponding Feature.
    """

    # Note that we will skip any 'unknown' needles return in the interpreted query
    query = interpret_unified_search_string(db, search_str)

    if not any([query['feature'], query['attribute'], query['disease'], query['pred'], query['therapy']]):
        return []

    # filter_components aggregates the filters we will apply to Assertion. No matter the search, we will always
    # include the "validated=True" filter on Assertions and load all Features & Attributes associated with that
    # Assertion (although they may be further filtered at a later point).
    filter_components = [
        FeatureDefinition.feature_def_id == Feature.feature_def_id,
        Feature.feature_id == FeatureAttribute.feature_id,
        AssertionToFeature.assertion_id == Assertion.assertion_id,
        AssertionToFeature.feature_id == Feature.feature_id,
        Assertion.validated.is_(True),
    ]

    if query['feature']:
        or_stmt = [FeatureDefinition.readable_name.ilike(feature_name) for feature_name in query['feature']]
        filter_components.append(or_(*or_stmt))

    if query['attribute']:
        or_stmt = []
        for attribute_str in query['attribute']:
            attribute_name, _, attribute_needle = attribute_str.partition(':')
            attribute_name = sanitize_token_value(attribute_name)
            attribute_needle = sanitize_token_value(attribute_needle)

            if attribute_name and attribute_needle:
                # Special case - if the attribute is a gene, we will search within FeatureAttributeDefinition.type ==
                # 'gene' instead of within FeatureAttributeDefinition.readable_name. This allows searching across all
                # possible Features that may contain a gene.
                attribute_def_match = or_(FeatureAttributeDefinition.readable_name.ilike(attribute_name),
                                          FeatureAttributeDefinition.name.ilike(attribute_name))
                if attribute_name.lower() == 'gene':
                    attribute_def_match = FeatureAttributeDefinition.type == 'gene'

                or_stmt.append(and_(
                    attribute_def_match,
                    FeatureAttribute.attribute_def_id == FeatureAttributeDefinition.attribute_def_id,
                    FeatureAttribute.value.ilike(attribute_needle)
                ))

        filter_components.append(or_(*or_stmt))

    if query['disease']:
        or_stmt = [Assertion.disease.ilike(cancer) for cancer in query['disease']]
        filter_components.append(or_(*or_stmt))

    if query['pred']:
        or_stmt = [Assertion.predictive_implication.ilike(pred) for pred in query['pred']]
        filter_components.append(or_(*or_stmt))

    if query['therapy']:
        or_stmt = [Assertion.therapy_name.ilike(therapy) for therapy in query['therapy']]
        filter_components.append(or_(*or_stmt))

    # The following produces a list of 2-tuples, where each tuple contains the following table objects:
    # (Assertion, Feature)
    return db.session.query(Assertion, AssertionToFeature).filter(*filter_components).all()
