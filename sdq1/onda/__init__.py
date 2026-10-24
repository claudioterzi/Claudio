"""
SDQ-1 · ONDA — il bus nervoso degli agenti (v1.1.1)

Sottosistema asincrono su Redis pub/sub, distinto dall'orchestratore
sincrono in `sdq1/orchestrator/gerarchico.py`. Qui gli agenti sono processi
indipendenti che dialogano via bus: l'Architetto (RAFFA-001) orchestra,
gli altri eseguono per capacità.

I nodi usano import piatti (`import bus_onda`): si avviano come script dalla
loro cartella, ciascuno nel proprio processo (es. `python raffa_001.py`).
"""

from .bus_onda import (
    AgenteONDA, Busta, BusONDA, scrivi_audit,
    PROTOCOLLO, PREFISSO,
    CANALE_COMANDI, CANALE_RISPOSTE, CANALE_EVENTI,
    TTL_REGISTRO, TIMEOUT_ACK,
    canale_agente, chiave_registro, chiave_stato, chiave_heartbeat,
)

__all__ = [
    "AgenteONDA", "Busta", "BusONDA", "scrivi_audit",
    "PROTOCOLLO", "PREFISSO",
    "CANALE_COMANDI", "CANALE_RISPOSTE", "CANALE_EVENTI",
    "TTL_REGISTRO", "TIMEOUT_ACK",
    "canale_agente", "chiave_registro", "chiave_stato", "chiave_heartbeat",
]
