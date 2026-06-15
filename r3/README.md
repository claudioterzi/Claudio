# R³∞ — Knowledge Redundancy System

> *"La conoscenza che sopravvive a chi la crea è l'unica vera conoscenza."*

**R³∞** is a minimal, self-healing document redundancy system. Upload a file once — it survives the loss of any single node, with automatic integrity verification and recovery. No blockchain. No cloud vendor. No single point of failure.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green.svg)](https://fastapi.tiangolo.com)
[![License: R³∞ KRL v1.0](https://img.shields.io/badge/license-R³∞%20KRL%20v1.0-red.svg)](./MOTION_PUBBLICA.md)

---

## Why

Every document you care about lives in one place. One disk failure, one company shutdown, one jurisdiction decision — and it's gone.

R³∞ is the answer to a simple question: *what is the minimum system needed to guarantee a document survives?*

The answer: **three independent nodes, SHA-256 content addressing, bidirectional sync, and hourly integrity checks.**

---

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   NODE A     │◄───►│   NODE B     │◄───►│   ARCHIVE    │
│  (Primary)   │     │ (Secondary)  │     │(Independent) │
└──────────────┘     └──────────────┘     └──────────────┘
      ▲                     ▲                     ▲
      └─────────────────────┴─────────────────────┘
             Bidirectional sync (5 min)
             Integrity verification (1 hour)
             Automatic repair
```

Each node runs the same `node.py` — no master, no coordination service, no shared state beyond the documents themselves.

---

## How it works

| Step | What happens |
|------|-------------|
| **Upload** | `POST /documents` → file saved to disk, ID = SHA-256 of content, Ed25519 signature recorded in SQLite |
| **Sync** | `sync.py` runs every 5 min: compares hash lists between nodes, pulls what's missing, pushes what the peer lacks |
| **Verify** | Every hour: recomputes SHA-256 of every file on disk, compares to DB — any mismatch triggers pull from peer |
| **Recover** | Corrupted or missing file → automatically restored from the first healthy peer found |

Documents are **content-addressed**: the ID *is* the SHA-256 hash. You cannot have a document with a given ID that isn't exactly that content.

---

## Quickstart (Docker — 3 nodes in 60 seconds)

```bash
git clone https://github.com/claudioterzi/Claudio
cd Claudio
docker compose -f r3/docker-compose.yml up -d
```

Three nodes running on ports 8001 (A), 8002 (B), 8003 (Archive).

```bash
# Upload a document
curl -X POST http://localhost:8001/documents \
  -H "Authorization: Bearer changeme" \
  -F "file=@myfile.txt"
# → {"id": "sha256...", "signature": "ed25519...", "size": 1234}

# Verify it replicated (after sync)
curl -H "Authorization: Bearer changeme" \
  http://localhost:8002/sync/hashes

# Run sync manually
R3_LOCAL_URL=http://localhost:8001 \
R3_PEERS=http://localhost:8002,http://localhost:8003 \
R3_API_TOKEN=changeme \
python r3/sync.py
```

---

## Quickstart (no Docker)

```bash
pip install fastapi uvicorn httpx PyNaCl python-multipart

# Node A
R3_NODE_ID=node-a R3_API_TOKEN=secret R3_DATA_DIR=data/a \
  uvicorn r3.node:app --port 8001

# Node B (different machine or terminal)
R3_NODE_ID=node-b R3_API_TOKEN=secret R3_DATA_DIR=data/b \
R3_PEERS=http://localhost:8001 \
  uvicorn r3.node:app --port 8002
```

---

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/documents` | Upload document |
| `GET` | `/documents/{id}` | Download document |
| `GET` | `/documents/{id}/info` | Metadata |
| `GET` | `/sync/hashes` | Hash list for sync comparison |
| `POST` | `/sync/receive` | Receive document from peer |
| `GET` | `/status` | Node status + Ed25519 verify key |
| `GET` | `/health` | Health check (no auth) |

All endpoints except `/health` require `Authorization: Bearer <token>`.

---

## Security

- **Integrity**: every document has ID = SHA-256(content). Verification is implicit.
- **Authenticity**: each node signs documents with a persistent Ed25519 key (PyNaCl). Public key exposed via `GET /status`.
- **Auth**: static Bearer token per deployment. Rotate via `R3_API_TOKEN` env var.
- **Audit**: append-only `audit_log` table in SQLite. Every upload, sync, and integrity event recorded.

---

## Success criteria (MVP)

The system is considered working if:

1. A document uploaded to A is present on B and Archive within 10 minutes
2. After 7 days, all documents have valid hashes on all nodes
3. Shutting down A: B becomes primary within 15 minutes (via `sync.py --loop`)
4. A offline for 1 hour, then restarted: re-syncs without data loss
5. File manually corrupted on A: detected and restored from B within 1 hour

---

## What it is NOT

R³∞ is deliberately minimal. It does **not** include:

- ❌ Blockchain / tokens
- ❌ Steganography or anonymization
- ❌ Dead man switches
- ❌ P2P mesh
- ❌ GUI
- ❌ Auto-deploy to cloud providers

These are features for later. The core must work first.

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `R3_NODE_ID` | `node-a` | Node identifier |
| `R3_API_TOKEN` | `changeme` | Auth token (change this) |
| `R3_DATA_DIR` | `data` | Storage directory |
| `R3_PEERS` | *(empty)* | Comma-separated peer URLs |
| `R3_SYNC_INTERVAL` | `300` | Sync interval (seconds) |
| `R3_INTEGRITY_INTERVAL` | `3600` | Integrity check interval |

---

## Stack

- **Python 3.10+** — FastAPI, uvicorn, httpx, PyNaCl
- **Storage** — file system + SQLite (zero external dependencies)
- **Docker** — optional but recommended for multi-node setup

---

## License

**R³∞ Knowledge Resilience License v1.0**

Use it, fork it, deploy it. Keep the redundancy (minimum 3 nodes). Don't remove verification mechanisms. Share security improvements.

---

## Author

**Claudio Terzi** — [terziclaudio@gmail.com](mailto:terziclaudio@gmail.com) · Bruxelles  
Part of the [SDQ-1](https://github.com/claudioterzi/Claudio) project.

*Built in a session. Designed to outlast it.*
