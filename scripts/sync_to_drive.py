"""
Sincronizzazione automatica repository → Google Drive
Claudio Terzi [CT-LGAI-001] — SDQ-1

Cartelle sincronizzate:
  output/agora/         → Drive: Agorà Digitale — SDQ-1 / Agora — Multimedia
  output/desideri/      → Drive: Agorà Digitale — SDQ-1 / Desideri — 11 Pilastri
  output/morning_brief/ → Drive: Agorà Digitale — SDQ-1 / Morning Brief
  output/portfolio/     → Drive: Agorà Digitale — SDQ-1 / Portfolio
  personale/            → Drive: Agorà Digitale — SDQ-1 / Personale (PRIVATO)
  portfolio/            → Drive: Agorà Digitale — SDQ-1 / Portfolio

REGOLA: i file personali (personale/, portfolio/) non vanno su GitHub.
Solo su Drive. Questo script è l'unico canale di backup per quei dati.
"""

import json
import os
import sys
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials

# Cartella root su Drive: "Agorà Digitale — SDQ-1"
DRIVE_FOLDER_ID = os.environ.get("AGORA_FOLDER_ID", "1-pJYRwoZ0uYCtyoLoBjNvSe2s_kNoMlm")

# Sottocartelle su Drive (ID fissi, creati il 16/06/2026)
# Le nuove cartelle vengono create automaticamente se non hanno ID
SUBFOLDER_IDS = {
    "agora":         "1YTOisPw_-da6w-ND2N7P9zYMKq45kpoH",  # Agora — Multimedia
    "desideri":      "1FUyvZ5-m-SSkJjZ2t_cBamguyyVH1xZQ",  # Desideri — 11 Pilastri
    "morning_brief": os.environ.get("DRIVE_BRIEF_FOLDER_ID",     "1nuL-2lu8gQMziHptzpMQ4NutBJLAw3Vj"),
    "portfolio":     os.environ.get("DRIVE_PORTFOLIO_FOLDER_ID", "17Gs7ZrYYmRNect-huQ4YYiBuQdN4N5R1"),
    "personale":     os.environ.get("DRIVE_PERSONALE_FOLDER_ID", "1iC__qD1gJ4ZzTG8ad6gj8my4P6jDxtHB"),
    "fabrizio":      os.environ.get("DRIVE_FABRIZIO_FOLDER_ID",  "1ifyqeh7gU0qlugF1LBuZL6-p7-QH2BKH"),
}

# File statici da sincronizzare sempre: (path locale, folder_drive)
SYNC_MAP_STATIC = [
    ("output/agora/AGORA_NOTEBOOKLM_COMPLETO.txt", "agora"),
    ("output/agora/podcast_agora_script.md",        "agora"),
    ("output/desideri/MAPPA_CONNESSIONI.md",         "desideri"),
    ("output/desideri/AGORA_NOTEBOOKLM.md",          "desideri"),
    ("REGISTRO_DESIDERI.md",                          "root"),
    ("SKYID.md",                                      "root"),
    ("portfolio/holdings.json",                       "portfolio"),
    ("personale/MADRE.md",                            "personale"),
    ("fabrizio/COME_FUNZIONA.md",                     "fabrizio"),
]

# Cartelle da sincronizzare interamente — incluse le lettere
SYNC_DIRS_LETTERS = [
    ("fabrizio/lettere", "fabrizio"),
]

# Cartelle da sincronizzare interamente (tutti i file .md e .json al loro interno)
SYNC_DIRS = [
    ("output/morning_brief", "morning_brief"),
    ("output/portfolio",     "portfolio"),
]

MIME_TEXT = "text/plain"
MIME_MD   = "text/plain"

def get_service():
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if not creds_json:
        raise ValueError("GOOGLE_CREDENTIALS_JSON non impostato")
    creds_data = json.loads(creds_json)
    creds = Credentials.from_service_account_info(
        creds_data,
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds)


def find_file(service, name, parent_id):
    query = f"name='{name}' and '{parent_id}' in parents and trashed=false"
    result = service.files().list(q=query, fields="files(id,name)").execute()
    files = result.get("files", [])
    return files[0]["id"] if files else None


def upload_or_update(service, local_path, parent_id):
    path = Path(local_path)
    if not path.exists():
        print(f"  SKIP (non esiste): {local_path}")
        return

    mime = MIME_MD if path.suffix == ".md" else MIME_TEXT
    media = MediaFileUpload(str(path), mimetype=mime, resumable=False)
    existing_id = find_file(service, path.name, parent_id)

    if existing_id:
        service.files().update(fileId=existing_id, media_body=media).execute()
        print(f"  AGGIORNATO: {path.name}")
    else:
        meta = {"name": path.name, "parents": [parent_id]}
        service.files().create(body=meta, media_body=media).execute()
        print(f"  CREATO: {path.name}")


def get_or_create_folder(service, name: str, parent_id: str) -> str:
    """Recupera o crea una sottocartella su Drive. Restituisce l'ID."""
    query = f"name='{name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    result = service.files().list(q=query, fields="files(id,name)").execute()
    files = result.get("files", [])
    if files:
        return files[0]["id"]
    meta = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = service.files().create(body=meta, fields="id").execute()
    print(f"  CARTELLA CREATA su Drive: {name}")
    return folder["id"]


def resolve_folder_id(service, folder_key: str) -> str:
    """Risolve l'ID Drive di una cartella, creandola se necessario."""
    folder_id = SUBFOLDER_IDS.get(folder_key, "")
    if folder_id:
        return folder_id
    # Crea la cartella sotto root
    name_map = {
        "morning_brief": "Morning Brief",
        "portfolio":     "Portfolio",
        "personale":     "Personale",
        "fabrizio":      "Io e Fabri",
    }
    folder_name = name_map.get(folder_key, folder_key)
    new_id = get_or_create_folder(service, folder_name, DRIVE_FOLDER_ID)
    SUBFOLDER_IDS[folder_key] = new_id
    return new_id


def main():
    repo_root = Path(__file__).parent.parent
    service = get_service()

    print(f"Sync → Drive folder: {DRIVE_FOLDER_ID}")

    # File statici
    for local_rel, folder_key in SYNC_MAP_STATIC:
        local_abs = repo_root / local_rel
        if folder_key == "root":
            parent_id = DRIVE_FOLDER_ID
        else:
            parent_id = resolve_folder_id(service, folder_key)
        upload_or_update(service, str(local_abs), parent_id)

    # Cartelle intere (output)
    for dir_rel, folder_key in SYNC_DIRS:
        dir_abs = repo_root / dir_rel
        if not dir_abs.exists():
            continue
        parent_id = resolve_folder_id(service, folder_key)
        for f in sorted(list(dir_abs.glob("*.md")) + list(dir_abs.glob("*.json"))):
            upload_or_update(service, str(f), parent_id)

    # Lettere Fabrizio — sottocartella "lettere/" dentro "Io e Fabri"
    for dir_rel, folder_key in SYNC_DIRS_LETTERS:
        dir_abs = repo_root / dir_rel
        if not dir_abs.exists():
            continue
        parent_folder_id = resolve_folder_id(service, folder_key)
        lettere_folder_id = get_or_create_folder(service, "lettere", parent_folder_id)
        for f in sorted(dir_abs.glob("*.md")):
            upload_or_update(service, str(f), lettere_folder_id)

    print("Sincronizzazione completata.")


if __name__ == "__main__":
    main()
