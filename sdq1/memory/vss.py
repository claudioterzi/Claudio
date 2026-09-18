"""VectorStateStore: stato condiviso tra agenti SDQ-1.

Gli agenti scrivono i loro output testuali qui invece di passarli come
blob nel payload. Ogni scrittura produce un pointer_id (stringa).
La lettura può avvenire:
  - direttamente per pointer_id  → O(1)
  - per similarità semantica      → filtrabile per run_id

Questo riduce i payload tra nodi e consente a qualsiasi agente di
recuperare contenuto rilevante da tutti i nodi precedenti dello stesso run.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .store import MemoriaVettoriale, RisultatoRicerca


class VectorStateStore:
    """Store condiviso; un'istanza per tutta la vita dell'app.

    NOTA PERSISTENZA: fino al commit 155cb5f lo store era solo in-process
    (la continuita' tra sessioni restava affidata ai file git).
    salva()/carica() lo rendono sopravvivibile tra run diversi su disco.
    """

    def __init__(self, memoria: MemoriaVettoriale):
        self._mem = memoria
        self._idx: dict[str, str] = {}  # pointer_id -> testo originale

    # ------------------------------------------------------------------ #
    # Scrittura                                                            #
    # ------------------------------------------------------------------ #

    def scrivi(self, testo: str, run_id: str, agente_id: str, chiave: str) -> str:
        """Salva il testo nel VSS e restituisce il pointer_id."""
        if not testo:
            return ""
        ptr = f"{run_id}:{agente_id}:{chiave}"
        self._mem.aggiungi(
            testo,
            metadata={
                "run_id": run_id,
                "agente_id": agente_id,
                "chiave": chiave,
                "ptr": ptr,
            },
        )
        self._idx[ptr] = testo
        return ptr

    # ------------------------------------------------------------------ #
    # Lettura diretta                                                      #
    # ------------------------------------------------------------------ #

    def leggi(self, ptr: str) -> str | None:
        """Recupera il testo originale da un pointer_id (O(1))."""
        return self._idx.get(ptr)

    # ------------------------------------------------------------------ #
    # Ricerca semantica                                                    #
    # ------------------------------------------------------------------ #

    def cerca_nel_run(
        self,
        query: str,
        run_id: str,
        top_k: int = 3,
        soglia: float = 0.1,
    ) -> list[str]:
        """Restituisce i testi più rilevanti per la query nello stesso run."""
        candidati: list[RisultatoRicerca] = self._mem.cerca(
            query, k=top_k * 4, soglia=soglia
        )
        risultati: list[str] = []
        for r in candidati:
            if r.ricordo.metadata.get("run_id") == run_id:
                risultati.append(r.ricordo.testo)
            if len(risultati) >= top_k:
                break
        return risultati

    def cerca_globale(self, query: str, top_k: int = 3) -> list[str]:
        """Ricerca su tutti i run (utile per MEMO-002 e seed)."""
        return [r.ricordo.testo for r in self._mem.cerca(query, k=top_k)]

    # ------------------------------------------------------------------ #
    # Info                                                                 #
    # ------------------------------------------------------------------ #

    def dimensione(self) -> int:
        return len(self._idx)

    def ptr_del_run(self, run_id: str) -> list[str]:
        """Elenca tutti i pointer appartenenti a un run."""
        return [p for p in self._idx if p.startswith(f"{run_id}:")]

    def esporta(self) -> list[dict]:
        return [{"ptr": ptr, "testo": testo} for ptr, testo in self._idx.items()]

    # ------------------------------------------------------------------ #
    # Persistenza (Fase 1 — fix-bloccanti)                                 #
    # ------------------------------------------------------------------ #

    def salva(self, percorso: str | Path) -> int:
        """Persiste lo stato su JSON. Ritorna il numero di pointer salvati.

        Salva sia l'indice ptr->testo (lettura O(1)) sia i ricordi della
        MemoriaVettoriale (ricerca semantica), cosi' un nuovo processo
        recupera entrambe le modalita'.
        """
        dati = {
            "versione": 1,
            "idx": self.esporta(),
            "ricordi": self._mem.esporta(),
        }
        p = Path(percorso)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(dati, ensure_ascii=False, indent=2),
                     encoding="utf-8")
        return len(self._idx)

    def carica(self, percorso: str | Path) -> int:
        """Ripristina lo stato da JSON. Ritorna il numero di pointer caricati.

        Idempotente: i pointer gia' presenti non vengono duplicati.
        I ricordi sono re-inseriti nella MemoriaVettoriale (nuovi id
        interni, stesso testo e metadata: la ricerca per run_id regge).
        """
        p = Path(percorso)
        if not p.exists():
            return 0
        dati = json.loads(p.read_text(encoding="utf-8"))

        ricordi_esistenti = {
            (m.get("ptr")) for m in
            (r.metadata for r in getattr(self._mem, "_ricordi", {}).values())
        }
        for r in dati.get("ricordi", []):
            ptr = r.get("metadata", {}).get("ptr")
            if ptr and ptr in ricordi_esistenti:
                continue
            self._mem.aggiungi(r["testo"], metadata=r.get("metadata", {}))

        for voce in dati.get("idx", []):
            self._idx.setdefault(voce["ptr"], voce["testo"])
        return len(dati.get("idx", []))
