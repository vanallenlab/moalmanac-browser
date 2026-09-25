"""
conftest.py

Shared pytest fixtures for the moalmanac-browser test suite.
"""

import json
import os

import pytest

from app import create_app

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def load_fixture(name: str):
    """
    Loads a JSON fixture file from tests/fixtures/.

    Args:
        name (str): The fixture filename, e.g. "statement.json".

    Returns:
        dict: The parsed JSON content.
    """
    with open(os.path.join(FIXTURES_DIR, name)) as f:
        return json.load(f)


@pytest.fixture
def app():
    """
    Builds a Flask app for the instance given by the APP_CONFIG environment variable (default:
    deploy/default/config.ini), using that instance's sqlite cache, pointed at the API running at
    http://localhost:8080.
    """
    repo_dir = os.path.dirname(os.path.dirname(__file__))
    config_path = os.path.join(repo_dir, os.environ.get("APP_CONFIG", "deploy/default/config.ini"))
    application = create_app(
        config_path=config_path, api="http://localhost:8080"
    )
    application.config["TESTING"] = True
    return application


@pytest.fixture
def client(app):
    return app.test_client()
