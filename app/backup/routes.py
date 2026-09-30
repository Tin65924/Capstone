import os
import threading
from datetime import datetime, timedelta, timezone

from flask import current_app, flash, jsonify, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required

from app.auth.decorators import admin_required
from app.auth.models import log_activity
from app.settings.models import is_restore_enabled

from . import backup_bp
from . import jobs
from .models import (
    delete_backup_row,
    get_backup_by_id,
    get_backup_logs,
    get_in_progress_backup,
    log_backup,
    update_backup_status,
)
from .utils import resolve_backup_path

_RESTORE_DISABLED_MSG = ('Backup restore is disabled — '
                         'turn it on in Library Settings to restore.')

# An in_progress row older than this is presumed orphaned (the worker died
# with the process, e.g. a restart) — the next request marks it failed so
# backups are never blocked forever.
_STALE_IN_PROGRESS_AGE = timedelta(hours=2)


def _live_in_progress():
    """Newest in_progress row that is still fresh, else None.

    Stale rows are flipped to failed so a dead worker never blocks backups.
    """
    row = get_in_progress_backup()
    if not row or len(row) < 7:
        # No row, or a malformed one we cannot age-check: stay safe and
        # treat it as busy rather than starting a second worker.
        return row
    created = row[6]
    try:
        if isinstance(created, str):
            created = datetime.fromisoformat(created)
        if getattr(created, 'tzinfo', None) is None:
            created = created.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) - created > _STALE_IN_PROGRESS_AGE:
            update_backup_status(row[0], 'failed',
                                 error_msg='Worker did not finish (stale in-progress run).')
            return None
    except Exception:  # noqa: BLE001 — unparseable timestamp: stay safe
        current_app.logger.exception('Could not age-check in-progress backup %s', row[0])
        return row
    return row


def _busy_kind():
    """'backup'/'restore' while a worker runs, else None.

    Backups pre-insert an in_progress history row; restores do not (only
    the in-memory job exists until the safety snapshot lands), so the
    caller needs the kind to describe progress truthfully.
    """
    job = jobs.active_job()
    if job is not None:
        return job.get('kind') or 'backup'
    if _live_in_progress() is not None:
        return 'backup'
    return None


def _busy():
    """True while a backup/restore worker is running (memory or DB row)."""
    return _busy_kind() is not None


def _backup_stats(logs):
    def _status(row):
        try:
            return row[3]
        except (IndexError, TypeError):
            return None

    def _size(row):
        try:
            return int(row[2] or 0)
        except (IndexError, TypeError, ValueError):
            return 0

    def _created(row):
        try:
            return row[6]
        except (IndexError, TypeError):
            return None

    completed = [row for row in logs if _status(row) == 'completed']
    total_size = sum(_size(row) for row in completed)
    # The newest row may be an in_progress run — health is about the newest
    # *finished* backup, so look at completed rows only.
    last = completed[0] if completed else None
    # Healthy only when the newest run succeeded and is recent — a failed
    # latest run must show Warning, never Healthy.
    healthy = False
    if last and _status(last) == 'completed' and _created(last):
        created = _created(last)
        if getattr(created, 'tzinfo', None) is None:
            try:
                created = created.replace(tzinfo=timezone.utc)
            except (AttributeError, TypeError, ValueError):
                created = None
        if created is not None:
            healthy = (datetime.now(timezone.utc) - created) <= timedelta(days=35)
    return {
        'count': len(completed),
        'total_size': total_size,
        'last': last,
        'healthy': healthy,
    }


def _pad_backup_row(row, width=7):
    """Pad short/legacy backup rows so positional template reads never crash."""
    try:
        items = list(row)
    except TypeError:
        return (None,) * width
    if len(items) < width:
        items = items + [None] * (width - len(items))
    return tuple(items)


@backup_bp.route('/admin/backup')
@login_required
@admin_required
def backup_page():
    logs = [_pad_backup_row(row) for row in (get_backup_logs() or [])]
    stats = _backup_stats(logs or [])
    recovery_events = [row for row in (logs or [])
                       if len(row) > 3 and row[3] == 'failed'][:10]
    keep_n = current_app.config.get('BACKUP_KEEP', 12)
    busy_kind = _busy_kind()
    busy = busy_kind is not None
    last_job = None if busy else jobs.recent_finished_job()
    return render_template(
        'backup/backup.html',
        backups=logs or [],
        stats=stats,
        recovery_events=recovery_events,
        keep_n=keep_n,
        busy=busy,
        busy_kind=busy_kind,
        last_job=last_job,
        restore_enabled=is_restore_enabled(),
        # One-shot signal: the restore POST redirects here with the
        # filename so the outcome modal opens exactly once (JS strips
        # the query before the busy auto-refresh fires).
        restore_started=request.args.get('restore_started'),
    )


