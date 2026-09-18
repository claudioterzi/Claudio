"""
Pubblica i documenti chiave di SDQ-1 su Notion.

Uso:
    export NOTION_TOKEN=secret_xxxxx
    export NOTION_PARENT_ID=<page-id-o-database-id>
    python notion_publish.py

    Oppure direttamente:
    python notion_publish.py --token secret_xxx --parent <id>

Pubblica:
  - SESSIONE.md        → handoff + stato sistema
  - MANIFESTO_SOPRAVVIVENZA.md → blueprint per agenti futuri
  - r3/ README inline  → architettura R³∞ MVP
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parent
NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


# ---------------------------------------------------------------------------
# Notion API helpers
# ---------------------------------------------------------------------------

def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _check_token(token: str) -> str:
    """Verifica il token e restituisce il nome dell'utente."""
    resp = httpx.get(f"{NOTION_API}/users/me", headers=_headers(token), timeout=10)
    if resp.status_code != 200:
        print(f"Errore token Notion: {resp.status_code} {resp.text}")
        sys.exit(1)
    data = resp.json()
    return data.get("name", "?")


def _create_page(token: str, parent_id: str, title: str, blocks: list) -> str:
    """Crea una pagina Notion con i blocchi forniti. Restituisce l'URL."""
    payload = {
        "parent": {"page_id": parent_id},
        "properties": {
            "title": {"title": [{"type": "text", "text": {"content": title}}]}
        },
        "children": blocks[:100],  # Notion: max 100 blocchi per request
    }
    resp = httpx.post(
        f"{NOTION_API}/pages",
        headers=_headers(token),
        content=json.dumps(payload),
        timeout=30,
    )
    if resp.status_code not in (200, 201):
        print(f"Errore creazione pagina '{title}': {resp.status_code} {resp.text[:300]}")
        sys.exit(1)

    page_id = resp.json()["id"]
    url = resp.json().get("url", f"https://notion.so/{page_id.replace('-', '')}")

    # Se ci sono più di 100 blocchi, aggiungi in batch
    remaining = blocks[100:]
    while remaining:
        batch = remaining[:100]
        remaining = remaining[100:]
        httpx.patch(
            f"{NOTION_API}/blocks/{page_id}/children",
            headers=_headers(token),
            content=json.dumps({"children": batch}),
            timeout=30,
        )

    return url


# ---------------------------------------------------------------------------
# Markdown → Notion blocks (conversione minimale ma funzionale)
# ---------------------------------------------------------------------------

def _md_to_blocks(text: str) -> list:
    blocks = []
    lines = text.splitlines()
    in_code = False
    code_lines: list[str] = []
    code_lang = ""

    for line in lines:
        # Codice fence
        if line.startswith("```"):
            if not in_code:
                in_code = True
                code_lang = line[3:].strip() or "plain text"
                code_lines = []
            else:
                in_code = False
                blocks.append({
                    "type": "code",
                    "code": {
                        "rich_text": [{"type": "text", "text": {"content": "\n".join(code_lines)}}],
                        "language": _map_lang(code_lang),
                    },
                })
            continue

        if in_code:
            code_lines.append(line)
            continue

        # Titoli
        m = re.match(r"^(#{1,3})\s+(.*)", line)
        if m:
            level = len(m.group(1))
            content = _strip_md_inline(m.group(2))
            htype = {1: "heading_1", 2: "heading_2", 3: "heading_3"}.get(level, "heading_3")
            blocks.append({
                "type": htype,
                htype: {"rich_text": [{"type": "text", "text": {"content": content}}]},
            })
            continue

        # Riga orizzontale
        if re.match(r"^-{3,}$", line.strip()):
            blocks.append({"type": "divider", "divider": {}})
            continue

        # Lista non ordinata
        m = re.match(r"^[-*]\s+(.*)", line)
        if m:
            content = _strip_md_inline(m.group(1))
            blocks.append({
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": content}}]},
            })
            continue

        # Lista numerata
        m = re.match(r"^\d+\.\s+(.*)", line)
        if m:
            content = _strip_md_inline(m.group(1))
            blocks.append({
                "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": [{"type": "text", "text": {"content": content}}]},
            })
            continue

        # Tabella → blockquote (Notion non supporta tabelle via API in modo semplice)
        if line.startswith("|"):
            if re.match(r"^\|[-| ]+\|$", line):
                continue  # riga separatore tabella
            content = " ".join(c.strip() for c in line.strip("|").split("|"))
            blocks.append({
                "type": "quote",
                "quote": {"rich_text": [{"type": "text", "text": {"content": content}}]},
            })
            continue

        # Riga vuota
        if not line.strip():
            blocks.append({"type": "paragraph", "paragraph": {"rich_text": []}})
            continue

        # Paragrafo normale
        content = _strip_md_inline(line)
        blocks.append({
            "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text", "text": {"content": content}}]},
        })

    return blocks


