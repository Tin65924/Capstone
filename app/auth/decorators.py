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
    """Format role names into a human-readable flash message fragment.
    Maps internal role names to natural phrases (e.g. Admin to an Admin)
    and joins multiples with commas and or, so access-denied flashes read
    naturally. Unmapped names pass through unchanged.
    Args:
        roles: Tuple/list of role name strings required by the guard.
    Returns:
        Human-readable string like 'a Librarian or an Admin'.
    """
    if not roles:
        return 'an authorized user'
    texts = [_ROLE_TEXT.get(r, r) for r in roles]
    if len(texts) == 1:
        return texts[0]
    return ', '.join(texts[:-1]) + ' or ' + texts[-1]


def role_required(*roles):
    """Build an RBAC decorator requiring one of the given roles.
    Produces the guard used by librarian_required, faculty_required, and
    admin_required. Unauthenticated users are sent to login; wrong-role
    users get an audit row (security:denied:<endpoint>) plus an error flash
    and a redirect to /user/profile instead of a raw 403.
    Args:
        *roles: Allowed role name strings (e.g. 'Librarian', 'Admin').
    Returns:
        Decorator that wraps a view with the role check.
    """
    def decorator(f):
        """Wrap a view function with the role membership check.

        Preserves the original name via wraps so Flask routing keeps
        working. Defers the actual check to the per-request handler.

        Args:
            f: View function to protect.

        Returns:
            Wrapped view enforcing the role guard.
        """
        @wraps(f)
        def wrapped(*args, **kwargs):
            """Enforce authentication then role membership per request.

            Redirects anonymous users to login, logs a security:denied
            audit row plus an error flash for wrong roles, and otherwise
            calls through to the original view.

            Args:
                *args: Positional args passed to the view.
                **kwargs: Keyword args passed to the view.

            Returns:
                Original view response, or a login/profile redirect.
            """
            if not current_user.is_authenticated:
                flash('Please sign in to access this page.', 'info')
                return redirect(url_for('auth.login', next=request.path))
            if current_user.role not in roles:
                try:
                    from app.auth.models import log_activity
                    log_activity(current_user.id,
                                 f'security:denied:{request.endpoint or request.path}')
                except Exception:  # noqa: BLE001 — audit must never break the redirect
                    pass
                flash(f'Access denied. You must be logged in as {_roles_text(roles)} to access this page.', 'error')
                return redirect(url_for('main.user_profile'))
            return f(*args, **kwargs)
        return wrapped
    return decorator


librarian_required = role_required('Librarian', 'Admin')
faculty_required = role_required('Faculty', 'Librarian', 'Admin')
admin_required = role_required('Admin')
