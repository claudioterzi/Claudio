"""Opt-in HTTPS smoke test using a fictitious creation; never prints credentials.

Set TERZI_QA_PASSWORD and run against the explicitly authorized production site.
The evidence file preserves creation_id so an interrupted run does not invent
another formula. This test retains its clearly labelled sample in the archive.
"""
import argparse
import hashlib
import http.cookiejar
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request
import uuid


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--evidence', required=True)
    args = parser.parse_args()
    target = Path(args.evidence)
    report = json.loads(target.read_text()) if target.exists() else {
        'schema_version': 1, 'date': '2026-09-10',
        'creation_id': str(uuid.uuid4()), 'checks': {},
        'scope': 'HTTPS production integration test; fictitious customer',
    }
    target.parent.mkdir(parents=True, exist_ok=True)

    def checkpoint():
        target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')

    def check(name, ok):
        report['checks'][name] = bool(ok)
        checkpoint()
        print(json.dumps({'check': name, 'passed': bool(ok)}), flush=True)
        if not ok:
            raise AssertionError(name)

    checkpoint()
    origin = 'https://claudio-ebon.vercel.app'
    password = os.environ['TERZI_QA_PASSWORD']

    def session():
        jar = http.cookiejar.CookieJar()
        return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar)), jar

    def request(client, path, data=None):
        body = urllib.parse.urlencode(data).encode() if data is not None else None
        req = urllib.request.Request(origin + path, data=body, headers={
            'Origin': origin, 'Cache-Control': 'no-cache',
            'User-Agent': 'Terzi-Archive-QA/1.0',
        })
        try:
            response = client.open(req, timeout=75)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            return response.status, response.read().decode(), response.headers

    def payload(html):
        match = re.search(r'<script type="application/json" id="perfume-data">(.*?)</script>', html, re.S)
        return json.loads(match.group(1)) if match else None

    def csrf(html):
        match = re.search(r'name="csrf_token" value="([^"]+)"', html)
        if not match:
            raise AssertionError('CSRF field missing')
        return match.group(1)

    public, _ = session()
    form = {'q': 'Collaudo archivio del 10 settembre 2026: interpreta il calore del ferro e la luce del tramonto nella fotografia di esempio.',
            'cliente': 'Collaudo Archivio', 'foto_esempio': 'cantiere',
            'creation_id': report['creation_id'], 'ondata': '2', 'stile': 'ellena'}
    status, html, headers = request(public, '/profumo', form)
    result = payload(html)
    check('photo_creation_http_200', status == 200 and result is not None)
    check('formula_saved_in_production', bool(result.get('serial')) and 'FORMULA ARCHIVIATA' in html)
    record = result['record']
    report['serial'] = record['serial']
    report['perfume_name'] = result['name']
    report['formula_sha256'] = record['formula_sha256']
    report['photo_analysis_version'] = record['perfume'].get('foto', {}).get('analysis_version')
    checkpoint()
    expected = hashlib.sha256(json.dumps(record['perfume'], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    check('formula_checksum_matches', expected == record['formula_sha256'])
    check('recipe_totals_100', abs(sum(float(row[2]) for row in record['perfume']['ricetta']) - 100) < 1e-6)
    status, repeated, _ = request(public, '/profumo', form)
    check('repeated_request_preserves_exact_record', status == 200 and payload(repeated)['record'] == record)
    path = '/atelier/archivio?serial=' + urllib.parse.quote(record['serial'])
    status, private, headers = request(public, path)
    check('anonymous_cannot_read_formula', status == 200 and payload(private) is None and 'Password archivio' in private)
    check('private_response_not_cacheable_or_cross_origin', headers.get('Cache-Control') == 'no-store' and headers.get('Access-Control-Allow-Origin') is None)

    first, first_jar = session()
    second, _ = session()
    for index, client in enumerate((first, second), 1):
        _, login, _ = request(client, '/atelier/archivio')
        status, listing, _ = request(client, '/atelier/archivio', {'password': password, 'csrf_token': csrf(login)})
        check('session_' + str(index) + '_login_and_listing', status == 200 and record['serial'] in listing and 'Esci dall’archivio' in listing)
        status, reopened, _ = request(client, path)
        loaded = payload(reopened)
        check('session_' + str(index) + '_exact_formula_reopen', status == 200 and loaded is not None and loaded['record'] == record)
        check('session_' + str(index) + '_dedication_preserved', loaded['dedication'] == result['dedication'])

    auth_cookie = next(cookie for cookie in first_jar if cookie.name == 'terzi_archive')
    check('cookie_secure_httponly_strict', auth_cookie.secure and auth_cookie.has_nonstandard_attr('HttpOnly') and auth_cookie.get_nonstandard_attr('SameSite') == 'Strict')
    _, listing, _ = request(first, '/atelier/archivio')
    status, logged_out, _ = request(first, '/atelier/archivio/esci', {'csrf_token': csrf(listing)})
    check('logout_returns_login', status == 200 and 'Password archivio' in logged_out)
    first_jar.set_cookie(auth_cookie)
    status, replayed, _ = request(first, path)
    check('logged_out_cookie_revoked_on_server', status == 200 and payload(replayed) is None and 'Password archivio' in replayed)
    status, other, _ = request(second, path)
    check('separate_session_remains_valid', status == 200 and payload(other)['record'] == record)
    _, listing, _ = request(second, '/atelier/archivio')
    request(second, '/atelier/archivio/esci', {'csrf_token': csrf(listing)})
    report['completed'] = True
    report['limitations'] = ['Provider backup/restore not tested', 'Native browser sign-in and iPhone not tested',
                             'Chosen access word also appears in public creative content; separate private password required before customer use']
    checkpoint()
    print(json.dumps({'completed': True, 'serial': record['serial'], 'checks': len(report['checks'])}), flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # HTTP/client exceptions can include credentials or URLs: type only.
        print(json.dumps({'completed': False, 'error_type': type(error).__name__}), flush=True)
        raise SystemExit(1)
