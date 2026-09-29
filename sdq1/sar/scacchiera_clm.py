"""Scacchiera Quantica x CLM — selezione dei nodi tramite System One Rank.

Collega ScacchieraV3 alla primitiva nativa `/v1/rank` di CLM, esposta da
`typesafe_sister.client.rank`. Il motore simbolico continua a generare i figli;
CLM sostituisce soltanto il passo di scelta (score composito + rumore casuale).

Regole (coerenti con docs/R3_SYSTEMONE_CLM_2026-09-29.md):
- Rank NON viene emulato su Jev o r3_clm: senza backend CLM si ricade sul
  selettore storico e il nodo lo dichiara (`selezione="fallback_casuale"`).
- Il ranking è un giudizio di modello, non evidenza: ogni nodo porta
  `provenienza_selezione` per distinguere ciò che è stato davvero eseguito.
- Nessuna azione esterna viene autorizzata da uno score.

Uso:
    from sdq1.sar.scacchiera_clm import ScacchieraCLM
    sc = ScacchieraCLM()
    percorso = sc.ciclo(max_livelli=5)
    print(sc.statistiche_selezione())
"""

from __future__ import annotations

import logging
from typing import Callable, Optional

from .scacchiera_quantica import MotoreQuantico, Nodo, ScacchieraV3, Stato

LOGGER = logging.getLogger(__name__)

DOMANDA_RANK = (
    "Quale sviluppo del pensiero è più fecondo, verificabile e non ridondante "
    "rispetto al nodo padre e alla tensione indicata?"
)

RankFn = Callable[..., dict]


def _rank_default() -> Optional[RankFn]:
    try:
        from typesafe_sister.client import rank
    except Exception:  # dipendenza opzionale (httpx) assente
        return None
    return rank


def _contesto(padre: Optional[Nodo], nodi: list[Nodo]) -> str:
    tensione = nodi[0].tensione if nodi else ("", "", "")
    righe = [
        "Scacchiera Quantica R3 — scelta del prossimo nodo.",
        f"Tensione: {tensione[0]} <-> {tensione[1]} ({tensione[2]})",
    ]
    if padre is not None:
        righe.append(f"Nodo padre (livello {padre.livello}, {padre.direzione}): {padre.contenuto}")
    return "\n".join(righe)


class MotoreQuanticoCLM(MotoreQuantico):
    """MotoreQuantico con scelta del migliore delegata a CLM Rank, se disponibile."""

    def __init__(self, rank_fn: Optional[RankFn] = None, timeout: float = 8):
        super().__init__()
        self._rank_fn = rank_fn if rank_fn is not None else _rank_default()
        self._timeout = timeout
        self.padre_corrente: Optional[Nodo] = None
        self.registro_selezioni: list[dict] = []

    def genera_figlio(self, padre: Nodo, stato: Stato) -> Nodo:
        self.padre_corrente = padre
        return super().genera_figlio(padre, stato)

    def _fallback(self, nodi: list[Nodo], motivo: str) -> Nodo:
        migliore = super().scegli_migliore(nodi)
        migliore.selezione = "fallback_casuale"  # type: ignore[attr-defined]
        migliore.provenienza_selezione = motivo  # type: ignore[attr-defined]
        self.registro_selezioni.append({"selezione": "fallback_casuale", "motivo": motivo})
        return migliore

    def scegli_migliore(self, nodi: list[Nodo]) -> Nodo:
        if not nodi:
            raise ValueError("Nessun nodo da scegliere")
        if self._rank_fn is None:
            return self._fallback(nodi, "rank_non_importabile")

        candidati = [n.contenuto for n in nodi]
        try:
            risultato = self._rank_fn(
                _contesto(self.padre_corrente, nodi), DOMANDA_RANK, candidati,
                timeout=self._timeout,
            )
        except Exception as exc:  # NotConfigured, CapabilityUnavailable, rete, ecc.
            return self._fallback(nodi, type(exc).__name__)

        ranked = risultato.get("ranked") if isinstance(risultato, dict) else None
        if not isinstance(ranked, list) or not ranked:
            return self._fallback(nodi, "risposta_rank_non_valida")

        primo = min(ranked, key=lambda r: r.get("rank", 10**6) if isinstance(r, dict) else 10**6)
        testo = primo.get("candidate") if isinstance(primo, dict) else None
        scelto = next((n for n in nodi if n.contenuto == testo), None)
        if scelto is None:
            return self._fallback(nodi, "candidato_non_riconosciuto")

        scelto.scelto = True
        scelto.selezione = "clm_rank"  # type: ignore[attr-defined]
        scelto.provenienza_selezione = str(risultato.get("_r3_provider", "clm"))  # type: ignore[attr-defined]
        scelto.prob_clm = primo.get("prob")  # type: ignore[attr-defined]
        self.registro_selezioni.append({
            "selezione": "clm_rank",
            "modello": str(risultato.get("model", "unknown"))[:100],
            "prob": primo.get("prob"),
        })
        return scelto


class ScacchieraCLM(ScacchieraV3):
    """ScacchieraV3 con selezione dei nodi via CLM Rank (fallback esplicito)."""

    def __init__(self, stato: Stato = Stato.FOCUS, rank_fn: Optional[RankFn] = None, timeout: float = 8):
        super().__init__(stato=stato)
        self.motore = MotoreQuanticoCLM(rank_fn=rank_fn, timeout=timeout)

    def statistiche_selezione(self) -> dict:
        reg = self.motore.registro_selezioni
        clm = sum(1 for r in reg if r["selezione"] == "clm_rank")
        return {
            "selezioni_totali": len(reg),
            "clm_rank": clm,
            "fallback_casuale": len(reg) - clm,
            "nota_epistemica": "ranking_di_modello_non_evidenza_fattuale",
        }
