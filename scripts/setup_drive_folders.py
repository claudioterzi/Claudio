#!/usr/bin/env python3
"""
setup_drive_folders.py — SDQ-1
Da eseguire UNA VOLTA sul tuo PC per:
1. Creare le 4 cartelle su Google Drive (se non esistono)
2. Stampare gli ID pronti da incollare nei GitHub Secrets

Uso:
  pip install google-api-python-client google-auth
  python scripts/setup_drive_folders.py /percorso/al/tuo/service-account.json
"""

import json
import sys
from pathlib import Path

ROOT_FOLDER_ID = "1-pJYRwoZ0uYCtyoLoBjNvSe2s_kNoMlm"

CARTELLE_DA_CREARE = [
    ("Morning Brief", "DRIVE_BRIEF_FOLDER_ID"),
    ("Portfolio",     "DRIVE_PORTFOLIO_FOLDER_ID"),
    ("Personale",     "DRIVE_PERSONALE_FOLDER_ID"),
    ("Io e Fabri",    "DRIVE_FABRIZIO_FOLDER_ID"),
]


def get_service(creds_path: str):
    from googleapiclient.discovery import build
    from google.oauth2.service_account import Credentials
    creds = Credentials.from_service_account_file(
        creds_path,
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds)


def trova_o_crea_cartella(service, nome: str, parent_id: str) -> str:
    query = (
        f"name='{nome}' and '{parent_id}' in parents "
        f"and mimeType='application/vnd.google-apps.folder' and trashed=false"
    )
    result = service.files().list(q=query, fields="files(id,name)").execute()
    files = result.get("files", [])
    if files:
        print(f"  [TROVATA] '{nome}' → {files[0]['id']}")
        return files[0]["id"]
    meta = {
        "name": nome,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    f = service.files().create(body=meta, fields="id").execute()
    print(f"  [CREATA]  '{nome}' → {f['id']}")
    return f["id"]


def crea_sottocartella_lettere(service, fabrizio_id: str) -> None:
    trova_o_crea_cartella(service, "lettere", fabrizio_id)


def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/setup_drive_folders.py /percorso/service-account.json")
        print()
        print("Il file JSON lo trovi in Google Cloud Console:")
        print("  console.cloud.google.com → IAM → Account di servizio → Chiavi → Crea chiave JSON")
        sys.exit(1)

    creds_path = sys.argv[1]
    if not Path(creds_path).exists():
        print(f"File non trovato: {creds_path}")
        sys.exit(1)

    print(f"\nConnessione a Google Drive con: {creds_path}")
    print(f"Cartella root Agorà: {ROOT_FOLDER_ID}\n")

    service = get_service(creds_path)

    ids = {}
    for nome, secret_name in CARTELLE_DA_CREARE:
        folder_id = trova_o_crea_cartella(service, nome, ROOT_FOLDER_ID)
        ids[secret_name] = folder_id

    # Crea sottocartella lettere dentro Io e Fabri
    crea_sottocartella_lettere(service, ids["DRIVE_FABRIZIO_FOLDER_ID"])

    print("\n" + "="*60)
    print("COPIA QUESTI VALORI NEI GITHUB SECRETS:")
    print(f"  https://github.com/Claudioterzi82/Claudio/settings/secrets/actions")
    print("="*60)
    print()
    print(f"  AGORA_FOLDER_ID          = {ROOT_FOLDER_ID}")
    for secret_name, folder_id in ids.items():
        print(f"  {secret_name:<30} = {folder_id}")
    print()

    # Salva anche in un file locale per copiare con calma
    output = {"AGORA_FOLDER_ID": ROOT_FOLDER_ID}
    output.update(ids)
    out_path = Path(__file__).parent.parent / "output" / "drive_folder_ids.txt"
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w") as f:
        for k, v in output.items():
            f.write(f"{k}={v}\n")
    print(f"IDs salvati anche in: {out_path}")
    print()
    print("Dopo aver aggiunto i secrets su GitHub, la sync Drive")
    print("partirà automaticamente ogni notte alle 2:00 Brussels.")


if __name__ == "__main__":
    main()
