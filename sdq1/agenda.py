"""
sdq1/agenda.py — Agenda personale e Pronto Rota di Claudio Terzi.

Legge da output/agenda.json (cachato dalla sessione Claude Code con accesso Drive+Calendar).
Fornisce riepilogo operativo per il briefing Telegram mattutino.

Il file output/agenda.json viene aggiornato ad ogni sessione interattiva
e letto dal workflow GitHub Actions (che non ha OAuth Calendar).

Uso:
    python -m sdq1.agenda                  # mostra pronto rota
    python -m sdq1.agenda --briefing       # formato Telegram
"""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

_TZ = timezone(timedelta(hours=2))
_AGENDA_FILE = Path("output/agenda.json")


def carica() -> dict[str, Any]:
    if not _AGENDA_FILE.exists():
        return {"ok": False, "viaggi": [], "pronto_rota": [], "note": []}
    try:
        return json.loads(_AGENDA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"ok": False, "viaggi": [], "pronto_rota": [], "note": []}


def salva(dati: dict[str, Any]) -> Path:
    _AGENDA_FILE.parent.mkdir(parents=True, exist_ok=True)
    dati["ultima_sync"] = datetime.now(_TZ).isoformat()
    dati["ok"] = True
    _AGENDA_FILE.write_text(json.dumps(dati, indent=2, ensure_ascii=False), encoding="utf-8")
    return _AGENDA_FILE


def _formatta_dt(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(_TZ)
        oggi = datetime.now(_TZ).date()
        domani = oggi + timedelta(days=1)
        if dt.date() == oggi:
            return f"OGGI {dt.strftime('%H:%M')}"
        elif dt.date() == domani:
            return f"DOMANI {dt.strftime('%H:%M')}"
        else:
            return dt.strftime("%d/%m %H:%M")
    except Exception:
        return iso[:16]


def prossimi_viaggi(giorni: int = 7) -> list[dict]:
    agenda = carica()
    ora = datetime.now(_TZ)
    limite = (ora + timedelta(days=giorni)).isoformat()
    ora_str = ora.isoformat()
    return [v for v in agenda.get("viaggi", [])
            if ora_str <= v.get("inizio", "") <= limite]


def riepilogo_briefing() -> str:
    agenda = carica()
    if not agenda.get("ok"):
        return ""

    righe: list[str] = []

    # Viaggi prossimi 48h
    viaggi = prossimi_viaggi(giorni=2)
    if viaggi:
        righe.append("\n<b>🚆 In partenza</b>")
        for v in viaggi:
            righe.append(f"  {_formatta_dt(v['inizio'])} — {v['titolo']}")
            if v.get("luogo"):
                righe.append(f"  📍 {v['luogo']}")

    # Pronto Rota — dossier prioritari
    rota = [r for r in agenda.get("pronto_rota", []) if not r.get("fatto")]
    if rota:
        righe.append("\n<b>📋 Pronto Rota</b>")
        for r in rota[:4]:
            icona = r.get("icona", "•")
            righe.append(f"  {icona} <b>{r['priorita']}</b> — {r['titolo']}")
            if r.get("prossimo_passo"):
                righe.append(f"      → {r['prossimo_passo']}")

    # Note operative
    note = agenda.get("note", [])
    if note:
        righe.append("\n<b>⚠️ Note</b>")
        for n in note[:2]:
            righe.append(f"  • {n}")

    return "\n".join(righe)


if __name__ == "__main__":
    import sys
    agenda = carica()
    if "--briefing" in sys.argv:
        print(riepilogo_briefing())
    else:
        print(f"Ultima sync: {agenda.get('ultima_sync', 'mai')}")
        print(f"Viaggi: {len(agenda.get('viaggi', []))}")
        rota = agenda.get("pronto_rota", [])
        da_fare = [r for r in rota if not r.get("fatto")]
        print(f"Pronto Rota: {len(da_fare)} item da fare\n")
        for r in da_fare:
            print(f"  [{r.get('priorita', '?')}] {r['titolo']}")
            if r.get("prossimo_passo"):
                print(f"       → {r['prossimo_passo']}")
