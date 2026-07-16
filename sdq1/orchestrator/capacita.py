"""Registro delle capacità degli agenti — abilita l'orchestrazione dinamica.

Ogni agente dichiara quali capacità offre. L'orchestratore dinamico usa
questo registro per selezionare, ad ogni run, il sottoinsieme minimo di
agenti necessario al task — invece di eseguire sempre la pipeline fissa.

Le capacità possono essere dichiarate esplicitamente nella config
(`agenti_attivi[].capacita`). Se assenti, vengono dedotte dal ruolo.
Questo è il passaggio da *protocollo a piattaforma*: gli agenti non sono
più nodi di una catena rigida, ma competenze componibili.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..config.loader import SDQ1Config

# ---------------------------------------------------------------------------
# Capacità canoniche del sistema
# ---------------------------------------------------------------------------

ANALISI        = "analisi"          # lettura dell'intento, navigazione (RAFFA-001)
DECOMPOSIZIONE = "decomposizione"   # scomposizione in sotto-obiettivi (DECOMP-005)
MEMORIA        = "memoria"          # recupero contesto rilevante (MEMO-002)
SICUREZZA      = "sicurezza"        # filtro identitario / anti-manipolazione (SENTIN-004)
GENERAZIONE    = "generazione"      # produzione della risposta (GEN-006)
STILE          = "stile"            # rifinitura tono e forma (WAVE-003)

# Capacità che devono essere presenti in OGNI piano, qualunque sia il task.
# Senza analisi non c'è direzione; senza sicurezza non c'è tutela dell'identità;
# senza generazione non c'è output.
SEMPRE_ATTIVE: set[str] = {ANALISI, SICUREZZA, GENERAZIONE}

# Fallback: ruolo dichiarato in config → capacità di default.
_RUOLO_CAPACITA: dict[str, set[str]] = {
    "architetto":       {ANALISI},
    "analista_intenti": {DECOMPOSIZIONE},
    "custode":          {MEMORIA},
    "vigilante":        {SICUREZZA},
    "compositore":      {GENERAZIONE},
    "messaggero":       {STILE},
}


@dataclass
class ProfiloCapacita:
    agente_id: str
    capacita: set[str]
    sempre_attivo: bool = False


class RegistroCapacita:
    """Mappa agente → capacità. Costruibile dalla config."""

    def __init__(self, profili: dict[str, ProfiloCapacita]):
        self._profili = profili

    def profilo(self, agente_id: str) -> ProfiloCapacita | None:
        return self._profili.get(agente_id)

    def capacita_di(self, agente_id: str) -> set[str]:
        prof = self._profili.get(agente_id)
        return set(prof.capacita) if prof else set()

    def agenti_per_capacita(self, cap: str) -> list[str]:
        return sorted(p.agente_id for p in self._profili.values() if cap in p.capacita)

    def profili(self) -> dict[str, ProfiloCapacita]:
        return dict(self._profili)

    @classmethod
    def da_config(cls, config: SDQ1Config) -> "RegistroCapacita":
        profili: dict[str, ProfiloCapacita] = {}
        for a in config.agenti:
            if a.capacita:
                caps = {c.strip().lower() for c in a.capacita if c.strip()}
            else:
                caps = set(_RUOLO_CAPACITA.get(a.ruolo, set()))
            profili[a.id] = ProfiloCapacita(
                agente_id=a.id,
                capacita=caps,
                sempre_attivo=bool(caps & SEMPRE_ATTIVE),
            )
        return cls(profili)
