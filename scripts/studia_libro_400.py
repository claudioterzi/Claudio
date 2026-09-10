"""Read-only structural audit of the book, canonical recipes and TRZ1 codes."""
import argparse
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bs4 import BeautifulSoup
from studio.parfums.formula_code import decode
from studio.parfums.codice_olfattivo import RACCONTI


def audit():
    raw = (ROOT / 'public/libro.html').read_bytes()
    book = BeautifulSoup(raw, 'html.parser')
    canon = json.loads((ROOT / 'studio/parfums/parfums_400.json').read_text())
    perfumes = canon['parfums']
    materials = {m['n']: m for m in json.loads((ROOT / 'studio/parfums/organo_terzi_300.json').read_text())['materie']}
    codes = {p['numero']: p for p in json.loads((ROOT / 'public/formule/codici-400.json').read_text())}
    sheets = book.select('.scheda')
    failures, warnings = [], []
    signatures, components, templates, body_totals = Counter(), Counter(), Counter(), Counter()
    used = Counter()
    public_rows = 0
    for index, perfume in enumerate(perfumes):
        number, rows = perfume['numero'], perfume['ricetta']
        def fail(reason):
            failures.append({'numero': number, 'reason': reason})
        if sum(Decimal(str(r['parti'])) for r in rows) != 100:
            fail('sum_not_100')
        if len({r['n'] for r in rows}) != len(rows):
            fail('repeated_material')
        for row in rows:
            used[row['n']] += 1
            if row['n'] not in materials or materials[row['n']]['nome'] != row['nome']:
                fail('material_id_name_mismatch')
            elif materials[row['n']].get('tipo') == 'SOL':
                warnings.append({'numero': number, 'material_id': row['n'], 'material': row['nome'],
                                 'parts': row['parti'], 'role': row['livello'],
                                 'reason': 'support_in_sillage_to_review_against_current_atelier_separation'})
        signature = tuple(sorted((r['n'], str(Decimal(str(r['parti'])).normalize()), bool(r['micro'])) for r in rows))
        signatures[signature] += 1
        components[tuple(sorted(r['n'] for r in rows))] += 1
        body_totals[tuple(sum(Decimal(str(r['parti'])) for r in rows if r['livello'] == level) for level in ('testa', 'cuore', 'fondo', 'scia'))] += 1
        expected = [{k: r[k] for k in ('n', 'nome', 'parti', 'livello', 'micro')} for r in rows]
        try:
            if decode(codes[number]['codice']) != expected:
                fail('code_decode_mismatch')
        except Exception as error:
            fail('code_error_' + type(error).__name__)
        sheet = sheets[index]
        if sheet.select_one('h3').get_text(strip=True) != perfume['nome']:
            fail('printed_name_mismatch')
        if sheet.select_one('.concept').get_text(strip=True) != perfume['concept']:
            fail('printed_concept_mismatch')
        if sheet.select_one('.codice-ricetta code').get_text(strip=True) != codes[number]['codice']:
            fail('printed_code_mismatch')
        table_rows = sheet.select('table.ricetta tr')
        public_rows += len(table_rows)
        if len(table_rows) != len(rows):
            fail('printed_recipe_length_mismatch')
        for tr, row in zip(table_rows, rows):
            cells = tr.select('td')
            name = cells[1].get_text(' ', strip=True).replace(' ⚠ 1%', '')
            parts = Decimal(cells[2].get_text(strip=True).replace(',', '.'))
            if name != row['nome'] or parts != Decimal(str(row['parti'])):
                fail('printed_recipe_mismatch')
        args = {level: perfume['piramide'][level][0]['nome'] for level in ('testa', 'cuore', 'fondo')}
        matched = next((i for i, pattern in enumerate(RACCONTI, 1) if pattern.format(**args) == perfume['racconto']), None)
        templates[str(matched)] += 1

    packaging = Counter(tuple(p['packaging'][k] for k in ('flacone', 'tappo', 'astuccio')) for p in perfumes)
    report = {
        'date': '2026-09-10', 'book_sha256': hashlib.sha256(raw).hexdigest(),
        'source_revision': '662923cd0381e99ff295c9e3f35981dc5e20b2fe',
        'book': {'bytes': len(raw), 'sheets': len(sheets), 'recipe_rows': public_rows,
                 'parts': [e.get_text(' ', strip=True) for e in book.select('h1.parte')],
                 'chapters': [e.get_text(' ', strip=True) for e in book.select('h1.capitolo')],
                 'recipe_links': len(book.select('.codice-ricetta a')),
                 'print_buttons_in_html': len([b for b in book.select('button') if 'stamp' in b.get_text().lower()]),
                 'sheet_anchors': sum(bool(s.get('id')) for s in sheets),
                 'table_headers_in_recipes': len(book.select('.scheda .ricetta th')),
                 'unique_bottle_image_sources': dict(Counter(i.get('src') for i in book.select('.scheda img'))),
                 'laboratory_widget_present': bool(book.select('[data-terzi-lab]')) or 'perfume-lab.js' in raw.decode(),
                 'contains_table_of_contents': bool(book.select('nav[aria-label*="Indice"],.indice,#indice'))},
        'recipes': {'count': len(perfumes), 'unique_names': len({p['nome'] for p in perfumes}),
                    'unique_formulas_by_material_dose_micro': len(signatures),
                    'unique_ingredient_sets': len(components),
                    'ingredient_count_distribution': dict(Counter(len(p['ricetta']) for p in perfumes)),
                    'families': dict(Counter(p['famiglia'] for p in perfumes)),
                    'feasibility': dict(Counter(p['fattibilita'] for p in perfumes)),
                    'organo_materials_used': len(used), 'organo_total_materials': len(materials),
                    'olfactory_materials_used': sum(materials[n].get('tipo') != 'SOL' for n in used),
                    'support_materials_used': sum(materials[n].get('tipo') == 'SOL' for n in used),
                    'unused_material_ids': sorted(set(materials) - set(used)),
                    'micro_rows': sum(bool(r['micro']) for p in perfumes for r in p['ricetta']),
                    'body_total_variants': [{'testa_cuore_fondo_scia': list(map(float, levels)), 'recipes': count} for levels, count in body_totals.most_common()],
                    'codes_checked': len(perfumes)},
        'writing': {'unique_complete_concepts': len({p['concept'] for p in perfumes}),
                    'unique_anima_phrases': len({p['anima'] for p in perfumes}),
                    'story_template_distribution': dict(templates),
                    'top_repeated_opening_phrases': Counter(p['anima'] for p in perfumes).most_common(8),
                    'packaging_designs_without_label': len(packaging)},
        'failures': failures, 'review_warnings': warnings,
    }
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    report = audit()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))
