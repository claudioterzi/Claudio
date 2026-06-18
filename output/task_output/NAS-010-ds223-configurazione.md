# NAS-010 — Configurazione Synology DS223 come Nodo SDQ-1
*Completato automaticamente da Agente Orario SDQ-1 — 2026-06-18*

---

## 1. Setup Iniziale DS223

### Accesso iniziale
- IP locale: **192.168.1.188**
- Accesso DSM: http://192.168.1.188:5000 (o https://192.168.1.188:5001)
- Username predefinito: `admin`

### Configurazione DSM 7.x
```
1. Aggiornamento DSM all'ultima versione stabile
   DSM > Pannello di Controllo > Aggiornamento DSM > Verifica aggiornamenti

2. Creazione utente dedicato sdq1
   DSM > Pannello di Controllo > Utenti > Crea
   - Username: sdq1
   - Password: [password sicura]
   - Gruppi: administrators (per Docker), users
   - Cartella home: abilitata

3. Cartelle condivise necessarie:
   - /volume1/sdq1-repo       ← clone del repository
   - /volume1/sdq1-output     ← output degli script
   - /volume1/sdq1-backups    ← backup del sistema
   - /volume1/drive-mirror    ← mirror Google Drive

4. Permessi cartelle:
   sdq1 user → Lettura/Scrittura su tutte e 4 le cartelle
```

---

## 2. Docker su Synology

### Installazione Container Manager
```
DSM > Package Center > Cerca "Container Manager" > Installa
```

### docker-compose.yml per SDQ-1
Salva in `/volume1/sdq1-repo/docker-compose.yml`:

```yaml
version: "3.8"

services:
  sdq1:
    image: python:3.11-slim
    container_name: sdq1-nodo
    restart: unless-stopped
    
    volumes:
      - /volume1/sdq1-repo:/app          # Repository clonato
      - /volume1/sdq1-output:/app/output  # Output persistente
      - /volume1/sdq1-backups:/app/backups
    
    working_dir: /app
    
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - TZ=Europe/Brussels
    
    # Installa dipendenze all'avvio
    command: >
      sh -c "pip install --no-cache-dir -r requirements.txt &&
             tail -f /dev/null"
    
    # Limiti risorse (DS223 ha risorse limitate)
    deploy:
      resources:
        limits:
          memory: 512M

  # File .env (NON committare nel repo!)
  # Crea /volume1/sdq1-repo/.env con le API key
```

### File .env locale sul NAS
```bash
# /volume1/sdq1-repo/.env
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
DEEPSEEK_API_KEY=sk-...
```

### Avvio container
```bash
# Via SSH sul NAS (vedi sezione sicurezza per abilitare SSH)
cd /volume1/sdq1-repo
docker compose up -d

# Verifica
docker ps
docker logs sdq1-nodo
```

---

## 3. Clone e Sync Automatico del Repository

### Configurazione SSH key per GitHub (read-only)

```bash
# 1. SSH sul NAS
ssh sdq1@192.168.1.188

# 2. Genera chiave SSH dedicata
ssh-keygen -t ed25519 -C "sdq1-nas-ds223" -f ~/.ssh/id_ed25519_github -N ""

# 3. Visualizza chiave pubblica
cat ~/.ssh/id_ed25519_github.pub
# → Copia questa chiave

# 4. Vai su GitHub → claudioterzi/Claudio → Settings → Deploy Keys
# → Add Deploy Key: incolla la chiave pubblica
# → Titolo: "DS223 NAS SDQ-1"
# → Allow write access: NO (solo lettura, più sicuro)

# 5. Configura SSH per usare questa chiave per GitHub
cat > ~/.ssh/config << 'EOF'
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_github
EOF

# 6. Clone iniziale
git clone git@github.com:claudioterzi/Claudio.git /volume1/sdq1-repo
```

### Script di sync automatico
Crea `/volume1/sdq1-repo/scripts/nas_sync.sh`:

```bash
#!/bin/bash
# NAS Sync Script — aggiorna il repo ogni ora
# Logs in /volume1/sdq1-output/nas_sync.log

LOG="/volume1/sdq1-output/nas_sync.log"
REPO="/volume1/sdq1-repo"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Inizio sync..." >> "$LOG"

cd "$REPO" || exit 1

# Pull ultime modifiche
git pull origin main >> "$LOG" 2>&1

if [ $? -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Sync completato" >> "$LOG"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERRORE sync" >> "$LOG"
fi

# Rotazione log (max 1MB)
if [ $(wc -c < "$LOG") -gt 1048576 ]; then
    tail -1000 "$LOG" > "${LOG}.tmp" && mv "${LOG}.tmp" "$LOG"
fi
```

```bash
chmod +x /volume1/sdq1-repo/scripts/nas_sync.sh
```

### Task Scheduler in DSM

