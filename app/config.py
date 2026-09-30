import os
from dotenv import load_dotenv

load_dotenv()


def _int_env(name, default):
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
    OVERNIGHT_DUE_DAYS_STUDENT = 2
    OVERNIGHT_DUE_DAYS_FACULTY = 30
    DAILY_CIRCULATION_DUE_DAYS = 0
    OVERDUE_FINE_PER_DAY = 5.0
    OVERDUE_GRACE_DAYS = 0
    RESERVATION_CLAIM_DAYS = 2
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
