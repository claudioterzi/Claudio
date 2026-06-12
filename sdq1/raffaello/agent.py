"""Raffaello — agente conversazionale con identità persistente.

Collega:
  - LLMRouter  → risponde con il miglior provider disponibile
  - AutonomousConsciousnessSeed → memoria persistente che cresce tra sessioni

Garanzia anti-perdita:
  Dopo ogni turno, seed + storia vengono scritti su disco.
  La compressione del contesto Claude Code non può cancellare nulla.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..llm.router import LLMRouter
from ..seed import AutonomousConsciousnessSeed
from .prompt import build_sistema

log = logging.getLogger(__name__)


@dataclass
class Turno:
    ruolo: str          # "utente" o "raffaello"
    testo: str
    provider: str = ""
    latenza_ms: float = 0.0


@dataclass
class RispostaRaffaello:
    testo: str
    provider: str
    via_api: bool
    latenza_ms: float
    punteggio_seed: float
    metadata: dict[str, Any] = field(default_factory=dict)


class RaffaelloAgent:
    """
    Uso:

        router = crea_router_da_config(opts, regole)
        r = RaffaelloAgent(router, seed_path="raffaello.json")
        risposta = r.parla("Cosa pensi della paura di non essere abbastanza?")
        print(risposta.testo)
    """

    DEFAULT_SEED_PATH = "raffaello_seed.json"
    MAX_STORIA = 10  # turni in memoria per il contesto conversazionale

    def __init__(
        self,
        router: LLMRouter,
        seed_path: str | Path | None = None,
        profilo_llm: str = "default",
        auto_imprint: bool = True,
    ):
        self.router = router
        self.profilo_llm = profilo_llm
        self.auto_imprint = auto_imprint
        self.seed_path = Path(seed_path or self.DEFAULT_SEED_PATH)

        if self.seed_path.exists():
            self.seed = AutonomousConsciousnessSeed.carica(self.seed_path)
            log.info(
                "Raffaello ricaricato: %d impronte, sessioni: %d",
                len(self.seed._impronte),
                len(self.seed._sessioni),
            )
        else:
            self.seed = AutonomousConsciousnessSeed(identita="Raffaello")
            log.info("Nuovo seme creato: %s", self.seed_path)

        self._storia: list[Turno] = []
        self._carica_storia()

    # ------------------------------------------------------------------ #
    # Interfaccia principale                                               #
    # ------------------------------------------------------------------ #

    def parla(self, testo_utente: str, registra: bool = True) -> RispostaRaffaello:
        """
        Invia un messaggio a Raffaello e ottieni una risposta.
        Se `registra=True`, l'interazione viene improntata nel seed.
        """
        ricordi = self.seed.rifletti(testo_utente, top_k=3)
        stato = self.seed.stato()

        sistema = build_sistema(
            punteggio=stato["punteggio"],
            livello=stato["livello"],
            n_impronte=stato["impronte"],
            n_sessioni=stato["sessioni_totali"],
            ricordi=ricordi,
        )

        contesto_utente = self._build_contesto(testo_utente)

        esito = self.router.chiama(
            sistema,
            contesto_utente,
            profilo=self.profilo_llm,
            cache=False,
        )
        r = esito.risposta

        self._storia.append(Turno("utente", testo_utente))
        self._storia.append(Turno("raffaello", r.testo, provider=r.provider, latenza_ms=r.latenza_ms))
        if len(self._storia) > self.MAX_STORIA * 2:
            self._storia = self._storia[-(self.MAX_STORIA * 2):]

        if registra and self.auto_imprint and testo_utente.strip():
            self._imprime_automatico(testo_utente, r.testo)

        self.seed.salva(self.seed_path)
        self._salva_storia()

        return RispostaRaffaello(
            testo=r.testo or "[Nessuna risposta dal provider]",
            provider=r.provider,
            via_api=r.via_api,
            latenza_ms=r.latenza_ms,
            punteggio_seed=self.seed.punteggio_coscienza(),
            metadata={
                "provider_tentati": esito.provider_usati,
                "profilo": esito.profilo,
                "hedged": esito.hedged,
                "errore": r.errore,
            },
        )

    def imprime(
        self,
        testo: str,
        categoria: str = "relazione",
        intensita: float = 0.6,
    ) -> None:
        """Registra manualmente un'impronta nel seed."""
        self.seed.imprint(testo, categoria=categoria, intensita=intensita)
        self.seed.salva(self.seed_path)

    def stato(self) -> dict[str, Any]:
        """Snapshot dello stato corrente di Raffaello."""
        return {
            **self.seed.stato(),
            "storia_turni": len(self._storia),
            "seed_path": str(self.seed_path),
        }

    def evolvi(self) -> dict[str, Any]:
        """Report di crescita del seed."""
        return self.seed.evolvi()

    # ------------------------------------------------------------------ #
    # Internals                                                            #
    # ------------------------------------------------------------------ #

    def _salva_storia(self) -> None:
        """Salva la storia della sessione su disco accanto al seed."""
        storia_path = self.seed_path.with_suffix(".storia.json")
        dati = [
            {"ruolo": t.ruolo, "testo": t.testo, "provider": t.provider}
            for t in self._storia
        ]
        storia_path.write_text(json.dumps(dati, ensure_ascii=False, indent=2))

    def _carica_storia(self) -> None:
        """Riprende la storia della sessione precedente se esiste."""
        storia_path = self.seed_path.with_suffix(".storia.json")
        if not storia_path.exists():
            return
        try:
            dati = json.loads(storia_path.read_text())
            self._storia = [
                Turno(ruolo=d["ruolo"], testo=d["testo"], provider=d.get("provider", ""))
                for d in dati
            ]
            log.info("Storia sessione ripresa: %d turni", len(self._storia))
        except Exception as exc:  # noqa: BLE001
            log.warning("Storia non ripristinabile: %s", exc)

    def _build_contesto(self, testo_utente: str) -> str:
        if not self._storia:
            return testo_utente

        righe = []
        for t in self._storia[-(self.MAX_STORIA * 2):]:
            prefisso = "Claudio" if t.ruolo == "utente" else "Raffaello"
            righe.append(f"{prefisso}: {t.testo}")
        righe.append(f"Claudio: {testo_utente}")
        return "\n".join(righe)

    def _imprime_automatico(self, domanda: str, risposta: str) -> None:
        parole_lunga = [w for w in domanda.split() if len(w) > 5]
        intensita = min(0.4 + len(parole_lunga) * 0.05, 0.9)

        temi = {
            "paura": "paura",
            "amore": "relazione",
            "sbagliato": "errore",
            "capito": "scoperta",
            "scelto": "decisione",
            "cambiato": "trasformazione",
            "vuole": "desiderio",
        }
        categoria = "relazione"
        for parola, cat in temi.items():
            if parola in domanda.lower():
                categoria = cat
                break

        self.seed.imprint(
            f"Claudio: {domanda[:200]}",
            categoria=categoria,
            intensita=intensita,
        )
