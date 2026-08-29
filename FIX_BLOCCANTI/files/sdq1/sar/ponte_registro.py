"""Ponte SAR -> Registro Ipotesi (Fase 3.1, branch fix-bloccanti).

Prima di questo modulo, P5 e P6 erano applicati a mano su ipotesi scritte
da umani. Qui le conclusioni che la SAR genera da se' (report.sintesi di
ciclo_completo) entrano nel Registro come ipotesi di prima classe, con la
stessa disciplina:

- ogni conclusione DEVE avere un criterio di falsificazione (P6);
  se non ce l'ha, Ipotesi.__post_init__ la marca NON_FALSIFICABILE;
- la SAR non puo' confermare le proprie conclusioni (P5):
  questo modulo registra solo come APERTA e non chiama mai
  applica_valutazione(). La conferma resta un atto esterno.

Id delle ipotesi generate dalla SAR: S1, S2, S3... (distinte dalle H*
mane), calcolati sul contenuto del registro caricato, cosi' i run
successivi non collidono.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import Any, Callable

# registro_ipotesi.py vive nella root del repo, fuori dal package sdq1
try:
    from registro_ipotesi import Registro, Ipotesi
except ImportError:  # pragma: no cover - dipende dal cwd
    _root = Path(__file__).resolve().parents[2]
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    from registro_ipotesi import Registro, Ipotesi

LLMFn = Callable[[str, str], str]

PROMPT_CRITERIO = (
    "Riscrivi questa conclusione come ipotesi falsificabile.\n"
    "Conclusione:\n{conclusione}\n\n"
    "Rispondi in questo formato esatto, due righe:\n"
    "IPOTESI: <una frase, la conclusione come affermazione verificabile>\n"
    "CRITERIO: <cosa, se osservato, la falsificherebbe — concreto e osservabile>\n"
    "Se la conclusione non e' falsificabile in linea di principio, scrivi:\n"
    "IPOTESI: <la frase>\nCRITERIO: NESSUNO"
)


class PonteRegistroSAR:
    """Registra le conclusioni della SAR nel Registro Ipotesi."""

    def __init__(self, percorso: str = "registro_ipotesi.json",
                 llm_fn: LLMFn | None = None):
        self.percorso = percorso
        self._llm = llm_fn
        self._registro = Registro(percorso)
        self._registro.carica()

    # ------------------------------------------------------------------ #
    def _prossimo_id(self) -> str:
        n = 0
        for k in self._registro.ipotesi:
            if k.startswith("S") and k[1:].isdigit():
                n = max(n, int(k[1:]))
        return f"S{n + 1}"

    # ------------------------------------------------------------------ #
    def registra_conclusione(self, conclusione: str, tensione: str) -> dict[str, Any]:
        """Trasforma una sintesi SAR in ipotesi registrata. Ritorna un riepilogo."""
        if not conclusione or conclusione.startswith("[LLM non disponibile]"):
            return {"registrata": False, "motivo": "nessuna conclusione LLM"}

        testo = conclusione.strip()
        criterio = ""
        if self._llm:
            risposta = self._llm(
                "Sei un epistemologo popperiano. Precisione, niente ornamenti.",
                PROMPT_CRITERIO.format(conclusione=conclusione[:2000]),
            )
            for riga in risposta.splitlines():
                if riga.startswith("IPOTESI:"):
                    testo = riga[len("IPOTESI:"):].strip() or testo
                elif riga.startswith("CRITERIO:"):
                    c = riga[len("CRITERIO:"):].strip()
                    criterio = "" if c.upper() == "NESSUNO" else c

        ip = Ipotesi(
            id=self._prossimo_id(),
            testo=testo[:500],
            autore="SAR",
            data_apertura=date.today().isoformat(),
            criterio_falsificazione=criterio,
            note=f"Generata dalla SAR su tensione '{tensione}'. "
                 "P5: la SAR non puo' confermarla — serve occhio esterno.",
        )
        self._registro.apri(ip)
        self._registro.salva()
        return {
            "registrata": True,
            "id": ip.id,
            "stato": ip.stato.value,
            "falsificabile": bool(criterio),
        }

    # ------------------------------------------------------------------ #
    def stato(self) -> str:
        return self._registro.stato_generale()
