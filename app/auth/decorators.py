from functools import wraps
from flask import flash, redirect, request, url_for
from flask_login import current_user

_ROLE_TEXT = {
    'Librarian': 'a Librarian',
    'Admin': 'an Admin',
    'Faculty': 'a Faculty member',
    'Student': 'a Student',
}


def _roles_text(roles):
    if not roles:
        return 'an authorized user'
    texts = [_ROLE_TEXT.get(r, r) for r in roles]
    if len(texts) == 1:
        return texts[0]
    return ', '.join(texts[:-1]) + ' or ' + texts[-1]


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please sign in to access this page.', 'info')
                return redirect(url_for('auth.login', next=request.path))
            if current_user.role not in roles:
                flash(f'Access denied. You must be logged in as {_roles_text(roles)} to access this page.', 'error')
                return redirect(url_for('main.user_profile'))
            return f(*args, **kwargs)
        return wrapped
    return decorator


librarian_required = role_required('Librarian', 'Admin')
faculty_required = role_required('Faculty', 'Librarian', 'Admin')
admin_required = role_required('Admin')
