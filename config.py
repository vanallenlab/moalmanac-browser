# These are development settings only. Security risk if deployed without modification.

from secret_key import GCP_SECRET_KEY

DEBUG = False
SQLALCHEMY_DATABASE_URI = 'sqlite:///salsa110.sqlite3'
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = GCP_SECRET_KEY
BOOTSTRAP_SERVE_LOCAL = True

APP_NAME = 'SALSA'
APP_NAME_SHORT = 'SALSA'
