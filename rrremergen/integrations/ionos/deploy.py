#!/usr/bin/env python3
"""
IONOS Direct Deployment — build, publish and verify generated apps.

Raw source is never published: prepare_project() writes the complete generated
project, builds it (React/Vite → dist/) or checks it (FastAPI → service bundle
with requirements and an ASGI server), and only the result is transferred.

Targets, chosen by the IONOS contract:
1. FTPS / SFTP — Web Hosting: static build, uploaded to a staging folder and swapped in
2. SSH service — VPS / Cloud Server: FastAPI release with its own venv, symlink switch
3. Git Push — Git repository on IONOS hosting
4. SSH Exec — operator-supplied deployment script

After publishing, verify_public() checks the page and the API from outside;
on failure the previous version is put back.

Every SSH-based connection verifies the server host key against known_hosts
(system file, or the path given as 'known_hosts' in the credentials) and
refuses unknown hosts.
"""

import os
import re
import json
import time
import shlex
import ssl
import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path, PurePosixPath

# Repository names end up in a remote shell command: allow only safe characters.
# Always use fullmatch: '$' alone would also accept a trailing newline.
_SAFE_APP_NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,63}')

# Push targets: ssh://user@host[:port]/path or scp-style user@host:path, nothing that git
# could read as an option or as another transport (ext::, file://, ...).
_SAFE_GIT_REMOTE = re.compile(
    r'ssh://[A-Za-z0-9._-]+@[A-Za-z0-9.-]+(:\d{1,5})?/[A-Za-z0-9._/-]+'
    r'|[A-Za-z0-9._-]+@[A-Za-z0-9.-]+:[A-Za-z0-9._/-]+'
)


def _safe_relative_path(name: Any) -> Optional[PurePosixPath]:
    """Return name as a relative POSIX path if it is safe to write under a deploy root.

    Rejects empty names, absolute paths, Windows drives/UNC/backslashes, '.' and '..'
    components, NTFS streams and anything that is or aliases a .git directory.
    """
    if not isinstance(name, str) or not name or '\\' in name or '\x00' in name or ':' in name:
        return None
    if name.startswith('/'):
        return None
    parts = name.split('/')
    for part in parts:
        if part in ('', '.', '..'):
            return None
        folded = part.rstrip(' .').lower()
        if folded == '.git' or folded.startswith('git~'):
            return None
    return PurePosixPath(*parts)


def _tls_context() -> ssl.SSLContext:
    """TLS context that verifies the server certificate and hostname."""
    return ssl.create_default_context()


def _ssh_options(known_hosts: Optional[str] = None) -> List[str]:
    """OpenSSH options that refuse unknown or changed host keys, never prompting."""
    options = ['-o', 'StrictHostKeyChecking=yes', '-o', 'BatchMode=yes']
    if known_hosts:
        options += ['-o', f'UserKnownHostsFile={known_hosts}']
    return options


def _connect_ssh_client(
    host: Optional[str],
    port: int,
    username: Optional[str],
    password: Optional[str] = None,
    key_filename: Optional[str] = None,
    known_hosts: Optional[str] = None,
):
    """Open a paramiko SSHClient that rejects hosts missing from known_hosts."""
    import paramiko

    if not host:
        raise ValueError('SSH host not configured')

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    if known_hosts:
        client.load_host_keys(known_hosts)
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    client.connect(
        host,
        port=port,
        username=username,
        password=None if key_filename else password,
        key_filename=key_filename,
        look_for_keys=False,
        allow_agent=False,
        timeout=30,
    )
    return client

# ---------------------------------------------------------------------------
# Release preparation: what gets published is a build, never raw source.
#
# The generator produces a complete project ({relative path: content}). Before
# anything leaves this machine it is written to a work directory, built and
# checked: a React/Vite project becomes its dist/ (or build/) folder, a FastAPI
# project becomes a service bundle with requirements and a start command.
# A static web space can only receive the first kind; the second needs a host
# that keeps a Python process running (VPS / Cloud Server).
# ---------------------------------------------------------------------------

STATIC = 'static'
PYTHON_SERVICE = 'python-service'

# Sources that a web server would hand out as text instead of running them.
_UNBUILT_SUFFIXES = ('.jsx', '.tsx', '.ts', '.vue', '.svelte')
_SOURCE_MARKERS = ('<?php', 'import React', 'from fastapi', 'export default function')
# The legacy single-string payload this bridge used to upload as index.html/index.php/index.js.
_LEGACY_KEYS = {'frontend', 'backend', 'database'}

_SAFE_REMOTE_DIR = re.compile(r'/[A-Za-z0-9._/-]*')


