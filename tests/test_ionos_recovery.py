"""Fault injection on real temporary directories; SSH replies are bounded stubs."""
import asyncio
import importlib.util
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_spec = importlib.util.spec_from_file_location(
    'ionos_recovery_under_test', Path(__file__).resolve().parents[1]
    / 'rrremergen/integrations/ionos/deploy.py')
deploy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(deploy)


class DirectoryDeployer(deploy._StaticSwapDeployer):
    method = 'LOCAL_FAULT_FIXTURE'

    def __init__(self, root):
        self.root = root
        self.fault = lambda old, new, after: None

    def path(self, name):
        return self.root / name.lstrip('/')

    def _connect(self):
        return self

    def _close(self, conn):
        pass

    def _exists(self, conn, name):
        return self.path(name).is_dir()

    def _mkdir(self, conn, name):
        self.path(name).mkdir()

    def _put(self, conn, local, remote):
        shutil.copyfile(local, self.path(remote))

    def _rename(self, conn, old, new):
        self.fault(old, new, False)
        self.path(old).rename(self.path(new))
        self.fault(old, new, True)


class DirectoryRecoveryTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        remote = self.root / 'remote'
        remote.mkdir()
        self.deployer = DirectoryDeployer(remote)
        self.deployer.path('/app').mkdir()
        self.deployer.path('/app/index.html').write_text('old site')
        source = self.root / 'source'
        source.mkdir()
        (source / 'index.html').write_text('new site')
        self.release = deploy.PreparedRelease(deploy.STATIC, source)

    def upload(self):
        return asyncio.run(self.deployer.upload_app(self.release, '/app'))

    def test_second_rename_failure_restores_exact_old_files(self):
        def fault(old, new, after):
            if '.staging-' in old and not after:
                raise OSError('publish failed')
        self.deployer.fault = fault
        result = self.upload()
        self.assertFalse(result['success'])
        self.assertTrue(result['rollback']['success'])
        self.assertFalse(result['manual_recovery_required'])
        self.assertEqual(self.deployer.path('/app/index.html').read_text(), 'old site')
        self.assertEqual(self.deployer.path(result['staging'] + '/index.html').read_text(), 'new site')

    def test_lost_reply_after_each_rename_recovers(self):
        for point in ('first', 'second'):
            with self.subTest(point=point):
                def fault(old, new, after):
                    if after and ((point == 'first' and '.previous-' in new)
                                  or (point == 'second' and '.staging-' in old)):
                        raise OSError('reply lost after remote rename')
                self.deployer.fault = fault
                result = self.upload()
                self.assertFalse(result['success'])
                self.assertTrue(result['rollback']['success'])
                self.assertEqual(self.deployer.path('/app/index.html').read_text(), 'old site')

    def test_recovery_failure_retains_previous_and_reports_manual_recovery(self):
        def fault(old, new, after):
            if not after and ('.staging-' in old or '.previous-' in old):
                raise OSError('injected transfer fault')
        self.deployer.fault = fault
        result = self.upload()
        self.assertFalse(result['success'])
        self.assertFalse(result['rollback']['success'])
        self.assertIsNone(result['rollback']['restored'])
        self.assertTrue(result['manual_recovery_required'])
        self.assertEqual(self.deployer.path(result['previous'] + '/index.html').read_text(), 'old site')

    def test_failed_explicit_rollback_reinstates_parked_active_version(self):
        result = self.upload()
        def fault(old, new, after):
            if '.previous-' in old and not after:
                raise OSError('previous cannot move')
        self.deployer.fault = fault
        recovery = asyncio.run(self.deployer.rollback(result))
        self.assertFalse(recovery['success'])
        self.assertIsNone(recovery['restored'])
        self.assertTrue(recovery['active_release_reinstated'])
        self.assertEqual(self.deployer.path('/app/index.html').read_text(), 'new site')
        self.assertEqual(self.deployer.path(result['previous'] + '/index.html').read_text(), 'old site')

    def test_missing_previous_does_not_remove_active_version(self):
        recovery = asyncio.run(self.deployer.rollback({'path': '/app', 'previous': '/app.previous-missing'}))
        self.assertFalse(recovery['success'])
        self.assertEqual(self.deployer.path('/app/index.html').read_text(), 'old site')

    def test_first_release_rollback_reports_removal_not_restoration(self):
        shutil.rmtree(self.deployer.path('/app'))
        result = self.upload()
        recovery = asyncio.run(self.deployer.rollback(result))
        self.assertTrue(recovery['success'])
        self.assertIsNone(recovery['restored'])
        self.assertEqual(recovery['outcome'], 'FIRST_RELEASE_REMOVED')
        self.assertFalse(self.deployer.path('/app').exists())
        self.assertEqual(self.deployer.path(recovery['parked'] + '/index.html').read_text(), 'new site')

    def test_noop_restore_cannot_pass_readback(self):
        real_rename = self.deployer._rename
        def rename(conn, old, new):
            if '.previous-' not in old:
                real_rename(conn, old, new)
        self.deployer._rename = rename
        result = self.upload()
        recovery = asyncio.run(self.deployer.rollback(result))
        self.assertFalse(recovery['success'])
        self.assertIsNone(recovery['restored'])
        self.assertEqual(self.deployer.path('/app/index.html').read_text(), 'new site')

    def test_release_names_are_unique_with_frozen_clock(self):
        with mock.patch.object(deploy.time, 'strftime', return_value='20261030-120000'):
            self.assertEqual(len({deploy._release_stamp() for _ in range(100)}), 100)

    def test_root_aliases_are_rejected_before_connecting(self):
        with mock.patch.object(self.deployer, '_connect') as connect:
            for path in ('/.', '/app/..', '/app/.', '/'):
                with self.subTest(path=path):
                    result = asyncio.run(self.deployer.upload_app(self.release, path))
                    self.assertFalse(result['success'])
            connect.assert_not_called()


class ServiceRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.deployer = deploy.IONOSServiceDeployer({})
        self.ssh = mock.MagicMock()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.release = deploy.PreparedRelease(deploy.PYTHON_SERVICE, Path(tmp.name))

    def run_failure(self, rollback_reply, readback=(0, '/app/releases/old\n'), previous='/app/releases/old'):
        replies = [(0, previous), (0, ''), (1, 'restart failed'), rollback_reply, readback]
        with mock.patch.object(self.deployer, '_connect', return_value=self.ssh), \
                mock.patch.object(self.deployer, '_exec', side_effect=replies) as execute:
            result = asyncio.run(self.deployer.deploy_service(self.release, '/app', 'restart-app'))
        return result, execute

    def test_failed_restart_has_verified_recovery(self):
        result, _ = self.run_failure((0, ''))
        self.assertFalse(result['success'])
        self.assertTrue(result['rollback']['success'])
        self.assertEqual(result['rollback']['restored'], '/app/releases/old')
        self.assertFalse(result['manual_recovery_required'])

    def test_failed_recovery_never_claims_previous_restored(self):
        result, execute = self.run_failure((9, 'recovery failed'))
        self.assertFalse(result['rollback']['success'])
        self.assertIsNone(result['rollback']['restored'])
        self.assertTrue(result['manual_recovery_required'])
        self.assertEqual(execute.call_count, 4)

    def test_wrong_symlink_readback_fails_even_after_zero_exit(self):
        result, _ = self.run_failure((0, ''), (0, '/app/releases/new'))
        self.assertFalse(result['rollback']['success'])
        self.assertIsNone(result['rollback']['restored'])

    def test_first_service_release_does_not_invent_a_previous_release(self):
        result, execute = self.run_failure((0, ''), previous='')
        self.assertFalse(result['rollback']['success'])
        self.assertIsNone(result['rollback']['restored'])
        self.assertEqual(execute.call_count, 3)

    def test_restart_transport_exception_also_attempts_recovery(self):
        replies = [(0, '/app/releases/old'), (0, ''), OSError('reply lost'),
                   (0, ''), (0, '/app/releases/old')]
        with mock.patch.object(self.deployer, '_connect', return_value=self.ssh), \
                mock.patch.object(self.deployer, '_exec', side_effect=replies):
            result = asyncio.run(self.deployer.deploy_service(self.release, '/app', 'restart-app'))
        self.assertFalse(result['success'])
        self.assertTrue(result['rollback']['success'])

    def test_preparation_failure_is_not_masked_by_readlink(self):
        with mock.patch.object(self.deployer, '_connect', return_value=self.ssh), \
                mock.patch.object(self.deployer, '_exec', return_value=(1, 'mkdir denied')) as execute:
            result = asyncio.run(self.deployer.deploy_service(self.release, '/app', 'restart-app'))
        self.assertFalse(result['success'])
        self.assertEqual(execute.call_count, 1)
        self.assertNotIn('|| true', execute.call_args.args[1])
        self.ssh.open_sftp.assert_not_called()

    @unittest.skipUnless(shutil.which('sh'), 'POSIX shell required')
    def test_real_symlink_restore_and_restart_failure(self):
        base = self.release.root / 'app'
        old, new = base / 'releases/old', base / 'releases/new'
        old.mkdir(parents=True)
        new.mkdir()
        (old / 'state').write_text('old')
        (new / 'state').write_text('new')
        (base / 'current').symlink_to(new)

        def execute(ssh, command):
            # Locally generated commands and temporary paths; no remote connection.
            result = subprocess.run(['sh', '-c', command], capture_output=True, text=True)  # nosec B603
            return result.returncode, result.stdout + result.stderr

        with mock.patch.object(self.deployer, '_exec', side_effect=execute):
            good = self.deployer._restore_service(self.ssh, str(old), str(base), 'true')
            self.assertTrue(good['success'])
            self.assertEqual((base / 'current/state').read_text(), 'old')
            self.assertEqual((new / 'state').read_text(), 'new')
            bad = self.deployer._restore_service(self.ssh, str(old), str(base), 'false')
            self.assertFalse(bad['success'])
            self.assertIsNone(bad['restored'])


if __name__ == '__main__':
    unittest.main()
