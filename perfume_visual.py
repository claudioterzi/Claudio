"""Recipe-bound art direction. Concept and copyright: Claudio Terzi, 2026.

Only public catalogue descriptors leave the server; no customer, story,
commercial reference, serial or exact formula is sent to the image service.
"""
import hashlib
import json
from pathlib import Path

STYLES = {
    'Agrumata': ('oro limone e cristallo trasparente', 'luce radente, riflessi solari netti'),
    'Floreale': ('perla, ametista tenue e oro chiaro', 'luce diffusa, rifrazioni delicate'),
    'Verde': ('verde profondo e argento satinato', 'ombre botaniche astratte, luce di bosco'),
    'Acquatica': ('blu petrolio e cristallo ghiaccio', 'caustiche acquatiche, luce liquida'),
    'Legnosa': ('ambra fumé e bronzo', 'luce calda radente, ombre architettoniche'),
    'Orientale': ('ambra intensa e oro brunito', 'chiaroscuro caldo, profondità resinosa'),
    'Speziata': ('rame e vetro granato', 'tagli di luce caldi, riflessi vibranti'),
    'Gourmand': ('cacao, champagne e vetro miele', 'luce vellutata, riflessi morbidi'),
}
SHAPES = (
    'monolite sfaccettato con spalle oblique e tappo prismatico',
    'ovale scultoreo con base massiccia e tappo in metallo satinato',
    'prisma esagonale con fianchi scanalati e tappo a disco',
    'volume a goccia allungata, fronte piano e tappo in cristallo',
    'rettangolo morbido con vetro spesso e tappo architettonico asimmetrico',
    'colonna ottagonale con base ottica e tappo ceramico',
)


def bottle_brief(perfume):
    catalog = json.loads((Path(__file__).parent / 'studio/parfums/organo_terzi_300.json').read_text())
    by_id = {m['n']: m for m in catalog['materie'] if m.get('tipo') != 'SOL'}
    rows = [r for r in perfume.get('ricetta', []) if len(r) >= 4 and r[1] in by_id]
    signature = hashlib.sha256(json.dumps(sorted((r[1], r[2], r[3]) for r in rows)).encode()).hexdigest()
    # Each layer contributes; the original formula doses are never transmitted.
    accents = []
    for level in ('testa', 'cuore', 'fondo', 'scia'):
        group = sorted((r for r in rows if r[3] == level), key=lambda r: -r[2])
        if group:
            accents.append(by_id[group[0][1]]['nome'])
    palette, light = STYLES.get(perfume.get('fam'), STYLES['Orientale'])
    shape = SHAPES[int(signature[:8], 16) % len(SHAPES)]
    prompt = (
        'Use case: product-mockup. Create ONE original, photorealistic niche perfume bottle. '
        'Art direction by Claudio Terzi. Do not copy a commercial bottle, logo or packaging. '
        f'Bottle silhouette: {shape}. Palette: {palette}. Lighting: {light}. '
        'Translate these olfactory accents into tactile glass, cap finish and abstract light, '
        'not literal ingredients inside the bottle: ' + ', '.join(accents) + '. '
        'Refine the geometry and surface details creatively. Thick optical glass, credible refraction, '
        'premium materials, exquisite editorial product photography. Square image, front view, '
        'full bottle and cap visible, bottle occupies x=25%..75%, y=12%..86%. '
        'Keep a flat front face with a blank dark rectangular plaque at x=37%..63%, y=47%..65% '
        'so a precise typographic label can be applied separately. No text, letters, logos, watermark, '
        'people, additional bottles, advertising layouts or health claims. '
        'This is a visual concept, not a manufacturing drawing.'
    )
    return dict(version='terzi-visual-2', recipe_fingerprint=signature, forma=shape,
                palette=palette, luce=light, accenti=accents, prompt=prompt,
                attribution='Concept e direzione: Claudio Terzi · © 2026 Claudio Terzi')
