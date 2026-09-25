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


def test_organization_id_from_short_name():
    assert services.organization_id_from_short_name("FDA") == "agent:org:fda"


def test_sort_biomarker_criteria_lists_present_first():
    biomarkers = [
        {"id": "bmkr:12", "name": "BCR::ABL1", "present": False},
        {"id": "bmkr:14", "name": "CD19 +", "present": True},
        {"id": "bmkr:1", "name": "ER positive", "present": True},
    ]
    assert [b["name"] for b in services.sort_biomarker_criteria(biomarkers)] == [
        "CD19 +",
        "ER positive",
        "BCR::ABL1",
    ]


def test_map_predict():
    assert services.map_predict("predictsSensitivityTo") == "Sensitivity"
    assert services.map_predict("predictsResistanceTo") == "Resistance"
    assert services.map_predict("somethingElse") == "ERROR"


def test_build_query_string_preserves_repeated_keys():
    params = [("agent_id", "agent:org:fda"), ("agent_id", "agent:org:ema")]
    query = services.build_query_string(params)
    assert query.count("agent_id=") == 2


def test_build_query_string_preserves_colons():
    params = [("agent_id", "agent:org:fda"), ("agent_id", "agent:org:ema")]
    assert services.build_query_string(params) == "agent_id=agent:org:fda&agent_id=agent:org:ema"


def test_encode_query_value_preserves_colons():
    assert services.encode_query_value("doc:ema:adcetris") == "doc:ema:adcetris"
    assert services.encode_query_value("a b&c") == "a%20b%26c"
    assert services.encode_query_value(None) == ""


def test_process_statement_summary_keeps_list_fields_only():
    statement = load_fixture("statement.json")
    summary = services.process_statement_summary(record=statement)

    assert set(summary) == {"id", "direction", "organization", "proposition"}
    assert set(summary["proposition"]) == {"predicate", "biomarkers", "cancer_type", "therapies"}
    assert summary["id"] == statement["id"]


def test_term_label_prefers_name_then_description_then_id():
    assert services.term_label({"record_id": "gene:hgnc:3236", "record_name": "EGFR"}) == "EGFR"
    description = "word " * 50
    label = services.term_label(
        {"record_id": "ind:fda:0", "record_name": None, "record_description": description}
    )
    assert label.endswith("…")
    assert len(label) <= services.TERM_LABEL_LENGTH + 1
    assert services.term_label({"record_id": "ind:fda:0", "record_name": None}) == "ind:fda:0"


def test_term_rank_tiers():
    term = {
        "record_id": "gene:hgnc:3236",
        "record_name": "EGFR",
        "record_description": "Epidermal growth factor receptor",
    }
    assert services.term_rank(term=term, query="egfr") == 0
    assert services.term_rank(term=term, query="eg") == 1
    assert services.term_rank(term=term, query="3236") == 2
    assert services.term_rank(term=term, query="growth factor") == 3
    assert services.term_rank(term=term, query="kras") is None
    assert services.term_rank(term=term, query="  ") is None


def test_term_url_for_each_table(app):
    expected = {
        "biomarkers": "/biomarkers/bmkr:1",
        "genes": "/genes/bmkr:1",
        "diseases": "/diseases/bmkr:1",
        "therapies": "/therapies/bmkr:1",
        "documents": "/documents/bmkr:1",
        "agents": "/organizations/bmkr:1",
        "indications": "/indications/bmkr:1",
    }
    assert set(expected) == set(services.TERM_TABLES)
    with app.test_request_context():
        for table, url in expected.items():
            assert services.term_url({"table": table, "record_id": "bmkr:1"}) == url


def test_term_snippet_centers_on_match():
    text = ("lorem ipsum " * 20) + "BRCA1 mutated" + (" dolor sit" * 20)
    before, match, after = services.term_snippet(text=text, query="brca1", width=60)
    assert match == "BRCA1"
    assert before.startswith("…")
    assert after.endswith("…")
    assert len(before) + len(match) + len(after) <= 62


def test_term_snippet_without_match():
    assert services.term_snippet(text="short", query="zzz") == ("short", "", "")


def test_term_rank_unnamed_terms_skip_id_substring_matches():
    term = {
        "record_id": "ind:fda:braftovi:0",
        "record_name": None,
        "record_description": "BRAFTOVI is a kinase inhibitor indicated for BRAF V600E melanoma.",
    }
    assert services.term_rank(term=term, query="braf") == 3
    assert services.term_rank(term=term, query="ind:fda:braftovi") == 1
    assert services.term_rank(term=term, query="ind:fda:braftovi:0") == 0
    assert services.term_rank(term={**term, "record_description": "Other text."}, query="braftovi") is None
