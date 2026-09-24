"""Background backup/restore jobs with pollable progress.

pg_dump/psql report no percentage, so jobs move through labelled stages
while the blocking subprocess call runs, and a ticker nudges the bar
forward (capped per stage) so the UI visibly progresses until the process
completes. Same pattern as the cataloging bulk-import worker: background
thread + in-memory dict, no task queue (jobs are lost on restart).
"""

import logging
import threading
import time
import uuid

from app.auth.models import log_activity

from .models import get_backup_by_id, log_backup
from .scheduler import apply_retention
from .utils import create_backup, restore_backup

log = logging.getLogger(__name__)

_jobs = {}
_jobs_lock = threading.Lock()

_TICK_INTERVAL = 0.4  # seconds between progress nudges
_TICK_STEP = 3  # percent per nudge (capped at the stage ceiling)
_JOB_TTL = 3600  # finished jobs are pruned after an hour

TERMINAL_STATES = ('done', 'failed')


def start_job(kind, label, user_id):
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
            'status': 'queued',
            'stage': 'Waiting to start…',
            'history': ['Waiting to start…'],
            'progress': 0,
            'filename': None,
            'error': None,
            'updated_at': now,
        }
    return job_id


def active_job():
    """The currently queued/running job, if any (only one at a time)."""
    with _jobs_lock:
        for job in _jobs.values():
            if job['status'] not in TERMINAL_STATES:
                return dict(job)
    return None


def get_job(job_id):
    """A snapshot of the job dict, or None for unknown ids."""
    with _jobs_lock:
        job = _jobs.get(job_id)
        return dict(job) if job else None


def _set(job_id, app=None, **fields):
    with _jobs_lock:
        job = _jobs.get(job_id)
        if not job:
            return
        if 'stage' in fields and fields['stage'] != job['stage']:
            job['history'].append(fields['stage'])
        job.update(fields)
        job['updated_at'] = time.time()
    if app is not None and 'stage' in fields:
        app.logger.info('backup job %s: %s', job_id, fields['stage'])


def _ticker(job_id, cap, stop_event):
    """Nudge progress toward `cap` while the blocking call runs."""
    while not stop_event.wait(_TICK_INTERVAL):
        with _jobs_lock:
            job = _jobs.get(job_id)
            if not job or job['status'] != 'running':
                return
            if job['progress'] < cap:
                job['progress'] = min(cap, job['progress'] + _TICK_STEP)
                job['updated_at'] = time.time()


def _run_with_ticker(job_id, cap, func, *args):
    stop = threading.Event()
    ticker = threading.Thread(target=_ticker, args=(job_id, cap, stop),
                              daemon=True)
    ticker.start()
    try:
        return func(*args)
    finally:
        stop.set()
        ticker.join()


def run_backup_job(app, job_id, user_id, keep_n):
    """Worker body: pg_dump + log + retention. Never raises out."""
    with app.app_context():
        _set(job_id, app, status='running',
             stage='Starting backup…', progress=3)
        _set(job_id, app, stage='Looking for database tools…', progress=8)
        _set(job_id, app, stage='Dumping database…', progress=15)
        try:
            filename, size_bytes = _run_with_ticker(
                job_id, 90, create_backup)
        except Exception as e:  # noqa: BLE001 — failure is a job result
            log_backup(filename='manual_backup_failed.sql',
                       backup_type='manual', status='failed',
                       error_msg=str(e)[:500])
            log_activity(user_id, 'backup:failed:manual')
            _set(job_id, app, status='failed', stage='Backup failed.',
                 error=str(e)[:500])
            return
        _set(job_id, app, stage=f'Saving {filename}…', progress=92)
        log_backup(filename, size_bytes, backup_type='manual',
                   status='completed')
        try:
            apply_retention(app, keep_n)
        except Exception:  # noqa: BLE001 — retention must not fail the job
            app.logger.exception('Backup retention failed for %s', filename)
        log_activity(user_id, f'backup:created:{filename}')
        _set(job_id, app, status='done', stage='Backup complete.',
             progress=100, filename=filename)


def run_restore_job(app, job_id, user_id, backup_id, filename):
    """Worker body: safety snapshot, then atomic replace. Never raises out."""
    with app.app_context():
        _set(job_id, app, status='running',
             stage=f'Looking for {filename}…', progress=3)
        row = get_backup_by_id(backup_id)
        if not row or row[3] != 'completed':
            _set(job_id, app, status='failed',
                 stage='Restore refused.',
                 error='Only completed backups can be restored.')
            return
        _set(job_id, app,
             stage='Snapshotting current data (safety backup)…', progress=8)
        try:
            safety_file, safety_size = _run_with_ticker(
                job_id, 25, create_backup)
            log_backup(safety_file, safety_size, backup_type='manual',
                       status='completed', error_msg='pre-restore auto-backup')
        except Exception as e:  # noqa: BLE001 — no safety net, refuse restore
            log_activity(user_id, f'backup:restore_aborted:{filename}')
            _set(job_id, app, status='failed', stage='Restore aborted.',
                 error=f'Could not snapshot current data: {e}')
            return
        _set(job_id, app,
             stage=f'Safety snapshot saved as {safety_file}.', progress=28)
        _set(job_id, app, stage=f'Restoring {filename}…', progress=32)
        try:
            _run_with_ticker(job_id, 90, restore_backup, filename)
        except Exception as e:  # noqa: BLE001 — safety backup is recovery point
            log_activity(user_id, f'backup:restore_failed:{filename}')
            _set(job_id, app, status='failed', stage='Restore failed.',
                 error=f'{e}. Current data was snapshotted as {safety_file}.')
            return
        _set(job_id, app, stage='Finalizing restore…', progress=95)
        log_activity(user_id, f'backup:restored:{filename}')
        _set(job_id, app, status='done',
             stage='Restore complete — the database was replaced.',
             progress=100, filename=filename)
