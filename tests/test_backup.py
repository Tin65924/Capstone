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
            with patch('app.backup.utils.resolve_tool', return_value='pg_dump'), \
                 patch.object(backup_utils.subprocess, 'run', side_effect=fake_run) as mock_run:
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
            with patch('app.backup.utils.resolve_tool', return_value='pg_dump'), \
                 patch.object(backup_utils.subprocess, 'run', side_effect=fake_run) as mock_run:
                backup_utils.create_backup()
                cmd = mock_run.call_args[0][0]
                assert isinstance(cmd, list)
                assert cmd[0] == 'pg_dump'

    def test_dump_uses_clean_replace_flags(self, app, tmp_path, monkeypatch):
        """Dumps must DROP existing objects so a restore truly replaces data."""
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
            with patch('app.backup.utils.resolve_tool', return_value='pg_dump'), \
                 patch.object(backup_utils.subprocess, 'run', side_effect=fake_run) as mock_run:
                backup_utils.create_backup()
                cmd = mock_run.call_args[0][0]
                assert '--clean' in cmd
                assert '--if-exists' in cmd

    def test_restore_uses_atomic_flags(self, app, tmp_path, monkeypatch):
        """Restore must be single-transaction + ON_ERROR_STOP (no false success)."""
        from app.backup import utils as backup_utils
        monkeypatch.setitem(app.config, 'BACKUP_DIR', str(tmp_path))
        monkeypatch.setitem(app.config, 'DATABASE_URL', 'postgresql://u:p@h/db')
        target = tmp_path / 'library_backup_20260101_020000.sql'
        target.write_text('dump')

        with app.app_context():
            with patch('app.backup.utils.resolve_tool', return_value='psql'), \
                 patch.object(backup_utils.subprocess, 'run') as mock_run:
                mock_run.return_value = subprocess.CompletedProcess([], 0, '', '')
                backup_utils.restore_backup('library_backup_20260101_020000.sql')
                cmd = mock_run.call_args[0][0]
                assert cmd[0] == 'psql'
                assert '--single-transaction' in cmd
                assert '-v' in cmd
                assert 'ON_ERROR_STOP=1' in cmd

    def test_restore_bounds_lock_waits(self, app, tmp_path, monkeypatch):
        """Restore must not wait forever on another session's table lock."""
        from app.backup import utils as backup_utils
        monkeypatch.setitem(app.config, 'BACKUP_DIR', str(tmp_path))
        monkeypatch.setitem(app.config, 'DATABASE_URL', 'postgresql://u:p@h/db')
        target = tmp_path / 'library_backup_20260101_020000.sql'
        target.write_text('dump')

        with app.app_context():
            with patch('app.backup.utils.resolve_tool', return_value='psql'), \
                 patch.object(backup_utils.subprocess, 'run') as mock_run:
                mock_run.return_value = subprocess.CompletedProcess([], 0, '', '')
                backup_utils.restore_backup('library_backup_20260101_020000.sql')
                cmd = mock_run.call_args[0][0]
                assert '-c' in cmd
                assert "SET lock_timeout = '120s'" in cmd

    def test_raises_with_stderr_on_failure(self, app, tmp_path, monkeypatch):
        from app.backup import utils as backup_utils
        monkeypatch.setitem(app.config, 'BACKUP_DIR', str(tmp_path))
        monkeypatch.setitem(app.config, 'DATABASE_URL', 'postgresql://u:p@h/db')

        def fake_run(cmd, **kwargs):
            raise subprocess.CalledProcessError(1, cmd, stderr='disk full')

        with app.app_context():
            with patch('app.backup.utils.resolve_tool', return_value='pg_dump'), \
                 patch.object(backup_utils.subprocess, 'run', side_effect=fake_run):
                with pytest.raises(RuntimeError, match='disk full'):
                    backup_utils.create_backup()

    def test_missing_tool_raises_friendly_error(self, app, tmp_path, monkeypatch):
        from app.backup import utils as backup_utils
        monkeypatch.setitem(app.config, 'BACKUP_DIR', str(tmp_path))
        monkeypatch.setitem(app.config, 'DATABASE_URL', 'postgresql://u:p@h/db')
        with app.app_context():
            with patch('app.backup.utils.resolve_tool',
                       side_effect=RuntimeError('pg_dump was not found')):
                with pytest.raises(RuntimeError, match='pg_dump was not found'):
                    backup_utils.create_backup()

    def test_resolve_blocks_traversal(self, app, tmp_path, monkeypatch):
        from app.backup import utils as backup_utils
        monkeypatch.setitem(app.config, 'BACKUP_DIR', str(tmp_path))
        with app.app_context():
            with pytest.raises(ValueError):
                backup_utils.resolve_backup_path('../../etc/passwd')

    def test_subprocess_never_inherits_stdin(self, app, tmp_path, monkeypatch):
        """pg_dump must not block on a password prompt with no terminal."""
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
            with patch('app.backup.utils.resolve_tool', return_value='pg_dump'), \
                 patch.object(backup_utils.subprocess, 'run',
                             side_effect=fake_run) as mock_run:
                backup_utils.create_backup()
                _, kwargs = mock_run.call_args
                assert kwargs['stdin'] == subprocess.DEVNULL
                assert kwargs['timeout'] == backup_utils._SUBPROCESS_TIMEOUT

    def test_create_timeout_removes_partial_file(self, app, tmp_path,
                                                 monkeypatch):
        from app.backup import utils as backup_utils
        monkeypatch.setitem(app.config, 'BACKUP_DIR', str(tmp_path))
        monkeypatch.setitem(app.config, 'DATABASE_URL', 'postgresql://u:p@h/db')

        def fake_run(cmd, **kwargs):
            for part in cmd:
                if part.startswith('--file='):
                    with open(part[len('--file='):], 'w') as f:
                        f.write('partial')
            raise subprocess.TimeoutExpired(cmd, 600)

        with app.app_context():
            with patch('app.backup.utils.resolve_tool', return_value='pg_dump'), \
                 patch.object(backup_utils.subprocess, 'run',
                             side_effect=fake_run):
                with pytest.raises(RuntimeError, match='timed out'):
                    backup_utils.create_backup()
        assert list(tmp_path.iterdir()) == []


