"""Selezione locale e verificabile: rinnova soltanto temi con dossier completati."""

from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MARKER = '<!-- STUDIO_SELECTION_V1 '
PUNTI = {'ALTA': 300, 'MEDIA': 200, 'BASSA': 100}


def _task(testo):
    """Legge solo intestazioni strutturate; il contenuto non è un'istruzione."""
    priorita = 'BASSA'
    task = {}
    corrente = None
    for linea in testo.splitlines():
        sezione = re.fullmatch(r'## (ALTA|MEDIA|BASSA) PRIORITÀ', linea)
        if sezione:
            priorita = sezione[1]
            corrente = None
        elif linea.startswith('## '):
            corrente = None
        intestazione = re.fullmatch(r'### \[(PENDING|DONE[^\]]*)\] ([A-Z][A-Z0-9-]*-\d+) — (.+)', linea)
        if intestazione:
            corrente = {'stato': intestazione[1], 'priorita': priorita}
            task[intestazione[2]] = corrente
        elif corrente is not None:
            output = re.fullmatch(r'\*\*Output atteso:\*\* `([^`]+)`', linea)
            if output:
                corrente['output'] = output[1]
    return task


def _ultimo_rinnovo(root, oggi):
    ultimi = {}
    for file in (root / 'output/morning_brief').glob('????-??-??.md'):
        try:
            giorno = datetime.date.fromisoformat(file.stem)
            # Una ripetizione nello stesso giorno conserva lo stesso ordine.
            if giorno >= oggi:
                continue
            with file.open(encoding='utf-8') as stream:
                prima = stream.readline().strip()
            if not prima.startswith(MARKER) or not prima.endswith(' -->'):
                continue  # I vecchi brief senza metadati non provano un rinnovo.
            dati = json.loads(prima[len(MARKER):-4])
            if dati['data'] != file.stem:
                continue
            for indice in dati['temi']:
                if type(indice) is int and indice >= 0:
                    ultimi[indice] = max(ultimi.get(indice, giorno), giorno)
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return ultimi


def seleziona_temi(temi, oggi=None, root=None):
    """Priorità del registro + anzianità del rinnovo, mai nuovi temi dal modello.

    Il massimo di 600 punti di anzianità evita che la priorità storica escluda
    per sempre i temi minori. PENDING ha un bonus solo con un tema esplicito.
    """
    root = Path(root) if root is not None else ROOT
    oggi = oggi or datetime.date.today()
    config = json.loads((root / 'studio/temi_lavorati.json').read_text(encoding='utf-8'))
    if config.get('modalita') != 'solo_temi_lavorati':
        raise ValueError('Lo Studio richiede la modalità solo_temi_lavorati')
    registro = (root / 'TASK_AUTONOMI.md').read_text(encoding='utf-8')
    task = _task(registro)
    ultimi = _ultimo_rinnovo(root, oggi)
    selezioni = []
    visti = set()
    for voce in config['temi']:
        indice = voce['indice']
        if type(indice) is not int or indice not in range(6) or indice not in temi or indice in visti:
            raise ValueError('Indice tema duplicato o sconosciuto')
        visti.add(indice)
        dossier = []
        priorita = 'BASSA'
        date_originali = []
        for task_id in voce['task_completati']:
            precedente = task.get(task_id, {})
            data = re.fullmatch(r'DONE (\d{4}-\d{2}-\d{2})(?:.*)', precedente.get('stato', ''))
            relativo = precedente.get('output', '')
            percorso = (root / relativo).resolve()
            archivio = (root / 'output/task_output').resolve()
            if not data or percorso.parent != archivio or not percorso.is_file():
                continue
            try:
                giorno = datetime.date.fromisoformat(data[1])
                if giorno > oggi:
                    continue
                contenuto = percorso.read_text(encoding='utf-8')
            except (ValueError, OSError):
                continue  # Un dossier corrotto non rende inutilizzabili gli altri.
            if not contenuto.strip():
                continue
            dossier.append({'id': task_id, 'path': relativo, 'data': giorno.isoformat(),
                            'sha256': hashlib.sha256(contenuto.encode()).hexdigest(),
                            'testo': contenuto[:6000], 'troncato': len(contenuto) > 6000})
            date_originali.append(giorno)
            if PUNTI[precedente['priorita']] > PUNTI[priorita]:
                priorita = precedente['priorita']
        if not dossier:
            continue  # Nessun dossier valido: mai ripiegare sulla wildcard.
        ultimo = max(date_originali + ([ultimi[indice]] if indice in ultimi else []))
        giorni = min(60, max(0, (oggi - ultimo).days))
        # Solo il tag esplicito nel blocco PENDING può associare un nuovo lavoro
        # a un tema già studiato; non si inventano collegamenti da parole chiave.
        pending = []
        for blocco in re.split(r'(?=^### )', registro, flags=re.MULTILINE):
            trovato = re.match(r'### \[PENDING\] ([A-Z][A-Z0-9-]*-\d+) — ', blocco)
            if trovato and re.search(rf'^\*\*Tema studio:\*\* {indice}\s*$', blocco, re.MULTILINE):
                pending.append(trovato[1])
        punteggio = PUNTI[priorita] + giorni * 10 + (500 if pending else 0)
        motivo = (f'priorità {priorita} in TASK_AUTONOMI.md; ultimo lavoro tracciato {ultimo}; '
                  f'{giorni} giorni di anzianità conteggiati (massimo 60)')
        if pending:
            motivo += '; task aperti associati: ' + ', '.join(pending)
        selezioni.append({'indice': indice, 'punteggio': punteggio, 'motivo': motivo,
                          'dossier': dossier, 'ambito': voce['ambito']})
    selezioni.sort(key=lambda x: (-x['punteggio'], x['indice']))
    if not selezioni:
        raise RuntimeError('Nessun tema già lavorato con dossier completato disponibile')
    return selezioni[:3]


def descrivi_selezione(selezioni, temi, oggi):
    metadati = json.dumps({'data': oggi.isoformat(), 'temi': [s['indice'] for s in selezioni]}, ensure_ascii=False)
    righe = [MARKER + metadati + ' -->', '## Perché questi temi', '',
             'Rinnovo di temi già lavorati. Priorità documentata nel registro e anzianità del rinnovo, '
             'non una valutazione di urgenze in tempo reale. Nessun nuovo tema viene aggiunto.', '']
    for scelta in selezioni:
        righe.append(f"- **{temi[scelta['indice']]['nome']}**: {scelta['motivo']} (punteggio {scelta['punteggio']}).")
        for dossier in scelta['dossier']:
            # Il percorso del brief è output/morning_brief, quello del dossier è output/task_output.
            righe.append(f"  - [{dossier['id']} del {dossier['data']}](../task_output/{Path(dossier['path']).name}) "
                         f"· SHA-256 {dossier['sha256']}")
    righe.extend(['', 'I dossier originali restano invariati. Le affermazioni storiche richiedono nuova verifica.', '', '---', ''])
    return '\n'.join(righe)
