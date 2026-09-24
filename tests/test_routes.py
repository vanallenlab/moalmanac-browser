"""
test_routes.py

End-to-end route tests against a locally running moalmanac-api (http://localhost:8080) and the active
instance's sqlite cache (data/cache.sqlite3, set by switch_instance.sh). These are integration tests, not
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
