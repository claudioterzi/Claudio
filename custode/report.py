"""Report di check-out: incrocia OCCHIO e SOGLIA.

Una mancanza confermata da entrambe le fonti (l'oggetto manca in foto
E il suo tag è uscito dal varco) è l'evidenza più forte possibile per
la richiesta AirCover/deposito.
"""

from dataclasses import dataclass, field
from typing import List

from custode.modelli import Discrepanza
from custode.varco import Allarme, RegistroTag


@dataclass
class ReportCheckout:
    discrepanze: List[Discrepanza] = field(default_factory=list)
    allarmi_varco: List[Allarme] = field(default_factory=list)

    def incroci(self, registro: RegistroTag) -> List[str]:
        """Mancanze fotografiche confermate da un'uscita al varco."""
        conferme = []
        for d in self.discrepanze:
            if d.mancanti == 0:
                continue
            for a in self.allarmi_varco:
                if a.tag.zona_id == d.zona_id and a.tag.oggetto.lower().startswith(
                        d.oggetto.lower().split(" ")[0]):
                    conferme.append(
                        f"«{a.tag.oggetto}»: mancante in foto (zona {d.zona_id}) "
                        f"E uscito dal varco alle {a.evento.quando} — "
                        f"evidenza doppia, valore {a.tag.valore_eur:.2f} €")
        return conferme

    def testo(self, registro: RegistroTag) -> str:
        righe = ["═══ REPORT CHECK-OUT CUSTODE ═══", ""]
        righe.append(f"OCCHIO — discrepanze fotografiche: {len(self.discrepanze)}")
        righe += [f"  {d}" for d in self.discrepanze] or ["  nessuna"]
        righe.append("")
        righe.append(f"SOGLIA — allarmi al varco: {len(self.allarmi_varco)}")
        righe += [f"  {a}" for a in self.allarmi_varco] or ["  nessuno"]
        righe.append("")
        conferme = self.incroci(registro)
        righe.append(f"INCROCIO — evidenze doppie: {len(conferme)}")
        righe += [f"  ★ {c}" for c in conferme] or ["  nessuna"]
        return "\n".join(righe)
