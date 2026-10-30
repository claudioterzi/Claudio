"""IONOS bridge: only built releases are published, verified from outside, rolled back on failure."""

import asyncio
import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_spec = importlib.util.spec_from_file_location(
    'ionos_release_under_test', Path(__file__).resolve().parents[1] / 'rrremergen' / 'integrations' / 'ionos' / 'deploy.py'
)
deploy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(deploy)

REACT_SOURCE = "import React from 'react'\nexport default function App() { return <h1>Ciao</h1> }\n"
FASTAPI_SOURCE = "from fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/health')\ndef health():\n    return {'ok': True}\n"


def _workdir(test):
    path = Path(tempfile.mkdtemp())
    test.addCleanup(shutil.rmtree, path, True)
    return path


def _fake_build(cmd, cwd, **kwargs):
    """Stand-in for npm: `npm run build` writes a Vite-like dist/."""
    if cmd[:3] == ['npm', 'run', 'build']:
        dist = Path(cwd) / 'dist'
        (dist / 'assets').mkdir(parents=True)
        (dist / 'index.html').write_text('<!doctype html><html><script src="/assets/app.js"></script></html>')
        (dist / 'assets' / 'app.js').write_text('console.log(1)')
    return subprocess.CompletedProcess(cmd, 0, 'ok', '')


class RawSourceIsNeverPublishedTests(unittest.TestCase):
    """The defect: React saved as index.html, Python as index.php/index.js."""

    def test_legacy_string_payload_is_refused_by_ftps_and_sftp(self):
        payload = {'frontend': REACT_SOURCE, 'backend': FASTAPI_SOURCE}
        for deployer in (deploy.IONOSFTPDeployer({}), deploy.IONOSSFTPDeployer({})):
            with mock.patch.object(deployer, '_connect') as connect:
                result = asyncio.run(deployer.upload_app(payload))
            self.assertFalse(result['success'])
            self.assertIn('raw source', result['error'])
            connect.assert_not_called()

    def test_legacy_payload_is_refused_by_prepare(self):
        with self.assertRaises(deploy.ReleaseError):
            deploy.prepare_project({'frontend': REACT_SOURCE}, _workdir(self))

    def test_jsx_without_build_step_is_refused(self):
        project = {'index.html': '<html></html>', 'src/App.jsx': REACT_SOURCE}
        with self.assertRaisesRegex(deploy.ReleaseError, 'Unbuilt source'):
            deploy.prepare_project(project, _workdir(self))

    def test_python_service_is_not_uploaded_to_a_web_space(self):
        release = deploy.PreparedRelease(deploy.PYTHON_SERVICE, _workdir(self))
        result = asyncio.run(deploy.IONOSSFTPDeployer({}).upload_app(release))
        self.assertFalse(result['success'])
        self.assertIn('Python', result['error'])


