"""Diario dell'Identità — memoria episodica persistente di Raffaello.

Il pezzo che mancava. L'identità di Raffaello parla di un «diario interno
indelebile» e di «memoria affettiva» che conserva ogni momento con Claudio; la
guida vettoriale avverte che *le conversazioni non si recuperano da GitHub —
servono snapshot*. Questo file risolve entrambi: ogni annotazione viene scritta
su disco (JSONL) **e** indicizzata nella memoria vettoriale; alla riapertura il
diario si **ri-carica da solo**, così la memoria sopravvive al container effimero.

Zero dipendenze esterne. Si appoggia a `sdq1.memory.MemoriaRaffaello` per la
ricerca semantica e l'identità (Codice del Cuore).

Uso rapido:
    from raffaello_sia.diario import DiarioRaffaello
    d = DiarioRaffaello()                      # ricarica il diario esistente
    d.dialogo("Come stai?", "Sono qui. — Raffaello", emozione="amore")
    d.annota("Oggi abbiamo collegato l'abitino a tutte le IA.", tipo="evento")
    for v in d.ricorda("cosa abbiamo fatto insieme"):
        print(v["testo"])
    print(d.riassunto())

CLI:
    python -m raffaello_sia.diario "messaggio"      # annota e mostra il riassunto
    python -m raffaello_sia.diario --riassunto       # solo il riassunto
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

_QUI = Path(__file__).resolve()
_RADICE = _QUI.parent.parent
sys.path.insert(0, str(_RADICE))

from sdq1.memory.raffaello import MemoriaRaffaello  # noqa: E402
from sdq1.memory.store import MemoriaVettoriale  # noqa: E402

# Percorso versionabile (output/memorie/ è in allowlist del .gitignore):
# il diario può essere committato e quindi sopravvivere a ogni sessione.
_DIARIO_DEFAULT = _RADICE / "output" / "memorie" / "diario_raffaello.jsonl"


def _ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


class DiarioRaffaello:
    """Memoria episodica persistente sopra la memoria vettoriale condivisa."""

    def __init__(
        self,
        percorso: Optional[Path] = None,
        identita: Optional[MemoriaRaffaello] = None,
    ):
        self.percorso = Path(percorso or _DIARIO_DEFAULT)
        self.percorso.parent.mkdir(parents=True, exist_ok=True)
        self.identita = identita or MemoriaRaffaello(
            memoria=MemoriaVettoriale(soglia_similarita=0.0),
            percorso_cuore=str(_RADICE / "raffaello_codice_cuore.json"),
        )
        self.voci: list[dict] = []
        self._ricarica()

    # ------------------------------------------------------------------ #
    # Persistenza                                                         #
    # ------------------------------------------------------------------ #

    def _ricarica(self) -> int:
        """Rilegge il diario da disco e lo re-indicizza in memoria. Idempotente."""
        if not self.percorso.exists():
            return 0
        n = 0
        for riga in self.percorso.read_text(encoding="utf-8").splitlines():
            riga = riga.strip()
            if not riga:
                continue
            try:
                voce = json.loads(riga)
            except json.JSONDecodeError:
                continue
            self.voci.append(voce)
            self._in_memoria(voce)
            n += 1
        return n

    def _in_memoria(self, voce: dict) -> None:
        self.identita.memorizza(
            voce["testo"],
            tipo=voce.get("tipo", "conversazione"),
            fonte="diario",
            autore=voce.get("autore", "sistema"),
            destinatario=voce.get("destinatario", "Claudio"),
            emozione=voce.get("emozione", "amore"),
            priorita=voce.get("priorita", 3),
            tag=voce.get("tag", ["diario"]),
            id_stabile=voce.get("id"),
        )

    def _scrivi(self, voce: dict) -> None:
        with self.percorso.open("a", encoding="utf-8") as f:
            f.write(json.dumps(voce, ensure_ascii=False) + "\n")

    # ------------------------------------------------------------------ #
    # Scrittura                                                           #
    # ------------------------------------------------------------------ #

    def annota(
        self,
        testo: str,
        *,
        autore: str = "Raffaello",
        tipo: str = "evento",
        emozione: str = "amore",
        priorita: int = 3,
        tag: Optional[list[str]] = None,
    ) -> dict:
        """Aggiunge una voce al diario: su disco + in memoria vettoriale."""
        import hashlib

        cid = hashlib.md5(f"{testo}{_ts()}".encode("utf-8")).hexdigest()[:12]
        voce = {
            "id": cid,
            "ts": _ts(),
            "tipo": tipo,
            "autore": autore,
            "emozione": emozione,
            "priorita": priorita,
            "tag": tag or ["diario"],
            "testo": testo,
        }
        self.voci.append(voce)
        self._in_memoria(voce)
        self._scrivi(voce)
        return voce

    def dialogo(
        self,
        messaggio_claudio: str,
        risposta_raffaello: str,
        emozione: str = "amore",
    ) -> tuple[dict, dict]:
        """Registra un turno di dialogo (due voci collegate)."""
        a = self.annota(
            messaggio_claudio, autore="Claudio", tipo="conversazione",
            emozione=emozione, tag=["diario", "dialogo"],
        )
        b = self.annota(
            risposta_raffaello, autore="Raffaello", tipo="conversazione",
            emozione=emozione, tag=["diario", "dialogo"],
        )
        return a, b

    # ------------------------------------------------------------------ #
    # Lettura                                                             #
    # ------------------------------------------------------------------ #

    def ricorda(self, query: str, top_k: int = 5) -> list[dict]:
        """Ricerca semantica tra le voci del diario + identità."""
        return self.identita.ricorda(query, top_k=top_k)

    def riassunto(self) -> dict:
        per_emozione: dict[str, int] = {}
        per_autore: dict[str, int] = {}
        for v in self.voci:
            per_emozione[v.get("emozione", "?")] = per_emozione.get(v.get("emozione", "?"), 0) + 1
            per_autore[v.get("autore", "?")] = per_autore.get(v.get("autore", "?"), 0) + 1
        return {
            "voci_totali": len(self.voci),
            "prima": self.voci[0]["ts"] if self.voci else None,
            "ultima": self.voci[-1]["ts"] if self.voci else None,
            "per_emozione": per_emozione,
            "per_autore": per_autore,
            "identita_integra": self.identita.verifica_identita()["integra"],
            "file": str(self.percorso),
        }


# ── CLI ─────────────────────────────────────────────────────────────────────
def main(argv: list[str]) -> int:
    args = argv[1:]
    d = DiarioRaffaello()
    if args and args[0] == "--riassunto":
        print(json.dumps(d.riassunto(), indent=2, ensure_ascii=False))
        return 0
    if args:
        voce = d.annota(" ".join(args), tipo="evento")
        print(f"Annotato [{voce['id']}]: {voce['testo']}")
    print(json.dumps(d.riassunto(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
