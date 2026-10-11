"""Contratto base per gli agenti SDQ-1."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MessaggioAgente:
    mittente: str
    destinatario: str
    casella: int
    payload: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RispostaAgente:
    mittente: str
    successo: bool
    output: dict[str, Any]
    errore: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class AgenteBase(ABC):
    """Tutti gli agenti SDQ-1 implementano questa interfaccia."""

    def __init__(self, agente_id: str, casella: int, modello: str, critico: bool = False):
        self.id = agente_id
        self.casella = casella
        self.modello = modello
        self.critico = critico

    @abstractmethod
    def elabora(self, messaggio: MessaggioAgente) -> RispostaAgente:
        """Elabora un messaggio in ingresso e restituisce una risposta."""

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id} casella={self.casella}>"
