"""Notifiche Telegram per SDQ-1 — canale diretto con Claudio.

Nessuna dipendenza esterna — usa urllib.request (stdlib).

Configurazione (.env o variabili d'ambiente):
    TELEGRAM_BOT_TOKEN=<token da @BotFather>
    TELEGRAM_CHAT_ID=<chat_id personale>

CLI:
    python -m sdq1 --notifica-test          # messaggio di prova
    python -m sdq1 --notifica-briefing      # briefing completo del mattino
    python -m sdq1 --telegram-comandi       # legge ed esegue comandi ricevuti

Comandi Telegram (scrivi al bot):
    /scan     → scansione sicurezza + qualità
    /status   → stato rapido sistema
    /agenti   → ciclo 7 agenti
    /push     → snapshot + push GitHub

Uso programmatico:
    from sdq1.notifiche import invia, notifica_progresso, notifica_completato
    from sdq1.notifiche import briefing_mattutino, alert_guardian
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
_OFFSET_FILE = Path("output/telegram_offset.json")


# ══════════════════════════════════════════════════════════════════
# UTILITÀ BASE
# ══════════════════════════════════════════════════════════════════

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


def _telegram_disponibile() -> bool:
    return bool(os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"))


def _emoji_livello(livello: str) -> str:
    return {"VERDE": "🟢", "GIALLO": "🟡", "ARANCIONE": "🟠", "ROSSO": "🔴"}.get(livello, "⚪")


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


# ══════════════════════════════════════════════════════════════════
# NOTIFICHE LIVE
# ══════════════════════════════════════════════════════════════════

def notifica_progresso(titolo: str, corpo: str = "", *, emoji: str = "🔧") -> bool:
    """Aggiornamento live durante un task."""
    ora = datetime.now(_TZ).strftime("%H:%M:%S")
    testo = f"{emoji} <b>{titolo}</b>  <i>[{ora}]</i>"
    if corpo:
        testo += f"\n{corpo}"
    return invia(testo)


def notifica_completato(titolo: str, risultati: list[str]) -> bool:
    """Notifica di completamento con lista risultati."""
    ora = datetime.now(_TZ).strftime("%H:%M:%S")
    righe = [f"✅ <b>{titolo}</b>  <i>[{ora}]</i>"]
    righe += [f"  {r}" for r in risultati]
    return invia("\n".join(righe))


def alert_guardian(livello: str, motivazione: str = "", dettagli: list[str] | None = None) -> bool:
    """Alert immediato quando il Guardian rileva un problema."""
    if not _telegram_disponibile():
        return False
    emoji = {"ARANCIONE": "🟠", "ROSSO": "🔴"}.get(livello, "⚠️")
    ora = datetime.now(_TZ).strftime("%H:%M:%S")
    righe = [f"{emoji} <b>GUARDIAN ALERT: {livello}</b>  <i>[{ora}]</i>"]
    if motivazione:
        righe.append(f"  {motivazione}")
    if dettagli:
        righe += [f"  • {d}" for d in dettagli[:5]]
    righe.append("\n<i>Controlla il sistema.</i>")
    return invia("\n".join(righe))


# ══════════════════════════════════════════════════════════════════
# BRIEFING MATTUTINO
# ══════════════════════════════════════════════════════════════════

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

    # ── AGENTI
    try:
        from sdq1.sar.agenti_autonomi import SistemaAgenti
        sistema = SistemaAgenti()
        sistema.attivazione()
        report = sistema.ciclo_valutazione()
        sq = report.get("scacchiera", {})
        scanner_data = report.get("scanner", {})

        righe.append("\n<b>🤖 Agenti</b>")
        grd_ag = report.get("agenti", {}).get("guardian", {}).get("livello_allerta", "?")
        righe.append(f"  Guardian: {_emoji_livello(grd_ag)} {grd_ag}")
        righe.append(f"  Scacchiera: {sq.get('score_medio', '?'):.2f}  dir: {sq.get('direzione_dominante', '?')}")
        if scanner_data.get("score_sistema"):
            righe.append(f"  Codebase: {scanner_data['score_sistema']}/100")
    except Exception:
        pass

    # ── DESIDERI
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
    righe.append("<i>Scrivi /scan /status /agenti /push per comandare il sistema</i>")
    return invia("\n".join(righe))


# ══════════════════════════════════════════════════════════════════
# COMANDI IN ENTRATA
# ══════════════════════════════════════════════════════════════════

def leggi_comandi() -> list[dict[str, Any]]:
    """Legge nuovi comandi Telegram dall'ultima lettura (stateful via offset file)."""
    last_id = 0
    if _OFFSET_FILE.exists():
        try:
            last_id = int(json.loads(_OFFSET_FILE.read_text()))
        except Exception:
            pass

    try:
        url = _API.format(token=_token(), method="getUpdates")
        params = urllib.parse.urlencode({"offset": last_id + 1, "timeout": 0, "limit": 20})
        with urllib.request.urlopen(f"{url}?{params}", timeout=10) as resp:
            data = json.loads(resp.read())
    except Exception:
        return []

    updates = data.get("result", [])
    if not updates:
        return []

    # Salva nuovo offset
    _OFFSET_FILE.parent.mkdir(parents=True, exist_ok=True)
    _OFFSET_FILE.write_text(json.dumps(updates[-1]["update_id"]))

    comandi = []
    for upd in updates:
        msg = upd.get("message", {})
        testo = msg.get("text", "").strip()
        if testo.startswith("/"):
            parti = testo.split()
            comandi.append({
                "comando":   parti[0].lower().lstrip("/"),
                "args":      parti[1:],
                "username":  msg.get("from", {}).get("username", ""),
                "update_id": upd["update_id"],
            })
    return comandi


