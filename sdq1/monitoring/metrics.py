"""Raccolta metriche per chiamata LLM, persistite via StatoStore."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

from ..persistence.store import StatoStore


@dataclass
class MetricaChiamata:
    id: str
    timestamp: float
    profilo: str
    provider: str
    modello: str
    successo: bool
    latenza_ms: int
    input_tokens: int | None = None
    output_tokens: int | None = None
    errore: str | None = None
    fallback_da: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MetricsCollector:
    """Registra metriche e calcola aggregati su finestra mobile."""

    def __init__(
        self,
        stato: StatoStore,
        prefisso: str = "metriche:",
        ttl_secondi: int = 86400,
        max_in_memoria: int = 500,
    ):
        self.stato = stato
        self.prefisso = prefisso
        self.ttl = ttl_secondi
        self.max_in_memoria = max_in_memoria
        self._recenti: list[MetricaChiamata] = []

    def registra(
        self,
        profilo: str,
        provider: str,
        modello: str,
        successo: bool,
        latenza_ms: int,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        errore: str | None = None,
        fallback_da: list[str] | None = None,
    ) -> MetricaChiamata:
        m = MetricaChiamata(
            id=uuid.uuid4().hex[:12],
            timestamp=time.time(),
            profilo=profilo,
            provider=provider,
            modello=modello,
            successo=successo,
            latenza_ms=latenza_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            errore=errore,
            fallback_da=fallback_da or [],
        )
        self._recenti.append(m)
        if len(self._recenti) > self.max_in_memoria:
            self._recenti = self._recenti[-self.max_in_memoria :]
        try:
            self.stato.set(f"{self.prefisso}{m.id}", m.to_dict(), ttl_secondi=self.ttl)
        except Exception:  # noqa: BLE001
            pass
        return m

    def aggregati(self) -> dict[str, Any]:
        if not self._recenti:
            return {
                "chiamate_totali": 0,
                "tasso_successo": 0.0,
                "latenza_media_ms": 0,
                "per_provider": {},
            }
        tot = len(self._recenti)
        ok = sum(1 for m in self._recenti if m.successo)
        latenze = [m.latenza_ms for m in self._recenti if m.successo]
        latenza_media = sum(latenze) // len(latenze) if latenze else 0

        per_provider: dict[str, dict[str, Any]] = {}
        for m in self._recenti:
            p = per_provider.setdefault(
                m.provider,
                {"chiamate": 0, "successi": 0, "latenze": [], "errori_recenti": []},
            )
            p["chiamate"] += 1
            if m.successo:
                p["successi"] += 1
                p["latenze"].append(m.latenza_ms)
            elif m.errore:
                p["errori_recenti"].append(m.errore[:200])

        for nome, p in per_provider.items():
            latenze_p = p.pop("latenze")
            errori = p.pop("errori_recenti")
            p["tasso_successo"] = round(p["successi"] / p["chiamate"], 3)
            p["latenza_media_ms"] = (
                sum(latenze_p) // len(latenze_p) if latenze_p else 0
            )
            p["errori_recenti"] = errori[-3:]

        return {
            "chiamate_totali": tot,
            "tasso_successo": round(ok / tot, 3),
            "latenza_media_ms": latenza_media,
            "per_provider": per_provider,
        }

    def esporta_json(self) -> str:
        return json.dumps(self.aggregati(), indent=2, ensure_ascii=False)
