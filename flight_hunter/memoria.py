"""Memoria dei minimi — la parte «lavora nel tempo» del progetto.

Ogni caccia registra il minimo trovato per (rotta, mese). Con lo storico:
    - si riconoscono i NUOVI minimi (quelli da segnalare);
    - si stima se comprare o aspettare.

L'euristica compra/aspetta è dichiaratamente semplice: confronta il prezzo
attuale con lo storico osservato e con la distanza dalla partenza. Non
pretende di prevedere il futuro — misura quello che ha visto.
"""
from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime

PERCORSO_DEFAULT = os.path.join(os.path.dirname(__file__), "..", "data", "flight_hunter.db")


@dataclass(frozen=True)
class Consiglio:
    azione: str          # "compra" | "aspetta" | "osserva"
    motivo: str
    minimo_storico: float | None
    osservazioni: int


class Memoria:
    def __init__(self, percorso: str = PERCORSO_DEFAULT) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(percorso)), exist_ok=True)
        self._db = sqlite3.connect(percorso)
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS minimi (
                rotta      TEXT NOT NULL,   -- es. "MXP-TIA" o chiave itinerario
                mese       TEXT NOT NULL,   -- YYYY-MM
                giorno     TEXT NOT NULL,   -- giorno del volo più economico
                totale     REAL NOT NULL,   -- costo reale stimato
                rilevato   TEXT NOT NULL    -- timestamp ISO della rilevazione
            )""")
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS osservazioni (
                rotta               TEXT NOT NULL,  -- singola tratta, es. "BGY-TIA"
                giorno_volo         TEXT NOT NULL,  -- YYYY-MM-DD
                prezzo              REAL NOT NULL,  -- tariffa nuda della tratta
                vettore             TEXT NOT NULL,
                giorni_alla_partenza INTEGER,       -- anticipo della rilevazione
                rilevato            TEXT NOT NULL
            )""")
        self._db.commit()

    def registra(self, rotta: str, mese: str, giorno: str, totale: float) -> float | None:
        """Salva la rilevazione. Ritorna il vecchio minimo se questo è un nuovo
        minimo (cioè: c'è qualcosa da festeggiare), altrimenti None."""
        riga = self._db.execute(
            "SELECT MIN(totale) FROM minimi WHERE rotta=? AND mese=?",
            (rotta, mese)).fetchone()
        vecchio = riga[0] if riga and riga[0] is not None else None
        self._db.execute(
            "INSERT INTO minimi (rotta, mese, giorno, totale, rilevato) VALUES (?,?,?,?,?)",
            (rotta, mese, giorno, totale, datetime.now().isoformat(timespec="seconds")))
        self._db.commit()
        if vecchio is None or totale < vecchio - 0.5:
            return vecchio if vecchio is not None else float("inf")
        return None

    def osserva(self, rotta: str, giorno_volo: str, prezzo: float,
                vettore: str, giorni_alla_partenza: int | None = None) -> None:
        """Registra una singola osservazione ricca (la miniera dati nel tempo).

        Dopo mesi di raccolta questa tabella permette analisi vere: curva
        prezzo/anticipo, giorno migliore per comprare, stagionalità per rotta.
        """
        self._db.execute(
            "INSERT INTO osservazioni "
            "(rotta, giorno_volo, prezzo, vettore, giorni_alla_partenza, rilevato) "
            "VALUES (?,?,?,?,?,?)",
            (rotta, giorno_volo, prezzo, vettore, giorni_alla_partenza,
             datetime.now().isoformat(timespec="seconds")))
        self._db.commit()

    def curva_anticipo(self, rotta: str) -> list[tuple[int, float]]:
        """(giorni_alla_partenza, prezzo_medio) — la curva che dice quando comprare."""
        righe = self._db.execute(
            "SELECT giorni_alla_partenza, AVG(prezzo) FROM osservazioni "
            "WHERE rotta=? AND giorni_alla_partenza IS NOT NULL "
            "GROUP BY giorni_alla_partenza ORDER BY giorni_alla_partenza DESC",
            (rotta,)).fetchall()
        return [(int(g), round(pr, 2)) for g, pr in righe]

    def consiglio(self, rotta: str, mese: str, totale_attuale: float) -> Consiglio:
        righe = self._db.execute(
            "SELECT totale FROM minimi WHERE rotta=? AND mese=? ORDER BY totale",
            (rotta, mese)).fetchall()
        prezzi = [r[0] for r in righe]
        n = len(prezzi)
        if n < 3:
            return Consiglio("osserva", "storico troppo corto per giudicare "
                             f"({n} rilevazioni): continua a monitorare",
                             prezzi[0] if prezzi else None, n)

        minimo = prezzi[0]
        mediana = prezzi[n // 2]
        giorni_alla_partenza = None
        try:
            primo_del_mese = date(int(mese[:4]), int(mese[5:7]), 1)
            giorni_alla_partenza = (primo_del_mese - date.today()).days
        except ValueError:
            pass

        if totale_attuale <= minimo * 1.03:
            return Consiglio("compra", "è il minimo mai osservato su questa rotta "
                             f"(storico: {n} rilevazioni, mediana {mediana:.0f}€)", minimo, n)
        if giorni_alla_partenza is not None and giorni_alla_partenza < 30:
            return Consiglio("compra", "meno di 30 giorni alla partenza: sui low cost "
                             "da qui in poi statisticamente si sale", minimo, n)
        if totale_attuale > mediana:
            return Consiglio("aspetta", f"sopra la mediana storica ({mediana:.0f}€): "
                             "probabile finestra migliore più avanti", minimo, n)
        return Consiglio("osserva", "tra minimo e mediana: né affare né rapina — "
                         "monitora ancora qualche giorno", minimo, n)

    def chiudi(self) -> None:
        self._db.close()
