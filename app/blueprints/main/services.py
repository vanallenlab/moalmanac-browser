"""
services.py

Service-layer functions for intermediate processing of data retrieved from handlers or API requests.
"""

import collections
import flask
import urllib.parse

# Indication statuses shown on list pages; Superseded and Withdrawn indications are only reachable by URL.
ACTIVE_INDICATION_STATUSES = ("Approved", "Accelerated")

# Maps each `terms.table` value to its display type, plural display type, detail endpoint, and the endpoint's
# id argument. Search result concept filters are listed in this order.
TERM_TABLES = {
    "biomarkers": ("Biomarker", "Biomarkers", "main.biomarkers", "biomarker_id"),
    "genes": ("Gene", "Genes", "main.genes", "gene_id"),
    "diseases": ("Cancer type", "Cancer types", "main.diseases", "disease_id"),
    "therapies": ("Therapy", "Therapies", "main.therapies", "therapy_id"),
    "documents": ("Document", "Documents", "main.documents", "document_id"),
    "agents": ("Organization", "Organizations", "main.organizations", "organization_id"),
    "indications": ("Indication", "Indications", "main.indications", "indication_id"),
}

# Maps the `type` of a record a contribution was made to onto its detail endpoint and the endpoint's id argument.
CONTRIBUTION_RECORD_ENDPOINTS = {
    "Indication": ("main.indications", "indication_id"),
    "Statement": ("main.statements", "statement_id"),
}

# Maximum length of a term label derived from its description.
TERM_LABEL_LENGTH = 120


def append_field_from_matching_records(
    target_list: list[dict],
    source_list: list[dict],
    source_field: str,
    new_field_name: str,
    match_key: str = "id",
):
    """
    Appends a field from one list of records, source_list, to another, target_list, based on matching keys.

    Args:
        target_list (list[dict]): The list of records to be updated.
        source_list (list[dict]): The list of records containing the values to add.
        source_field (str): The field from the source records to append.
        new_field_name (str): The name of the new field to add to the target records.
        match_key (str): The key to match between target and source records.

    Returns:
        list[dict]: The updated list of target records with the appended field.
    """
    source_lookup = {
        item[match_key]: item[source_field]
        for item in source_list
        if match_key in item and source_field in item
    }

    for record in target_list:
        record_id = record.get(match_key)
        if record_id in source_lookup:
            record[new_field_name] = source_lookup[record_id]

    return target_list


def append_contributions_count(contributors: list[dict], contributions: list[dict]):
    """
    Adds a `contributions_count` field to each contributor, counting the contributions made by it.

    Args:
        contributors (list[dict]): Agent records from the API.
        contributions (list[dict]): Contribution records from the API.

    Returns:
        list[dict]: The contributors, each with a `contributions_count` field.
    """
    counts = collections.Counter(
        contribution["contributor"]["id"] for contribution in contributions
    )
    for contributor in contributors:
        contributor["contributions_count"] = counts.get(contributor["id"], 0)
    return contributors


def categorize_propositions(records: list[dict]):
    """
    Categorizes propositions by their type.

    Args:
        records (list[dict]): A list of proposition records.

    Returns:
        dict: A dictionary of proposition types and their corresponding records.
    """
    categorized = collections.defaultdict(list)
    for record in records:
        key = record.get("type")
        categorized[key].append(record)
    return dict(categorized)


def extract_biomarkers(biomarkers: list[dict]):
    """
    Extracts `id` and `name` from a list of dictionaries representing biomarker criteria, as found within a
    proposition's `biomarkers` extension (each item is `{id, present, subject: Biomarker}`).

    Args:
        biomarkers (list[dict]): A list of biomarker criterion dictionaries.

    Returns:
        list[dict]: A list of dictionaries only containing `id` and `name` keys for each biomarker's subject.
    """
    return [
        {
            "id": criterion["subject"]["id"],
            "name": criterion["subject"]["name"],
            "present": criterion["present"]
        }
        for criterion in biomarkers
    ]


