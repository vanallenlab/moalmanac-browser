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
        print(request)
        response = requests.get(request)
        return response

    @classmethod
    def get_biomarker(cls, biomarker_name: str = None):
        if biomarker_name:
            response = cls.get(request=f"biomarkers/{biomarker_name}")
            if response.status_code == 200:
                data = response.json()['data']
                return data[0]
            else:
                return response.json()
        else:
            # return biomarker with "biomarker name not found message"
            return ""

    @classmethod
    def get_biomarkers(cls, config_organization_filter: bool = False, filters: str = None):
        request = "biomarkers"
        filters_to_apply = []
        if config_organization_filter:
            organization_filters = cls.get_config_organization_filters()
            filters_to_apply.append(organization_filters)
        if filters:
            filters_to_apply.append(filters)
        if filters_to_apply:
            request = f"{request}?{'&'.join(filters_to_apply)}"
        response = cls.get(request=request)
        if response.status_code == 200:
            data = response.json()['data']
            return data
        else:
            return response.json()

    @classmethod
    def get_config_organization_filters(cls):
        config = flask.current_app.config['INI_CONFIG']
        enabled_agencies = [agency for agency, enabled in config['agencies'].items() if enabled.lower() == 'true']
        agency_statements = [f"organization={agency.lower()}" for agency in enabled_agencies]
        string = '&'.join(agency_statements)
        return string.replace(' ', '%20')

    @classmethod
    def get_disease(cls, name: str = None):
        if name:
            response = cls.get(request=f"diseases/{name}")
            if response.status_code == 200:
                data = response.json()['data']
                return data[0]
            else:
                return response.json()
        else:
            # return disease with "disease name not found message"
            return ""

    @classmethod
    def get_document(cls, document_id: str):
        if document_id:
            response = cls.get(request=f"documents/{document_id}")
            if response.status_code == 200:
                data = response.json()['data']
                return data[0]
            else:
                return response.json()
        else:
            # Return "document id not found" message
            return ""

    @classmethod
    def get_documents(cls, config_organization_filter:bool = False, filters:str = None):
        request = "documents"
        filters_to_apply = []
        if config_organization_filter:
            organization_filters = cls.get_config_organization_filters()
            filters_to_apply.append(organization_filters)
        if filters:
            filters_to_apply.append(filters)
        if filters_to_apply:
            request = f"{request}?{'&'.join(filters_to_apply)}"
        response = cls.get(request=request)
        if response.status_code == 200:
            data = response.json()['data']
            return data
        else:
            return response.json()

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
    def get_indication(cls, indication_id: str):
        response = cls.get(request=f"indications/{indication_id}")
        if response.status_code == 200:
            data = response.json()['data']
            return data[0]
        else:
            return response.json()

    @classmethod
    def get_indications(cls, config_organization_filter:bool = False, filters:str = None):
        request = "indications"
        filters_to_apply = []
        if config_organization_filter:
            organization_filters = cls.get_config_organization_filters()
            filters_to_apply.append(organization_filters)
        if filters:
            filters_to_apply.append(filters)
        if filters_to_apply:
            request = f"{request}?{'&'.join(filters_to_apply)}"
        response = cls.get(request=request)
        if response.status_code == 200:
            data = response.json()['data']
            return data
        else:
            return response.json()

    @classmethod
    def get_organization(cls, organization_id: str):
        response = cls.get(request=f"organizations/{organization_id}")
        if response.status_code == 200:
            data = response.json()['data']
            return data[0]
        else:
            return response.json()

    @classmethod
    def get_propositions(cls):
        response = cls.get(request="propositions")
        if response.status_code == 200:
            data = response.json()['data']
            return data
        else:
            return response.json()

    @classmethod
    def get_statement(cls, statement_id):
        response = cls.get(request=f"statements/{statement_id}")
        if response.status_code == 200:
            data = response.json()['data']
            return data[0]
        else:
            return response.json()

    @classmethod
    def get_statements(cls, config_organization_filter:bool = False, filters:str = None):
        request = "statements"
        filters_to_apply = []
        if config_organization_filter:
            organization_filters = cls.get_config_organization_filters()
            filters_to_apply.append(organization_filters)
        if filters:
            filters_to_apply.append(filters)
        if filters_to_apply:
            request = f"{request}?{'&'.join(filters_to_apply)}"
        response = cls.get(request=request)
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
            # return therapies with "therapy name not found message"
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
    def get_indications(cls):
        handler = handlers.Indications()
        statement = handler.construct_base_query(model=models.Indications)
        results = cls.get(handler=handler, statement=statement)
        return cls.sort(data=results, sort_key='id')

    @classmethod
    def get_organizations(cls):
        handler = handlers.Organizations()
        statement = handler.construct_base_query(model=models.Organizations)
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
