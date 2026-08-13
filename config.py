import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "default-fallback-secret-key-change-in-production")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:Eshwarnjr10*@localhost/hospital_management_system"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = os.getenv("FLASK_DEBUG", "1") in ["1", "true", "True"]
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False