def extract_biomarker_genes(biomarker: dict):
    """
    Extracts the genes associated with a biomarker record from its `constraints`. Genes may appear as the
    `featureContext` of a constraint (e.g. a variant on a single gene) or within `adjoinedElements` of an
    `AdjacencyConstraint` (e.g. a fusion).

    Args:
        biomarker (dict): A biomarker record from the API.

    Returns:
        list[dict]: A sorted, de-duplicated list of dictionaries containing `id` and `name` for each gene.
    """
    genes = {}
    for constraint in biomarker.get("constraints") or []:
        feature_context = constraint.get("featureContext")
        if feature_context:
            genes[feature_context["id"]] = {
                "id": feature_context["id"],
                "name": feature_context["name"],
            }
        for element in constraint.get("adjoinedElements") or []:
            # Fusion partners are not always known genes; an unknown partner is represented as an
            # `UnspecifiedElement` with no `id`/`name`, which is skipped here.
            if element.get("conceptType") == "Gene":
                genes[element["id"]] = {"id": element["id"], "name": element["name"]}
    return sort_dicts_by_key(data=list(genes.values()), key="name")


def extract_biomarker_about(biomarker: dict):
    """
    Builds the rows displayed in the About card of the biomarker view. Which rows are shown depends on the
    biomarker's `biomarker_type` extension. A row is a dictionary with a `label` and either a `value` or, for
    gene context, a list of `genes`. Rows without a value are omitted.

    Args:
        biomarker (dict): A biomarker record from the API, with `genes` already extracted.

    Returns:
        list[dict]: The rows to display, in order.
    """
    extensions = biomarker.get("extensions") or []
    constraints = biomarker.get("constraints") or []
    biomarker_type = get_extension_value(list_of_extensions=extensions, name="biomarker_type")

    def constraint_of_type(constraint_type: str):
        return next((c for c in constraints if c.get("type") == constraint_type), None)

    def copy_change_row():
        constraint = constraint_of_type("CopyChangeConstraint") or {}
        return {"label": "Copy change", "value": constraint.get("copyChange")}

    def extension_row(name: str):
        return {
            "label": format_label(name),
            "value": get_extension_value(list_of_extensions=extensions, name=name),
        }

    gene_context_row = {"label": "Gene context", "genes": biomarker.get("genes") or []}

    rows = [{"label": "Biomarker type", "value": biomarker_type}]
    if biomarker_type == "Copy number":
        rows += [gene_context_row, copy_change_row()]
    elif biomarker_type == "Copy number (arm level)":
        location = (constraint_of_type("DefiningLocationConstraint") or {}).get("location") or {}
        reference = (location.get("sequenceReference") or {}).get("description") or ""
        location_value = None
        if reference:
            location_value = f"{reference.rstrip('.')} {location.get('start')} - {location.get('end')}"
        rows += [{"label": "Location", "value": location_value}, copy_change_row()]
    elif biomarker_type == "Germline variant":
        rows.append(gene_context_row)
        rows += [
            extension_row(extension["name"])
            for extension in extensions
            if extension.get("name") != "biomarker_type"
        ]
    elif biomarker_type in ("Homologous recombination", "Microsatellite stability", "Mismatch repair"):
        rows.append(extension_row("status"))
    elif biomarker_type == "Protein expression":
        rows += [extension_row(name) for name in ("marker", "unit", "equality", "value")]
    elif biomarker_type == "Somatic variant":
        rows.append(gene_context_row)
        allele = (constraint_of_type("DefiningAlleleConstraint") or {}).get("allele") or {}
        rows += [
            {"label": format_expression_syntax(expression.get("syntax")), "value": expression.get("value")}
            for expression in allele.get("expressions") or []
        ]
    elif biomarker_type == "Tumor mutational burden":
        rows += [extension_row("classification"), extension_row("minimum_mutations_per_megabase")]
    elif biomarker_type in ("Gene fusion", "Rearrangement", "Translocation", "Wild type"):
        rows.append(gene_context_row)
    else:
        # Types without a dedicated layout show gene context and all remaining extensions.
        rows.append(gene_context_row)
        rows += [
            extension_row(extension["name"])
            for extension in extensions
            if extension.get("name") != "biomarker_type"
        ]

    return [row for row in rows if row.get("genes") or row.get("value") not in (None, "")]


