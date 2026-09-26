"""
test_routes.py

End-to-end route tests against a locally running moalmanac-api (http://localhost:8080) and the sqlite
cache of the instance given by APP_CONFIG (default: deploy/default/config.ini). These are integration tests, not
unit tests: they are skipped automatically if the local API cannot be reached.
"""

import socket

import pytest


def _api_is_reachable():
    try:
        with socket.create_connection(("localhost", 8080), timeout=1):
            return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(
    not _api_is_reachable(),
    reason="Requires the moalmanac-api running locally at http://localhost:8080",
)


LIST_ROUTES = [
    "/",
    "/about",
    "/biomarkers",
    "/contributors",
    "/diseases",
    "/documents",
    "/genes",
    "/indications",
    "/organizations",
    "/propositions",
    "/search",
    "/statements",
    "/therapies",
]


@pytest.mark.parametrize("route", LIST_ROUTES)
def test_list_route_returns_200(client, route):
    response = client.get(route)
    assert response.status_code == 200


def test_gene_detail_route_returns_200_with_content(client):
    response = client.get("/genes/gene:hgnc:1097")
    assert response.status_code == 200
    assert b"BRAF" in response.data
    assert b"ERROR" not in response.data


def test_fusion_biomarker_detail_route_handles_unspecified_partner(client):
    response = client.get("/biomarkers/bmkr:8")
    assert response.status_code == 200
    assert b"ALK" in response.data


def test_uncached_biomarker_detail_route_returns_200(client):
    # bmkr:124 is not associated with any statement from the ie instance's organizations
    response = client.get("/biomarkers/bmkr:124")
    assert response.status_code == 200
    assert b"biomarker_id=bmkr:124" in response.data


def test_gene_detail_route_by_legacy_symbol_redirects_to_id(client):
    response = client.get("/genes/BRAF")
    assert response.status_code == 301
    assert response.headers["Location"].endswith("/genes/gene:hgnc:1097")


def test_organization_detail_route_uses_agent_id(client):
    response = client.get("/organizations/agent:org:fda")
    assert response.status_code == 200
    assert b"Food and Drug Administration" in response.data


def test_organization_detail_route_redirects_legacy_short_name(client):
    response = client.get("/organizations/FDA")
    assert response.status_code == 301
    assert response.headers["Location"].endswith("/organizations/agent:org:fda")


def test_unknown_organization_returns_404(client):
    response = client.get("/organizations/not-an-org")
    assert response.status_code == 404


def test_contributors_list_route_lists_user_contributors(client):
    response = client.get("/contributors")
    assert response.status_code == 200
    assert b'href="/contributors/agent:user:vanallenlab"' in response.data
    contributors_table = response.data.split(b'id="contributions-table-result"')[0]
    assert b"/contributors/agent:org:" not in contributors_table


def test_contributors_list_route_lists_contributions_from_all_contributors(client):
    response = client.get("/contributors")
    text = response.data.decode()
    assert 'id="contributions-table-result"' in text
    assert 'href="/contributors/agent:org:fda"' in text
    assert 'href="/contributors/agent:user:vanallenlab"' in text.split('id="contributions-table-result"')[1]


def test_organizations_list_route_lists_only_site_organization_contributions(client):
    response = client.get("/organizations")
    assert response.status_code == 200
    table = response.data.decode().split('id="contributions-table-result"')[1]
    assert 'href="/contributors/agent:org:' in table
    assert 'href="/contributors/agent:user:' not in table


def test_contributor_detail_route_lists_contributed_records(client):
    response = client.get("/contributors/agent:user:vanallenlab")
    assert response.status_code == 200
    assert b"Van Allen lab" in response.data
    assert b'href="/indications/ind:' in response.data
    assert b'href="/statements/stmt:' in response.data


def test_contributor_detail_route_groups_records_with_the_same_text(client):
    # The 28 statements derived from stmt:fda:lynparza:6 share one description, so they share one row.
    response = client.get("/contributors/agent:user:vanallenlab")
    text = response.data.decode()
    assert text.count('href="/statements/stmt:fda:lynparza:6:0"') == 1
    assert "28 statements:" in text
    assert 'href="/statements/stmt:fda:lynparza:6:27"' in text


