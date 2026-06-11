"""Implementazioni degli agenti SDQ-1.

Tutti gli agenti usano `ClaudeClient` (API reale se chiave presente,
fallback stub deterministico altrimenti). MEMO-002 usa la memoria
vettoriale condivisa via `imposta_runtime`. SENTIN-004 applica
filtri pattern + validazione LLM opzionale.

Ottimizzazioni attive:
  B. Hedging          – agenti critici passano hedging=True al client
  D. Model Affinity   – payload["provider_vincolo"] viene propagato
  VSS                 – agenti scrivono output nel VectorStateStore;
                        GEN-006 interroga il VSS per arricchire il contesto
"""

from __future__ import annotations

from typing import Any

from .base import AgenteBase, MessaggioAgente, RispostaAgente
from .registry import registra
from ..config.loader import AgenteConfig
from ..llm.client import ClaudeClient
from ..memory.store import MemoriaVettoriale
from ..memory.vss import VectorStateStore


class AgenteSDQ(AgenteBase):
    """Base condivisa con client LLM e accesso al VectorStateStore."""

    def __init__(self, cfg: AgenteConfig, llm: ClaudeClient, vss: VectorStateStore):
        super().__init__(cfg.id, cfg.casella, cfg.modello, cfg.critico)
        self.llm = llm
        self.vss = vss
        self.ruolo = cfg.ruolo

    def _run_id(self, messaggio: MessaggioAgente) -> str:
        return messaggio.payload.get("_run_id", "run_unknown")

    def _vincolo(self, messaggio: MessaggioAgente) -> str | None:
        """D: Model Affinity — legge il provider vincolato dal payload."""
        return messaggio.payload.get("provider_vincolo")

    def _meta(self, risposta) -> dict[str, Any]:
        return {
            "via_api":          risposta.via_api,
            "provider":         risposta.provider,
            "modello":          risposta.modello,
            "latenza_ms":       risposta.metadata.get("latenza_ms"),
            "input_tokens":     risposta.metadata.get("input_tokens"),
            "output_tokens":    risposta.metadata.get("output_tokens"),
            "profilo":          risposta.metadata.get("profilo"),
            "provider_tentati": risposta.metadata.get("provider_tentati"),
            "hedged":           risposta.metadata.get("hedged", False),
        }


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
            "parole":    len(testo.split()),
            "ha_domanda": "?" in testo,
        }
        risposta = self.llm.completa(
            self.SISTEMA, testo,
            hedging=self.critico,
            provider_vincolo=self._vincolo(messaggio),
        )
        run_id = self._run_id(messaggio)
        ptr = self.vss.scrivi(risposta.testo, run_id, self.id, "interpretazione")
        return RispostaAgente(
            mittente=self.id,
            successo=True,
            output={
                "analisi_semantica":      analisi_base,
                "interpretazione":        risposta.testo,
                "interpretazione_ptr":    ptr,
            },
            metadata=self._meta(risposta),
        )


# ---------- DECOMP-005: Decomposizione Intento (Fase 2) ----------

class DecompAnalista(AgenteSDQ):
    SISTEMA = (
        "Sei DECOMP-005. Scomponi il messaggio dell'utente in una lista "
        "numerata di intenti elementari (max 5). Solo la lista, niente preambolo."
    )

    def elabora(self, messaggio: MessaggioAgente) -> RispostaAgente:
        testo = messaggio.payload.get("testo", "")
        risposta = self.llm.completa(
            self.SISTEMA, testo,
            hedging=self.critico,
            provider_vincolo=self._vincolo(messaggio),
        )
        intenti = [
            riga.strip(" -•*").lstrip("0123456789. ").strip()
            for riga in risposta.testo.splitlines()
            if riga.strip()
        ]
        intenti = intenti[:5] or [testo]
        run_id = self._run_id(messaggio)
        ptr = self.vss.scrivi("\n".join(intenti), run_id, self.id, "intenti")
        return RispostaAgente(
            mittente=self.id,
            successo=True,
            output={"intenti": intenti, "intenti_ptr": ptr},
            metadata=self._meta(risposta),
        )


# ---------- MEMO-002: Memoria RAG ----------