class PrepareProjectTests(unittest.TestCase):
    def test_react_project_is_built_and_only_dist_is_published(self):
        project = {
            'package.json': json.dumps({'scripts': {'build': 'vite build'}}),
            'package-lock.json': '{}',
            'index.html': '<div id="root"></div><script type="module" src="/src/main.jsx"></script>',
            'src/App.jsx': REACT_SOURCE,
        }
        runner = mock.Mock(side_effect=_fake_build)
        releases = deploy.prepare_project(project, _workdir(self), runner=runner)
        commands = [c.args[0] for c in runner.call_args_list]
        self.assertEqual(commands, [['npm', 'ci', '--no-audit', '--no-fund'], ['npm', 'run', 'build']])
        release = releases['frontend']
        self.assertEqual(release.kind, deploy.STATIC)
        self.assertEqual(release.root.name, 'dist')
        self.assertEqual([str(p) for p in release.files()], ['assets/app.js', 'index.html'])

    def test_failed_build_stops_everything(self):
        project = {'package.json': json.dumps({'scripts': {'build': 'vite build'}})}
        runner = mock.Mock(return_value=subprocess.CompletedProcess([], 1, '', 'vite: not found'))
        with self.assertRaisesRegex(deploy.ReleaseError, 'vite: not found'):
            deploy.prepare_project(project, _workdir(self), runner=runner)

    def test_package_without_build_script_is_refused(self):
        with self.assertRaisesRegex(deploy.ReleaseError, "no 'build' script"):
            deploy.prepare_project({'package.json': '{"scripts": {}}'}, _workdir(self))

    def test_fullstack_react_plus_fastapi(self):
        project = {
            'frontend/package.json': json.dumps({'scripts': {'build': 'vite build'}}),
            'frontend/src/App.jsx': REACT_SOURCE,
            'backend/requirements.txt': 'fastapi==0.115.0\nuvicorn[standard]>=0.30\n',
            'backend/app/main.py': FASTAPI_SOURCE,
            'backend/app/__init__.py': '',
        }
        releases = deploy.prepare_project(project, _workdir(self), runner=mock.Mock(side_effect=_fake_build))
        self.assertEqual(releases['frontend'].kind, deploy.STATIC)
        backend = releases['backend']
        self.assertEqual(backend.kind, deploy.PYTHON_SERVICE)
        self.assertEqual(backend.start_command[:2], ['uvicorn', 'app.main:app'])

    def test_fastapi_without_asgi_server_is_refused(self):
        project = {'requirements.txt': 'fastapi\n', 'main.py': FASTAPI_SOURCE}
        with self.assertRaisesRegex(deploy.ReleaseError, 'ASGI server'):
            deploy.prepare_project(project, _workdir(self))

    def test_fastapi_syntax_error_is_refused(self):
        project = {'requirements.txt': 'fastapi\nuvicorn\n', 'main.py': 'app = FastAPI(\n'}
        with self.assertRaisesRegex(deploy.ReleaseError, 'Syntax error'):
            deploy.prepare_project(project, _workdir(self))

    @unittest.skipUnless(shutil.which('npm'), 'npm not available')
    def test_real_npm_build(self):
        build = ("node -e \"const fs=require('fs');fs.mkdirSync('dist',{recursive:true});"
                 "fs.writeFileSync('dist/index.html','<!doctype html><html>ok</html>')\"")
        project = {'package.json': json.dumps({'name': 'probe', 'version': '1.0.0', 'scripts': {'build': build}})}
        releases = deploy.prepare_project(project, _workdir(self))
        self.assertEqual([str(p) for p in releases['frontend'].files()], ['index.html'])


class SwapAndRollbackTests(unittest.TestCase):
    def _ftps(self, existing=True):
        ftp = mock.MagicMock()
        import ftplib  # nosec B402 -- exception class for an FTPS mock; no connection
        if not existing:
            ftp.cwd.side_effect = ftplib.error_perm('550')
        return ftp

    def _release(self):
        root = _workdir(self)
        (root / 'index.html').write_text('<!doctype html><html></html>')
        return deploy.PreparedRelease(deploy.STATIC, root)

    def test_upload_goes_to_staging_then_swaps_keeping_previous(self):
        ftp = self._ftps()
        deployer = deploy.IONOSFTPDeployer({'ftp_username': 'u', 'ftp_password': 'p'})
        with mock.patch.object(deployer, '_connect', return_value=ftp):
            result = asyncio.run(deployer.upload_app(self._release(), '/app'))
        self.assertTrue(result['success'], result)
        stored = ftp.storbinary.call_args.args[0]
        self.assertRegex(stored, r'^STOR /app\.staging-\d{8}-\d{6}-[0-9a-f]{32}/index\.html$')
        renames = [c.args for c in ftp.rename.call_args_list]
        self.assertEqual(renames[0][0], '/app')
        self.assertTrue(renames[0][1].startswith('/app.previous-'))
        self.assertEqual(renames[1][1], '/app')
        self.assertEqual(result['previous'], renames[0][1])

        with mock.patch.object(deployer, '_connect', return_value=ftp):
            back = asyncio.run(deployer.rollback(result))
        self.assertTrue(back['success'])
        self.assertEqual(ftp.rename.call_args.args, (result['previous'], '/app'))

    def test_root_target_is_refused(self):
        result = asyncio.run(deploy.IONOSFTPDeployer({}).upload_app(self._release(), '/'))
        self.assertFalse(result['success'])


