"""Security regression tests for IONOS deployers (no network, no paramiko needed)."""

import asyncio
import importlib.util
import os
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
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

    exit_status = 0

    def exec_command(self, command):
        out = mock.MagicMock()
        out.read.return_value = b'ok'
        out.channel.recv_exit_status.return_value = self.exit_status
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

    def test_ssh_failure_is_reported_even_with_empty_stderr(self):
        with mock.patch.object(_FakeSSHClient, 'exit_status', 1):
            result = asyncio.run(deploy.IONOSSSHDeployer({'ssh_host': 'h'}).execute_deployment({}, 'false'))
        self.assertFalse(result['success'])
        self.assertEqual(result['exit_status'], 1)

    def test_missing_host_is_an_error(self):
        result = asyncio.run(deploy.IONOSSSHDeployer({}).execute_deployment({}, 'true'))
        self.assertFalse(result['success'])


class _PreparedTempDir:
    """Stand-in for tempfile.TemporaryDirectory that yields a directory prepared by the test."""

    def __init__(self, path):
        self.path = path

    def __call__(self, *args, **kwargs):
        return self

    def __enter__(self):
        return str(self.path)

    def __exit__(self, *exc):
        return False


class GitPushFilesystemTests(unittest.TestCase):
    def setUp(self):
        self.deployer = deploy.IONOSGitDeployer({'git_host': 'git.example.test', 'git_username': 'u'})
        self.base = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.base, True)

    @unittest.skipUnless(hasattr(os, 'symlink'), 'symlinks not supported')
    def test_symlinks_inside_the_deploy_root_cannot_redirect_writes(self):
        outside = self.base / 'outside'
        outside.mkdir()
        sentinel = outside / 'sentinel.txt'
        sentinel.write_text('ORIGINAL')
        root = self.base / 'root'
        root.mkdir()
        try:
            (root / 'linkdir').symlink_to(outside, target_is_directory=True)
            (root / 'linkfile.txt').symlink_to(sentinel)
        except OSError as exc:  # e.g. Windows without symlink privilege
            self.skipTest(f'cannot create symlinks here: {exc}')

        with mock.patch('tempfile.TemporaryDirectory', _PreparedTempDir(root)), \
                mock.patch('subprocess.run', return_value=mock.Mock(returncode=0)):
            via_dir = asyncio.run(self.deployer.push_and_deploy(
                {'linkdir/new.txt': 'X'}, 'app', 'u@h.example:repo.git'))
            via_file = asyncio.run(self.deployer.push_and_deploy(
                {'linkfile.txt': 'X'}, 'app', 'u@h.example:repo.git'))

        self.assertFalse(via_dir['success'], via_dir)
        self.assertFalse(via_file['success'], via_file)
        self.assertFalse((outside / 'new.txt').exists())
        self.assertEqual(sentinel.read_text(), 'ORIGINAL')

    @unittest.skipUnless(shutil.which('git'), 'git not available')
    def test_real_git_commits_nested_files(self):
        real_run = subprocess.run
        pushed = {}

        def run(cmd, *args, **kwargs):
            if cmd[:2] == ['git', 'push']:
                listing = real_run(['git', 'ls-files'], cwd=kwargs['cwd'], env=kwargs['env'],
                                   capture_output=True, text=True, check=True)
                pushed['files'] = sorted(listing.stdout.split())
                pushed['ssh'] = kwargs['env']['GIT_SSH_COMMAND']
                return mock.Mock(returncode=0)
            return real_run(cmd, *args, capture_output=True, **kwargs)

        with mock.patch('subprocess.run', side_effect=run):
            result = asyncio.run(self.deployer.push_and_deploy(
                {'index.html': 'a', 'public/css/site.css': 'b'}, 'app', 'u@h.example:repo.git'))

        self.assertTrue(result['success'], result)
        self.assertEqual(pushed['files'], ['index.html', 'public/css/site.css'])
        self.assertIn('StrictHostKeyChecking=yes', pushed['ssh'])


