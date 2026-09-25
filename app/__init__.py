import flask
import flask_bootstrap
import os

from . import database
from . import models
from .blueprints import main
from .blueprints.main import services
from .blueprints.main.requests import APIError

def create_app(
    config_path='deploy/default/config.ini',
    api='http://127.0.0.1:8000',
    api_public: str | None = None,
    populating: bool = False
):
    app = flask.Flask(__name__)
    app.json.sort_keys = False

    config = database.read_config_ini(path=config_path)
    app.config['INI_CONFIG'] = config
    # API_URL is used for server-side requests (the local API instance in production), while API_PUBLIC_URL is
    # rendered into templates as links for users.
    app.config['API_URL'] = api
    app.config['API_PUBLIC_URL'] = api_public or api

    db_filename = config['app']['cache']
    engine, session_factory = database.init_db(file=db_filename, must_exist=not populating)
    models.Base.metadata.create_all(bind=engine)

    app.config['SESSION_FACTORY'] = session_factory

    flask_bootstrap.Bootstrap5(app)
    app.register_blueprint(main.main_bp)

    app.add_url_rule(rule="/", endpoint="index")

    app.jinja_env.filters['api_id'] = services.encode_query_value
    app.jinja_env.filters['short_agent_id'] = services.short_agent_id

    @app.errorhandler(404)
    def handle_not_found(error):
        return flask.render_template("404.html"), 404

    @app.errorhandler(APIError)
    def handle_api_error(error):
        app.logger.error(str(error))
        return flask.render_template(
            "error.html",
            status_code=error.status_code or 503,
            message="The Molecular Oncology Almanac API is currently unavailable. Please try again shortly.",
        ), 503

    @app.errorhandler(500)
    def handle_server_error(error):
        return flask.render_template(
            "error.html",
            status_code=500,
            message="Something went wrong while loading this page.",
        ), 500

    @app.context_processor
    def inject_config_vars():
        css_path = f"css/{config['app'].get('theme', 'default-theme-colors.css')}"
        footer_logos_path = config['app'].get('logos', 'default-footer.html')
        subtitle = config['homepage'].get('subtitle', 'Browser')
        caption = config['homepage'].get('caption', 'An open-source knowledgebase for precision cancer medicine.')
        api_url = app.config['API_PUBLIC_URL']
        url = app.config['INI_CONFIG']['app'].get('url', 'moalmanac.org')
        about_template = app.config['INI_CONFIG']['about'].get('template', None)
        return dict(
            css_path=css_path,
            footer_logos_path=footer_logos_path,
            subtitle=subtitle,
            caption=caption,
            api_url=api_url,
            url=url,
            about_template=about_template
        )

    return app
