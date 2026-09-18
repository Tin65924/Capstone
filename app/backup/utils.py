import os
import subprocess
from datetime import datetime

from flask import current_app


DEFAULT_BACKUP_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'backups',
)


def get_backup_dir():
    """Configurable secure storage location (env BACKUP_DIR via config)."""
    configured = None
    try:
        configured = current_app.config.get('BACKUP_DIR')
    except RuntimeError:
        configured = None
    return configured or DEFAULT_BACKUP_DIR


def resolve_backup_path(filename):
    """Absolute path for `filename` guarded to stay inside BACKUP_DIR.

    Raises ValueError on path traversal attempts.
    """
    backup_dir = os.path.abspath(get_backup_dir())
    path = os.path.abspath(os.path.join(backup_dir, filename))
    if os.path.commonpath([backup_dir, path]) != backup_dir:
        raise ValueError('Invalid backup filename.')
    return path


def create_backup():
    """Run pg_dump (argv list — no shell) and return (filename, size_bytes).

    Raises RuntimeError with the captured pg_dump stderr on failure.
    """
    backup_dir = get_backup_dir()
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'library_backup_{timestamp}.sql'
    filepath = os.path.join(backup_dir, filename)

    db_url = current_app.config['DATABASE_URL']
    pg_dump = os.getenv('PG_DUMP', 'pg_dump')
    try:
        subprocess.run(
            [pg_dump, '--dbname=' + db_url, '--file=' + filepath],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        err = (e.stderr or '').strip() or f'pg_dump exited with status {e.returncode}'
        try:
            if os.path.isfile(filepath):
                os.remove(filepath)
        except OSError:
            pass
        raise RuntimeError(err)
    size_bytes = os.path.getsize(filepath)
    return filename, size_bytes


def restore_backup(filename):
    """Run psql against a stored backup file (argv list — no shell).

    Raises FileNotFoundError if the file is missing, ValueError on
    traversal, RuntimeError with captured psql stderr on failure.
    """
    filepath = resolve_backup_path(filename)
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f'Backup file not found: {filename}')

    db_url = current_app.config['DATABASE_URL']
    psql = os.getenv('PSQL', 'psql')
    try:
        subprocess.run(
            [psql, '--dbname=' + db_url, '--file=' + filepath],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        err = (e.stderr or '').strip() or f'psql exited with status {e.returncode}'
        raise RuntimeError(err)