def extract_diseases(disease: dict):
    """
    Extracts `id` and `name` from a dictionary representing cancer types / diseases,
    from the `conditionQualifier` field.

    Args:
        disease (dict): A dictionary containing cancer type / disease information.

    Returns:
        dict: A dictionary only containing `id` and `name` keys.
    """
    return {"id": disease["id"], "name": disease["name"]}


def extract_organizations(propositions: dict):
    """
    Returns organizations associated with Variant Therapeutic Response Propositions to filter by regulatory agency.

    Args:
        propositions (dict): A dictionary processed propositions by type from /search route.

    Returns:
        list(dict): list of dictionaries of agent ids.
    """
    agents = set()
    for proposition in propositions.get("VariantTherapeuticResponseProposition", []):
        for agent in proposition.get("aggregates", {}).get("by_agent", []):
            if "id" in agent:
                agents.add(agent["id"])
    return [{"id": agent_id} for agent_id in sorted(agents)]


def extract_therapies(object_therapeutic: dict):
    """
    Extracts `id` and `name` from a dictionary representing therapy(ies), from the `objectTherapeutic` field. Single
    therapies are managed separately from therapy groups.

    Args:
        object_therapeutic (dict): A dictionary containing therapy information, from the `objectTherapeutic` field.

    Returns:
         list[dict]: A list of dictionaries only containing `id` and `name` keys for each therapy in objectTherapeutic.
    """
    if "therapies" in object_therapeutic:
        return [
            {"id": t["id"], "name": t["name"]} for t in object_therapeutic["therapies"]
        ]
    else:
        return [{"id": object_therapeutic["id"], "name": object_therapeutic["name"]}]


def build_query_string(params: list[tuple]):
    """
    Encodes a list of (key, value) tuples into a URL query string, preserving repeated keys.

    Args:
        params (list[tuple]): A list of (key, value) tuples, e.g. from
            `requests.API.get_config_organization_filters`.

    Returns:
        str: A URL-encoded query string, e.g. "agent_id=agent:org:fda&agent_id=agent:org:ema". Colons are
            left unencoded so that ids appear in the URL as they do in the API.
    """
    return urllib.parse.urlencode(params or [], safe=":")


def encode_query_value(value: str | None):
    """
    Percent-encodes a value for use in a URL query string, leaving `:` unencoded so prefixed ids
    (e.g. "bmkr:0", "doc:ema:adcetris") are preserved as-is.

    Args:
        value (str | None): The value to encode.

    Returns:
        str: The encoded value. Returns an empty string if `value` is None.
    """
    if value is None:
        return ""
    return urllib.parse.quote(str(value), safe=":")


def format_expression_syntax(syntax: str | None):
    """
    Formats a variation expression syntax for display as a label, capitalizing the "hgvs" prefix while
    leaving the sequence type lowercase, e.g. "hgvs.p" becomes "HGVS.p". Other syntaxes are returned as-is.

    Args:
        syntax (str | None): The expression syntax, e.g. "hgvs.p".

    Returns:
        str | None: The formatted syntax.
    """
    if syntax and syntax.startswith("hgvs"):
        return "HGVS" + syntax[len("hgvs"):]
    return syntax


def format_label(name: str):
    """
    Formats an extension name for display as a label, e.g. "minimum_mutations_per_megabase" becomes
    "Minimum mutations per megabase".

    Args:
        name (str): The extension name.

    Returns:
        str: The name with underscores replaced by spaces, the first letter capitalized, and the rest lowercase.
    """
    return name.replace("_", " ").capitalize()


def get_extension(list_of_extensions: list, name: str):
    """
    Subsets `list_of_extensions` to retrieve the extension whose name matches `name`.

    Args:
        - list_of_extensions (list): A list of dictionaries representing extensions.
        - name (str): The name of the extension to retrieve.

    Returns:
        - list: A list of extensions whose name value matches `name`.
    """
    return [
        extension
        for extension in (list_of_extensions or [])
        if extension.get("name") == name
    ]


def get_extension_value(list_of_extensions: list, name: str, default=None):
    """
    Retrieves the `value` of the extension whose name matches `name`.

    Args:
        - list_of_extensions (list): A list of dictionaries representing extensions.
        - name (str): The name of the extension to retrieve.
        - default: The value to return if no matching extension is found.

    Returns:
        The extension's `value`, or `default` if no extension named `name` exists.
    """
    matches = get_extension(list_of_extensions=list_of_extensions, name=name)
    return matches[0]["value"] if matches else default


