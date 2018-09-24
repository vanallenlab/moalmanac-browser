from flask import Flask
from flask_bootstrap import Bootstrap

from db import db
from .modules.api import api
from .modules.editor import editor
from .modules.portal import portal


def create_app(name=__name__):
    app = Flask(name)
    app.config.from_object('config')

    Bootstrap(app)
    app.register_blueprint(api, url_prefix='/api')
    # app.register_blueprint(editor, url_prefix='/editor')
    app.register_blueprint(portal)

    db.init_app(app)

    return app

