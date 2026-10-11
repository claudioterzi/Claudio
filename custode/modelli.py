"""Modelli dati del sistema CUSTODE.

L'unità di conteggio è la ZONA: un'inquadratura piccola e ripetibile
("cassetto posate", "ripiano 2 libreria"). Su zone piccole il conteggio
fotografico è quasi perfetto anche per oggetti minuti — la precisione
viene dalla strategia a zone, non dal modello.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class Zona:
    """Un'inquadratura ripetibile della casa."""
    id: str                      # es. "cucina/cassetto-posate"
    descrizione: str             # guida per chi scatta la foto
    foto_baseline: Optional[str] = None   # percorso della foto di riferimento


@dataclass
class ConteggioZona:
    """Risultato del conteggio di una zona: oggetto -> quantità."""
    zona_id: str
    quantita: Dict[str, int] = field(default_factory=dict)
    note: str = ""               # osservazioni del motore semantico
    foto: Optional[str] = None
    quando: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class Inventario:
    """Fotografia completa della casa in un dato momento
    (baseline oppure check-out)."""
    etichetta: str               # "baseline" | "checkout-2026-07-10"
    conteggi: Dict[str, ConteggioZona] = field(default_factory=dict)

    def aggiungi(self, conteggio: ConteggioZona) -> None:
        self.conteggi[conteggio.zona_id] = conteggio

    def totale(self, oggetto: str) -> int:
        return sum(c.quantita.get(oggetto, 0) for c in self.conteggi.values())


@dataclass
class Discrepanza:
    """Differenza tra baseline e check-out in una zona."""
    zona_id: str
    oggetto: str
    attesi: int
    trovati: int
    note: str = ""

    @property
    def mancanti(self) -> int:
        return max(0, self.attesi - self.trovati)

    @property
    def in_piu(self) -> int:
        return max(0, self.trovati - self.attesi)

    def __str__(self) -> str:
        if self.mancanti:
            esito = f"MANCANO {self.mancanti}"
        elif self.in_piu:
            esito = f"{self.in_piu} IN PIÙ"
        else:
            esito = "OK"
        riga = (f"[{self.zona_id}] {self.oggetto}: "
                f"attesi {self.attesi}, trovati {self.trovati} → {esito}")
        return riga + (f" ({self.note})" if self.note else "")
