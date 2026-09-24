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

    def test_create_route_starts_async_and_completes(self, admin_client, mock_db):
        """POST returns at once with an in_progress row; the worker finishes it."""
        from app.backup import jobs as jobs_mod
        # Guard lookup finds nothing running; the INSERT returns id 3.
        mock_db['fetch_one'].side_effect = [None, (3,)]
        with patch('app.backup.jobs.create_backup',
                   return_value=('f.sql', 42)), \
             patch('app.backup.jobs.apply_retention'), \
             patch('app.backup.jobs.log_activity'):
            resp = admin_client.post('/admin/backup/create')
            assert resp.status_code == 302
            assert '/admin/backup' in resp.location
            # The request returned while an in_progress row exists.
            inserts = [c for c in mock_db['fetch_one'].call_args_list
                       if 'INSERT INTO backup_log' in c[0][0]]
            assert inserts
            assert 'in_progress' in inserts[0][0][1]
            _wait_for_idle()
            assert jobs_mod.active_job() is None
        updates = [c for c in mock_db['execute'].call_args_list
                   if 'UPDATE backup_log' in c[0][0]]
        assert updates
        query, params = updates[0][0]
        assert 'completed' in params
        assert 'f.sql' in params

    def test_create_returns_without_waiting_for_worker(self, admin_client, mock_db):
        """The response must not block on pg_dump (true background thread)."""
        import threading
        import time
        from app.backup import jobs as jobs_mod
        # Guard lookup finds nothing running; the INSERT returns id 3.
        mock_db['fetch_one'].side_effect = [None, (3,)]
        release = threading.Event()

        def slow():
            assert release.wait(10)
            return ('slow.sql', 1)

        with patch('app.backup.jobs.create_backup', side_effect=slow), \
             patch('app.backup.jobs.apply_retention'), \
             patch('app.backup.jobs.log_activity'):
            started = time.time()
            resp = admin_client.post('/admin/backup/create')
            elapsed = time.time() - started
            assert resp.status_code == 302
            # Returned fast while the worker is still blocked on pg_dump.
            assert elapsed < 5
            assert jobs_mod.active_job() is not None
            inserts = [c for c in mock_db['fetch_one'].call_args_list
                       if 'INSERT INTO backup_log' in c[0][0]]
            assert inserts and 'in_progress' in inserts[0][0][1]
            release.set()
            _wait_for_idle()
        updates = [c for c in mock_db['execute'].call_args_list
                   if 'UPDATE backup_log' in c[0][0]]
        assert updates and 'completed' in updates[0][0][1]

    def test_create_route_failure_flips_row_to_failed(self, admin_client, mock_db):
        mock_db['fetch_one'].side_effect = [None, (3,)]
        with patch('app.backup.jobs.create_backup',
                   side_effect=RuntimeError('boom')), \
             patch('app.backup.jobs.log_activity'):
            resp = admin_client.post('/admin/backup/create')
            assert resp.status_code == 302
            _wait_for_idle()
        updates = [c for c in mock_db['execute'].call_args_list
                   if 'UPDATE backup_log' in c[0][0]]
        assert updates
        query, params = updates[0][0]
        assert 'failed' in params
        assert any('boom' in str(p) for p in params)

    def test_create_refused_while_busy(self, admin_client, mock_db):
        """A second backup while one runs redirects — no second row."""
        import threading
        release = threading.Event()

        def slow():
            assert release.wait(10)
            return ('slow.sql', 1)

        mock_db['fetch_one'].side_effect = [None, (3,)]
        with patch('app.backup.jobs.create_backup', side_effect=slow), \
             patch('app.backup.jobs.apply_retention'), \
             patch('app.backup.jobs.log_activity'):
            resp = admin_client.post('/admin/backup/create')
            assert resp.status_code == 302
            resp2 = admin_client.post('/admin/backup/create')
            assert resp2.status_code == 302
            assert '/admin/backup' in resp2.location
            inserts = [c for c in mock_db['fetch_one'].call_args_list
                       if 'INSERT INTO backup_log' in c[0][0]]
            assert len(inserts) == 1
            release.set()
            _wait_for_idle()

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

    def test_restore_starts_async_then_replaces(self, admin_client, mock_db):
        mock_db['fetch_one'].side_effect = [('1',), _row(), None, _row(), (5,)]
        with patch('app.backup.jobs.create_backup',
                   return_value=('safety.sql', 9)) as mk, \
             patch('app.backup.jobs.restore_backup') as rs, \
             patch('app.backup.jobs.log_activity') as log_act:
            resp = admin_client.post('/admin/backup/1/restore')
            assert resp.status_code == 302
            assert '/admin/backup' in resp.location
            _wait_for_idle()
        mk.assert_called_once()
        rs.assert_called_once_with('library_backup_20260101_020000.sql')
        acts = [c[0][1] for c in log_act.call_args_list]
        assert any('backup:restored:' in a for a in acts)

    def test_restore_refuses_failed_backup(self, admin_client, mock_db):
        mock_db['fetch_one'].return_value = _row(status='failed')
        with patch('app.backup.jobs.create_backup') as mk:
            resp = admin_client.post('/admin/backup/1/restore')
        assert resp.status_code == 302
        mk.assert_not_called()

    def test_restore_aborts_without_safety_net(self, admin_client, mock_db):
        from app.backup import jobs as jobs_mod
        mock_db['fetch_one'].side_effect = [('1',), _row(), None, _row()]
        with patch('app.backup.jobs.create_backup',
                   side_effect=RuntimeError('no space')), \
             patch('app.backup.jobs.restore_backup') as rs, \
             patch('app.backup.jobs.log_activity'):
            resp = admin_client.post('/admin/backup/1/restore')
            assert resp.status_code == 302
            _wait_for_idle()
        rs.assert_not_called()
        assert jobs_mod.recent_finished_job()['status'] == 'failed'

    def test_restore_psql_failure_recorded_on_job(self, admin_client, mock_db):
        """A mid-restore psql error surfaces on the finished job, never success."""
        from app.backup import jobs as jobs_mod
        mock_db['fetch_one'].side_effect = [('1',), _row(), None, _row(), (5,)]
        mock_db['fetch_all'].return_value = []
        with patch('app.backup.jobs.create_backup',
                   return_value=('safety.sql', 9)), \
             patch('app.backup.jobs.restore_backup',
                   side_effect=RuntimeError('psql exited with status 3')), \
             patch('app.backup.jobs.log_activity'):
            resp = admin_client.post('/admin/backup/1/restore')
            assert resp.status_code == 302
            assert '/admin/backup' in resp.location
            _wait_for_idle()
            job = jobs_mod.recent_finished_job()
        assert job['status'] == 'failed'
        assert 'psql exited with status 3' in job['error']
        assert 'safety.sql' in job['error']


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


