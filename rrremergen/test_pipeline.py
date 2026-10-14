"""Regression tests: real API/SSE, artifact readback and negative controls; no LLM calls."""
import asyncio
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, patch
import zipfile

from fastapi.testclient import TestClient
from rrremergen.api.main import app
from rrremergen.api.router import LLMRouter, ProviderError
from rrremergen.api.orchestrator import RRRemeRgenOrchestrator
from rrremergen.agents.architect import Architect, AppBlueprint
from rrremergen.agents.pm import PM
from rrremergen.api.demo import FRONTEND, BACKEND, DATABASE


def events(response):
    return [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_demo_api_to_zip_readback(self):
        result = self.client.post('/api/rrremergen/compose', json={
            'prompt': 'Prova pipeline senza inferenza', 'advanced_options': {'mode': 'demo'}})
        self.assertEqual(result.status_code, 200)
        stream = events(result)
        self.assertEqual([e['stage'] for e in stream if e['type'] == 'stage_progress'],
                         ['architect', 'designer', 'developer', 'integrator', 'pm', 'export'])
        self.assertEqual(stream[-1]['type'], 'completion')
        artifact = stream[-1]['app']
        self.assertTrue(artifact['simulation'])
        self.assertIsNone(artifact['github_url'])
        self.assertIsNone(artifact['vercel_url'])
        data = base64.b64decode(artifact['artifact']['content_base64'])
        self.assertEqual(hashlib.sha256(data).hexdigest(), artifact['artifact']['sha256'])
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            self.assertEqual(len(archive.namelist()), 5)
            self.assertEqual(archive.read('backend.py').decode(), BACKEND.strip())
            manifest = json.loads(archive.read('manifest.json'))
            self.assertEqual(manifest['deployment_status'], 'not_deployed')
            self.assertFalse(manifest['validation']['runtime_verified'])

    def test_local_failure_is_terminal_not_completion(self):
        with patch.dict(os.environ, {'RRREMERGEN_LOCAL_RUNNER': str(Path('missing-local-runner.py').resolve())}):
            result = self.client.post('/api/rrremergen/compose', json={'prompt': 'Componi una semplice applicazione'})
        stream = events(result)
        self.assertEqual(stream[-1]['type'], 'error')
        self.assertFalse(any(e['type'] == 'completion' for e in stream))

    def test_invalid_options_and_prompt_rejected(self):
        for options in ({'mode': 'unknown'}, {'mode': 'demo', 'deploy': True}):
            result = self.client.post('/api/rrremergen/compose', json={'prompt': 'Una applicazione semplice', 'advanced_options': options})
            self.assertEqual(result.status_code, 422)
        self.assertEqual(self.client.post('/api/rrremergen/compose', json={'prompt': 'x'}).status_code, 422)

    def test_cloud_cannot_be_enabled_by_a_request_alone(self):
        with patch.dict(os.environ, {'RRREMERGEN_ALLOW_CLOUD': '0'}):
            result = self.client.post('/api/rrremergen/compose', json={
                'prompt': 'Una applicazione semplice', 'advanced_options': {'mode': 'cloud'}})
        self.assertEqual(events(result)[-1]['type'], 'error')

    def test_invalid_blueprint_is_not_replaced_by_invented_content(self):
        router = LLMRouter('demo')
        router.complete = AsyncMock(return_value={'text': '// Error provider'})
        with self.assertRaises(ValueError):
            asyncio.run(Architect(router).analyze('Create an app', 'test'))

    def test_failed_pm_blocks_export_even_after_unchanged_repair(self):
        async def run():
            flow = RRRemeRgenOrchestrator(LLMRouter('demo'))
            flow.developer.generate_code = AsyncMock(return_value={'frontend': 'x', 'backend': 'y', 'database': 'z'})
            flow.developer.fix_issues = AsyncMock(return_value={'frontend': 'x', 'backend': 'y', 'database': 'z'})
            return [event async for event in flow.compose_app('Create an app', {'mode': 'demo'})]
        stream = asyncio.run(run())
        self.assertEqual(stream[-1]['type'], 'error')
        self.assertEqual(stream[-1]['code'], 'validation_failed')
        self.assertFalse(any(e['type'] == 'completion' for e in stream))

    def test_python_syntax_failure_and_validation_endpoint_agree(self):
        source = 'invalid Python try' * 20
        code = {'frontend': FRONTEND, 'backend': source, 'database': DATABASE}
        result = self.client.post('/api/rrremergen/validate', json=code)
        self.assertFalse(result.json()['valid'])
        self.assertTrue(any(e['type'] == 'invalid_syntax' for e in result.json()['issues']))

    def test_deploy_does_not_claim_queued_work(self):
        self.assertEqual(self.client.post('/api/rrremergen/deploy', json={}).status_code, 501)

    def test_metadata_separates_configuration_and_live_health(self):
        health = self.client.get('/health').json()
        self.assertEqual(health['status'], 'ok')
        self.assertTrue(all(not value['reachable_verified'] for value in health['providers'].values()))
        self.assertIn('local', self.client.get('/models').json()['providers'])
        self.assertEqual(LLMRouter()._get_provider_for_model('gpt-4o'), 'openai')

    def test_cloud_error_text_cannot_be_generated_source(self):
        router = LLMRouter('cloud')
        router._complete_openai = AsyncMock(return_value={'text': '// Error upstream', 'tokens_used': 0})
        with patch.dict(os.environ, {'RRREMERGEN_ALLOW_CLOUD': '1', 'OPENAI_API_KEY': 'test-fixture'}):
            with self.assertRaises(ProviderError):
                asyncio.run(router.complete('Test', 'gpt-4o'))


if __name__ == '__main__':
    unittest.main()
