import os
from flask import Flask, render_template, request, redirect, flash, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
from .config import Config
from .extensions import login_manager

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    # Trust Render's proxy headers (X-Forwarded-Proto for HTTPS, X-Forwarded-For for IP)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    if test_config:
        app.config.update(test_config)

    from .database import init_db
    init_db(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from .auth import auth_bp
    from .requests import requests_bp
    from .procurement import procurement_bp
    from .resources import resources_bp
    from .cataloging import cataloging_bp
    from .circulation import circulation_bp
    from .inventory import inventory_bp
    from .analytics import analytics_bp
    from .backup import backup_bp
    from .settings import settings_bp
    from .main import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(requests_bp)
    app.register_blueprint(procurement_bp)
    app.register_blueprint(resources_bp)
    app.register_blueprint(cataloging_bp)
    app.register_blueprint(circulation_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(backup_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(main_bp)

    try:
        # Skip DB-backed settings sync in tests so mocked db call counts
        # in tests (analytics/catalog/autosuggest) stay deterministic.
        if not app.config.get('TESTING'):
            with app.app_context():
                from .settings.models import sync_settings_to_config
                sync_settings_to_config(app)
    except Exception:
        pass

    register_error_handlers(app)

    try:
        if not app.config.get('TESTING'):
            from .backup.scheduler import start_scheduler
            start_scheduler(app)
    except Exception:
        # Never fail app startup over the scheduler — but log loudly so a
        # typo'd BACKUP_DAY/BACKUP_HOUR can't silently disable backups.
        app.logger.exception('Backup scheduler failed to start')

    return app


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/error.html',
                               code=404, title='Page Not Found',
                               message='The page you are looking for does not exist or may have been moved.'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/error.html',
                               code=403, title='Access Denied',
                               message='You do not have permission to access this page.'), 403

    @app.errorhandler(401)
    def unauthorized(e):
        if request.path.startswith(('/admin', '/librarian')):
            flash('Please sign in to access this page.', 'info')
            return redirect(url_for('auth.login', next=request.path))
        return render_template('errors/error.html',
                               code=401, title='Unauthorized',
                               message='Please sign in to continue.'), 401

    @app.errorhandler(500)
    def internal_error(e):
        return render_template('errors/error.html',
                               code=500, title='Something Went Wrong',
                               message='An unexpected error occurred. Please try again later.'), 500
