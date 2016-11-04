from flask import Blueprint

api = Blueprint('api', __name__)

@api.route('/')
def index():
	return 'API'

@api.route('/add_assertions')
def add_assertions():
    return 'Assertions'
