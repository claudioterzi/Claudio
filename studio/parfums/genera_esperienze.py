"""Indici e QR delle esperienze editoriali. Nessun documentario AI viene simulato."""
import base64
import io
import json
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[2]
ORIGIN = 'https://claudio-ebon.vercel.app'


def qr_png(identifier):
    from reportlab.graphics.barcode.qrencoder import QRCode, QRErrorCorrectLevel
    from PIL import Image, ImageDraw
    qr = QRCode(None, QRErrorCorrectLevel.M)
    qr.addData(f'{ORIGIN}/esperienza.html?id={identifier}')
    qr.make()
    count, scale, border = qr.getModuleCount(), 6, 4
    image = Image.new('1', ((count + border * 2) * scale,) * 2, 1)
    draw = ImageDraw.Draw(image)
    for row in range(count):
        for col in range(count):
            if qr.isDark(row, col):
                x, y = (col + border) * scale, (row + border) * scale
                draw.rectangle((x, y, x + scale - 1, y + scale - 1), fill=0)
    out = io.BytesIO()
    image.save(out, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(out.getvalue()).decode('ascii')


def qr_block(identifier, title='Percorso visivo del profumo'):
    url = f'{ORIGIN}/esperienza.html?id={identifier}'
    return (f'<div class="olf-qr"><a href="{url}" aria-label="Apri {escape(title)}">'
            f'<img src="{qr_png(identifier)}" alt="QR: {escape(title)}" width="246" height="246"></a>'
            f'<div><strong>{escape(title)}</strong><p><a href="{url}">{identifier} · Apri il percorso</a></p>'
            '<p class="olf-note">Sceneggiatura e collegamento all’Atelier.<br>Documentario 3D AI in progetto.</p></div></div>')


def generate():
    canon = json.loads((ROOT / 'studio/parfums/parfums_400.json').read_text())
    entries = []
    for perfume in canon['parfums']:
        materials = list(dict.fromkeys(row['nome'] for row in perfume['ricetta']))
        scenes = []
        for level, title in [('testa', 'Apertura'), ('cuore', 'Il cuore'), ('fondo', 'La traccia')]:
            names = ', '.join(row['nome'] for row in perfume['ricetta'] if row['livello'] == level)
            scenes.append({'title': title, 'text': f'Interpretare visivamente {names}. '
                           'Luce, superfici e movimento sono scelte creative da confrontare con il campione.'})
        entries.append({'id': f'P{perfume["numero"]:03d}', 'kind': 'Libro dei 400',
            'title': perfume['nome'], 'number': perfume['numero'], 'family': perfume['famiglia'],
            'concept': perfume['concept'], 'materials': materials, 'scenes': scenes,
            'source': f'libro.html#profumo-{perfume["numero"]:03d}',
            'status': 'Sceneggiatura preliminare da dati del libro', 'media': None})
    categories = [('M00-IND', 'Industria', 'Il prodotto, il contesto del lancio, il campione e la sua evoluzione.'),
                  ('M00-NIC', 'Nicchia', 'La maison, l’intenzione del profumiere e il linguaggio della creazione.'),
                  ('M00-MAT', 'Materie prime', 'L’origine documentata della materia, il processo e la prova sul campione.')]
    for identifier, title, text in categories:
        entries.append({'id': identifier, 'kind': 'Magazine · modello di articolo', 'title': title,
            'concept': text, 'materials': [], 'source': 'magazine.html', 'media': None,
            'status': 'Articolo e campione da selezionare', 'scenes': [
                {'title': 'La fonte', 'text': 'Raccogliere informazioni, immagini e autorizzazioni dalla maison o dal produttore.'},
                {'title': 'Il racconto', 'text': text},
                {'title': 'Il campione', 'text': 'Associare l’articolo alla mouillette e registrare le osservazioni.'}]})
    entries.append({'id': 'LAVANDA', 'kind': 'Episodio pilota · idea di Claudio Terzi',
        'title': 'Lavanda, nel sud della Francia', 'materials': ['Lavanda'], 'source': 'magazine.html#ponte-immersivo',
        'concept': 'Dal luogo alla materia, dalla materia al profumo: un viaggio che può essere percorso anche al contrario.',
        'status': 'Storyboard: luoghi, riprese e campione da documentare', 'media': None,
        'scenes': [
            {'title': '01 · Il paesaggio', 'text': 'Entrare in un campo di lavanda nel sud della Francia. Scegliere un luogo reale, documentarlo e associare riprese autorizzate.'},
            {'title': '02 · La pianta', 'text': 'Avvicinarsi alla pianta e distinguere la materia effettivamente trattata nell’articolo. Identità botanica e provenienza da verificare.'},
            {'title': '03 · La trasformazione', 'text': 'Seguire il processo di lavorazione presso il produttore. Ricostruzioni generate dall’AI devono essere riconoscibili come tali.'},
            {'title': '04 · L’incontro', 'text': 'Il racconto invita a prendere la mouillette indicata sull’inserto, osservare il campione e annotare le proprie associazioni.'},
            {'title': '05 · Il ritorno', 'text': 'Trasformare le immagini del viaggio in una nuova intenzione olfattiva nell’Atelier; dalla nuova formula costruire un’altra lettura visiva.'}]})
    target = ROOT / 'public/esperienze-olfattive.json'
    target.write_text(json.dumps({'version': 1, 'author': 'Claudio Terzi', 'entries': entries}, ensure_ascii=False, separators=(',', ':')))
    page = ROOT / 'public/magazine.html'
    html = page.read_text()
    for identifier, title, _ in categories:
        marker = f'<!-- QR:{identifier} -->'
        start, end = f'<!-- QR-BEGIN:{identifier} -->', f'<!-- QR-END:{identifier} -->'
        block = start + qr_block(identifier, 'Esperienza · ' + title) + end
        if marker in html:
            html = html.replace(marker, block)
        elif start in html:
            a, b = html.index(start), html.index(end) + len(end)
            html = html[:a] + block + html[b:]
    marker = '<!-- QR:LAVANDA -->'
    start, end = '<!-- QR-BEGIN:LAVANDA -->', '<!-- QR-END:LAVANDA -->'
    block = start + qr_block('LAVANDA', 'Lavanda · Episodio pilota') + end
    if marker in html:
        html = html.replace(marker, block)
    elif start in html:
        a, b = html.index(start), html.index(end) + len(end)
        html = html[:a] + block + html[b:]
    page.write_text(html)
    print(f'{len(entries)} percorsi indicizzati; QR del magazine aggiornati.')


if __name__ == '__main__':
    generate()
