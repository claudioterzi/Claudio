"""Sim-to-Real bridge: converte output WAVE-003 in geometria CadQuery / STEP / G-Code.

Funziona in due modalità:
  · Solo script (.py): sempre disponibile, non richiede CadQuery installato
  · Script + STEP:     richiede `pip install cadquery` (OpenCASCADE)

SICUREZZA: nessun file viene scritto e nessuna esecuzione fisica avviene
senza conferma esplicita dell'operatore (parametro `confermato=True` o
flag `--sim-to-real --conferma` da CLI).
"""

from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import cadquery as cq
    _CQ_OK = True
except ImportError:
    _CQ_OK = False


@dataclass
class ParamGeometria:
    """Parametri estratti dall'output testuale o forniti direttamente."""
    tipo: str = "sfera"          # sfera | cubo | cilindro | custom
    raggio_mm: float = 15.0
    altezza_mm: float = 30.0
    larghezza_mm: float = 30.0
    foro_diametro_mm: float = 5.0
    foro_profondita_mm: float = 12.0
    nome_file: str = "sdq1_output"
    note: str = ""


def _estrai_parametri(testo: str) -> ParamGeometria:
    """Ricava parametri geometrici da testo libero con regex permissive."""
    p = ParamGeometria()
    if re.search(r"sfer|sphere|ball", testo, re.I):
        p.tipo = "sfera"
    elif re.search(r"cubo|cube|box", testo, re.I):
        p.tipo = "cubo"
    elif re.search(r"cilindr|cylinder", testo, re.I):
        p.tipo = "cilindro"

    m = re.search(r"raggio[\s:=]*(\d+(?:\.\d+)?)", testo, re.I)
    if m:
        p.raggio_mm = float(m.group(1))

    m = re.search(r"diametro[\s:=]*(\d+(?:\.\d+)?)", testo, re.I)
    if m:
        p.foro_diametro_mm = float(m.group(1))

    m = re.search(r"profond\w*[\s:=]*(\d+(?:\.\d+)?)", testo, re.I)
    if m:
        p.foro_profondita_mm = float(m.group(1))

    return p


def genera_script(params: ParamGeometria) -> str:
    """Restituisce il codice Python CadQuery come stringa."""
    if params.tipo == "sfera":
        corpo = textwrap.dedent(f"""\
            solido = cq.Workplane("XY").sphere({params.raggio_mm})
            if {params.foro_diametro_mm} > 0:
                solido = (
                    solido
                    .faces(">Z").workplane()
                    .hole(diameter={params.foro_diametro_mm}, depth={params.foro_profondita_mm})
                )
        """)
    elif params.tipo == "cubo":
        corpo = textwrap.dedent(f"""\
            solido = cq.Workplane("XY").box(
                {params.larghezza_mm}, {params.larghezza_mm}, {params.altezza_mm}
            )
        """)
    else:  # cilindro
        corpo = textwrap.dedent(f"""\
            solido = cq.Workplane("XY").cylinder(
                {params.altezza_mm}, {params.raggio_mm}
            )
        """)

    return textwrap.dedent(f"""\
        # SDQ-1 · Sim-to-Real bridge — generato automaticamente
        # Parametri: {params}
        # ATTENZIONE: verificare il toolpath prima di avviare la Pocket NC.

        import cadquery as cq

        {corpo}
        cq.exporters.export(solido, "{params.nome_file}.step")
        print("[+] STEP generato: {params.nome_file}.step")
    """)


class CadBridge:
    """Interfaccia principale del bridge Sim-to-Real."""

    def __init__(self, cartella_output: str | Path = "output/cad"):
        self.cartella = Path(cartella_output)

    def _cartella_pronta(self) -> None:
        self.cartella.mkdir(parents=True, exist_ok=True)

    def elabora(
        self,
        testo_wave: str,
        params: ParamGeometria | None = None,
        confermato: bool = False,
    ) -> dict[str, Any]:
        """
        Genera script e, se CadQuery è disponibile e confermato=True, esporta STEP.

        Returns dict con:
          script_path: percorso al .py generato (o None)
          step_path:   percorso al .step generato (o None)
          cq_disponibile: bool
          confermato: bool
          script: sorgente generata
        """
        p = params or _estrai_parametri(testo_wave)
        script = genera_script(p)
        risultato: dict[str, Any] = {
            "params": p,
            "script": script,
            "script_path": None,
            "step_path": None,
            "cq_disponibile": _CQ_OK,
            "confermato": confermato,
        }

        if not confermato:
            risultato["msg"] = (
                "Script generato ma NON scritto su disco. "
                "Passa confermato=True o usa --sim-to-real --conferma per procedere."
            )
            return risultato

        self._cartella_pronta()
        script_path = self.cartella / f"{p.nome_file}.py"
        script_path.write_text(script, encoding="utf-8")
        risultato["script_path"] = str(script_path)

        if _CQ_OK:
            try:
                exec(compile(script, str(script_path), "exec"),  # noqa: S102
                     {"__file__": str(script_path)})
                step_path = self.cartella / f"{p.nome_file}.step"
                if step_path.exists():
                    risultato["step_path"] = str(step_path)
            except Exception as exc:  # noqa: BLE001
                risultato["cq_errore"] = str(exc)
        else:
            risultato["msg_step"] = (
                "CadQuery non installato: solo script .py generato. "
                "Installa con: conda install -c cadquery cadquery"
            )

        return risultato
