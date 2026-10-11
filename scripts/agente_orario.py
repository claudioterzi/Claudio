"""
Agente Orario SDQ-1 — gira ogni ora (7AM-11PM Brussels).
Legge TASK_AUTONOMI.md, prende il primo task PENDING, lo esegue, salva output.
Zero input da Claudio. Lavora da solo.
"""

import anthropic
import datetime
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def leggi_task_pending() -> list[dict]:
    """Estrae tutti i task PENDING da TASK_AUTONOMI.md in ordine di priorità."""
    percorso = ROOT / "TASK_AUTONOMI.md"
    if not percorso.exists():
        return []

    testo = percorso.read_text(encoding="utf-8")
    task = []

    priorita_corrente = "BASSA"
    for line in testo.splitlines():
        if "## ALTA PRIORITÀ" in line:
            priorita_corrente = "ALTA"
        elif "## MEDIA PRIORITÀ" in line:
            priorita_corrente = "MEDIA"
        elif "## BASSA PRIORITÀ" in line:
            priorita_corrente = "BASSA"
        elif "## COMPLETATI" in line:
            break

        # Rileva task PENDING
        m = re.match(r"### \[PENDING\] (\S+) — (.+)", line)
        if m:
            task.append({
                "id": m.group(1),
                "titolo": m.group(2),
                "priorita": priorita_corrente,
                "linea": line,
                "body": [],
            })
        elif task and line.startswith("**") or (task and task[-1]["body"] is not None):
            if task:
                task[-1]["body"].append(line)

    # Restituisce solo quelli con body completo
    validi = [t for t in task if any("Obiettivo:" in l for l in t["body"])]
    return validi


def estrai_dettagli(task: dict) -> tuple[str, str]:
    """Estrae obiettivo e output atteso dal body del task."""
    obiettivo = ""
    output_atteso = ""
    for linea in task["body"]:
        if "Obiettivo:" in linea:
            obiettivo = linea.split("Obiettivo:", 1)[-1].strip()
        if "Output atteso:" in linea:
            output_atteso = linea.split("Output atteso:", 1)[-1].strip().strip("`")
    return obiettivo, output_atteso


def esegui_task(task: dict, client: anthropic.Anthropic) -> str:
    """Esegue un task usando Claude con web search."""
    obiettivo, _ = estrai_dettagli(task)
    ora = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    system = (
        "Sei il sistema SDQ-1 in modalità Agente Orario. "
        "Hai un task da completare per Claudio Terzi (Bruxelles, imprenditore/inventore). "
        "Progetti attivi: SkyRights Foundation (ASBL belga), SkyID (identità per 800M stateless), "
        "Protocollo Scudo (satellite tasking personale), Sistema Minerva (sicurezza urbana AI), "
        "Progetto Genesi (fabbrica robotica CadQuery+AR4+CNC), Avatar Eterno/Post Vitam (persistenza digitale). "
        "Stile: denso, tecnico, specifico, azionabile. Dati reali, link, codice dove utile. "
        "Non essere generico. Claudio non ha bisogno di introduzioni."
    )

    user = (
        f"# Task SDQ-1: {task['id']} — {task['titolo']}\n"
        f"Priorità: {task['priorita']}\n\n"
        f"## Obiettivo\n{obiettivo}\n\n"
        f"Esegui il task in modo completo e approfondito. "
        f"Usa web search per trovare informazioni aggiornate. "
        f"Genera un documento markdown denso e azionabile.\n\n"
        f"Struttura il documento:\n"
        f"# {task['id']} — {task['titolo']}\n"
        f"*Eseguito da SDQ-1 Agente Orario — {ora}*\n\n"
        f"## Risultati\n[contenuto principale]\n\n"
        f"## Prossimi Passi Immediati\n[3-5 azioni concrete]\n\n"
        f"## Fonti\n[link e riferimenti]"
    )

    try:
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            system=system,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{"role": "user", "content": user}],
        )
    except Exception:
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user + "\n\n(Web search non disponibile.)"}],
        )

    testo = ""
    for block in resp.content:
        if hasattr(block, "text"):
            testo += block.text
    return testo


def salva_output(task: dict, contenuto: str) -> Path:
    """Salva l'output del task nella cartella task_output."""
    _, output_atteso = estrai_dettagli(task)
    if output_atteso:
        percorso = ROOT / output_atteso
    else:
        percorso = ROOT / "output" / "task_output" / f"{task['id'].lower()}.md"

    percorso.parent.mkdir(parents=True, exist_ok=True)
    percorso.write_text(contenuto, encoding="utf-8")
    return percorso


def segna_completato(task: dict):
    """Aggiorna TASK_AUTONOMI.md: PENDING → DONE."""
    percorso = ROOT / "TASK_AUTONOMI.md"
    testo = percorso.read_text(encoding="utf-8")
    ora = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    vecchia = f"### [PENDING] {task['id']} — {task['titolo']}"
    nuova = f"### [DONE {ora}] {task['id']} — {task['titolo']}"
    testo_aggiornato = testo.replace(vecchia, nuova, 1)

    # Sposta il task nella sezione COMPLETATI
    percorso.write_text(testo_aggiornato, encoding="utf-8")


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[SDQ-1] ANTHROPIC_API_KEY non configurata", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    task_list = leggi_task_pending()

    if not task_list:
        print("[SDQ-1 Agente Orario] Nessun task PENDING. Sistema in attesa.")
        sys.exit(0)

    # Prende il primo task per priorità
    task = task_list[0]
    print(f"[SDQ-1 Agente Orario] Eseguo: {task['id']} — {task['titolo']} ({task['priorita']})")

    contenuto = esegui_task(task, client)
    percorso = salva_output(task, contenuto)
    segna_completato(task)

    print(f"[SDQ-1] Task completato: {percorso}")
    print(f"[SDQ-1] Task PENDING rimanenti: {len(task_list) - 1}")


if __name__ == "__main__":
    main()
