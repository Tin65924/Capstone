import glob
import os
import shutil
import subprocess
from datetime import datetime

from flask import current_app


DEFAULT_BACKUP_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'backups',
)

# Windows PostgreSQL installers do not add bin/ to PATH, so look there too.
_WINDOWS_TOOL_DIRS = (
    r'C:\Program Files\PostgreSQL\*\bin',
    r'C:\Program Files (x86)\PostgreSQL\*\bin',
)


def resolve_tool(name, env_var):
    """Locate a postgres client tool (pg_dump/psql).

    Checks the env override first, then PATH, then well-known Windows
    install locations. Raises RuntimeError with setup guidance when missing
    (instead of leaking a bare "[WinError 2]" to the UI).
    """
    override = os.getenv(env_var)
    if override:
        if os.path.isfile(override) or shutil.which(override):
            return override
        raise RuntimeError(
            f'{name} not found at {env_var}={override!r}. '
            f'Install the PostgreSQL client tools or fix the {env_var} path.'
        )
    on_path = shutil.which(name)
    if on_path:
        return on_path
    if os.name == 'nt':
        candidates = []
        for pattern in _WINDOWS_TOOL_DIRS:
            candidates.extend(glob.glob(os.path.join(pattern, name + '.exe')))
        if candidates:
            # Newest server version first (e.g. .../18/bin before .../16/bin).
            return sorted(candidates, reverse=True)[0]
    raise RuntimeError(
        f'{name} was not found. Install the PostgreSQL client tools and add '
        f'them to PATH, or point {env_var} at the executable '
        f'(e.g. C:\\Program Files\\PostgreSQL\\18\\bin\\{name}.exe).'
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

    Dumps with --clean --if-exists so a restore is a true replace of the
    database (DROP + recreate + reload), not an append onto live tables.

    Raises RuntimeError with the captured pg_dump stderr on failure.
    """
    backup_dir = get_backup_dir()
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'library_backup_{timestamp}.sql'
    filepath = os.path.join(backup_dir, filename)

    db_url = current_app.config['DATABASE_URL']
    pg_dump = resolve_tool('pg_dump', 'PG_DUMP')
    try:
        subprocess.run(
            [pg_dump, '--clean', '--if-exists',
             '--dbname=' + db_url, '--file=' + filepath],
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
    except (FileNotFoundError, OSError) as e:
        raise RuntimeError(
            f'Could not start pg_dump ({pg_dump}): {e}. '
            'Install the PostgreSQL client tools or set PG_DUMP to its path.'
        )
    size_bytes = os.path.getsize(filepath)
    return filename, size_bytes


def restore_backup(filename):
    """Replace the database from a stored backup file (argv list — no shell).

    Runs inside a single transaction with ON_ERROR_STOP so any failure
    aborts the whole restore (atomic) and surfaces as an error instead of
    a false success. The dump's --clean --if-exists DROPs make this a true
    replace: rows added after the backup was taken are deleted.

    Raises FileNotFoundError if the file is missing, ValueError on
    traversal, RuntimeError with captured psql stderr on failure.
    """
    filepath = resolve_backup_path(filename)
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f'Backup file not found: {filename}')

    db_url = current_app.config['DATABASE_URL']
    psql = resolve_tool('psql', 'PSQL')
    try:
        subprocess.run(
            [psql, '--dbname=' + db_url, '-v', 'ON_ERROR_STOP=1',
             '--single-transaction', '--file=' + filepath],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        err = (e.stderr or '').strip() or f'psql exited with status {e.returncode}'
        raise RuntimeError(err)
    except (FileNotFoundError, OSError) as e:
        raise RuntimeError(
            f'Could not start psql ({psql}): {e}. '
            'Install the PostgreSQL client tools or set PSQL to its path.'
        )
