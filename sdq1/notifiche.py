"""Notifiche Telegram per SDQ-1 — canale diretto con Claudio.

Nessuna dipendenza esterna — usa urllib.request (stdlib).

Configurazione (.env o variabili d'ambiente):
    TELEGRAM_BOT_TOKEN=<token da @BotFather>
    TELEGRAM_CHAT_ID=<chat_id personale>

CLI:
    python -m sdq1 --notifica-test          # messaggio di prova
    python -m sdq1 --notifica-briefing      # briefing completo del mattino

Uso programmatico:
    from sdq1.notifiche import invia, briefing_mattutino
    invia("Testo")
    briefing_mattutino()
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

_TZ = timezone(timedelta(hours=2))
_API = "https://api.telegram.org/bot{token}/{method}"


def _token() -> str:
    t = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not t:
        raise RuntimeError("TELEGRAM_BOT_TOKEN non configurato nel .env")
    return t


def _chat_id() -> str:
    c = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not c:
        raise RuntimeError("TELEGRAM_CHAT_ID non configurato nel .env")
    return c


def invia(testo: str, *, parse_mode: str = "HTML") -> bool:
    """Invia un messaggio Telegram a Claudio. Restituisce True se ok."""
    try:
        url = _API.format(token=_token(), method="sendMessage")
        payload = json.dumps({
            "chat_id":    _chat_id(),
            "text":       testo,
            "parse_mode": parse_mode,
        }).encode()
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read()).get("ok", False)
    except Exception as e:
        print(f"[TELEGRAM] Errore invio: {e}")
        return False


def _emoji_livello(livello: str) -> str:
    return {"VERDE": "🟢", "GIALLO": "🟡", "ARANCIONE": "🟠", "ROSSO": "🔴"}.get(livello, "⚪")


def briefing_mattutino() -> bool:
    """Costruisce e invia il briefing completo del mattino."""
    ora = datetime.now(_TZ).strftime("%Y-%m-%d %H:%M")
    righe = [f"<b>☀️ SDQ-1 — Briefing {ora}</b>"]

    # ── SNAPSHOT
    try:
        from sdq1.snapshot import crea_snapshot
        snap = crea_snapshot()
        g = snap["git"]
        c = snap["codice"]
        a = snap["agenti"]
        sc = snap.get("scanner", {})

        righe.append("\n<b>📦 Sistema</b>")
        righe.append(f"  Branch: <code>{g['branch']}</code>  commit <code>{g['commit_short']}</code>")
        stato_git = "✓ pulito" if not g["dirty"] else f"⚠ {len(g['file_modificati'])} file modificati"
        righe.append(f"  Git: {stato_git}")
        righe.append(f"  Codice: {c['file_presenti']}/{len(c['file'])} file integri")

        if a.get("ok"):
            grd = _emoji_livello(a.get("guardian_allerta", "VERDE"))
            righe.append(f"  Guardian: {grd} {a.get('guardian_allerta', '?')}")
            righe.append(f"  Scacchiera: {a.get('scacchiera_score', '?'):.2f}")

        if sc.get("score_sistema") is not None:
            sic_ok = "✅" if sc.get("sicurezza_ok") else "🔴"
            righe.append(f"  Scanner: {sc['score_sistema']}/100  Sicurezza: {sic_ok}  Qualità: {sc.get('qualita_score', '?')}/100")
    except Exception as e:
        righe.append(f"\n⚠ Snapshot non disponibile: {e}")

    # ── AGENTI (ciclo rapido)
    try:
        from sdq1.sar.agenti_autonomi import SistemaAgenti
        sistema = SistemaAgenti()
        sistema.attivazione()
        report = sistema.ciclo_valutazione()
        scanner_data = report.get("scanner", {})
        sq = report.get("scacchiera", {})

        righe.append("\n<b>🤖 Agenti</b>")
        stati = report.get("agenti", {})
        grd_ag = stati.get("guardian", {}).get("livello_allerta", "?")
        righe.append(f"  Guardian: {_emoji_livello(grd_ag)} {grd_ag}")
        righe.append(f"  Scacchiera: {sq.get('score_medio', '?'):.2f}  dir: {sq.get('direzione_dominante', '?')}")
        if scanner_data.get("score_sistema"):
            righe.append(f"  Codebase: {scanner_data['score_sistema']}/100")
    except Exception:
        pass

    # ── DESIDERI aperti (se il file esiste)
    try:
        p = Path("output/stato_sdq1.json")
        if p.exists():
            stato = json.loads(p.read_text(encoding="utf-8"))
            n_des = stato.get("desideri_aperti", 0)
            if n_des:
                righe.append(f"\n<b>💫 Desideri aperti:</b> {n_des}")
    except Exception:
        pass

    righe.append("\n<i>— SDQ-1 autonomo | ogni mattina alle 08:00 CET</i>")
    return invia("\n".join(righe))


def test_connessione() -> bool:
    """Invia un messaggio di test e verifica la connessione."""
    ora = datetime.now(_TZ).strftime("%H:%M:%S")
    return invia(
        f"<b>✅ SDQ-1 — Connessione verificata</b>\n"
        f"Ora: {ora}\n"
        f"Sistema operativo e pronto."
    )
