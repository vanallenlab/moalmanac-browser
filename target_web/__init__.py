import config
from flask import Flask
from flask_bootstrap import Bootstrap
from modules.api import api
from modules.editor import editor
from modules.portal import portal

def create_app(config_file=None):
	if config_file is None:
		config_file = 'config'

	app = Flask(__name__)
	app.config.from_object(config_file)

	Bootstrap(app)
	app.register_blueprint(portal)
	app.register_blueprint(api, url_prefix='/api/v0')
	app.register_blueprint(editor, url_prefix='/editor')

	return app
