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
    """Locate PostgreSQL data directory."""
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
    """Locate PostgreSQL bin directory from the data dir path."""
    data_dir = find_pg_data_dir()
    if not data_dir:
        return None
    pg_root = os.path.dirname(data_dir)
    bin_dir = os.path.join(pg_root, 'bin')
    if os.path.isdir(bin_dir):
        return bin_dir
    return None


def reload_pg(data_dir):
    """Reload PostgreSQL configuration."""
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
    """Add trust auth rules at the top of pg_hba.conf."""
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
    """Remove the temporary trust auth lines from pg_hba.conf."""
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
    """Update or add DATABASE_URL in .env."""
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
