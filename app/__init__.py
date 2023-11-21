from flask import Flask

from config import Config
from app.extensions import db, bcrypt, mail, login_manager

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions here
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    from app.category import bp as category_bp
    app.register_blueprint(category_bp, url_prefix='/category')

    from app.request import bp as request_bp
    app.register_blueprint(request_bp, url_prefix='/request')

    from app.stock import bp as stock_bp
    app.register_blueprint(stock_bp, url_prefix='/stock')

    from app.user import bp as user_bp
    app.register_blueprint(user_bp, url_prefix='/user')

    return app