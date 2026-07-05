from datetime import timedelta

class Config:
    SECRET_KEY = "123_springboard7.0_secret_key"

    SQLALCHEMY_DATABASE_URI = (
        "mysql+pymysql://root:Eshwarnjr10*@localhost/hospital_management_system"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False