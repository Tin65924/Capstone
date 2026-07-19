import os
import pytest
from flask import Flask
from unittest.mock import patch, MagicMock
import sys

# Must patch before ANY app imports happen
patcher_init_db = patch('app.database.init_db', return_value=None)
patcher_db_pool = patch('app.database.db.init_app', return_value=None)
patcher_init_db.start()
patcher_db_pool.start()

def _cleanup_patches():
    patcher_init_db.stop()
    patcher_db_pool.stop()

# Register cleanup at exit (called when pytest finishes)
import atexit
atexit.register(_cleanup_patches)

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ['FLASK_DEBUG'] = '0'
os.environ['SECRET_KEY'] = 'test-secret'
os.environ['GOOGLE_OAUTH_CLIENT_ID'] = 'test-client-id'
os.environ['GOOGLE_OAUTH_CLIENT_SECRET'] = 'test-client-secret'


# ---------------------------------------------------------------------------
# Fixtures: mock the database singleton so no real PostgreSQL is needed
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def mock_db():
    """Mock app.database.db.execute, fetch_one, fetch_all before every test."""
    patcher_execute = patch('app.database.db.execute', return_value=[])
    patcher_fetch_one = patch('app.database.db.fetch_one', return_value=None)
    patcher_fetch_all = patch('app.database.db.fetch_all', return_value=[])

    mock_exec = patcher_execute.start()
    mock_fetch_one = patcher_fetch_one.start()
    mock_fetch_all = patcher_fetch_all.start()

    yield {
        'execute': mock_exec,
        'fetch_one': mock_fetch_one,
        'fetch_all': mock_fetch_all,
    }

    patcher_execute.stop()
    patcher_fetch_one.stop()
    patcher_fetch_all.stop()


@pytest.fixture
def mock_roles(mock_db):
    """Seed the roles table mock return."""
    mock_db['fetch_all'].return_value = [
        (1, 'Student'),
        (2, 'Faculty'),
        (3, 'Librarian'),
        (4, 'Admin'),
    ]
    mock_db['fetch_one'].side_effect = lambda q, p=None: {
        (1, 'Student') if p and 'Student' in str(p) or (p and p[0] == 'Student') else
        (2, 'Faculty') if p and 'Faculty' in str(p) or (p and p[0] == 'Faculty') else
        (3, 'Librarian') if p and 'Librarian' in str(p) or (p and p[0] == 'Librarian') else
        (4, 'Admin') if p and 'Admin' in str(p) or (p and p[0] == 'Admin') else None
        for _ in [1]
    }.get(True)
    return mock_db


# ---------------------------------------------------------------------------
# App & client fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def app():
    from app import create_app
    app = create_app(test_config={
        'TESTING': True,
        'SECRET_KEY': 'test-secret',
        'DATABASE_URL': 'postgresql://test:test@localhost:5432/library_test',
        'GOOGLE_OAUTH_CLIENT_ID': 'test-client-id',
        'GOOGLE_OAUTH_CLIENT_SECRET': 'test-client-secret',
        'SERVER_NAME': 'localhost.localdomain',
        'WTF_CSRF_ENABLED': False,
    })
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


# ---------------------------------------------------------------------------
# Mock user loader so Flask-Login can reload users across requests
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def mock_user_loader():
    from unittest.mock import patch
    user_map = {
        '1': (1, 'student@mcst.edu.ph', 'Student', 'Test Student'),
        '2': (2, 'faculty@mcst.edu.ph', 'Faculty', 'Test Faculty'),
        '3': (3, 'librarian@mcst.edu.ph', 'Librarian', 'Test Librarian'),
        '4': (4, 'admin@mcst.edu.ph', 'Admin', 'Test Admin'),
    }
    with patch('app.auth.models.get_user_by_id', side_effect=lambda uid: user_map.get(str(uid))):
        yield


# ---------------------------------------------------------------------------
# User fixtures for simulating Flask-Login sessions
# ---------------------------------------------------------------------------
from flask_login import login_user
from app.auth.user import User


def _log_in_user(client, user_id, email, role, full_name):
    user = User(user_id, email, role, full_name)
    with client.session_transaction() as sess:
        sess['_user_id'] = user.get_id()
        sess['_fresh'] = True
    return user


@pytest.fixture
def student_client(client, mock_db):
    _log_in_user(client, '1', 'student@mcst.edu.ph', 'Student', 'Test Student')
    return client


@pytest.fixture
def faculty_client(client, mock_db):
    _log_in_user(client, '2', 'faculty@mcst.edu.ph', 'Faculty', 'Test Faculty')
    return client


@pytest.fixture
def librarian_client(client, mock_db):
    _log_in_user(client, '3', 'librarian@mcst.edu.ph', 'Librarian', 'Test Librarian')
    return client


@pytest.fixture
def admin_client(client, mock_db):
    _log_in_user(client, '4', 'admin@mcst.edu.ph', 'Admin', 'Test Admin')
    return client


# ---------------------------------------------------------------------------
# OAuth helpers
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_oauth_flow():
    """Mock the entire Google OAuth flow so no real HTTP calls are made."""
    with patch('app.auth.routes._build_flow') as mock_build:
        mock_flow = MagicMock()
        mock_build.return_value = mock_flow
        yield mock_flow
