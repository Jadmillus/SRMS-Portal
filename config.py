import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = '370HSSV0773H'
    SQLALCHEMY_DATABASE_URI = "mysql://root:icui4cu2@localhost/srms"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = "rogueoutis@gmail.com"
    MAIL_PASSWORD = 'zkst nxom wqbx vwna' 