from almanac_browser import create_app
import os

app = create_app(__name__)

if __name__ == '__main__':

	# for debugging
	#if os.environ['FLASK_ENV'] == 'development':
	#	app.run(host='0.0.0.0', debug=True, use_debugger=False, use_reloader=False, passthrough_errors=True)

	# for hosting
	#else:
	app.run(host='0.0.0.0', debug=True)
