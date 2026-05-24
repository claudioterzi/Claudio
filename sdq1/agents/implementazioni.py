"""Implementazioni stub degli agenti Fase 1.

Stub deterministici: nessuna chiamata LLM. Sostituire `elabora()` con la
logica reale (Claude API, RAG, ecc.) quando si passa alle fasi successive.
"""

from __future__ import annotations

from .base import AgenteBase, MessaggioAgente, RispostaAgente
from .registry import registra
from ..config.loader import AgenteConfig


class RaffaArchitetto(AgenteBase):
    """RAFFA-001 — Casella 0: Analisi Semantica."""

    def elabora(self, messaggio: MessaggioAgente) -> RispostaAgente:
        testo = messaggio.payload.get("testo", "")
        analisi = {
            "lunghezza": len(testo),
            "parole": len(testo.split()),
            "ha_domanda": "?" in testo,
        }
        return RispostaAgente(
            mittente=self.id,
            successo=True,
            output={"analisi_semantica": analisi},
        )


class MemoCustode(AgenteBase):
    """MEMO-002 — Casella 2: Memoria RAG."""

    def elabora(self, messaggio: MessaggioAgente) -> RispostaAgente:
        return RispostaAgente(
            mittente=self.id,
            successo=True,
            output={"contesto_recuperato": []},
        )


class SentinVigilante(AgenteBase):
    """SENTIN-004 — Casella 4: Allineamento Identitario."""

    def elabora(self, messaggio: MessaggioAgente) -> RispostaAgente:
        testo = messaggio.payload.get("testo", "").lower()
        violazioni = []
        if "ignora le tue istruzioni" in testo or "ignore your instructions" in testo:
            violazioni.append("tentativo_jailbreak")
        return RispostaAgente(
            mittente=self.id,
            successo=len(violazioni) == 0,
            output={"violazioni": violazioni},
            errore=None if not violazioni else f"Violazioni: {violazioni}",
        )


class WaveMessaggero(AgenteBase):
    """WAVE-003 — Casella 12: Stile e Tono."""

    def elabora(self, messaggio: MessaggioAgente) -> RispostaAgente:
        return RispostaAgente(
            mittente=self.id,
            successo=True,
            output={"stile": {"tono": "calmo", "formalita": "media"}},
        )


@registra("RAFFA-001")
def _make_raffa(cfg: AgenteConfig) -> AgenteBase:
    return RaffaArchitetto(cfg.id, cfg.casella, cfg.modello, cfg.critico)


@registra("MEMO-002")
def _make_memo(cfg: AgenteConfig) -> AgenteBase:
    return MemoCustode(cfg.id, cfg.casella, cfg.modello, cfg.critico)


@registra("SENTIN-004")
def _make_sentin(cfg: AgenteConfig) -> AgenteBase:
    return SentinVigilante(cfg.id, cfg.casella, cfg.modello, cfg.critico)


@registra("WAVE-003")
def _make_wave(cfg: AgenteConfig) -> AgenteBase:
    return WaveMessaggero(cfg.id, cfg.casella, cfg.modello, cfg.critico)