class TestResolveTool:
    def test_env_override_wins(self, tmp_path, monkeypatch):
        from app.backup.utils import resolve_tool
        exe = tmp_path / 'pg_dump.exe'
        exe.write_text('x')
        monkeypatch.setenv('PG_DUMP', str(exe))
        assert resolve_tool('pg_dump', 'PG_DUMP') == str(exe)

    def test_bad_env_override_explains(self, tmp_path, monkeypatch):
        from app.backup.utils import resolve_tool
        monkeypatch.setenv('PG_DUMP', str(tmp_path / 'missing.exe'))
        with pytest.raises(RuntimeError, match='PG_DUMP'):
            resolve_tool('pg_dump', 'PG_DUMP')

    def test_path_hit(self, monkeypatch):
        from app.backup import utils as backup_utils
        monkeypatch.delenv('PG_DUMP', raising=False)
        with patch.object(backup_utils.shutil, 'which', return_value='/usr/bin/pg_dump'):
            assert backup_utils.resolve_tool('pg_dump', 'PG_DUMP') == '/usr/bin/pg_dump'

    def test_windows_fallback_prefers_newest(self, monkeypatch):
        from app.backup import utils as backup_utils
        monkeypatch.delenv('PG_DUMP', raising=False)
        monkeypatch.setattr(backup_utils.os, 'name', 'nt')
        found = [
            r'C:\Program Files\PostgreSQL\16\bin\pg_dump.exe',
            r'C:\Program Files\PostgreSQL\18\bin\pg_dump.exe',
        ]
        with patch.object(backup_utils.shutil, 'which', return_value=None), \
             patch.object(backup_utils.glob, 'glob', return_value=found):
            assert backup_utils.resolve_tool('pg_dump', 'PG_DUMP').endswith('18\\bin\\pg_dump.exe')

    def test_missing_tool_guidance(self, monkeypatch):
        from app.backup import utils as backup_utils
        monkeypatch.delenv('PG_DUMP', raising=False)
        with patch.object(backup_utils.shutil, 'which', return_value=None), \
             patch.object(backup_utils.glob, 'glob', return_value=[]):
            with pytest.raises(RuntimeError, match='was not found'):
                backup_utils.resolve_tool('pg_dump', 'PG_DUMP')


