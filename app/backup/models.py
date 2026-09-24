from app.database import db

import logging

log = logging.getLogger(__name__)


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