class ReleaseError(Exception):
    """The project cannot be turned into something publishable."""


@dataclass
class PreparedRelease:
    """A built, checked release ready to be transferred."""

    kind: str                       # STATIC or PYTHON_SERVICE
    root: Path                      # directory whose content is published
    start_command: Optional[List[str]] = None
    log: List[str] = field(default_factory=list)

    def files(self) -> List[PurePosixPath]:
        out = []
        for path in sorted(self.root.rglob('*')):
            if path.is_symlink():
                raise ReleaseError(f"Symlink in release: {path.relative_to(self.root)}")
            if path.is_file():
                out.append(PurePosixPath(*path.relative_to(self.root).parts))
        return out


def _is_legacy_payload(app_code: Any) -> bool:
    return isinstance(app_code, dict) and bool(app_code) and set(app_code) <= _LEGACY_KEYS


def _write_project(project: Dict[str, str], root: Path) -> None:
    root = root.resolve()
    for name, content in project.items():
        relative = _safe_relative_path(name)
        if relative is None:
            raise ReleaseError(f"Invalid file name in project: {name!r}")
        if not isinstance(content, str):
            raise ReleaseError(f"File content must be text: {name!r}")
        target = root.joinpath(*relative.parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.parent.resolve() != root and root not in target.parent.resolve().parents:
            raise ReleaseError(f"File escapes project directory: {name!r}")
        target.write_text(content, encoding='utf-8')


def _run(runner, cmd: List[str], cwd: Path, log: List[str], timeout: int = 900) -> None:
    log.append('$ ' + shlex.join(cmd))
    result = runner(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout)  # nosec B603
    tail = ((result.stdout or '') + (result.stderr or '')).strip().splitlines()[-20:]
    log.extend(tail)
    if result.returncode != 0:
        raise ReleaseError(f"{shlex.join(cmd)} failed (exit {result.returncode}): " + ' | '.join(tail[-5:]))


def _check_static_output(out_dir: Path) -> None:
    if not (out_dir / 'index.html').is_file():
        raise ReleaseError(f"Build output {out_dir.name}/ has no index.html")
    for path in out_dir.rglob('*'):
        if path.is_file() and path.suffix in _UNBUILT_SUFFIXES:
            raise ReleaseError(f"Unbuilt source in publishable output: {path.relative_to(out_dir)}")
    html = (out_dir / 'index.html').read_text(encoding='utf-8', errors='replace')
    for marker in _SOURCE_MARKERS:
        if marker in html:
            raise ReleaseError(f"index.html still contains source code ({marker!r})")


def _build_node(root: Path, runner, log: List[str]) -> PreparedRelease:
    try:
        package = json.loads((root / 'package.json').read_text(encoding='utf-8'))
    except ValueError as exc:
        raise ReleaseError(f"package.json is not valid JSON: {exc}") from exc
    if 'build' not in (package.get('scripts') or {}):
        raise ReleaseError("package.json has no 'build' script: nothing produces publishable files")
    if (root / 'package-lock.json').is_file():
        _run(runner, ['npm', 'ci', '--no-audit', '--no-fund'], root, log)
    else:
        _run(runner, ['npm', 'install', '--no-audit', '--no-fund'], root, log)
    _run(runner, ['npm', 'run', 'build'], root, log)
    for candidate in ('dist', 'build'):
        out_dir = root / candidate
        if out_dir.is_dir():
            _check_static_output(out_dir)
            return PreparedRelease(STATIC, out_dir, log=log)
    raise ReleaseError("npm run build produced neither dist/ nor build/")


def _requirement_names(text: str) -> set:
    names = set()
    for line in text.splitlines():
        line = line.split('#', 1)[0].strip()
        match = re.match(r'([A-Za-z0-9_.-]+)', line)
        if match and not line.startswith('-'):
            names.add(match.group(1).lower().replace('_', '-'))
    return names


def _prepare_fastapi(root: Path, log: List[str]) -> PreparedRelease:
    requirements = root / 'requirements.txt'
    if not requirements.is_file():
        raise ReleaseError("Python service without requirements.txt: the server cannot install it")
    names = {n.split('[', 1)[0] for n in _requirement_names(requirements.read_text(encoding='utf-8'))}
    if 'fastapi' not in names:
        raise ReleaseError("requirements.txt does not list fastapi")
    if not names & {'uvicorn', 'gunicorn'}:
        raise ReleaseError("requirements.txt lists no ASGI server (uvicorn/gunicorn): nothing would run the app")

    entry = None
    for path in sorted(root.rglob('*.py')):
        source = path.read_text(encoding='utf-8')
        try:
            compile(source, str(path.relative_to(root)), 'exec')
        except SyntaxError as exc:
            raise ReleaseError(f"Syntax error in {path.relative_to(root)}: {exc}") from exc
        match = re.search(r'^(\w+)\s*=\s*FastAPI\(', source, re.M)
        if match and entry is None:
            module = '.'.join(path.relative_to(root).with_suffix('').parts)
            entry = f"{module}:{match.group(1)}"
    if entry is None:
        raise ReleaseError("No module assigns a FastAPI() application")
    log.append(f"FastAPI entry point: {entry} (static check; dependencies are installed on the server)")
    return PreparedRelease(
        PYTHON_SERVICE, root,
        start_command=['uvicorn', entry, '--host', '127.0.0.1', '--port', '8000'],
        log=log,
    )


def _prepare_one(root: Path, runner) -> PreparedRelease:
    log: List[str] = []
    if (root / 'package.json').is_file():
        return _build_node(root, runner, log)
    if (root / 'requirements.txt').is_file() or (root / 'pyproject.toml').is_file():
        return _prepare_fastapi(root, log)
    if (root / 'index.html').is_file():
        _check_static_output(root)
        return PreparedRelease(STATIC, root, log=['plain static site, no build step'])
    raise ReleaseError(
        f"{root.name or 'project'}: no package.json, requirements.txt or index.html — "
        "cannot tell how to build or run it"
    )


def prepare_project(
    project: Dict[str, str],
    workdir: Path,
    runner=None,
) -> Dict[str, PreparedRelease]:
    """Write, build and check a generated project.

    `project` maps relative paths to file contents. A project with top-level
    `frontend/` and `backend/` folders yields both releases; otherwise the root
    is a single release under the key 'frontend' (static) or 'backend' (service).
    """
    if _is_legacy_payload(project):
        raise ReleaseError(
            "app_code is the legacy {frontend, backend, database} string payload: "
            "pass the complete project {path: content} so it can be built"
        )
    if not project:
        raise ReleaseError('Empty project')
    if runner is None:
        import subprocess  # nosec B404
        runner = subprocess.run

    root = Path(workdir).resolve()
    _write_project(project, root)

    if (root / 'frontend').is_dir() or (root / 'backend').is_dir():
        releases = {}
        for part in ('frontend', 'backend'):
            if (root / part).is_dir():
                releases[part] = _prepare_one(root / part, runner)
        if 'frontend' in releases and releases['frontend'].kind != STATIC:
            raise ReleaseError('frontend/ did not produce static files')
        if 'backend' in releases and releases['backend'].kind != PYTHON_SERVICE:
            raise ReleaseError('backend/ is not a Python service')
        return releases

    release = _prepare_one(root, runner)
    return {'frontend' if release.kind == STATIC else 'backend': release}


def _release_stamp() -> str:
    return time.strftime('%Y%m%d-%H%M%S', time.gmtime())


def _check_remote_dir(path: str) -> str:
    if not _SAFE_REMOTE_DIR.fullmatch(path or '') or '/../' in path + '/' or path.rstrip('/') == '':
        raise ReleaseError(f"Unsafe or root target path: {path!r} (use the folder the domain points to)")
    return path.rstrip('/')


class _StaticSwapDeployer:
    """Common upload-then-swap logic for web spaces (FTPS and SFTP).

    Files go to `<target>.staging-<stamp>`; only when every file is there is the
    live folder renamed to `<target>.previous-<stamp>` and the staging folder put
    in its place. Nothing is deleted, so `rollback` can restore the old version.
    """

    method = ''

    async def upload_app(self, release: Any, target_path: str = '/app') -> Dict[str, Any]:
        """Publish a prepared static release into target_path."""
        if _is_legacy_payload(release) or not isinstance(release, PreparedRelease):
            return {'success': False, 'method': self.method, 'error': (
                'Refusing raw source: build the project with prepare_project() and pass the '
                'PreparedRelease (React → dist/, never source saved as index.html/index.php/index.js)'
            )}
        if release.kind != STATIC:
            return {'success': False, 'method': self.method, 'error': (
                'A web space serves files, it does not keep a Python process running: '
                'deploy the FastAPI service with IONOSServiceDeployer on a VPS/Cloud Server'
            )}
        try:
            target = _check_remote_dir(target_path)
            files = release.files()
        except ReleaseError as e:
            return {'success': False, 'method': self.method, 'error': str(e)}

        stamp = _release_stamp()
        staging = f"{target}.staging-{stamp}"
        try:
            conn = self._connect()
        except Exception as e:
            return {'success': False, 'method': self.method, 'error': str(e)}
        try:
            failed = []
            for relative in files:
                remote = f"{staging}/{relative.as_posix()}"
                try:
                    self._makedirs(conn, str(PurePosixPath(remote).parent))
                    self._put(conn, release.root.joinpath(*relative.parts), remote)
                except Exception as e:
                    failed.append(f"{relative} ({e})")
            if failed:
                # The live folder was never touched.
                return {'success': False, 'method': self.method, 'staging': staging,
                        'error': f"Upload failed, live site unchanged: {', '.join(failed)}"}

            previous = None
            if self._exists(conn, target):
                previous = f"{target}.previous-{stamp}"
                self._rename(conn, target, previous)
            self._rename(conn, staging, target)
            return {
                'success': True,
                'method': self.method,
                'path': target,
                'previous': previous,
                'files': len(files),
            }
        except Exception as e:
            return {'success': False, 'method': self.method, 'error': str(e)}
        finally:
            self._close(conn)

    async def rollback(self, deployed: Dict[str, Any]) -> Dict[str, Any]:
        """Put back the version that was live before `deployed` (the upload_app result)."""
        target, previous = deployed.get('path'), deployed.get('previous')
        try:
            conn = self._connect()
        except Exception as e:
            return {'success': False, 'error': str(e)}
        try:
            self._rename(conn, target, f"{target}.failed-{_release_stamp()}")
            if previous:
                self._rename(conn, previous, target)
            return {'success': True, 'restored': previous}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            self._close(conn)

    def _makedirs(self, conn, path: str) -> None:
        current = ''
        for part in path.strip('/').split('/'):
            current += '/' + part
            if not self._exists(conn, current):
                self._mkdir(conn, current)


class IONOSFTPDeployer(_StaticSwapDeployer):
    """Deploy static builds to IONOS Web Hosting via FTPS (FTP over TLS)."""

    method = 'FTPS'

    def __init__(self, credentials: Dict[str, str]):
        """Initialize FTPS deployer."""
        self.host = credentials.get('ftp_host', 'ftp.ionos.com')
        self.username = credentials.get('ftp_username')
        self.password = credentials.get('ftp_password')
        self.port = int(credentials.get('ftp_port', 21))

    def _connect(self):
        # TLS is negotiated before login and enforced on the data channel.
        import ftplib  # nosec B402

        ftp = ftplib.FTP_TLS(context=_tls_context())  # nosec B321
        ftp.connect(self.host, self.port, timeout=30)
        ftp.auth()
        ftp.login(self.username, self.password)
        ftp.prot_p()
        return ftp

    def _exists(self, ftp, path: str) -> bool:
        import ftplib  # nosec B402

        try:
            ftp.cwd(path)
            ftp.cwd('/')
            return True
        except ftplib.error_perm:
            return False

    def _mkdir(self, ftp, path: str) -> None:
        ftp.mkd(path)

    def _put(self, ftp, local: Path, remote: str) -> None:
        with open(local, 'rb') as fh:
            ftp.storbinary(f'STOR {remote}', fh)

    def _rename(self, ftp, old: str, new: str) -> None:
        ftp.rename(old, new)

    def _close(self, ftp) -> None:
        try:
            ftp.quit()
        except Exception:
            pass


class IONOSSFTPDeployer(_StaticSwapDeployer):
    """Deploy static builds to IONOS Web Hosting via SFTP."""

    method = 'SFTP'

    def __init__(self, credentials: Dict[str, str]):
        """Initialize SFTP deployer."""
        self.host = credentials.get('sftp_host', 'sftp.ionos.com')
        self.username = credentials.get('sftp_username')
        self.password = credentials.get('sftp_password')
        self.port = int(credentials.get('sftp_port', 22))
        self.private_key = credentials.get('sftp_private_key')
        self.known_hosts = credentials.get('known_hosts')

    def _connect(self):
        client = _connect_ssh_client(
            self.host,
            self.port,
            self.username,
            password=self.password,
            key_filename=self.private_key,
            known_hosts=self.known_hosts,
        )
        return client, client.open_sftp()

    def _exists(self, conn, path: str) -> bool:
        try:
            conn[1].stat(path)
            return True
        except IOError:
            return False

    def _mkdir(self, conn, path: str) -> None:
        conn[1].mkdir(path)

    def _put(self, conn, local: Path, remote: str) -> None:
        conn[1].put(str(local), remote)

    def _rename(self, conn, old: str, new: str) -> None:
        conn[1].rename(old, new)

    def _close(self, conn) -> None:
        client, sftp = conn
        sftp.close()
        client.close()


class IONOSServiceDeployer:
    """Run a prepared FastAPI release on an IONOS VPS / Cloud Server.

    Layout on the server: <app_path>/releases/<stamp>/ holds each version with
    its own .venv; <app_path>/current is a symlink switched atomically. The
    operator supplies `restart_command` once (e.g. a systemd unit that runs
    <app_path>/current/.venv/bin/uvicorn ... from <app_path>/current).
    """

    def __init__(self, credentials: Dict[str, str]):
        self.host = credentials.get('ssh_host')
        self.username = credentials.get('ssh_username')
        self.password = credentials.get('ssh_password')
        self.port = int(credentials.get('ssh_port', 22))
        self.private_key = credentials.get('ssh_private_key')
        self.known_hosts = credentials.get('known_hosts')

    def _connect(self):
        return _connect_ssh_client(
            self.host, self.port, self.username,
            password=self.password, key_filename=self.private_key, known_hosts=self.known_hosts,
        )

    @staticmethod
    def _exec(ssh, command: str) -> Tuple[int, str]:
        _, stdout, stderr = ssh.exec_command(command)  # nosec B601 — every value is shlex-quoted
        output = stdout.read().decode() + stderr.read().decode()
        return stdout.channel.recv_exit_status(), output

    async def deploy_service(self, release: Any, app_path: str, restart_command: str) -> Dict[str, Any]:
        if not isinstance(release, PreparedRelease) or release.kind != PYTHON_SERVICE:
            return {'success': False, 'method': 'SSH service', 'error': 'Expected a prepared Python service release'}
        if not restart_command:
            return {'success': False, 'method': 'SSH service', 'error': (
                'restart_command not configured: without it the new version would be copied but never run'
            )}
        try:
            base = _check_remote_dir(app_path)
            files = release.files()
        except ReleaseError as e:
            return {'success': False, 'method': 'SSH service', 'error': str(e)}

        rel_dir = f"{base}/releases/{_release_stamp()}"
        q = shlex.quote
        try:
            ssh = self._connect()
        except Exception as e:
            return {'success': False, 'method': 'SSH service', 'error': str(e)}
        try:
            code, out = self._exec(ssh, f"mkdir -p {q(rel_dir)} && readlink {q(base + '/current')} || true")
            if code != 0:
                return {'success': False, 'method': 'SSH service', 'error': out}
            previous = out.strip() or None

            sftp = ssh.open_sftp()
            try:
                made = set()
                for relative in files:
                    remote = f"{rel_dir}/{relative.as_posix()}"
                    parent = str(PurePosixPath(remote).parent)
                    if parent not in made:
                        self._exec(ssh, f"mkdir -p {q(parent)}")
                        made.add(parent)
                    sftp.put(str(release.root.joinpath(*relative.parts)), remote)
            finally:
                sftp.close()

            code, out = self._exec(ssh, (
                f"cd {q(rel_dir)} && python3 -m venv .venv && "
                f".venv/bin/pip install --quiet -r requirements.txt"
            ))
            if code != 0:
                return {'success': False, 'method': 'SSH service', 'release': rel_dir,
                        'error': f"Dependency install failed, live service unchanged: {out[-2000:]}"}

            switch = (f"ln -sfn {q(rel_dir)} {q(base + '/current.new')} && "
                      f"mv -Tf {q(base + '/current.new')} {q(base + '/current')}")
            code, out = self._exec(ssh, f"{switch} && {restart_command}")
            if code != 0:
                if previous:
                    self._exec(ssh, f"ln -sfn {q(previous)} {q(base + '/current.new')} && "
                                    f"mv -Tf {q(base + '/current.new')} {q(base + '/current')} && {restart_command}")
                return {'success': False, 'method': 'SSH service', 'error': f"Restart failed, previous restored: {out[-2000:]}"}

            return {'success': True, 'method': 'SSH service', 'path': base, 'release': rel_dir,
                    'previous': previous, 'restart_command': restart_command,
                    'start_command': release.start_command}
        except Exception as e:
            return {'success': False, 'method': 'SSH service', 'error': str(e)}
        finally:
            ssh.close()

    async def rollback(self, deployed: Dict[str, Any]) -> Dict[str, Any]:
        previous, base = deployed.get('previous'), deployed.get('path')
        if not previous:
            return {'success': False, 'error': 'No previous release to restore'}
        q = shlex.quote
        try:
            ssh = self._connect()
        except Exception as e:
            return {'success': False, 'error': str(e)}
        try:
            code, out = self._exec(ssh, (
                f"ln -sfn {q(previous)} {q(base + '/current.new')} && "
                f"mv -Tf {q(base + '/current.new')} {q(base + '/current')} && {deployed['restart_command']}"
            ))
            return {'success': code == 0, 'restored': previous, 'output': out[-2000:]}
        finally:
            ssh.close()


class IONOSGitDeployer:
    """Deploy apps via Git repository on IONOS."""

    def __init__(self, credentials: Dict[str, str]):
        """Initialize Git deployer."""
        self.host = credentials.get('git_host', 'git.ionos.com')
        self.username = credentials.get('git_username')
        self.password = credentials.get('git_password')
        self.ssh_key = credentials.get('git_ssh_key')
        self.known_hosts = credentials.get('known_hosts')

    async def create_git_repo(self, app_name: str) -> Dict[str, Any]:
        """Create Git repository on IONOS."""
        try:
            import subprocess  # nosec B404

            if not _SAFE_APP_NAME.fullmatch(app_name or ''):
                return {'success': False, 'error': f"Invalid app name: {app_name!r}"}
            if not self.username or not self.host:
                return {'success': False, 'error': 'Git SSH user or host not configured'}

            # Create bare repository (git init creates the directory)
            repo_path = f"/var/git/{app_name}.git"

            # No local shell; '--' stops ssh from parsing the destination as an option.
            cmd = [
                'ssh', *_ssh_options(self.known_hosts), '--',
                f"{self.username}@{self.host}", 'git', 'init', '--bare', repo_path,
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=60)  # nosec B603
            if result.returncode != 0:
                return {'success': False, 'error': f"Command failed: {' '.join(cmd)}"}

            return {
                'success': True,
                'repository': f"ssh://{self.username}@{self.host}{repo_path}",
                'app_name': app_name,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def push_and_deploy(
        self,
        app_code: Dict[str, str],
        app_name: str,
        git_remote: str
    ) -> Dict[str, Any]:
        """Push code and trigger deployment."""
        if not git_remote or git_remote.startswith('-') or not _SAFE_GIT_REMOTE.fullmatch(git_remote):
            return {'success': False, 'error': f"Invalid git remote: {git_remote!r}"}

        # Validate every file name before writing anything or running git.
        files = []
        for filename, content in (app_code or {}).items():
            relative = _safe_relative_path(filename)
            if relative is None:
                return {'success': False, 'error': f"Invalid file name in app_code: {filename!r}"}
            files.append((relative, content))
        if not files:
            return {'success': False, 'error': 'No files to deploy'}

        try:
            import subprocess  # nosec B404
            import tempfile

            # Git ignores the user's and system's configuration (hooks, filters, aliases).
            git_env = {**os.environ, 'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_NOSYSTEM': '1'}

            def git(*args, **kwargs):
                return subprocess.run(['git', *args], cwd=tmpdir, check=True, env=git_env, **kwargs)  # nosec B603

            # Create temporary directory for git operations
            with tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir).resolve()
                git('init')
                git('config', 'user.email', 'deploy@claudio.ai')
                git('config', 'user.name', 'Claude Deploy')

                # Write files, refusing anything that resolves outside the temporary root
                for relative, content in files:
                    filepath = root.joinpath(*relative.parts)
                    filepath.parent.mkdir(parents=True, exist_ok=True)
                    if root not in filepath.parent.resolve().parents and filepath.parent.resolve() != root:
                        return {'success': False, 'error': f"File escapes deploy directory: {relative}"}
                    if filepath.is_symlink():
                        return {'success': False, 'error': f"Refusing to write through symlink: {relative}"}
                    filepath.write_text(content)

                # Commit
                git('add', '.')
                git('commit', '-m', 'Auto-generated app deployment')

                # Push to IONOS; git runs ssh through a shell, so quote every option
                git_env['GIT_SSH_COMMAND'] = shlex.join(['ssh', *_ssh_options(self.known_hosts)])
                git('push', '-u', git_remote, 'master')

                return {
                    'success': True,
                    'method': 'Git Push',
                    'repository': git_remote,
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}


class IONOSSSHDeployer:
    """Deploy apps via SSH commands."""

    def __init__(self, credentials: Dict[str, str]):
        """Initialize SSH deployer."""
        self.host = credentials.get('ssh_host')
        self.username = credentials.get('ssh_username')
        self.password = credentials.get('ssh_password')
        self.port = int(credentials.get('ssh_port', 22))
        self.private_key = credentials.get('ssh_private_key')
        self.known_hosts = credentials.get('known_hosts')

    async def execute_deployment(
        self,
        app_code: Dict[str, str],
        deployment_script: str,
        app_path: str = '/var/www/app'
    ) -> Dict[str, Any]:
        """Execute deployment via SSH."""
        try:
            ssh = _connect_ssh_client(
                self.host,
                self.port,
                self.username,
                password=self.password,
                key_filename=self.private_key,
                known_hosts=self.known_hosts,
            )

            # Execute deployment script (operator-supplied, runs on the remote host)
            stdin, stdout, stderr = ssh.exec_command(deployment_script)  # nosec B601

            output = stdout.read().decode()
            error = stderr.read().decode()
            exit_status = stdout.channel.recv_exit_status()

            ssh.close()

            # Many tools write progress to stderr: the exit status decides.
            return {
                'success': exit_status == 0,
                'method': 'SSH',
                'exit_status': exit_status,
                'output': output,
                'error': error,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}


def _http_get(url: str, timeout: int = 20) -> Tuple[int, str, str]:
    """GET url; return (status, content-type, body). HTTP errors are returned, not raised."""
    import urllib.request
    import urllib.error

    if not url.startswith('https://'):
        raise ValueError(f"Public checks use https only: {url!r}")
    request = urllib.request.Request(url, headers={'User-Agent': 'rrremergen-deploy-check/1'})
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=_tls_context()) as response:  # nosec B310
            return response.status, response.headers.get('Content-Type', ''), response.read(200_000).decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get('Content-Type', '') if e.headers else '', ''


