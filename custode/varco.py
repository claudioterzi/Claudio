"""SOGLIA — registro tag RFID e varco d'uscita.

I gate reader UHF (EPC Gen2 / RAIN RFID) espongono eventi di lettura:
EPC del tag + direzione (dai sensori infrarossi ai lati della porta).
Questo modulo è il livello software sopra quel flusso di eventi: in v2
gli eventi arriveranno dal reader reale via LLRP/MQTT, oggi dal
simulatore incluso — la logica non cambia.

I tag tracciano OGGETTI, mai persone (vincolo di progetto, vedi studio).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Dict, List, Optional


class Direzione(Enum):
    INGRESSO = "ingresso"
    USCITA = "uscita"


@dataclass
class TagRegistrato:
    epc: str                 # codice EPC univoco del tag
    oggetto: str             # es. "libro — Il nome della rosa"
    zona_id: str             # zona d'inventario di appartenenza
    tipo_tag: str = "inlay-carta-uhf"   # oppure "murata-1.25mm" (solo palmare)
    valore_eur: float = 0.0


@dataclass
class EventoVarco:
    epc: str
    direzione: Direzione
    quando: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class Allarme:
    evento: EventoVarco
    tag: TagRegistrato

    def __str__(self) -> str:
        return (f"⚠ USCITA NON AUTORIZZATA: «{self.tag.oggetto}» "
                f"(zona {self.tag.zona_id}, EPC {self.tag.epc}) "
                f"alle {self.evento.quando}")


class RegistroTag:
    """Anagrafica dei tag applicati agli oggetti della casa."""

    def __init__(self):
        self._tag: Dict[str, TagRegistrato] = {}

    def registra(self, tag: TagRegistrato) -> None:
        self._tag[tag.epc] = tag

    def cerca(self, epc: str) -> Optional[TagRegistrato]:
        return self._tag.get(epc)

    def tutti(self) -> List[TagRegistrato]:
        return list(self._tag.values())


class Varco:
    """Varco d'uscita: riceve eventi di lettura e decide se allarmare.

    Politica: allarme solo in USCITA e solo per EPC registrati.
    Gli EPC sconosciuti (tag su oggetti dell'ospite, es. capi d'abbigliamento)
    vengono ignorati e non registrati: minimizzazione dei dati.
    """

    def __init__(self, registro: RegistroTag,
                 notifica: Optional[Callable[[Allarme], None]] = None):
        self._registro = registro
        self._notifica = notifica
        self.allarmi: List[Allarme] = []

    def evento(self, evento: EventoVarco) -> Optional[Allarme]:
        if evento.direzione is not Direzione.USCITA:
            return None
        tag = self._registro.cerca(evento.epc)
        if tag is None:
            return None
        allarme = Allarme(evento=evento, tag=tag)
        self.allarmi.append(allarme)
        if self._notifica:
            self._notifica(allarme)
        return allarme


class SimulatoreVarco:
    """Genera eventi come farebbe un gate reader reale (per demo e test)."""

    def __init__(self, varco: Varco):
        self._varco = varco

    def transito(self, epc: str, direzione: Direzione) -> Optional[Allarme]:
        return self._varco.evento(EventoVarco(epc=epc, direzione=direzione))
