"""
requests.py

Defines unified interfaces for retrieving data from two sources:

1. The external Molecular Oncology Almanac API service (via the `API` class).
2. The local SQLite database cache (via the `Local` class).

- The `API` class manages outbound HTTP requests to the live MOAlmanac API.
- The `Local` class manages queries to the locally cached database using SQLAlchemy handlers.

Each class provides helper methods for retrieving and processing relevant resources such as genes, therapies, propositions, and documents.
"""

import flask
import requests

from . import handlers
from app import models


class APIError(Exception):
    """
    Raised when the Molecular Oncology Almanac API cannot be reached, or responds with a non-200 status code.
    """

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class API:
    """
    Class for making requests against Molecular Oncology Almanac API service.
    """

    TIMEOUT_SECONDS = 10

    @staticmethod
    def get_api_url():
        return flask.current_app.config["API_URL"]

    @classmethod
    def get(cls, path: str, params: list[tuple] | None = None):
        """
        Issues a GET request against the API and returns the `data` payload of the response.

        Args:
            path (str): The API path to request, e.g. "biomarkers".
            params (list[tuple] | None): A list of (key, value) query parameter tuples. Repeated keys
                (e.g. multiple `agent_id` values) are supported.

        Returns:
            list | dict: The `data` field of the API's JSON response.

        Raises:
            APIError: If the API cannot be reached, or responds with a status code other than 200.
        """
        root = cls.get_api_url()
        url = f"{root}/{path}"
        try:
            response = requests.get(url, params=params, timeout=cls.TIMEOUT_SECONDS)
        except requests.RequestException as error:
            raise APIError(
                f"Could not reach the Molecular Oncology Almanac API at {root}."
            ) from error
        if response.status_code != 200:
            raise APIError(
                f"The Molecular Oncology Almanac API returned an error for {url}.",
                status_code=response.status_code,
            )
        return response.json()["data"]

    @classmethod
    def get_config_organization_filters(cls):
        """
        Builds the `agent_id` query parameters for the organizations enabled in this instance's config.ini.

        Returns:
            list[tuple]: A list of ("agent_id", "agent:org:<agency>") tuples.
        """
        config = flask.current_app.config["INI_CONFIG"]
        enabled_agencies = [
            agency
            for agency, enabled in config["agencies"].items()
            if enabled.lower() == "true"
        ]
        return [
            ("agent_id", f"agent:org:{agency.lower()}") for agency in enabled_agencies
        ]

    @classmethod
    def _get_list(
        cls,
        path: str,
        config_organization_filter: bool = False,
        filters: list[tuple] | None = None,
    ):
        params = []
        if config_organization_filter:
            params.extend(cls.get_config_organization_filters())
        if filters:
            params.extend(filters)
        return cls.get(path=path, params=params or None)

    @classmethod
    def _get_one(cls, path: str, params: list[tuple]):
        data = cls.get(path=path, params=params)
        if not data:
            flask.abort(404)
        return data[0]

    @classmethod
    def get_biomarker(cls, biomarker_name: str | None = None):
        if not biomarker_name:
            flask.abort(404)
        return cls._get_one(
            path="biomarkers", params=[("biomarker_name", biomarker_name)]
        )

    @classmethod
    def get_biomarkers(
        cls, config_organization_filter: bool = False, filters: list[tuple] | None = None
    ):
        return cls._get_list(
            path="biomarkers",
            config_organization_filter=config_organization_filter,
            filters=filters,
        )

    @classmethod
    def get_disease(cls, name: str | None = None):
        if not name:
            flask.abort(404)
        return cls._get_one(path="diseases", params=[("disease_name", name)])

    @classmethod
    def get_document(cls, document_id: str | None = None):
        if not document_id:
            flask.abort(404)
        return cls._get_one(path="documents", params=[("document_id", document_id)])

    @classmethod
    def get_documents(
        cls, config_organization_filter: bool = False, filters: list[tuple] | None = None
    ):
        return cls._get_list(
            path="documents",
            config_organization_filter=config_organization_filter,
            filters=filters,
        )

    @classmethod
    def get_gene(cls, name: str | None = None):
        if not name:
            flask.abort(404)
        return cls._get_one(path="genes", params=[("gene_name", name)])

    @classmethod
    def get_indication(cls, indication_id: str | None = None):
        if not indication_id:
            flask.abort(404)
        return cls._get_one(
            path="indications", params=[("indication_id", indication_id)]
        )

    @classmethod
    def get_indications(
        cls, config_organization_filter: bool = False, filters: list[tuple] | None = None
    ):
        return cls._get_list(
            path="indications",
            config_organization_filter=config_organization_filter,
            filters=filters,
        )

    @classmethod
    def get_organization(cls, organization_id: str | None = None):
        if not organization_id:
            flask.abort(404)
        return cls._get_one(path="agents", params=[("agent_id", organization_id)])

    @classmethod
    def get_proposition(cls, proposition_id: str | None = None):
        if not proposition_id:
            flask.abort(404)
        return cls._get_one(
            path="propositions", params=[("proposition_id", proposition_id)]
        )

    @classmethod
    def get_propositions(cls):
        return cls.get(path="propositions")

    @classmethod
    def get_search_results(
        cls, config_organization_filter: bool = False, filters: list[tuple] | None = None
    ):
        return cls._get_list(
            path="search",
            config_organization_filter=config_organization_filter,
            filters=filters,
        )

    @classmethod
    def get_statement(cls, statement_id: str | None = None):
        if not statement_id:
            flask.abort(404)
        return cls._get_one(
            path="statements", params=[("statement_id", statement_id)]
        )

    @classmethod
    def get_statements(
        cls, config_organization_filter: bool = False, filters: list[tuple] | None = None
    ):
        return cls._get_list(
            path="statements",
            config_organization_filter=config_organization_filter,
            filters=filters,
        )

    @classmethod
    def get_therapy(cls, name: str | None = None):
        if not name:
            flask.abort(404)
        return cls._get_one(path="therapies", params=[("therapy_name", name)])


