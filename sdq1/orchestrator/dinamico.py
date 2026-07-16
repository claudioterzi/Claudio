"""Orchestratore dinamico — il salto da protocollo a piattaforma.

A differenza di `OrchestratoreGerarchico`, che esegue sempre la stessa
pipeline fissa (0→1→2→4→3→12), l'orchestratore dinamico *pianifica* ad
ogni run il sottoinsieme minimo di agenti necessario al task, in base
alle capacità richieste (vedi `capacita.py`).

Principio: gli agenti sempre-attivi (analisi, sicurezza, generazione)
girano comunque — sono la spina dorsale identitaria del sistema. Gli
agenti opzionali (decomposizione, memoria, stile) vengono attivati solo
quando il task li richiede davvero. Meno chiamate LLM inutili, più
aderenza al bisogno reale.

Riusa integralmente la logica di retry, persistenza e model-affinity di
`OrchestratoreGerarchico`: si limita a decidere *quali* caselle eseguire,
poi delega l'esecuzione al genitore via `pipeline_override`.
"""

from __future__ import annotations

import logging
from typing import Any

from ..agents.base import AgenteBase
from ..config.loader import SDQ1Config
from ..persistence.store import StatoStore
from . import capacita as cap
from .capacita import RegistroCapacita
from .gerarchico import EsecuzioneGrafo, OrchestratoreGerarchico

log = logging.getLogger(__name__)

# Parole che segnalano un riferimento alla memoria / al passato condiviso.
_INDIZI_MEMORIA = (
    "ricord", "prima", "sessione", "come diceva", "come dicevo",
    "il progetto", "memoria", "l'altra volta", "in passato", "avevamo",
)


class OrchestratoreDinamico(OrchestratoreGerarchico):
    def __init__(
        self,
        config: SDQ1Config,
        agenti: dict[str, AgenteBase],
        stato: StatoStore | None = None,
        registro: RegistroCapacita | None = None,
    ):
        super().__init__(config, agenti, stato=stato)
        self.registro = registro or RegistroCapacita.da_config(config)

    # -- API pubblica -------------------------------------------------------

    def esegui(
        self,
        payload: dict[str, Any],
        pipeline_override: list[int] | None = None,
    ) -> EsecuzioneGrafo:
        # Se il chiamante forza una pipeline, la rispettiamo (compatibilità).
        piano = pipeline_override if pipeline_override is not None else self._pianifica(payload)
        log.debug("Piano dinamico: caselle=%s", piano)
        esecuzione = super().esegui(payload, pipeline_override=piano)
        self._garantisci_output(esecuzione)
        return esecuzione

    @staticmethod
    def _garantisci_output(esecuzione: EsecuzioneGrafo) -> None:
        """Preserva il contratto di output quando WAVE-003 (stile) è saltato.

        `risposta_finale` è normalmente prodotta da WAVE-003. Se lo stile
        non è nel piano, promuoviamo la bozza di GEN-006 a risposta finale,
        così i consumatori a valle trovano sempre la stessa chiave.
        """
        ctx = esecuzione.output_finale
        if not ctx or esecuzione.interrotta:
            return
        if not ctx.get("risposta_finale") and ctx.get("risposta_bozza"):
            ctx["risposta_finale"] = ctx["risposta_bozza"]
            ctx["stile_applicato"] = False

    # -- Pianificazione -----------------------------------------------------

    def _pianifica(self, payload: dict[str, Any]) -> list[int]:
        """Sceglie le caselle da eseguire in base alle capacità richieste.

        Mantiene l'ordine canonico della pipeline (le dipendenze fra agenti
        restano valide: analisi → decomposizione → memoria → sicurezza →
        generazione → stile). Filtra soltanto ciò che non serve.
        """
        richieste = self._capacita_richieste(payload)

        selezionate: list[int] = []
        for casella in self.pipeline_caselle:
            agente_cfg = self.config.agente_per_casella(casella)
            if agente_cfg is None:
                continue
            prof = self.registro.profilo(agente_cfg.id)
            if prof is None:
                # Nessun profilo: prudenza, lo includiamo.
                selezionate.append(casella)
                continue
            if prof.sempre_attivo or (prof.capacita & richieste):
                selezionate.append(casella)

        # Sicurezza anti-piano-vuoto: se qualcosa è andato storto nella
        # deduzione, torniamo alla pipeline completa.
        if not selezionate:
            log.warning("Piano dinamico vuoto, fallback su pipeline completa")
            return list(self.pipeline_caselle)
        return selezionate

    def _capacita_richieste(self, payload: dict[str, Any]) -> set[str]:
        """Deduce le capacità necessarie dal payload.

        Combina due segnali:
          1. la fase creativa (esplora/soglia/cristallizza) fissa la base;
          2. euristiche sul contenuto possono solo *aggiungere* capacità.
        Le capacità sempre-attive sono garantite in ogni caso.
        """
        richieste: set[str] = set(cap.SEMPRE_ATTIVE)

        fase = str(payload.get("fase", "soglia")).lower()
        if fase == "cristallizza":
            richieste |= {cap.DECOMPOSIZIONE, cap.MEMORIA, cap.STILE}
        elif fase == "soglia":
            richieste |= {cap.MEMORIA, cap.STILE}
        # 'esplora': solo il minimo (spina dorsale)

        testo = self._estrai_testo(payload)
        t = testo.lower()

        # Task articolato → serve decomposizione.
        if len(testo) > 280 or t.count("?") > 1 or self._e_multiparte(t):
            richieste.add(cap.DECOMPOSIZIONE)

        # Riferimento al passato/contesto condiviso → serve memoria.
        if any(k in t for k in _INDIZI_MEMORIA):
            richieste.add(cap.MEMORIA)

        # Output interno (auto-riflessione, sub-task): non serve rifinire lo stile.
        if payload.get("_origine") == "interno":
            richieste.discard(cap.STILE)

        # Richiesta esplicita di capacità dal chiamante.
        extra = payload.get("_capacita_extra")
        if extra:
            richieste |= {str(c).lower() for c in extra}

        return richieste

    @staticmethod
    def _estrai_testo(payload: dict[str, Any]) -> str:
        for chiave in ("input", "messaggio", "testo", "prompt", "query"):
            val = payload.get(chiave)
            if isinstance(val, str) and val:
                return val
        return ""

    @staticmethod
    def _e_multiparte(testo: str) -> bool:
        """Riconosce richieste composte (più obiettivi in una frase)."""
        marcatori = (" e ", " poi ", " inoltre ", ";", "\n-", "1.", "2.", " oltre a ")
        return any(m in testo for m in marcatori)
