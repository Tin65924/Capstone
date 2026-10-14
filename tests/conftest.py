import os
import pytest
from flask import Flask
from unittest.mock import patch, MagicMock
import sys

# Ensure app.database is importable (needed for patching)
import app.database

# Must patch before ANY app imports happen
patcher_init_db = patch('app.database.init_db', return_value=None)
patcher_db_pool = patch('app.database.db.init_app', return_value=None)
patcher_init_db.start()
patcher_db_pool.start()

def _cleanup_patches():
    """Stop the module-level ``init_db``/``db.init_app`` patches.

    Registered with ``atexit`` so the patches started at import time
    (which keep the real PostgreSQL pool from opening during test
    collection) are always reverted when the pytest process exits.

    Returns:
        None.

    Side effects:
        Stops both module-level patchers.
    """
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
    """Mock app.database.db.execute, fetch_one, fetch_all before every test.

    Patches the three ``Database`` methods for the duration of each
    test (no real PostgreSQL needed) with empty defaults — ``execute``
    returns ``[]``, ``fetch_one`` returns ``None``, ``fetch_all``
    returns ``[]`` — and yields the mocks so tests can set return
    values before hitting an endpoint.

    Yields:
        dict: ``{'execute': mock, 'fetch_one': mock, 'fetch_all': mock}``
            MagicMock handles for the patched ``db`` methods.

    Side effects:
        Patches (and unpatches after the test) ``app.database.db``.
    """
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
    """Seed the roles table mock return.

    Preloads ``fetch_all`` with the 4 canonical roles (Student 1,
    Faculty 2, Librarian 3, Admin 4) and installs a ``fetch_one``
    side effect that resolves a role tuple from the queried params,
    so role lookups behave without a database.

    Args:
        mock_db (dict): The autouse DB mocks to configure.

    Returns:
        dict: The same ``mock_db`` mapping, with role data installed.

    Side effects:
        Mutates ``mock_db`` mock return values/side effects.
    """
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
    """Build the Flask test application.

    Calls :func:`app.create_app` with ``TESTING=True``, fixed test
    secrets/OAuth credentials, a dummy ``DATABASE_URL`` (never opened
    thanks to the ``mock_db`` fixture) and CSRF disabled, so every
    test gets an isolated app instance.

    Returns:
        Flask: Configured application for test clients/runners.

    Side effects:
        None beyond app construction.
    """
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
    """Provide a Flask test client for the test app.

    Args:
        app (Flask): The :func:`app` fixture instance.

    Returns:
        FlaskClient: Test client bound to ``app`` for GET/POST calls.

    Side effects:
        None.
    """
    return app.test_client()


@pytest.fixture
def runner(app):
    """Provide a Flask CLI test runner for the test app.

    Args:
        app (Flask): The :func:`app` fixture instance.

    Returns:
        FlaskCliRunner: CLI runner bound to ``app``.

    Side effects:
        None.
    """
    return app.test_cli_runner()


# ---------------------------------------------------------------------------
# Mock user loader so Flask-Login can reload users across requests
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def mock_user_loader():
    """Patch user loading so Flask-Login works without a database.

    Replaces ``app.auth.models.get_user_by_id`` with an in-memory map
    of ids 1-4 to the canned Student/Faculty/Librarian/Admin tuples,
    so session ``_user_id`` values set by the login fixtures resolve
    on every request.

    Yields:
        None.

    Side effects:
        Patches ``get_user_by_id`` for the duration of each test.
    """
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
    """Log a canned user into the test client session.

    Builds a :class:`app.auth.user.User` and writes its id into the
    client's session (``_user_id`` + fresh flag) so subsequent
    requests pass ``@login_required`` and RBAC guards as that role.

    Args:
        client (FlaskClient): Test client whose session to mutate.
        user_id (str): Canned user id ('1'-'4').
        email (str): Canned ``@mcst.edu.ph`` address.
        role (str): Role name (Student/Faculty/Librarian/Admin).
        full_name (str): Display name for the session user.

    Returns:
        User: The constructed user object.

    Side effects:
        Mutates the client's session transaction.
    """
    user = User(user_id, email, role, full_name)
    with client.session_transaction() as sess:
        sess['_user_id'] = user.get_id()
        sess['_fresh'] = True
    return user