def test_contributor_detail_route_redirects_organizations(client):
    response = client.get("/contributors/agent:org:fda")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/organizations/agent:org:fda")


def test_unknown_contributor_returns_404(client):
    response = client.get("/contributors/not-a-contributor")
    assert response.status_code == 404


def test_indication_detail_route_lists_contributions_newest_first(client):
    response = client.get("/indications/ind:fda:verzenio:0")
    assert response.status_code == 200
    text = response.data.decode()
    assert 'id="contributions-table-result"' in text
    assert text.index("2025-04-10") < text.index("2024-10-30") < text.index("2023-03-03")
    assert 'href="/contributors/agent:org:fda"' in text


def test_statement_detail_route_lists_contributions(client):
    response = client.get("/statements/stmt:ema:jemperli:0:0")
    assert response.status_code == 200
    assert b'id="contributions-table-result"' in response.data
    assert b'href="/contributors/agent:user:vanallenlab"' in response.data


def test_proposition_lists_absent_biomarkers_after_present(client):
    response = client.get("/propositions/prop:vtxr:46")
    assert response.status_code == 200
    text = response.data.decode()
    present = text.index(">CD19 +</a>")
    absent = text.index('not <a href="/biomarkers/bmkr:12">BCR::ABL1</a>')
    assert present < absent


def test_withdrawn_indication_detail_route_returns_200(client):
    response = client.get("/indications/ind:ema:gavreto:0")
    assert response.status_code == 200
    assert b"Withdrawn" in response.data


def test_deprecated_document_detail_route_returns_200(client):
    response = client.get("/documents/doc:ema:gavreto")
    assert response.status_code == 200
    assert b'<span class="badge text-bg-secondary">Deprecated</span>' in response.data


def test_deprecated_statement_detail_route_returns_200(client):
    response = client.get("/statements/stmt:ema:gavreto:0:0")
    assert response.status_code == 200
    assert b">Deprecated</span>" in response.data


def test_superseded_statement_detail_route_returns_200(client):
    response = client.get("/statements/stmt:ema:jemperli:0:0")
    assert response.status_code == 200
    assert b">Superseded</span>" in response.data


def test_active_document_detail_route_has_no_status_badge(client):
    response = client.get("/documents/doc:fda:verzenio")
    assert response.status_code == 200
    assert b">Active</span>" not in response.data


def test_indications_list_route_excludes_inactive(client):
    response = client.get("/indications")
    assert response.status_code == 200
    assert b"ind:ema:gavreto:0" not in response.data


def test_unknown_gene_returns_404(client):
    response = client.get("/genes/NOTAGENE")
    assert response.status_code == 404
    assert b"404" in response.data


def test_unknown_path_returns_404(client):
    response = client.get("/does-not-exist")
    assert response.status_code == 404


def test_api_down_returns_503(client, monkeypatch):
    from app.blueprints.main import requests as browser_requests

    def _raise(cls, path, params=None):
        raise browser_requests.APIError("API unreachable")

    monkeypatch.setattr(browser_requests.API, "get", classmethod(_raise))
    response = client.get("/genes/gene:hgnc:1097")
    assert response.status_code == 503
    assert b"unavailable" in response.data.lower()


def test_disease_detail_route_by_id_returns_200(client):
    response = client.get("/diseases/dis:oncotree:PRAD")
    assert response.status_code == 200
    assert b"Prostate Adenocarcinoma" in response.data


def test_disease_detail_route_by_legacy_name_redirects_to_id(client):
    response = client.get("/diseases/Prostate%20Adenocarcinoma")
    assert response.status_code == 301
    assert response.headers["Location"].endswith("/diseases/dis:oncotree:PRAD")


def test_disease_detail_route_by_legacy_name_with_slash_redirects(client):
    response = client.get("/diseases/Myeloid/Lymphoid%20Neoplasms")
    assert response.status_code == 301
    assert "/diseases/dis:" in response.headers["Location"]


