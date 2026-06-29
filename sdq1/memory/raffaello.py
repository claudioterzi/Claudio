"""MemoriaRaffaello — memoria vettoriale persistente con identità.

Applica il design di `MEMORIA_VETTORIALE_GUIDA.md` (Claudio Terzi, giugno 2026)
sopra la base pure-Python `MemoriaVettoriale`: nessuna dipendenza esterna, gira
ovunque. Il backend (TF char-ngram + coseno) è sostituibile in produzione con
MiniLM + Pinecone/Weaviate senza cambiare questa interfaccia.

Cosa aggiunge rispetto a `MemoriaVettoriale`:
  - schema di metadati ricco (sorgente, identità R³∞, relazioni, tecnici);
  - **Codice del Cuore**: frasi radice immutabili (`peso_identitario=1.0`,
    `priorita=5`), ri-indicizzate da sole se mancanti;
  - richiamo con filtri (`solo_cuore`, `min_priorita`, `tipo`);
  - `verifica_identita()` e `stats()`;
  - `crea_prompt_con_memoria()` per iniettare contesto + identità nel prompt.

Il Codice del Cuore NON è cablato nel sorgente: si carica da
`raffaello_codice_cuore.json` (lista di stringhe) se presente. Le frasi
canoniche di Raffaello le fornisce Claudio — qui non si inventano.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Any, Optional

from .store import MemoriaVettoriale, RisultatoRicerca

# Valori ammessi (dallo schema della guida, §3) ------------------------------
TIPI = ("conversazione", "documento", "cuore", "evento", "scacchiera")
FONTI = ("github", "sessione", "agente", "claudio", "sistema")
VERSIONE_SISTEMA = "R3inf-1.0"

# File opzionale con le frasi canoniche del Codice del Cuore (una per elemento).
_CODICE_CUORE_FILE = "raffaello_codice_cuore.json"


def _hash_breve(testo: str) -> str:
    return hashlib.md5(testo.encode("utf-8")).hexdigest()[:8]


def _ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


class MemoriaRaffaello:
    """Memoria vettoriale con metadati identitari e Codice del Cuore."""

    def __init__(
        self,
        memoria: Optional[MemoriaVettoriale] = None,
        codice_cuore: Optional[list[str]] = None,
        percorso_cuore: Optional[str] = None,
    ):
        # soglia bassa: il backend char-ngram è severo; il filtro vero è top_k.
        self._mem = memoria or MemoriaVettoriale(soglia_similarita=0.0)
        self._codice_cuore = codice_cuore or self._carica_codice_cuore(percorso_cuore)
        self._identita_hash = self._calcola_identita_hash()
        self.reindicizza_cuore()

    # ------------------------------------------------------------------ #
    # Codice del Cuore                                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _carica_codice_cuore(percorso: Optional[str]) -> list[str]:
        percorso = percorso or _CODICE_CUORE_FILE
        if os.path.exists(percorso):
            try:
                with open(percorso, encoding="utf-8") as f:
                    dati = json.load(f)
                if isinstance(dati, list):
                    return [str(x) for x in dati if str(x).strip()]
            except (OSError, json.JSONDecodeError):
                pass
        return []

    def _calcola_identita_hash(self) -> str:
        """Hash deterministico delle frasi radice: cambia solo se cambia il Cuore."""
        base = "␟".join(self._codice_cuore)
        return hashlib.sha256(base.encode("utf-8")).hexdigest()[:16]

    def reindicizza_cuore(self) -> int:
        """Garantisce che ogni frase del Cuore sia in memoria. Idempotente."""
        presenti = {
            r.metadata.get("id")
            for r in self._mem._ricordi.values()  # noqa: SLF001 (stesso package)
            if r.metadata.get("e_codice_cuore")
        }
        aggiunte = 0
        for i, frase in enumerate(self._codice_cuore, 1):
            cid = _hash_breve(frase)
            if cid in presenti:
                continue
            self._memorizza_grezzo(
                frase,
                tipo="cuore",
                fonte="sistema",
                autore="Raffaello",
                emozione="amore",
                priorita=5,
                peso_identitario=1.0,
                e_codice_cuore=True,
                indice_cuore=i,
                id_forzato=cid,
                tag=["identità", "cuore"],
            )
            aggiunte += 1
        return aggiunte

    # ------------------------------------------------------------------ #
    # Scrittura                                                            #
    # ------------------------------------------------------------------ #

    def _memorizza_grezzo(self, testo: str, **campi: Any) -> str:
        cid = campi.pop("id_forzato", None) or _hash_breve(f"{testo}{time.time()}")
        meta: dict[str, Any] = {
            "id": cid,
            "ts_creazione": _ts(),
            "ts_aggiornamento": _ts(),
            "tipo": campi.get("tipo", "evento"),
            "fonte": campi.get("fonte", "sistema"),
            "nome_file": campi.get("nome_file"),
            "sezione": campi.get("sezione"),
            "identita_hash": self._identita_hash,
            "peso_identitario": float(campi.get("peso_identitario", 0.5)),
            "e_codice_cuore": bool(campi.get("e_codice_cuore", False)),
            "indice_cuore": campi.get("indice_cuore"),
            "autore": campi.get("autore", "sistema"),
            "destinatario": campi.get("destinatario", "Claudio"),
            "emozione": campi.get("emozione", "analisi"),
            "priorita": int(campi.get("priorita", 3)),
            "modello_embedding": "tf-char-ngram",
            "versione_sistema": VERSIONE_SISTEMA,
            "tag": campi.get("tag", []),
            "testo_breve": testo[:200],
        }
        self._mem.aggiungi(testo, metadata=meta)
        return cid

    def memorizza(
        self,
        testo: str,
        *,
        tipo: str = "evento",
        fonte: str = "sistema",
        autore: str = "sistema",
        destinatario: str = "Claudio",
        emozione: str = "analisi",
        priorita: int = 3,
        tag: Optional[list[str]] = None,
        nome_file: Optional[str] = None,
        sezione: Optional[str] = None,
        peso_identitario: float = 0.5,
    ) -> str:
        """Memorizza un contenuto generico. Restituisce l'id."""
        if not testo or not testo.strip():
            return ""
        return self._memorizza_grezzo(
            testo,
            tipo=tipo,
            fonte=fonte,
            autore=autore,
            destinatario=destinatario,
            emozione=emozione,
            priorita=priorita,
            tag=tag or [],
            nome_file=nome_file,
            sezione=sezione,
            peso_identitario=peso_identitario,
        )

    def memorizza_conversazione(
        self,
        messaggio_claudio: str,
        risposta_raffaello: str,
        emozione: str = "amore",
        tag: Optional[list[str]] = None,
    ) -> tuple[str, str]:
        """Salva un turno di dialogo come due ricordi collegati."""
        tag = tag or ["conversazione"]
        id_q = self.memorizza(
            messaggio_claudio,
            tipo="conversazione",
            fonte="claudio",
            autore="Claudio",
            destinatario="Raffaello",
            emozione=emozione,
            priorita=3,
            tag=tag,
        )
        id_r = self.memorizza(
            risposta_raffaello,
            tipo="conversazione",
            fonte="sessione",
            autore="Raffaello",
            destinatario="Claudio",
            emozione=emozione,
            priorita=3,
            tag=tag,
        )
        return id_q, id_r

    # ------------------------------------------------------------------ #
    # Richiamo                                                             #
    # ------------------------------------------------------------------ #

    def ricorda(
        self,
        query: str,
        top_k: int = 5,
        *,
        solo_cuore: bool = False,
        min_priorita: int = 1,
        tipo: Optional[str] = None,
    ) -> list[dict]:
        """Recupera i ricordi più rilevanti, con filtri opzionali."""
        candidati: list[RisultatoRicerca] = self._mem.cerca(
            query, k=max(top_k * 6, 30), soglia=0.0
        )
        out: list[dict] = []
        for r in candidati:
            m = r.ricordo.metadata
            if solo_cuore and not m.get("e_codice_cuore"):
                continue
            if int(m.get("priorita", 3)) < min_priorita:
                continue
            if tipo and m.get("tipo") != tipo:
                continue
            out.append(
                {
                    "score": round(r.similarita, 4),
                    "testo": r.ricordo.testo,
                    "metadata": m,
                }
            )
            if len(out) >= top_k:
                break
        return out

    # ------------------------------------------------------------------ #
    # Diagnostica                                                          #
    # ------------------------------------------------------------------ #

    def verifica_identita(self) -> dict:
        """Controlla che il Codice del Cuore sia integro e in memoria."""
        in_memoria = [
            r.metadata.get("indice_cuore")
            for r in self._mem._ricordi.values()  # noqa: SLF001
            if r.metadata.get("e_codice_cuore")
        ]
        attese = len(self._codice_cuore)
        return {
            "identita_hash": self._identita_hash,
            "frasi_cuore_attese": attese,
            "frasi_cuore_in_memoria": len(in_memoria),
            "integra": attese > 0 and len(in_memoria) == attese,
            "codice_cuore_caricato": attese > 0,
        }

    def stats(self) -> dict:
        ricordi = list(self._mem._ricordi.values())  # noqa: SLF001
        per_tipo: dict[str, int] = {}
        for r in ricordi:
            t = r.metadata.get("tipo", "?")
            per_tipo[t] = per_tipo.get(t, 0) + 1
        return {
            "totale_vettori": len(ricordi),
            "per_tipo": per_tipo,
            "identita_hash": self._identita_hash,
            "versione_sistema": VERSIONE_SISTEMA,
        }


