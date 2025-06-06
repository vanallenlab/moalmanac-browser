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


def init_db(file: str) -> tuple[Engine, sessionmaker]:
    """
    Initializes the sqlite database connection and session.

    This function reads the SQLite3 database from the data/ folder in root.

    Args:
        file (str): A sqlite3 filename within the data/ folder.

    Returns:
        tuple[sqlalchemy.orm.engine, sqlalchemy.orm.Session]: A tuple containing the SQLAlchemy engine
            and configured session.

    Raises:
        FileNotFoundError: If the specified configuration file does not exist.
        KeyError: If the database path is not found within the configuration file.
    """
    path = os.path.join("data", file)
    path = os.path.abspath(path)
    if file == "cache.sqlite3":
        if not os.path.exists(path):
            raise FileNotFoundError(f"SQLite database file not found: {path}")

    engine = sqlalchemy.create_engine(f"sqlite:///{path}")
    session_factory = sessionmaker(bind=engine)
    return engine, session_factory
