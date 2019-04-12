from flask import jsonify, g
from app import db
from app.api import bp
from app.api.auth import basic_auth

#TODO implement with auth. Copied from microblog tutorial


@bp.route('/tokens', method=['POST'])
@basic_auth.login_required
def get_token():
    token = g.current_user.get_token()
    db.session.commit()
    return jsonify({'token': token})


@bp.route('/tokens', methods=['DELETE'])
@token_auth.login_required
def revoke_token():
    g.current_user.revoke_token()
    db.session.commit()
    return '', 204