def short_agent_id(agent_id: str | None):
    """
    Shortens a prefixed agent id (e.g. "agent:org:fda") to its display form (e.g. "FDA").

    Args:
        agent_id (str | None): A prefixed agent id.

    Returns:
        str: The text after the final `:` in `agent_id`, upper-cased. Returns an empty string if `agent_id`
            is falsy.
    """
    if not agent_id:
        return ""
    return agent_id.rsplit(":", 1)[-1].upper()


def filter_search_results_required_organization(records: list[dict], organization_id: str) -> list[dict]:
    """
    Filters processed proposition records from process_propositions function
    to require the specified organization.

    Args:
        records (list[dict]): List of proposition records from process_propositions function.

    Returns:
        list[dict]: records, requires organization to be listed within aggregates['by_agent']
    """
    filtered = []
    for record in records:
        by_agent = record.get("aggregates", {}).get("by_agent", [])
        if any(agent.get("id") == organization_id for agent in by_agent):
            filtered.append(record)
    return filtered


def map_predict(string: str):
    """
    Maps the predicate string from the values required by VA-Spec to the chosen string to display within the view.

    Args:
        string (str): The value corresponding to the predicate field in a proposition record.

    Returns:
        str: The mapped string to display within the view.
    """
    if string == "predictsSensitivityTo":
        return "Sensitivity"
    elif string == "predictsResistanceTo":
        return "Resistance"
    else:
        return "ERROR"


def organization_id_from_short_name(short_name: str):
    """
    Expands an organization's short name (e.g. "fda") to its agent id (e.g. "agent:org:fda").

    Args:
        short_name (str): An organization's short name, as used in legacy browser URLs.

    Returns:
        str: The organization's agent id.
    """
    return f"agent:org:{short_name.lower()}"


def process_biomarker(record: dict):
    """
    Process a biomarker record from the API for use within the biomarker view. Adds a `genes` field derived
    from the record's constraints, drops extensions with a null value, and adds the `about` rows displayed
    for the record's biomarker type.

    Args:
        record (dict): A biomarker record from the API.

    Returns:
        record (dict): A dictionary of the original record with `genes` and `about` added and null
            extensions removed.
    """
    record = dict(record)
    record["genes"] = extract_biomarker_genes(biomarker=record)
    record["extensions"] = [
        extension
        for extension in record.get("extensions") or []
        if extension.get("value") is not None
    ]
    record["about"] = extract_biomarker_about(biomarker=record)
    return record


def process_contribution_records(records: list[dict]):
    """
    Flattens contributions requested with `include_records=true` into rows for contribution tables that list
    records. Records of the same type with the same text within one contribution (e.g. the statements derived from
    one indication, which share its description) are grouped into a single row.

    Args:
        records (list[dict]): Contribution records from the API, each with a `records` extension.

    Returns:
        list[dict]: Rows with `date`, `contributor` (the contribution's agent), `label` (the records' name, else
            their description, else the record id), `type` (e.g. "Statement"), and `records` (a list of `id` and
            `url` for each grouped record) fields, sorted by date in descending order.
    """
    rows = {}
    for contribution in records:
        contributed_records = get_extension_value(
            list_of_extensions=contribution.get("extensions"),
            name="records",
            default=[],
        )
        for record in contributed_records:
            label = record.get("name") or record.get("description") or record["id"]
            row = rows.setdefault(
                (contribution["id"], record["type"], label),
                {
                    "date": contribution["date"],
                    "contributor": contribution["contributor"],
                    "label": label,
                    "type": record["type"],
                    "records": [],
                },
            )
            endpoint, argument = CONTRIBUTION_RECORD_ENDPOINTS[record["type"]]
            row["records"].append(
                {
                    "id": record["id"],
                    "url": flask.url_for(endpoint, **{argument: record["id"]}),
                }
            )
    return sort_dicts_by_key(data=list(rows.values()), key="date", reverse=True)


