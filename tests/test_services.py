"""
test_services.py

Tests for app/blueprints/main/services.py against real record shapes from moalmanac-db's dereferenced fixtures.
"""

from app.blueprints.main import services

from .conftest import load_fixture


def test_simplify_proposition_record():
    proposition = load_fixture("proposition.json")
    simplified = services.simplify_proposition_record(record=proposition)

    assert simplified["id"] == proposition["id"]
    assert simplified["predicate"] in {"Sensitivity", "Resistance"}
    assert simplified["predicate"] != "ERROR"
    assert simplified["proposition_type"] == "Therapeutic response"
    assert simplified["biomarkers"]
    assert all("id" in b and "name" in b for b in simplified["biomarkers"])
    assert simplified["cancer_type"]["name"]
    assert simplified["therapies"]


def test_extract_biomarker_genes_skips_unspecified_fusion_partner():
    biomarker = load_fixture("biomarker_fusion.json")
    genes = services.extract_biomarker_genes(biomarker=biomarker)

    assert len(genes) == 1
    assert genes[0]["name"] == "NRG1"


def test_process_biomarker_drops_null_extensions_and_adds_genes():
    biomarker = load_fixture("biomarker_fusion.json")
    processed = services.process_biomarker(record=biomarker)

    assert processed["genes"]
    assert all(ext.get("value") is not None for ext in processed["extensions"])


def test_process_indication():
    indication = load_fixture("indication.json")
    processed = services.process_indication(record=indication)

    assert processed["id"] == indication["id"]
    assert processed["description"]
    assert processed["document"]["id"]
    assert processed["agent"]["name"]
    assert processed["status"] in {"Approved", "Accelerated", "Withdrawn", "Superseded"}


def test_process_statement():
    statement = load_fixture("statement.json")
    processed = services.process_statement(record=statement)

    assert processed["id"] == statement["id"]
    assert processed["direction"] in {"Supports", "Disputes"}
    assert processed["organization"]
    assert processed["organization"] == processed["organization"].upper()
    assert processed["strength"]
    assert processed["indication"] is not None
    assert processed["indication"]["agent"]["name"]
    assert processed["proposition"]["predicate"] != "ERROR"


def test_short_agent_id():
    assert services.short_agent_id("agent:org:fda") == "FDA"
    assert services.short_agent_id(None) == ""


def test_map_predict():
    assert services.map_predict("predictsSensitivityTo") == "Sensitivity"
    assert services.map_predict("predictsResistanceTo") == "Resistance"
    assert services.map_predict("somethingElse") == "ERROR"


def test_build_query_string_preserves_repeated_keys():
    params = [("agent_id", "agent:org:fda"), ("agent_id", "agent:org:ema")]
    query = services.build_query_string(params)
    assert query.count("agent_id=") == 2