class TestBackupStats:
    def test_failed_latest_is_not_healthy(self):
        from app.backup.routes import _backup_stats
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        failed = _row(2, 'manual_backup_failed.sql', None, 'failed', 'manual', now)
        old_ok = _row(1, 'library_backup_old.sql', 100, 'completed', 'manual',
                      datetime(2025, 1, 1))
        stats = _backup_stats([failed, old_ok])
        assert stats['healthy'] is False
        assert stats['count'] == 1  # failed runs are not counted as stored
        assert stats['total_size'] == 100

    def test_recent_completed_is_healthy(self):
        from app.backup.routes import _backup_stats
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        stats = _backup_stats([_row(1, 'f.sql', 50, 'completed', 'manual', now)])
        assert stats['healthy'] is True
        assert stats['count'] == 1


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

    def test_page_warns_when_latest_failed(self, admin_client, mock_db):
        now = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=123456)
        mock_db['fetch_all'].return_value = [
            _row(2, 'manual_backup_failed.sql', None, 'failed', 'manual', now),
        ]
        resp = admin_client.get('/admin/backup')
        assert resp.status_code == 200
        assert b'Warning' in resp.data
        assert b'Healthy' not in resp.data
        # Timestamps render without microseconds.
        assert b'.123456' not in resp.data
        assert now.strftime('%Y-%m-%d %H:%M').encode() in resp.data

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

    def test_restore_psql_failure_flashes_error_not_success(self, admin_client, mock_db):
        """A mid-restore psql error must surface — never a false success."""
        import subprocess as sp
        mock_db['fetch_one'].return_value = _row()
        mock_db['fetch_all'].return_value = []
        with patch('app.backup.routes.create_backup', return_value=('safety.sql', 9)), \
             patch('app.backup.routes.restore_backup',
                   side_effect=RuntimeError('psql exited with status 3')), \
             patch('app.backup.routes.apply_retention'), \
             patch('app.backup.routes.log_activity'):
            resp = admin_client.post('/admin/backup/1/restore', follow_redirects=True)
        assert resp.status_code == 200
        assert b'Restore failed' in resp.data
        assert b'Restore complete' not in resp.data


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

    def test_schedule_values_clamped(self, app):
        """Typo'd BACKUP_DAY/HOUR must not silently disable backups."""
        from app.backup import scheduler as sched
        with patch('apscheduler.schedulers.background.BackgroundScheduler') as cls:
            inst = cls.return_value
            inst.running = False
            app.config['TESTING'] = False
            app.config['BACKUP_DAY'] = 99
            app.config['BACKUP_HOUR'] = 99
            sched.start_scheduler(app)
            kwargs = inst.add_job.call_args[1]
            assert kwargs['day'] == 28
            assert kwargs['hour'] == 23

    def test_schedule_garbage_falls_back(self, app):
        from app.backup import scheduler as sched
        with patch('apscheduler.schedulers.background.BackgroundScheduler') as cls:
            inst = cls.return_value
            inst.running = False
            app.config['TESTING'] = False
            app.config['BACKUP_DAY'] = 'bogus'
            app.config['BACKUP_HOUR'] = None
            sched.start_scheduler(app)
            kwargs = inst.add_job.call_args[1]
            assert kwargs['day'] == 1
            assert kwargs['hour'] == 2

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

    def test_next_backup_this_month(self):
        from datetime import datetime
        from app.backup import scheduler as sched
        nxt = sched.next_scheduled_backup(20, 2, now=datetime(2026, 9, 10, 12, 0))
        assert (nxt.year, nxt.month, nxt.day, nxt.hour) == (2026, 9, 20, 2)

    def test_next_backup_rolls_to_next_month(self):
        from datetime import datetime
        from app.backup import scheduler as sched
        nxt = sched.next_scheduled_backup(1, 2, now=datetime(2026, 9, 10, 12, 0))
        assert (nxt.year, nxt.month, nxt.day, nxt.hour) == (2026, 10, 1, 2)

    def test_next_backup_rolls_year(self):
        from datetime import datetime
        from app.backup import scheduler as sched
        nxt = sched.next_scheduled_backup(1, 2, now=datetime(2026, 12, 15, 12, 0))
        assert (nxt.year, nxt.month, nxt.day, nxt.hour) == (2027, 1, 1, 2)

    def test_next_backup_clamps_day(self):
        from datetime import datetime
        from app.backup import scheduler as sched
        nxt = sched.next_scheduled_backup(99, 99, now=datetime(2026, 9, 10, 12, 0))
        assert (nxt.month, nxt.day, nxt.hour) == (9, 28, 23)

    def test_reschedule_noop_without_running_scheduler(self, app):
        from app.backup import scheduler as sched
        assert sched.reschedule(app) is False


