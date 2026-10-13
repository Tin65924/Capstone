from flask_login import LoginManager

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please sign in to access this page.'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    from flask import current_app
    from app.auth.models import get_user_by_id
    from app.auth.user import User

    try:
        user_data = get_user_by_id(user_id)
    except Exception as e:
        # Transient DB/pool failure must redirect to login, never 500
        # on every page navigation.
        try:
            current_app.logger.warning('load_user DB failure for %s: %s', user_id, e)
        except Exception:
            pass
        return None
    if user_data is None:
        return None
    try:
        return User(*user_data)
    except Exception:
        try:
            current_app.logger.warning('load_user bad row for %s', user_id)
        except Exception:
            pass
        return None


@login_manager.unauthorized_handler
def unauthorized():
    from flask import flash, redirect, url_for, request

    try:
        from app.auth.models import log_system_event
        log_system_event(f'system:auth_required:{request.path[:100]}')
    except Exception:  # noqa: BLE001 — audit must never break the redirect
        pass
    flash('Please sign in to access this page.', 'info')
    return redirect(url_for('auth.login', next=request.path))
