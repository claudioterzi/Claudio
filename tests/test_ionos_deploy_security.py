"""Security regression tests for IONOS deployers (no network, no paramiko needed)."""

import asyncio
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest import mock

# Load deploy.py on its own: the package __init__ pulls in httpx/boto3.
_spec = importlib.util.spec_from_file_location(
    'ionos_deploy_under_test', Path(__file__).resolve().parents[1] / 'rrremergen' / 'integrations' / 'ionos' / 'deploy.py'
)
deploy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(deploy)


class _FakeSSHClient:
    def __init__(self):
        self.policy = None
        self.system_keys_loaded = False
        self.host_key_files = []
        self.connect_kwargs = None
        self.closed = False

    def load_system_host_keys(self):
        self.system_keys_loaded = True

    def load_host_keys(self, path):
        self.host_key_files.append(path)

    def set_missing_host_key_policy(self, policy):
        self.policy = policy

    def connect(self, host, **kwargs):
        self.connect_kwargs = dict(kwargs, host=host)

    def open_sftp(self):
        sftp = mock.MagicMock()
        sftp.mkdir.side_effect = OSError('exists')
        return sftp

    def exec_command(self, command):
        out = mock.MagicMock()
        out.read.return_value = b'ok'
        err = mock.MagicMock()
        err.read.return_value = b''
        return None, out, err

    def close(self):
        self.closed = True


def _fake_paramiko():
    module = types.ModuleType('paramiko')
    module.created = []

    def factory():
        client = _FakeSSHClient()
        module.created.append(client)
        return client

    module.SSHClient = factory
    module.RejectPolicy = type('RejectPolicy', (), {})
    module.AutoAddPolicy = type('AutoAddPolicy', (), {})
    return module


class SSHHostKeyTests(unittest.TestCase):
    def setUp(self):
        self.paramiko = _fake_paramiko()
        patcher = mock.patch.dict(sys.modules, {'paramiko': self.paramiko})
        patcher.start()
        self.addCleanup(patcher.stop)

    def _assert_rejects_unknown_hosts(self, client, known_hosts):
        self.assertIsInstance(client.policy, self.paramiko.RejectPolicy)
        self.assertTrue(client.system_keys_loaded)
        self.assertEqual(client.host_key_files, [known_hosts])

    def test_sftp_verifies_host_key(self):
        deployer = deploy.IONOSSFTPDeployer({
            'sftp_host': 'sftp.example.test',
            'sftp_username': 'u',
            'sftp_password': 'p',
            'known_hosts': '/tmp/known_hosts',
        })
        result = asyncio.run(deployer.upload_app({'frontend': '<html></html>'}, '/site'))
        self.assertTrue(result['success'], result)
        client = self.paramiko.created[0]
        self._assert_rejects_unknown_hosts(client, '/tmp/known_hosts')
        self.assertTrue(client.closed)

    def test_ssh_verifies_host_key_and_prefers_key_file(self):
        deployer = deploy.IONOSSSHDeployer({
            'ssh_host': 'ssh.example.test',
            'ssh_username': 'u',
            'ssh_password': 'p',
            'ssh_private_key': '/keys/id_ed25519',
            'known_hosts': '/tmp/known_hosts',
        })
        result = asyncio.run(deployer.execute_deployment({}, 'echo ok'))
        self.assertTrue(result['success'], result)
        client = self.paramiko.created[0]
        self._assert_rejects_unknown_hosts(client, '/tmp/known_hosts')
        self.assertEqual(client.connect_kwargs['key_filename'], '/keys/id_ed25519')
        self.assertIsNone(client.connect_kwargs['password'])

    def test_missing_host_is_an_error(self):
        result = asyncio.run(deploy.IONOSSSHDeployer({}).execute_deployment({}, 'true'))
        self.assertFalse(result['success'])


class GitRepoCreationTests(unittest.TestCase):
    def setUp(self):
        self.deployer = deploy.IONOSGitDeployer({'git_host': 'git.example.test', 'git_username': 'u'})

    def test_rejects_shell_metacharacters_in_app_name(self):
        with mock.patch('subprocess.run') as run:
            for name in ('x; rm -rf ~', '$(id)', '../etc', '-oProxyCommand=x', '', 'a' * 65):
                result = asyncio.run(self.deployer.create_git_repo(name))
                self.assertFalse(result['success'], name)
            run.assert_not_called()

    def test_runs_without_local_shell(self):
        with mock.patch('subprocess.run') as run:
            run.return_value = mock.Mock(returncode=0)
            result = asyncio.run(self.deployer.create_git_repo('my-app_1.0'))
        self.assertTrue(result['success'], result)
        args, kwargs = run.call_args
        self.assertEqual(
            args[0],
            ['ssh', '--', 'u@git.example.test', 'git', 'init', '--bare', '/var/git/my-app_1.0.git'],
        )
        self.assertNotIn('shell', kwargs)


class FTPSTests(unittest.TestCase):
    def test_uses_tls_on_control_and_data_channels(self):
        ftp = mock.MagicMock()
        with mock.patch('ftplib.FTP_TLS', return_value=ftp) as ftp_tls, \
                mock.patch('ftplib.FTP') as plain_ftp:
            deployer = deploy.IONOSFTPDeployer({'ftp_username': 'u', 'ftp_password': 'p'})
            result = asyncio.run(deployer.upload_app({'frontend': '<html></html>'}))
        self.assertTrue(result['success'], result)
        self.assertEqual(result['method'], 'FTPS')
        ftp_tls.assert_called_once()
        plain_ftp.assert_not_called()
        calls = [c[0] for c in ftp.method_calls]
        self.assertLess(calls.index('auth'), calls.index('login'))
        self.assertLess(calls.index('login'), calls.index('prot_p'))


if __name__ == '__main__':
    unittest.main()
