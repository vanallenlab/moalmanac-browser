# These are development settings only. Security risk if deployed without modification.

from secret_key import GCP_SECRET_KEY, USERNAME, PASSWORD

DEBUG = False
SQLALCHEMY_DATABASE_URI = 'sqlite:///db_versions/almanac.0.4.5.sqlite3'
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = GCP_SECRET_KEY
BOOTSTRAP_SERVE_LOCAL = True

APP_NAME = 'The Molecular Oncology Almanac'
APP_NAME_SHORT = 'Molecular Oncology Almanac'

#for password protecting certain pages with sensitive data (emails)
BASIC_AUTH_USERNAME = USERNAME
BASIC_AUTH_PASSWORD = PASSWORD
