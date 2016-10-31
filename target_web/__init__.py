from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import config

app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)
db.init_app(app)

import target_web.views
