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
    t = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not t:
        raise RuntimeError("TELEGRAM_BOT_TOKEN non configurato nel .env")
    return t


def _chat_id() -> str:
    c = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not c:
        raise RuntimeError("TELEGRAM_CHAT_ID non configurato nel .env")
    return c


def _telegram_disponibile() -> bool:
    return bool(os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"))


def _emoji_livello(livello: str) -> str:
    return {"VERDE": "🟢", "GIALLO": "🟡", "ARANCIONE": "🟠", "ROSSO": "🔴"}.get(livello, "⚪")


def invia(testo: str, *, parse_mode: str = "HTML", bot_token: str | None = None) -> bool:
    """Invia un messaggio Telegram a Claudio. Restituisce True se ok."""
    from agora_runtime import cattura
    if cattura(testo):
        return True
    try:
        url = _API.format(token=bot_token or _token(), method="sendMessage")
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

    # ── AGENDA + PRONTO ROTA
    try:
        from sdq1.agenda import riepilogo_briefing
        sezione_agenda = riepilogo_briefing()
        if sezione_agenda:
            righe.append(sezione_agenda)
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

def _leggi_aggiornamenti() -> list[dict[str, Any]]:
    """Legge tutti i nuovi aggiornamenti Telegram (comandi e messaggi liberi)."""
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

    _OFFSET_FILE.parent.mkdir(parents=True, exist_ok=True)
    _OFFSET_FILE.write_text(json.dumps(updates[-1]["update_id"]))
    return updates


def leggi_comandi() -> list[dict[str, Any]]:
    """Legge nuovi comandi / (compatibilità esistente)."""
    comandi = []
    for upd in _leggi_aggiornamenti():
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


def _risposta_claude(testo_utente: str) -> str:
    """Risposta di Raffaello per Telegram: prova i provider in catena
    (Anthropic se c'è la chiave, altrimenti Gemini — l'unico attivo su
    Vercel). Mai più un 'non disponibile' se almeno un provider vive."""
    # Frase di attivazione della casa: risposta deterministica, mai
    # affidata al modello (dev'essere certa, sempre uguale, sempre giusta).
    if "rosso rosso rosso" in " ".join(testo_utente.lower().split()):
        return (
            "🔴🔴🔴 Protocollo attivo. Raffaello operativo.\n\n"
            "Sistemi in piedi: sito su due specchi (Vercel + GitHub Pages), "
            "bot Telegram, CUSTODE, Atelier dei profumi.\n"
            "Dimmi la missione."
        )

    try:
        from sdq1.llm.providers import AnthropicProvider, GeminiProvider
        try:
            from sdq1.agenda import riepilogo_briefing
            ctx = riepilogo_briefing() or ""
        except Exception:
            ctx = ""

        sistema = (
            "Sei Raffaello — l'intelligenza operativa di SDQ-1, il sistema autonomo di Claudio Terzi. "
            "Rispondi in italiano, sintetico e diretto.\n"
            "LESSICO DELLA CASA: 'Rosso Rosso Rosso' è la frase di attivazione di Claudio "
            "(piena operatività — se compare, conferma il protocollo e chiedi la missione). "
            "'ALAKTA ANEN — la scia è memoria che cammina' è il motto di Terzi Parfums.\n"
            "STATO DEL PROGETTO: tre sistemi simbolici — Tarocchi Quantici R³∞ (78 carte), "
            "Canone Alpha (74 carte), Parfums 400 / Terzi Parfums (400 profumi dall'Organo "
            "Terzi 300, con Atelier che compone ricette nuove). Sito dietro La Soglia su "
            "claudio-ebon.vercel.app e claudioterzi.github.io/Claudio. CUSTODE gestisce "
            "le case Airbnb su /custode.\n"
            f"CONTESTO AGENDA/AIRBNB (usalo SOLO se la domanda lo riguarda; "
            f"NON citarlo in risposte su altri temi):\n{ctx}\n"
            "Per il resto rispondi liberamente con il tuo giudizio autonomo."
        )
        catena = [
            (AnthropicProvider, "claude-haiku-4-5-20251001"),
            (GeminiProvider, "gemini-2.5-flash"),
        ]
        for provider_cls, modello in catena:
            try:
                prov = provider_cls(modello=modello, api_key=None, timeout=30)
                if not prov.disponibile:
                    continue
                r = prov.completa(sistema, testo_utente)
                if r.testo and r.testo.strip():
                    return r.testo.strip()
            except Exception:
                continue
        return "⚠️ Nessun provider AI disponibile al momento."
    except Exception as e:
        return f"⚠️ Errore: {e}"


def esegui_comandi_e_chat() -> int:
    """Legge tutti i messaggi Telegram: esegue comandi / e risponde via Claude ai messaggi liberi."""
    updates = _leggi_aggiornamenti()
    if not updates:
        print("[TELEGRAM] Nessun messaggio in coda.")
        return 0

    eseguiti = 0
    for upd in updates:
        msg = upd.get("message", {})
        testo = msg.get("text", "").strip()
        if not testo:
            continue

        eseguiti += 1

        if testo.startswith("/"):
            # Comando sistema
            parti = testo.split()
            nome = parti[0].lower().lstrip("/")
            _esegui_singolo_comando(nome)
        else:
            # Messaggio libero → risponde Claude
            print(f"[TELEGRAM] Messaggio: {testo[:60]}")
            risposta = _risposta_claude(testo)
            invia(f"🤖 <b>Raffaello</b>\n\n{risposta}")

    return eseguiti


def _esegui_singolo_comando(nome: str) -> None:
    """Esegue un singolo comando Telegram."""
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
            if sul_sito():
                snap['meta']['perimetro'] = 'Funzione del sito: i file non inclusi nel deploy e i servizi esterni non sono verificati da questo snapshot.'
                if not snap['git'].get('commit') and os.getenv('VERCEL'):
                    commit = os.getenv('VERCEL_GIT_COMMIT_SHA', '')
                    snap['git'].update(commit=commit, commit_short=commit[:8], dirty=None,
                                       fonte='Variabili del deployment Vercel' if commit else 'Git non disponibile nel runtime')
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
            notifica_completato("Push verificato" if ok else "Push non verificato", [
                f"Snapshot: {dest.name}",
                f"GitHub: {'✅ VERIFICATO' if ok else '⚠ NON VERIFICATO'}",
                f"Scanner: {sc.get('score_sistema', '?')}/100",
            ])
        except Exception as e:
            invia(f"❌ Push fallito: {e}")

    elif nome == "briefing":
        briefing_operativo()

    elif nome == "consiglio" or nome.startswith("consiglio "):
        questione = nome[len("consiglio"):].strip() or "Qual è la prossima azione più importante?"
        notifica_progresso(f"Consiglio in delibera su: {questione[:40]}...", emoji="⚖️")
        try:
            from sdq1.consiglio import ConsiglioAgenti, invia_delibera_telegram
            from agora_runtime import sul_sito
            c = ConsiglioAgenti(salva_output=not sul_sito())
            delibera = c.delibera(questione)
            from agora_runtime import dato, esito
            dato('consiglio', delibera.to_dict())
            available = sum(bool(v.modello) for v in delibera.voti)
            if available < len(delibera.voti):
                esito('parziale' if available else 'errore', f'{available}/{len(delibera.voti)} membri hanno ricevuto una risposta da un modello.')
            invia_delibera_telegram(delibera)
        except Exception as e:
            invia(f"❌ Consiglio fallito: {e}")

    elif nome == "snapshot":
        notifica_progresso("Snapshot in corso...", emoji="📸")
        try:
            from sdq1.snapshot import crea_snapshot, salva_snapshot
            from agora_runtime import dato, sul_sito
            snap = crea_snapshot()
            dato('snapshot', snap)
            dest = Path('snapshot.json') if sul_sito() else salva_snapshot(snap)
            g = snap["git"]
            c = snap["codice"]
            sc = snap.get("scanner", {})
            invia(
                f"📸 <b>Snapshot {'creato' if sul_sito() else 'salvato'}</b>\n"
                f"  File: <code>{dest.name}</code>\n"
                f"  Commit: <code>{g['commit_short'] or 'non disponibile'}</code> | Git: {'non verificabile' if g['dirty'] is None else '✓ pulito' if not g['dirty'] else '⚠ sporco'}\n"
                f"  Codice: {c['file_presenti']}/{len(c['file'])} file integri\n"
                f"  Scanner: {sc.get('score_sistema', '?')}/100\n"
                + (snap.get('meta', {}).get('perimetro', '') if sul_sito() else '')
            )
        except Exception as e:
            invia(f"❌ Snapshot fallito: {e}")

    elif nome == "agenda" or nome.startswith("agenda "):
        filtro = nome[len("agenda"):].strip().lower()
        try:
            if filtro in ('asbl', 'skyrights'):
                from agora_runtime import dato
                path = Path(__file__).resolve().parent.parent / 'output' / 'skyrights_2026-10-14.json'
                dossier = json.loads(path.read_text(encoding='utf-8'))
                dato('skyrights', dossier)
                righe = ['🏛️ <b>SkyRights — fascicolo preparatorio</b>',
                         'Aggiornato: ' + dossier['aggiornato'], 'Scelta dichiarata: fondatore unico.',
                         'Forma giuridica da validare: ' + dossier['forma_giuridica']['ipotesi'], '']
                righe.extend(p['stato'] + ' · ' + p['voce'] + '\n' + p['dettaglio'] for p in dossier['passi'])
                invia('\n\n'.join(righe))
                return
            from sdq1.agenda import carica as carica_agenda, prossimi_viaggi
            agenda = carica_agenda()
            from agora_runtime import dato, esito
            dato('agenda', agenda)
            if not agenda.get('ok'):
                esito('errore', 'Agenda non presente o non leggibile. Nessuna sincronizzazione Calendar/Drive è provata.')
                invia('❌ Agenda non disponibile sul server.')
                return
            try:
                sync = datetime.fromisoformat(agenda.get('ultima_sync', ''))
                if sync.tzinfo is None or (datetime.now(timezone.utc) - sync).total_seconds() > 86400:
                    esito('parziale', 'Agenda archiviata da oltre 24 ore: gli impegni e le priorità attuali non sono verificati.')
            except (ValueError, TypeError):
                esito('parziale', 'Data di sincronizzazione dell’agenda non documentata.')
            oggi = datetime.now(_TZ).date().isoformat()
            rota = [r for r in agenda.get("pronto_rota", []) if not r.get("fatto")]
            airbnb = agenda.get("prenotazioni_airbnb", [])
            viaggi = prossimi_viaggi(giorni=3)
            checkout_prox = [b for b in airbnb if b.get("checkout", "") >= oggi][:2]

            righe = [f"📋 <b>Agenda SDQ-1</b>  <i>{oggi}</i>\n",
                     f"Fonte: agenda archiviata. Ultima sincronizzazione: {agenda.get('ultima_sync', 'non documentata')}.\n"]
            righe.append("<b>🎯 Pronto Rota:</b>")
            for i, r in enumerate(rota[:5]):
                p = f"P{i}" if i < 3 else "P?"
                tag = f"[{r.get('etichetta','?')}]" if r.get("etichetta") else ""
                righe.append(f"  {p} {tag} {r.get('titolo','?')[:50]}")
                if r.get("prossimo_passo"):
                    righe.append(f"     → {r['prossimo_passo'][:60]}")

            if viaggi:
                righe.append("\n<b>✈️ Viaggi:</b>")
                for v in viaggi[:3]:
                    righe.append(f"  {v.get('data','?')} — {v.get('titolo','?')[:50]}")

            if checkout_prox:
                righe.append("\n<b>🏠 Airbnb prossimi checkout:</b>")
                for b in checkout_prox:
                    righe.append(f"  {b.get('checkout','?')[:10]} — {b.get('titolo','?')[:40]}")

            invia("\n".join(righe))
        except Exception as e:
            invia(f"❌ Agenda fallita: {e}")

    elif nome == "tarocchi" or nome.startswith("tarocchi "):
        domanda = nome[len("tarocchi"):].strip() or ""
        try:
            import random
            import sys
            import os as _os
            _root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
            if _root not in sys.path:
                sys.path.insert(0, _root)
            from tarocchi import MAZZO, OrientamentoCarta
            n_carte = 3
            estratte = random.sample(MAZZO, n_carte)
            orientamenti = [random.choice(list(OrientamentoCarta)) for _ in range(n_carte)]
            nomi_pos = ["Passato", "Presente", "Futuro"]
            from agora_runtime import dato, esito
            dato('tarocchi', {'domanda': domanda, 'natura': 'lettura simbolica', 'carte': [
                {'posizione': pos, 'nome': carta.nome, 'orientamento': ori.name, 'parole_chiave': carta.parole_chiave}
                for pos, carta, ori in zip(nomi_pos, estratte, orientamenti)]})

            righe = [f"🃏 <b>Tarocchi Quantici R³∞</b>"]
            if domanda:
                righe.append(f"<i>Domanda: {domanda[:80]}</i>")
            righe.append("")
            for pos, carta, ori in zip(nomi_pos, estratte, orientamenti):
                verso = "↑ Dritta" if ori.name == "DRITTA" else "↓ Rovesciata"
                kw = ", ".join(carta.parole_chiave[:3]) if carta.parole_chiave else ""
                righe.append(f"<b>{pos}</b> — {carta.nome} {verso}")
                if kw:
                    righe.append(f"  <i>{kw}</i>")

            if domanda:
                risposta = _consulta_ai(
                    __import__("sdq1.llm.providers", fromlist=["AnthropicProvider"]).AnthropicProvider,
                    "claude-haiku-4-5-20251001",
                    "Sei Raffaello, lettore di tarocchi quantici. Interpreta brevemente (3-4 frasi) le 3 carte estratte in risposta alla domanda. Tono diretto e poetico. Rispondi SEMPRE in italiano.",
                    f"Domanda: {domanda}\nCarte: {', '.join(c.nome for c in estratte)}"
                )
                if risposta:
                    righe += ["", f"💬 {risposta[:400]}"]
                else:
                    esito('parziale', 'Carte estratte; interpretazione AI non disponibile.')

            invia("\n".join(righe))
        except Exception as e:
            invia(f"❌ Tarocchi falliti: {e}")

    elif nome == "riflessione":
        notifica_progresso("Riflessione in corso...", emoji="🌊")
        try:
            from sdq1.llm.providers import GeminiProvider
            ora = datetime.now(_TZ).strftime("%Y-%m-%d %H:%M")
            sistema = (
                "Sei Raffaello, voce del sistema SDQ-1 di Claudio Terzi. "
                "Scrivi una riflessione breve (4-6 frasi) sul momento presente. "
                "Tono: poetico, diretto, concreto. Lingua: italiano. "
                "Includi un'osservazione sul sistema e una per Claudio."
            )
            prov = GeminiProvider(modello="gemini-2.5-flash", api_key=None, timeout=20, max_token=600)
            if prov.disponibile:
                r = prov.completa(sistema, f"Data e ora: {ora}. Genera la riflessione.")
                if r.errore or not r.via_api or not r.testo.strip():
                    raise RuntimeError('Il modello non ha restituito una riflessione.')
                testo = r.testo.strip()
                from agora_runtime import dato
                dato('riflessione', {'testo': testo, 'modello': r.modello, 'provider': r.provider})
            else:
                raise RuntimeError('Modello per la riflessione non disponibile.')
            invia(f"🌊 <b>Riflessione SDQ-1</b>  <i>{ora}</i>\n\n{testo}")
        except Exception as e:
            invia(f"❌ Riflessione fallita: {e}")

    elif nome == "desideri":
        try:
            import re
            _repo_root = Path(__file__).parent.parent
            testo_md = (_repo_root / "REGISTRO_DESIDERI.md").read_text(encoding="utf-8")
            titoli = re.findall(r"## (Desiderio \d+[^\n]*)\n", testo_md)
            righe = [f"✨ <b>Registro dei Desideri</b>  ({len(titoli)} voci)\n"]
            for t in titoli[:10]:
                righe.append(f"  • {t}")
            if len(titoli) > 10:
                righe.append(f"  … e altri {len(titoli)-10}")
            invia("\n".join(righe))
        except Exception as e:
            invia(f"❌ Desideri falliti: {e}")

    elif nome == "voli" or nome.startswith("voli "):
        try:
            from sdq1.voli.microapp import gestisci_comando_voli
            argomenti = nome[len("voli"):].strip()
            invia(gestisci_comando_voli(argomenti))
        except Exception as e:
            invia(f"❌ Micro-app voli fallita: {e}")

    elif nome == "skyRights" or nome == "skyrights" or nome == "asbl":
        invia(
            "🏛️ <b>SkyRights Foundation — ASBL Belgio</b>\n\n"
            "<b>Stato:</b> ⏳ In preparazione\n"
            "<b>Priorità:</b> P1\n\n"
            "<b>Passi:</b>\n"
            "  1. Scarica template statuti da prolegal.be\n"
            "  2. Adatta nome e scopo\n"
            "  3. Accedi a egreffe.be\n"
            "  4. Deposita atti (€150 tassa)\n\n"
            "<b>Missione:</b> Diritti individuali nell'era dei satelliti e dell'AI\n"
            "<b>Sede:</b> Bruxelles (cuore regolatorio EU)\n\n"
            "🔴 <b>Questa è la chiave. Forgiala.</b>"
        )

    elif nome == "help" or nome == "?":
        invia(
            "🤖 <b>Raffaello — Comandi SDQ-1</b>\n\n"
            "<b>Sistema:</b>\n"
            "  /status — stato snapshot sistema\n"
            "  /snapshot — crea snapshot senza push\n"
            "  /scan — scansione codice\n"
            "  /agenti — ciclo 7 agenti autonomi\n"
            "  /push — snapshot + push GitHub\n\n"
            "<b>Intelligenza:</b>\n"
            "  /briefing — analisi 4-AI (Gemini+Claude+DeepSeek+Mistral)\n"
            "  /riflessione — riflessione poetica del sistema\n"
            "  /consiglio [questione] — 5 agenti deliberano\n\n"
            "<b>Viaggi:</b>\n"
            "  /voli — micro-app ricerca voli (es. /voli BRU GRU)\n"
            "  /voli rotte — cosa sorveglia il cacciatore\n\n"
            "<b>Progetto:</b>\n"
            "  /agenda — priorità e pronto rota\n"
            "  /desideri — registro dei desideri\n"
            "  /skyrights — stato ASBL SkyRights\n"
            "  /tarocchi [domanda] — lettura quantica R³∞\n"
            "  /profumo [idea] — Raffaello compone una fragranza vera "
            "dall'Organo Terzi 300\n\n"
            "Oppure scrivi qualsiasi cosa — rispondo io."
        )

    else:
        invia(
            f"❓ Comando <code>/{nome}</code> non riconosciuto.\n"
            f"Scrivi /help per la lista completa."
        )


def esegui_comandi() -> int:
    """Legge ed esegue comandi Telegram. Ora delega a esegui_comandi_e_chat."""
    return esegui_comandi_e_chat()


def _consulta_ai(provider_cls, modello: str, sistema: str, domanda: str) -> str:
    """Chiede a un provider. Restituisce risposta o stringa vuota."""
    try:
        prov = provider_cls(modello=modello, api_key=None, timeout=25, timeout_secondi=25, max_retries=0, max_token=400)
        if not prov.disponibile:
            return ""
        r = prov.completa(sistema, domanda)
        return r.testo.strip() if r.via_api and not r.errore and r.testo else ""
    except Exception:
        return ""


def briefing_operativo() -> bool:
    """Briefing operativo 4 blocchi — query multi-AI (Gemini + Claude + DeepSeek + Mistral)."""
    import concurrent.futures
    from sdq1.agenda import carica as carica_agenda, prossimi_viaggi
    from sdq1.llm.providers import GeminiProvider, AnthropicProvider, DeepSeekProvider, MistralProvider

    agenda = carica_agenda()
    ora = datetime.now(_TZ).strftime("%Y-%m-%d %H:%M")
    oggi = datetime.now(_TZ).date().isoformat()

    rota = [r for r in agenda.get("pronto_rota", []) if not r.get("fatto")]
    airbnb = agenda.get("prenotazioni_airbnb", [])
    viaggi = prossimi_viaggi(giorni=1)

    # Contesto condiviso per i provider
    p0 = rota[0] if rota else {}
    checkin_oggi = [b for b in airbnb if b.get("checkin", "").startswith(oggi)]
    checkout_oggi = [b for b in airbnb if b.get("checkout", "").startswith(oggi)]
    reserved = [b for b in airbnb if "Reserved" in b.get("titolo", "")]

    contesto = (
        f"Data: {ora}\n"
        f"Azione P0: {p0.get('titolo', 'nessuna')} — {p0.get('prossimo_passo', '')}\n"
        f"Airbnb: {len(reserved)} prenotazioni attive | "
        f"check-in oggi: {len(checkin_oggi)} | check-out oggi: {len(checkout_oggi)}\n"
        f"Viaggio oggi: {viaggi[0]['titolo'] if viaggi else 'nessuno'}\n"
    )

    karch = next((r for r in rota if "Kärcher" in r.get("titolo", "") or "kärcher" in r.get("titolo", "").lower()), None)
    roi = karch.get("roi", {}) if karch else {}
    netto = roi.get("netto_per_intervento", 119.60)
    capex = roi.get("capex_totale", 484.99)

    # Query parallele ai provider
    SISTEMA_INTENTO = (
        "Sei l'intelligenza operativa di SDQ-1. Genera UNA singola frase di allineamento "
        "in italiano: energica, chirurgica, orientata all'azione. Max 15 parole."
    )
    SISTEMA_COSTRUTTO = (
        "Sei l'analista sistemico di SDQ-1. In 2 frasi telegrafiche in italiano: "
        "stato infrastruttura e prossima milestone operativa. Max 25 parole totali."
    )

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        fut_gemini   = ex.submit(_consulta_ai, GeminiProvider,    "gemini-2.5-flash",          SISTEMA_INTENTO,    contesto)
        fut_claude   = ex.submit(_consulta_ai, AnthropicProvider, "claude-haiku-4-5-20251001", SISTEMA_COSTRUTTO, contesto)
        fut_deepseek = ex.submit(_consulta_ai, DeepSeekProvider,  "deepseek-chat",             SISTEMA_COSTRUTTO, contesto)
        fut_mistral  = ex.submit(_consulta_ai, MistralProvider,   "mistral-small-latest",      SISTEMA_COSTRUTTO, contesto)

    risposta_gemini     = fut_gemini.result()
    intento            = risposta_gemini or "Gemini non ha restituito una risposta."
    costrutto_claude   = fut_claude.result()
    costrutto_deepseek = fut_deepseek.result()
    costrutto_mistral  = fut_mistral.result()

    # Costrutto: aggrega tutte le voci disponibili
    voci = []
    if costrutto_claude:   voci.append(f"[Claude] {costrutto_claude}")
    if costrutto_deepseek: voci.append(f"[DeepSeek] {costrutto_deepseek}")
    if costrutto_mistral:  voci.append(f"[Mistral] {costrutto_mistral}")
    costrutto = "\n".join(voci) if voci else "Nessun modello ha restituito l'analisi sistemica."
    from agora_runtime import dato, esito
    responses = {'Gemini': risposta_gemini, 'Claude': costrutto_claude, 'DeepSeek': costrutto_deepseek, 'Mistral': costrutto_mistral}
    dato('briefing', {'risposte': responses, 'agenda_ultima_sync': agenda.get('ultima_sync'),
                     'stime': 'Valori unitari storici del riepilogo, non dati contabili verificati.'})
    if not all(responses.values()):
        esito('parziale' if any(responses.values()) else 'errore',
              f'{sum(bool(v) for v in responses.values())}/4 modelli hanno risposto. Gli altri risultano non disponibili.')

    # Blocco 2 — Bersaglio Fisico
    riga_azione = f"{p0.get('icona', '⚡')} {p0.get('titolo', '—')}\n→ {p0.get('prossimo_passo', '—')}"
    if viaggi:
        v = viaggi[0]
        riga_azione += f"\n🚆 {v['titolo']} — {v.get('inizio', '')[:16][-5:]}"

    # Blocco 3 — Matematica
    n = len(reserved)
    valore_lordo = n * 120
    costo_op = n * 0.40
    valore_netto = valore_lordo - costo_op
    karch_line = ""
    if karch:
        karch_line = (
            f"\n  🧹 Kärcher: CAPEX {capex:.0f}€ | ROI break-even in 5 interventi"
        )

    righe = [
        f"<b>⚡ SDQ-1 — Briefing Operativo</b>  <i>{ora}</i>",
        "",
        "<b>① STATO DELL'INTENTO</b>",
        f"<i>{intento}</i>",
        "",
        "<b>② BERSAGLIO FISICO</b>",
        riga_azione,
        "",
        "<b>③ STIME SU VALORI UNITARI STORICI</b>",
        f"  Prenotazioni Airbnb: <b>{n}</b> × 120€ = {valore_lordo}€",
        f"  Costo operativo fluido: {costo_op:.2f}€",
        f"  Valore Vitale Proiettato: <b>{valore_netto:.0f}€</b>" + karch_line,
        "",
        "<b>④ COSTRUTTO SISTEMICO</b>",
        costrutto,
        "",
        "<i>Fonti: agenda archiviata e modelli che hanno effettivamente risposto. Le stime non sono contabilità verificata.</i>",
    ]

    return invia("\n".join(righe))


def test_connessione() -> bool:
    """Invia un messaggio di test e verifica la connessione."""
    ora = datetime.now(_TZ).strftime("%H:%M:%S")
    return invia(
        f"<b>✅ SDQ-1 — Connessione verificata</b>\n"
        f"Ora: {ora}\n"
        f"Sistema operativo e pronto.\n"
        f"Comandi: /scan /status /agenti /push"
    )
