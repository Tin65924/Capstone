import os
from datetime import datetime, timedelta, timezone

from flask import current_app, flash, redirect, render_template, send_file, url_for
from flask_login import current_user, login_required

from app.auth.decorators import admin_required
from app.auth.models import log_activity

from . import backup_bp
from .models import get_backup_by_id, get_backup_logs, log_backup
from .scheduler import apply_retention
from .utils import create_backup, resolve_backup_path, restore_backup


def _backup_stats(logs):
    completed = [row for row in logs if row[3] == 'completed']
    total_size = sum((row[2] or 0) for row in completed)
    last = logs[0] if logs else None
    # Healthy only when the newest run succeeded and is recent — a failed
    # latest run must show Warning, never Healthy.
    healthy = False
    if last and last[3] == 'completed' and last[6]:
        created = last[6]
        if getattr(created, 'tzinfo', None) is None:
            created = created.replace(tzinfo=timezone.utc)
        healthy = (datetime.now(timezone.utc) - created) <= timedelta(days=35)
    return {
        'count': len(completed),
        'total_size': total_size,
        'last': last,
        'healthy': healthy,
    }


@backup_bp.route('/admin/backup')
@login_required
@admin_required
def backup_page():
    logs = get_backup_logs()
    stats = _backup_stats(logs or [])
    recovery_events = [row for row in (logs or []) if row[3] == 'failed'][:10]
    keep_n = current_app.config.get('BACKUP_KEEP', 12)
    return render_template(
        'backup/backup.html',
        backups=logs or [],
        stats=stats,
        recovery_events=recovery_events,
        keep_n=keep_n,
    )


@backup_bp.route('/admin/backup/create', methods=['POST'])
@login_required
@admin_required
def create_backup_route():
    keep_n = current_app.config.get('BACKUP_KEEP', 12)
    try:
        filename, size_bytes = create_backup()
    except Exception as e:  # noqa: BLE001 — expected user-visible failure path
        log_backup(
            filename='manual_backup_failed.sql',
            backup_type='manual',
            status='failed',
            error_msg=str(e)[:500],
        )
        log_activity(current_user.id, 'backup:failed:manual')
        flash(f'Backup failed: {e}', 'error')
        return redirect(url_for('backup.backup_page'))
    log_backup(filename, size_bytes, backup_type='manual', status='completed')
    apply_retention(current_app, keep_n)
    log_activity(current_user.id, f'backup:created:{filename}')
    flash(f'Backup created: {filename}', 'success')
    return redirect(url_for('backup.backup_page'))


@backup_bp.route('/admin/backup/<int:backup_id>/download')
@login_required
@admin_required
def download_backup(backup_id):
    row = get_backup_by_id(backup_id)
    if not row:
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
    row = get_backup_by_id(backup_id)
    if not row:
        flash('Backup not found.', 'error')
        return redirect(url_for('backup.backup_page'))
    if row[3] != 'completed':
        flash('Only completed backups can be restored.', 'error')
        return redirect(url_for('backup.backup_page'))

    # Safety net: snapshot the current state before the destructive restore.
    try:
        safety_file, safety_size = create_backup()
        log_backup(safety_file, safety_size, backup_type='manual',
                   status='completed', error_msg='pre-restore auto-backup')
    except Exception as e:  # noqa: BLE001 — refuse a restore with no safety net
        log_activity(current_user.id, f'backup:restore_aborted:{row[1]}')
        flash(f'Restore aborted — could not snapshot current data: {e}', 'error')
        return redirect(url_for('backup.backup_page'))

    try:
        restore_backup(row[1])
    except (FileNotFoundError, ValueError) as e:
        log_activity(current_user.id, f'backup:restore_failed:{row[1]}')
        flash(f'Restore failed: {e}', 'error')
        return redirect(url_for('backup.backup_page'))
    except Exception as e:  # noqa: BLE001 — psql failure; safety backup is the recovery point
        log_activity(current_user.id, f'backup:restore_failed:{row[1]}')
        flash(f'Restore failed: {e}. Current data was snapshotted as {safety_file}.', 'error')
        return redirect(url_for('backup.backup_page'))

    log_activity(current_user.id, f'backup:restored:{row[1]}')
    flash(f'Restore complete: the database was replaced from {row[1]}. '
          'Anything added after that backup was lost.', 'success')
    return redirect(url_for('backup.backup_page'))
