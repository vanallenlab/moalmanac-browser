import configparser
import os
import sqlalchemy
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker


class CaseSensitiveConfigParser(configparser.ConfigParser):
    """Overrides a base class of configparser.ConfigParser to preserve case sensitivity."""
    def optionxform(self, optionstr):
        return optionstr


def read_config_ini(path: str) -> configparser.ConfigParser():
    """
    Reads a configuration file in INI format.

    Args:
        path (str): The path to the database configuration file.

    Returns:
        config (configparser.ConfigParser()): A ConfigParser object containing the configuration data.

    Raises:
        FileNotFoundError: If the specified configuration file does not exist.
    """
    config = CaseSensitiveConfigParser()

    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found at {path}")

    config.read(path)
    return config


def init_db(
        file: str, 
        must_exist: bool = True,
    ) -> tuple[Engine, sessionmaker]:
    """
    Initializes the sqlite database connection and session.

    This function reads the SQLite3 database from the data/ folder in root.

    Args:
        file (str): A sqlite3 filename within the data/ folder.
        must_exist (bool): Raise an error if the file does not exist. Set to False when populating a new cache.

    Returns:
        tuple[sqlalchemy.orm.engine, sqlalchemy.orm.Session]: A tuple containing the SQLAlchemy engine
            and configured session.

    Raises:
        FileNotFoundError: If must_exist is True and the sqlite3 file does not exist.
    """
    path = os.path.join("data", file)
    path = os.path.abspath(path)
    if must_exist and not os.path.exists(path):
        raise FileNotFoundError(f"SQLite database file not found: {path}")

    engine = sqlalchemy.create_engine(f"sqlite:///{path}")
    session_factory = sessionmaker(bind=engine)
    return engine, session_factory
