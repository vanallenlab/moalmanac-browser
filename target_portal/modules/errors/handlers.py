from flask import jsonify, request, url_for
from target_portal.modules.errors import errors
from target_portal.modules.api.errors import error_response as api_error_response
from db import db


def wants_json_response():
    return request.accept_mimetypes['application/json'] >= \
        request.accept_mimetypes['text/html']


@errors.app_errorhandler(404)
def not_found_error(error):
    if wants_json_response():
        return api_error_response(404)
    return render_template('errors/404.html'), 404


@errors.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if wants_json_response():
        return api_error_response(500)
    return render_template('errors/500.html'), 500


@errors.app_errorhandler(400)
def bad_request(error):
    if wants_json_response():
        return api_error_response(400)
    return render_template('errors/400.html'), 400