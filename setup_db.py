"""
Database Setup Script — run once to initialize the LMS database.

Usage:
    python setup_db.py

What it does:
    1. Locates your PostgreSQL 18 installation
    2. Temporarily enables trust authentication for local connections
    3. Sets a known password for the postgres user
    4. Creates the library_db database
    5. Runs app/schema.sql to create all tables
    6. Inserts seed data (roles)
    7. Restores original pg_hba.conf
    8. Updates .env with the connection string
"""

import os
import sys
import shutil
import re
import subprocess
import glob

DB_NAME = 'library_db'
DB_PASSWORD = 'postgres'
SCHEMA_FILE = os.path.join(os.path.dirname(__file__), 'app', 'schema.sql')
ENV_FILE = os.path.join(os.path.dirname(__file__), '.env')


def find_pg_data_dir():
    """Locate the local PostgreSQL data directory.

    Probes well-known install paths (versions 18/17/16) plus any
    ``C:\\Program Files\\PostgreSQL\\*\\data`` glob hit, returning the
    first directory that actually contains ``pg_hba.conf``.

    Returns:
        str | None: Data-directory path, or None when no PostgreSQL
            installation is found.

    Side effects:
        None; filesystem probes only.
    """
    candidates = [
        r'C:\Program Files\PostgreSQL\18\data',
        r'C:\Program Files\PostgreSQL\17\data',
        r'C:\Program Files\PostgreSQL\16\data',
    ]
    pg_version_dirs = glob.glob(r'C:\Program Files\PostgreSQL\*\data')
    candidates.extend(pg_version_dirs)

    for path in candidates:
        hba = os.path.join(path, 'pg_hba.conf')
        if os.path.isfile(hba):
            return path
    return None


def find_pg_bin_dir():
    """Locate the PostgreSQL ``bin`` directory for the installed server.

    Derives the server root from :func:`find_pg_data_dir` and returns
    its ``bin`` subdirectory (home of ``pg_ctl.exe``/``psql.exe``).

    Returns:
        str | None: ``bin``-directory path, or None when the data
            directory (or its ``bin`` folder) cannot be found.

    Side effects:
        None; filesystem probes only.
    """
    data_dir = find_pg_data_dir()
    if not data_dir:
        return None
    pg_root = os.path.dirname(data_dir)
    bin_dir = os.path.join(pg_root, 'bin')
    if os.path.isdir(bin_dir):
        return bin_dir
    return None


def reload_pg(data_dir):
    """Reload the PostgreSQL configuration without restarting the server.

    Runs ``pg_ctl.exe reload -D <data_dir>`` so ``pg_hba.conf`` edits
    take effect; prints a warning (instead of raising) when the reload
    fails or ``pg_ctl`` cannot be located.

    Args:
        data_dir (str): PostgreSQL data-directory path passed to
            ``pg_ctl reload -D``.

    Returns:
        None.

    Side effects:
        Spawns the ``pg_ctl`` subprocess; prints status/warnings.
    """
    bin_dir = find_pg_bin_dir()
    if bin_dir:
        pg_ctl = os.path.join(bin_dir, 'pg_ctl.exe')
        result = subprocess.run(
            [pg_ctl, 'reload', '-D', data_dir],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f'Warning: pg_ctl reload exited with code {result.returncode}')
            print(result.stderr)
        else:
            print('PostgreSQL configuration reloaded.')
    else:
        print('Warning: could not find pg_ctl. Reload PostgreSQL manually.')


def enable_trust_auth(hba_path):
    """Prepend temporary trust-auth rules to ``pg_hba.conf``.

    Inserts a marked block (``local`` + IPv4/IPv6 ``host`` trust lines)
    at the top of the file so the setup script can connect as
    ``postgres`` without a password; the block is removed afterwards by
    :func:`remove_trust_auth`.

    Args:
        hba_path (str): Path to ``pg_hba.conf``.

    Returns:
        None.

    Side effects:
        Rewrites ``pg_hba.conf`` (takes effect after ``reload_pg``).
    """
    trust_lines = (
        '# --- LMS Setup: temporary trust auth ---\n'
        'local all all trust\n'
        'host all all 127.0.0.1/32 trust\n'
        'host all all ::1/128 trust\n'
        '# --- end temporary trust auth ---\n'
    )
    with open(hba_path, 'r') as f:
        content = f.read()
    with open(hba_path, 'w') as f:
        f.write(trust_lines + content)


def remove_trust_auth(hba_path):
    """Remove the temporary trust-auth block from ``pg_hba.conf``.

    Drops every line between (and including) the
    ``--- LMS Setup: temporary trust auth ---`` markers written by
    :func:`enable_trust_auth`, restoring the file's original rules.

    Args:
        hba_path (str): Path to ``pg_hba.conf``.

    Returns:
        None.

    Side effects:
        Rewrites ``pg_hba.conf`` (takes effect after ``reload_pg``).
    """
    with open(hba_path, 'r') as f:
        lines = f.readlines()
    filtered = []
    skip = False
    for line in lines:
        if '# --- LMS Setup: temporary trust auth ---' in line:
            skip = True
            continue
        if '# --- end temporary trust auth ---' in line:
            skip = False
            continue
        if not skip:
            filtered.append(line)
    with open(hba_path, 'w') as f:
        f.writelines(filtered)


