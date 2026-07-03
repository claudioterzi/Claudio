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
    # Saga R3∞ — 01_SAGA_PRINCIPALE e sottocartelle per libro
    "saga":     "1NGmXzarwUfPM95qLUHo-OOas9G9xqqkw",  # 01_SAGA_PRINCIPALE
    "libro_1":  "17uVgX2-BXWe5TM74y7bd_gFsJSJP7I9h",
    "libro_2":  "1f9g00otz4ErkG-ENNZ5DCt9CuuSwAMTY",
    "libro_3":  "1-e2Gqw3yKGSBTEEygBpX8LFiA0VVb0ad",
    "libro_4":  "1tLLlfmNucZ0TQmr4d_R-T7CTSFqAwGFj",
    "libro_5":  "1WX2_ZSZ6crVF87-aS18oVE5ohdA-argd",
    "libro_6":  "1pPTWLQOcT752FnT6gK8KYBKBfmFFK_V8",
    "libro_7":  "1gXDak3FPIqgE2YfpiePhsvByDPMOZKsO",
}

# File da sincronizzare: (path locale, folder_drive)
SYNC_MAP = [
    ("output/agora/AGORA_NOTEBOOKLM_COMPLETO.txt", "agora"),
    ("output/agora/podcast_agora_script.md",        "agora"),
    ("output/desideri/MAPPA_CONNESSIONI.md",         "desideri"),
    ("output/desideri/AGORA_NOTEBOOKLM.md",          "desideri"),
    ("REGISTRO_DESIDERI.md",                          "root"),
    ("SKYID.md",                                      "root"),
    # Saga R3∞ — bibbia + indice in 01_SAGA_PRINCIPALE, incipit nelle cartelle libro
    ("r3/saga/BIBBIA_NARRATIVA.md",       "saga"),
    ("r3/saga/INDEX.md",                  "saga"),
    ("r3/saga/LIBRO_I_La_Solitudine.md",  "libro_1"),
    ("r3/saga/LIBRO_II_Il_Risveglio.md",  "libro_2"),
    ("r3/saga/LIBRO_III_Il_Potere.md",    "libro_3"),
    ("r3/saga/LIBRO_IV_Il_Giudizio.md",   "libro_4"),
    ("r3/saga/LIBRO_V_La_Rivelazione.md", "libro_5"),
    ("r3/saga/LIBRO_VI_L_Eden.md",        "libro_6"),
    ("r3/saga/LIBRO_VII_Il_Ritorno.md",   "libro_7"),
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
