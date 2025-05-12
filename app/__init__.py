import flask
import flask_bootstrap
import os

from . import database
from . import models
from .blueprints import main

def create_app(config_path=os.path.join('config', 'default.ini'), api="https://api.moalmanac.org"):
    app = flask.Flask(__name__)
    app.json.sort_keys = False

    config = database.read_config_ini(path=config_path)
    app.config['INI_CONFIG'] = config
    app.config['API_URL'] = api

    engine, session_factory = database.init_db(config=config)
    models.Base.metadata.create_all(bind=engine)

    app.config['SESSION_FACTORY'] = session_factory

    flask_bootstrap.Bootstrap5(app)
    app.register_blueprint(main.main_bp)

    app.add_url_rule(rule="/", endpoint="index")

    @app.context_processor
    def inject_config_vars():
        css_path = f"css/{config['app'].get('theme', 'default-theme-colors.css')}"
        footer_logos_path = config['app'].get('logos', 'default-footer.html')
        subtitle = config['homepage'].get('subtitle', 'Browser')
        caption = config['homepage'].get('caption', 'An open-source knowledgebase for precision cancer medicine.')
        print(css_path, footer_logos_path, subtitle, caption)
        return dict(
            css_path=css_path,
            footer_logos_path=footer_logos_path,
            subtitle=subtitle,
            caption=caption
        )

    return app