@pytest.fixture
def student_client(client, mock_db):
    """Provide a test client logged in as the canned Student (id 1).

    Args:
        client (FlaskClient): Base test client to log in.
        mock_db (dict): Autouse DB mocks (unused; ensures patching).

    Returns:
        FlaskClient: Client authenticated as Test Student.

    Side effects:
        Mutates the client session via :func:`_log_in_user`.
    """
    _log_in_user(client, '1', 'student@mcst.edu.ph', 'Student', 'Test Student')
    return client


@pytest.fixture
def faculty_client(client, mock_db):
    """Provide a test client logged in as the canned Faculty (id 2).

    Args:
        client (FlaskClient): Base test client to log in.
        mock_db (dict): Autouse DB mocks (unused; ensures patching).

    Returns:
        FlaskClient: Client authenticated as Test Faculty.

    Side effects:
        Mutates the client session via :func:`_log_in_user`.
    """
    _log_in_user(client, '2', 'faculty@mcst.edu.ph', 'Faculty', 'Test Faculty')
    return client


@pytest.fixture
def librarian_client(client, mock_db):
    """Provide a test client logged in as the canned Librarian (id 3).

    Args:
        client (FlaskClient): Base test client to log in.
        mock_db (dict): Autouse DB mocks (unused; ensures patching).

    Returns:
        FlaskClient: Client authenticated as Test Librarian.

    Side effects:
        Mutates the client session via :func:`_log_in_user`.
    """
    _log_in_user(client, '3', 'librarian@mcst.edu.ph', 'Librarian', 'Test Librarian')
    return client


@pytest.fixture
def admin_client(client, mock_db):
    """Provide a test client logged in as the canned Admin (id 4).

    Args:
        client (FlaskClient): Base test client to log in.
        mock_db (dict): Autouse DB mocks (unused; ensures patching).

    Returns:
        FlaskClient: Client authenticated as Test Admin.

    Side effects:
        Mutates the client session via :func:`_log_in_user`.
    """
    _log_in_user(client, '4', 'admin@mcst.edu.ph', 'Admin', 'Test Admin')
    return client


# ---------------------------------------------------------------------------
# OAuth helpers
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_oauth_flow():
    """Mock the entire Google OAuth flow so no real HTTP calls are made.

    Patches ``app.auth.routes._build_flow`` and yields its
    ``MagicMock`` flow object, so login/callback tests can drive the
    OAuth handshake (authorization URL, token fetch, id-token verify)
    entirely in memory.

    Yields:
        MagicMock: The mocked OAuth flow object.

    Side effects:
        Patches ``_build_flow`` for the duration of the test.
    """
    with patch('app.auth.routes._build_flow') as mock_build:
        mock_flow = MagicMock()
        mock_build.return_value = mock_flow
        yield mock_flow


# ---------------------------------------------------------------------------
# Failure notes: show each test's troubleshooting note when it fails
# ---------------------------------------------------------------------------
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Attach the test docstring (Validates / If fails / Indicates) to failure output.

    This hookwrapper lets the test run first, then appends the test
    function's docstring as a ``"Test note"`` section on the failure
    report, so failure output shows the troubleshooting note inline.

    Args:
        item (pytest.Item): The test item being reported.
        call (pytest.CallInfo): Call phase info (only ``"call"``
            failures are annotated).

    Returns:
        Generator: Yields to the inner hook and processes the report.

    Side effects:
        Mutates the failure report's ``longrepr`` sections.
    """
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        doc = getattr(item.obj, "__doc__", None)
        if doc:
            note = doc.strip()
            if note:
                try:
                    report.longrepr.addsection("Test note", note)
                except Exception:
                    pass