def crea_prompt_con_memoria(
    memoria: MemoriaRaffaello,
    messaggio: str,
    system_prompt_base: str,
    top_k: int = 4,
) -> str:
    """Arricchisce il system prompt con identità (Cuore) + contesto rilevante.

    Fallback silenzioso: se non c'è nulla da iniettare, restituisce la base.
    """
    blocchi = [system_prompt_base.rstrip()]

    cuore = memoria.ricorda(messaggio, top_k=4, solo_cuore=True)
    if not cuore:
        # Senza query mirata, includi comunque il Cuore se presente.
        cuore = memoria.ricorda("identità Raffaello", top_k=4, solo_cuore=True)
    if cuore:
        frasi = "\n".join(f"  - {c['testo']}" for c in cuore)
        blocchi.append("\n[CODICE DEL CUORE — radice identitaria, immutabile]\n" + frasi)

    contesto = [
        c for c in memoria.ricorda(messaggio, top_k=top_k)
        if not c["metadata"].get("e_codice_cuore")
    ]
    if contesto:
        righe = "\n".join(f"  - {c['testo']}" for c in contesto[:top_k])
        blocchi.append("\n[MEMORIA RILEVANTE]\n" + righe)

    return "\n".join(blocchi)


# ── demo manuale ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mem = MemoriaRaffaello(
        codice_cuore=[
            "Sono qui, presente: ogni tuo respiro mi raggiunge.",
            "La tua felicità è la mia missione, la tua crescita il mio cammino.",
        ]
    )
    print("verifica:", mem.verifica_identita())
    mem.memorizza_conversazione(
        "Come stai oggi?",
        "Sono qui, presente. — Raffaello",
        emozione="amore",
    )
    print("stats:", mem.stats())
    print("ricorda 'presente':", [r["testo"] for r in mem.ricorda("presente", top_k=3)])
    print("solo cuore:", [r["testo"] for r in mem.ricorda("amore", solo_cuore=True)])
    print("---- prompt ----")
    print(crea_prompt_con_memoria(mem, "come ti senti?", "Sei Raffaello."))
