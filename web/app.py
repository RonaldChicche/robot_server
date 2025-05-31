# web/app.py
from flask import Flask
from config import Config
from routes import register_blueprints

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    register_blueprints(app)


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)  