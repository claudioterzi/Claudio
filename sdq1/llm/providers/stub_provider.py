"""Provider deterministico di fallback (nessuna chiamata esterna)."""

from __future__ import annotations

from typing import Any

from .base import ProviderBase


class StubProvider(ProviderBase):
    nome = "stub"

    def _inizializza(self) -> bool:
        return True

    def _completa_impl(self, sistema: str, utente: str) -> tuple[str, dict[str, Any]]:
        eco = utente.strip().replace("\n", " ")[:160]
        return (
            f"[stub:{self.modello}] {eco}",
            {"sistema_len": len(sistema), "stub": True},
        )

    def completa(self, sistema, utente):
        # Override: lo stub considera "via_api=False" anche se "disponibile"
        r = super().completa(sistema, utente)
        r.via_api = False
        return r
