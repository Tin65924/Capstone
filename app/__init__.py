import os
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from .config import Config
from .extensions import login_manager

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    # Trust Render's proxy headers (X-Forwarded-Proto for HTTPS)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    if test_config:
        app.config.update(test_config)

    from .database import init_db
    init_db(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from .auth import auth_bp
    from .requests import requests_bp
    from .procurement import procurement_bp
    from .cataloging import cataloging_bp
    from .circulation import circulation_bp
    from .inventory import inventory_bp
    from .analytics import analytics_bp
    from .backup import backup_bp
    from .main import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(requests_bp)
    app.register_blueprint(procurement_bp)
    app.register_blueprint(cataloging_bp)
    app.register_blueprint(circulation_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(backup_bp)
    app.register_blueprint(main_bp)

    return app
