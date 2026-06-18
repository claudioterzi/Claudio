# Task: Configura Google Drive Sync per il sistema SDQ-1 di Claudio Terzi

## Contesto
Claudio ha un sistema automatico (SDQ-1) su GitHub che genera morning briefs, analisi portfolio crypto, e documenti personali. Il codice è pronto. Manca solo la connessione a Google Drive per il backup automatico dei file.

**Repository GitHub:** `https://github.com/claudioterzi/Claudio`

---

## Step 1 — Controlla se le credenziali esistono già

Vai su:
`https://github.com/claudioterzi/Claudio/settings/secrets/actions`

**Cerca questi secrets nella lista:**
- `GOOGLE_CREDENTIALS_JSON`
- `AGORA_FOLDER_ID`

**Se `GOOGLE_CREDENTIALS_JSON` esiste già → vai direttamente allo Step 3.**
**Se non esiste → fai lo Step 2.**

---

## Step 2 — Crea le credenziali Google (solo se mancano)

1. Vai su `https://console.cloud.google.com/`
2. Accedi con l'account Google di Claudio (`terziclaudio@gmail.com`)
3. Seleziona il progetto già esistente (cerca quello collegato a Google Drive / SDQ-1)
4. Menu laterale → **IAM e amministrazione** → **Account di servizio**
5. Cerca un account di servizio esistente (probabilmente ne esiste già uno)
6. Clicca sul service account → **Chiavi** → **Aggiungi chiave** → **Crea nuova chiave** → JSON
7. Scarica il file `.json`
8. Apri il file con un editor di testo — copia **tutto il contenuto**

---

## Step 3 — Aggiungi i Secrets a GitHub

Vai su:
`https://github.com/claudioterzi/Claudio/settings/secrets/actions`

Aggiungi (o aggiorna) questi secrets:

| Nome Secret | Valore |
|-------------|--------|
| `GOOGLE_CREDENTIALS_JSON` | Tutto il contenuto JSON scaricato (o già esistente) |
| `AGORA_FOLDER_ID` | `1-pJYRwoZ0uYCtyoLoBjNvSe2s_kNoMlm` |

---

## Step 4 — Crea le cartelle su Google Drive

Vai su:
`https://drive.google.com/drive/folders/1-pJYRwoZ0uYCtyoLoBjNvSe2s_kNoMlm`

Dentro la cartella "Agorà Digitale — SDQ-1" crea queste 4 sottocartelle:
- `Morning Brief`
- `Portfolio`
- `Personale`
- `Io e Fabri` (dentro questa, crea anche una sottocartella `lettere`)

Per ogni cartella creata: apri la cartella → copia l'ID dall'URL del browser
(la parte finale dopo `/folders/`)

Poi aggiungi questi 4 secrets su GitHub:

| Nome Secret | Cartella Drive |
|-------------|----------------|
| `DRIVE_BRIEF_FOLDER_ID` | ID cartella "Morning Brief" |
| `DRIVE_PORTFOLIO_FOLDER_ID` | ID cartella "Portfolio" |
| `DRIVE_PERSONALE_FOLDER_ID` | ID cartella "Personale" |
| `DRIVE_FABRIZIO_FOLDER_ID` | ID cartella "Io e Fabri" |

---

## Step 5 — Testa la sync

Vai su:
`https://github.com/claudioterzi/Claudio/actions/workflows/sync_drive.yml`

Clicca **"Run workflow"** → **"Run workflow"** (verde)

Aspetta 60 secondi. Se il workflow diventa verde ✓ → tutto funziona.

---

## Note tecniche per l'AI che esegue questo task

- Il service account deve avere accesso alla Google Drive API
- Se il service account non esiste, creane uno nuovo con ruolo "Editor"
- Attiva l'API "Google Drive API" nel progetto se non è già attiva
- Il file JSON del service account ha questo formato:
  ```json
  {
    "type": "service_account",
    "project_id": "...",
    "private_key_id": "...",
    ...
  }
  ```
- Una volta configurato, il sistema sincronizzerà automaticamente ogni notte alle 2:00 Brussels

---

*Documento generato da SDQ-1 · 18 giugno 2026*
*Per: Claudio Terzi [CT-LGAI-001]*
