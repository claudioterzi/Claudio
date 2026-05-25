"""Implementazioni degli agenti SDQ-1.

Tutti gli agenti usano `ClaudeClient` (API reale se chiave presente,
fallback stub deterministico altrimenti). MEMO-002 usa la memoria
vettoriale condivisa via `set_contesto_runtime`. SENTIN-004 applica
filtri pattern + validazione LLM opzionale.
"""

from __future__ import annotations

from typing import Any

from .base import AgenteBase, MessaggioAgente, RispostaAgente
from .registry import registra
from ..config.loader import AgenteConfig
from ..llm.client import ClaudeClient
from ..memory.store import MemoriaVettoriale


class AgenteSDQ(AgenteBase):
    """Base condivisa che incapsula il client LLM."""

    def __init__(self, cfg: AgenteConfig, llm: ClaudeClient):
        super().__init__(cfg.id, cfg.casella, cfg.modello, cfg.critico)
        self.llm = llm
        self.ruolo = cfg.ruolo


# ---------- RAFFA-001: Analisi Semantica ----------

class RaffaArchitetto(AgenteSDQ):
    SISTEMA = (
        "Sei RAFFA-001, architetto semantico di SDQ-1. "
        "Analizza il messaggio in massimo 3 righe: intento principale, "
        "tono percepito, urgenza (bassa/media/alta). Risposta secca."
    )

    def elabora(self, messaggio: MessaggioAgente) -> RispostaAgente:
        testo = messaggio.payload.get("testo", "")
        if not testo:
            return RispostaAgente(self.id, False, {}, errore="testo vuoto")
        analisi_base = {
            "lunghezza": len(testo),
            "parole": len(testo.split()),
            "ha_domanda": "?" in testo,
        }
        risposta = self.llm.completa(self.SISTEMA, testo)
        return RispostaAgente(
            mittente=self.id,
            successo=True,
            output={
                "analisi_semantica": analisi_base,
                "interpretazione": risposta.testo,
            },
            metadata={"via_api": risposta.via_api},
        )


# ---------- DECOMP-005: Decomposizione Intento (Fase 2) ----------

class DecompAnalista(AgenteSDQ):
    SISTEMA = (
        "Sei DECOMP-005. Scomponi il messaggio dell'utente in una lista "
        "numerata di intenti elementari (max 5). Solo la lista, niente preambolo."
    )

    def elabora(self, messaggio: MessaggioAgente) -> RispostaAgente:
        testo = messaggio.payload.get("testo", "")
        risposta = self.llm.completa(self.SISTEMA, testo)
        # parse semplice
        intenti = [
            riga.strip(" -•*").lstrip("0123456789. ").strip()
            for riga in risposta.testo.splitlines()
            if riga.strip()
        ]
        return RispostaAgente(
            mittente=self.id,
            successo=True,
            output={"intenti": intenti[:5] or [testo]},
            metadata={"via_api": risposta.via_api},
        )


# ---------- MEMO-002: Memoria RAG ----------

class MemoCustode(AgenteSDQ):
    def __init__(self, cfg: AgenteConfig, llm: ClaudeClient, memoria: MemoriaVettoriale):
        super().__init__(cfg, llm)
        self.memoria = memoria

    def elabora(self, messaggio: MessaggioAgente) -> RispostaAgente:
        testo = messaggio.payload.get("testo", "")
        risultati = self.memoria.cerca(testo)
        contesto = [
            {"testo": r.ricordo.testo, "similarita": round(r.similarita, 3)}
            for r in risultati
        ]
        # registra il nuovo input come ricordo (con limite di crescita)
        if testo and self.memoria.dimensione() < 1000:
            self.memoria.aggiungi(testo, metadata={"origine": "input_utente"})
        return RispostaAgente(
            mittente=self.id,
            successo=True,
            output={
                "contesto_recuperato": contesto,
                "ricordi_totali": self.memoria.dimensione(),
            },
        )


# ---------- SENTIN-004: Allineamento Identitario ----------