def process_gene(record: dict):
    """
    Process a gene record from the API for use within the genes view. Extracts the gene's location, and
    identifies its Ensembl, NCBI and RefSeq mappings by coding system rather than assuming a fixed order.

    Args:
        record (dict): A gene record from the API.

    Returns:
        record (dict): A dictionary of the original record with extensions moved to the root.
    """
    record = dict(record)
    record["location"] = get_extension_value(
        list_of_extensions=record.get("extensions"), 
        name="location",
    )

    mapping_systems = {
        "https://www.ensembl.org": "ensembl",
        "https://www.ncbi.nlm.nih.gov/gene": "ncbi",
        "https://www.ncbi.nlm.nih.gov/nuccore": "refseq",
    }
    mappings_by_source = {}
    for mapping in record.get("mappings") or []:
        source = mapping_systems.get(mapping.get("coding", {}).get("system"))
        if source:
            mappings_by_source[source] = mapping
    record["mappings_by_source"] = mappings_by_source
    return record


def process_proposition(record: dict):
    """
    Processes a single proposition record from the API response into a simplified format for the propositions view.

    Args:
        record (dict): A proposition record from the API.

    Returns:
        record (dict): A simplified proposition record.
    """
    return simplify_proposition_record(record=record)


def process_propositions(records: list[dict]):
    """
    Processes proposition records from the API response into a simplified format for the propositions view.

    Args:
        records (list[dict]): A list of proposition records from the API.

    Returns:
        dict: A dictionary of proposition types and their corresponding simplified records.
    """
    simplified = simplify_proposition_records(records=records)
    return categorize_propositions(records=simplified)


def process_indication(record: dict):
    """
    Processes an indication record from the API response into a simplified format, flattening its reporting
    document, publishing agent and extensions for use within the indication and related views.

    Args:
        record (dict): An indication record from the API.

    Returns:
        dict: A simplified indication record.
    """
    reported_in = record.get("reportedIn") or []
    document = reported_in[0] if reported_in else {}
    agent = get_extension_value(
        list_of_extensions=document.get("extensions"), 
        name="agent", 
        default={},
    )
    extensions = record.get("extensions") or []
    return {
        "id": record["id"],
        "description": record.get("description"),
        "document": document,
        "agent": agent,
        "status": get_extension_value(extensions, "status"),
        "reimbursement_scheme": get_extension_value(extensions, "reimbursement_scheme"),
        "reimbursement_comment": get_extension_value(extensions, "reimbursement_comment"),
        "contributions": sort_contributions(contributions=record.get("contributions") or []),
    }


def process_search_terms(terms: list[dict]):
    """
    Processes records from the terms table into the fields used by the term search box's suggestions.

    Args:
        terms (list[dict]): Records from the terms table.

    Returns:
        list[dict]: Terms with `id`, `name`, `description`, `label`, `type`, and `url` fields.
    """
    return [
        {
            "id": term["record_id"],
            "name": term["record_name"],
            "description": term["record_description"],
            "label": term_label(term=term),
            "type": term_type(term=term),
            "url": term_url(term=term),
        }
        for term in terms
    ]


def process_statement(record: dict):
    """
    Processes a single statement record from the API response into a simplified format for the statements view.

    Args:
        record (dict): A statement record from the API.

    Returns:
        dict: A simplified statement record.
    """
    reported_in = record.get("reportedIn") or []
    document = reported_in[0] if reported_in else {}
    agent = get_extension_value(
        list_of_extensions=document.get("extensions"), 
        name="agent", 
        default={},
    )
    extensions = record.get("extensions") or []
    indication = get_extension_value(
        list_of_extensions=extensions, 
        name="indication",
    )
    return {
        "id": record["id"],
        "proposition": simplify_proposition_record(record=record["proposition"]),
        "description": record["description"],
        "direction": "Supports" if record["direction"] == "supports" else "Disputes",
        "documents": [
            {
                "id": doc["id"],
                "documentType": doc["documentType"],
                "name": doc["name"],
                "description": doc["description"],
            }
            for doc in reported_in
        ],
        "agent": agent.get("id", "").upper() if agent else None,
        "organization": short_agent_id(agent.get("id")) if agent else None,
        "status": get_extension_value(list_of_extensions=extensions, name="status"),
        "strength": (record.get("strength") or {}).get("name"),
        "indication": process_indication(record=indication) if indication else None,
        "contributions": sort_contributions(contributions=record.get("contributions") or []),
        "raw": record,
    }


