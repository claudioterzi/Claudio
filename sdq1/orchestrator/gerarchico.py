"""Orchestratore gerarchico con persistenza opzionale.

Ottimizzazione D (Model Affinity): dopo il primo nodo LLM con risposta
reale, il provider usato viene iniettato nel contesto come
'provider_vincolo' e tutti i nodi successivi lo ricevono nel payload.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from ..agents.base import AgenteBase, MessaggioAgente, RispostaAgente
from ..config.loader import SDQ1Config
from ..persistence.store import StatoStore


log = logging.getLogger(__name__)


@dataclass
class EsecuzioneGrafo:
    id: str
    input_iniziale: dict[str, Any]
    passi: list[RispostaAgente] = field(default_factory=list)
    output_finale: dict[str, Any] | None = None
    interrotta: bool = False
    motivo_interruzione: str | None = None
    durata_secondi: float | None = None


class OrchestratoreGerarchico:
    def __init__(
        self,
        config: SDQ1Config,
        agenti: dict[str, AgenteBase],
        stato: StatoStore | None = None,
    ):
        self.config = config
        self.agenti = agenti
        self.stato = stato
        self.capo_id: str = config.orchestratore["capo"]
        if self.capo_id not in agenti:
            raise KeyError(f"Capo {self.capo_id} non istanziato")
        self.timeout: int = config.orchestratore["timeout_nodo_secondi"]
        retry = config.orchestratore.get("retry", {})
        self.retry_max: int = retry.get("max_tentativi", 0)
        self.backoff: list[int] = retry.get("backoff_secondi", [])
        self.pipeline_caselle = config.pipeline()
        self.persistenza = bool(config.orchestratore.get("persistenza"))

    def esegui(self, payload: dict[str, Any]) -> EsecuzioneGrafo:
        esecuzione = EsecuzioneGrafo(
            id=uuid.uuid4().hex[:12], input_iniziale=payload
        )
        inizio = time.time()
        contesto: dict[str, Any] = dict(payload)
        self._persisti(esecuzione, contesto, stato="started")

        for casella in self.pipeline_caselle:
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
                    esecuzione.durata_secondi = round(time.time() - inizio, 3)
                    self._persisti(esecuzione, contesto, stato="aborted")
                    return esecuzione
                log.warning("Agente non critico %s fallito, proseguo", agente.id)
                continue

            contesto.update(risposta.output)

            # D. Model Affinity: vincola i nodi successivi al primo provider reale usato
            if "provider_vincolo" not in contesto:
                p = (risposta.metadata or {}).get("provider")
                if p and p != "stub":
                    contesto["provider_vincolo"] = p
                    log.debug("Affinity: provider vincolato a '%s' per questo run", p)

            self._persisti(esecuzione, contesto, stato="running")

        esecuzione.output_finale = contesto
        esecuzione.durata_secondi = round(time.time() - inizio, 3)
        self._persisti(esecuzione, contesto, stato="completed")
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

    def _persisti(
        self, esecuzione: EsecuzioneGrafo, contesto: dict[str, Any], stato: str
    ) -> None:
        if not self.persistenza or self.stato is None:
            return
        snapshot = {
            "id": esecuzione.id,
            "stato": stato,
            "passi": len(esecuzione.passi),
            "ultimo_agente": (
                esecuzione.passi[-1].mittente if esecuzione.passi else None
            ),
            "contesto_keys": list(contesto.keys()),
        }
        try:
            self.stato.set(
                f"esecuzione:{esecuzione.id}",
                snapshot,
                ttl_secondi=self.config.redis.get("ttl_stato_secondi"),
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("Persistenza snapshot fallita: %s", exc)
