from app.database import db

import logging

log = logging.getLogger(__name__)


# Tuple contract (SELECT column order — callers index by position):
#   (backup_id, filename, size_bytes, status, backup_type, error_msg, created_at)


def log_backup(filename, size_bytes=None, backup_type='manual',
               status='completed', error_msg=None):
    """Record a backup run row and return its new id.

    Inserts into ``backup_log`` with the file metadata, run type
    (manual/scheduled), outcome status, and optional error text. Used
    for finished runs, pre-inserted ``in_progress`` rows, and scheduled
    failures. The filename uses the timestamped ``library_backup_*``
    convention; failed scheduled runs use a sentinel name.

    Args:
        filename: Dump filename inside BACKUP_DIR (or sentinel).
        size_bytes: File size in bytes, or None when unknown/failed.
        backup_type: ``'manual'`` or ``'scheduled'``.
        status: ``'completed'``, ``'failed'``, or ``'in_progress'``.
        error_msg: Truncated failure text, or None on success.

    Returns:
        New backup_id integer, or None if the INSERT returned nothing.
    """
    row = db.fetch_one(
        '''INSERT INTO backup_log (filename, size_bytes, status, backup_type, error_msg)
           VALUES (%s, %s, %s, %s, %s) RETURNING backup_id''',
        (filename, size_bytes, status, backup_type, error_msg)
    )
    return row[0] if row else None


def get_backup_logs(limit=None):
    """Fetch backup history rows newest-first for the admin table.

    Returns the full tuple contract (backup_id, filename, size_bytes,
    status, backup_type, error_msg, created_at) ordered by created_at
    DESC. Powers the backup history table, retention scans, and the
    pre-restore history snapshot. An optional limit bounds the page.

    Args:
        limit: Maximum rows to return, or None for all history.

    Returns:
        List of 7-tuples newest-first (possibly empty).
    """
    query = (
        'SELECT backup_id, filename, size_bytes, status, backup_type, error_msg, created_at'
        ' FROM backup_log ORDER BY created_at DESC'
    )
    if limit is not None:
        return db.fetch_all(query + ' LIMIT %s', (limit,))
    return db.fetch_all(query)


def get_in_progress_backup():
    """Fetch the newest still-running backup row, or None.

    Newest backup row still running, or None. Used as the concurrency guard:
    only one backup/restore runs at a time. The routes layer age-checks
    the row (stale ``in_progress`` rows from a dead worker are flipped
    to failed) before refusing new work.

    Returns:
        7-tuple (backup_id, filename, size_bytes, status, backup_type,
        error_msg, created_at) for the newest ``in_progress`` row, or
        None when no worker is running.
    """
    return db.fetch_one(
        'SELECT backup_id, filename, size_bytes, status, backup_type, error_msg, created_at'
        ' FROM backup_log WHERE status = %s ORDER BY created_at DESC',
        ('in_progress',)
    )


def update_backup_status(backup_id, status, filename=None, size_bytes=None,
                         error_msg=None):
    """Update a backup row's outcome fields and return the rowcount.

    Always sets ``status``; optionally overwrites the placeholder
    filename with the real dump name, records the file size, and stores
    a truncated error message. Used by workers to flip ``in_progress``
    rows to ``completed``/``failed`` and by the stale-row reaper.

    Args:
        backup_id: Target backup_log row.
        status: New status (``completed``/``failed``/``in_progress``).
        filename: Real dump filename to store, or None to keep.
        size_bytes: File size to store, or None to keep.
        error_msg: Failure text to store, or None to keep.

    Returns:
        Rowcount from the UPDATE.
    """
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
    """Fetch a single backup row by primary key, or None.

    Returns the full 7-tuple contract for download/restore/delete
    pre-checks (existence, ``completed`` status, filename). Callers
    treat a None result as "Backup not found" and redirect with a flash
    instead of touching the filesystem.

    Args:
        backup_id: Primary key of the backup_log row.

    Returns:
        7-tuple (backup_id, filename, size_bytes, status, backup_type,
        error_msg, created_at), or None when missing.
    """
    return db.fetch_one(
        'SELECT backup_id, filename, size_bytes, status, backup_type, error_msg, created_at'
        ' FROM backup_log WHERE backup_id = %s',
        (backup_id,)
    )


def get_stale_backups(keep_n):
    """Fetch rows beyond the newest keep_n for retention deletion.

    Orders history newest-first and offsets past the ``keep_n`` rows to
    keep, so everything returned is a deletion candidate (oldest
    first among the stale set by position). The retention worker then
    filters to ``completed`` rows only and removes both file and row.

    Args:
        keep_n: Number of newest history rows to retain.

    Returns:
        List of 7-tuples beyond the retention window (possibly empty).
    """
    return db.fetch_all(
        'SELECT backup_id, filename, size_bytes, status, backup_type, error_msg, created_at'
        ' FROM backup_log ORDER BY created_at DESC OFFSET %s',
        (keep_n,)
    )


def delete_backup_row(backup_id):
    """Delete one backup history row by primary key.

    Used by retention cleanup after the dump file is removed from disk,
    and by the delete-backup route. Only completed rows with real files
    are candidates — in_progress and failed rows are never touched.

    Args:
        backup_id: Backup_log row to delete.
    """
    db.execute('DELETE FROM backup_log WHERE backup_id = %s', (backup_id,))


def reinsert_backup_row(filename, size_bytes, status, backup_type,
                        error_msg, created_at):
    """Re-record one backup history row wiped by a restore.

    Keeps the original metadata (including created_at) so history order
    is unchanged. Returns the db.execute result.
    """
    return db.execute(
        '''INSERT INTO backup_log
           (filename, size_bytes, status, backup_type, error_msg, created_at)
           VALUES (%s, %s, %s, %s, %s, %s)''',
        (filename, size_bytes, status, backup_type, error_msg, created_at)
    )


def preserve_backup_history():
    """Snapshot backup_log rows before a restore.

    A restore replays a full pg_dump, so backup_log reverts to the
    backup-time state and every row logged since (newer backups, the
    just-taken safety snapshot) would otherwise vanish. Returns the
    snapshot (possibly empty) — never raises.
    """
    try:
        return list(get_backup_logs() or [])
    except Exception:
        log.exception('Could not snapshot backup history before restore')
        return []


def reconcile_backup_history(preserved):
    """Re-record rows wiped by a restore. Returns the failure count.

    Rows whose filename already exists (dump-time rows survive the
    restore) are skipped. Never raises: the data replace already
    happened, so a bookkeeping failure is logged loudly instead of
    failing the restore.
    """
    if not preserved:
        return 0
    try:
        existing = {row[1] for row in get_backup_logs() or []}
    except Exception:
        log.exception('Could not read backup history after restore; '
                      '%d row(s) not re-recorded', len(preserved))
        return len(preserved)
    failed = 0
    for row in preserved:
        try:
            if len(row) < 7:
                raise ValueError(f'malformed history row: {row!r}')
            if row[1] in existing:
                continue
            reinsert_backup_row(row[1], row[2], row[3], row[4], row[5],
                                row[6])
        except Exception:
            log.exception('Could not re-record backup history row %r',
                          row[1] if len(row) > 1 else row)
            failed += 1
    return failed
