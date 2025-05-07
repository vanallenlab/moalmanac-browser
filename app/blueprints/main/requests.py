import flask
import requests
import sqlalchemy

from . import main_bp
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
        return cls.get(handler=handler, statement=statement)

    @classmethod
    def get_diseases(cls):
        handler = handlers.Diseases()
        statement = handler.construct_base_query(model=models.Diseases)
        return cls.get(handler=handler, statement=statement)

    @classmethod
    def get_documents(cls):
        handler = handlers.Documents()
        statement = handler.construct_base_query(model=models.Documents)
        return cls.get(handler=handler, statement=statement)

    @classmethod
    def get_genes(cls):
        handler = handlers.Genes()
        statement = handler.construct_base_query(model=models.Genes)
        return cls.get(handler=handler, statement=statement)

    @classmethod
    def get_terms(cls):
        handler = handlers.Terms()
        statement = handler.construct_base_query(model=models.Terms)
        return cls.get(handler=handler, statement=statement)

    @classmethod
    def get_therapies(cls):
        handler = handlers.Therapies()
        statement = handler.construct_base_query(model=models.Therapies)
        return cls.get(handler=handler, statement=statement)