class GitRepoCreationTests(unittest.TestCase):
    def setUp(self):
        self.deployer = deploy.IONOSGitDeployer({
            'git_host': 'git.example.test',
            'git_username': 'u',
            'known_hosts': '/tmp/known hosts',
        })

    def test_rejects_shell_metacharacters_in_app_name(self):
        with mock.patch('subprocess.run') as run:
            for name in ('x; rm -rf ~', '$(id)', '../etc', '-oProxyCommand=x', '', 'a' * 65,
                         'x\n', 'x\nid'):
                result = asyncio.run(self.deployer.create_git_repo(name))
                self.assertFalse(result['success'], repr(name))
            run.assert_not_called()

    def test_runs_without_local_shell_and_with_strict_host_keys(self):
        with mock.patch('subprocess.run') as run:
            run.return_value = mock.Mock(returncode=0)
            result = asyncio.run(self.deployer.create_git_repo('my-app_1.0'))
        self.assertTrue(result['success'], result)
        args, kwargs = run.call_args
        self.assertEqual(
            args[0],
            ['ssh', '-o', 'StrictHostKeyChecking=yes', '-o', 'BatchMode=yes',
             '-o', 'UserKnownHostsFile=/tmp/known hosts', '--',
             'u@git.example.test', 'git', 'init', '--bare', '/var/git/my-app_1.0.git'],
        )
        self.assertNotIn('shell', kwargs)

    def test_git_push_rejects_option_like_or_foreign_remotes(self):
        with mock.patch('subprocess.run') as run:
            for remote in ('--receive-pack=x', '-oProxyCommand=x', '--repo=ext::sh', 'ext::sh -c id',
                           'file:///etc', 'ssh://u@h/repo\n', '', 'u@h:repo; id'):
                result = asyncio.run(self.deployer.push_and_deploy({'a': 'b'}, 'app', remote))
                self.assertFalse(result['success'], repr(remote))
            run.assert_not_called()

    def test_unsafe_file_names_are_rejected_before_any_write_or_git(self):
        outside = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, outside, True)
        sentinel = outside / 'sentinel.txt'
        sentinel.write_text('ORIGINAL')
        bad_names = [str(sentinel), '/etc/passwd', '../escape.txt', 'a/../../escape.txt', './x', 'a//b',
                     '', 'C:/x.txt', 'C:x.txt', '\\\\server\\share\\x', 'dir\\x.txt', '.git/config',
                     '.GIT/hooks/pre-commit', 'sub/.git/config', '.git./config', '.git /config',
                     'GIT~1/config', 'file.txt:stream', 'nul\x00.txt']
        with mock.patch('subprocess.run') as run:
            for name in bad_names:
                result = asyncio.run(self.deployer.push_and_deploy(
                    {'ok.txt': 'fine', name: 'OVERWRITTEN'}, 'app', 'ssh://u@h.example/r.git'))
                self.assertFalse(result['success'], repr(name))
            run.assert_not_called()
        self.assertEqual(sentinel.read_text(), 'ORIGINAL')

    def test_nested_valid_names_are_written_inside_the_temp_root(self):
        written = {}

        def fake_run(cmd, cwd=None, **kwargs):
            if cmd[:2] == ['git', 'add']:
                root = Path(cwd)
                written.update({p.relative_to(root).as_posix(): p.read_text()
                                for p in root.rglob('*') if p.is_file()})
            return mock.Mock(returncode=0)

        with mock.patch('subprocess.run', side_effect=fake_run) as run:
            result = asyncio.run(self.deployer.push_and_deploy(
                {'index.html': 'a', 'public/css/site.css': 'b', 'api/v1/x.py': 'c'},
                'app', 'u@h.example:repo.git'))
        self.assertTrue(result['success'], result)
        self.assertEqual(written, {'index.html': 'a', 'public/css/site.css': 'b', 'api/v1/x.py': 'c'})
        for call in run.call_args_list:
            self.assertEqual(call.kwargs['env']['GIT_CONFIG_NOSYSTEM'], '1')
            self.assertEqual(call.kwargs['env']['GIT_CONFIG_GLOBAL'], os.devnull)

    def test_git_push_uses_strict_host_keys(self):
        with mock.patch('subprocess.run') as run:
            result = asyncio.run(self.deployer.push_and_deploy(
                {'index.html': '<html></html>'}, 'app', 'ssh://u@git.example.test/var/git/app.git'))
        self.assertTrue(result['success'], result)
        push = [c for c in run.call_args_list if c.args[0][:2] == ['git', 'push']]
        self.assertEqual(len(push), 1)
        ssh_command = push[0].kwargs['env']['GIT_SSH_COMMAND']
        self.assertEqual(
            ssh_command,
            "ssh -o StrictHostKeyChecking=yes -o BatchMode=yes "
            "-o 'UserKnownHostsFile=/tmp/known hosts'",
        )


