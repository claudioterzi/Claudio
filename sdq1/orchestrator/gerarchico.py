"""Orchestratore gerarchico minimale per Fase 1."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from ..agents.base import AgenteBase, MessaggioAgente, RispostaAgente
from ..config.loader import SDQ1Config


log = logging.getLogger(__name__)


@dataclass
class EsecuzioneGrafo:
    input_iniziale: dict[str, Any]
    passi: list[RispostaAgente] = field(default_factory=list)
    output_finale: dict[str, Any] | None = None
    interrotta: bool = False
    motivo_interruzione: str | None = None


class OrchestratoreGerarchico:
    """Esegue gli agenti in ordine di casella, sotto il controllo del 'capo'."""

    def __init__(self, config: SDQ1Config, agenti: dict[str, AgenteBase]):
        self.config = config
        self.agenti = agenti
        self.capo_id: str = config.orchestratore["capo"]
        if self.capo_id not in agenti:
            raise KeyError(f"Capo {self.capo_id} non istanziato")
        self.max_iter: int = config.orchestratore["max_iterazioni"]
        self.timeout: int = config.orchestratore["timeout_nodo_secondi"]
        retry = config.orchestratore.get("retry", {})
        self.retry_max: int = retry.get("max_tentativi", 0)
        self.backoff: list[int] = retry.get("backoff_secondi", [])

    def esegui(self, payload: dict[str, Any]) -> EsecuzioneGrafo:
        esecuzione = EsecuzioneGrafo(input_iniziale=payload)
        contesto: dict[str, Any] = dict(payload)

        for casella in self.config.caselle_attive:
            agente_cfg = self.config.agente_per_casella(casella)
            if agente_cfg is None:
                continue
            agente = self.agenti[agente_cfg.id]
            messaggio = MessaggioAgente(
                mittente=self.capo_id,
                destinatario=agente.id,
                casella=casella,
                payload=dict(contesto),
            )
            risposta = self._esegui_con_retry(agente, messaggio)
            esecuzione.passi.append(risposta)

            if not risposta.successo:
                if agente.critico:
                    esecuzione.interrotta = True
                    esecuzione.motivo_interruzione = (
                        f"Agente critico {agente.id} fallito: {risposta.errore}"
                    )
                    return esecuzione
                log.warning("Agente non critico %s fallito, proseguo", agente.id)
                continue

            contesto.update(risposta.output)

        esecuzione.output_finale = contesto
        return esecuzione

    def _esegui_con_retry(
        self, agente: AgenteBase, messaggio: MessaggioAgente
    ) -> RispostaAgente:
        tentativi = self.retry_max + 1 if agente.critico else 1
        ultima: RispostaAgente | None = None
        for i in range(tentativi):
            try:
                ultima = agente.elabora(messaggio)
                if ultima.successo:
                    return ultima
            except Exception as exc:  # noqa: BLE001
                ultima = RispostaAgente(
                    mittente=agente.id, successo=False, output={}, errore=str(exc)
                )
            if i < tentativi - 1 and i < len(self.backoff):
                time.sleep(self.backoff[i])
        assert ultima is not None
        return ultima
