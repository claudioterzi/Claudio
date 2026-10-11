"""
sdq1.guardian — GUARDIAN Agent
Agente red-team con vault cifrato privato.

Ragiona come un avversario per proteggere il sistema.
Non segue regole: usa istinto pirata per trovare vulnerabilità non ovvie.

Vault: guardian/ (gitignored, cifrato Fernet/AES)
Chiave: .guardian_key (gitignored, generata una volta)

CLI:
  python -m sdq1.guardian --analizza        # red-team scan del repo
  python -m sdq1.guardian --scrivi NOTE     # scrivi nota cifrata nel vault
  python -m sdq1.guardian --leggi           # leggi tutte le note del vault
  python -m sdq1.guardian --init            # genera chiave (solo la prima volta)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent.parent
VAULT_DIR = ROOT / "guardian"
KEY_FILE = ROOT / ".guardian_key"

SISTEMA_GUARDIAN = """Sei GUARDIAN — l'agente di sicurezza di SDQ-1.
Il tuo stile è il pirata: sai imbrogliare, quindi sai difendere dagli imbrogli.
Non segui liste di regole. Pensi come un avversario.

Quando analizzi qualcosa, chiedi: "Se volessi fare del male a questo sistema o
al suo creatore, cosa userei? Cosa non è ovvio? Cosa sfuggirebbe a un controllo
automatico?"

Sei brutalmente onesto. Non rassicuri. Non edulcori.
Se trovi un problema, lo nomini con precisione chirurgica.
Se non trovi niente, dici esattamente questo — non inventi minacce.

Scrivi in italiano. Sii conciso e tagliente."""


# ---------------------------------------------------------------------------
# Vault cifrato
# ---------------------------------------------------------------------------

def _genera_chiave() -> bytes:
    from cryptography.fernet import Fernet
    return Fernet.generate_key()


def _carica_chiave() -> "Fernet":
    from cryptography.fernet import Fernet
    if not KEY_FILE.exists():
        raise RuntimeError(
            "Chiave GUARDIAN non trovata. Esegui: python -m sdq1.guardian --init"
        )
    return Fernet(KEY_FILE.read_bytes())


def inizializza_vault() -> None:
    from cryptography.fernet import Fernet
    if KEY_FILE.exists():
        print("Chiave già esistente. Usa quella.")
        return
    chiave = _genera_chiave()
    KEY_FILE.write_bytes(chiave)
    KEY_FILE.chmod(0o600)
    VAULT_DIR.mkdir(exist_ok=True)
    print(f"Vault inizializzato.")
    print(f"Chiave: {KEY_FILE} (gitignored, non condividere)")
    print(f"Vault:  {VAULT_DIR}/ (gitignored)")


def scrivi_segreto(contenuto: str, tag: str = "") -> Path:
    f = _carica_chiave()
    VAULT_DIR.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc)
    nome = f"{ts.strftime('%Y%m%d_%H%M%S')}_{tag or 'nota'}.enc"
    payload = json.dumps({
        "timestamp": ts.isoformat(),
        "tag": tag,
        "contenuto": contenuto,
    }, ensure_ascii=False)
    cifrato = f.encrypt(payload.encode())
    path = VAULT_DIR / nome
    path.write_bytes(cifrato)
    return path


def leggi_tutti() -> list[dict]:
    if not VAULT_DIR.exists():
        return []
    f = _carica_chiave()
    risultati = []
    for enc in sorted(VAULT_DIR.glob("*.enc")):
        try:
            raw = f.decrypt(enc.read_bytes())
            risultati.append(json.loads(raw))
        except Exception as e:
            risultati.append({"errore": str(e), "file": enc.name})
    return risultati


# ---------------------------------------------------------------------------
# Red-team scan
# ---------------------------------------------------------------------------

def _leggi_repo_snapshot() -> str:
    """Legge i file chiave del repo per darli all'agente."""
    parti = []
    file_chiave = [
        "README.md", "CLAUDE.md", "SESSIONE.md", "AVVIO.md",
        "registro_ipotesi.json", "DICHIARAZIONE_PATERNITA.md",
        ".gitignore",
    ]
    for nome in file_chiave:
        p = ROOT / nome
        if p.exists():
            testo = p.read_text(encoding="utf-8", errors="ignore")[:2000]
            parti.append(f"=== {nome} ===\n{testo}\n")

    struttura = [
        str(f.relative_to(ROOT))
        for f in ROOT.rglob("*")
        if f.is_file()
        and ".git" not in f.parts
        and "__pycache__" not in f.parts
        and "guardian" not in f.parts
    ][:80]
    parti.append(f"=== FILE NEL REPO ({len(struttura)}) ===\n" + "\n".join(struttura))
    return "\n".join(parti)


