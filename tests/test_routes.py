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
    response = client.get("/genes/BRAF")
    assert response.status_code == 200
    assert b"BRAF" in response.data
    assert b"ERROR" not in response.data


def test_fusion_biomarker_detail_route_handles_unspecified_partner(client):
    response = client.get("/biomarkers/bmkr:8")
    assert response.status_code == 200
    assert b"ALK" in response.data


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
    response = client.get("/genes/BRAF")
    assert response.status_code == 503
    assert b"unavailable" in response.data.lower()
