"""Versioned organ lifecycle. Concept Claudio Terzi, © 2026.

Proposals never enter compositions until explicitly admitted with stock and
supplier evidence. Suspension preserves historical recipes and numeric IDs.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent


def load_registry(path=None):
    path = Path(path) if path else BASE / 'organo_evolution.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('schema_version') != 1 or not isinstance(data.get('overrides'), list):
        raise ValueError('Registro dell’organo non valido')
    return data


def composition_catalog(catalog, registry=None):
    registry = registry if registry is not None else load_registry()
    numbers = {m['n'] for m in catalog['materie']}
    seen, suspended = set(), set()
    for entry in registry['overrides']:
        n = entry.get('n')
        if n not in numbers or n in seen or entry.get('status') not in ('active', 'suspended'):
            raise ValueError('Stato della materia non valido')
        seen.add(n)
        if entry['status'] == 'suspended': suspended.add(n)
    result = dict(catalog)
    result['materie'] = [m for m in catalog['materie'] if m['n'] not in suspended]
    result['evolution_revision'] = registry['revision']
    return result


def _save(path, data):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def set_status(n, status, reason, registry_path=None, catalog_path=None):
    registry_path = Path(registry_path) if registry_path else BASE / 'organo_evolution.json'
    catalog_path = Path(catalog_path) if catalog_path else BASE / 'organo_terzi_300.json'
    registry = load_registry(registry_path)
    catalog = json.loads(catalog_path.read_text())
    if status not in ('active', 'suspended') or not reason.strip():
        raise ValueError('Indica stato e motivazione')
    if n not in {m['n'] for m in catalog['materie']}:
        raise ValueError('Materia non presente nel catalogo')
    now = datetime.now(timezone.utc).isoformat()
    registry['overrides'] = [x for x in registry['overrides'] if x['n'] != n]
    registry['overrides'].append(dict(n=n, status=status, reason=reason.strip(), updated_at=now))
    registry['revision'] += 1
    registry['updated_at'] = now
    registry['events'].append(dict(action=status, n=n, reason=reason.strip(), at=now))
    composition_catalog(catalog, registry)
    _save(registry_path, registry)


def admit_material(proposal_id, evidence, registry_path=None, catalog_path=None, snapshots_path=None):
    """Admit a documented, actually available preparation under a NEW numeric ID."""
    registry_path = Path(registry_path) if registry_path else BASE / 'organo_evolution.json'
    catalog_path = Path(catalog_path) if catalog_path else BASE / 'organo_terzi_300.json'
    snapshots_path = Path(snapshots_path) if snapshots_path else BASE.parents[1] / 'public/formule'
    registry = load_registry(registry_path)
    proposal = next((x for x in registry['proposals'] if x['id'] == proposal_id), None)
    if not proposal or proposal['status'] != 'proposed':
        raise ValueError('Proposta non disponibile per l’ammissione')
    required = ('availability_confirmed_by', 'supplier', 'supplier_product', 'preparation', 'technical_document')
    if not all(isinstance(evidence.get(k), str) and evidence[k].strip() for k in required):
        raise ValueError('Servono conferma della disponibilità, fornitore, prodotto, preparazione e documento tecnico')
    material = dict(evidence.get('material') or {})
    if material.get('nome') != proposal['name']:
        raise ValueError('Il nome deve identificare la proposta esatta')
    if material.get('tipo') not in ('NAT','SIN','BASE') or material.get('livello') not in ('CORE','ESP','MASTER'):
        raise ValueError('Classificazione della materia non valida')
    if not isinstance(material.get('forza'), int) or not 1 <= material['forza'] <= 5:
        raise ValueError('Indicare la forza olfattiva di studio')
    if not material.get('famiglia') or not material.get('nota') or any(c not in 'TCF/' for c in material['nota']):
        raise ValueError('Indicare famiglia e nota T/C/F')
    raw = catalog_path.read_bytes(); catalog = json.loads(raw)
    if any(m['nome'].casefold() == material['nome'].casefold() for m in catalog['materie']):
        raise ValueError('Nome già presente: verificare identità e fornitura prima di duplicare')
    material['n'] = max(m['n'] for m in catalog['materie']) + 1
    material.update(fornitore=evidence['supplier'], preparazione_disponibile=evidence['preparation'],
                    documentazione=evidence['technical_document'])
    material.setdefault('diluizione_studio', '')
    material.setdefault('ruolo_scia', '-')
    material.setdefault('prezzo', '')
    material.setdefault('note_uso', '')
    now = datetime.now(timezone.utc).isoformat()
    catalog['materie'].append(material); catalog['totale_materie'] = len(catalog['materie'])
    proposal.update(status='admitted', n=material['n'], admitted_at=now, evidence=evidence)
    registry['revision'] += 1; registry['updated_at'] = now
    registry['events'].append(dict(action='admitted', proposal=proposal_id, n=material['n'], at=now))
    snapshots_path.mkdir(parents=True, exist_ok=True)
    old_snapshot = snapshots_path / ('organo-' + hashlib.sha256(raw).hexdigest()[:16] + '.json')
    if old_snapshot.exists() and old_snapshot.read_bytes() != raw:
        raise ValueError('Snapshot storico incoerente: nessuna modifica applicata')
    old_snapshot.write_bytes(raw)
    new_raw = (json.dumps(catalog, ensure_ascii=False, indent=2) + '\n').encode()
    new_snapshot = snapshots_path / ('organo-' + hashlib.sha256(new_raw).hexdigest()[:16] + '.json')
    if new_snapshot.exists() and new_snapshot.read_bytes() != new_raw:
        raise ValueError('Snapshot nuovo incoerente')
    new_snapshot.write_bytes(new_raw)
    _save(catalog_path, catalog); _save(registry_path, registry)
    return material['n']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Gestione versionata dell’Organo Terzi')
    sub = parser.add_subparsers(dest='action', required=True)
    for action in ('suspend', 'restore'):
        command = sub.add_parser(action); command.add_argument('n', type=int); command.add_argument('--reason', required=True)
    command = sub.add_parser('admit'); command.add_argument('proposal_id'); command.add_argument('evidence_json', type=Path)
    args = parser.parse_args()
    if args.action == 'admit':
        print('Nuova materia N°', admit_material(args.proposal_id, json.loads(args.evidence_json.read_text())))
    else:
        set_status(args.n, 'suspended' if args.action == 'suspend' else 'active', args.reason)
    print('Registro aggiornato. Rigenerare Atelier e Organo e pubblicare catalogo, snapshot e registro nello stesso commit.')
