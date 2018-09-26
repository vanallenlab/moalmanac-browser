from flask import jsonify, request, url_for
from target_portal.modules.models import Assertion
from target_portal import db
from .errors import bad_request
from .auth import token_auth
from app.modules.api import api


"""Everything below taken from microblog tutorial"""

@api.route('/users/<int:id>', methods=['GET', 'PUT'])
@token_auth.login_required
def get_user(id):
    if request.method == 'PUT':
        user = User.query.get_or_404(id)
        data = request.get_json() or {}
        if 'username' in data and data['username'] != user.username and \
                User.query.filter_by(username=data['username']).first():
            return bad_request('please use a different username')
        if 'email' in data and data['email'] != user.email and \
                User.query.filter_by(email=data['email']).first():
            return bad_request('please use a different email address')
        user.from_dict(request.get_json() or {}, new_user=False)
        db.session.commit()
        return jsonify(user.to_dict())
    elif request.method == 'GET':
        return jsonify(User.query.get_or_404(id).to_dict())


@api.route('/users', methods=['GET', 'POST'])
def create_or_get_user():
    if request.method == 'POST':
        data = request.get_json() or {}
        if 'username' not in data or 'email' not in data or 'password' not in data:
            return bad_request('must include username, email and password fields')
        if User.query.filter_by(username=data['username']).first():
            return bad_request('please use a different username')
        if User.query.filter_by(email=data['email']).first():
            return bad_request('please use a different email address')
        user = User()
        user.from_dict(data, new_user=True)
        db.session.add(user)
        db.session.commit()
        response = jsonify(user.to_dict())
        response.status_code = 201
        response.headers['Location'] = url_for('api.get_user', id=user.id)
        return response

    elif request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        data = User.to_collection_dict(User.query, page, per_page, 'api.get_users')
        return jsonify(data)


@api.route('/users/<int:id>/followers', methods=['GET'])
@token_auth.login_required
def get_followers(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(user.followers, page, per_page,
                                   'api.get_followers', id=id)
    return jsonify(data)


@api.route('/users/<int:id>/followed', methods=['GET'])
@token_auth.login_required
def get_followed(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(user.followed, page, per_page,
                                   'api.get_followed', id=id)
    return jsonify(data)
