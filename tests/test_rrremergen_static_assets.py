"""Every asset referenced by public/rrremergen/index.html must be served by vercel.json.

Resolves each local href/src the way the Vercel routes in vercel.json would (first
matching route wins, $N substitution) and checks the destination file exists.
"""

import json
import re
import unittest
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]
PAGE_URL = '/rrremergen/'
PAGE_FILE = ROOT / 'public' / 'rrremergen' / 'index.html'


def _served_file(url_path, routes):
    for route in routes:
        match = re.fullmatch(route['src'], url_path)
        if not match:
            continue
        dest = route.get('dest', '')
        for i, group in enumerate(match.groups(), 1):
            dest = dest.replace(f'${i}', group or '')
        return ROOT / dest.split('?')[0].lstrip('/')
    return ROOT / 'public' / url_path.lstrip('/')


class RRRemergenStaticAssetsTests(unittest.TestCase):
    def test_every_local_asset_resolves_to_an_existing_file(self):
        routes = json.loads((ROOT / 'vercel.json').read_text())['routes']
        html = PAGE_FILE.read_text()
        refs = re.findall(r'\b(?:href|src)="([^"#?]+)', html)
        local = [r for r in refs if not r.startswith(('http:', 'https:', '//', 'data:'))]
        self.assertTrue(local, 'no local assets found in index.html')
        missing = []
        for ref in local:
            url_path = urljoin(PAGE_URL, ref)
            target = _served_file(url_path, routes)
            if not target.is_file():
                missing.append(f'{ref} -> {url_path} -> {target.relative_to(ROOT)}')
        self.assertEqual(missing, [], 'assets not served:\n' + '\n'.join(missing))

    def test_frontend_build_script_targets_rrremergen_base(self):
        # The page above is build output; the next Vite build must keep the /rrremergen/ base.
        scripts = json.loads((ROOT / 'studio' / 'web' / 'package.json').read_text())['scripts']
        build = scripts.get('build:rrremergen', '')
        self.assertIn('--base=/rrremergen/', build)
        self.assertIn('--outDir ../../public/rrremergen', build)


if __name__ == '__main__':
    unittest.main()
