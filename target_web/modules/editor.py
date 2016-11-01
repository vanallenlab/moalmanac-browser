from flask import Blueprint

editor = Blueprint('editor', __name__)

@editor.route('/')
def index():
	return 'Editor'
