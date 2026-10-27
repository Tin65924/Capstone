"""Small session-bound CSRF protection for server-rendered forms and fetches."""

import re
import secrets
from hmac import compare_digest
from html import escape

from flask import abort, current_app, request, session


_POST_FORM = re.compile(r'(<form\b[^>]*\bmethod\s*=\s*["\']?post\b[^>]*>)', re.IGNORECASE)


def csrf_token():
    """Return the stable per-session token used by form and fetch requests."""
    token = session.get('_csrf_token')
    if not token:
        token = secrets.token_urlsafe(32)
        session['_csrf_token'] = token
    return token


def init_csrf(app):
    """Register validation and inject tokens into rendered POST forms."""
    @app.context_processor
    def csrf_context():
        return {'csrf_token': csrf_token}

    @app.before_request
    def protect_mutations():
        if not app.config.get('CSRF_ENABLED', True) or not app.config.get('WTF_CSRF_ENABLED', True):
            return
        if request.method not in ('POST', 'PUT', 'PATCH', 'DELETE'):
            return
        supplied = request.headers.get('X-CSRFToken') or request.form.get('csrf_token')
        expected = session.get('_csrf_token')
        if not expected or not supplied or not compare_digest(expected, supplied):
            abort(400, description='Invalid or missing CSRF token.')

    @app.after_request
    def inject_form_tokens(response):
        if not app.config.get('CSRF_ENABLED', True):
            return response
        if response.mimetype != 'text/html' or response.direct_passthrough:
            return response
        body = response.get_data(as_text=True)
        if '<form' not in body.lower():
            return response
        token = escape(csrf_token(), quote=True)
        body = _POST_FORM.sub(
            lambda match: match.group(1) + f'<input type="hidden" name="csrf_token" value="{token}">',
            body,
        )
        response.set_data(body)
        return response
