from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow  #must initialize after SQLAlchemy

db = SQLAlchemy()
ma = Marshmallow()  #must initialize after SQLAlchemy