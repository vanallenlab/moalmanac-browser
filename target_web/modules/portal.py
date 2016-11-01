from flask import Blueprint

portal = Blueprint('portal', __name__)

@portal.route('/')
def index():
	return 'Portal'