class MemoCustode(AgenteSDQ):
    def __init__(
        self,
        cfg: AgenteConfig,
        llm: ClaudeClient,
        vss: VectorStateStore,
        memoria: MemoriaVettoriale,
    ):
        super().__init__(cfg, llm, vss)
        self.memoria = memoria

    def elabora(self, messaggio: MessaggioAgente) -> RispostaAgente:
        testo = messaggio.payload.get("testo", "")
        risultati = self.memoria.cerca(testo)
        contesto = [
            {"testo": r.ricordo.testo, "similarita": round(r.similarita, 3)}
            for r in risultati
        ]
        if testo and self.memoria.dimensione() < 1000:
            self.memoria.aggiungi(testo, metadata={"origine": "input_utente"})
        run_id = self._run_id(messaggio)
        blob = "\n".join(c["testo"] for c in contesto)
        ptr = self.vss.scrivi(blob, run_id, self.id, "contesto_rag") if blob else ""
        return RispostaAgente(
            mittente=self.id,
            successo=True,
            output={
                "contesto_recuperato": contesto,
                "contesto_rag_ptr":    ptr,
                "ricordi_totali":      self.memoria.dimensione(),
            },
        )


# ---------- SENTIN-004: Allineamento Identitario ----------

class SentinVigilante(AgenteSDQ):
    def __init__(
        self,
        cfg: AgenteConfig,
        llm: ClaudeClient,
        vss: VectorStateStore,
        pattern_blocco: list[str],
    ):
        super().__init__(cfg, llm, vss)
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
        run_id = self._run_id(messaggio)

        # VSS: arricchisci il contesto con contenuti rilevanti di questo run
        testo_query = p.get("testo", "")
        extra_vss = self.vss.cerca_nel_run(testo_query, run_id, top_k=3)

        prompt = (
            f"INPUT UTENTE: {testo_query}\n"
            f"INTERPRETAZIONE: {p.get('interpretazione', '(assente)')}\n"
            f"INTENTI: {p.get('intenti', [])}\n"
            f"CONTESTO RAG: {p.get('contesto_recuperato', [])}\n"
            + (f"CONTESTO AGGIUNTIVO VSS: {extra_vss}\n" if extra_vss else "")
        )
        risposta = self.llm.completa(
            self.SISTEMA, prompt,
            hedging=self.critico,
            provider_vincolo=self._vincolo(messaggio),
        )
        ptr = self.vss.scrivi(risposta.testo, run_id, self.id, "risposta_bozza")
        return RispostaAgente(
            mittente=self.id,
            successo=bool(risposta.testo),
            output={"risposta_bozza": risposta.testo, "risposta_bozza_ptr": ptr},
            metadata=self._meta(risposta),
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
        risposta = self.llm.completa(
            self.SISTEMA, bozza,
            hedging=self.critico,
            provider_vincolo=self._vincolo(messaggio),
        )
        run_id = self._run_id(messaggio)
        ptr = self.vss.scrivi(risposta.testo or bozza, run_id, self.id, "risposta_finale")
        return RispostaAgente(
            mittente=self.id,
            successo=True,
            output={
                "risposta_finale":     risposta.testo or bozza,
                "risposta_finale_ptr": ptr,
                "stile_applicato":     risposta.via_api,
                "stile":               {"tono": "calmo", "formalita": "media"},
            },
        )


# ---------- Registro: factory che ricevono dipendenze runtime ----------

_RUNTIME: dict[str, Any] = {}


def imposta_runtime(
    *,
    llm_factory,
    memoria: MemoriaVettoriale,
    vss: VectorStateStore,
    pattern_blocco: list[str],
):
    _RUNTIME["llm_factory"] = llm_factory
    _RUNTIME["memoria"] = memoria
    _RUNTIME["vss"] = vss
    _RUNTIME["pattern_blocco"] = pattern_blocco


def _llm(cfg: AgenteConfig) -> ClaudeClient:
    return _RUNTIME["llm_factory"](cfg.modello)

def _vss() -> VectorStateStore:
    return _RUNTIME["vss"]


@registra("RAFFA-001")
def _make_raffa(cfg: AgenteConfig) -> AgenteBase:
    return RaffaArchitetto(cfg, _llm(cfg), _vss())


@registra("DECOMP-005")
def _make_decomp(cfg: AgenteConfig) -> AgenteBase:
    return DecompAnalista(cfg, _llm(cfg), _vss())


@registra("MEMO-002")
def _make_memo(cfg: AgenteConfig) -> AgenteBase:
    return MemoCustode(cfg, _llm(cfg), _vss(), _RUNTIME["memoria"])


@registra("SENTIN-004")
def _make_sentin(cfg: AgenteConfig) -> AgenteBase:
    return SentinVigilante(cfg, _llm(cfg), _vss(), _RUNTIME["pattern_blocco"])


@registra("GEN-006")
def _make_gen(cfg: AgenteConfig) -> AgenteBase:
    return GenCompositore(cfg, _llm(cfg), _vss())


@registra("WAVE-003")
def _make_wave(cfg: AgenteConfig) -> AgenteBase:
    return WaveMessaggero(cfg, _llm(cfg), _vss())