class FTPSTests(unittest.TestCase):
    def test_uses_tls_on_control_and_data_channels(self):
        ftp = mock.MagicMock()
        with mock.patch('ftplib.FTP_TLS', return_value=ftp) as ftp_tls, \
                mock.patch('ftplib.FTP') as plain_ftp:
            deployer = deploy.IONOSFTPDeployer({'ftp_username': 'u', 'ftp_password': 'p'})
            result = asyncio.run(deployer.upload_app({'frontend': '<html></html>'}))
        self.assertTrue(result['success'], result)
        self.assertEqual(result['method'], 'FTPS')
        plain_ftp.assert_not_called()
        context = ftp_tls.call_args.kwargs['context']
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(context.check_hostname)
        calls = [c[0] for c in ftp.method_calls]
        self.assertLess(calls.index('auth'), calls.index('login'))
        self.assertLess(calls.index('login'), calls.index('prot_p'))


class FTPSUploadFailureTests(unittest.TestCase):
    def test_failed_upload_is_not_reported_as_success(self):
        ftp = mock.MagicMock()
        ftp.storbinary.side_effect = OSError('550 permission denied')
        with mock.patch('ftplib.FTP_TLS', return_value=ftp):
            deployer = deploy.IONOSFTPDeployer({'ftp_username': 'u', 'ftp_password': 'p'})
            result = asyncio.run(deployer.upload_app({'frontend': 'x', 'backend': 'y'}))
        self.assertFalse(result['success'])
        self.assertIn('frontend', result['error'])
        self.assertIn('backend', result['error'])


@unittest.skipUnless(shutil.which('openssl'), 'openssl CLI not available')
class TLSHandshakeTests(unittest.TestCase):
    """Real TLS handshakes against a local server: the FTPS context must refuse bad certs."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.cert = Path(cls.tmp.name) / 'cert.pem'
        cls.key = Path(cls.tmp.name) / 'key.pem'
        subprocess.run(
            ['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1',
             '-subj', '/CN=localhost', '-addext', 'subjectAltName=DNS:localhost',
             '-keyout', str(cls.key), '-out', str(cls.cert)],
            check=True, capture_output=True,
        )

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def _serve_once(self):
        server_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        server_ctx.load_cert_chain(self.cert, self.key)
        listener = socket.create_server(('127.0.0.1', 0))
        self.addCleanup(listener.close)

        def accept():
            try:
                conn, _ = listener.accept()
                with server_ctx.wrap_socket(conn, server_side=True):
                    pass
            except (OSError, ssl.SSLError):
                pass

        threading.Thread(target=accept, daemon=True).start()
        return listener.getsockname()[1]

    def _handshake(self, context, server_hostname):
        port = self._serve_once()
        with socket.create_connection(('127.0.0.1', port), timeout=5) as raw, \
                context.wrap_socket(raw, server_hostname=server_hostname):
            pass

    def test_rejects_untrusted_self_signed_certificate(self):
        with self.assertRaises(ssl.SSLCertVerificationError):
            self._handshake(deploy._tls_context(), 'localhost')

    def test_rejects_hostname_mismatch_even_with_trusted_ca(self):
        context = deploy._tls_context()
        context.load_verify_locations(self.cert)
        self._handshake(context, 'localhost')  # trusted CA + right name: accepted
        with self.assertRaises(ssl.SSLCertVerificationError):
            self._handshake(context, 'ftp.ionos.com')


if __name__ == '__main__':
    unittest.main()
