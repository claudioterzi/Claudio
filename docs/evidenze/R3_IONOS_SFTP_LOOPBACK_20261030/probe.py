"""Real SSH/SFTP loopback probe. Requires paramiko; never contacts IONOS."""
import asyncio
import errno
import importlib.util
import json
import os
from pathlib import Path
import secrets
import socket
import tempfile
import threading
import time

import paramiko

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('ionos_probe', ROOT / 'rrremergen/integrations/ionos/deploy.py')
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)


def main():
    with tempfile.TemporaryDirectory(prefix='ionos-loopback-') as tmp:
        root = Path(tmp)
        remote = root / 'remote'
        remote.mkdir()
        secret = secrets.token_urlsafe(32)
        fault = {'mode': 'none'}
        connections = []
        stopped = threading.Event()

        class Auth(paramiko.ServerInterface):
            def check_auth_password(self, username, password):
                return paramiko.AUTH_SUCCESSFUL if username == 'probe' and password == secret else paramiko.AUTH_FAILED

            def get_allowed_auths(self, username):
                return 'password'

            def check_channel_request(self, kind, channel_id):
                return paramiko.OPEN_SUCCEEDED if kind == 'session' else paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

        class Files(paramiko.SFTPServerInterface):
            def local(self, path):
                p = (remote / path.lstrip('/')).resolve()
                if not p.is_relative_to(remote):
                    raise PermissionError(errno.EACCES, 'outside fixture')
                return p

            def stat(self, path):
                try:
                    return paramiko.SFTPAttributes.from_stat(self.local(path).stat())
                except OSError as exc:
                    return paramiko.SFTPServer.convert_errno(exc.errno)

            lstat = stat

            def mkdir(self, path, attr):
                try:
                    self.local(path).mkdir()
                    return paramiko.SFTP_OK
                except OSError as exc:
                    return paramiko.SFTPServer.convert_errno(exc.errno)

            def open(self, path, flags, attr):
                try:
                    fd = os.open(self.local(path), flags, 0o600)
                    mode = 'r+b' if flags & os.O_RDWR else 'wb' if flags & os.O_WRONLY else 'rb'
                    file = os.fdopen(fd, mode)
                    handle = paramiko.SFTPHandle(flags)
                    if flags & (os.O_WRONLY | os.O_RDWR):
                        handle.writefile = file
                    else:
                        handle.readfile = file
                    return handle
                except OSError as exc:
                    return paramiko.SFTPServer.convert_errno(exc.errno)

            def rename(self, old, new):
                try:
                    if fault['mode'] in {'publish', 'both'} and '.staging-' in old:
                        raise PermissionError(errno.EACCES, 'injected publish rejection')
                    if fault['mode'] == 'both' and '.previous-' in old:
                        raise PermissionError(errno.EACCES, 'injected recovery rejection')
                    if self.local(new).exists():
                        raise FileExistsError(errno.EEXIST, 'destination exists')
                    self.local(old).rename(self.local(new))
                    return paramiko.SFTP_OK
                except OSError as exc:
                    return paramiko.SFTPServer.convert_errno(exc.errno)

        server_key = paramiko.RSAKey.generate(2048)
        listener = socket.socket()
        listener.bind(('127.0.0.1', 0))
        listener.listen(4)
        listener.settimeout(0.2)
        port = listener.getsockname()[1]
        known_hosts = root / 'known_hosts'
        known_hosts.write_text(f'[127.0.0.1]:{port} {server_key.get_name()} {server_key.get_base64()}\n')

        def serve():
            while not stopped.is_set():
                try:
                    client, _ = listener.accept()
                except socket.timeout:
                    continue
                except OSError:
                    break
                transport = paramiko.Transport(client)
                connections.append(transport)
                transport.add_server_key(server_key)
                transport.set_subsystem_handler('sftp', paramiko.SFTPServer, Files)
                transport.start_server(server=Auth())

        worker = threading.Thread(target=serve, daemon=True)
        worker.start()
        source = root / 'source'
        source.mkdir()
        (source / 'index.html').write_text('<html>new fixture</html>')
        release = deploy.PreparedRelease(deploy.STATIC, source)
        credentials = {'sftp_host': '127.0.0.1', 'sftp_port': str(port),
                       'sftp_username': 'probe', 'sftp_password': secret,
                       'known_hosts': str(known_hosts)}
        uploader = deploy.IONOSSFTPDeployer(credentials)
        results = []
        try:
            for case in ('normal', 'publish', 'both'):
                target = remote / case
                target.mkdir()
                (target / 'index.html').write_text('<html>old fixture</html>')
                fault['mode'] = 'none' if case == 'normal' else case
                result = asyncio.run(uploader.upload_app(release, '/' + case))
                if case == 'normal':
                    assert result['success']
                    assert (target / 'index.html').read_text() == '<html>new fixture</html>'
                    recovery = asyncio.run(uploader.rollback(result))
                    assert recovery['success']
                    assert (target / 'index.html').read_text() == '<html>old fixture</html>'
                elif case == 'publish':
                    assert not result['success'] and result['rollback']['success']
                    assert (target / 'index.html').read_text() == '<html>old fixture</html>'
                else:
                    assert not result['success'] and not result['rollback']['success']
                    assert result['manual_recovery_required']
                    assert (remote / result['previous'].lstrip('/') / 'index.html').read_text() == '<html>old fixture</html>'
                results.append({'case': case, 'passed': True})
            print(json.dumps({'scope': 'real authenticated SSH/SFTP on loopback only',
                              'ionos_host_tested': False, 'host_key_verification': 'RejectPolicy with pinned temporary host key',
                              'paramiko': paramiko.__version__, 'results': results}, indent=2))
        finally:
            stopped.set()
            listener.close()
            for transport in connections:
                transport.close()
            worker.join(timeout=2)


if __name__ == '__main__':
    main()
