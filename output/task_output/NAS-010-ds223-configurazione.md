# NAS-010 — Configurazione Synology DS223 come Nodo SDQ-1
*Task autonomo SDQ-1 — completato 2026-06-20*

---

## Setup base (IP locale: 192.168.1.188)

### 1. Accesso iniziale

```
Browser → http://192.168.1.188:5000
Login: admin / [password scelta al primo avvio]
```

Se non risponde: verificare che DS223 sia acceso e cavo ethernet collegato.
**Non usare WiFi per il NAS** — sempre cablato per affidabilità.

---

### 2. DSM aggiornamento

```
Control Panel → Update & Restore → DSM Update
→ Installa DSM 7.2 se non già installato
→ Riavvia se richiesto
```

---

### 3. Docker su DS223

Il DS223 ha CPU Intel Celeron J4125 (x86-64) → supporta Docker nativamente.

```
Package Center → cerca "Container Manager" → Installa
```

Container Manager = Docker + Docker Compose integrato in DSM 7.2.

---

### 4. Deploy Nodo R3∞ su DS223

Crea la struttura:

```bash
# Sul NAS via SSH (Control Panel → Terminal → Enable SSH)
ssh admin@192.168.1.188

mkdir -p /volume1/sdq1/r3/data/node-nas
mkdir -p /volume1/sdq1/backups
mkdir -p /volume1/sdq1/repo
```

File `docker-compose-nas.yml` per il NAS:

```yaml
# /volume1/sdq1/r3/docker-compose-nas.yml
services:
  node-nas:
    image: python:3.12-slim
    container_name: r3-node-nas
    restart: unless-stopped
    ports:
      - "8004:8000"   # porta 8004 sul NAS (non conflitto con altri nodi)
    volumes:
      - /volume1/sdq1/r3:/app
      - /volume1/sdq1/r3/data/node-nas:/data
    working_dir: /app
    environment:
      R3_API_TOKEN: ${R3_API_TOKEN:-changeme-nas}
      R3_NODE_ID: node-nas
      R3_DATA_DIR: /data
      R3_PEERS: "http://IP_SERVER_PRINCIPALE:8001,http://IP_SERVER_PRINCIPALE:8002"
    command: >
      sh -c "pip install -r requirements.txt -q &&
             uvicorn node:app --host 0.0.0.0 --port 8000"
```

Deploy:
```bash
cd /volume1/sdq1/r3
docker compose -f docker-compose-nas.yml up -d
```

---

### 5. Backup automatico del repo Git

Script `/volume1/sdq1/scripts/backup_repo.sh`:

```bash
#!/bin/bash
# Backup repo Claudio → NAS ogni 6 ore
REPO_DIR="/volume1/sdq1/repo/Claudio"
BACKUP_DIR="/volume1/sdq1/backups"
LOG_FILE="/volume1/sdq1/logs/backup.log"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"

TIMESTAMP=$(date +%Y-%m-%d_%H-%M)

echo "[$TIMESTAMP] Inizio backup repo..." >> "$LOG_FILE"

# Clone o pull
if [ -d "$REPO_DIR/.git" ]; then
    cd "$REPO_DIR" && git pull origin main >> "$LOG_FILE" 2>&1
else
    git clone "https://${GITHUB_TOKEN}@github.com/claudioterzi/Claudio.git" "$REPO_DIR" >> "$LOG_FILE" 2>&1
fi

# Crea snapshot tar
tar -czf "$BACKUP_DIR/repo_${TIMESTAMP}.tar.gz" "$REPO_DIR" >> "$LOG_FILE" 2>&1

# Mantieni solo gli ultimi 30 backup
ls -t "$BACKUP_DIR"/repo_*.tar.gz | tail -n +31 | xargs rm -f >> "$LOG_FILE" 2>&1

echo "[$TIMESTAMP] Backup completato" >> "$LOG_FILE"
```

Aggiungi a DSM → Control Panel → Task Scheduler:
- Tipo: Script utente
- Schedule: ogni 6 ore
- Script: `bash /volume1/sdq1/scripts/backup_repo.sh`

---

### 6. Mirror Google Drive → NAS

```bash
# Installa rclone sul NAS via SSH
curl -O https://downloads.rclone.org/rclone-current-linux-amd64.zip
unzip rclone-current-linux-amd64.zip
cp rclone-*/rclone /usr/local/bin/
chmod +x /usr/local/bin/rclone

# Configura Drive
rclone config
# → n (new remote)
# → nome: gdrive
# → tipo: drive (Google Drive)
# → segui OAuth sul browser

# Test
rclone ls gdrive:

# Sync Drive → NAS (ogni notte)
rclone sync "gdrive:Agorà Digitale — SDQ-1" /volume1/sdq1/drive_mirror/ \
  --log-file /volume1/sdq1/logs/rclone.log \
  --log-level INFO
```

Task Scheduler DSM → ogni notte alle 3:00:
```bash
/usr/local/bin/rclone sync "gdrive:Agorà Digitale — SDQ-1" /volume1/sdq1/drive_mirror/ --log-file /volume1/sdq1/logs/rclone.log
```

---

### 7. VPN Tailscale per accesso remoto

Tailscale permette di accedere al NAS da qualsiasi posto del mondo come se fosse in rete locale.

```bash
# Sul NAS via SSH
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up --authkey=INSERISCI_AUTH_KEY_TAILSCALE
```

Auth key: vai su tailscale.com → Settings → Keys → Generate auth key.

Dopo l'installazione:
- Il NAS appare nella rete Tailscale come `synology-ds223`
- Puoi accedere da Bruxelles, aeroporto, ovunque con `http://100.x.x.x:5000`
- Nessuna porta aperta su internet (più sicuro di port forwarding)

---

### 8. Struttura cartelle NAS

```
/volume1/sdq1/
├── r3/               ← Codice nodo R3∞ + data nodo-nas
├── repo/             ← Mirror repo GitHub (backup)
│   └── Claudio/
├── drive_mirror/     ← Mirror Google Drive (backup)
│   └── Agora Digitale/
├── backups/          ← Snapshot tar del repo (30 giorni)
├── scripts/          ← Script di automazione
│   └── backup_repo.sh
└── logs/             ← Log di tutti i processi
    ├── backup.log
    └── rclone.log
```

---

### 9. Monitoraggio salute nodo

Il NAS risponde su `http://192.168.1.188:8004/health` quando il container R3 è attivo.

Il heartbeat ARGO già monitora node-a, node-b, archive.
**Aggiungere node-nas** nell'ARGO heartbeat:

```javascript
// In argo_heartbeat.gs
const NODE_NAS_URL = "http://192.168.1.188:8004";  // o IP Tailscale
```

---

### 10. Riepilogo porte usate

| Servizio | Porta locale | Accessibile da |
|---|---|---|
| DSM (interfaccia) | 5000 (HTTP), 5001 (HTTPS) | Rete locale + Tailscale |
| Nodo R3∞ | 8004 | Rete locale + Tailscale |
| SSH | 22 | Rete locale + Tailscale |

**Non aprire porte su internet.** Usa solo Tailscale per accesso remoto.

---

*NAS-010 completato — 2026-06-20*
*SDQ-1 / Claudio Terzi, Bruxelles*