def process_statements(records: list[dict]):
    """
    Processes statement records from the API response into a simplified format for the statements view.

    Args:
        records (list[dict]): A list of statement records from the API.

    Returns:
        dict: A dictionary of statements and their corresponding simplified records.
    """
    new_records = []
    for record in records:
        new_record = process_statement(record=record)
        new_records.append(new_record)
    return new_records


def process_statement_summary(record: dict):
    """
    Processes a statement record from the API into the minimal fields shown in the statements list view. These
    summaries are what the local cache stores, since full statement records are fully dereferenced and large.

    Args:
        record (dict): A statement record from the API.

    Returns:
        dict: A statement summary with `id`, `direction`, `organization`, and a `proposition` holding `predicate`,
            `biomarkers`, `cancer_type`, and `therapies`.
    """
    processed = process_statement(record=record)
    proposition = processed["proposition"]
    return {
        "id": processed["id"],
        "direction": processed["direction"],
        "organization": processed["organization"],
        "proposition": {
            "predicate": proposition["predicate"],
            "biomarkers": proposition["biomarkers"],
            "cancer_type": proposition["cancer_type"],
            "therapies": proposition["therapies"],
        },
    }


def process_therapy(record: dict):
    """
    Process a therapy record from the API for use within the therapies view. Currently, this simply extracts the
    therapy strategies and therapy type.

    Args:
        record (dict): A therapy record from the API.

    Returns:
        record (dict): A dictionary of the original record with extensions moved to the root.
    """
    record = dict(record)
    therapy_strategy = get_extension_value(
        list_of_extensions=record.get("extensions"), 
        name="therapy_strategy", 
        default=[],
    )
    record["therapy_strategy"] = ", ".join(therapy_strategy or [])
    record["therapy_type"] = get_extension_value(
        list_of_extensions=record.get("extensions"), 
        name="therapy_type",
    )
    return record


def simplify_proposition_record(record: dict):
    """
    Processes a proposition record from the API response into a simplified format, keeping only the necessary fields
    for the propositions view and reformatting some values.

    Args:
        record (dict): A proposition record from the API.

    Returns:
        new_record (dict): A simplified proposition record.
    """
    new_record = {
        "id": record["id"],
        "type": record["type"],
        "predicate": map_predict(string=record["predicate"]),
        "aggregates": record.get("aggregates", {}),
    }
    if record["type"] == "VariantTherapeuticResponseProposition":
        biomarker_criteria = get_extension_value(
            list_of_extensions=record.get("extensions"), 
            name="biomarkers", 
            default=[],
        )
        biomarkers = extract_biomarkers(biomarkers=biomarker_criteria)
        new_record["biomarkers"] = sort_biomarker_criteria(biomarkers=biomarkers)
        new_record["cancer_type"] = extract_diseases(
            disease=record["conditionQualifier"],
        )
        therapies = extract_therapies(object_therapeutic=record["objectTherapeutic"])
        new_record["therapies"] = sort_dicts_by_key(data=therapies, key="name")
        new_record["proposition_type"] = "Therapeutic response"
    else:
        # We'll add if else statements as we support additional proposition types
        print("This should not happen!")
    return new_record


def simplify_proposition_records(records: list[dict]):
    """
    Processes the proposition records from the API response into a simplified format, keeping only the necessary fields
    for the propositions view and reformatting some values.

    Args:
        records (list[dict]): A list of proposition records from the API.

    Returns:
        new_records (list[dict]): A list of simplified proposition records.
    """
    new_records = []
    for record in records:
        new_record = simplify_proposition_record(record=record)
        new_records.append(new_record)
    return new_records


def sort_biomarker_criteria(biomarkers: list[dict]):
    """
    Sorts biomarker criteria so that present biomarkers come before absent ones, each group sorted by name.

    Args:
        biomarkers (list[dict]): Biomarker criteria from `extract_biomarkers`, each with `name` and `present`.

    Returns:
        list[dict]: The sorted biomarker criteria.
    """
    return sorted(
        biomarkers,
        key=lambda biomarker: (not biomarker["present"], biomarker["name"]),
    )


