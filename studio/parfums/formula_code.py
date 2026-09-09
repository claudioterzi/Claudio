"""TRZ1: lossless recipe encoding; catalog snapshots must never be overwritten."""
import hashlib
import json
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEVELS = {'testa':'T','cuore':'C','fondo':'F','scia':'S'}

def catalog_bytes():
    return (ROOT/'studio/parfums/organo_terzi_300.json').read_bytes()

def encode(rows):
    catalog = json.loads(catalog_bytes())
    materials = {m['n']:m for m in catalog['materie']}
    entries=[]
    for r in rows:
        if r['n'] not in materials or r['nome'] != materials[r['n']]['nome']:
            raise ValueError('Materiale non corrispondente al catalogo')
        q=Decimal(str(r['parti']))*10
        if q != q.to_integral_value() or q <= 0:
            raise ValueError('TRZ1 richiede parti positive con precisione 0,1')
        entries.append(f"{r['n']}:{int(q)}:{LEVELS[r['livello']]}:{int(bool(r['micro']))}")
    if sum(Decimal(str(r['parti'])) for r in rows)!=100:
        raise ValueError('Totale diverso da 100')
    body='TRZ1.'+hashlib.sha256(catalog_bytes()).hexdigest()[:16]+'.'+'-'.join(entries)
    return body+'.'+hashlib.sha256(body.encode()).hexdigest()[:12]

def decode(code):
    version,revision,payload,checksum=code.strip().split('.')
    body='.'.join([version,revision,payload])
    if version!='TRZ1' or hashlib.sha256(body.encode()).hexdigest()[:12]!=checksum:
        raise ValueError('Codice non valido')
    # The current catalogue is already bundled with the Python compositor.
    # Use it only when its exact revision matches; historical codes still
    # require their immutable snapshot, never a newer catalogue by default.
    raw=catalog_bytes()
    if hashlib.sha256(raw).hexdigest()[:16]!=revision:
        raw=(ROOT/'public/formule'/f'organo-{revision}.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()[:16]!=revision:raise ValueError('Catalogo alterato')
    materials={m['n']:m for m in json.loads(raw)['materie']}
    rows=[]
    for entry in payload.split('-'):
        n,q,level,micro=entry.split(':');n=int(n);q=int(q)
        if q<=0 or level not in LEVELS.values() or micro not in ('0','1'):raise ValueError('Dose non valida')
        rows.append({'n':n,'nome':materials[n]['nome'],'parti':q/10,'livello':next(k for k,v in LEVELS.items() if v==level),'micro':micro=='1'})
    if sum(Decimal(str(r['parti'])) for r in rows)!=100:raise ValueError('Totale non valido')
    return rows