def test_disease_detail_route_unknown_returns_404(client):
    response = client.get("/diseases/not-a-disease")
    assert response.status_code == 404


def test_therapy_detail_route_by_id_returns_200(client):
    response = client.get("/therapies/tx:ncit:C1005")
    assert response.status_code == 200
    assert b"Arsenic trioxide" in response.data


def test_therapy_detail_route_by_legacy_name_redirects_to_id(client):
    response = client.get("/therapies/Arsenic%20trioxide")
    assert response.status_code == 301
    assert response.headers["Location"].endswith("/therapies/tx:ncit:C1005")


def test_therapy_detail_route_unknown_returns_404(client):
    response = client.get("/therapies/not-a-therapy")
    assert response.status_code == 404


def test_statements_list_route_reads_from_cache(client, monkeypatch):
    from app.blueprints.main import requests as browser_requests

    def _raise(cls, path, params=None):
        raise browser_requests.APIError("API unreachable")

    monkeypatch.setattr(browser_requests.API, "get", classmethod(_raise))
    response = client.get("/statements")
    assert response.status_code == 200
    assert b"/statements/stmt:" in response.data


def test_index_route_has_term_search(client):
    response = client.get("/")
    assert b'id="term-search"' in response.data
    assert b'id="term-search-data"' in response.data


def test_search_route_without_query_shows_search_box(client):
    response = client.get("/search")
    assert response.status_code == 200
    assert b'id="term-search"' in response.data
    assert b'id="search-table-result"' not in response.data
    assert b"No results" not in response.data


def test_search_route_lists_exact_name_first(client):
    response = client.get("/search?q=egfr")
    assert response.status_code == 200
    assert b"/genes/gene:hgnc:3236" in response.data
    assert b"/biomarkers/bmkr:" in response.data


def test_search_route_single_match_redirects_to_record(client):
    response = client.get("/search?q=gene:hgnc:3236")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/genes/gene:hgnc:3236")


def test_search_route_lists_multiple_matches(client):
    response = client.get("/search?q=BRCA")
    assert response.status_code == 200
    assert b'id="search-table-result"' in response.data
    assert b'<option value="Biomarker">Biomarkers</option>' in response.data
    assert b"/biomarkers/bmkr:" in response.data
    # The search box on the results page keeps the query and offers suggestions.
    assert b'value="BRCA"' in response.data
    assert b'id="term-search-data"' in response.data
    # The browse links follow the results table.
    assert response.data.index(b"Or browse all") > response.data.index(b'id="search-table-result"')


def test_search_route_finds_organizations(client):
    response = client.get("/search?q=Food and Drug Administration")
    assert response.status_code == 200
    assert b"/organizations/agent:org:fda" in response.data


def test_search_route_matches_indication_descriptions(client):
    response = client.get("/search?q=kinase inhibitor")
    assert response.status_code == 200
    # Indications link from both the ID and the "Name or description" columns.
    assert response.data.count(b'href="/indications/ind:') >= 2 * response.data.count(b"<td>Indication</td>") > 0


def test_search_route_with_no_matches(client):
    response = client.get("/search?q=zzzzzz")
    assert response.status_code == 200
    assert b"No results" in response.data
    assert b"Or browse all" in response.data


def test_propositions_route_defaults_to_site_organizations(client):
    response = client.get("/propositions")
    assert response.status_code == 200
    assert b"Show all propositions" in response.data
    assert b'class="form-check-input org-toggle"' in response.data


def test_propositions_route_scope_all_includes_propositions_without_statements(client):
    site = client.get("/propositions")
    everything = client.get("/propositions?scope=all")
    assert everything.status_code == 200
    assert b"Show only this site" in everything.data
    assert everything.data.count(b"/propositions/prop:") > site.data.count(b"/propositions/prop:")


def test_index_statements_link_points_to_statements(client):
    response = client.get("/")
    assert b'href="/statements">' in response.data
