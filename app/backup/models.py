from app.database import db


# Tuple contract (SELECT column order — callers index by position):
#   (backup_id, filename, size_bytes, status, backup_type, error_msg, created_at)


def log_backup(filename, size_bytes=None, backup_type='manual',
               status='completed', error_msg=None):
    """Record a backup run. Returns the new backup_id (or None)."""
    row = db.fetch_one(
        '''INSERT INTO backup_log (filename, size_bytes, status, backup_type, error_msg)
           VALUES (%s, %s, %s, %s, %s) RETURNING backup_id''',
        (filename, size_bytes, status, backup_type, error_msg)
    )
    return row[0] if row else None


def get_backup_logs(limit=None):
    """Newest-first backup history rows."""
    query = (
        'SELECT backup_id, filename, size_bytes, status, backup_type, error_msg, created_at'
        ' FROM backup_log ORDER BY created_at DESC'
    )
    if limit is not None:
        return db.fetch_all(query + ' LIMIT %s', (limit,))
    return db.fetch_all(query)


def get_in_progress_backup():
    """Newest backup row still running, or None.

    Used as the concurrency guard: only one backup/restore runs at a time.
    """
    return db.fetch_one(
        'SELECT backup_id, filename, size_bytes, status, backup_type, error_msg, created_at'
        ' FROM backup_log WHERE status = %s ORDER BY created_at DESC',
        ('in_progress',)
    )


def update_backup_status(backup_id, status, filename=None, size_bytes=None,
                         error_msg=None):
    """Update a backup row's outcome. Returns the updated rowcount."""
    sets = ['status = %s']
    params = [status]
    if filename is not None:
        sets.append('filename = %s')
        params.append(filename)
    if size_bytes is not None:
        sets.append('size_bytes = %s')
        params.append(size_bytes)
    if error_msg is not None:
        sets.append('error_msg = %s')
        params.append(error_msg)
    params.append(backup_id)
    return db.execute(
        f"UPDATE backup_log SET {', '.join(sets)} WHERE backup_id = %s",
        tuple(params)
    )


def get_backup_by_id(backup_id):
    """Single backup row by id, or None."""
    return db.fetch_one(
        'SELECT backup_id, filename, size_bytes, status, backup_type, error_msg, created_at'
        ' FROM backup_log WHERE backup_id = %s',
        (backup_id,)
    )


def get_stale_backups(keep_n):
    """Rows beyond the newest `keep_n` (candidates for retention deletion)."""
    return db.fetch_all(
        'SELECT backup_id, filename, size_bytes, status, backup_type, error_msg, created_at'
        ' FROM backup_log ORDER BY created_at DESC OFFSET %s',
        (keep_n,)
    )


def delete_backup_row(backup_id):
    db.execute('DELETE FROM backup_log WHERE backup_id = %s', (backup_id,))
