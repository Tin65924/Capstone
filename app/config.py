import os
from dotenv import load_dotenv

load_dotenv()


def _int_env(name, default):
    """Read an integer setting from the environment with a safe fallback.

    Wraps ``os.getenv`` with int coercion so a missing, empty, or
    non-numeric variable (e.g. a typo'd ``BACKUP_DAY=abc``) never raises
    at import time. Used for ``BACKUP_DAY``/``BACKUP_HOUR``/``BACKUP_KEEP``
    defaults on the :class:`Config` object.

    Args:
        name: Environment variable name to read.
        default: Fallback value used when the variable is missing or
            cannot be parsed as an integer.

    Returns:
        The parsed integer, or ``int(default)`` when parsing fails.
    """
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return int(default)


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/library_db')
    GOOGLE_OAUTH_CLIENT_ID = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
    GOOGLE_OAUTH_CLIENT_SECRET = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')
    MAX_BORROW_LIMIT_STUDENT = 3
    MAX_BORROW_LIMIT_FACULTY = 5
    OVERNIGHT_DUE_DAYS_STUDENT = 1
    OVERNIGHT_DUE_DAYS_FACULTY = 7
    OVERDUE_FINE_PER_DAY = 5.0
    OVERDUE_GRACE_DAYS = 0
    RESERVATION_CLAIM_HOURS = 2
    DUE_SOON_NOTIFY_DAYS = 2
    OVERNIGHT_NOTIFY_HOURS_STUDENT = 5
    OVERNIGHT_NOTIFY_DAYS_FACULTY = 2
    IN_LIBRARY_NOTIFY_HOURS = 1

    BACKUP_DIR = os.getenv(
        'BACKUP_DIR',
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backups'),
    )
    BACKUP_DAY = _int_env('BACKUP_DAY', 1)
    BACKUP_HOUR = _int_env('BACKUP_HOUR', 2)
    BACKUP_KEEP = _int_env('BACKUP_KEEP', 12)
    # Skip replaying schema.sql at boot (faster restarts once the DB is
    # initialized). Default OFF (run it) so fresh databases never break —
    # only set SKIP_SCHEMA_SYNC=1 after the schema is known-good.
    SKIP_SCHEMA_SYNC = os.getenv('SKIP_SCHEMA_SYNC', '0') == '1'
