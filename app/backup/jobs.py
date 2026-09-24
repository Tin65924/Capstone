"""Background backup/restore workers.

The request that starts a backup or restore returns immediately (flash +
redirect) while the heavy pg_dump/psql work runs on a daemon thread — the
page never blocks. Progress is tracked in the database, not a modal: the
worker inserts nothing itself; the route pre-inserts an ``in_progress``
backup_log row and the worker flips it to ``completed``/``failed`` when
done, so the history table itself shows "In Progress" until then.

Same pattern as the cataloging bulk-import worker: background thread +
in-memory dict, no task queue (jobs are lost on restart; a stale
``in_progress`` row is reaped by the next request's guard).
"""

import logging
import threading
import time
import uuid

from app.auth.models import log_activity

from .models import (
    get_backup_by_id,
    log_backup,
    update_backup_status,
)
from .scheduler import apply_retention
from .utils import create_backup, restore_backup

log = logging.getLogger(__name__)

_jobs = {}
_jobs_lock = threading.Lock()

_JOB_TTL = 3600  # finished jobs are pruned after an hour
_FINISHED_BANNER_AGE = 600  # recent results surface as a page banner (seconds)

TERMINAL_STATES = ('done', 'failed')


def start_job(kind, label, user_id, backup_id=None):
    """Register a job and return its id. Prunes stale finished jobs."""
    now = time.time()
    job_id = uuid.uuid4().hex
    with _jobs_lock:
        stale = [jid for jid, job in _jobs.items()
                 if job['status'] in TERMINAL_STATES
                 and now - job['updated_at'] > _JOB_TTL]
        for jid in stale:
            del _jobs[jid]
        _jobs[job_id] = {
            'job_id': job_id,
            'kind': kind,
            'label': label,
            'user_id': user_id,
            'backup_id': backup_id,
            'status': 'running',
            'filename': None,
            'error': None,
            'updated_at': now,
        }
    return job_id


def active_job():
    """The currently running job, if any (only one at a time)."""
    with _jobs_lock:
        for job in _jobs.values():
            if job['status'] not in TERMINAL_STATES:
                return dict(job)
    return None


def recent_finished_job(max_age=_FINISHED_BANNER_AGE):
    """Most recent terminal job within `max_age` seconds, else None."""
    now = time.time()
    with _jobs_lock:
        finished = [j for j in _jobs.values()
                    if j['status'] in TERMINAL_STATES
                    and now - j['updated_at'] <= max_age]
    if not finished:
        return None
    return dict(max(finished, key=lambda j: j['updated_at']))


def _finish(job_id, app, status, filename=None, error=None):
    with _jobs_lock:
        job = _jobs.get(job_id)
        if not job:
            return
        job['status'] = status
        job['filename'] = filename
        job['error'] = error
        job['updated_at'] = time.time()
    if app is not None:
        app.logger.info('backup job %s %s: %s', job_id, status,
                        filename or error)


def run_backup_job(app, job_id, backup_id, user_id, keep_n):
    """Worker body: pg_dump, then flip the in_progress row. Never raises out."""
    with app.app_context():
        try:
            filename, size_bytes = create_backup()
        except Exception as e:  # noqa: BLE001 — failure is a row update
            update_backup_status(backup_id, 'failed',
                                 error_msg=str(e)[:500])
            log_activity(user_id, 'backup:failed:manual')
            _finish(job_id, app, 'failed', error=str(e)[:500])
            return
        update_backup_status(backup_id, 'completed', filename=filename,
                             size_bytes=size_bytes)
        try:
            apply_retention(app, keep_n)
        except Exception:  # noqa: BLE001 — retention must not fail the job
            app.logger.exception('Backup retention failed for %s', filename)
        log_activity(user_id, f'backup:created:{filename}')
        _finish(job_id, app, 'done', filename=filename)


def run_restore_job(app, job_id, user_id, backup_id, filename):
    """Worker body: safety snapshot, then atomic replace. Never raises out."""
    with app.app_context():
        row = get_backup_by_id(backup_id)
        if not row or row[3] != 'completed':
            log_activity(user_id, f'backup:restore_aborted:{filename}')
            _finish(job_id, app, 'failed',
                    error='Only completed backups can be restored.')
            return
        try:
            safety_file, safety_size = create_backup()
            log_backup(safety_file, safety_size, backup_type='manual',
                       status='completed', error_msg='pre-restore auto-backup')
        except Exception as e:  # noqa: BLE001 — no safety net, refuse restore
            log_activity(user_id, f'backup:restore_aborted:{filename}')
            _finish(job_id, app, 'failed',
                    error=f'Could not snapshot current data: {e}')
            return
        try:
            restore_backup(filename)
        except Exception as e:  # noqa: BLE001 — safety backup is recovery point
            log_activity(user_id, f'backup:restore_failed:{filename}')
            _finish(job_id, app, 'failed',
                    error=f'{e}. Current data was snapshotted as {safety_file}.')
            return
        log_activity(user_id, f'backup:restored:{filename}')
        _finish(job_id, app, 'done', filename=filename)
