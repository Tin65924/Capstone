import subprocess
import os
from datetime import datetime
from flask import current_app


BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'backups')


def create_backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'library_backup_{timestamp}.sql'
    filepath = os.path.join(BACKUP_DIR, filename)

    db_url = current_app.config['DATABASE_URL']
    cmd = f'pg_dump "{db_url}" > "{filepath}"'
    subprocess.run(cmd, shell=True, check=True)
    return filename
