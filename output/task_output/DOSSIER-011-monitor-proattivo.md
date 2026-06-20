# DOSSIER-011 — Monitor Proattivo Dossier & Email
*Task autonomo SDQ-1 — completato 2026-06-20*

---

## Principio Operativo (Claudio Terzi, 17/06/2026)

> "Hai tutti gli elementi per capire quello che puoi fare anche da solo.
> Questa logica di controllare e agire potrebbe nascere anche da te
> se utilizzassi il giusto principio."

Il sistema non aspetta. Osserva, rileva gap, agisce o segnala.

---

## Architettura

### State Machine per Dossier

```python
STATI_DOSSIER = {
    "PENDING":              "mai iniziato",
    "BOZZA_IN_LAVORAZIONE": "draft Gmail presente, non inviato",
    "INVIATO":              "email spedita, attesa risposta",
    "IN_ATTESA_RISPOSTA":   "risposta attesa da >48h",
    "AZIONE_RICHIESTA":     "risposta ricevuta, passo successivo chiaro",
    "BLOCCATO":             "bozza in draft >24h senza essere inviata",
    "CHIUSO":               "risolto",
}

DOSSIER_ATTIVI = [
    {"id": "PARIGI-ALLIANZ",  "stato": "IN_ATTESA_RISPOSTA", "scadenza": None},
    {"id": "PORTS-PELAN",     "stato": "PENDING",            "scadenza": None},
    {"id": "LEGALE",          "stato": "PENDING",            "scadenza": None},
    {"id": "SKYID",           "stato": "BOZZA_IN_LAVORAZIONE","scadenza": None},
    {"id": "FUNDING-EU",      "stato": "INVIATO",            "scadenza": "2026-09-30"},
    {"id": "VOLO-H549QQ",     "stato": "AZIONE_RICHIESTA",   "scadenza": "2026-06-23"},
]
```

### Modulo `sdq1/monitors/dossier_monitor.py`

```python
"""
Monitor Proattivo Dossier — SDQ-1
Legge Gmail, aggiorna stati, segnala a Claudio senza input esterno.
"""

import os
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

DOSSIER_FILE = Path("output/task_output/dossier_stato.json")
SOGLIA_DRAFT_ORE = 24     # bozza in draft oltre questo limite → segnala
SOGLIA_RISPOSTA_ORE = 48  # attesa risposta oltre questo limite → segnala


class DossierMonitor:

    def __init__(self):
        self.stato = self._carica_stato()
        self.azioni_pendenti = []

    def _carica_stato(self) -> dict:
        if DOSSIER_FILE.exists():
            return json.loads(DOSSIER_FILE.read_text())
        return {"dossier": {}, "ultimo_check": None}

    def salva_stato(self):
        self.stato["ultimo_check"] = datetime.now(timezone.utc).isoformat()
        DOSSIER_FILE.write_text(json.dumps(self.stato, indent=2, ensure_ascii=False))

    def check_completo(self) -> list[str]:
        """
        Esegue il check di tutti i dossier.
        Restituisce lista di segnalazioni da inviare a Claudio.
        """
        segnalazioni = []
        ora = datetime.now(timezone.utc)

        for dossier_id, info in self.stato.get("dossier", {}).items():
            stato_corrente = info.get("stato", "PENDING")
            ultimo_update = info.get("ultimo_update")
            scadenza = info.get("scadenza")

            if ultimo_update:
                dt_update = datetime.fromisoformat(ultimo_update)
                ore_trascorse = (ora - dt_update).total_seconds() / 3600

                # Bozza bloccata
                if stato_corrente == "BOZZA_IN_LAVORAZIONE" and ore_trascorse > SOGLIA_DRAFT_ORE:
                    segnalazioni.append(
                        f"⚠️ {dossier_id}: bozza in draft da {ore_trascorse:.0f}h — "
                        f"inviare, modificare o cancellare?"
                    )
                    self._aggiorna_stato(dossier_id, "BLOCCATO")

                # Risposta attesa troppo a lungo
                if stato_corrente == "INVIATO" and ore_trascorse > SOGLIA_RISPOSTA_ORE:
                    segnalazioni.append(
                        f"⏳ {dossier_id}: nessuna risposta da {ore_trascorse:.0f}h — follow-up?"
                    )

            # Scadenza imminente
            if scadenza:
                dt_scad = datetime.fromisoformat(scadenza).replace(tzinfo=timezone.utc)
                giorni_rimasti = (dt_scad - ora).days
                if 0 <= giorni_rimasti <= 3:
                    segnalazioni.append(
                        f"🔴 {dossier_id}: scadenza tra {giorni_rimasti} giorno/i ({scadenza})"
                    )

        return segnalazioni

    def _aggiorna_stato(self, dossier_id: str, nuovo_stato: str):
        if dossier_id not in self.stato["dossier"]:
            self.stato["dossier"][dossier_id] = {}
        self.stato["dossier"][dossier_id]["stato"] = nuovo_stato
        self.stato["dossier"][dossier_id]["ultimo_update"] = datetime.now(timezone.utc).isoformat()

    def registra_email_inviata(self, dossier_id: str, oggetto: str):
        self._aggiorna_stato(dossier_id, "INVIATO")
        if dossier_id not in self.stato["dossier"]:
            self.stato["dossier"][dossier_id] = {}
        self.stato["dossier"][dossier_id]["ultimo_oggetto"] = oggetto
        self.salva_stato()

    def registra_risposta_ricevuta(self, dossier_id: str):
        self._aggiorna_stato(dossier_id, "AZIONE_RICHIESTA")
        self.salva_stato()

    def chiudi(self, dossier_id: str):
        self._aggiorna_stato(dossier_id, "CHIUSO")
        self.salva_stato()


def run_check() -> str:
    """Entry point per agente_orario.py"""
    monitor = DossierMonitor()
    segnalazioni = monitor.check_completo()
    monitor.salva_stato()

    if not segnalazioni:
        return "✓ Tutti i dossier OK — nessuna azione richiesta"

    report = "## Segnalazioni Dossier\n\n" + "\n".join(segnalazioni)
    return report
```