def verify_public(
    page_url: str,
    api_url: Optional[str] = None,
    fetch=_http_get,
    attempts: int = 5,
    delay: float = 6.0,
    sleep=time.sleep,
) -> Dict[str, Any]:
    """Check the published app from outside: the page renders HTML, the API answers.

    Fails when the page serves source code instead of a build — exactly the
    defect of uploading JSX as index.html or Python as index.php.
    """
    checks: Dict[str, Any] = {}
    for attempt in range(1, attempts + 1):
        checks = {}
        try:
            status, ctype, body = fetch(page_url)
            lowered = body.lower()
            page_ok = (status == 200 and 'html' in ctype.lower()
                       and ('<html' in lowered or '<!doctype' in lowered))
            leaked = [m for m in _SOURCE_MARKERS if m in body]
            checks['page'] = {'url': page_url, 'status': status, 'content_type': ctype,
                              'ok': page_ok and not leaked, 'source_leak': leaked}
            if api_url:
                status, ctype, _ = fetch(api_url)
                checks['api'] = {'url': api_url, 'status': status, 'content_type': ctype,
                                 'ok': status == 200}
        except Exception as e:
            checks['error'] = str(e)
        if 'error' not in checks and all(c['ok'] for c in checks.values()):
            return {'success': True, 'attempts': attempt, 'checks': checks}
        if attempt < attempts:
            sleep(delay)
    return {'success': False, 'attempts': attempts, 'checks': checks}