```
DSM > Pannello di Controllo > Task Scheduler > Crea > Task pianificato > Script definito dall'utente

Impostazioni:
- Nome: SDQ-1 Repo Sync
- Utente: sdq1
- Pianificazione: Ogni ora (ogni giorno, ogni ora)
- Comando: /volume1/sdq1-repo/scripts/nas_sync.sh
- Email notifica errori: terziclaudio@gmail.com
```

---

## 4. Tailscale VPN

### Installazione via Docker (metodo più affidabile su Synology)

```yaml
# Aggiungi al docker-compose.yml:
  tailscale:
    image: tailscale/tailscale:latest
    container_name: tailscale-nas
    hostname: claudio-nas-ds223
    restart: unless-stopped
    network_mode: host
    cap_add:
      - NET_ADMIN
      - NET_RAW
    volumes:
      - /volume1/docker/tailscale:/var/lib/tailscale
    environment:
      - TS_AUTHKEY=${TAILSCALE_AUTH_KEY}  # Da tailscale.com/settings/keys
      - TS_EXTRA_ARGS=--advertise-exit-node
      - TS_STATE_DIR=/var/lib/tailscale
```

### Configurazione Tailscale
```bash
# Ottieni auth key da: https://login.tailscale.com/admin/settings/keys
# → Generate auth key → Tag: tag:nas → Expiry: 90 days

# Aggiungi al .env del NAS:
TAILSCALE_AUTH_KEY=tskey-auth-xxxxx

# Avvia
docker compose up -d tailscale

# Verifica connessione
docker exec tailscale-nas tailscale status
# → claudio-nas-ds223  100.x.x.x  Synology  ✓ connected
```

### MagicDNS
Nel pannello Tailscale (tailscale.com):
- DNS → Enable MagicDNS
- Il NAS sarà raggiungibile come: `claudio-nas-ds223.tail-xxx.ts.net`

### Accesso da iPhone
1. Installa Tailscale su iPhone
2. Login con stesso account
3. Accedi al NAS: `http://claudio-nas-ds223.tail-xxx.ts.net:5000`
4. SSH: `ssh sdq1@claudio-nas-ds223`

---

## 5. Backup Google Drive

### Configurazione Cloud Sync in DSM

```
DSM > Package Center > Installa "Cloud Sync"

Configurazione nuova task:
- Provider: Google Drive
- Account: terziclaudio@gmail.com
- Cartella locale: /volume1/sdq1-output
- Cartella remota (Drive): SDQ-1 Output
- Direzione: Bidirezionale (o solo Upload se non vuoi sync inverso)
- Pianificazione: Ogni 6 ore
- Crittografia: abilitata (opzionale, con password)
```

### Backup specifico output task
Crea `/volume1/sdq1-repo/scripts/nas_backup_drive.sh`:

```bash
#!/bin/bash
# Sync output verso Google Drive (usa rsync locale + Cloud Sync)
TIMESTAMP=$(date '+%Y%m%d_%H%M')
BACKUP_DIR="/volume1/sdq1-backups/snapshots"

mkdir -p "$BACKUP_DIR"

# Snapshot locale compresso
tar -czf "${BACKUP_DIR}/snapshot_${TIMESTAMP}.tar.gz" \
    /volume1/sdq1-repo/output/ \
    /volume1/sdq1-repo/TASK_AUTONOMI.md \
    /volume1/sdq1-repo/MEMORIA_PROGETTO.md

# Cloud Sync si occupa del resto automaticamente
echo "[$(date)] Snapshot creato: snapshot_${TIMESTAMP}.tar.gz"

# Pulisci snapshot più vecchi di 30 giorni
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
```

---

## 6. Esecuzione Script SDQ-1 sul NAS

### Script agente_orario sul NAS

```
DSM > Pannello di Controllo > Task Scheduler > Crea

Task 1: Agente Orario (locale)
- Nome: SDQ-1 Agente Orario NAS
- Pianificazione: Ogni ora (07:00-23:00)
- Comando: docker exec sdq1-nodo python scripts/agente_orario.py
- Output: /volume1/sdq1-output/nas_agente.log

Task 2: Studio Notturno
- Nome: SDQ-1 Studio Notturno NAS
- Pianificazione: Ogni giorno alle 02:00
- Comando: docker exec sdq1-nodo python scripts/studio_notturno.py
- Output: /volume1/sdq1-output/nas_studio.log
```

**Nota:** Il NAS esegue gli script **in aggiunta** a GitHub Actions, non in sostituzione. Se GitHub Actions fallisce (API down, runner occupato), il NAS garantisce continuità.

---

## 7. Backup del NAS con Hyper Backup

```
DSM > Package Center > Installa "Hyper Backup"

Configurazione:
- Destinazione: Google Drive (account Claudio)
  - Cartella: NAS-DS223-HyperBackup
- Cartelle da fare il backup:
  - /volume1/sdq1-repo
  - /volume1/sdq1-output
  - /volume1/sdq1-backups
- Pianificazione: Ogni giorno alle 03:00
- Retention: 30 versioni
- Notifiche: email su fallimento
```

