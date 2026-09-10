"""Regression tests for real outages and bounded autonomous repairs."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import site_monitor as monitor


class TestSiteMonitor(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'public').mkdir()
        (self.root / 'config').mkdir()
        (self.root / 'public/fabbrica.html').write_text('<title>Fabbrica</title><img src="/picture.webp">')
        (self.root / 'public/picture.webp').write_bytes(b'fixture')
        self.config = {'origin': 'https://example.test', 'aliases': {'/fabbrica': 'fabbrica.html'},
                       'safe_get': [{'path': '/api/status', 'equals': {'available': True}}]}
        self.save_config()
        self.routes = {'routes': [{'src': '/private/(.*)', 'dest': 'private.py'},
                                  {'src': '/(.*)', 'dest': 'app.py'}]}
        self.save_routes()

    def save_config(self):
        (self.root / 'config/site_monitor.json').write_text(json.dumps(self.config))

    def save_routes(self):
        (self.root / 'vercel.json').write_text(json.dumps(self.routes))

    def test_repair_restores_broken_alias_and_preserves_unrelated_rules(self):
        self.assertTrue(monitor.local_checks(self.root, check_js=False)['failures'])
        self.assertEqual(monitor.repair_aliases(self.root), ['/fabbrica'])
        repaired = json.loads((self.root / 'vercel.json').read_text())['routes']
        self.assertEqual(repaired[1:], self.routes['routes'])
        self.assertFalse(monitor.local_checks(self.root, check_js=False)['failures'])
        original = (self.root / 'vercel.json').read_bytes()
        self.assertEqual(monitor.repair_aliases(self.root), [])
        self.assertEqual((self.root / 'vercel.json').read_bytes(), original)

    def test_missing_source_aborts_entire_repair_without_writing(self):
        self.config['aliases']['/missing'] = 'absent.html'
        self.save_config()
        original = (self.root / 'vercel.json').read_bytes()
        with self.assertRaises(ValueError):
            monitor.repair_aliases(self.root)
        self.assertEqual((self.root / 'vercel.json').read_bytes(), original)

    def test_deleted_resource_is_a_failure(self):
        monitor.repair_aliases(self.root)
        (self.root / 'public/picture.webp').unlink()
        result = monitor.local_checks(self.root, check_js=False)
        self.assertTrue(any('picture.webp' in item for item in result['failures']))

    def response(self, request, timeout):
        body = b'{"available":true}' if '/api/' in request.full_url else b'<title>Fabbrica</title>'
        response = io.BytesIO(body)
        response.status = 200
        return response

    def test_live_probe_only_visits_explicit_public_pages_aliases_and_safe_apis(self):
        with patch.object(monitor, 'urlopen', side_effect=self.response) as network:
            self.assertFalse(monitor.live_checks(self.root)['failures'])
        paths = {call.args[0].full_url for call in network.call_args_list}
        self.assertEqual(paths, {'https://example.test/fabbrica.html', 'https://example.test/fabbrica',
                                 'https://example.test/api/status'})

    def test_wrong_page_with_http_200_is_detected(self):
        def wrong(request, timeout):
            response = io.BytesIO(b'<title>Pagina non trovata</title>')
            response.status = 200
            return response
        with patch.object(monitor, 'urlopen', side_effect=wrong):
            report = monitor.live_checks(self.root)
        self.assertEqual(len(report['failures']), 3)

    def test_unavailable_service_with_http_200_is_detected(self):
        def unavailable(request, timeout):
            if '/api/' not in request.full_url:
                return self.response(request, timeout)
            response = io.BytesIO(b'{"available":false,"private":"never log this"}')
            response.status = 200
            return response
        with patch.object(monitor, 'urlopen', side_effect=unavailable):
            report = monitor.live_checks(self.root)
        self.assertEqual(len(report['failures']), 1)
        self.assertNotIn('never log this', json.dumps(report))


if __name__ == '__main__':
    unittest.main()