class VerifyPublicTests(unittest.TestCase):
    def _verify(self, responses, api=None):
        fetch = mock.Mock(side_effect=lambda url: responses[url])
        return deploy.verify_public('https://app.example', api, fetch=fetch, attempts=2, sleep=lambda s: None)

    def test_built_page_and_api_pass(self):
        result = self._verify({
            'https://app.example': (200, 'text/html', '<!doctype html><html></html>'),
            'https://app.example/api/health': (200, 'application/json', '{"ok":true}'),
        }, 'https://app.example/api/health')
        self.assertTrue(result['success'], result)

    def test_page_serving_jsx_source_fails(self):
        result = self._verify({'https://app.example': (200, 'text/html', '<html>' + REACT_SOURCE)})
        self.assertFalse(result['success'])
        self.assertEqual(result['checks']['page']['source_leak'], ['import React', 'export default function'])

    def test_api_down_fails(self):
        result = self._verify({
            'https://app.example': (200, 'text/html', '<html></html>'),
            'https://app.example/api/health': (502, 'text/html', ''),
        }, 'https://app.example/api/health')
        self.assertFalse(result['success'])


class OrchestratorTests(unittest.TestCase):
    PROJECT = {'index.html': '<!doctype html><html></html>'}

    def test_failed_verification_rolls_back_and_returns_no_url(self):
        orch = deploy.IONOSDeploymentOrchestrator({})
        upload = {'success': True, 'path': '/app', 'previous': '/app.previous-x'}
        with mock.patch.object(orch.sftp_deployer, 'upload_app', mock.AsyncMock(return_value=upload)), \
                mock.patch.object(orch.sftp_deployer, 'rollback', mock.AsyncMock(return_value={'success': True})) as rb:
            result = asyncio.run(orch.deploy_app(self.PROJECT, 'app', {
                'method': 'sftp', 'public_url': 'https://app.example'},
                verify=lambda *a: {'success': False}))
        self.assertFalse(result['success'])
        self.assertEqual(result['stage'], 'verify')
        self.assertNotIn('url', result)
        rb.assert_awaited_once_with(upload)

    def test_verified_deploy_returns_public_url(self):
        orch = deploy.IONOSDeploymentOrchestrator({})
        with mock.patch.object(orch.ftp_deployer, 'upload_app', mock.AsyncMock(return_value={'success': True})):
            result = asyncio.run(orch.deploy_app(self.PROJECT, 'app', {
                'method': 'ftps', 'public_url': 'https://app.example'},
                verify=lambda *a: {'success': True}))
        self.assertTrue(result['success'], result)
        self.assertEqual(result['url'], 'https://app.example')

    def test_backend_on_web_space_is_refused_before_any_upload(self):
        orch = deploy.IONOSDeploymentOrchestrator({})
        project = {'requirements.txt': 'fastapi\nuvicorn\n', 'main.py': FASTAPI_SOURCE}
        with mock.patch.object(orch.sftp_deployer, 'upload_app', mock.AsyncMock()) as up:
            result = asyncio.run(orch.deploy_app(project, 'app', {
                'method': 'sftp', 'public_url': 'https://app.example'}))
        self.assertFalse(result['success'])
        self.assertIn('VPS', result['error'])
        up.assert_not_awaited()

    def test_method_must_be_explicit(self):
        result = asyncio.run(deploy.IONOSDeploymentOrchestrator({}).deploy_app(
            self.PROJECT, 'app', {'public_url': 'https://app.example'}))
        self.assertFalse(result['success'])
        self.assertIn('Deploy Now', result['error'])


if __name__ == '__main__':
    unittest.main()
