from flask import Blueprint

patent_database_bp = Blueprint('patent_database', __name__,
                           template_folder='templates',
                           static_folder='static',
                           url_prefix='/patent_database')

from . import routes

def register(app):
    app.register_blueprint(patent_database_bp)