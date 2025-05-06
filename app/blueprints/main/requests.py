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
    @classmethod
    def get(cls, request):
        response = requests.get(request)
        return ""

class Local:
    """
    Class for making requests against the local database.
    """
    @classmethod
    def get(cls):
        return ""

    @classmethod
    def get_about(cls):
        handler = handlers.About()
        statement = handler.construct_base_query(model=models.About)
        session_factory = flask.current_app.config['SESSION_FACTORY']
        with session_factory() as session:
            result = handler.execute_query(session=session, statement=statement)
            serialized = handler.serialize_instances(instances=result)
            serialized = serialized[0]
        return serialized
