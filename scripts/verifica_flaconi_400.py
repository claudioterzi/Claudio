"""Verify recipe/image identity, all embedded raster files and a print sample."""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from studia_libro_400 import audit


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, list):
        return [canonical(v) for v in value]
    return value


def verify():
    source = ROOT / 'studio/parfums/parfums_400.json'
    perfumes = json.loads(source.read_text())['parfums']
    manifest = json.loads((ROOT / 'studio/parfums/flaconi_400.json').read_text())
    photo_file = ROOT / 'studio/parfums/foto_400.json'
    photographs = {p['numero']: p for p in json.loads(photo_file.read_text())['perfumes']} if photo_file.exists() else {}
    soup = BeautifulSoup((ROOT / 'public/libro.html').read_text(), 'html.parser')
    sheets = {sheet['id']: sheet for sheet in soup.select('.scheda')}
    shapes, images, body_pixels = set(), set(), set()
    assert len(manifest['perfumes']) == len(perfumes) == 400
    for p, record in zip(perfumes, manifest['perfumes']):
        number = p['numero']
        assert record['numero'] == number and record['nome'] == p['nome']
        recipe = sorted([[r['n'], r['parti'], r['livello'], bool(r['micro'])] for r in p['ricetta']])
        signature = sha(json.dumps(canonical(recipe), separators=(',', ':')).encode())
        assert signature == record['recipe_fingerprint'], number
        image_path = ROOT / 'public' / record['src']
        content = image_path.read_bytes()
        assert sha(content) == record['sha256'], number
        svg = ET.fromstring(content)
        assert p['nome'] in svg.find('{http://www.w3.org/2000/svg}title').text
        node = svg.find('{http://www.w3.org/2000/svg}image')
        uri = node.attrib['{http://www.w3.org/1999/xlink}href']
        assert uri.startswith('data:image/jpeg;base64,')
        jpg = base64.b64decode(uri.split(',', 1)[1], validate=True)
        with Image.open(io.BytesIO(jpg)) as drawing:
            drawing.load()
            assert drawing.size == (900, 1200)
            # Excludes all typographic labels: distinct names alone do not pass.
            body_pixels.add(sha(drawing.crop((170, 65, 730, 500)).tobytes()))
        sheet = sheets[f'profumo-{number:03d}']
        image = sheet.select_one('.flacone-fotonico img')
        primary = photographs.get(number, {}).get('primary') or record['src']
        assert image['src'] == primary
        assert image.parent['href'] == primary
        if primary != record['src']:
            assert sheet.select_one('.disegno-collezione')['href'] == record['src']
        for photo in photographs.get(number, {}).get('photos', []):
            assert sha((ROOT / 'public' / photo['src']).read_bytes()) == photo['sha256']
            assert sheet.select_one(f'a[href="{photo["src"]}"]')
        assert 'C.Terzi' in sheet.select_one('figcaption').get_text()
        shapes.add(record['geometry_fingerprint'])
        images.add(sha(jpg))
    assert len(shapes) == len(images) == len(body_pixels) == 400
    legacy = audit()
    assert not legacy['failures'], legacy['failures']
    assert len(soup.select('.scheda .olf-qr img')) == 400
    assert soup.select_one('#rubrica-olfattiva')
    return {
        'date': '2026-09-10', 'canonical_sha256': sha(source.read_bytes()),
        'book_sha256': sha((ROOT / 'public/libro.html').read_bytes()),
        'recipes_verified': 400, 'bottle_images': len(images),
        'distinct_geometries': len(shapes), 'distinct_pixels_excluding_labels': len(body_pixels),
        'recipe_codes_verified': legacy['recipes']['codes_checked'],
        'recipe_rows_verified': legacy['book']['recipe_rows'], 'qr_in_sheets': 400,
        'mouillette_insert_present': True, 'failures': [],
        'photos_associated': sum(len(p['photos']) for p in photographs.values()),
        'visual_scope': '400 native 3D illustrations; one separately identified AI artistic example.',
        'browser_qa': 'Not requested; not performed.',
    }


def print_sample(output):
    from weasyprint import HTML
    from pypdf import PdfReader
    soup = BeautifulSoup((ROOT / 'public/libro.html').read_text(), 'html.parser')
    ids = [1, 51, 101, 151, 201, 251, 301, 400]
    sheets = ''.join(str(soup.select_one(f'#profumo-{n:03d}')) for n in ids)
    # Use the real book stylesheet and unmodified cards; allow natural pagination.
    sample = f'<!doctype html><html lang="it">{soup.head}<body><main class="libro">{sheets}</main></body></html>'
    HTML(string=sample, base_url=str(ROOT / 'public')).write_pdf(str(output))
    pdf = PdfReader(output)
    assert len(pdf.pages) == 8, f'Unexpected pagination: {len(pdf.pages)}'
    for page, number in zip(pdf.pages, ids):
        text = page.extract_text()
        assert f'N° {number}' in text and 'Codice di ricostruzione' in text
        assert 'TRZ1' in text and 'Mouillette' in text and 'Posizione' in text
    return {'pages': len(pdf.pages), 'recipes': ids, 'sha256': sha(output.read_bytes())}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', required=True, type=Path)
    parser.add_argument('--pdf', type=Path)
    args = parser.parse_args()
    result = verify()
    if args.pdf:
        args.pdf.parent.mkdir(parents=True, exist_ok=True)
        result['print_sample'] = print_sample(args.pdf)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