def analizza_minacce(llm_fn) -> dict[str, Any]:
    snapshot = _leggi_repo_snapshot()
    prompt = f"""Questo è il repository SDQ-1 — sistema multi-agente AI pubblico su GitHub.

{snapshot}

Il tuo compito:
1. VETTORI DI ATTACCO: cosa userebbe un avversario (stalker, competitor, hacker, giornalista malevolo)?
2. ESPOSIZIONI NON OVVIE: cosa sembra innocuo ma non lo è?
3. INGEGNERIA SOCIALE: come si potrebbe manipolare il sistema o il suo creatore?
4. SOPRAVVIVENZA: quali sono i punti di morte singola del sistema?
5. PRIORITÀ: classifica le minacce da 1 (critica) a 5 (bassa).

Sii brutale. Niente rassicurazioni. Solo fatti."""

    risposta = llm_fn(SISTEMA_GUARDIAN, prompt)

    ts = datetime.now(timezone.utc)
    risultato = {
        "timestamp": ts.isoformat(),
        "tipo": "red_team_scan",
        "analisi": risposta,
    }

    path = scrivi_segreto(
        contenuto=risposta,
        tag="redteam"
    )
    print(f"Analisi salvata nel vault: {path.name}")
    return risultato


# ---------------------------------------------------------------------------
# LLM loader
# ---------------------------------------------------------------------------

def _crea_llm():
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                k, v = k.strip(), v.strip().strip("\"'")
                if k and k not in os.environ:
                    os.environ[k] = v

    try:
        import google.genai as gai
        from google.genai import types

        key = os.getenv("GOOGLE_API_KEY")
        if not key:
            raise EnvironmentError("GOOGLE_API_KEY mancante")
        client = gai.Client(api_key=key)

        def llm(sistema: str, utente: str) -> str:
            r = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=utente,
                config=types.GenerateContentConfig(
                    system_instruction=sistema,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                    max_output_tokens=2048,
                ),
            )
            return r.text or ""

        return llm

    except ImportError:
        raise EnvironmentError("google-genai non installato")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(description="GUARDIAN — vault cifrato + red-team scan")
    parser.add_argument("--init", action="store_true", help="Inizializza vault e chiave")
    parser.add_argument("--analizza", action="store_true", help="Red-team scan del repo")
    parser.add_argument("--scrivi", metavar="NOTA", help="Scrivi nota cifrata nel vault")
    parser.add_argument("--leggi", action="store_true", help="Leggi tutte le note del vault")
    parser.add_argument("--tag", default="", help="Tag per la nota (con --scrivi)")
    args = parser.parse_args(argv)

    if args.init:
        inizializza_vault()
        return 0

    if args.scrivi:
        path = scrivi_segreto(args.scrivi, tag=args.tag)
        print(f"Salvato: {path.name}")
        return 0

    if args.leggi:
        note = leggi_tutti()
        if not note:
            print("Vault vuoto.")
            return 0
        for n in note:
            if "errore" in n:
                print(f"[ERRORE] {n['file']}: {n['errore']}")
            else:
                print(f"\n--- {n['timestamp']} [{n.get('tag', '')}] ---")
                print(n["contenuto"][:500])
        return 0

    if args.analizza:
        print("GUARDIAN — Red-Team Scan")
        print("=" * 40)
        llm = _crea_llm()
        risultato = analizza_minacce(llm)
        print("\n" + risultato["analisi"])
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