def update_env(db_url):
    """Write ``DATABASE_URL`` into the project ``.env`` file.

    Replaces the existing ``DATABASE_URL=`` line when present,
    otherwise appends it; prints a manual-setup hint when no ``.env``
    file exists instead of creating one.

    Args:
        db_url (str): Full SQLAlchemy/psycopg2 connection URL, e.g.
            ``postgresql://postgres:postgres@localhost:5432/library_db``.

    Returns:
        None.

    Side effects:
        Rewrites ``.env``; prints a confirmation or manual hint.
    """
    line = f'DATABASE_URL={db_url}\n'
    if os.path.isfile(ENV_FILE):
        with open(ENV_FILE, 'r') as f:
            content = f.read()
        pattern = r'^DATABASE_URL=.*\n?'
        if re.search(pattern, content, re.MULTILINE):
            content = re.sub(pattern, line, content, flags=re.MULTILINE)
        else:
            content += '\n' + line
        with open(ENV_FILE, 'w') as f:
            f.write(content)
        print(f'Updated {ENV_FILE} with DATABASE_URL.')
    else:
        print(f'{ENV_FILE} not found. Set DATABASE_URL={db_url} manually.')


def main():
    """Run the one-shot local database bootstrap.

    Backs up ``pg_hba.conf``, enables temporary trust auth, sets the
    ``postgres`` password, drops/recreates ``library_db``, applies
    ``app/schema.sql`` (tables + role seed), restores ``pg_hba.conf``
    and reloads, then writes ``DATABASE_URL`` to ``.env``. On any
    failure the original ``pg_hba.conf`` is restored and the process
    exits non-zero.

    Returns:
        None.

    Side effects:
        Rewrites ``pg_hba.conf`` (temporarily), manages the
        ``library_db`` database, writes ``.env``, prints progress.
    """
    data_dir = find_pg_data_dir()
    if not data_dir:
        print('Could not find PostgreSQL data directory.')
        print('Make sure PostgreSQL is installed at C:\\Program Files\\PostgreSQL\\18\\')
        sys.exit(1)

    hba_path = os.path.join(data_dir, 'pg_hba.conf')
    bak_path = hba_path + '.setup.bak'

    print(f'PostgreSQL data directory: {data_dir}')
    print(f'pg_hba.conf: {hba_path}')

    # Backup original pg_hba.conf
    shutil.copy2(hba_path, bak_path)
    print('Backed up pg_hba.conf → pg_hba.conf.setup.bak')

    # Enable trust auth
    enable_trust_auth(hba_path)
    print('Added temporary trust authentication rules.')

    # Reload PostgreSQL
    reload_pg(data_dir)

    # Connect and set up
    import psycopg2
    from psycopg2 import sql as psql

    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='postgres',
            dbname='postgres'
        )
        conn.autocommit = True
        cur = conn.cursor()
        print('Connected to PostgreSQL (trust auth).')

        # Set password
        cur.execute(psql.SQL("ALTER USER postgres WITH PASSWORD %s"), [DB_PASSWORD])
        print(f'Password for postgres user set to: {DB_PASSWORD}')

        # Drop database if exists, then recreate
        cur.execute(
            psql.SQL("SELECT pg_terminate_backend(pg_stat_activity.pid) "
                     "FROM pg_stat_activity "
                     "WHERE pg_stat_activity.datname = %s "
                     "AND pid <> pg_backend_pid()"),
            [DB_NAME]
        )
        cur.execute(psql.SQL("DROP DATABASE IF EXISTS {}").format(psql.Identifier(DB_NAME)))
        cur.execute(psql.SQL("CREATE DATABASE {}").format(psql.Identifier(DB_NAME)))
        print(f'Database {DB_NAME} dropped and recreated.')

        cur.close()
        conn.close()

        # Connect to the new database
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password=DB_PASSWORD,
            dbname=DB_NAME
        )
        conn.autocommit = True
        cur = conn.cursor()
        print(f'Connected to {DB_NAME}.')

        # Run schema.sql
        if os.path.isfile(SCHEMA_FILE):
            with open(SCHEMA_FILE, 'r') as f:
                schema_sql = f.read()
            cur.execute(schema_sql)
            print('Schema created successfully (all tables + seed data).')
        else:
            print(f'Warning: {SCHEMA_FILE} not found. Skipping schema creation.')

        cur.close()
        conn.close()

    except Exception as e:
        print(f'Error during setup: {e}')
        print('Restoring original pg_hba.conf...')
        shutil.copy2(bak_path, hba_path)
        remove_trust_auth(hba_path)
        reload_pg(data_dir)
        sys.exit(1)

    # Restore original pg_hba.conf
    remove_trust_auth(hba_path)
    os.remove(bak_path)
    print('Restored original pg_hba.conf (removed temporary rules).')

    # Reload PostgreSQL
    reload_pg(data_dir)

    # Update .env
    db_url = f'postgresql://postgres:{DB_PASSWORD}@localhost:5432/{DB_NAME}'
    update_env(db_url)

    print('\n=== Setup complete! ===')
    print(f'Database: {DB_NAME}')
    print(f'Username: postgres')
    print(f'Password: {DB_PASSWORD}')
    print(f'URL: {db_url}')
    print('\nYou can now run: python run.py')


if __name__ == '__main__':
    main()
