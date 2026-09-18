import os
import subprocess
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest


def _row(backup_id=1, filename='library_backup_20260101_020000.sql',
         size=1024, status='completed', btype='manual', created=None):
    return (backup_id, filename, size, status, btype, None,
            created or datetime(2026, 1, 1, 2, 0, 0))


class TestCreateBackup:
    def test_writes_file_and_returns_size(self, app, tmp_path, monkeypatch):
        from app.backup import utils as backup_utils
        monkeypatch.setitem(app.config, 'BACKUP_DIR', str(tmp_path))
        monkeypatch.setitem(app.config, 'DATABASE_URL', 'postgresql://u:p@h/db')

        def fake_run(cmd, **kwargs):
            assert isinstance(cmd, list)
            assert kwargs.get('shell') is not True
            for part in cmd:
                if part.startswith('--file='):
                    with open(part[len('--file='):], 'w') as f:
                        f.write('dump-bytes')
            return subprocess.CompletedProcess(cmd, 0, '', '')

        with app.app_context():
            with patch.object(backup_utils.subprocess, 'run', side_effect=fake_run) as mock_run:
                filename, size = backup_utils.create_backup()
                assert filename.startswith('library_backup_')
                assert size == len('dump-bytes')
                assert (tmp_path / filename).is_file()
                # No shell=True anywhere in the call
                _, kwargs = mock_run.call_args
                assert 'shell' not in kwargs

    def test_no_shell_in_call_args(self, app, tmp_path, monkeypatch):
        from app.backup import utils as backup_utils
        monkeypatch.setitem(app.config, 'BACKUP_DIR', str(tmp_path))
        monkeypatch.setitem(app.config, 'DATABASE_URL', 'postgresql://u:p@h/db')

        def fake_run(cmd, **kwargs):
            for part in cmd:
                if part.startswith('--file='):
                    with open(part[len('--file='):], 'w') as f:
                        f.write('x')
            return subprocess.CompletedProcess(cmd, 0, '', '')

        with app.app_context():
            with patch.object(backup_utils.subprocess, 'run', side_effect=fake_run) as mock_run:
                backup_utils.create_backup()
                cmd = mock_run.call_args[0][0]
                assert isinstance(cmd, list)
                assert cmd[0] == 'pg_dump'

    def test_raises_with_stderr_on_failure(self, app, tmp_path, monkeypatch):
        from app.backup import utils as backup_utils
        monkeypatch.setitem(app.config, 'BACKUP_DIR', str(tmp_path))
        monkeypatch.setitem(app.config, 'DATABASE_URL', 'postgresql://u:p@h/db')

        def fake_run(cmd, **kwargs):
            raise subprocess.CalledProcessError(1, cmd, stderr='disk full')

        with app.app_context():
            with patch.object(backup_utils.subprocess, 'run', side_effect=fake_run):
                with pytest.raises(RuntimeError, match='disk full'):
                    backup_utils.create_backup()

    def test_resolve_blocks_traversal(self, app, tmp_path, monkeypatch):
        from app.backup import utils as backup_utils
        monkeypatch.setitem(app.config, 'BACKUP_DIR', str(tmp_path))
        with app.app_context():
            with pytest.raises(ValueError):
                backup_utils.resolve_backup_path('../../etc/passwd')


class TestBackupModels:
    def test_get_logs_order_and_fields(self, mock_db):
        from app.backup import models
        mock_db['fetch_all'].return_value = [_row(2), _row(1)]
        rows = models.get_backup_logs()
        assert rows[0][0] == 2
        assert 'SELECT' in mock_db['fetch_all'].call_args[0][0]
        assert 'ORDER BY created_at DESC' in mock_db['fetch_all'].call_args[0][0]

    def test_log_backup_insert(self, mock_db):
        from app.backup import models
        mock_db['fetch_one'].return_value = (7,)
        assert models.log_backup('f.sql', 10, 'manual') == 7
        query, params = mock_db['fetch_one'].call_args[0]
        assert 'INSERT INTO backup_log' in query
        assert params[0] == 'f.sql'

    def test_stale_backups_offset(self, mock_db):
        from app.backup import models
        models.get_stale_backups(12)
        query, params = mock_db['fetch_all'].call_args[0]
        assert 'OFFSET %s' in query
        assert params == (12,)

    def test_delete_old_backups_keeps_newest(self, app, tmp_path, monkeypatch, mock_db):
        from app.backup import scheduler
        monkeypatch.setitem(app.config, 'BACKUP_DIR', str(tmp_path))
        old_file = tmp_path / 'library_backup_old.sql'
        old_file.write_text('old')
        stale = [
            (99, 'library_backup_old.sql', 5, 'completed', 'manual', None,
             datetime(2025, 1, 1)),
            (100, '../../evil.sql', 5, 'completed', 'manual', None,
             datetime(2025, 1, 2)),
        ]
        mock_db['fetch_all'].return_value = stale
        with app.app_context():
            scheduler.apply_retention(app, 12)
        assert not old_file.exists()
        deletes = [c[0][1] for c in mock_db['execute'].call_args_list
                   if 'DELETE FROM backup_log' in c[0][0]]
        assert (99,) in deletes
        # Traversal filename must never delete outside BACKUP_DIR
        assert (100,) not in deletes


