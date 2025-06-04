# web/app.py
from dotenv import load_dotenv

load_dotenv()
from flask import Flask
from flasgger import Swagger
from services.config import Config
from routes import register_blueprints



def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    swagger = Swagger(app)

    register_blueprints(app)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)  