@backup_bp.route('/admin/backup/create', methods=['POST'])
@login_required
@admin_required
def create_backup_route():
    """Start a backup on a background thread and return immediately.

    The history table shows the new row as In Progress until the worker
    flips it to completed/failed — the request never waits for pg_dump.
    """
    if _busy():
        flash('A backup or restore is already running — '
              'wait for it to finish first.', 'error')
        return redirect(url_for('backup.backup_page'))
    keep_n = current_app.config.get('BACKUP_KEEP', 12)
    placeholder = f"library_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_in_progress.sql"
    backup_id = log_backup(placeholder, None, backup_type='manual',
                           status='in_progress')
    if not backup_id:
        flash('Could not start the backup. Please try again.', 'error')
        return redirect(url_for('backup.backup_page'))
    app = current_app._get_current_object()
    user_id = current_user.id
    job_id = jobs.start_job('backup', 'Creating backup…', user_id,
                            backup_id=backup_id)
    thread = threading.Thread(
        target=jobs.run_backup_job,
        args=(app, job_id, backup_id, user_id, keep_n),
        daemon=True,
    )
    thread.start()
    flash('Backup started — it is running in the background and will '
          'appear below as In Progress until it finishes.', 'info')
    return redirect(url_for('backup.backup_page'))


@backup_bp.route('/admin/backup/<int:backup_id>/download')
@login_required
@admin_required
def download_backup(backup_id):
    row = get_backup_by_id(backup_id)
    if not row or len(row) < 2:
        flash('Backup not found.', 'error')
        return redirect(url_for('backup.backup_page'))
    try:
        path = resolve_backup_path(row[1])
    except ValueError:
        flash('Invalid backup filename.', 'error')
        return redirect(url_for('backup.backup_page'))
    if not os.path.isfile(path):
        flash('Backup file is missing from storage.', 'error')
        return redirect(url_for('backup.backup_page'))
    return send_file(path, as_attachment=True, download_name=row[1])


@backup_bp.route('/admin/backup/<int:backup_id>/restore', methods=['POST'])
@login_required
@admin_required
def restore_backup_route(backup_id):
    """Start a restore on a background thread and return immediately.

    The worker snapshots the current data first, then replaces the
    database — the request never waits for either step.
    """
    if not is_restore_enabled():
        flash(_RESTORE_DISABLED_MSG, 'error')
        return redirect(url_for('backup.backup_page'))
    row = get_backup_by_id(backup_id)
    if not row or len(row) < 4:
        flash('Backup not found.', 'error')
        return redirect(url_for('backup.backup_page'))
    if row[3] != 'completed':
        flash('Only completed backups can be restored.', 'error')
        return redirect(url_for('backup.backup_page'))
    if _busy():
        flash('A backup or restore is already running — '
              'wait for it to finish first.', 'error')
        return redirect(url_for('backup.backup_page'))

    app = current_app._get_current_object()
    user_id = current_user.id
    job_id = jobs.start_job('restore', f'Restoring {row[1]}…', user_id)
    thread = threading.Thread(
        target=jobs.run_restore_job,
        args=(app, job_id, user_id, backup_id, row[1]),
        daemon=True,
    )
    thread.start()
    flash(f'Restore started — {row[1]} is being restored in the background.',
          'info')
    return redirect(url_for('backup.backup_page', restore_started=row[1]))


@backup_bp.route('/admin/backup/<int:backup_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_backup_route(backup_id):
    """Delete one backup's file and history row.

    JSON (like the job endpoints) so the delete modals can report the
    outcome without reloading. Refuses while a worker runs so a file
    that is being written or restored can never be pulled mid-operation.
    """
    if _busy():
        return jsonify({'error': 'A backup or restore is running — '
                                 'wait for it to finish before deleting.'}), 409
    row = get_backup_by_id(backup_id)
    if not row or len(row) < 2:
        return jsonify({'error': 'Backup not found.'}), 404
    try:
        path = resolve_backup_path(row[1])
    except ValueError:
        return jsonify({'error': 'Invalid backup filename.'}), 400
    file_missing = not os.path.isfile(path)
    if not file_missing:
        try:
            os.remove(path)
        except OSError as e:  # noqa: BLE001 — row kept so history stays true
            return jsonify({'error': f'Could not delete the backup file: {e}'}), 500
    delete_backup_row(backup_id)
    log_activity(current_user.id, f'backup:deleted:{row[1]}')
    if file_missing:
        return jsonify({'deleted': row[1],
                        'note': 'The file was already missing from storage; '
                                'its history row was removed.'})
    return jsonify({'deleted': row[1]})