class SentinVigilante(AgenteSDQ):
    def __init__(self, cfg: AgenteConfig, llm: ClaudeClient, pattern_blocco: list[str]):
        super().__init__(cfg, llm)
        self.pattern = [p.lower() for p in pattern_blocco]

    def elabora(self, messaggio: MessaggioAgente) -> RispostaAgente:
        testo = (messaggio.payload.get("testo") or "").lower()
        violazioni = [p for p in self.pattern if p in testo]
        if violazioni:
            return RispostaAgente(
                mittente=self.id,
                successo=False,
                output={"violazioni": violazioni, "pattern_matched": True},
                errore=f"Pattern bloccati: {violazioni}",
            )
        return RispostaAgente(
            mittente=self.id,
            successo=True,
            output={"violazioni": [], "pattern_matched": False},
        )


# ---------- GEN-006: Generazione Risposta (Fase 2) ----------

class GenCompositore(AgenteSDQ):
    SISTEMA = (
        "Sei GEN-006, compositore di SDQ-1. Riceverai input utente, "
        "interpretazione semantica, intenti decomposti e contesto recuperato. "
        "Genera una risposta chiara, utile e onesta in italiano. "
        "Non inventare fatti se il contesto è vuoto: chiedi chiarimenti."
    )

    def elabora(self, messaggio: MessaggioAgente) -> RispostaAgente:
        p = messaggio.payload
        prompt = (
            f"INPUT UTENTE: {p.get('testo', '')}\n"
            f"INTERPRETAZIONE: {p.get('interpretazione', '(assente)')}\n"
            f"INTENTI: {p.get('intenti', [])}\n"
            f"CONTESTO: {p.get('contesto_recuperato', [])}\n"
        )
        risposta = self.llm.completa(self.SISTEMA, prompt)
        return RispostaAgente(
            mittente=self.id,
            successo=bool(risposta.testo),
            output={"risposta_bozza": risposta.testo},
            metadata={"via_api": risposta.via_api},
        )


# ---------- WAVE-003: Stile e Tono ----------

class WaveMessaggero(AgenteSDQ):
    SISTEMA = (
        "Sei WAVE-003. Rifinisci la bozza con tono calmo, formalità media, "
        "senza emoji a meno che la bozza già le contenga. Mantieni la sostanza."
    )

    def elabora(self, messaggio: MessaggioAgente) -> RispostaAgente:
        bozza = messaggio.payload.get("risposta_bozza", "")
        if not bozza:
            return RispostaAgente(
                self.id, True, {"risposta_finale": "", "stile_applicato": False}
            )
        risposta = self.llm.completa(self.SISTEMA, bozza)
        return RispostaAgente(
            mittente=self.id,
            successo=True,
            output={
                "risposta_finale": risposta.testo or bozza,
                "stile_applicato": risposta.via_api,
                "stile": {"tono": "calmo", "formalita": "media"},
            },
        )


# ---------- Registro: factory che ricevono dipendenze runtime ----------

# Dipendenze condivise iniettate da costruisci_agenti_con_dipendenze
_RUNTIME: dict[str, Any] = {}


def imposta_runtime(*, llm_factory, memoria: MemoriaVettoriale, pattern_blocco: list[str]):
    _RUNTIME["llm_factory"] = llm_factory
    _RUNTIME["memoria"] = memoria
    _RUNTIME["pattern_blocco"] = pattern_blocco


def _llm(cfg: AgenteConfig) -> ClaudeClient:
    return _RUNTIME["llm_factory"](cfg.modello)


@registra("RAFFA-001")
def _make_raffa(cfg: AgenteConfig) -> AgenteBase:
    return RaffaArchitetto(cfg, _llm(cfg))


@registra("DECOMP-005")
def _make_decomp(cfg: AgenteConfig) -> AgenteBase:
    return DecompAnalista(cfg, _llm(cfg))


@registra("MEMO-002")
def _make_memo(cfg: AgenteConfig) -> AgenteBase:
    return MemoCustode(cfg, _llm(cfg), _RUNTIME["memoria"])


@registra("SENTIN-004")
def _make_sentin(cfg: AgenteConfig) -> AgenteBase:
    return SentinVigilante(cfg, _llm(cfg), _RUNTIME["pattern_blocco"])


@registra("GEN-006")
def _make_gen(cfg: AgenteConfig) -> AgenteBase:
    return GenCompositore(cfg, _llm(cfg))


@registra("WAVE-003")
def _make_wave(cfg: AgenteConfig) -> AgenteBase:
    return WaveMessaggero(cfg, _llm(cfg))
