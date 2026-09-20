import os

_scheduler = None


def run_scheduled_backup(app):
    """Monthly job body: backup + log + retention. Failures become 'failed' rows."""
    with app.app_context():
        from .models import log_backup, delete_backup_row, get_stale_backups
        from .utils import create_backup, resolve_backup_path
        from app.auth.models import log_system_event

        keep_n = app.config.get('BACKUP_KEEP', 12)
        try:
            filename, size_bytes = create_backup()
        except Exception as e:  # noqa: BLE001 — must not raise out of the scheduler
            app.logger.exception('Scheduled backup failed')
            log_backup(
                filename='scheduled_backup_failed.sql',
                backup_type='scheduled',
                status='failed',
                error_msg=str(e)[:500],
            )
            try:
                log_system_event('system:scheduled_backup:failed')
            except Exception:  # noqa: BLE001 — audit must never break the job
                app.logger.exception('Scheduled backup audit row failed')
            return
        log_backup(filename, size_bytes, backup_type='scheduled', status='completed')
        try:
            log_system_event(f'system:scheduled_backup:completed:{filename}')
        except Exception:  # noqa: BLE001 — audit must never break the job
            app.logger.exception('Scheduled backup audit row failed')
        _apply_retention(app, keep_n)


def _apply_retention(app, keep_n):
    from .models import delete_backup_row, get_stale_backups
    from .utils import resolve_backup_path

    try:
        stale = get_stale_backups(keep_n)
    except Exception:  # noqa: BLE001 — retention must never break the request/job
        app.logger.exception('Backup retention lookup failed')
        return
    for row in stale or []:
        backup_id, filename = row[0], row[1]
        try:
            path = resolve_backup_path(filename)
            if os.path.isfile(path):
                os.remove(path)
        except Exception:  # noqa: BLE001 — keep deleting other rows
            app.logger.exception('Failed to delete stale backup file %s', filename)
            continue
        try:
            delete_backup_row(backup_id)
        except Exception:  # noqa: BLE001
            app.logger.exception('Failed to delete stale backup row %s', backup_id)


def apply_retention(app, keep_n):
    """Retention helper shared by routes (public for testing)."""
    _apply_retention(app, keep_n)


def _clamp_int(app, name, value, lo, hi, default):
    """Coerce a schedule value to int and clamp into range (warn on fix-up)."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        app.logger.warning(
            'Invalid %s=%r — falling back to %s.', name, value, default)
        return default
    if number < lo or number > hi:
        app.logger.warning(
            'Out-of-range %s=%r — clamping to %d..%d.', name, value, lo, hi)
        return max(lo, min(hi, number))
    return number


def reschedule(app):
    """Apply the current BACKUP_DAY/HOUR to the running monthly job.

    Called after admin settings updates so edits take effect without a
    restart. No-op when the scheduler isn't running (tests, fresh boot
    before start). Returns True when a job was rescheduled.
    """
    global _scheduler
    sched = _scheduler
    if sched is None or not getattr(sched, 'running', False):
        return False
    try:
        job = sched.get_job('monthly_backup')
    except Exception:  # noqa: BLE001 — never break a settings save
        app.logger.exception('Backup reschedule lookup failed')
        return False
    if job is None:
        return False
    day = _clamp_int(app, 'BACKUP_DAY', app.config.get('BACKUP_DAY', 1), 1, 28, 1)
    hour = _clamp_int(app, 'BACKUP_HOUR', app.config.get('BACKUP_HOUR', 2), 0, 23, 2)
    job.reschedule(trigger='cron', day=day, hour=hour, minute=0)
    app.logger.info('Backup schedule updated (monthly: day=%s hour=%s).', day, hour)
    return True


def next_scheduled_backup(day, hour, now=None):
    """Next automatic-backup datetime after `now` for a monthly day/hour.

    Day is clamped to 1..28 (same rule as the scheduler) so it is valid
    in every month; a passed this-month slot rolls to next month.
    """
    from datetime import datetime
    now = now or datetime.now()
    try:
        day = max(1, min(28, int(day)))
    except (TypeError, ValueError):
        day = 1
    try:
        hour = max(0, min(23, int(hour)))
    except (TypeError, ValueError):
        hour = 2
    candidate = now.replace(day=day, hour=hour, minute=0, second=0,
                            microsecond=0)
    if candidate <= now:
        if now.month == 12:
            candidate = candidate.replace(year=now.year + 1, month=1)
        else:
            candidate = candidate.replace(month=now.month + 1)
    return candidate


def start_scheduler(app):
    """Start the monthly APScheduler cron job. No-op in tests / if running.

    Note: the scheduler is in-process, so it assumes a single worker. Under
    multiple workers each process would run its own monthly backup.
    """
    global _scheduler
    if app.config.get('TESTING'):
        return None
    if _scheduler is not None and _scheduler.running:
        return _scheduler

    # Avoid double-start under the Werkzeug reloader (only the child serves).
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'false':
        return None

    from apscheduler.schedulers.background import BackgroundScheduler

    # Day clamped to 1..28 so the job fires every month (29-31 skip months);
    # a typo'd env var must never silently disable backups.
    day = _clamp_int(app, 'BACKUP_DAY', app.config.get('BACKUP_DAY', 1), 1, 28, 1)
    hour = _clamp_int(app, 'BACKUP_HOUR', app.config.get('BACKUP_HOUR', 2), 0, 23, 2)
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        lambda: run_scheduled_backup(app),
        'cron',
        day=day,
        hour=hour,
        minute=0,
        id='monthly_backup',
        replace_existing=True,
    )
    _scheduler.start()
    app.logger.info('Backup scheduler started (monthly: day=%s hour=%s).', day, hour)
    return _scheduler
