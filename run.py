from flask import Flask
from patent_database import register
import config

def create_dev_app():
    app = Flask(__name__,
                template_folder='patent_database/templates',
                static_folder='patent_database/static')
    app.config.from_object(config.DevConfig)
    register(app)
    return app

if __name__ == '__main__':
    app = create_dev_app()
    print("Open http://127.0.0.1:5000/patent_database")
    app.run(debug=True)