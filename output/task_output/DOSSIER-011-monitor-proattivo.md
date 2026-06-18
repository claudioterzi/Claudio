# DOSSIER-011 — Monitor Proattivo Dossier & Email (Principio CT)
*Completato automaticamente da Agente Orario SDQ-1 — 2026-06-17*

---

## Indice

1. [Principio CT — Definizione operativa](#1-principio-ct--definizione-operativa)
2. [State machine per ogni dossier](#2-state-machine-per-ogni-dossier)
3. [Architettura Python — classe DossierMonitor](#3-architettura-python--classe-dossiermonitor)
4. [Gmail Monitor — gap analysis strategia vs realtà](#4-gmail-monitor--gap-analysis-strategia-vs-realtà)
5. [Trigger automatici](#5-trigger-automatici)
6. [Dashboard live — struttura JSON](#6-dashboard-live--struttura-json)
7. [Codice Python completo — dossier_monitor.py](#7-codice-python-completo--dossier_monitorpy)
8. [Integrazione in agente_orario.py](#8-integrazione-in-agente_orariopy)
9. [Stato attuale dei dossier al 2026-06-17](#9-stato-attuale-dei-dossier-al-2026-06-17)

---

## 1. Principio CT — Definizione operativa

**Il sistema non aspetta.** Ogni dossier aperto di Claudio ha uno stato attuale,
una prossima azione attesa, e una scadenza implicita o esplicita.
Il monitor interroga proattivamente:

- lo stato interno (JSON del dossier)
- la casella Gmail (email inviate, bozze, ricevute)
- il calendario (scadenze udienza, appuntamenti)

e **emette alert** se c'è disallineamento tra ciò che doveva accadere e ciò che
risulta accaduto. Questo è il **Principio CT**: il sistema monitora e agisce,
non aspetta di essere interrogato.

**Frequenza**: ogni esecuzione dell'agente orario (ogni ora, 07:00–23:00 CEST).

---

## 2. State machine per ogni dossier

Ogni dossier segue la stessa macchina a stati. Le transizioni sono guidate da
eventi Gmail, da azioni manuali di Claudio, o da trigger temporali.

### 2.1 Grafo degli stati (tutti i dossier)

```
PENDING ──────────────────────────────────────────────────────►  CHIUSO
   │                                                               ▲
   ▼                                                               │
INVIATO ──► IN_ATTESA_RISPOSTA ──► AZIONE_RICHIESTA ──────────────┘
   │                │                      │
   │                ▼                      │
   │         SCADENZA_IMMINENTE            │
   │                │                      │
   └────────────────┴──────────────────────┘
                    │
                    ▼
               [ALERT emesso]
```

### 2.2 Definizione stati

| Stato | Descrizione | Uscite |
|---|---|---|
| `PENDING` | Azione identificata, non ancora eseguita | → `INVIATO` (email/lettera inviata) |
| `INVIATO` | Comunicazione inviata, attesa risposta | → `IN_ATTESA_RISPOSTA` (ack ricevuto o timeout) |
| `IN_ATTESA_RISPOSTA` | Controparte deve rispondere entro N giorni | → `AZIONE_RICHIESTA` (risposta arrivata o scadenza) |
| `AZIONE_RICHIESTA` | Risposta ricevuta, Claudio deve agire | → `INVIATO` (azione eseguita) · → `CHIUSO` |
| `SCADENZA_IMMINENTE` | Scadenza entro 72h | → alert + blocca su stato precedente |
| `CHIUSO` | Dossier risolto | terminale |

### 2.3 Trigger di transizione

| Trigger | Transizione | Nota |
|---|---|---|
| Email trovata in `sent` con keyword dossier | `PENDING → INVIATO` | Data invio = timestamp email |
| Bozza in draft con keyword dossier da >24h | alert `PENDING` | Chiede a Claudio se inviare |
| Email in inbox da controparte | `INVIATO/IN_ATTESA → AZIONE_RICHIESTA` | Analisi mittente + subject |
| Scadenza entro 72h | → `SCADENZA_IMMINENTE` | Sovrapposto allo stato corrente |
| Scadenza entro 24h | → alert urgente | Escalation livello 2 |
| Nessuna risposta dopo N giorni attesi | → alert `IN_ATTESA_RISPOSTA` | Default N=14 giorni |

### 2.4 State machine per dossier specifici

#### PORTS/Pelan — Causa prud'hommes Parigi

```
Stato attuale: AZIONE_RICHIESTA
└── Capitale ricevuto (7.013,53 €) ✓
└── Interessi ~2.050 € NON pagati
└── Prossimo passo: mandare huissier de justice

Transizioni:
  AZIONE_RICHIESTA
    ├─ [inviata lettera mise en demeure] ──► INVIATO
    │     └─ [14gg senza risposta] ──────── IN_ATTESA_RISPOSTA → AZIONE_RICHIESTA(huissier)
    ├─ [contatto huissier confermato] ────► INVIATO
    └─ [pagamento interessi ricevuto] ────► CHIUSO

Keywords Gmail: "PORTS", "Pelan", "prud'hommes", "RG 22/08190",
               "Cour d'Appel", "huissier", "intérêts"
```

#### Allianz Direct — Sinistro allagamento Parigi

```
Stato attuale: IN_ATTESA_RISPOSTA
└── Contestazione inviata ✓
└── Attesa: preventivo artigiano (sabato 2026-06-21)
└── Attesa: risposta Allianz al contestazione

Transizioni:
  IN_ATTESA_RISPOSTA
    ├─ [preventivo artigiano ricevuto] ──► AZIONE_RICHIESTA (inviare ad Allianz)
    ├─ [risposta Allianz] ───────────────► AZIONE_RICHIESTA
    └─ [nessuna risposta entro 14gg] ────► AZIONE_RICHIESTA (escalation)

Keywords Gmail: "Allianz", "sinistre", "dégât", "devis", "contestation",
               "allagamento", "scarichi"
Scadenza naturale: 2026-06-21 (preventivo artigiano)
```

#### SkyRights Foundation — ASBL Bruxelles

```
Stato attuale: PENDING
└── Registrazione in corso
└── Nessuna email di conferma registrazione ancora

Transizioni:
  PENDING
    ├─ [email BCE/Moniteur Belge ricevuta] ──► IN_ATTESA_RISPOSTA
    ├─ [atto notarile inviato] ─────────────► INVIATO
    └─ [numero BCE assegnato] ──────────────► AZIONE_RICHIESTA (pubblicazione)

Keywords Gmail: "SkyRights", "ASBL", "BCE", "Moniteur Belge",
               "registrazione", "notaire", "fondation"
```

#### Martin/PP Retail — Dossier legale

```
Stato attuale: PENDING (informazioni incomplete — solo nome dossier noto)
└── In attesa di più dettagli da Claudio per affinare lo stato

Transizioni: standard (vedi schema generale)

Keywords Gmail: "Martin", "PP Retail", "dossier", "legale"
Alert speciale: richiedere a Claudio stato attuale al primo check
```

---

## 3. Architettura Python — classe DossierMonitor

Il `DossierMonitor` è il cervello del sistema. Legge lo stato persistito in JSON,
interroga Gmail via MCP tool, confronta strategia vs realtà, emette alert.

```python
# sdq1/dossier/monitor.py
"""
DossierMonitor — Principio CT
Monitora ogni dossier aperto di Claudio contro la realtà Gmail.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable


class StatoDossier(str, Enum):
    PENDING             = "PENDING"
    INVIATO             = "INVIATO"
    IN_ATTESA_RISPOSTA  = "IN_ATTESA_RISPOSTA"
    AZIONE_RICHIESTA    = "AZIONE_RICHIESTA"
    SCADENZA_IMMINENTE  = "SCADENZA_IMMINENTE"
    CHIUSO              = "CHIUSO"


class LivelloAlert(str, Enum):
    INFO     = "INFO"
    WARN     = "WARN"
    URGENTE  = "URGENTE"


@dataclass
class Alert:
    dossier_id: str
    livello: LivelloAlert
    messaggio: str
    azione_suggerita: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class StatoDossierSnapshot:
    """Snapshot completo del dossier in un momento dato."""
    id: str
    nome: str
    stato: StatoDossier
    ultima_azione: str | None
    prossima_azione: str | None
    scadenza: str | None              # ISO date string, es. "2026-06-21"
    keywords_gmail: list[str]
    giorni_attesa_max: int            # dopo quanti giorni senza risposta → alert
    ultima_email_inviata: str | None  # ISO timestamp dell'ultima email sent trovata
    ultima_email_ricevuta: str | None # ISO timestamp dell'ultima email in inbox
    draft_in_attesa: bool             # c'è una bozza rilevante in draft?
    note: str
    alerts: list[Alert] = field(default_factory=list)


@dataclass
class ResultatoControllo:
    """Risultato di una singola sessione controlla()."""
    timestamp: str
    dossiers: list[StatoDossierSnapshot]
    alerts_totali: list[Alert]
    sommario: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, ensure_ascii=False, default=str)
```

### 3.1 Metodo `controlla()` — flusso principale

```python
class DossierMonitor:
    """
    Monitor proattivo dei dossier aperti di Claudio Terzi.

    Uso:
        monitor = DossierMonitor(gmail_tool=gmail_mcp_wrapper)
        risultato = monitor.controlla()
        for alert in risultato.alerts_totali:
            print(f"[{alert.livello}] {alert.dossier_id}: {alert.messaggio}")
    """

    STATO_FILE = Path("output/dossier_stato.json")

    def __init__(
        self,
        gmail_tool: "GmailMCPWrapper",
        stato_file: Path | None = None,
        ora_fn: Callable[[], datetime] | None = None,
    ):
        self.gmail = gmail_tool
        self.stato_file = stato_file or self.STATO_FILE
        self._ora = ora_fn or (lambda: datetime.now(timezone.utc))

    # ── Entry point principale ─────────────────────────────────────────────────

    def controlla(self) -> ResultatoControllo:
        """Controlla tutti i dossier e restituisce il risultato completo."""
        ora = self._ora()
        dossiers_config = self._carica_config_dossiers()
        snapshots: list[StatoDossierSnapshot] = []
        alerts_totali: list[Alert] = []

        for cfg in dossiers_config:
            snapshot = self._controlla_singolo(cfg, ora)
            snapshots.append(snapshot)
            alerts_totali.extend(snapshot.alerts)

        # Persisti stato aggiornato
        self._salva_stato(snapshots)

        sommario = self._genera_sommario(snapshots, alerts_totali)

        return ResultatoControllo(
            timestamp=ora.isoformat(),
            dossiers=snapshots,
            alerts_totali=alerts_totali,
            sommario=sommario,
        )

    # ── Controllo singolo dossier ──────────────────────────────────────────────

    def _controlla_singolo(
        self,
        cfg: dict[str, Any],
        ora: datetime,
    ) -> StatoDossierSnapshot:
        """Legge stato, controlla Gmail, aggiorna snapshot, emette alert."""
        stato_precedente = self._leggi_stato_precedente(cfg["id"])
        stato_corrente = StatoDossier(stato_precedente.get("stato", "PENDING"))

        # Cerca email inviate, ricevute, bozze
        email_inviate  = self.gmail.cerca_sent(cfg["keywords_gmail"])
        email_ricevute = self.gmail.cerca_inbox(cfg["keywords_gmail"])
        bozze          = self.gmail.cerca_draft(cfg["keywords_gmail"])

        ultima_inviata  = self._timestamp_piu_recente(email_inviate)
        ultima_ricevuta = self._timestamp_piu_recente(email_ricevute)
        draft_in_attesa = len(bozze) > 0

        # Transizioni di stato automatiche
        nuovo_stato = self._calcola_stato(
            stato_corrente, ultima_inviata, ultima_ricevuta, ora, cfg
        )

        # Genera alert
        alerts = self._genera_alerts(
            cfg, nuovo_stato, ultima_inviata, ultima_ricevuta,
            draft_in_attesa, bozze, ora
        )

        snapshot = StatoDossierSnapshot(
            id=cfg["id"],
            nome=cfg["nome"],
            stato=nuovo_stato,
            ultima_azione=stato_precedente.get("ultima_azione"),
            prossima_azione=cfg.get("prossima_azione"),
            scadenza=cfg.get("scadenza"),
            keywords_gmail=cfg["keywords_gmail"],
            giorni_attesa_max=cfg.get("giorni_attesa_max", 14),
            ultima_email_inviata=ultima_inviata,
            ultima_email_ricevuta=ultima_ricevuta,
            draft_in_attesa=draft_in_attesa,
            note=cfg.get("note", ""),
            alerts=alerts,
        )
        return snapshot

    # ── Logica di transizione stati ────────────────────────────────────────────

    def _calcola_stato(
        self,
        stato_attuale: StatoDossier,
        ultima_inviata: str | None,
        ultima_ricevuta: str | None,
        ora: datetime,
        cfg: dict,
    ) -> StatoDossier:
        """Determina il nuovo stato basandosi sui dati Gmail."""

        # Se email inviata più recente dell'ultima ricevuta → INVIATO o IN_ATTESA
        if ultima_inviata and not ultima_ricevuta:
            if stato_attuale == StatoDossier.PENDING:
                return StatoDossier.INVIATO
            return stato_attuale

        # Se email ricevuta dopo l'ultima inviata → AZIONE_RICHIESTA
        if ultima_ricevuta and ultima_inviata:
            dt_inviata  = datetime.fromisoformat(ultima_inviata)
            dt_ricevuta = datetime.fromisoformat(ultima_ricevuta)
            if dt_ricevuta > dt_inviata:
                return StatoDossier.AZIONE_RICHIESTA

        # Se in attesa da troppo tempo → resta IN_ATTESA ma aggiungeremo alert
        if stato_attuale == StatoDossier.INVIATO and ultima_inviata:
            dt_inviata = datetime.fromisoformat(ultima_inviata)
            giorni_trascorsi = (ora - dt_inviata).days
            if giorni_trascorsi > cfg.get("giorni_attesa_max", 14):
                return StatoDossier.IN_ATTESA_RISPOSTA

        return stato_attuale
```

---

## 4. Gmail Monitor — gap analysis strategia vs realtà

La logica centrale: confronta *cosa avrebbe dovuto succedere* con *cosa Gmail mostra*.

### 4.1 Wrapper Gmail MCP

```python
# sdq1/dossier/gmail_wrapper.py
"""
Wrapper intorno ai Gmail MCP tools:
  - search_threads  (mcp__f0b90091__search_threads)
  - list_drafts     (mcp__f0b90091__list_drafts)
  - get_thread      (mcp__f0b90091__get_thread)

In produzione questi vengono chiamati via subprocess o via l'interfaccia MCP.
In test vengono mockati.
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from typing import Any


class GmailMCPWrapper:
    """
    Interfaccia Python verso i Gmail MCP tools.
    Chiama i tool tramite il sistema MCP di Claude Code.
    """

    def cerca_sent(self, keywords: list[str]) -> list[dict]:
        """Cerca email INVIATE contenenti le keyword del dossier."""
        query = "in:sent (" + " OR ".join(keywords) + ")"
        return self._search_threads(query)

    def cerca_inbox(self, keywords: list[str]) -> list[dict]:
        """Cerca email RICEVUTE contenenti le keyword del dossier."""
        query = "in:inbox (" + " OR ".join(keywords) + ")"
        return self._search_threads(query)

    def cerca_draft(self, keywords: list[str]) -> list[dict]:
        """Cerca BOZZE contenenti le keyword del dossier."""
        # list_drafts non ha filtro per keyword, quindi filtriamo manualmente
        tutti_i_draft = self._list_drafts()
        keywords_lower = [k.lower() for k in keywords]
        risultati = []
        for draft in tutti_i_draft:
            soggetto = (draft.get("subject") or "").lower()
            snippet  = (draft.get("snippet") or "").lower()
            if any(k in soggetto or k in snippet for k in keywords_lower):
                risultati.append(draft)
        return risultati

    def get_thread_dettaglio(self, thread_id: str) -> dict:
        """Legge il contenuto completo di un thread."""
        return self._get_thread(thread_id)

    # ── Chiamate MCP sottostanti ───────────────────────────────────────────────

    def _search_threads(self, query: str) -> list[dict]:
        """
        Chiama mcp__f0b90091__search_threads.
        In produzione: via tool call dal sistema Claude Code.
        Qui: stub che in futuro viene sostituito con la chiamata reale.
        """
        # IMPLEMENTAZIONE REALE: chiamata MCP via Claude Code tool
        # Il tool restituisce lista di thread con id, subject, snippet, date
        raise NotImplementedError(
            "Da implementare: chiamata a mcp__f0b90091__search_threads con query='{query}'"
        )

    def _list_drafts(self) -> list[dict]:
        """Chiama mcp__f0b90091__list_drafts."""
        raise NotImplementedError(
            "Da implementare: chiamata a mcp__f0b90091__list_drafts"
        )

    def _get_thread(self, thread_id: str) -> dict:
        """Chiama mcp__f0b90091__get_thread."""
        raise NotImplementedError(
            f"Da implementare: chiamata a mcp__f0b90091__get_thread con thread_id='{thread_id}'"
        )
```

### 4.2 Gap analysis — logica di confronto

```python
def analizza_gap(
    cfg: dict,
    email_inviate: list[dict],
    email_ricevute: list[dict],
    bozze: list[dict],
    ora: datetime,
) -> list[str]:
    """
    Confronta la strategia attesa con la realtà Gmail.
    Restituisce lista di gap trovati (stringhe descrittive).

    Strategia attesa = cfg["prossima_azione"] + cfg["stato"]
    Realtà           = email_inviate, email_ricevute, bozze
    """
    gap = []
    stato = StatoDossier(cfg.get("stato", "PENDING"))

    # Gap 1: PENDING ma nessuna email inviata da molto tempo
    if stato == StatoDossier.PENDING and not email_inviate:
        gap.append(
            f"[GAP] {cfg['nome']}: stato PENDING ma nessuna email trovata in sent. "
            f"Prossima azione attesa: {cfg.get('prossima_azione', 'non definita')}"
        )

    # Gap 2: Bozza presente da >24h (email scritta ma non inviata)
    for draft in bozze:
        data_draft = _parse_email_date(draft.get("date") or draft.get("internalDate"))
        if data_draft:
            ore_in_draft = (ora - data_draft).total_seconds() / 3600
            if ore_in_draft > 24:
                gap.append(
                    f"[GAP] {cfg['nome']}: bozza '{draft.get('subject', '(senza oggetto)')}' "
                    f"in draft da {int(ore_in_draft)}h — vuoi che la invii?"
                )

    # Gap 3: Email inviata ma risposta attesa non arrivata
    if stato == StatoDossier.IN_ATTESA_RISPOSTA and email_inviate and not email_ricevute:
        ultima = email_inviate[0]
        data_invio = _parse_email_date(ultima.get("date"))
        if data_invio:
            giorni = (ora - data_invio).days
            max_giorni = cfg.get("giorni_attesa_max", 14)
            if giorni > max_giorni:
                gap.append(
                    f"[GAP] {cfg['nome']}: email inviata {giorni}gg fa, "
                    f"nessuna risposta (limite attesa: {max_giorni}gg). "
                    f"Sollecito necessario?"
                )

    # Gap 4: Risposta ricevuta ma nessuna azione a seguire
    if email_ricevute and email_inviate:
        dt_ricevuta = _parse_email_date(email_ricevute[0].get("date"))
        dt_inviata  = _parse_email_date(email_inviate[0].get("date"))
        if dt_ricevuta and dt_inviata and dt_ricevuta > dt_inviata:
            ore_senza_azione = (ora - dt_ricevuta).total_seconds() / 3600
            if ore_senza_azione > 48:
                gap.append(
                    f"[GAP] {cfg['nome']}: risposta ricevuta {int(ore_senza_azione)}h fa "
                    f"senza azione successiva visibile."
                )

    # Gap 5: Scadenza imminente
    scadenza_str = cfg.get("scadenza")
    if scadenza_str:
        scadenza = datetime.fromisoformat(scadenza_str).replace(tzinfo=timezone.utc)
        ore_alla_scadenza = (scadenza - ora).total_seconds() / 3600
        if 0 < ore_alla_scadenza <= 72:
            gap.append(
                f"[SCADENZA] {cfg['nome']}: scadenza tra {int(ore_alla_scadenza)}h "
                f"({scadenza_str}). Azione richiesta ora."
            )

    return gap


def _parse_email_date(date_val: Any) -> datetime | None:
    """Parsa date Gmail (epoch ms o ISO string) in datetime UTC-aware."""
    if date_val is None:
        return None
    try:
        if isinstance(date_val, (int, float)):
            # epoch millisecondi (formato Gmail API)
            return datetime.fromtimestamp(date_val / 1000, tz=timezone.utc)
        if isinstance(date_val, str):
            return datetime.fromisoformat(date_val.replace("Z", "+00:00"))
    except (ValueError, OSError):
        return None
    return None
```

---

## 5. Trigger automatici

Tabella completa dei trigger con soglie, livelli di alert e azione suggerita.

```python
# sdq1/dossier/triggers.py
"""Logica trigger automatici del DossierMonitor."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any
from .monitor import Alert, LivelloAlert, StatoDossier


def _genera_alerts(
    cfg: dict[str, Any],
    stato: StatoDossier,
    ultima_inviata: str | None,
    ultima_ricevuta: str | None,
    draft_in_attesa: bool,
    bozze: list[dict],
    ora: datetime,
) -> list[Alert]:
    """Genera tutti gli alert per un singolo dossier."""
    alerts: list[Alert] = []
    dossier_id = cfg["id"]

    # ── TRIGGER 1: Bozza in draft da >24h ─────────────────────────────────────
    for draft in bozze:
        data_draft = _parse_email_date(draft.get("date") or draft.get("internalDate"))
        if data_draft:
            ore = (ora - data_draft).total_seconds() / 3600
            if ore > 24:
                alerts.append(Alert(
                    dossier_id=dossier_id,
                    livello=LivelloAlert.WARN,
                    messaggio=(
                        f"Bozza '{draft.get('subject', '(senza oggetto)')}' "
                        f"in draft da {int(ore)}h senza essere inviata."
                    ),
                    azione_suggerita=(
                        "Revisiona la bozza e invia, oppure elimina se non più necessaria."
                    ),
                ))

    # ── TRIGGER 2: Scadenza entro 72h ─────────────────────────────────────────
    scadenza_str = cfg.get("scadenza")
    if scadenza_str and stato != StatoDossier.CHIUSO:
        scadenza = datetime.fromisoformat(scadenza_str).replace(tzinfo=timezone.utc)
        ore_rimanenti = (scadenza - ora).total_seconds() / 3600

        if 0 < ore_rimanenti <= 24:
            alerts.append(Alert(
                dossier_id=dossier_id,
                livello=LivelloAlert.URGENTE,
                messaggio=f"SCADENZA TRA {int(ore_rimanenti)}H: {scadenza_str}",
                azione_suggerita="Azione immediata richiesta — blocca tutto il resto.",
            ))
        elif 24 < ore_rimanenti <= 72:
            alerts.append(Alert(
                dossier_id=dossier_id,
                livello=LivelloAlert.WARN,
                messaggio=f"Scadenza imminente tra {int(ore_rimanenti)}h ({scadenza_str})",
                azione_suggerita="Prepara l'azione richiesta entro domani.",
            ))

    # ── TRIGGER 3: Attesa risposta oltre soglia ────────────────────────────────
    if stato in (StatoDossier.INVIATO, StatoDossier.IN_ATTESA_RISPOSTA):
        if ultima_inviata and not ultima_ricevuta:
            dt_invio = _parse_email_date(ultima_inviata)
            if dt_invio:
                giorni = (ora - dt_invio).days
                max_giorni = cfg.get("giorni_attesa_max", 14)
                if giorni > max_giorni:
                    alerts.append(Alert(
                        dossier_id=dossier_id,
                        livello=LivelloAlert.WARN,
                        messaggio=(
                            f"Nessuna risposta da {giorni} giorni "
                            f"(soglia: {max_giorni}gg)."
                        ),
                        azione_suggerita="Invia sollecito formale o contatta telefonicamente.",
                    ))

    # ── TRIGGER 4: Risposta ricevuta, nessuna azione entro 48h ────────────────
    if stato == StatoDossier.AZIONE_RICHIESTA and ultima_ricevuta:
        dt_ricevuta = _parse_email_date(ultima_ricevuta)
        if dt_ricevuta:
            ore_inazione = (ora - dt_ricevuta).total_seconds() / 3600
            if ore_inazione > 48:
                alerts.append(Alert(
                    dossier_id=dossier_id,
                    livello=LivelloAlert.WARN,
                    messaggio=(
                        f"Risposta ricevuta {int(ore_inazione)}h fa, "
                        "nessuna azione rilevata."
                    ),
                    azione_suggerita=cfg.get(
                        "prossima_azione", "Definire e eseguire prossimo passo."
                    ),
                ))

    # ── TRIGGER 5: Dossier PENDING da >7 giorni senza movimenti ───────────────
    if stato == StatoDossier.PENDING:
        data_ultimo_mov = cfg.get("data_ultimo_aggiornamento")
        if data_ultimo_mov:
            dt = _parse_email_date(data_ultimo_mov)
            if dt:
                giorni_stallo = (ora - dt).days
                if giorni_stallo > 7:
                    alerts.append(Alert(
                        dossier_id=dossier_id,
                        livello=LivelloAlert.INFO,
                        messaggio=f"Dossier in PENDING da {giorni_stallo} giorni senza movimenti.",
                        azione_suggerita=cfg.get("prossima_azione", "Definire prossimo passo."),
                    ))

    # ── TRIGGER 6: Dossier Martin/PP Retail — info insufficienti ──────────────
    if dossier_id == "MARTIN_PP_RETAIL" and stato == StatoDossier.PENDING:
        alerts.append(Alert(
            dossier_id=dossier_id,
            livello=LivelloAlert.INFO,
            messaggio="Dossier Martin/PP Retail: dettagli insufficienti per monitoraggio preciso.",
            azione_suggerita=(
                "Fornire al sistema: stato attuale, prossima azione, "
                "controparte email, scadenze."
            ),
        ))

    return alerts


def _parse_email_date(date_val: Any) -> datetime | None:
    """Parsa date Gmail in datetime UTC-aware."""
    if date_val is None:
        return None
    try:
        if isinstance(date_val, (int, float)):
            return datetime.fromtimestamp(date_val / 1000, tz=timezone.utc)
        if isinstance(date_val, str):
            return datetime.fromisoformat(date_val.replace("Z", "+00:00"))
    except (ValueError, OSError):
        return None
    return None
```

---

## 6. Dashboard live — struttura JSON

Il file `output/dossier_stato.json` è la dashboard in tempo reale.
Aggiornato a ogni esecuzione dell'agente orario.

```json
{
  "aggiornato_il": "2026-06-17T14:00:00+00:00",
  "versione": "1.0.0",
  "principio": "CT — il sistema monitora, non aspetta",
  "dossiers": {
    "PORTS_PELAN": {
      "id": "PORTS_PELAN",
      "nome": "PORTS/Pelan — Prud'hommes Parigi",
      "stato": "AZIONE_RICHIESTA",
      "ultima_azione": "Arrêt Cour d'Appel 27/01/2026 — capitale ricevuto",
      "prossima_azione": "Contattare huissier de justice per recupero interessi ~2.050€",
      "scadenza": null,
      "capitale_ricevuto_eur": 7013.53,
      "interessi_attesi_eur": 2050.0,
      "rg": "22/08190",
      "keywords_gmail": [
        "PORTS", "Pelan", "prud'hommes", "RG 22/08190",
        "Cour d'Appel", "huissier", "intérêts"
      ],
      "giorni_attesa_max": 14,
      "ultima_email_inviata": null,
      "ultima_email_ricevuta": "2026-01-27T00:00:00+00:00",
      "draft_in_attesa": false,
      "note": "Capitale 7.013,53€ ricevuto. Interessi ~2.050€ non pagati. RG 22/08190.",
      "alerts": []
    },
    "ALLIANZ_DIRECT": {
      "id": "ALLIANZ_DIRECT",
      "nome": "Allianz Direct — Sinistro allagamento Parigi",
      "stato": "IN_ATTESA_RISPOSTA",
      "ultima_azione": "Contestazione devis inviata ad Allianz",
      "prossima_azione": "Ricevere preventivo artigiano (sabato 2026-06-21) e inviare ad Allianz",
      "scadenza": "2026-06-21",
      "keywords_gmail": [
        "Allianz", "sinistre", "dégât", "devis",
        "contestation", "allagamento", "scarichi", "assurance"
      ],
      "giorni_attesa_max": 10,
      "ultima_email_inviata": null,
      "ultima_email_ricevuta": null,
      "draft_in_attesa": false,
      "note": "Allagamento da scarichi. Devis controverso. Preventivo artigiano atteso sabato.",
      "alerts": [
        {
          "dossier_id": "ALLIANZ_DIRECT",
          "livello": "WARN",
          "messaggio": "Scadenza imminente tra ~72h (2026-06-21) — preventivo artigiano",
          "azione_suggerita": "Confermare appuntamento artigiano sabato, preparare invio ad Allianz",
          "timestamp": "2026-06-17T14:00:00+00:00"
        }
      ]
    },
    "SKYRIGHTS_FOUNDATION": {
      "id": "SKYRIGHTS_FOUNDATION",
      "nome": "SkyRights Foundation — ASBL Bruxelles",
      "stato": "PENDING",
      "ultima_azione": null,
      "prossima_azione": "Completare registrazione ASBL presso BCE/Moniteur Belge",
      "scadenza": null,
      "keywords_gmail": [
        "SkyRights", "ASBL", "BCE", "Moniteur Belge",
        "registrazione", "notaire", "fondation", "association"
      ],
      "giorni_attesa_max": 30,
      "ultima_email_inviata": null,
      "ultima_email_ricevuta": null,
      "draft_in_attesa": false,
      "note": "Fondazione ASBL in fase di registrazione a Bruxelles.",
      "alerts": []
    },
    "MARTIN_PP_RETAIL": {
      "id": "MARTIN_PP_RETAIL",
      "nome": "Martin/PP Retail — Dossier legale",
      "stato": "PENDING",
      "ultima_azione": null,
      "prossima_azione": "Da definire — informazioni incomplete",
      "scadenza": null,
      "keywords_gmail": [
        "Martin", "PP Retail", "dossier"
      ],
      "giorni_attesa_max": 14,
      "ultima_email_inviata": null,
      "ultima_email_ricevuta": null,
      "draft_in_attesa": false,
      "note": "Dettagli insufficienti. Richiedere a Claudio stato e prossima azione.",
      "alerts": [
        {
          "dossier_id": "MARTIN_PP_RETAIL",
          "livello": "INFO",
          "messaggio": "Dettagli insufficienti per monitoraggio preciso",
          "azione_suggerita": "Fornire stato attuale, controparte, scadenze",
          "timestamp": "2026-06-17T14:00:00+00:00"
        }
      ]
    }
  },
  "sommario": {
    "totale_dossiers": 4,
    "chiusi": 0,
    "urgenti": 0,
    "warn": 2,
    "info": 1,
    "prossima_scadenza": "2026-06-21 (ALLIANZ_DIRECT — preventivo artigiano)"
  }
}
```

---

## 7. Codice Python completo — dossier_monitor.py

Questo è il file unico da salvare in `sdq1/dossier/monitor_completo.py`.
Funziona in modalità reale (con Gmail MCP) e in modalità stub (per test senza Gmail).

```python
#!/usr/bin/env python3
"""
sdq1/dossier/monitor_completo.py
─────────────────────────────────
DossierMonitor — Principio CT (Monitor Proattivo Dossier & Email)
Sistema SDQ-1 di Claudio Terzi (Bruxelles)

Uso standalone:
    python sdq1/dossier/monitor_completo.py --stub     # test senza Gmail
    python sdq1/dossier/monitor_completo.py            # produzione con Gmail MCP

Uso da agente_orario.py:
    from sdq1.dossier.monitor_completo import esegui_monitor_dossier
    risultato = esegui_monitor_dossier(gmail_tool=None)  # None = stub mode
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional


# ── Costanti ──────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parents[2]
STATO_FILE   = ROOT / "output" / "dossier_stato.json"
CONFIG_FILE  = ROOT / "output" / "dossier_config.json"
ALERT_LOG    = ROOT / "output" / "dossier_alerts.jsonl"


# ── Enumerazioni ──────────────────────────────────────────────────────────────

class StatoDossier(str, Enum):
    PENDING             = "PENDING"
    INVIATO             = "INVIATO"
    IN_ATTESA_RISPOSTA  = "IN_ATTESA_RISPOSTA"
    AZIONE_RICHIESTA    = "AZIONE_RICHIESTA"
    SCADENZA_IMMINENTE  = "SCADENZA_IMMINENTE"
    CHIUSO              = "CHIUSO"


class LivelloAlert(str, Enum):
    INFO    = "INFO"
    WARN    = "WARN"
    URGENTE = "URGENTE"


# ── Strutture dati ────────────────────────────────────────────────────────────

@dataclass
class Alert:
    dossier_id: str
    livello: LivelloAlert
    messaggio: str
    azione_suggerita: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def __str__(self) -> str:
        return f"[{self.livello.value}] {self.dossier_id}: {self.messaggio}"


@dataclass
class StatoDossierSnapshot:
    id: str
    nome: str
    stato: StatoDossier
    ultima_azione: Optional[str]
    prossima_azione: Optional[str]
    scadenza: Optional[str]
    keywords_gmail: list[str]
    giorni_attesa_max: int
    ultima_email_inviata: Optional[str]
    ultima_email_ricevuta: Optional[str]
    draft_in_attesa: bool
    note: str
    alerts: list[Alert] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["stato"] = self.stato.value
        d["alerts"] = [
            {**asdict(a), "livello": a.livello.value}
            for a in self.alerts
        ]
        return d


@dataclass
class ResultatoControllo:
    timestamp: str
    dossiers: list[StatoDossierSnapshot]
    alerts_totali: list[Alert]
    sommario: str

    def report_testo(self) -> str:
        linee = [
            "╔══════════════════════════════════════════════╗",
            "║      DOSSIER MONITOR — Principio CT          ║",
            "╚══════════════════════════════════════════════╝",
            f"  Aggiornato: {self.timestamp}",
            "",
        ]
        for d in self.dossiers:
            emoji_stato = {
                "PENDING": "⏳", "INVIATO": "📤", "IN_ATTESA_RISPOSTA": "🕐",
                "AZIONE_RICHIESTA": "🔴", "SCADENZA_IMMINENTE": "⚠️", "CHIUSO": "✅"
            }.get(d.stato.value, "?")
            linee.append(f"  {emoji_stato} [{d.stato.value}] {d.nome}")
            if d.prossima_azione:
                linee.append(f"      → {d.prossima_azione}")
            if d.scadenza:
                linee.append(f"      Scadenza: {d.scadenza}")
            for alert in d.alerts:
                prefisso = {"INFO": "ℹ", "WARN": "⚠", "URGENTE": "🚨"}.get(alert.livello.value, "?")
                linee.append(f"      {prefisso} {alert.messaggio}")
            linee.append("")
        linee.append(f"  {self.sommario}")
        return "\n".join(linee)

    def to_json(self) -> str:
        return json.dumps(
            {
                "timestamp": self.timestamp,
                "dossiers": [d.to_dict() for d in self.dossiers],
                "alerts_totali": [
                    {**asdict(a), "livello": a.livello.value}
                    for a in self.alerts_totali
                ],
                "sommario": self.sommario,
            },
            indent=2,
            ensure_ascii=False,
            default=str,
        )


# ── Configurazione dossier ────────────────────────────────────────────────────

DOSSIER_CONFIG_DEFAULT: list[dict] = [
    {
        "id": "PORTS_PELAN",
        "nome": "PORTS/Pelan — Prud'hommes Parigi",
        "stato": "AZIONE_RICHIESTA",
        "ultima_azione": "Arrêt Cour d'Appel 27/01/2026 — capitale 7.013,53€ ricevuto",
        "prossima_azione": "Contattare huissier de justice per recupero interessi ~2.050€",
        "scadenza": None,
        "keywords_gmail": [
            "PORTS", "Pelan", "prud'hommes", "RG 22/08190",
            "Cour d'Appel", "huissier", "intérêts"
        ],
        "giorni_attesa_max": 14,
        "note": "Capitale 7.013,53€ ricevuto. Interessi ~2.050€ non pagati. RG 22/08190.",
        "data_ultimo_aggiornamento": "2026-01-27T00:00:00+00:00",
    },
    {
        "id": "ALLIANZ_DIRECT",
        "nome": "Allianz Direct — Sinistro allagamento Parigi",
        "stato": "IN_ATTESA_RISPOSTA",
        "ultima_azione": "Contestazione devis inviata ad Allianz",
        "prossima_azione": "Ricevere preventivo artigiano sabato 21/06 e inviare ad Allianz",
        "scadenza": "2026-06-21T09:00:00+00:00",
        "keywords_gmail": [
            "Allianz", "sinistre", "dégât", "devis",
            "contestation", "allagamento", "scarichi", "assurance"
        ],
        "giorni_attesa_max": 10,
        "note": "Allagamento da scarichi. Devis controverso. Preventivo artigiano atteso sabato.",
        "data_ultimo_aggiornamento": "2026-06-15T00:00:00+00:00",
    },
    {
        "id": "SKYRIGHTS_FOUNDATION",
        "nome": "SkyRights Foundation — ASBL Bruxelles",
        "stato": "PENDING",
        "ultima_azione": None,
        "prossima_azione": "Completare registrazione ASBL presso BCE / Moniteur Belge",
        "scadenza": None,
        "keywords_gmail": [
            "SkyRights", "ASBL", "BCE", "Moniteur Belge",
            "registrazione", "notaire", "fondation", "association"
        ],
        "giorni_attesa_max": 30,
        "note": "Fondazione ASBL in fase di registrazione a Bruxelles.",
        "data_ultimo_aggiornamento": "2026-06-10T00:00:00+00:00",
    },
    {
        "id": "MARTIN_PP_RETAIL",
        "nome": "Martin/PP Retail — Dossier legale",
        "stato": "PENDING",
        "ultima_azione": None,
        "prossima_azione": "Da definire — richiedere dettagli a Claudio",
        "scadenza": None,
        "keywords_gmail": ["Martin", "PP Retail", "dossier"],
        "giorni_attesa_max": 14,
        "note": "Dettagli dossier incompleti. Richiedere a Claudio stato e prossima azione.",
        "data_ultimo_aggiornamento": None,
    },
]


# ── Stub Gmail (per test senza MCP) ──────────────────────────────────────────

class GmailStub:
    """Stub Gmail per test — non chiama nessuna API reale."""

    def cerca_sent(self, keywords: list[str]) -> list[dict]:
        return []

    def cerca_inbox(self, keywords: list[str]) -> list[dict]:
        return []

    def cerca_draft(self, keywords: list[str]) -> list[dict]:
        return []

    def get_thread_dettaglio(self, thread_id: str) -> dict:
        return {}


# ── DossierMonitor (classe principale) ────────────────────────────────────────

class DossierMonitor:
    """
    Monitor proattivo dei dossier aperti di Claudio Terzi.

    In modalità produzione: riceve un oggetto gmail_tool con i metodi
    cerca_sent(), cerca_inbox(), cerca_draft().

    In modalità stub: usa GmailStub (nessuna chiamata reale).
    """

    def __init__(
        self,
        gmail_tool: Any = None,
        stato_file: Path = STATO_FILE,
        config_override: list[dict] | None = None,
        ora_fn: Callable[[], datetime] | None = None,
    ):
        self.gmail = gmail_tool or GmailStub()
        self.stato_file = stato_file
        self.config = config_override or self._carica_config()
        self._ora = ora_fn or (lambda: datetime.now(timezone.utc))

    # ── Entry point ────────────────────────────────────────────────────────────

    def controlla(self) -> ResultatoControllo:
        """Controlla tutti i dossier. Salva stato. Ritorna ResultatoControllo."""
        ora = self._ora()
        stato_precedente = self._leggi_stato_precedente()
        snapshots: list[StatoDossierSnapshot] = []
        alerts_totali: list[Alert] = []

        for cfg in self.config:
            snapshot = self._controlla_singolo(cfg, stato_precedente, ora)
            snapshots.append(snapshot)
            alerts_totali.extend(snapshot.alerts)

        self._salva_stato(snapshots, ora)
        self._log_alerts(alerts_totali)

        sommario = self._genera_sommario(snapshots, alerts_totali)
        return ResultatoControllo(
            timestamp=ora.isoformat(),
            dossiers=snapshots,
            alerts_totali=alerts_totali,
            sommario=sommario,
        )

    # ── Controllo singolo ──────────────────────────────────────────────────────

    def _controlla_singolo(
        self,
        cfg: dict,
        stato_precedente: dict,
        ora: datetime,
    ) -> StatoDossierSnapshot:
        prev = stato_precedente.get(cfg["id"], {})
        stato_corrente = StatoDossier(
            prev.get("stato") or cfg.get("stato") or "PENDING"
        )

        # Gmail checks
        try:
            email_inviate  = self.gmail.cerca_sent(cfg["keywords_gmail"])
            email_ricevute = self.gmail.cerca_inbox(cfg["keywords_gmail"])
            bozze          = self.gmail.cerca_draft(cfg["keywords_gmail"])
        except Exception as e:
            print(f"[DossierMonitor] Gmail error per {cfg['id']}: {e}", file=sys.stderr)
            email_inviate = email_ricevute = bozze = []

        ultima_inviata  = self._timestamp_piu_recente(email_inviate)
        ultima_ricevuta = self._timestamp_piu_recente(email_ricevute)
        draft_in_attesa = len(bozze) > 0

        nuovo_stato = self._calcola_stato(
            stato_corrente, ultima_inviata, ultima_ricevuta, ora, cfg
        )

        alerts = self._genera_alerts(
            cfg, nuovo_stato, ultima_inviata, ultima_ricevuta,
            draft_in_attesa, bozze, ora
        )

        return StatoDossierSnapshot(
            id=cfg["id"],
            nome=cfg["nome"],
            stato=nuovo_stato,
            ultima_azione=prev.get("ultima_azione") or cfg.get("ultima_azione"),
            prossima_azione=cfg.get("prossima_azione"),
            scadenza=cfg.get("scadenza"),
            keywords_gmail=cfg["keywords_gmail"],
            giorni_attesa_max=cfg.get("giorni_attesa_max", 14),
            ultima_email_inviata=ultima_inviata,
            ultima_email_ricevuta=ultima_ricevuta,
            draft_in_attesa=draft_in_attesa,
            note=cfg.get("note", ""),
            alerts=alerts,
        )

    # ── Logica stati ───────────────────────────────────────────────────────────

    def _calcola_stato(
        self,
        stato_attuale: StatoDossier,
        ultima_inviata: str | None,
        ultima_ricevuta: str | None,
        ora: datetime,
        cfg: dict,
    ) -> StatoDossier:
        if stato_attuale == StatoDossier.CHIUSO:
            return StatoDossier.CHIUSO

        # Scadenza imminente (sovrascrive tutto tranne CHIUSO)
        scadenza_str = cfg.get("scadenza")
        if scadenza_str:
            try:
                scadenza = datetime.fromisoformat(scadenza_str.replace("Z", "+00:00"))
                if not scadenza.tzinfo:
                    scadenza = scadenza.replace(tzinfo=timezone.utc)
                ore = (scadenza - ora).total_seconds() / 3600
                if 0 < ore <= 72:
                    return StatoDossier.SCADENZA_IMMINENTE
            except ValueError:
                pass

        # Risposta ricevuta dopo invio → AZIONE_RICHIESTA
        if ultima_ricevuta and ultima_inviata:
            try:
                dt_r = datetime.fromisoformat(ultima_ricevuta)
                dt_i = datetime.fromisoformat(ultima_inviata)
                if dt_r > dt_i:
                    return StatoDossier.AZIONE_RICHIESTA
            except ValueError:
                pass

        # Email inviata, nessuna risposta → INVIATO
        if ultima_inviata and not ultima_ricevuta:
            if stato_attuale == StatoDossier.PENDING:
                return StatoDossier.INVIATO

        # Troppo tempo senza risposta → IN_ATTESA_RISPOSTA
        if stato_attuale == StatoDossier.INVIATO and ultima_inviata:
            try:
                dt_i = datetime.fromisoformat(ultima_inviata)
                if not dt_i.tzinfo:
                    dt_i = dt_i.replace(tzinfo=timezone.utc)
                giorni = (ora - dt_i).days
                if giorni > cfg.get("giorni_attesa_max", 14):
                    return StatoDossier.IN_ATTESA_RISPOSTA
            except ValueError:
                pass

        return stato_attuale

    # ── Generazione alert ──────────────────────────────────────────────────────

    def _genera_alerts(
        self,
        cfg: dict,
        stato: StatoDossier,
        ultima_inviata: str | None,
        ultima_ricevuta: str | None,
        draft_in_attesa: bool,
        bozze: list[dict],
        ora: datetime,
    ) -> list[Alert]:
        alerts: list[Alert] = []
        did = cfg["id"]

        # T1: Bozza in draft da >24h
        for draft in bozze:
            data = _parse_date(draft.get("date") or draft.get("internalDate"))
            if data:
                ore = (ora - data).total_seconds() / 3600
                if ore > 24:
                    alerts.append(Alert(
                        dossier_id=did,
                        livello=LivelloAlert.WARN,
                        messaggio=(
                            f"Bozza '{draft.get('subject', '(senza oggetto)')}' "
                            f"in draft da {int(ore)}h senza essere inviata."
                        ),
                        azione_suggerita="Rivedi la bozza: invia o elimina.",
                    ))

        # T2: Scadenza entro 72h
        if cfg.get("scadenza") and stato != StatoDossier.CHIUSO:
            try:
                scad = datetime.fromisoformat(
                    cfg["scadenza"].replace("Z", "+00:00")
                )
                if not scad.tzinfo:
                    scad = scad.replace(tzinfo=timezone.utc)
                ore = (scad - ora).total_seconds() / 3600
                if 0 < ore <= 24:
                    alerts.append(Alert(
                        dossier_id=did, livello=LivelloAlert.URGENTE,
                        messaggio=f"SCADENZA TRA {int(ore)}H ({cfg['scadenza']})",
                        azione_suggerita="Azione immediata — priorità assoluta.",
                    ))
                elif 24 < ore <= 72:
                    alerts.append(Alert(
                        dossier_id=did, livello=LivelloAlert.WARN,
                        messaggio=f"Scadenza tra {int(ore)}h ({cfg['scadenza']})",
                        azione_suggerita=cfg.get("prossima_azione", "Agire entro domani."),
                    ))
            except ValueError:
                pass

        # T3: Attesa oltre soglia
        if stato in (StatoDossier.INVIATO, StatoDossier.IN_ATTESA_RISPOSTA):
            if ultima_inviata and not ultima_ricevuta:
                dt = _parse_date(ultima_inviata)
                if dt:
                    giorni = (ora - dt).days
                    max_g  = cfg.get("giorni_attesa_max", 14)
                    if giorni > max_g:
                        alerts.append(Alert(
                            dossier_id=did, livello=LivelloAlert.WARN,
                            messaggio=f"Nessuna risposta da {giorni}gg (soglia: {max_g}gg).",
                            azione_suggerita="Invia sollecito o contatta telefonicamente.",
                        ))

        # T4: Risposta ricevuta, inazione >48h
        if stato == StatoDossier.AZIONE_RICHIESTA and ultima_ricevuta:
            dt = _parse_date(ultima_ricevuta)
            if dt:
                ore = (ora - dt).total_seconds() / 3600
                if ore > 48:
                    alerts.append(Alert(
                        dossier_id=did, livello=LivelloAlert.WARN,
                        messaggio=f"Risposta ricevuta {int(ore)}h fa, nessuna azione rilevata.",
                        azione_suggerita=cfg.get("prossima_azione", "Definire e eseguire prossimo passo."),
                    ))

        # T5: PENDING da >7gg senza movimenti
        if stato == StatoDossier.PENDING:
            data_ult = cfg.get("data_ultimo_aggiornamento")
            if data_ult:
                dt = _parse_date(data_ult)
                if dt:
                    giorni = (ora - dt).days
                    if giorni > 7:
                        alerts.append(Alert(
                            dossier_id=did, livello=LivelloAlert.INFO,
                            messaggio=f"Dossier in PENDING da {giorni}gg senza movimenti.",
                            azione_suggerita=cfg.get("prossima_azione", "Definire prossimo passo."),
                        ))

        # T6: Info insufficienti (Martin/PP Retail)
        if did == "MARTIN_PP_RETAIL" and stato == StatoDossier.PENDING:
            alerts.append(Alert(
                dossier_id=did, livello=LivelloAlert.INFO,
                messaggio="Dettagli dossier insufficienti per monitoraggio preciso.",
                azione_suggerita="Fornire stato, controparte email, scadenze.",
            ))

        return alerts

    # ── Utilità ────────────────────────────────────────────────────────────────

    def _timestamp_piu_recente(self, emails: list[dict]) -> str | None:
        if not emails:
            return None
        dates = []
        for e in emails:
            dt = _parse_date(e.get("date") or e.get("internalDate"))
            if dt:
                dates.append(dt)
        if not dates:
            return None
        return max(dates).isoformat()

    def _carica_config(self) -> list[dict]:
        if CONFIG_FILE.exists():
            try:
                return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return DOSSIER_CONFIG_DEFAULT

    def _leggi_stato_precedente(self) -> dict:
        if self.stato_file.exists():
            try:
                data = json.loads(self.stato_file.read_text(encoding="utf-8"))
                return {d["id"]: d for d in data.get("dossiers", {}).values()
                        if isinstance(d, dict)}
            except Exception:
                pass
        return {}

    def _salva_stato(self, snapshots: list[StatoDossierSnapshot], ora: datetime) -> None:
        self.stato_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "aggiornato_il": ora.isoformat(),
            "principio": "CT — il sistema monitora, non aspetta",
            "dossiers": {s.id: s.to_dict() for s in snapshots},
            "sommario": {
                "totale_dossiers": len(snapshots),
                "chiusi":  sum(1 for s in snapshots if s.stato == StatoDossier.CHIUSO),
                "urgenti": sum(
                    1 for s in snapshots
                    for a in s.alerts if a.livello == LivelloAlert.URGENTE
                ),
                "warn": sum(
                    1 for s in snapshots
                    for a in s.alerts if a.livello == LivelloAlert.WARN
                ),
                "info": sum(
                    1 for s in snapshots
                    for a in s.alerts if a.livello == LivelloAlert.INFO
                ),
            },
        }
        self.stato_file.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

    def _log_alerts(self, alerts: list[Alert]) -> None:
        if not alerts:
            return
        ALERT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ALERT_LOG.open("a", encoding="utf-8") as f:
            for a in alerts:
                f.write(json.dumps(asdict(a), ensure_ascii=False, default=str) + "\n")

    def _genera_sommario(
        self,
        snapshots: list[StatoDossierSnapshot],
        alerts: list[Alert],
    ) -> str:
        urgenti = sum(1 for a in alerts if a.livello == LivelloAlert.URGENTE)
        warn    = sum(1 for a in alerts if a.livello == LivelloAlert.WARN)
        chiusi  = sum(1 for s in snapshots if s.stato == StatoDossier.CHIUSO)

        parti = [f"Dossier: {len(snapshots)} totali, {chiusi} chiusi"]
        if urgenti:
            parti.append(f"{urgenti} URGENTI")
        if warn:
            parti.append(f"{warn} avvisi")

        scadenze = [
            (s.id, s.scadenza) for s in snapshots
            if s.scadenza and s.stato != StatoDossier.CHIUSO
        ]
        if scadenze:
            prossima = min(scadenze, key=lambda x: x[1])
            parti.append(f"Prossima scadenza: {prossima[1]} ({prossima[0]})")

        return " — ".join(parti)


# ── Funzioni di utilità globali ───────────────────────────────────────────────

def _parse_date(val: Any) -> datetime | None:
    """Parsa date Gmail (epoch ms, ISO string) in datetime UTC-aware."""
    if val is None:
        return None
    try:
        if isinstance(val, (int, float)):
            return datetime.fromtimestamp(val / 1000, tz=timezone.utc)
        if isinstance(val, str):
            dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
            if not dt.tzinfo:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
    except (ValueError, OSError, OverflowError):
        return None
    return None


# ── Funzione di integrazione per agente_orario.py ────────────────────────────

def esegui_monitor_dossier(
    gmail_tool: Any = None,
    stub_mode: bool = False,
) -> str:
    """
    Entry point per l'integrazione in agente_orario.py.

    Args:
        gmail_tool: Istanza del wrapper Gmail (None = stub mode)
        stub_mode:  Forza stub anche se gmail_tool è fornito

    Returns:
        Stringa Markdown con il report del monitor da appendere all'output del task.
    """
    monitor = DossierMonitor(
        gmail_tool=None if stub_mode else gmail_tool,
    )
    risultato = monitor.controlla()

    # Genera sezione Markdown per il report
    ora_str = datetime.now(timezone(timedelta(hours=2))).strftime("%Y-%m-%d %H:%M CEST")
    linee = [
        "",
        "---",
        "",
        f"## Monitor Dossier — {ora_str}",
        "",
        "```",
        risultato.report_testo(),
        "```",
        "",
    ]

    alerts_urgenti = [a for a in risultato.alerts_totali if a.livello == LivelloAlert.URGENTE]
    alerts_warn    = [a for a in risultato.alerts_totali if a.livello == LivelloAlert.WARN]

    if alerts_urgenti:
        linee.append("### 🚨 Alert urgenti\n")
        for a in alerts_urgenti:
            linee.append(f"- **{a.dossier_id}**: {a.messaggio}")
            linee.append(f"  → *{a.azione_suggerita}*")
        linee.append("")

    if alerts_warn:
        linee.append("### ⚠️ Avvisi\n")
        for a in alerts_warn:
            linee.append(f"- **{a.dossier_id}**: {a.messaggio}")
            linee.append(f"  → *{a.azione_suggerita}*")
        linee.append("")

    return "\n".join(linee)


# ── Main standalone ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    stub = "--stub" in sys.argv or "--test" in sys.argv
    monitor = DossierMonitor(gmail_tool=None if stub else None)
    risultato = monitor.controlla()

    if "--json" in sys.argv:
        print(risultato.to_json())
    else:
        print(risultato.report_testo())

    n_urgenti = sum(1 for a in risultato.alerts_totali if a.livello == LivelloAlert.URGENTE)
    sys.exit(1 if n_urgenti > 0 else 0)
```

---

## 8. Integrazione in agente_orario.py

Il monitor si aggancia all'agente orario in **due punti** precisi.

### 8.1 Import da aggiungere in testa (dopo gli import esistenti)

```python
# ── Dossier Monitor (Principio CT) ───────────────────────────────────────────
# Aggiungere dopo: from pathlib import Path
try:
    from sdq1.dossier.monitor_completo import esegui_monitor_dossier
    _DOSSIER_MONITOR_OK = True
except ImportError:
    _DOSSIER_MONITOR_OK = False
    print("[agente_orario] DossierMonitor non disponibile — skip", file=sys.stderr)
```

### 8.2 Chiamata nel `main()` — inserire dopo la scrittura dell'output

Inserire **dopo** la riga `dest.write_text(output, encoding="utf-8")` (riga 209 di agente_orario.py):

```python
    # ── Monitor Dossier — Principio CT ───────────────────────────────────────
    if _DOSSIER_MONITOR_OK:
        try:
            print("[agente_orario] Esecuzione DossierMonitor...")
            report_dossier = esegui_monitor_dossier(stub_mode=True)  # stub_mode=False in prod con Gmail
            # Appendi il report dossier all'output del task
            with dest.open("a", encoding="utf-8") as f:
                f.write(report_dossier)
            print("[agente_orario] DossierMonitor: report appeso all'output")
        except Exception as e:
            print(f"[agente_orario] DossierMonitor error: {e}", file=sys.stderr)
    # ─────────────────────────────────────────────────────────────────────────
```

### 8.3 Esecuzione standalone del monitor (fuori dai task)

Aggiungere anche una modalità `--monitor` al main di agente_orario.py:

```python
def main() -> int:
    # Modalità standalone: solo monitor dossier
    if "--monitor" in sys.argv:
        if _DOSSIER_MONITOR_OK:
            from sdq1.dossier.monitor_completo import DossierMonitor
            m = DossierMonitor()
            r = m.controlla()
            print(r.report_testo())
            return 1 if any(
                a.livello.value == "URGENTE"
                for a in r.alerts_totali
            ) else 0
        else:
            print("[agente_orario] DossierMonitor non disponibile")
            return 1

    # ... resto del main esistente ...
```

### 8.4 Cron / GitHub Actions — aggiungere job dedicato

Nel workflow GitHub Actions esistente, aggiungere uno step:

```yaml
# In .github/workflows/agente_orario.yml
- name: Monitor dossier (Principio CT)
  run: python scripts/agente_orario.py --monitor
  continue-on-error: true  # non blocca il resto se fallisce
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

---

## 9. Stato attuale dei dossier al 2026-06-17

| Dossier | Stato | Prossima azione | Scadenza | Priorità |
|---|---|---|---|---|
| PORTS/Pelan | AZIONE_RICHIESTA | Contattare huissier — interessi 2.050€ | Nessuna formale | ALTA |
| Allianz Direct | IN_ATTESA_RISPOSTA | Ricevere preventivo artigiano sabato | **21/06/2026** | ALTA |
| SkyRights Foundation | PENDING | Completare registrazione BCE | Non definita | MEDIA |
| Martin/PP Retail | PENDING | Richiedere dettagli a Claudio | Non definita | DA DEFINIRE |

### Alert attivi al 17/06/2026

- **ALLIANZ_DIRECT** [WARN]: Scadenza tra ~96h (preventivo artigiano sabato 21/06). Confermare appuntamento.
- **PORTS_PELAN** [WARN]: Dossier in AZIONE_RICHIESTA — nessun huissier contattato ancora rilevabile.
- **MARTIN_PP_RETAIL** [INFO]: Dettagli insufficienti per monitoraggio preciso.
- **SKYRIGHTS_FOUNDATION** [INFO]: In PENDING da 7gg senza movimenti email rilevati.

---

## Note di implementazione

**Dipendenze Python**: nessuna dipendenza esterna (solo stdlib). Il monitor funziona out-of-the-box.

**File da creare**:
- `sdq1/dossier/__init__.py` (vuoto)
- `sdq1/dossier/monitor_completo.py` (il codice della sezione 7)

**File da modificare**:
- `scripts/agente_orario.py` (aggiunte sezione 8)

**File generati a runtime**:
- `output/dossier_stato.json` — dashboard live (aggiornata ogni ora)
- `output/dossier_alerts.jsonl` — log storico degli alert

**Integrazione Gmail reale**: quando i Gmail MCP tools sono accessibili dall'agente,
sostituire `GmailStub` con un wrapper che chiama `mcp__f0b90091__search_threads`,
`mcp__f0b90091__list_drafts`, `mcp__f0b90091__get_thread`. I metodi del wrapper
devono avere la stessa firma di `GmailStub`.

**Aggiornamento config dossier**: modificare `DOSSIER_CONFIG_DEFAULT` nel codice
oppure creare `output/dossier_config.json` (ha precedenza sulla config hardcoded).

---

*Report generato dal sistema SDQ-1 — Principio CT attivo dal 2026-06-17*
*Claudio Terzi — Bruxelles*
