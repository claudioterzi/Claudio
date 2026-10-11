"""
Sincronizzazione automatica repository → Google Drive
Claudio Terzi [CT-LGAI-001] — SDQ-1

Cartelle sincronizzate:
  output/agora/     → Drive: Agorà Digitale — SDQ-1 / Agora — Multimedia
  output/desideri/  → Drive: Agorà Digitale — SDQ-1 / Desideri — 11 Pilastri
  REGISTRO_DESIDERI.md → Drive: Agorà Digitale — SDQ-1 (root)
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
SUBFOLDER_IDS = {
    "agora":    "1YTOisPw_-da6w-ND2N7P9zYMKq45kpoH",  # Agora — Multimedia
    "desideri": "1FUyvZ5-m-SSkJjZ2t_cBamguyyVH1xZQ",  # Desideri — 11 Pilastri
}

# File da sincronizzare: (path locale, folder_drive)
SYNC_MAP = [
    ("output/agora/AGORA_NOTEBOOKLM_COMPLETO.txt", "agora"),
    ("output/agora/podcast_agora_script.md",        "agora"),
    ("output/desideri/MAPPA_CONNESSIONI.md",         "desideri"),
    ("output/desideri/AGORA_NOTEBOOKLM.md",          "desideri"),
    ("REGISTRO_DESIDERI.md",                          "root"),
    ("SKYID.md",                                      "root"),
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


def main():
    repo_root = Path(__file__).parent.parent
    service = get_service()

    print(f"Sync → Drive folder: {DRIVE_FOLDER_ID}")
    for local_rel, folder_key in SYNC_MAP:
        local_abs = repo_root / local_rel
        if folder_key == "root":
            parent_id = DRIVE_FOLDER_ID
        else:
            parent_id = SUBFOLDER_IDS[folder_key]
        upload_or_update(service, str(local_abs), parent_id)

    print("Sincronizzazione completata.")


if __name__ == "__main__":
    main()
