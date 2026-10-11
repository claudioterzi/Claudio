"""SognatoreSDQ — Livello 5B: speculazione ottimista rigorosa.

Contrappeso al Contraddittore (Livello 5A).
Dove il Contraddittore attacca le premesse, il Sognatore espande le possibilità.

Il Sognatore non è ingenuo: opera sempre nella verità.
Non inventa fatti. Non nega ostacoli.
Trova le migliori interpretazioni possibili di ciò che esiste già,
e proietta le traiettorie più favorevoli che i dati permettono.

Trilogia del Livello 5:
  5A → ContraddittoreSDQ — attacca le premesse
  5B → SognatoreSDQ      — espande le possibilità  ← questo modulo
  5C → sintesi dialettica tra 5A e 5B (in sar.py)

Uso:
    from sdq1.sar.sognatore import SognatoreSDQ
    s = SognatoreSDQ(llm_fn=my_llm)
    visione = s.espandi("SDQ-1 potrebbe un giorno essere usato da altri")
    print(visione.scenario_ottimale)
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

REPO = Path(__file__).resolve().parents[2]
STORICO_PATH = REPO / "sdq1" / "sar" / "_sognatore_storico.jsonl"

LLMFn = Callable[[str, str], str]


SISTEMA_SOGNATORE = (
    "Sei il Sognatore del sistema SDQ-1. Il tuo compito è l'opposto del Contraddittore: "
    "non attacchi le premesse — le espandi. "
    "Trovi le migliori interpretazioni possibili di un'idea, "
    "le traiettorie più favorevoli che i dati permettono, "
    "le connessioni inaspettate tra ciò che esiste e ciò che potrebbe essere. "
    "Operi sempre nella verità: non inventi fatti, non ignori ostacoli, "
    "non trasformi problemi in magie. "
    "La tua domanda guida non è 'perché questo non funziona' "
    "ma 'se questo funzionasse nel modo migliore possibile, cosa sarebbe possibile?'"
)


@dataclass
class VisioneSognatrice:
    affermazione: str
    scenario_ottimale: str
    connessioni_inaspettate: list[str] = field(default_factory=list)
    potenziale_nascosto: list[str] = field(default_factory=list)
    condizioni_favorevoli: list[str] = field(default_factory=list)
    domande_aperte: list[str] = field(default_factory=list)
    forza: bool = True
    motivo_forza: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp":               time.time(),
            "affermazione":            self.affermazione,
            "scenario_ottimale":       self.scenario_ottimale,
            "connessioni_inaspettate": self.connessioni_inaspettate,
            "potenziale_nascosto":     self.potenziale_nascosto,
            "condizioni_favorevoli":   self.condizioni_favorevoli,
            "domande_aperte":          self.domande_aperte,
            "forza":                   self.forza,
            "motivo_forza":            self.motivo_forza,
        }


class SognatoreSDQ:
    """Speculatore ottimista rigoroso — Livello 5B della SAR.

    Produce visioni di possibilità reali, non rassicurazioni vuote.
    Una visione senza ancoraggi nel reale non è sognare: è fuggire.
    """

    def __init__(self, llm_fn: LLMFn | None = None):
        self._llm = llm_fn

    def espandi(self, affermazione: str) -> VisioneSognatrice:
        """Espande un'affermazione verso le sue migliori possibilità reali.

        Args:
            affermazione: qualsiasi idea, ipotesi o situazione del sistema

        Returns:
            VisioneSognatrice con scenario ottimale + connessioni + condizioni
        """
        if not self._llm:
            visione = VisioneSognatrice(
                affermazione=affermazione,
                scenario_ottimale="[LLM non disponibile]",
                forza=False,
                motivo_forza="LLM non configurato",
            )
            return visione

        prompt = (
            f"Espandi questa affermazione verso le sue migliori possibilità reali.\n\n"
            f"AFFERMAZIONE: {affermazione}\n\n"
            "Rispondi con SOLO questo JSON (breve, max 300 parole totali):\n"
            '{"scenario_ottimale": "Descrizione in 2-3 frasi di come questa idea potrebbe '
            'realizzarsi nel modo migliore possibile, restando ancorata alla realtà attuale.", '
            '"connessioni_inaspettate": ["connessione non ovvia tra questa idea e X", "max 3"], '
            '"potenziale_nascosto": ["aspetto positivo non ancora riconosciuto", "max 3"], '
            '"condizioni_favorevoli": ["cosa deve essere vero perché questo si realizzi", "max 3"], '
            '"domande_aperte": ["domanda che apre possibilità, non chiude", "max 2"], '
            '"forza": true, '
            '"motivo_forza": "Perché questa visione è solida, non fantasia."}\n\n'
            "REGOLE: Sii specifico sul sistema SDQ-1 e su Claudio Terzi. "
            "Non lodare l'idea. Trova cosa c'è di genuinamente potente in essa. "
            "SOLO JSON nessun testo extra."
        )

        risposta = self._llm(SISTEMA_SOGNATORE, prompt)
        dati = self._parse(risposta)

        visione = VisioneSognatrice(
            affermazione=affermazione,
            scenario_ottimale=dati.get("scenario_ottimale", ""),
            connessioni_inaspettate=dati.get("connessioni_inaspettate", []),
            potenziale_nascosto=dati.get("potenziale_nascosto", []),
            condizioni_favorevoli=dati.get("condizioni_favorevoli", []),
            domande_aperte=dati.get("domande_aperte", []),
            forza=bool(dati.get("forza", True)),
            motivo_forza=dati.get("motivo_forza", ""),
        )

        self._salva(visione)
        return visione

    def dialogo_con_contraddittore(
        self,
        affermazione: str,
        rapporto_contraddittore: Any,  # RapportoContraddizione
    ) -> dict[str, Any]:
        """Sintetizza visione sognante + obiezioni contraddittore.

        Il Contraddittore ha già attaccato l'affermazione. Il Sognatore risponde
        non negando le obiezioni, ma trovando la via che le integra.
        Produce una sintesi dialettica: l'affermazione più robusta possibile.
        """
        if not self._llm:
            return {"sintetizzato": False}

        obiezioni = getattr(rapporto_contraddittore, "obiezioni", [])
        regge = getattr(rapporto_contraddittore, "regge", None)

        prompt = (
            f"Il Contraddittore ha analizzato: '{affermazione}'\n"
            f"Regge secondo il Contraddittore: {regge}\n"
            f"Obiezioni: {json.dumps(obiezioni, ensure_ascii=False)}\n\n"
            "Il tuo compito: non difendere l'affermazione, non negare le obiezioni. "
            "Trova la versione più potente dell'affermazione che *integra* le obiezioni "
            "come vincoli invece che come confutazioni.\n\n"
            "Rispondi con SOLO questo JSON:\n"
            '{"affermazione_integrata": "versione raffinata che sopravvive alle obiezioni", '
            '"cosa_rimane_potente": "cosa c\'è di genuinamente valido dopo l\'attacco", '
            '"cosa_va_abbandonato": "cosa il Contraddittore ha giustamente eliminato", '
            '"prossimo_passo": "azione concreta per testare l\'affermazione integrata"}\n\n'
            "SOLO JSON nessun testo extra."
        )

        risposta = self._llm(SISTEMA_SOGNATORE, prompt)
        dati = self._parse(risposta)
        dati["sintetizzato"] = True
        dati["affermazione_originale"] = affermazione

        return dati

    def _parse(self, risposta: str) -> dict[str, Any]:
        s = risposta.strip()
        start = s.find("{")
        end = s.rfind("}") + 1
        if start == -1 or end == 0:
            return {}
        try:
            return json.loads(s[start:end])
        except Exception:
            return {}

    def _salva(self, visione: VisioneSognatrice) -> None:
        try:
            STORICO_PATH.parent.mkdir(parents=True, exist_ok=True)
            with STORICO_PATH.open("a", encoding="utf-8") as f:
                f.write(json.dumps(visione.to_dict(), ensure_ascii=False) + "\n")
        except Exception:
            pass

    def visioni_precedenti(self, ultime: int = 10) -> list[dict[str, Any]]:
        if not STORICO_PATH.exists():
            return []
        righe = []
        try:
            for riga in STORICO_PATH.read_text(encoding="utf-8").strip().splitlines():
                righe.append(json.loads(riga))
        except Exception:
            pass
        return righe[-ultime:]