def esegui_comandi() -> int:
    """Legge ed esegue tutti i comandi Telegram in coda. Restituisce numero eseguiti."""
    comandi = leggi_comandi()
    if not comandi:
        print("[TELEGRAM] Nessun comando in coda.")
        return 0

    for cmd in comandi:
        nome = cmd["comando"]
        print(f"[TELEGRAM] Comando: /{nome}")

        if nome == "scan":
            notifica_progresso("Scan in corso...", emoji="🔍")
            try:
                from sdq1.sar.code_scanner import CodeScanner
                sc = CodeScanner()
                sic = sc.scansione_sicurezza()
                qual = sc.analisi_qualita()
                score = round(sic["score"] * 0.6 + qual["score_salute"] * 0.4)
                invia(
                    f"🔍 <b>Scan completato</b>\n"
                    f"  Score: <b>{score}/100</b>\n"
                    f"  Sicurezza: {sic['score']}/100 {'✅' if sic['ok'] else '🔴'}\n"
                    f"  Qualità: {qual['score_salute']}/100 | debito: {qual['score_debito']}pt\n"
                    f"  File: {qual['file_py_analizzati']} | Pattern: {sic['pattern_scansionati']}"
                )
            except Exception as e:
                invia(f"❌ Scan fallito: {e}")

        elif nome == "status":
            try:
                from sdq1.snapshot import crea_snapshot
                snap = crea_snapshot()
                g = snap["git"]
                c = snap["codice"]
                a = snap["agenti"]
                sc = snap.get("scanner", {})
                grd = _emoji_livello(a.get("guardian_allerta", "?")) if a.get("ok") else "?"
                invia(
                    f"📊 <b>Status SDQ-1</b>\n"
                    f"  Commit: <code>{g['commit_short']}</code> | Git: {'✓' if not g['dirty'] else '⚠'}\n"
                    f"  Codice: {c['file_presenti']}/{len(c['file'])} integri\n"
                    f"  Guardian: {grd} {a.get('guardian_allerta', '?')}\n"
                    f"  Scacchiera: {a.get('scacchiera_score', '?')}\n"
                    f"  Scanner: {sc.get('score_sistema', '?')}/100"
                )
            except Exception as e:
                invia(f"❌ Status fallito: {e}")

        elif nome == "agenti":
            notifica_progresso("Ciclo 7 agenti in corso...", emoji="🤖")
            try:
                from sdq1.sar.agenti_autonomi import SistemaAgenti
                sistema = SistemaAgenti()
                sistema.attivazione()
                report = sistema.ciclo_valutazione()
                sq = report.get("scacchiera", {})
                grd = report.get("agenti", {}).get("guardian", {}).get("livello_allerta", "?")
                notifica_completato("Agenti completati", [
                    f"Guardian: {_emoji_livello(grd)} {grd}",
                    f"Scacchiera: {sq.get('score_medio', '?'):.2f}  dir: {sq.get('direzione_dominante', '?')}",
                    f"Codebase: {report.get('scanner', {}).get('score_sistema', '?')}/100",
                ])
            except Exception as e:
                invia(f"❌ Agenti falliti: {e}")

        elif nome == "push":
            notifica_progresso("Snapshot + push in corso...", emoji="☁️")
            try:
                from sdq1.snapshot import crea_snapshot, salva_snapshot, push_snapshot
                snap = crea_snapshot()
                dest = salva_snapshot(snap)
                ok = push_snapshot(dest)
                sc = snap.get("scanner", {})
                notifica_completato("Push completato" if ok else "Push fallito", [
                    f"Snapshot: {dest.name}",
                    f"GitHub: {'✅ OK' if ok else '❌ FALLITO'}",
                    f"Scanner: {sc.get('score_sistema', '?')}/100",
                ])
            except Exception as e:
                invia(f"❌ Push fallito: {e}")

        else:
            invia(
                f"❓ Comando <code>/{nome}</code> non riconosciuto.\n"
                f"Comandi disponibili: /scan /status /agenti /push"
            )

    return len(comandi)


def test_connessione() -> bool:
    """Invia un messaggio di test e verifica la connessione."""
    ora = datetime.now(_TZ).strftime("%H:%M:%S")
    return invia(
        f"<b>✅ SDQ-1 — Connessione verificata</b>\n"
        f"Ora: {ora}\n"
        f"Sistema operativo e pronto.\n"
        f"Comandi: /scan /status /agenti /push"
    )