def _wait_for_job(client, job_id, timeout=10):
    """Poll the status endpoint until the job reaches a terminal state."""
    import time
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = client.get(f'/admin/backup/jobs/{job_id}')
        assert resp.status_code == 200
        job = resp.get_json()
        if job['status'] in ('done', 'failed'):
            return job
        time.sleep(0.05)
    raise AssertionError('backup job did not reach a terminal state')


class TestBackupJobs:
    def test_jobs_require_admin(self, client, student_client, librarian_client,
                                mock_db):
        resp = client.post('/admin/backup/jobs')
        assert resp.status_code == 302
        resp = student_client.post('/admin/backup/jobs')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location
        resp = librarian_client.post('/admin/backup/jobs')
        assert resp.status_code == 302
        resp = client.get('/admin/backup/jobs/abc')
        assert resp.status_code == 302

    def test_backup_job_completes_with_progress(self, admin_client, mock_db):
        mock_db['fetch_one'].return_value = (3,)
        with patch('app.backup.jobs.create_backup',
                   return_value=('f.sql', 42)), \
             patch('app.backup.jobs.apply_retention'), \
             patch('app.backup.jobs.log_activity'):
            resp = admin_client.post('/admin/backup/jobs')
            assert resp.status_code == 202
            job = _wait_for_job(admin_client, resp.get_json()['job_id'])
        assert job['status'] == 'done'
        assert job['progress'] == 100
        assert job['filename'] == 'f.sql'
        inserts = [c for c in mock_db['fetch_one'].call_args_list
                   if 'INSERT INTO backup_log' in c[0][0]]
        assert inserts

    def test_backup_job_failure_surfaces_error(self, admin_client, mock_db):
        with patch('app.backup.jobs.create_backup',
                   side_effect=RuntimeError('disk full')), \
             patch('app.backup.jobs.log_activity'):
            resp = admin_client.post('/admin/backup/jobs')
            assert resp.status_code == 202
            job = _wait_for_job(admin_client, resp.get_json()['job_id'])
        assert job['status'] == 'failed'
        assert 'disk full' in job['error']
        query, params = mock_db['fetch_one'].call_args[0]
        assert 'INSERT INTO backup_log' in query
        assert 'failed' in params

    def test_job_status_unknown_404(self, admin_client, mock_db):
        resp = admin_client.get('/admin/backup/jobs/does-not-exist')
        assert resp.status_code == 404
        assert 'Unknown backup job' in resp.get_json()['error']

    def test_concurrent_backup_job_rejected(self, admin_client, mock_db):
        import threading
        release = threading.Event()

        def slow(*args, **kwargs):
            assert release.wait(10)
            return ('f.sql', 1)

        with patch('app.backup.jobs.create_backup', side_effect=slow), \
             patch('app.backup.jobs.apply_retention'), \
             patch('app.backup.jobs.log_activity'):
            resp = admin_client.post('/admin/backup/jobs')
            assert resp.status_code == 202
            resp2 = admin_client.post('/admin/backup/jobs')
            assert resp2.status_code == 409
            assert 'already running' in resp2.get_json()['error']
            release.set()
            job = _wait_for_job(admin_client, resp.get_json()['job_id'])
        assert job['status'] == 'done'

    def test_concurrent_restore_job_rejected(self, admin_client, mock_db):
        import threading
        mock_db['fetch_one'].return_value = _row()
        release = threading.Event()

        def slow(*args, **kwargs):
            assert release.wait(10)
            return ('safety.sql', 1)

        with patch('app.backup.jobs.create_backup', side_effect=slow), \
             patch('app.backup.jobs.restore_backup'), \
             patch('app.backup.jobs.log_activity'):
            resp = admin_client.post('/admin/backup/1/restore-job')
            assert resp.status_code == 202
            resp2 = admin_client.post('/admin/backup/1/restore-job')
            assert resp2.status_code == 409
            release.set()
            job = _wait_for_job(admin_client, resp.get_json()['job_id'])
        assert job['status'] == 'done'

    def test_job_status_reports_stage_history(self, admin_client, mock_db):
        mock_db['fetch_one'].return_value = (3,)
        with patch('app.backup.jobs.create_backup',
                   return_value=('f.sql', 42)), \
             patch('app.backup.jobs.apply_retention'), \
             patch('app.backup.jobs.log_activity'):
            resp = admin_client.post('/admin/backup/jobs')
            assert resp.status_code == 202
            job = _wait_for_job(admin_client, resp.get_json()['job_id'])
        assert job['status'] == 'done'
        assert 'Dumping database…' in job['history']
        assert 'Backup complete.' in job['history']

    def test_restore_job_completes(self, admin_client, mock_db):
        mock_db['fetch_one'].return_value = _row()
        with patch('app.backup.jobs.create_backup',
                   return_value=('safety.sql', 9)) as mk, \
             patch('app.backup.jobs.restore_backup') as rs, \
             patch('app.backup.jobs.log_activity') as log_act:
            resp = admin_client.post('/admin/backup/1/restore-job')
            assert resp.status_code == 202
            job = _wait_for_job(admin_client, resp.get_json()['job_id'])
        assert job['status'] == 'done'
        assert job['progress'] == 100
        mk.assert_called_once()
        rs.assert_called_once_with('library_backup_20260101_020000.sql')
        acts = [c[0][1] for c in log_act.call_args_list]
        assert any('backup:restored:' in a for a in acts)

    def test_restore_job_refuses_failed_backup(self, admin_client, mock_db):
        mock_db['fetch_one'].return_value = _row(status='failed')
        with patch('app.backup.jobs.create_backup') as mk:
            resp = admin_client.post('/admin/backup/1/restore-job')
        assert resp.status_code == 400
        assert 'Only completed' in resp.get_json()['error']
        mk.assert_not_called()

    def test_restore_job_missing_backup_404(self, admin_client, mock_db):
        mock_db['fetch_one'].return_value = None
        resp = admin_client.post('/admin/backup/9/restore-job')
        assert resp.status_code == 404

    def test_restore_job_aborts_without_safety_net(self, admin_client,
                                                   mock_db):
        mock_db['fetch_one'].return_value = _row()
        with patch('app.backup.jobs.create_backup',
                   side_effect=RuntimeError('no space')), \
             patch('app.backup.jobs.restore_backup') as rs, \
             patch('app.backup.jobs.log_activity'):
            resp = admin_client.post('/admin/backup/1/restore-job')
            assert resp.status_code == 202
            job = _wait_for_job(admin_client, resp.get_json()['job_id'])
        assert job['status'] == 'failed'
        assert 'snapshot' in job['error']
        rs.assert_not_called()

    def test_page_uses_progress_modal(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = [_row()]
        resp = admin_client.get('/admin/backup')
        assert resp.status_code == 200
        assert b'backup-progress-modal' in resp.data
        assert b'backup-progress-bar' in resp.data
        assert b'data-restore-job-url' in resp.data
        assert b'run-backup-form' in resp.data
        # Per-backup confirmation modals are gone.
        assert b'restore-modal-' not in resp.data

    def test_backup_form_posts_to_jobs_endpoint(self, admin_client, mock_db):
        """The intercepted form must target the JSON job endpoint — posting
        to the sync route returns a redirect (HTML), which breaks .json()."""
        mock_db['fetch_all'].return_value = []
        resp = admin_client.get('/admin/backup')
        assert resp.status_code == 200
        assert b'action="/admin/backup/jobs"' in resp.data
