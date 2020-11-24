from flask import Flask
from flask_bootstrap import Bootstrap
from flask_cors import CORS

from db import db, ma
from auth import basic_auth

from .modules.api import api
from .modules.editor import editor
from .modules.portal import portal

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlite3 import Connection


@event.listens_for(Engine, 'connect')
def _set_sqlite_pragma(dbapi_connection, connection_record):
    """By default, SQLite does not support foreign keys unless manually enabled."""

    if isinstance(dbapi_connection, Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute('PRAGMA foreign_keys=ON;')
        cursor.close()


def create_app(name=__name__):
    app = Flask(name)
    app.config.from_object('config')

    Bootstrap(app)
    app.register_blueprint(api, url_prefix='/api')
    # app.register_blueprint(editor, url_prefix='/editor')
    app.register_blueprint(portal)

    db.init_app(app)
    ma.init_app(app)  # must initialize after SQLAlchemy

    CORS(app)

    basic_auth.init_app(app)

    return app
