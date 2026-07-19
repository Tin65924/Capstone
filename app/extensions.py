from flask_login import LoginManager

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please sign in to access this page.'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    from app.auth.models import get_user_by_id
    from app.auth.user import User

    user_data = get_user_by_id(user_id)
    if user_data is None:
        return None
    return User(*user_data)


@login_manager.unauthorized_handler
def unauthorized():
    from flask import flash, redirect, url_for, request

    flash('Please sign in to access this page.', 'info')
    return redirect(url_for('auth.login', next=request.path))