def _wait_for_idle(timeout=10):
    """Block until the backup worker thread finishes (or fail)."""
    import time
    from app.backup import jobs as jobs_mod
    deadline = time.time() + timeout
    while time.time() < deadline:
        if jobs_mod.active_job() is None:
            return True
        time.sleep(0.05)
    raise AssertionError('backup worker did not finish')


@pytest.fixture(autouse=True)
def _clean_backup_jobs():
    """Module-global job registry must not leak between tests."""
    from app.backup import jobs as jobs_mod
    jobs_mod._jobs.clear()
    yield
    jobs_mod._jobs.clear()


def _in_progress_row(**overrides):
    row = (9, 'library_backup_20260920_020000_in_progress.sql', None,
           'in_progress', 'manual', None, datetime.now().replace(microsecond=0))
    for key, value in overrides.items():
        idx = {'backup_id': 0, 'filename': 1, 'size': 2, 'status': 3,
               'btype': 4, 'error': 5, 'created': 6}[key]
        row = row[:idx] + (value,) + row[idx + 1:]
    return row


class TestBackupJobs:
    def test_create_and_restore_require_admin(self, client, student_client,
                                              librarian_client, mock_db):
        resp = client.post('/admin/backup/create')
        assert resp.status_code == 302
        resp = student_client.post('/admin/backup/create')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location
        resp = librarian_client.post('/admin/backup/create')
        assert resp.status_code == 302
        resp = student_client.post('/admin/backup/1/restore')
        assert resp.status_code == 302
        assert '/user/profile' in resp.location
        resp = client.post('/admin/backup/1/restore')
        assert resp.status_code == 302

    def test_restore_refuses_in_progress_row(self, admin_client, mock_db):
        """An in_progress history row is not restorable."""
        mock_db['fetch_one'].return_value = _in_progress_row()
        with patch('app.backup.jobs.create_backup') as mk:
            resp = admin_client.post('/admin/backup/9/restore')
        assert resp.status_code == 302
        mk.assert_not_called()

    def test_restore_missing_backup(self, admin_client, mock_db):
        mock_db['fetch_one'].return_value = None
        resp = admin_client.post('/admin/backup/9/restore')
        assert resp.status_code == 302

    def test_stale_in_progress_reaped(self, admin_client, mock_db):
        """A worker that died hours ago must not block new backups forever."""
        stale = _in_progress_row(created=datetime(2026, 9, 18, 2, 0, 0))
        mock_db['fetch_one'].side_effect = [stale, (3,)]
        with patch('app.backup.jobs.create_backup',
                   return_value=('f.sql', 1)), \
             patch('app.backup.jobs.apply_retention'), \
             patch('app.backup.jobs.log_activity'):
            resp = admin_client.post('/admin/backup/create')
            assert resp.status_code == 302
            _wait_for_idle()
        failed = [c for c in mock_db['execute'].call_args_list
                  if 'UPDATE backup_log' in c[0][0]
                  and 'failed' in c[0][1]]
        assert failed

    def test_page_has_no_progress_modal(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = [_row()]
        mock_db['fetch_one'].return_value = None
        resp = admin_client.get('/admin/backup')
        assert resp.status_code == 200
        assert b'backup-progress-modal' not in resp.data
        assert b'backup-progress-bar' not in resp.data
        assert b'data-restore-job-url' not in resp.data
        assert b'run-backup-form' not in resp.data
        assert b'restore-modal-' not in resp.data

    def test_backup_form_posts_to_create_endpoint(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = []
        mock_db['fetch_one'].return_value = None
        resp = admin_client.get('/admin/backup')
        assert resp.status_code == 200
        assert b'action="/admin/backup/create"' in resp.data

    def test_restore_uses_plain_forms(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = [_row()]
        mock_db['fetch_one'].return_value = None
        resp = admin_client.get('/admin/backup')
        assert resp.status_code == 200
        assert b'action="/admin/backup/1/restore"' in resp.data

    def test_page_shows_in_progress_state(self, admin_client, mock_db):
        running = _in_progress_row()
        mock_db['fetch_all'].return_value = [running, _row()]
        mock_db['fetch_one'].return_value = running
        resp = admin_client.get('/admin/backup')
        assert resp.status_code == 200
        assert b'In Progress' in resp.data
        assert b'Backup Running' in resp.data
        assert b'http-equiv="refresh"' in resp.data
        # Restore is unavailable while busy.
        assert b'action="/admin/backup/1/restore"' not in resp.data

    def test_page_shows_recent_failure_banner(self, admin_client, mock_db):
        from app.backup import jobs as jobs_mod
        mock_db['fetch_one'].return_value = _row()
        mock_db['fetch_all'].return_value = []
        with patch('app.backup.jobs.create_backup',
                   side_effect=RuntimeError('disk full')), \
             patch('app.backup.jobs.log_activity'):
            admin_client.post('/admin/backup/create')
            _wait_for_idle()
            assert jobs_mod.recent_finished_job()['status'] == 'failed'
            resp = admin_client.get('/admin/backup')
        assert resp.status_code == 200
        assert b'failed.' in resp.data
        assert b'disk full' in resp.data


class TestBackupStatsInProgress:
    def test_newest_in_progress_ignored_for_health(self):
        from app.backup.routes import _backup_stats
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        running = _in_progress_row(created=now)
        ok = _row(1, 'f.sql', 50, 'completed', 'manual', now)
        stats = _backup_stats([running, ok])
        assert stats['count'] == 1
        assert stats['total_size'] == 50
        assert stats['healthy'] is True
        assert stats['last'][0] == 1

    def test_only_in_progress_means_no_last(self):
        from app.backup.routes import _backup_stats
        stats = _backup_stats([_in_progress_row()])
        assert stats['count'] == 0
        assert stats['last'] is None
        assert stats['healthy'] is False


class TestBackupModelsStatus:
    def test_get_in_progress_uses_bound_param(self, mock_db):
        from app.backup import models
        mock_db['fetch_one'].return_value = None
        assert models.get_in_progress_backup() is None
        query, params = mock_db['fetch_one'].call_args[0]
        assert "status = %s" in query
        assert params == ('in_progress',)

    def test_update_backup_status_completed(self, mock_db):
        from app.backup import models
        models.update_backup_status(9, 'completed', filename='f.sql',
                                    size_bytes=10)
        query, params = mock_db['execute'].call_args[0]
        assert query.startswith('UPDATE backup_log SET')
        assert 'status = %s' in query
        assert 'filename = %s' in query
        assert 'size_bytes = %s' in query
        assert params == ('completed', 'f.sql', 10, 9)

    def test_update_backup_status_failed(self, mock_db):
        from app.backup import models
        models.update_backup_status(9, 'failed', error_msg='boom')
        query, params = mock_db['execute'].call_args[0]
        assert 'error_msg = %s' in query
        assert params == ('failed', 'boom', 9)

    def test_retention_skips_in_progress(self, app, tmp_path, monkeypatch,
                                         mock_db):
        from app.backup import scheduler
        monkeypatch.setitem(app.config, 'BACKUP_DIR', str(tmp_path))
        keep_file = tmp_path / 'library_backup_new.sql'
        keep_file.write_text('new')
        stale = [
            _in_progress_row(backup_id=98),
            (99, 'library_backup_old.sql', 5, 'completed', 'manual', None,
             datetime(2025, 1, 1)),
        ]
        mock_db['fetch_all'].return_value = stale
        with app.app_context():
            scheduler.apply_retention(app, 1)
        deletes = [c[0][1] for c in mock_db['execute'].call_args_list
                   if 'DELETE FROM backup_log' in c[0][0]]
        assert (99,) in deletes
        assert (98,) not in deletes

class TestRestoreToggle:
    """BACKUP_RESTORE_ENABLED gates the async restore entry point."""

    def test_page_shows_restore_form_when_enabled(self, admin_client,
                                                  mock_db):
        mock_db['fetch_all'].return_value = [_row()]
        mock_db['fetch_one'].return_value = None  # empty settings ? on
        resp = admin_client.get('/admin/backup')
        assert resp.status_code == 200
        assert b'action="/admin/backup/1/restore"' in resp.data
        assert b'title="Restore' in resp.data
        assert b'restore disabled in Library Settings' not in resp.data

    def test_page_greys_restore_when_disabled(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = [_row()]
        with patch('app.backup.routes.is_restore_enabled', return_value=False):
            resp = admin_client.get('/admin/backup')
        assert resp.status_code == 200
        # No restore form posts (the JS selector string still mentions the
        # attribute name, so assert on the form action).
        assert b'action="/admin/backup/1/restore"' not in resp.data
        assert b'title="Restore"' not in resp.data
        assert b'restore disabled in Library Settings' in resp.data
        # Download stays available - only restore is gated.
        assert b'/admin/backup/1/download' in resp.data

    def test_restore_refused_when_disabled(self, admin_client, mock_db):
        with patch('app.backup.routes.is_restore_enabled', return_value=False), \
             patch('app.backup.jobs.create_backup') as mk:
            resp = admin_client.post('/admin/backup/1/restore')
        assert resp.status_code == 302
        assert '/admin/backup' in resp.location
        mk.assert_not_called()

    def test_restore_redirect_carries_started_signal(self, admin_client,
                                                     mock_db):
        """The POST redirects with ?restore_started= so the outcome modal
        opens exactly once on the reloaded page."""
        from app.backup import jobs as jobs_mod
        mock_db['fetch_one'].side_effect = [('1',), _row(), None, _row(),
                                            (6,)]
        mock_db['fetch_all'].return_value = []
        with patch('app.backup.jobs.create_backup',
                   return_value=('safety.sql', 9)), \
             patch('app.backup.jobs.restore_backup'), \
             patch('app.backup.jobs.log_activity'):
            resp = admin_client.post('/admin/backup/1/restore')
            assert resp.status_code == 302
            assert 'restore_started=library_backup_20260101_020000.sql' \
                in resp.location
            _wait_for_idle()
            assert jobs_mod.active_job() is None


class TestRestoreConfirmModal:
    def test_confirm_modal_states_consequences(self, admin_client, mock_db):
        """Modal 1 of 2 must spell out what restoring will do."""
        mock_db['fetch_all'].return_value = [_row()]
        mock_db['fetch_one'].return_value = None
        resp = admin_client.get('/admin/backup')
        assert resp.status_code == 200
        assert b'id="restore-confirm-modal"' in resp.data
        assert b'Restore this backup?' in resp.data
        assert b'safety snapshot' in resp.data.lower()
        assert b'permanently lost' in resp.data.lower()
        assert b'id="restore-confirm-cancel"' in resp.data
        assert b'Yes, restore' in resp.data

    def test_result_modal_opens_once_after_restore_post(self, admin_client,
                                                        mock_db):
        """Modal 2 of 2 opens on the redirected load and names the file."""
        mock_db['fetch_all'].return_value = [_row()]
        mock_db['fetch_one'].return_value = None
        resp = admin_client.get(
            '/admin/backup?restore_started=library_backup_20260101_020000.sql')
        assert resp.status_code == 200
        assert b'id="restore-result-modal" class="modal-overlay open"' \
            in resp.data
        assert b'data-auto-open="1"' in resp.data
        assert b'library_backup_20260101_020000.sql' in resp.data
        assert b'Restore started' in resp.data

    def test_result_modal_stays_closed_otherwise(self, admin_client,
                                                 mock_db):
        mock_db['fetch_all'].return_value = [_row()]
        mock_db['fetch_one'].return_value = None
        resp = admin_client.get('/admin/backup')
        assert resp.status_code == 200
        assert b'id="restore-result-modal" class="modal-overlay"' in resp.data
        # The JS still names the attribute, so assert on its rendered value.
        assert b'data-auto-open="1"' not in resp.data


class TestRestorePreservesHistory:
    """Restoring an older backup must never drop newer backup history.

    pg_dump dumps backup_log too, so the replay reverts the table to the
    backup-time state. The restore worker must re-record the rows logged
    since (newer backups + the safety snapshot).
    """

    def _old_and_new(self):
        old = _row(backup_id=1, filename='library_backup_20250101_020000.sql',
                   created=datetime(2025, 1, 1, 2, 0, 0))
        new = _row(backup_id=5, filename='library_backup_20260301_020000.sql',
                   created=datetime(2026, 3, 1, 2, 0, 0))
        safety = _row(backup_id=6, filename='library_backup_20260401_020000.sql',
                      created=datetime(2026, 4, 1, 2, 0, 0))
        return old, new, safety

    def _reinserted_filenames(self, mock_db):
        return [c[0][1][0] for c in mock_db['execute'].call_args_list
                if 'INSERT INTO backup_log' in c[0][0]
                and len(c[0][1]) == 6]

    def test_worker_rerecords_newer_rows(self, admin_client, mock_db):
        from app.backup import jobs as jobs_mod
        old, new, safety = self._old_and_new()
        # Gate setting, route lookup, busy guard, worker lookup, safety log.
        mock_db['fetch_one'].side_effect = [('1',), old, None, old, (6,)]
        # Pre-restore snapshot, then the dump-time table after the replay.
        mock_db['fetch_all'].side_effect = [[new, safety, old], [old]]
        with patch('app.backup.jobs.create_backup',
                   return_value=('safety.sql', 9)), \
             patch('app.backup.jobs.restore_backup') as rs, \
             patch('app.backup.jobs.log_activity'):
            resp = admin_client.post('/admin/backup/1/restore')
            assert resp.status_code == 302
            _wait_for_idle()
            assert jobs_mod.active_job() is None
            job = jobs_mod.recent_finished_job()
        assert job['status'] == 'done'
        rs.assert_called_once_with('library_backup_20250101_020000.sql')
        filenames = self._reinserted_filenames(mock_db)
        assert 'library_backup_20260301_020000.sql' in filenames
        assert 'library_backup_20260401_020000.sql' in filenames
        # Dump-time rows survive the replay - never duplicated.
        assert 'library_backup_20250101_020000.sql' not in filenames

    def test_worker_failed_restore_does_not_reinsert(self, admin_client,
                                                     mock_db):
        from app.backup import jobs as jobs_mod
        old, new, _ = self._old_and_new()
        mock_db['fetch_one'].side_effect = [('1',), old, None, old, (6,)]
        mock_db['fetch_all'].return_value = [new, old]
        with patch('app.backup.jobs.create_backup',
                   return_value=('safety.sql', 9)), \
             patch('app.backup.jobs.restore_backup',
                   side_effect=RuntimeError('psql exited with status 3')), \
             patch('app.backup.jobs.log_activity'):
            resp = admin_client.post('/admin/backup/1/restore')
            assert resp.status_code == 302
            _wait_for_idle()
            job = jobs_mod.recent_finished_job()
        assert job['status'] == 'failed'
        assert self._reinserted_filenames(mock_db) == []

    def test_reconcile_failure_keeps_job_done(self, admin_client, mock_db):
        """History bookkeeping must never fail a good restore."""
        from app.backup import jobs as jobs_mod
        old, new, _ = self._old_and_new()
        mock_db['fetch_one'].side_effect = [('1',), old, None, old, (6,)]
        mock_db['fetch_all'].side_effect = [[new, old], [old]]
        mock_db['execute'].side_effect = RuntimeError('db down')
        with patch('app.backup.jobs.create_backup',
                   return_value=('safety.sql', 9)), \
             patch('app.backup.jobs.restore_backup'), \
             patch('app.backup.jobs.log_activity'):
            resp = admin_client.post('/admin/backup/1/restore')
            assert resp.status_code == 302
            _wait_for_idle()
            job = jobs_mod.recent_finished_job()
        assert job['status'] == 'done'
        mock_db['execute'].side_effect = None


class TestDeleteBackup:
    def test_page_shows_delete_button_on_every_row(self, admin_client,
                                                   mock_db):
        mock_db['fetch_all'].return_value = [
            _row(),
            _row(2, 'manual_backup_failed.sql', None, 'failed'),
        ]
        mock_db['fetch_one'].return_value = None
        resp = admin_client.get('/admin/backup')
        assert resp.status_code == 200
        assert b'data-delete-url="/admin/backup/1/delete"' in resp.data
        assert b'data-delete-url="/admin/backup/2/delete"' in resp.data

    def test_delete_modals_state_consequences(self, admin_client, mock_db):
        mock_db['fetch_all'].return_value = [_row()]
        mock_db['fetch_one'].return_value = None
        resp = admin_client.get('/admin/backup')
        assert resp.status_code == 200
        assert b'id="delete-confirm-modal"' in resp.data
        assert b'Delete this backup?' in resp.data
        assert b'permanently removed' in resp.data.lower()
        assert b'Yes, delete' in resp.data
        assert b'id="delete-result-modal"' in resp.data
        assert b'Reload page' in resp.data

    def test_delete_removes_file_and_row(self, admin_client, mock_db,
                                         tmp_path):
        target = tmp_path / 'library_backup_20260101_020000.sql'
        target.write_text('dump')
        mock_db['fetch_one'].return_value = _row()
        with patch('app.backup.routes.resolve_backup_path',
                   return_value=str(target)), \
             patch('app.backup.routes.log_activity') as log_act:
            resp = admin_client.post('/admin/backup/1/delete')
        assert resp.status_code == 200
        assert resp.get_json()['deleted'] == \
            'library_backup_20260101_020000.sql'
        assert not target.exists()
        deletes = [c for c in mock_db['execute'].call_args_list
                   if 'DELETE FROM backup_log' in c[0][0]]
        assert deletes
        assert deletes[0][0][1] == (1,)
        acts = [c[0][1] for c in log_act.call_args_list]
        assert any('backup:deleted:' in a for a in acts)

    def test_delete_missing_row_404(self, admin_client, mock_db):
        mock_db['fetch_one'].return_value = None
        resp = admin_client.post('/admin/backup/9/delete')
        assert resp.status_code == 404
        assert 'not found' in resp.get_json()['error'].lower()

    def test_delete_refused_while_job_running(self, admin_client, mock_db):
        mock_db['fetch_one'].return_value = _row()
        with patch('app.backup.routes.jobs.active_job',
                   return_value={'status': 'running'}):
            resp = admin_client.post('/admin/backup/1/delete')
        assert resp.status_code == 409
        assert 'running' in resp.get_json()['error'].lower()

    def test_delete_missing_file_still_removes_row(self, admin_client,
                                                   mock_db, tmp_path):
        mock_db['fetch_one'].return_value = _row()
        with patch('app.backup.routes.resolve_backup_path',
                   return_value=str(tmp_path / 'gone.sql')), \
             patch('app.backup.routes.log_activity'):
            resp = admin_client.post('/admin/backup/1/delete')
        assert resp.status_code == 200
        assert 'note' in resp.get_json()
        deletes = [c for c in mock_db['execute'].call_args_list
                   if 'DELETE FROM backup_log' in c[0][0]]
        assert deletes