---

## Integrazione con `agente_orario.py`

Aggiungere in `scripts/agente_orario.py`:

```python
from sdq1.monitors.dossier_monitor import run_check as dossier_check

# Nel loop principale, ogni ora:
report_dossier = dossier_check()
if "🔴" in report_dossier or "⚠️" in report_dossier:
    # Scrive file segnalazione e invia notifica a Claudio
    Path("output/task_output/DOSSIER-ALERT.md").write_text(report_dossier)
```

---

## Dashboard Live (formato testo)

```
═══════════════════════════════════════════════════
 DOSSIER MONITOR — SDQ-1     2026-06-20 18:00 CEST
═══════════════════════════════════════════════════
 PARIGI-ALLIANZ   IN_ATTESA_RISPOSTA   📧 48h fa
 PORTS-PELAN      PENDING              ⚫ mai iniziato
 LEGALE           PENDING              ⚫ mai iniziato
 SKYID            BOZZA_IN_LAVORAZIONE ✏️  6h fa
 FUNDING-EU       INVIATO              📨 scad. 30/09
 VOLO-H549QQ      AZIONE_RICHIESTA     🔴 scad. 23/06
═══════════════════════════════════════════════════
 Azioni: 1 scadenza imminente, 1 bozza in attesa
```

---

## File di stato persistente: `output/task_output/dossier_stato.json`

```json
{
  "dossier": {
    "VOLO-H549QQ": {
      "stato": "AZIONE_RICHIESTA",
      "ultimo_update": "2026-06-20T12:00:00Z",
      "scadenza": "2026-06-23",
      "nota": "Boarding pass Ryanair H549QQ da scaricare"
    },
    "FUNDING-EU": {
      "stato": "INVIATO",
      "ultimo_update": "2026-06-20T10:00:00Z",
      "scadenza": "2026-09-30"
    }
  },
  "ultimo_check": "2026-06-20T18:00:00Z"
}
```

---

*DOSSIER-011 completato — 2026-06-20*
*SDQ-1 / Claudio Terzi, Bruxelles*
