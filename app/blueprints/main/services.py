"""
services.py

Service-layer functions for intermediate processing of data retrieved from handlers or API requests.
"""
import collections

def append_field_from_matching_records(
        target_list: list[dict],
        source_list: list[dict],
        source_field: str,
        new_field_name: str,
        match_key: str = 'id'
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
    source_lookup = {item[match_key]: item[source_field] for item in source_list if match_key in item and source_field in item}

    for record in target_list:
        record_id = record.get(match_key)
        if record_id in source_lookup:
            record[new_field_name] = source_lookup[record_id]

    return target_list


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
        key = record.get('type')
        categorized[key].append(record)
    return dict(categorized)

def extract_biomarkers(biomarkers: list[dict]):
    """
    Extracts `id` and `name` from a list of dictionaries representing biomarkers.

    Args:
        biomarkers (list[dict]): A list of dictionaries containing biomarker information.

    Returns:
        list[dict]: A list of dictionaries only containing `id` and `name` keys for each biomarker in biomarkers.
    """
    return [{'id': b['id'], 'name': b['name']} for b in biomarkers]

def extract_diseases(disease: dict):
    """
    Extracts `id` and `name` from a dictionary representing cancer types / diseases,
    from the `conditionQualifier` field.

    Args:
        disease (dict): A dictionary containing cancer type / disease information.

    Returns:
        dict: A dictionary only containing `id` and `name` keys.
    """
    return {'id': disease['id'], 'name': disease['name']}

def extract_therapies(object_therapeutic: dict):
    """
    Extracts `id` and `name` from a dictionary representing therapy(ies), from the `objectTherapeutic` field. Single
    therapies are managed separately from therapy groups.

    Args:
        object_therapeutic (dict): A dictionary containing therapy information, from the `objectTherapeutic` field.

    Returns:
         list[dict]: A list of dictionaries only containing `id` and `name` keys for each therapy in objectTherapeutic.
    """
    if 'therapies' in object_therapeutic:
        return [{'id': t['id'], 'name': t['name']} for t in object_therapeutic['therapies']]
    else:
        return [{'id': object_therapeutic['id'], 'name': object_therapeutic['name']}]

def map_predict(string: str):
    """
    Maps the predicate string from the values required by VA-Spec to the chosen string to display within the view.

    Args:
        string (str): The value corresponding to the predicate field in a proposition record.

    Returns:
        str: The mapped string to display within the view.
    """
    if string == 'predictSensitivityTo':
        return 'Sensitivity'
    elif string == 'predictResistanceTo':
        return 'Resistance'
    else:
        return 'ERROR'

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
        new_record = {
            'id': record['id'],
            'proposition': simplify_proposition_record(record=record['proposition']),
            'direction': '+' if record['direction'] == 'supports' else '-',
            'documents': [(doc['id'], doc['name']) for doc in record['reportedIn']]
        }
        new_records.append(new_record)
    return new_records

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
        'id': record['id'],
        'type': record['type'],
        'predicate': map_predict(string=record['predicate'])
    }
    if record['type'] == 'VariantTherapeuticResponseProposition':
        biomarkers = extract_biomarkers(biomarkers=record['biomarkers'])
        new_record['biomarkers'] = sort_dicts_by_key(data=biomarkers, key='name')
        new_record['cancer_type'] = extract_diseases(disease=record['conditionQualifier'])
        therapies = extract_therapies(object_therapeutic=record['objectTherapeutic'])
        new_record['therapies'] = sort_dicts_by_key(data=therapies, key='name')
    else:
        # We'll add if else statements as we support additional proposition types
        print('This should not happen!')
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
