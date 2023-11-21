from flask import Blueprint

bp = Blueprint('request', __name__)


from app.request import routes