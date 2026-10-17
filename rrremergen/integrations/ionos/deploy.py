#!/usr/bin/env python3
"""
IONOS Direct Deployment — FTP/SFTP/SSH publishing for generated apps.

Strategies:
1. FTPS — FTP over explicit TLS (plain FTP is refused)
2. SFTP Secure — SFTP over SSH for secure transfer
3. Git Push — Git repository on IONOS hosting
4. WebDAV — WebDAV protocol for web publishing
5. SSH Exec — Direct SSH commands for deployment

Every SSH-based connection verifies the server host key against known_hosts
(system file, or the path given as 'known_hosts' in the credentials) and
refuses unknown hosts.
"""

import os
import re
import shlex
import ssl
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path, PurePosixPath
import zipfile
import io

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


class IONOSFTPDeployer:
    """Deploy apps directly to IONOS hosting via FTPS (FTP over TLS)."""

    def __init__(self, credentials: Dict[str, str]):
        """Initialize FTPS deployer."""
        self.host = credentials.get('ftp_host', 'ftp.ionos.com')
        self.username = credentials.get('ftp_username')
        self.password = credentials.get('ftp_password')
        self.port = int(credentials.get('ftp_port', 21))

    async def upload_app(
        self,
        app_code: Dict[str, str],  # {frontend, backend, database}
        target_path: str = '/web'
    ) -> Dict[str, Any]:
        """Upload generated app via FTPS."""
        try:
            # TLS is negotiated before login and enforced on the data channel.
            import ftplib  # nosec B402

            ftp = ftplib.FTP_TLS(context=_tls_context())  # nosec B321
            ftp.connect(self.host, self.port, timeout=30)
            ftp.auth()
            ftp.login(self.username, self.password)
            ftp.prot_p()

            # Create directory structure
            await self._create_directories(ftp, target_path)

            failed = []

            # Upload frontend
            if app_code.get('frontend'):
                frontend_path = f"{target_path}/public"
                if not await self._upload_file(
                    ftp,
                    frontend_path,
                    'index.html',
                    app_code['frontend']
                ):
                    failed.append('frontend')

            # Upload backend (PHP/Node.js compatible format)
            if app_code.get('backend'):
                backend_path = f"{target_path}/api"
                if not await self._upload_file(
                    ftp,
                    backend_path,
                    'index.php',
                    app_code['backend']
                ):
                    failed.append('backend')

            ftp.quit()

            if failed:
                return {'success': False, 'method': 'FTPS', 'error': f"Upload failed: {', '.join(failed)}"}

            return {
                'success': True,
                'method': 'FTPS',
                'url': f"https://{self.host.replace('ftp.', 'www.')}/{target_path}",
                'frontend_path': f"{target_path}/public",
                'backend_path': f"{target_path}/api",
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _create_directories(self, ftp, base_path: str) -> bool:
        """Create directory structure on FTP server."""
        import ftplib  # nosec B402

        try:
            directories = [
                base_path,
                f"{base_path}/public",
                f"{base_path}/api",
                f"{base_path}/uploads",
                f"{base_path}/logs",
            ]

            for dir_path in directories:
                try:
                    ftp.mkd(dir_path)
                except ftplib.all_errors:
                    # Directory might already exist
                    pass

            return True
        except Exception as e:
            print(f"Error creating directories: {e}")
            return False

    async def _upload_file(
        self,
        ftp,
        directory: str,
        filename: str,
        content: str
    ) -> bool:
        """Upload file via FTP."""
        try:
            ftp.cwd(directory)
            file_bytes = content.encode('utf-8')
            ftp.storbinary(f'STOR {filename}', io.BytesIO(file_bytes))
            return True
        except Exception as e:
            print(f"Error uploading file: {e}")
            return False


class IONOSSFTPDeployer:
    """Deploy apps securely via SFTP."""

    def __init__(self, credentials: Dict[str, str]):
        """Initialize SFTP deployer."""
        self.host = credentials.get('sftp_host', 'sftp.ionos.com')
        self.username = credentials.get('sftp_username')
        self.password = credentials.get('sftp_password')
        self.port = int(credentials.get('sftp_port', 22))
        self.private_key = credentials.get('sftp_private_key')
        self.known_hosts = credentials.get('known_hosts')

    async def upload_app(
        self,
        app_code: Dict[str, str],
        target_path: str = '/home/user/public_html'
    ) -> Dict[str, Any]:
        """Upload generated app via SFTP."""
        try:
            client = _connect_ssh_client(
                self.host,
                self.port,
                self.username,
                password=self.password,
                key_filename=self.private_key,
                known_hosts=self.known_hosts,
            )
            sftp = client.open_sftp()

            # Create directory structure
            await self._create_directories(sftp, target_path)

            # Upload files
            uploads = []

            if app_code.get('frontend'):
                sftp.putfo(
                    io.BytesIO(app_code['frontend'].encode()),
                    f"{target_path}/public/index.html"
                )
                uploads.append('frontend')

            if app_code.get('backend'):
                sftp.putfo(
                    io.BytesIO(app_code['backend'].encode()),
                    f"{target_path}/api/index.js"
                )
                uploads.append('backend')

            if app_code.get('database'):
                sftp.putfo(
                    io.BytesIO(app_code['database'].encode()),
                    f"{target_path}/database/schema.sql"
                )
                uploads.append('database')

            sftp.close()
            client.close()

            return {
                'success': True,
                'method': 'SFTP',
                'uploads': uploads,
                'path': target_path,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _create_directories(self, sftp, base_path: str) -> bool:
        """Create directory structure via SFTP."""
        try:
            directories = [
                base_path,
                f"{base_path}/public",
                f"{base_path}/api",
                f"{base_path}/database",
                f"{base_path}/uploads",
                f"{base_path}/logs",
            ]

            for dir_path in directories:
                try:
                    sftp.mkdir(dir_path)
                except IOError:
                    # Directory exists
                    pass

            return True
        except Exception:
            return False


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


class IONOSDeploymentOrchestrator:
    """Orchestrates deployment across multiple IONOS services."""

    def __init__(self, credentials: Dict[str, str]):
        """Initialize deployment orchestrator."""
        self.ftp_deployer = IONOSFTPDeployer(credentials)
        self.sftp_deployer = IONOSSFTPDeployer(credentials)
        self.git_deployer = IONOSGitDeployer(credentials)
        self.ssh_deployer = IONOSSSHDeployer(credentials)

    async def deploy_app(
        self,
        app_code: Dict[str, str],
        app_name: str,
        deployment_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deploy app using best available method.

        Strategy:
        1. Try SFTP (most secure)
        2. Fall back to Git
        3. Fall back to FTP
        4. Fall back to SSH commands
        """
        methods = [
            ('SFTP', self.sftp_deployer.upload_app),
            ('Git', self.git_deployer.push_and_deploy),
            ('FTP', self.ftp_deployer.upload_app),
            ('SSH', self.ssh_deployer.execute_deployment),
        ]

        for method_name, method_func in methods:
            try:
                if method_name == 'Git':
                    result = await method_func(
                        app_code,
                        app_name,
                        deployment_config.get('git_remote', '')
                    )
                elif method_name == 'SSH':
                    result = await method_func(
                        app_code,
                        deployment_config.get('deploy_script', ''),
                    )
                else:
                    result = await method_func(app_code)

                if result.get('success'):
                    return {
                        'success': True,
                        'method': method_name,
                        'details': result,
                    }
            except Exception as e:
                print(f"{method_name} deployment failed: {e}")
                continue

        return {'success': False, 'error': 'All deployment methods failed'}
