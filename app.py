import os
from flask import Flask

from config import DevelopmentConfig, ProductionConfig
from extensions import db, login_manager

app = Flask(__name__)

if os.getenv("FLASK_ENV") == "production":
    app.config.from_object(ProductionConfig)
else:
    app.config.from_object(DevelopmentConfig)

db.init_app(app)
login_manager.init_app(app)

login_manager.login_view = "login"

from routes.auth import *
from routes.dashboard import *
from routes.api import *
from models import User

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    debug_mode = app.config.get("DEBUG", False)
    app.run(debug=debug_mode)