class Local:
    """
    Class for making requests against the local database.
    """

    @classmethod
    def get(cls, handler, statement):
        session_factory = flask.current_app.config["SESSION_FACTORY"]
        with session_factory() as session:
            result = handler.execute_query(session=session, statement=statement)
            serialized = handler.serialize_instances(instances=result)
            serialized = serialized
        return serialized

    @classmethod
    def get_about(cls):
        handler = handlers.About()
        statement = handler.construct_base_query(model=models.About)
        results = cls.get(handler=handler, statement=statement)
        if not results:
            flask.abort(404)
        return results[0]

    @classmethod
    def get_biomarker(cls, biomarker_id: str):
        for record in cls.get_biomarkers():
            if record.get("id") == biomarker_id:
                return record
        return None

    @classmethod
    def get_biomarkers(cls):
        handler = handlers.Biomarkers()
        statement = handler.construct_base_query(model=models.Biomarkers)
        results = cls.get(handler=handler, statement=statement)
        return cls.sort(data=results, sort_key="name")

    @classmethod
    def get_diseases(cls):
        handler = handlers.Diseases()
        statement = handler.construct_base_query(model=models.Diseases)
        results = cls.get(handler=handler, statement=statement)
        return cls.sort(data=results, sort_key="name")

    @classmethod
    def get_documents(cls):
        handler = handlers.Documents()
        statement = handler.construct_base_query(model=models.Documents)
        results = cls.get(handler=handler, statement=statement)
        return cls.sort(data=results, sort_key="name")

    @classmethod
    def get_genes(cls):
        handler = handlers.Genes()
        statement = handler.construct_base_query(model=models.Genes)
        results = cls.get(handler=handler, statement=statement)
        return cls.sort(data=results, sort_key="name")

    @classmethod
    def get_indications(cls):
        handler = handlers.Indications()
        statement = handler.construct_base_query(model=models.Indications)
        results = cls.get(handler=handler, statement=statement)
        return cls.sort(data=results, sort_key="id")

    @classmethod
    def get_organizations(cls):
        handler = handlers.Agents()
        statement = handler.construct_base_query(model=models.Agents)
        results = cls.get(handler=handler, statement=statement)
        return cls.sort(data=results, sort_key="name")

    @classmethod
    def get_terms(cls):
        handler = handlers.Terms()
        statement = handler.construct_base_query(model=models.Terms)
        return cls.get(handler=handler, statement=statement)

    @classmethod
    def get_therapies(cls):
        handler = handlers.Therapies()
        statement = handler.construct_base_query(model=models.Therapies)
        results = cls.get(handler=handler, statement=statement)
        return cls.sort(data=results, sort_key="name")

    @classmethod
    def sort(cls, data, sort_key="name", reverse=False):
        """
        Sort a list of dictionaries by the value associated with sort_key.

        Parameters:
            data (list of dict): List of dictionaries to sort.
            sort_key (str): The key to sort the dictionaries by.
            reverse (bool): If True, sort in descending order. Default is ascending.

        Returns:
            list of dict: The sorted list of dictionaries.

        Raises:
            KeyError: If any dictionary in the list lacks the sort_key.
        """
        try:
            return sorted(data, key=lambda d: d[sort_key], reverse=reverse)
        except KeyError as e:
            raise KeyError(
                f"Missing key '{sort_key}' in one or more dictionaries."
            ) from e
