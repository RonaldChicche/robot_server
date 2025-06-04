from .redis_routes import redis_bp
from .influx_routes import influx_bp
#from .general_routes import general_bp

def register_blueprints(app):
    app.register_blueprint(redis_bp, url_prefix="/redis")
    app.register_blueprint(influx_bp, url_prefix="/influx")
    #app.register_blueprint(general_bp, url_prefix="/")