class IONOSDeploymentOrchestrator:
    """Prepare → publish → verify from outside → keep or roll back.

    The method is chosen by the IONOS contract, never by trial and error:
      - 'sftp' / 'ftps'  Web Hosting: static frontend only
      - 'ssh'            VPS / Cloud Server: frontend via SFTP + FastAPI service
      - Deploy Now builds from the GitHub branch itself: nothing to upload here.
      - MyWebsite / Website Builder has no file access for custom apps.

    deployment_config:
      method        'sftp' | 'ftps' | 'ssh'
      target_path   folder the domain points to (frontend)
      public_url    https URL of the page, checked after publishing
      api_url       https URL of an API health endpoint (required with a backend)
      service       {'app_path': ..., 'restart_command': ...} (required with a backend)
    """

    def __init__(self, credentials: Dict[str, str]):
        """Initialize deployment orchestrator."""
        self.ftp_deployer = IONOSFTPDeployer(credentials)
        self.sftp_deployer = IONOSSFTPDeployer(credentials)
        self.git_deployer = IONOSGitDeployer(credentials)
        self.ssh_deployer = IONOSSSHDeployer(credentials)
        self.service_deployer = IONOSServiceDeployer(credentials)

    async def deploy_app(
        self,
        app_code: Dict[str, str],
        app_name: str,
        deployment_config: Dict[str, Any],
        runner=None,
        verify=verify_public,
    ) -> Dict[str, Any]:
        """Deploy a complete generated project; return the public URL only once verified."""
        import tempfile

        method = (deployment_config.get('method') or '').lower()
        static = {'sftp': self.sftp_deployer, 'ftps': self.ftp_deployer, 'ssh': self.sftp_deployer}.get(method)
        if static is None:
            return {'success': False, 'error': (
                f"Unknown or missing method {method!r}: set 'sftp'/'ftps' (Web Hosting) or 'ssh' (VPS). "
                "Deploy Now publishes from GitHub on its own; MyWebsite has no file access."
            )}
        public_url = deployment_config.get('public_url')
        if not public_url:
            return {'success': False, 'error': 'public_url is required: an unverified deploy has no address'}

        with tempfile.TemporaryDirectory(prefix=f"ionos-{app_name}-") as workdir:
            try:
                releases = prepare_project(app_code, Path(workdir), runner=runner)
            except ReleaseError as e:
                return {'success': False, 'stage': 'prepare', 'error': str(e)}

            backend = releases.get('backend')
            service_cfg = deployment_config.get('service') or {}
            if backend is not None:
                if method != 'ssh':
                    return {'success': False, 'stage': 'prepare', 'error': (
                        'The project has a FastAPI backend but the target is a web space: '
                        "use method 'ssh' with a VPS, or host the Python service separately"
                    )}
                if not service_cfg.get('app_path') or not deployment_config.get('api_url'):
                    return {'success': False, 'stage': 'prepare', 'error': (
                        "A backend needs service.app_path, service.restart_command and api_url"
                    )}

            deployed = []  # (deployer, result) to roll back in reverse order
            if backend is not None:
                result = await self.service_deployer.deploy_service(
                    backend, service_cfg['app_path'], service_cfg.get('restart_command', ''))
                if not result.get('success'):
                    return {'success': False, 'stage': 'publish', 'details': result}
                deployed.append((self.service_deployer, result))
            if 'frontend' in releases:
                result = await static.upload_app(releases['frontend'], deployment_config.get('target_path', '/app'))
                if not result.get('success'):
                    rollbacks = [await d.rollback(r) for d, r in reversed(deployed)]
                    return {'success': False, 'stage': 'publish', 'details': result, 'rollback': rollbacks}
                deployed.append((static, result))

            check = verify(public_url, deployment_config.get('api_url'))
            if not check.get('success'):
                rollbacks = [await d.rollback(r) for d, r in reversed(deployed)]
                return {'success': False, 'stage': 'verify', 'verification': check, 'rollback': rollbacks}

            return {
                'success': True,
                'method': method,
                'url': public_url,
                'verification': check,
                'details': [r for _, r in deployed],
                'build_log': {k: r.log for k, r in releases.items()},
            }