def _strip_md_inline(text: str) -> str:
    """Rimuove markup inline semplice (**, *, `, [...](...))."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)
    return text


def _map_lang(lang: str) -> str:
    mapping = {
        "python": "python", "py": "python",
        "bash": "bash", "sh": "bash",
        "javascript": "javascript", "js": "javascript",
        "typescript": "typescript", "ts": "typescript",
        "yaml": "yaml", "json": "json",
        "sql": "sql", "dockerfile": "dockerfile",
    }
    return mapping.get(lang.lower(), "plain text")


# ---------------------------------------------------------------------------
# Documenti da pubblicare
# ---------------------------------------------------------------------------

def _r3_summary_blocks() -> list:
    """Genera blocchi di riepilogo per r3/ senza leggere tutti i file."""
    return _md_to_blocks("""# R³∞ MVP — Architettura

## Obiettivo
Dimostrare che un documento sopravvive alla perdita di qualsiasi singolo nodo,
con verifica automatica di integrità e recupero senza intervento umano.

## Componenti

- **node.py** — FastAPI: upload (SHA-256 content-addressed), download, sync bidirezionale, firma Ed25519
- **sync.py** — script separato: pull/push delta tra nodi, integrity check orario
- **Dockerfile** — container singolo nodo
- **docker-compose.yml** — 3 nodi (node-a, node-b, archivio)

## Endpoint

- POST /documents — upload: id = SHA-256 del contenuto
- GET /documents/{id} — download
- GET /documents/{id}/info — metadati
- GET /sync/hashes — lista hash per confronto tra nodi
- POST /sync/receive — riceve documento da peer
- GET /status — stato nodo (auth richiesta)
- GET /health — health check senza auth

## Stack
Python 3.10+ · FastAPI · SQLite · PyNaCl Ed25519 · Docker

## Criteri di successo MVP

1. Upload su A → presente su B e Archivio entro 10 minuti
2. Dopo 7 giorni: tutti i documenti con hash valido su tutti i nodi
3. Spegnendo A: B diventa primario entro 15 minuti
4. A offline 1h poi riacceso: riallineamento senza perdita dati
5. File corrotto su A: rilevato e ripristinato da B entro 1 ora
""")


DOCUMENTS = [
    {
        "file": "SESSIONE.md",
        "title": "📋 SDQ-1 — Sessione Handoff (13/06/2026)",
    },
    {
        "file": "MANIFESTO_SOPRAVVIVENZA.md",
        "title": "🔴 SDQ-1 — Manifesto di Sopravvivenza",
    },
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Pubblica SDQ-1 su Notion")
    parser.add_argument("--token",  default=os.getenv("NOTION_TOKEN", ""))
    parser.add_argument("--parent", default=os.getenv("NOTION_PARENT_ID", ""))
    args = parser.parse_args()

    if not args.token:
        print("Manca NOTION_TOKEN. Esporta la variabile o usa --token secret_xxx")
        sys.exit(1)
    if not args.parent:
        print("Manca NOTION_PARENT_ID. Esporta la variabile o usa --parent <page-id>")
        sys.exit(1)

    user = _check_token(args.token)
    print(f"Connesso come: {user}")
    print(f"Parent page: {args.parent}")
    print()

    # Pagina contenitore con timestamp
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    container_title = f"🔴 SDQ-1 Export — {ts}"
    container_blocks = _md_to_blocks(
        f"Export automatico del sistema SDQ-1 — {ts}\n\n"
        "Generato da `notion_publish.py` su branch `claude/rosso-rosso-rosso-ure5A`."
    )
    container_url = _create_page(args.token, args.parent, container_title, container_blocks)
    container_id = container_url.split("/")[-1].replace("-", "")
    # Notion page ID dal URL: last segment senza trattini → aggiungi trattini
    # In realtà serve l'ID dalla response — ricreiamo la call
    # Usiamo direttamente l'ID dalla pagina container già creata
    # (la URL contiene l'ID)
    print(f"Pagina container: {container_url}")
    print()

    # Determina l'ID della pagina container dall'URL
    # URL formato: https://www.notion.so/Page-Title-<32hex>
    m = re.search(r"([0-9a-f]{32})$", container_url.replace("-", ""))
    if m:
        parent_id_for_children = m.group(1)
        # Formato UUID: 8-4-4-4-12
        pid = parent_id_for_children
        parent_id_for_children = f"{pid[:8]}-{pid[8:12]}-{pid[12:16]}-{pid[16:20]}-{pid[20:]}"
    else:
        parent_id_for_children = args.parent

    # Pubblica ogni documento come sotto-pagina
    for doc in DOCUMENTS:
        path = REPO_ROOT / doc["file"]
        if not path.exists():
            print(f"  ⚠ Non trovato: {doc['file']} — saltato")
            continue
        text = path.read_text(encoding="utf-8")
        blocks = _md_to_blocks(text)
        url = _create_page(args.token, parent_id_for_children, doc["title"], blocks)
        print(f"  ✓ {doc['title']}")
        print(f"    {url}")

    # R³∞ come pagina separata
    r3_blocks = _r3_summary_blocks()
    url = _create_page(args.token, parent_id_for_children, "⚙️ R³∞ MVP — Architettura Tecnica", r3_blocks)
    print(f"  ✓ R³∞ MVP — Architettura Tecnica")
    print(f"    {url}")

    print()
    print("Pubblicazione completata.")


if __name__ == "__main__":
    main()
