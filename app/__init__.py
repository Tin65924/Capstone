import os
from flask import Flask, render_template, request, redirect, flash, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
from .config import Config
from .extensions import login_manager

def create_app(test_config=None):
    """Create and configure the MCST LMS Flask application instance.
    Builds the Flask app with instance-relative config, trusts Render proxy
    headers via ProxyFix, initializes the database and login manager,
    registers all module blueprints, syncs DB-backed settings, wires error
    handlers and template filters, and starts the backup scheduler.
    Args:
        test_config: Optional dict of config overrides for testing.
    Returns:
        Configured Flask application instance ready to serve requests.
    """
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

    from .circulation.models import format_due
    app.template_filter('duefmt')(format_due)

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
    """Register HTTP error handlers for the Flask application.
    Attaches handlers for 401, 403, 404, 405, and 500 codes so every
    failure renders the shared errors/error.html template instead of a
    default stack trace. Called once from create_app during startup.
    Args:
        app: Flask application instance to attach handlers to.
    Returns:
        None; handlers are registered on the app in place.
    """
    @app.errorhandler(404)
    def not_found(e):
        """Render the 404 Page Not Found error page.
        Handles HTTP 404 when a URL matches no route. Renders
        errors/error.html with code 404 and a moved-or-missing message.
        Args:
            e: Original 404 exception passed by Flask.
        Returns:
            Tuple of rendered error template and 404 status code.
        """
        return render_template('errors/error.html',
                               code=404, title='Page Not Found',
                               message='The page you are looking for does not exist or may have been moved.'), 404

    @app.errorhandler(403)
    def forbidden(e):
        """Render the 403 Access Denied error page.
        Handles HTTP 403 when an authenticated user lacks permission.
        Renders errors/error.html with code 403 and a permission message.
        Args:
            e: Original 403 exception passed by Flask.
        Returns:
            Tuple of rendered error template and 403 status code.
        """
        return render_template('errors/error.html',
                               code=403, title='Access Denied',
                               message='You do not have permission to access this page.'), 403

    @app.errorhandler(401)
    def unauthorized(e):
        """Handle HTTP 401 by redirecting protected areas or rendering 401.
        Sends /admin and /librarian paths to the login page with a sign-in
        flash and the original path as next, so post-login redirect works.
        All other paths render errors/error.html with code 401.
        Args:
            e: Original 401 exception passed by Flask.
        Returns:
            Login redirect for admin/librarian paths, else rendered 401 page.
        """
        if request.path.startswith(('/admin', '/librarian')):
            flash('Please sign in to access this page.', 'info')
            return redirect(url_for('auth.login', next=request.path))
        return render_template('errors/error.html',
                               code=401, title='Unauthorized',
                               message='Please sign in to continue.'), 401

    @app.errorhandler(405)
    def method_not_allowed(e):
        """Render the 405 Method Not Allowed error page.
        Handles HTTP 405 when a URL is hit with the wrong method (e.g.
        resubmitting a form with the Back button). Renders
        errors/error.html with code 405 and guidance to go back.
        Args:
            e: Original 405 exception passed by Flask.
        Returns:
            Tuple of rendered error template and 405 status code.
        """
        return render_template('errors/error.html',
                               code=405, title='Method Not Allowed',
                               message='That action is not available here (for example, resubmitting a form with the Back button). Please go back and continue browsing.'), 405

    @app.errorhandler(500)
    def internal_error(e):
        """Render the 500 Something Went Wrong error page.
        Logs the real traceback and writes a system:error:500 audit row so
        Render logs stay diagnosable, then renders errors/error.html with
        code 500 and a generic retry-later message. Never raises itself.
        Args:
            e: Original 500 exception passed by Flask.
        Returns:
            Tuple of rendered error template and 500 status code.
        """
        # Log the real traceback first: with debug off the browser only
        # sees the generic page, so Render logs are the only diagnosis.
        app.logger.exception('500 on %s', request.path)
        try:
            from app.auth.models import log_system_event
            log_system_event(f'system:error:500:{request.path[:100]}')
        except Exception:  # noqa: BLE001 — the error page must always render
            app.logger.exception('System audit row for 500 failed')
        return render_template('errors/error.html',
                               code=500, title='Something Went Wrong',
                               message='An unexpected error occurred. Please try again later.'), 500