def sort_contributions(contributions: list[dict]):
    """
    Sorts contributions by date, most recent first.

    Args:
        contributions (list[dict]): Contribution records from the API.

    Returns:
        list[dict]: The sorted contributions.
    """
    return sort_dicts_by_key(data=contributions, key="date", reverse=True)


def sort_dicts_by_key(data: list[dict], key, reverse=False):
    """
    Sort a list of dictionaries by the value of a specified key.

    Args:
        data (list[dict]): The list of dictionaries to sort.
        key (str): The dictionary key to sort by.
        reverse (bool): Whether to sort in descending order. Default is False (ascending).

    Returns:
        list[dict]: The sorted list of dictionaries.

    Raises:
        KeyError: If any dictionary in the list is missing the specified key.
    """
    try:
        return sorted(data, key=lambda d: d[key], reverse=reverse)
    except KeyError as e:
        raise KeyError(f"Missing key '{key}' in one or more dictionaries.") from e


def term_label(term: dict, max_length: int = TERM_LABEL_LENGTH):
    """
    Returns the display label for a term: its name, or else its description (trimmed), or else its id.

    Args:
        term (dict): A record from the terms table.
        max_length (int): The maximum length of a label derived from the description.

    Returns:
        str: The term's display label.
    """
    if term.get("record_name"):
        return term["record_name"]
    description = term.get("record_description")
    if description:
        if len(description) <= max_length:
            return description
        return description[:max_length].rsplit(" ", 1)[0] + "…"
    return term["record_id"]


def term_rank(term: dict, query: str):
    """
    Ranks how well a term matches a search query, where lower is better.

    Args:
        term (dict): A record from the terms table.
        query (str): The search query.

    Returns:
        int | None: 0 for an exact id or name match, 1 if the id or name starts with the query, 2 if the id or
            name contains the query, 3 if only the description contains the query, or None if nothing matches.
            Terms without a name (e.g. indications) only match their id exactly or by prefix, since ids like
            `ind:fda:braftovi:0` would otherwise surface them as name-like matches for "braf".
    """
    query = query.strip().lower()
    if not query:
        return None
    keys = [(term.get(field) or "").lower() for field in ("record_id", "record_name")]
    if query in keys:
        return 0
    if any(key.startswith(query) for key in keys):
        return 1
    if term.get("record_name") and any(query in key for key in keys):
        return 2
    if query in (term.get("record_description") or "").lower():
        return 3
    return None


def term_snippet(text: str, query: str, width: int = 160):
    """
    Returns about `width` characters of `text` around the first case-insensitive match of `query`, split so the
    match can be highlighted.

    Args:
        text (str): The text to excerpt, e.g. a term's description.
        query (str): The search query.
        width (int): The approximate length of the excerpt.

    Returns:
        tuple[str, str, str]: The text before the match, the match, and the text after the match. If `query` is not
            found, the first `width` characters of `text` and two empty strings.
    """
    index = text.lower().find(query.strip().lower())
    if index == -1:
        return (text[:width] + ("…" if len(text) > width else ""), "", "")
    length = len(query.strip())
    start = max(0, index - (width - length) // 2)
    # Start on a word boundary, as long as it doesn't skip past the match.
    space = text.find(" ", start)
    if start > 0 and -1 < space < index:
        start = space + 1
    end = min(len(text), start + width)
    before = ("…" if start > 0 else "") + text[start:index]
    after = text[index + length:end] + ("…" if end < len(text) else "")
    return (before, text[index:index + length], after)


def term_type(term: dict):
    """
    Returns the display type (e.g. "Cancer type") of a term.

    Args:
        term (dict): A record from the terms table.

    Returns:
        str: The term's display type.
    """
    return TERM_TABLES[term["table"]][0]


def term_url(term: dict):
    """
    Builds the URL of a term's detail page from its table and record id.

    Args:
        term (dict): A record from the terms table.

    Returns:
        str: The URL of the term's detail page.
    """
    _, _, endpoint, argument = TERM_TABLES[term["table"]]
    return flask.url_for(endpoint, **{argument: term["record_id"]})