def _credentials_from_env() -> Dict[str, str]:
    """Credentials come from the environment (GitHub secrets), never from arguments."""
    keys = ['ftp_host', 'ftp_username', 'ftp_password', 'ftp_port',
            'sftp_host', 'sftp_username', 'sftp_password', 'sftp_port', 'sftp_private_key',
            'ssh_host', 'ssh_username', 'ssh_password', 'ssh_port', 'ssh_private_key', 'known_hosts']
    return {k: os.environ[f"IONOS_{k.upper()}"] for k in keys if os.environ.get(f"IONOS_{k.upper()}")}


def _load_project_dir(directory: Path) -> Dict[str, str]:
    skip = {'node_modules', '.git', 'dist', 'build', '.venv', '__pycache__'}
    project = {}
    for path in sorted(directory.rglob('*')):
        rel = path.relative_to(directory)
        if any(part in skip for part in rel.parts) or not path.is_file():
            continue
        project[rel.as_posix()] = path.read_text(encoding='utf-8')
    return project


def main(argv: Optional[List[str]] = None) -> int:
    """CLI for a CI workflow: python deploy.py --project DIR --method sftp --public-url https://..."""
    import argparse

    parser = argparse.ArgumentParser(description='Build, publish and verify an app on IONOS')
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--app-name', default='app')
    parser.add_argument('--method', required=True, choices=['sftp', 'ftps', 'ssh'])
    parser.add_argument('--target-path', default='/app')
    parser.add_argument('--public-url', required=True)
    parser.add_argument('--api-url')
    parser.add_argument('--service-path')
    parser.add_argument('--restart-command', default=os.environ.get('IONOS_RESTART_COMMAND', ''))
    args = parser.parse_args(argv)

    config = {'method': args.method, 'target_path': args.target_path,
              'public_url': args.public_url, 'api_url': args.api_url}
    if args.service_path:
        config['service'] = {'app_path': args.service_path, 'restart_command': args.restart_command}
    orchestrator = IONOSDeploymentOrchestrator(_credentials_from_env())
    result = asyncio.run(orchestrator.deploy_app(_load_project_dir(args.project), args.app_name, config))
    print(json.dumps(result, indent=2, default=str))
    return 0 if result.get('success') else 1


if __name__ == '__main__':
    raise SystemExit(main())
