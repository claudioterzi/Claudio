#!/usr/bin/env python3
"""
IONOS Direct Deployment — FTP/SFTP/SSH publishing for generated apps.

Strategies:
1. FTP Classic — Pure FTP upload to IONOS hosting
2. SFTP Secure — SFTP over SSH for secure transfer
3. Git Push — Git repository on IONOS hosting
4. WebDAV — WebDAV protocol for web publishing
5. SSH Exec — Direct SSH commands for deployment
"""

import os
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import zipfile
import io


class IONOSFTPDeployer:
    """Deploy apps directly to IONOS hosting via FTP."""

    def __init__(self, credentials: Dict[str, str]):
        """Initialize FTP deployer."""
        self.host = credentials.get('ftp_host', 'ftp.ionos.com')
        self.username = credentials.get('ftp_username')
        self.password = credentials.get('ftp_password')
        self.port = int(credentials.get('ftp_port', 21))

    async def upload_app(
        self,
        app_code: Dict[str, str],  # {frontend, backend, database}
        target_path: str = '/web'
    ) -> Dict[str, Any]:
        """Upload generated app via FTP."""
        try:
            import ftplib

            ftp = ftplib.FTP()
            ftp.connect(self.host, self.port, timeout=30)
            ftp.login(self.username, self.password)

            # Create directory structure
            await self._create_directories(ftp, target_path)

            # Upload frontend
            if app_code.get('frontend'):
                frontend_path = f"{target_path}/public"
                await self._upload_file(
                    ftp,
                    frontend_path,
                    'index.html',
                    app_code['frontend']
                )

            # Upload backend (PHP/Node.js compatible format)
            if app_code.get('backend'):
                backend_path = f"{target_path}/api"
                await self._upload_file(
                    ftp,
                    backend_path,
                    'index.php',
                    app_code['backend']
                )

            ftp.quit()

            return {
                'success': True,
                'method': 'FTP',
                'url': f"https://{self.host.replace('ftp.', 'www.')}/{target_path}",
                'frontend_path': f"{target_path}/public",
                'backend_path': f"{target_path}/api",
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _create_directories(self, ftp, base_path: str) -> bool:
        """Create directory structure on FTP server."""
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

    async def upload_app(
        self,
        app_code: Dict[str, str],
        target_path: str = '/home/user/public_html'
    ) -> Dict[str, Any]:
        """Upload generated app via SFTP."""
        try:
            import paramiko

            transport = paramiko.Transport((self.host, self.port))

            if self.private_key:
                # Use SSH key
                private_key = paramiko.RSAKey.from_private_key_file(self.private_key)
                transport.connect(username=self.username, pkey=private_key)
            else:
                # Use password
                transport.connect(username=self.username, password=self.password)

            sftp = paramiko.SFTPClient.from_transport(transport)

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
            transport.close()

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

    async def create_git_repo(self, app_name: str) -> Dict[str, Any]:
        """Create Git repository on IONOS."""
        try:
            import subprocess

            # Create bare repository
            repo_path = f"/var/git/{app_name}.git"

            commands = [
                f"ssh {self.username}@{self.host} 'mkdir -p {repo_path}'",
                f"ssh {self.username}@{self.host} 'cd {repo_path} && git init --bare'",
            ]

            for cmd in commands:
                result = subprocess.run(cmd, shell=True, capture_output=True)
                if result.returncode != 0:
                    return {'success': False, 'error': f"Command failed: {cmd}"}

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
        try:
            import subprocess
            import tempfile
            import shutil

            # Create temporary directory for git operations
            with tempfile.TemporaryDirectory() as tmpdir:
                # Initialize git repo
                subprocess.run(['git', 'init'], cwd=tmpdir, check=True)
                subprocess.run(
                    ['git', 'config', 'user.email', 'deploy@claudio.ai'],
                    cwd=tmpdir,
                    check=True
                )
                subprocess.run(
                    ['git', 'config', 'user.name', 'Claude Deploy'],
                    cwd=tmpdir,
                    check=True
                )

                # Write files
                for filename, content in app_code.items():
                    filepath = Path(tmpdir) / filename
                    filepath.parent.mkdir(parents=True, exist_ok=True)
                    filepath.write_text(content)

                # Commit
                subprocess.run(['git', 'add', '.'], cwd=tmpdir, check=True)
                subprocess.run(
                    ['git', 'commit', '-m', 'Auto-generated app deployment'],
                    cwd=tmpdir,
                    check=True
                )

                # Push to IONOS
                subprocess.run(
                    ['git', 'push', '-u', git_remote, 'master'],
                    cwd=tmpdir,
                    check=True
                )

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

    async def execute_deployment(
        self,
        app_code: Dict[str, str],
        deployment_script: str,
        app_path: str = '/var/www/app'
    ) -> Dict[str, Any]:
        """Execute deployment via SSH."""
        try:
            import paramiko

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            if self.private_key:
                private_key = paramiko.RSAKey.from_private_key_file(self.private_key)
                ssh.connect(
                    self.host,
                    port=self.port,
                    username=self.username,
                    pkey=private_key
                )
            else:
                ssh.connect(
                    self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password
                )

            # Execute deployment script
            stdin, stdout, stderr = ssh.exec_command(deployment_script)

            output = stdout.read().decode()
            error = stderr.read().decode()

            ssh.close()

            return {
                'success': not error,
                'method': 'SSH',
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
