"""Append-only perfume image import and automatic book image registry.

Images are matched by explicit canonical recipe number, never by guessed names.
The newest valid image becomes primary; drawings and older images remain available.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
PATTERN = re.compile(r'^P(?P<number>\d{3})--(?P<stamp>\d{8}T\d{12}Z)--(?P<kind>immagine|fotografia|studio-ia)--(?P<digest>[a-f0-9]{12})\.(?P<ext>jpg|png|webp)$')
KINDS = {'immagine': 'Immagine', 'fotografia': 'Fotografia', 'studio-ia': 'Studio artistico IA'}


def image_info(path):
    if path.stat().st_size > 15 * 1024 * 1024:
        raise ValueError('Immagine oltre 15 MB')
    with Image.open(path) as image:
        if image.format not in {'JPEG', 'PNG', 'WEBP'}:
            raise ValueError('Formato non supportato: usare JPEG, PNG o WebP')
        if image.width * image.height > 40_000_000 or min(image.size) < 64:
            raise ValueError('Dimensioni immagine non supportate')
        image.verify()
        return image.format, image.width, image.height


def load_perfumes(root):
    return {p['numero']: p for p in json.loads((root / 'studio/parfums/parfums_400.json').read_text())['parfums']}


def import_image(source, number, kind='immagine', root=ROOT):
    root, source = Path(root), Path(source)
    if number not in load_perfumes(root):
        raise ValueError('Numero di profumo assente dal libro: nessuna associazione effettuata')
    if kind not in KINDS:
        raise ValueError('Tipo di immagine non valido')
    fmt, _, _ = image_info(source)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    folder = root / 'public/images/foto-profumi'
    folder.mkdir(parents=True, exist_ok=True)
    for existing in folder.glob(f'P{number:03d}--*'):
        if hashlib.sha256(existing.read_bytes()).hexdigest() == digest:
            return existing, False
    ext = {'JPEG': 'jpg', 'PNG': 'png', 'WEBP': 'webp'}[fmt]
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    target = folder / f'P{number:03d}--{stamp}--{kind}--{digest[:12]}.{ext}'
    # Exclusive creation: no existing photo can be silently replaced.
    with source.open('rb') as inp, target.open('xb') as out:
        shutil.copyfileobj(inp, out)
    return target, True


def sync(root=ROOT):
    root = Path(root)
    perfumes = load_perfumes(root)
    registry_path = root / 'studio/parfums/foto_400.json'
    previous = json.loads(registry_path.read_text()) if registry_path.exists() else {'perfumes': []}
    previous_files = {photo['src']: photo['sha256'] for p in previous['perfumes'] for photo in p['photos']}
    records = {n: {'numero': n, 'nome': p['nome'], 'photos': [], 'primary': None} for n, p in perfumes.items()}
    pending, accepted = [], {}
    folder = root / 'public/images/foto-profumi'
    for file in sorted(folder.glob('*')):
        if not file.is_file():
            continue
        match = PATTERN.fullmatch(file.name)
        if not match or int(match['number']) not in records:
            pending.append({'file': file.name, 'reason': 'Riferimento al profumo assente o non valido'})
            continue
        try:
            fmt, width, height = image_info(file)
            expected_ext = {'JPEG': 'jpg', 'PNG': 'png', 'WEBP': 'webp'}[fmt]
            if expected_ext != match['ext']:
                raise ValueError('Estensione e contenuto non corrispondono')
            when = datetime.strptime(match['stamp'], '%Y%m%dT%H%M%S%fZ').replace(tzinfo=timezone.utc)
            digest = hashlib.sha256(file.read_bytes()).hexdigest()
            if not digest.startswith(match['digest']):
                raise ValueError('Contenuto modificato rispetto alla versione importata')
            src = file.relative_to(root / 'public').as_posix()
            photo = {'src': src, 'sha256': digest, 'created_at': when.isoformat(),
                     'kind': match['kind'], 'label': KINDS[match['kind']],
                     'width': width, 'height': height}
            records[int(match['number'])]['photos'].append(photo)
            accepted[src] = digest
        except (OSError, ValueError, Image.DecompressionBombError) as exc:
            pending.append({'file': file.name, 'reason': str(exc)})
    for src, digest in previous_files.items():
        if accepted.get(src) != digest:
            raise ValueError(f'Foto storica rimossa o alterata: {src}. Registro precedente conservato.')
    for record in records.values():
        record['photos'].sort(key=lambda p: (p['created_at'], p['src']))
        if record['photos']:
            record['primary'] = record['photos'][-1]['src']
    result = {'version': 1, 'policy': 'La nuova immagine valida è principale; le versioni precedenti restano disponibili.',
              'perfumes': list(records.values()), 'unassigned': pending}
    # Stable output: repeated synchronization produces no new commits.
    content = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if not registry_path.exists() or registry_path.read_text() != content:
        temp = registry_path.with_suffix('.json.tmp')
        temp.write_text(content)
        temp.replace(registry_path)
    return records, pending


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--immagine', type=Path)
    parser.add_argument('--profumo', type=int)
    parser.add_argument('--tipo', choices=KINDS, default='immagine')
    args = parser.parse_args()
    if bool(args.immagine) != (args.profumo is not None):
        parser.error('--immagine e --profumo devono essere indicati insieme')
    if args.immagine:
        file, added = import_image(args.immagine, args.profumo, args.tipo)
        print(json.dumps({'file': str(file), 'added': added}, ensure_ascii=False))
    records, pending = sync()
    print(json.dumps({'photos': sum(len(r['photos']) for r in records.values()),
                      'perfumes_with_photos': sum(bool(r['photos']) for r in records.values()),
                      'unassigned': pending}, ensure_ascii=False))
