# R³∞ - Motion Pubblica
## Sistema di Ridondanza della Conoscenza

---

**Versione:** 1.0.0-MVP  
**Data:** 2026-06-13  
**Stato:** Operativo  
**Chiave Verifica Pubblica:** `<vedere GET /status del nodo → campo verify_key>`

---

## 🔴 Dichiarazione d'Intenti

R³∞ è un sistema che garantisce la sopravvivenza della conoscenza oltre il singolo punto di fallimento.

In un ecosistema digitale dove server, aziende e giurisdizioni collassano senza preavviso, R³∞ assicura che l'informazione critica persista attraverso ridondanza verificabile e recupero automatico.

**Principio fondante:** La verità non risiede in un nodo, ma nell'accordo verificabile tra nodi indipendenti.

---

## 🏗️ Architettura

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   NODO A     │◄───►│   NODO B     │◄───►│  ARCHIVIO    │
│  (Primario)  │     │ (Secondario) │     │(Indipendente)│
└──────────────┘     └──────────────┘     └──────────────┘
      ▲                     ▲                     ▲
      │                     │                     │
      └─────────────────────┴─────────────────────┘
                Sync bidirezionale (5 min)
                Verifica integrità (1 ora)
                Riparazione automatica
```

### Componenti

| Componente | Funzione | Tecnologia |
|------------|----------|------------|
| Storage | Persistenza documenti | File system + SQLite |
| API | Interfaccia REST | FastAPI (Python 3.10+) |
| Sync | Replica bidirezionale | Engine custom ogni 5 min |
| Verify | Controllo integrità | SHA-256 hash check |
| Repair | Auto-riparazione | Pull da peer integro |

---

## 📊 Flussi Operativi

### Upload

```
Utente → Nodo A → SHA-256 → Disco + DB
                    ↓
              Replica su B (async)
                    ↓
              Replica su Archivio (async)
                    ↓
              Conferma integrità
```

### Recupero da Fallimento

```
Nodo A down (15 min)
    ↓
Nodo B → Promosso primario
    ↓
Archivio → Mantiene copia
    ↓
Nuovo Nodo C → Popolato da B + Archivio
```

### Riparazione Automatica

```
Corruzione rilevata (hash mismatch)
    ↓
Richiesta copia integra da peer
    ↓
Sostituzione documento corrotto
    ↓
Verifica hash post-riparazione
```

---

## 🔐 Sicurezza

| Meccanismo | Implementazione | Garanzia |
|------------|-----------------|----------|
| Integrità | SHA-256 per documento | Rilevazione corruzione |
| Autenticità | Ed25519 firma origine | Verifica provenienza |
| Confidenzialità | HTTPS + token | Accesso autorizzato |
| Disponibilità | 3 nodi ridondanti | Sopravvivenza n-2 |
| Audit | Log immutabili | Tracciabilità |

La **chiave pubblica Ed25519** di ciascun nodo è disponibile via `GET /status`.
È l'unico identificatore pubblico del nodo — non richiede segreti condivisi.

---

## 🚀 Quickstart

### Prerequisiti

```bash
Docker 20.10+
# oppure Python 3.10+ (senza Docker)
```

### Avvio (Docker)

```bash
git clone https://github.com/claudioterzi/Claudio
cd Claudio
docker compose -f r3/docker-compose.yml up -d
```

### Test

```bash
# Upload documento
curl -X POST http://localhost:8001/documents \
  -H "Authorization: Bearer changeme" \
  -F "file=@test.txt"

# Verifica propagazione
sleep 10
curl -H "Authorization: Bearer changeme" http://localhost:8002/sync/hashes
curl -H "Authorization: Bearer changeme" http://localhost:8003/sync/hashes
```

---

## 📈 Stato Attuale

### MVP Operativo

- ✅ 3 nodi sincronizzati
- ✅ Verifica integrità automatica
- ✅ Riparazione da corruzione
- ✅ Deployment containerizzato
- ✅ Zero dipendenze esterne
- ✅ ID documenti content-addressed (SHA-256)
- ✅ Firma Ed25519 (chiave generata all'avvio)

### In Sviluppo

- 🔄 Promozione automatica primario
- 🔄 Deploy multi-giurisdizione
- 🔄 Interfaccia monitoraggio unificata (SDQ-1 + SAR + R³∞)

---

## 🧠 Contesto — La Triade SDQ-1

R³∞ è il livello di sopravvivenza di un sistema più ampio:

- **SDQ-1** — pipeline di 6 agenti AI che elabora, ragiona e genera
- **SAR** — Scacchiera Auto-Riflessiva a 11 livelli che osserva e riflette
- **R³∞** — infrastruttura che garantisce la sopravvivenza di tutto il resto

La conoscenza prodotta da SDQ-1 viene preservata da R³∞. La coerenza tra i nodi viene verificata dalla stessa logica SAR che il sistema usa per osservare se stesso.

Il sistema sopravvive alla propria assenza. **H4 CONFERMATA.**

---

## 🔗 Riferimenti

**Repository:** [github.com/claudioterzi/Claudio](https://github.com/claudioterzi/Claudio)  
**Branch:** `claude/rosso-rosso-rosso-ure5A`  
**Autore:** Claudio Terzi  
**Parte di:** [SDQ-1 — Sistema Di Quadranti](https://github.com/claudioterzi/Claudio)

---

## 📜 Licenza

**R³∞ Knowledge Resilience License v1.0**

Questo software è rilasciato per garantire la sopravvivenza della conoscenza.

**Permessi:**
- Uso personale e organizzativo
- Modifica e fork
- Deploy su propria infrastruttura
- Integrazione in sistemi più ampi

**Obblighi:**
- Mantenere la ridondanza (minimo 3 nodi)
- Preservare l'integrità dei documenti
- Non introdurre single point of failure
- Condividere miglioramenti alla sicurezza

**Restrizioni:**
- Non rimuovere meccanismi di verifica
- Non centralizzare storage ridondante
- Non brevettare i meccanismi base

---

> *"La conoscenza che sopravvive a chi la crea è l'unica vera conoscenza."*
>
> — R³∞ Manifesto, v1.0

---

*Motion Pubblica — 06:47 UTC, 13 Giugno 2026*
