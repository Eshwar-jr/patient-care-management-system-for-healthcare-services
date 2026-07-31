from flask import Flask

from config import Config
from extensions import db, login_manager

app = Flask(__name__)

app.config.from_object(Config)

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

    app.run(debug=True)