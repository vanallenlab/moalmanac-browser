"""
handlers.py

Functions for serializing SQLAlchemy model instances into JSON-serializable dictionaries.
"""

import datetime
import sqlalchemy
import typing

from app import models

class BaseHandler:
    """
    A base class for handling SQL queries. This class provides common functionality for managing SQL queries and serves
    as a template for specific Handler classes, which inherit from BaseHandler and implement route-specific logic.
    """
    def __init__(self):
        """
        Initializes the BaseHandler class.
        """
        pass

    @staticmethod
    def construct_base_query(model: models.Base) -> sqlalchemy.Select:
        """
        Constructs a base SQLAlchemy select statement from the primary table model.

        Args:
            model (models.Base): The SQLAlchemy model class representing the table.

        Returns:
            Select: A SQLAlchemy select statement for the provided `model`.
        """
        return sqlalchemy.select(model)

    @staticmethod
    def convert_date_to_iso(value: datetime.date) -> str:
        """
        Converts a datetime.date value to an ISO 8601 format string.

        Args:
            value (datetime.date): The datetime.date value to convert.

        Returns:
            str: The ISO 8601 format string if the value is a date, otherwise the original value.
        """
        if isinstance(value, datetime.date):
            return value.isoformat()
        else:
            raise ValueError(f"Input value not of type datetime.date: {value}")


    @staticmethod
    def execute_query(session: sqlalchemy.orm.Session, statement: sqlalchemy.sql.Executable) -> list[models.Base]:
        """
        Executes the given SQLAlchemy statement and returns the results as a list of SQLAlchemy model instances.

        Args:
            session (sqlalchemy.orm.Session): A session instance.
            statement (sqlalchemy.sql.Executable): The SQLAlchemy statement to execute.

        Returns:
            list[model.Base]: A list of SQLAlchemy model instances returned by the query.
        """
        return (
            session
            .execute(statement=statement)
            .unique()
            .scalars()
            .all()
        )

    @classmethod
    def serialize_instances(cls, instances: list[models.Base], **kwargs) -> list[dict[str, typing.Any]]:
        """
        Serializes the fields populated by relationships with other tables, defined by this table's model
        and the applied joinedload operation.

        This is Step 6 of managing the query.

        Args:
            instances (list[models.Base]): A list of SQLAlchemy model instances to serialize.

        Returns:
            list[dict[str, typing.Any]]: A list of dictionaries with all keys serialized.
        """
        result = []
        for instance in instances:
            serialized_instance = cls.serialize_single_instance(instance=instance, **kwargs)
            result.append(serialized_instance)
        return result

    @classmethod
    def serialize_primary_instance(cls, instance: models.Base) -> dict[str, typing.Any]:
        """
        Serializes the fields of the primary table's records.

        Args:
            instance (models.Base): A SQLAlchemy model instance to serialize.

        Returns:
            dict[str, typing.Any]: A dictionary representation of the Row object.
        """
        return {column.name: getattr(instance, column.name) for column in instance.__table__.columns}

    @classmethod
    def serialize_secondary_instances(cls, instance: models.Base, record: dict[str, typing.Any], **kwargs) -> dict[str, typing.Any]:
        """
        References `serialize_instance` functions from relevant classes for each secondary table that is referenced
        within the instance. This function should be implemented by each route's Handler class.

        Args:
            instance (models.Base): A SQLAlchemy model instance to serialize.
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.

        Returns:
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.

        Raises:
            NotImplementedError: If the route's Handler class does not implement this method.
        """
        raise NotImplementedError("Subclasses should implement this method.")

    @classmethod
    def serialize_single_instance(cls, instance: models.Documents) -> dict[str, typing.Any]:
        """
        Serializes a single instance of the Documents table.

        This method extends the base class implementation by serializing the instance and any related tables. The key
        `id` is removed after serialization.

        Args:
            instance (models.Documents): A SQLAlchemy model instance to serialize.

        Returns:
            dict[str, typing.Any]: A list of dictionaries with all keys serialized.
        """
        serialized_record = cls.serialize_primary_instance(instance=instance)
        return serialized_record



class About(BaseHandler):
    """
    Handler class to manage queries against the About table.
    """


class Biomarkers(BaseHandler):
    """
    Handler class to manage queries against the Biomarker table.
    """


class Diseases(BaseHandler):
    """
    Handler class to manage queries against the Disease table.
    """


class Documents(BaseHandler):
    """
    Handler class to manage queries against the About table.
    """


class Genes(BaseHandler):
    """
    Handler class to manage queries against the Genes table.
    """


class Terms(BaseHandler):
    """
    Handler class to manage queries against the About table.
    """


class Therapies(BaseHandler):
    """
    Handler class to manage queries against the Therapies table.
    """
