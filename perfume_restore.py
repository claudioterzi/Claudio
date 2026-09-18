"""Reopen exported creations without composing, publishing or archiving them."""
import json
import math
import re
from urllib.parse import urlsplit

from studio.parfums.formula_code import encode, decode
from perfume_visual import bottle_brief

MAX_FILE_BYTES = 300_000


def text(value, limit=12000):
    if not isinstance(value, str) or len(value) > limit:
        raise ValueError('Testo non valido nella scheda.')
    return value


def fields(value, names, limit=12000):
    if not isinstance(value, dict):
        raise ValueError('Struttura della scheda non valida.')
    return {name: text(value[name], limit) for name in names if name in value}


def items(value, limit):
    if not isinstance(value, list) or len(value) > limit:
        raise ValueError('Elenco non valido nella scheda.')
    return value


def restore(raw):
    if len(raw) > MAX_FILE_BYTES:
        raise ValueError('La scheda supera 300 KB.')
    try:
        saved = json.loads(raw)
        if not isinstance(saved, dict) or saved.get('schema_version') != 1:
            raise ValueError('Formato della scheda non riconosciuto.')
        original = saved['perfume']
        perfume = fields(original, ('nome', 'fam', 'liv', 'concept', 'ragionamento', 'gusti_cliente', 'riferimento'))
        for name in ('nome', 'fam', 'liv'):
            text(perfume[name], 200)
        customer = text(saved.get('customer', ''), 60)
        intention = text(saved.get('intention', ''), 3000)
        rows = items(original['ricetta'], 293)
        normalized = []
        for row in rows:
            if (not isinstance(row, list) or len(row) != 5 or type(row[1]) is not int
                    or type(row[2]) not in (int, float) or not math.isfinite(row[2])
                    or type(row[4]) not in (bool, int) or row[4] not in (0, 1)
                    or row[3] not in ('testa', 'cuore', 'fondo', 'scia')):
                raise ValueError('Ingrediente o dose non validi.')
            normalized.append(dict(nome=text(row[0], 200), n=row[1], parti=row[2], livello=row[3], micro=row[4]))
        if not rows or len({r['n'] for r in normalized}) != len(rows):
            raise ValueError('La formula contiene materie duplicate o mancanti.')
        code = original.get('formula_code')
        if code:
            if not isinstance(code, str) or len(code) > 12000 or not re.fullmatch(r'TRZ1\.[0-9a-f]{16}\.[0-9:TCFS-]+\.[0-9a-f]{12}', code):
                raise ValueError('Codice della formula non valido.')
            if decode(code) != normalized:
                raise ValueError('La ricetta non corrisponde al suo codice.')
        else:
            code = encode(normalized)
        perfume.update(ricetta=rows, formula_code=code)
        if original.get('esempio'):
            perfume['esempio'] = fields(original['esempio'], ('provenienza', 'intenzione'))
        if original.get('foto'):
            photo = original['foto']
            cleaned = fields(photo, ('direzione', 'incertezze'))
            cleaned['osservazioni'] = [text(v, 3000) for v in items(photo.get('osservazioni', []), 5)]
            cleaned['associazioni'] = [fields(v, ('elemento', 'evocazione'), 3000) for v in items(photo.get('associazioni', []), 5)]
            # Only the already public photograph may be embedded on reopening.
            if photo.get('esempio_pubblico') == 'cantiere':
                cleaned['esempio_pubblico'] = 'cantiere'
            for name in ('analysis_version', 'image_sha256'):
                if name in photo and isinstance(photo[name], (str, int)):
                    cleaned[name] = photo[name]
            perfume['foto'] = cleaned
        if original.get('preferenze'):
            preferences = original['preferenze']
            cleaned = fields(preferences, ('origin', 'status'), 100)
            cleaned['items'] = [fields(v, ('name', 'relation', 'clarification'), 1000) for v in items(preferences.get('items', []), 5)]
            perfume['preferenze'] = cleaned
        if original.get('ricerca'):
            research = original['ricerca']
            cleaned = fields(research, ('reference', 'summary', 'consulted_at', 'status'))
            sources = []
            for source in items(research.get('sources', []), 20):
                entry = fields(source, ('title', 'url'), 3000)
                url = urlsplit(entry['url'])
                if url.scheme != 'https' or not url.hostname or url.username or url.password:
                    raise ValueError('Collegamento non valido nella scheda.')
                sources.append(entry)
            cleaned['sources'] = sources
            # Never restore executable suggestion markup or arbitrary image URLs.
            perfume['ricerca'] = cleaned
        perfume['flacone'] = bottle_brief(perfume)
        lab = saved.get('laboratory') or original.get('lab_draft')
        if lab:
            cleaned = fields(lab, ('basis', 'concentration', 'density', 'support'), 300)
            if cleaned['basis'] not in ('g', 'ml'):
                raise ValueError('Unità del laboratorio non valida.')
            for name in ('concentration', 'density'):
                if not re.fullmatch(r'\d{0,3}(?:\.\d{0,6})?', cleaned[name]):
                    raise ValueError('Dato del laboratorio non valido.')
            declarations = items(lab.get('preparations', []), len(rows))
            identifiers = {r[1] for r in rows}
            seen = set()
            cleaned['preparations'] = []
            for entry in declarations:
                n = entry['n']
                if type(n) is not int or n not in identifiers or n in seen:
                    raise ValueError('Preparazione estranea alla formula.')
                seen.add(n)
                cleaned['preparations'].append({'n':n, 'preparation':text(entry['preparation'], 120)})
            cleaned['production_validated'] = False
            perfume['lab_draft'] = cleaned
        presentation = saved.get('presentation') or {}
        variant = (presentation.get('bottle') or {}).get('label')
        return dict(perfume=perfume, customer=customer, intention=intention,
                    restored_variant=variant if variant in ('Scultura', 'Essenza') else 'Scultura')
    except (KeyError, TypeError, AttributeError, OSError, OverflowError, RecursionError) as exc:
        raise ValueError('Scheda incompleta o non compatibile. Usa “Scarica scheda e formula”.') from exc
