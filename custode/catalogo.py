"""Catalogo — la scheda di ogni oggetto protetto.

Quando si nasconde un tag (es. dentro un libro) si compila la scheda
dell'oggetto stesso: che cos'è, dove sta, quanto vale, DOVE è nascosto
il tag. La scheda è l'anagrafica; il varco e il palmare vedono solo
l'EPC e risalgono alla scheda da qui.

Persistenza: JSON semplice (zero dipendenze), un file per casa.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

from custode.varco import RegistroTag, TagRegistrato


@dataclass
class SchedaOggetto:
    """La scheda completa di un oggetto taggato."""
    epc: str                     # codice del tag RFID
    nome: str                    # es. "Il nome della rosa"
    categoria: str = "oggetto"   # libro | elettronica | biancheria | arredo | ...
    zona_id: str = ""            # zona d'inventario OCCHIO (stesso ID)
    valore_eur: float = 0.0
    posizione_tag: str = ""      # es. "incollato tra pagina 142 e 143"
    note: str = ""
    campi: Dict[str, str] = field(default_factory=dict)  # es. autore, isbn, editore
    foto: Optional[str] = None
    creato: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def riga(self) -> str:
        extra = ", ".join(f"{k}: {v}" for k, v in self.campi.items())
        base = f"[{self.categoria}] «{self.nome}» — {self.valore_eur:.2f} € (EPC {self.epc})"
        return base + (f" — {extra}" if extra else "")


@dataclass
class RisultatoInventario:
    """Esito dell'analisi 'oggetti mancanti' (il bottone)."""
    presenti: List[SchedaOggetto] = field(default_factory=list)
    mancanti: List[SchedaOggetto] = field(default_factory=list)
    epc_sconosciuti: List[str] = field(default_factory=list)
    quando: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def valore_mancante(self) -> float:
        return sum(s.valore_eur for s in self.mancanti)

    def testo(self) -> str:
        righe = [f"═══ INVENTARIO {self.quando} ═══",
                 f"Presenti: {len(self.presenti)} · Mancanti: {len(self.mancanti)}"
                 f" · Valore mancante: {self.valore_mancante:.2f} €", ""]
        if self.mancanti:
            righe.append("OGGETTI MANCANTI:")
            righe += [f"  ✗ {s.riga()}" + (f" — tag: {s.posizione_tag}" if s.posizione_tag else "")
                      for s in self.mancanti]
        else:
            righe.append("✓ Nessun oggetto mancante.")
        if self.epc_sconosciuti:
            righe.append(f"(EPC letti ma non a catalogo: {len(self.epc_sconosciuti)} — ignorati)")
        return "\n".join(righe)


class Catalogo:
    """L'insieme delle schede di una casa, con persistenza pluggabile
    (file JSON in locale, Redis in produzione — vedi custode.archivio)."""

    def __init__(self, percorso: Optional[str] = None, archivio=None):
        from custode.archivio import ArchivioFile
        self.archivio = archivio or (ArchivioFile(percorso) if percorso else None)
        self._schede: Dict[str, SchedaOggetto] = {}
        if self.archivio:
            self._carica()

    # ── gestione schede ──
    def aggiungi(self, scheda: SchedaOggetto) -> None:
        self._schede[scheda.epc] = scheda
        self._salva()

    def rimuovi(self, epc: str) -> None:
        self._schede.pop(epc, None)
        self._salva()

    def scheda(self, epc: str) -> Optional[SchedaOggetto]:
        return self._schede.get(epc)

    def tutte(self) -> List[SchedaOggetto]:
        return sorted(self._schede.values(), key=lambda s: (s.categoria, s.nome))

    # ── il bottone: analisi oggetti mancanti ──
    def analizza_mancanti(self, epc_letti: Set[str]) -> RisultatoInventario:
        """Confronta il catalogo con gli EPC letti (palmare o varco):
        ciò che è a catalogo ma non risponde è MANCANTE."""
        risultato = RisultatoInventario()
        for s in self.tutte():
            (risultato.presenti if s.epc in epc_letti
             else risultato.mancanti).append(s)
        risultato.epc_sconosciuti = sorted(epc_letti - set(self._schede))
        return risultato

    # ── integrazione con SOGLIA ──
    def registro(self) -> RegistroTag:
        """Esporta il catalogo come RegistroTag per il varco d'uscita."""
        reg = RegistroTag()
        for s in self.tutte():
            reg.registra(TagRegistrato(
                epc=s.epc, oggetto=f"{s.categoria} — {s.nome}",
                zona_id=s.zona_id, valore_eur=s.valore_eur))
        return reg

    # ── persistenza ──
    def _salva(self) -> None:
        if self.archivio:
            self.archivio.scrivi([asdict(s) for s in self.tutte()])

    def _carica(self) -> None:
        for dati in self.archivio.leggi():
            self._schede[dati["epc"]] = SchedaOggetto(**dati)