---

## 8. Checklist Sicurezza

### Firewall DSM
```
DSM > Pannello di Controllo > Sicurezza > Firewall

Regole consigliate:
- Nega tutto di default
- Consenti porte LAN (192.168.1.0/24):
  5000 (HTTP DSM), 5001 (HTTPS DSM), 22 (SSH)
- Consenti porte Tailscale: solo tramite VPN
- Blocca accesso diretto da internet (tutto il traffico esterno via Tailscale)
```

### 2FA per DSM
```
DSM > Pannello di Controllo > Utenti > (utente admin) > Account > Abilita autenticazione a 2 fattori
App consigliata: Google Authenticator o Authy
```

### Porte aperte verso internet
**ZERO** porte aperte verso internet direttamente. Tutto via Tailscale VPN. Il NAS non deve essere raggiungibile da internet pubblico.

```bash
# Verifica: nessuna porta esposta su internet
# Dal router: DMZ → disabilitato, Port Forwarding → vuoto per DS223
```

### SSH sicuro
```bash
# /etc/ssh/sshd_config sul NAS
PermitRootLogin no          # Mai root via SSH
PasswordAuthentication no   # Solo chiave SSH
AllowUsers sdq1             # Solo utente sdq1
Port 22                     # Considera di cambiare porta (es. 2222)
```

---

## 9. Monitoring e Alert

### Notifiche via email (DSM nativo)
```
DSM > Pannello di Controllo > Notifiche > Email
- SMTP: smtp.gmail.com:587 (TLS)
- Account: terziclaudio@gmail.com
- Abilita notifiche per: errori disco, temperatura, task falliti
```

### Script monitoring SDQ-1
Crea `/volume1/sdq1-repo/scripts/nas_health.sh`:

```bash
#!/bin/bash
# Monitoring salute SDQ-1 NAS — invia alert se problemi

ALERT_EMAIL="terziclaudio@gmail.com"
LOG="/volume1/sdq1-output/nas_health.log"

check_container() {
    if ! docker ps | grep -q "sdq1-nodo"; then
        echo "ALERT: Container sdq1-nodo non attivo!" | mail -s "SDQ-1 NAS Alert" "$ALERT_EMAIL"
        docker compose -f /volume1/sdq1-repo/docker-compose.yml up -d sdq1
        echo "[$(date)] Container riavviato automaticamente" >> "$LOG"
    fi
}

check_disk() {
    USAGE=$(df /volume1 | awk 'NR==2 {print $5}' | tr -d '%')
    if [ "$USAGE" -gt 85 ]; then
        echo "ALERT: Disco /volume1 al ${USAGE}%" | mail -s "SDQ-1 NAS Disco Pieno" "$ALERT_EMAIL"
    fi
}

check_last_output() {
    # Verifica che l'agente orario abbia prodotto output nelle ultime 2 ore
    LAST_MOD=$(find /volume1/sdq1-output -name "*.md" -newer /tmp/sentinel 2>/dev/null | wc -l)
    touch /tmp/sentinel
    if [ "$LAST_MOD" -eq 0 ] && [ "$(date +%H)" -gt 9 ] && [ "$(date +%H)" -lt 22 ]; then
        echo "ALERT: Nessun output SDQ-1 nelle ultime 2 ore" | mail -s "SDQ-1 Silenzio" "$ALERT_EMAIL"
    fi
}

check_container
check_disk
check_last_output

echo "[$(date)] Health check OK" >> "$LOG"
```

### Task Scheduler — Health Check
```
Nome: SDQ-1 Health Check
Pianificazione: Ogni 2 ore
Comando: /volume1/sdq1-repo/scripts/nas_health.sh
```

---

## 10. Riepilogo Architettura NAS

```
DS223 (192.168.1.188)
│
├── Tailscale VPN ──────────────────── Accesso remoto sicuro (iPhone, PC)
│
├── Docker
│   ├── sdq1-nodo (Python 3.11)
│   │   ├── agente_orario.py (ogni ora)
│   │   └── studio_notturno.py (02:00)
│   └── tailscale (VPN client)
│
├── Task Scheduler (DSM)
│   ├── nas_sync.sh (ogni ora) ──────── git pull da GitHub
│   ├── nas_backup_drive.sh (ogni 6h) ─ snapshot → Drive
│   └── nas_health.sh (ogni 2h) ──────── monitoring
│
├── Cloud Sync
│   └── /volume1/sdq1-output → Google Drive/SDQ-1 Output
│
└── Hyper Backup
    └── Backup completo → Google Drive/NAS-DS223 (ogni notte)
```

---

*Documentazione: Synology DSM 7.x Help, Tailscale docs, Docker Compose v3 spec*