class TestBackupRoutes:
    def test_page_requires_admin(self, client, student_client, librarian_client, mock_db):
        resp = client.get('/admin/backup')
        assert resp.status_code == 302
        resp = student_client.get('/admin/backup')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location
        resp = librarian_client.get('/admin/backup')
        assert resp.status_code == 302

    def test_page_renders_history(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = [_row()]
        resp = admin_client.get('/admin/backup')
        assert resp.status_code == 200
        assert b'library_backup_20260101_020000.sql' in resp.data
        assert b'Run Backup Now' in resp.data

    def test_page_empty_state(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        resp = admin_client.get('/admin/backup')
        assert resp.status_code == 200
        assert b'No backups yet' in resp.data

    def test_create_route_logs_row(self, admin_client, mock_db):
        mock_db['fetch_one'].return_value = (3,)
        with patch('app.backup.routes.create_backup', return_value=('f.sql', 42)), \
             patch('app.backup.routes.apply_retention'), \
             patch('app.backup.routes.log_activity'):
            resp = admin_client.post('/admin/backup/create')
        assert resp.status_code == 302
        assert '/admin/backup' in resp.location
        inserts = [c for c in mock_db['fetch_one'].call_args_list
                   if 'INSERT INTO backup_log' in c[0][0]]
        assert inserts

    def test_create_route_failure_logs_failed(self, admin_client, mock_db):
        with patch('app.backup.routes.create_backup', side_effect=RuntimeError('boom')), \
             patch('app.backup.routes.log_activity'):
            resp = admin_client.post('/admin/backup/create')
        assert resp.status_code == 302
        query, params = mock_db['fetch_one'].call_args[0]
        assert 'INSERT INTO backup_log' in query
        assert 'failed' in params

    def test_download_serves_file(self, admin_client, mock_db, tmp_path, app):
        target = tmp_path / 'library_backup_20260101_020000.sql'
        target.write_text('dump')
        mock_db['fetch_one'].return_value = _row()
        with patch('app.backup.routes.resolve_backup_path', return_value=str(target)):
            resp = admin_client.get('/admin/backup/1/download')
        assert resp.status_code == 200
        assert resp.data == b'dump'

    def test_download_missing_file_redirects(self, admin_client, mock_db, tmp_path):
        mock_db['fetch_one'].return_value = _row()
        with patch('app.backup.routes.resolve_backup_path',
                   return_value=str(tmp_path / 'gone.sql')):
            resp = admin_client.get('/admin/backup/1/download')
        assert resp.status_code == 302

    def test_restore_auto_backups_then_psql(self, admin_client, mock_db):
        mock_db['fetch_one'].return_value = _row()
        with patch('app.backup.routes.create_backup', return_value=('safety.sql', 9)) as mk, \
             patch('app.backup.routes.restore_backup') as rs, \
             patch('app.backup.routes.apply_retention'), \
             patch('app.backup.routes.log_activity') as log_act:
            resp = admin_client.post('/admin/backup/1/restore')
        assert resp.status_code == 302
        mk.assert_called_once()
        rs.assert_called_once_with('library_backup_20260101_020000.sql')
        acts = [c[0][1] for c in log_act.call_args_list]
        assert any('backup:restored:' in a for a in acts)

    def test_restore_refuses_failed_backup(self, admin_client, mock_db):
        mock_db['fetch_one'].return_value = _row(status='failed')
        with patch('app.backup.routes.create_backup') as mk:
            resp = admin_client.post('/admin/backup/1/restore')
        assert resp.status_code == 302
        mk.assert_not_called()

    def test_restore_aborts_without_safety_net(self, admin_client, mock_db):
        mock_db['fetch_one'].return_value = _row()
        with patch('app.backup.routes.create_backup', side_effect=RuntimeError('no space')), \
             patch('app.backup.routes.restore_backup') as rs, \
             patch('app.backup.routes.log_activity'):
            resp = admin_client.post('/admin/backup/1/restore')
        assert resp.status_code == 302
        rs.assert_not_called()


class TestScheduler:
    def test_job_registered_on_start(self, app):
        from app.backup import scheduler as sched
        with patch('apscheduler.schedulers.background.BackgroundScheduler') as cls:
            inst = cls.return_value
            inst.running = False
            app.config['TESTING'] = False
            sched.start_scheduler(app)
            assert inst.add_job.called
            assert inst.start.called
            job_kwargs = inst.add_job.call_args[0]
            assert inst.add_job.call_args[1]['id'] == 'monthly_backup'

    def test_start_skipped_in_testing(self, app):
        from app.backup import scheduler as sched
        app.config['TESTING'] = True
        assert sched.start_scheduler(app) is None

    def test_scheduled_run_logs_scheduled_type(self, app, mock_db):
        from app.backup import scheduler as sched
        mock_db['fetch_one'].return_value = (1,)
        mock_db['fetch_all'].return_value = []
        with patch('app.backup.utils.create_backup', return_value=('f.sql', 5)):
            sched.run_scheduled_backup(app)
        _, params = mock_db['fetch_one'].call_args[0]
        assert 'scheduled' in params

    def test_scheduled_failure_logs_failed(self, app, mock_db):
        from app.backup import scheduler as sched
        with patch('app.backup.utils.create_backup', side_effect=RuntimeError('x')):
            sched.run_scheduled_backup(app)
        _, params = mock_db['fetch_one'].call_args[0]
        assert 'failed' in params
