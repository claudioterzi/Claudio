"""Read-only site checks plus a finite repair of explicitly registered aliases.

No arbitrary crawling of APIs: the live probe only uses the reviewed safe GET list.
No messages, purchases, image generation, private records or model calls.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.title, self.in_title, self.resources, self.links = '', False, [], []
        self.scripts, self.script = [], None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'title':
            self.in_title = True
        if tag == 'a' and attrs.get('href'):
            self.links.append(attrs['href'])
        if tag in ('img', 'script', 'source') and attrs.get('src'):
            self.resources.append(attrs['src'])
        if tag == 'link' and attrs.get('href'):
            self.resources.append(attrs['href'])
        if tag == 'script' and not attrs.get('src') and attrs.get('type', '') in ('', 'text/javascript', 'application/javascript', 'module'):
            self.script = []

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False
        if tag == 'script' and self.script is not None:
            self.scripts.append(''.join(self.script))
            self.script = None

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.script is not None:
            self.script.append(data)


def configuration(root):
    return json.loads((root / 'config/site_monitor.json').read_text())


def destination(path, routes):
    for rule in routes:
        match = re.fullmatch(rule['src'], path)
        if match:
            dest = rule.get('dest', '')
            for index, value in enumerate(match.groups(), 1):
                dest = dest.replace(f'${index}', value or '')
            return dest
    return None


def repair_aliases(root=ROOT):
    """Only the explicit aliases in the reviewed registry can be repaired."""
    root = Path(root)
    file = root / 'vercel.json'
    settings, changed = json.loads(file.read_text()), []
    for alias, page in configuration(root)['aliases'].items():
        target = '/public/' + page
        if not (root / 'public' / page).is_file():
            raise ValueError(f'Pagina sorgente mancante: {page}; nessuna riparazione pubblicabile')
        if destination(alias, settings['routes']) != target:
            settings['routes'] = [r for r in settings['routes'] if r['src'] != alias]
            settings['routes'].insert(0, {'src': alias, 'dest': target})
            changed.append(alias)
    if changed:
        file.write_text(json.dumps(settings, indent=2) + '\n')
    return changed


def local_checks(root=ROOT, check_js=True):
    root = Path(root)
    config = configuration(root)
    rules = json.loads((root / 'vercel.json').read_text())['routes']
    failures, resources, pages, scripts = [], set(), {}, []
    for file in sorted((root / 'public').glob('*.html')):
        parsed = Page(file.read_text())
        pages[file.name] = parsed.title.strip()
        if not parsed.title.strip():
            failures.append(f'Titolo mancante: {file.name}')
        scripts.extend((file.name, text) for text in parsed.scripts if text.strip())
        for url in parsed.resources:
            part = urlsplit(url)
            if part.scheme or part.netloc or not part.path:
                continue
            asset = root / 'public' / unquote(part.path.lstrip('/'))
            if not asset.is_file():
                failures.append(f'Risorsa mancante: {file.name} → {part.path}')
            else:
                resources.add(asset)
        for url in parsed.links:
            part = urlsplit(url)
            if re.fullmatch(r'claudio-[a-z0-9-]+-claudio-terzi-s-projects\.vercel\.app', part.netloc):
                failures.append(f'Collegamento a una versione temporanea: {file.name}')
            if part.netloc and part.netloc != urlsplit(config['origin']).netloc:
                continue
            if part.scheme not in ('', 'https', 'http') or not part.path:
                continue
            local = root / 'public' / unquote(part.path.lstrip('/'))
            if Path(part.path).suffix in ('.html', '.pdf', '.js', '.css', '.svg', '.webp', '.jpg', '.png') and not local.is_file():
                failures.append(f'Collegamento mancante: {file.name} → {part.path}')
    for alias, page in config['aliases'].items():
        if page not in pages or destination(alias, rules) != '/public/' + page:
            failures.append(f'Indirizzo breve non valido: {alias}')
    if check_js:
        for file in sorted((root / 'public').glob('*.js')):
            result = subprocess.run(['node', '--check', str(file)], capture_output=True, text=True)
            if result.returncode:
                failures.append(f'JavaScript non valido: {file.name}')
        with tempfile.TemporaryDirectory() as temp:
            for index, (name, script) in enumerate(scripts):
                file = Path(temp) / f'inline-{index}.mjs'
                file.write_text(script)
                result = subprocess.run(['node', '--check', str(file)], capture_output=True, text=True)
                if result.returncode:
                    failures.append(f'JavaScript inline non valido: {name}')
    return {'kind': 'local', 'pages_checked': len(pages), 'resources_checked': len(resources),
            'inline_scripts_checked': len(scripts) if check_js else 0,
            'aliases_checked': len(config['aliases']), 'failures': sorted(set(failures))}


def live_checks(root=ROOT):
    root = Path(root)
    config = configuration(root)
    pages = {file.name: Page(file.read_text()).title.strip() for file in (root / 'public').glob('*.html')}
    checks = [{'path': '/' + name, 'title': title} for name, title in sorted(pages.items())]
    checks += [{'path': alias, 'title': pages[name]} for alias, name in config['aliases'].items()]
    checks += config['safe_get']

    def probe(item):
        start = time.monotonic()
        record = {'path': item['path'], 'ok': False}
        try:
            request = Request(config['origin'] + item['path'], headers={'User-Agent': 'Terzi-Site-Monitor/1.0'})
            with urlopen(request, timeout=20) as response:
                content = response.read(2_000_000 if 'title' not in item else 65536)
                record['status'] = response.status
                if response.status != 200:
                    raise ValueError('Stato HTTP inatteso')
                if 'title' in item:
                    if Page(content.decode('utf8', 'replace')).title.strip() != item['title']:
                        raise ValueError('La risposta non contiene la pagina attesa')
                else:
                    data = json.loads(content)
                    for key, expected in item.get('equals', {}).items():
                        if not isinstance(data, dict) or data.get(key) != expected:
                            raise ValueError(f'Servizio indisponibile: {key}')
                    if 'list_length' in item and (not isinstance(data, list) or len(data) != item['list_length']):
                        raise ValueError('Catalogo incompleto')
                    if 'nonempty_list' in item and (not isinstance(data, dict) or not isinstance(data.get(item['nonempty_list']), list) or not data[item['nonempty_list']]):
                        raise ValueError('Dati del catalogo mancanti')
                record['ok'] = True
        except HTTPError as exc:
            record.update(status=exc.code, error='Errore HTTP')
        except (URLError, TimeoutError, OSError, ValueError) as exc:
            # No response body, token, cookie, prompt or user record is logged.
            record['error'] = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
        record['duration_ms'] = round((time.monotonic() - start) * 1000)
        return record

    with ThreadPoolExecutor(max_workers=5) as pool:
        rows = list(pool.map(probe, checks))
    return {'kind': 'live', 'origin': config['origin'], 'checks': rows,
            'failures': [row['path'] + ': ' + row.get('error', 'errore') for row in rows if not row['ok']]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--repair-known-links', action='store_true')
    parser.add_argument('--output', type=Path, default=Path('output/site-monitor/result.json'))
    args = parser.parse_args()
    repaired = repair_aliases() if args.repair_known_links else []
    report = live_checks() if args.live else local_checks()
    report.update(checked_at=datetime.now(timezone.utc).isoformat(), repaired_aliases=repaired)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    summary = os.getenv('GITHUB_STEP_SUMMARY')
    if summary:
        lines = ['## Controllo del sito', '', f"Esito: {'problemi rilevati' if report['failures'] else 'controlli superati'}", '']
        lines += ['- ' + item for item in report['failures']] or ['Pagine e controlli previsti disponibili.']
        with open(summary, 'a') as out:
            out.write('\n'.join(lines) + '\n')
    return 1 if report['failures'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
