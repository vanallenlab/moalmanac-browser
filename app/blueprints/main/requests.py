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

class API:
    """
    Class for making requests against Molecular Oncology Almanac API service.
    """
    @staticmethod
    def get_api_url():
        return flask.current_app.config['API_URL']

    @classmethod
    def get(cls, request):
        root = cls.get_api_url()
        request = f"{root}/{request}"
        response = requests.get(request)
        return response

    @classmethod
    def get_gene(cls, name: str = None):
        if name:
            response = cls.get(request=f"genes/{name}")
            if response.status_code == 200:
                data = response.json()['data']
                return data[0]
            else:
                return response.json()
        else:
            # return genes with "gene symbol not found message"
            return ""

    @classmethod
    def get_config_organization_filters(cls):
        config = flask.current_app.config['INI_CONFIG']
        agencies = config['agencies']
        print(agencies)
        return ''

    @classmethod
    def get_propositions(cls):
        response = cls.get(request="propositions")
        if response.status_code == 200:
            data = response.json()['data']
            return data
        else:
            return response.json()

    @classmethod
    def get_statements(cls):
        organization_filters = cls.get_config_organization_filters()
        response = cls.get(request="statements")
        if response.status_code == 200:
            data = response.json()['data']
            return data
        else:
            return response.json()

    @classmethod
    def get_therapy(cls, name: str = None):
        if name:
            response = cls.get(request=f"therapies/{name}")
            if response.status_code == 200:
                data = response.json()['data']
                return data[0]
            else:
                return response.json()
        else:
            # return genes with "gene symbol not found message"
            return ""


class Local:
    """
    Class for making requests against the local database.
    """
    @classmethod
    def get(cls, handler, statement):
        session_factory = flask.current_app.config['SESSION_FACTORY']
        with session_factory() as session:
            result = handler.execute_query(session=session, statement=statement)
            serialized = handler.serialize_instances(instances=result)
            serialized = serialized
        return serialized

    @classmethod
    def get_about(cls):
        handler = handlers.About()
        statement = handler.construct_base_query(model=models.About)
        return cls.get(handler=handler, statement=statement)[0]

    @classmethod
    def get_biomarkers(cls):
        handler = handlers.Biomarkers()
        statement = handler.construct_base_query(model=models.Biomarkers)
        results = cls.get(handler=handler, statement=statement)
        return cls.sort(data=results, sort_key='name')

    @classmethod
    def get_diseases(cls):
        handler = handlers.Diseases()
        statement = handler.construct_base_query(model=models.Diseases)
        results = cls.get(handler=handler, statement=statement)
        return cls.sort(data=results, sort_key='name')

    @classmethod
    def get_documents(cls):
        handler = handlers.Documents()
        statement = handler.construct_base_query(model=models.Documents)
        results = cls.get(handler=handler, statement=statement)
        return cls.sort(data=results, sort_key='name')

    @classmethod
    def get_genes(cls):
        handler = handlers.Genes()
        statement = handler.construct_base_query(model=models.Genes)
        results = cls.get(handler=handler, statement=statement)
        return cls.sort(data=results, sort_key='name')

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
        return cls.sort(data=results, sort_key='name')

    @classmethod
    def sort(cls, data, sort_key='name', reverse=False):
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
            raise KeyError(f"Missing key '{sort_key}' in one or more dictionaries.") from e
