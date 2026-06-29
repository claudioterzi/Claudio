"""Canone Alpha 0.1 — Motore di collasso (Sistema B).

Dà vita alle 74 carte del Canone Alpha applicando la formula fondativa:

    CARTA + ASSE + POLARITÀ = SIGNIFICATO

Il motore non predice: fa *collassare* un significato dall'incontro tra
la domanda dell'osservatore (→ asse) e il suo contesto interiore (→ polarità).
Coerente col manifesto: «I Tarocchi Quantici non assegnano significati.
Permettono ai significati di emergere.»

Convenzione assi (dal MEMORIA_PROGETTO):
    nord  = radice / inconscio
    est   = azione / futuro
    sud   = emozione / presente
    ovest = riflessione / passato

Polarità: luce = manifestazione costruttiva · ombra = manifestazione d'ombra.
Sono *due manifestazioni della stessa energia*, mai un giudizio.

Zero dipendenze esterne (json, random, re).
"""
from __future__ import annotations

import json
import os
import random
import re
from dataclasses import dataclass, field
from typing import Optional

_QUI = os.path.dirname(os.path.abspath(__file__))
_JSON_DEFAULT = os.path.join(_QUI, "tarocchi_quantici_alpha.json")

ASSI = {
    "nord":  "radice / inconscio",
    "est":   "azione / futuro",
    "sud":   "emozione / presente",
    "ovest": "riflessione / passato",
}
POLARITA = {
    "luce":  "manifestazione costruttiva",
    "ombra": "manifestazione d'ombra",
}

# ── Lessici euristici per il collasso ───────────────────────────────────────
# La domanda fa collassare verso un asse; il contesto verso una polarità.
# Le parole sono confrontate sui *gambi* (match per inclusione) così da
# catturare anche le flessioni: "sentire", "sento", "sentivo"…
_LESSICO_ASSE = {
    "nord": [
        "perché", "perche", "radice", "origine", "inconscio", "profond",
        "paura", "vergogn", "nascond", "blocco", "blocca", "sogn", "ombra",
        "chi sono", "identità", "identita", "senso", "vuoto", "fondo",
    ],
    "est": [
        "fare", "faccio", "agire", "azione", "devo", "dovrei", "futur",
        "domani", "comincia", "inizia", "scelg", "sceglie", "decid",
        "andare", "vado", "cambia", "muover", "muovo", "prossim", "osare",
    ],
    "sud": [
        "sento", "sentire", "senti", "emozion", "adesso", "ora", "present",
        "amore", "amo", "cuore", "provo", "felic", "trist", "rabbia",
        "gioia", "dolore", "vivo", "pancia",
    ],
    "ovest": [
        "passat", "ieri", "ricord", "prima", "rimpiant", "indietro",
        "perso", "perdut", "lasciat", "ho fatto", "ero", "era stato",
        "stato", "memoria", "nostalg", "torna",
    ],
}

_LESSICO_POLARITA = {
    "luce": [
        "spero", "voglio", "pront", "apert", "fiduci", "cresc", "luce",
        "avanti", "forza", "gratitud", "amore", "possibil", "fiorire",
        "coraggio", "sì", "si ", "nuovo", "rinasc", "libero", "liber",
    ],
    "ombra": [
        "paura", "blocc", "buio", "perso", "perdut", "solo", "sola",
        "stanc", "fatica", "dubbi", "ansia", "rabbia", "trist", "non riesco",
        "non ce la", "vuoto", "pesa", "chius", "intrappol", "no ", "mai",
    ],
}


def _conta(testo: str, gambi: list[str]) -> int:
    t = (testo or "").lower()
    return sum(1 for g in gambi if g in t)


@dataclass
class Lettura:
    """Esito di un singolo collasso."""
    carta: str
    simbolo: str
    ciclo: str
    asse: str
    asse_dominio: str
    asse_motivo: str
    polarita: str
    polarita_dominio: str
    polarita_motivo: str
    significato: str          # CARTA + ASSE + POLARITÀ
    manifestazione_gemella: str  # stesso asse, polarità opposta
    formula: str
    sintesi: str

    def to_dict(self) -> dict:
        return {
            "carta": self.carta,
            "simbolo": self.simbolo,
            "ciclo": self.ciclo,
            "asse": self.asse,
            "asse_dominio": self.asse_dominio,
            "asse_motivo": self.asse_motivo,
            "polarita": self.polarita,
            "polarita_dominio": self.polarita_dominio,
            "polarita_motivo": self.polarita_motivo,
            "significato": self.significato,
            "manifestazione_gemella": self.manifestazione_gemella,
            "formula": self.formula,
            "sintesi": self.sintesi,
        }


class CanoneAlpha:
    """Motore di collasso sulle 74 carte del Canone Alpha 0.1."""

    def __init__(self, percorso: Optional[str] = None):
        with open(percorso or _JSON_DEFAULT, encoding="utf-8") as f:
            self._doc = json.load(f)
        self.carte: list[dict] = self._doc["carte"]
        self._per_nome = {c["nome"].lower(): c for c in self.carte}
        self._per_id = {c["id"]: c for c in self.carte}

    # ── lookup ──────────────────────────────────────────────────────────
    def carta_per_nome(self, nome: str) -> Optional[dict]:
        return self._per_nome.get((nome or "").strip().lower())

    def carta_per_id(self, id_: int) -> Optional[dict]:
        return self._per_id.get(id_)

    def estrai(self, rng: Optional[random.Random] = None) -> dict:
        return (rng or random).choice(self.carte)

    # ── scelte di collasso ──────────────────────────────────────────────
    def scegli_asse(self, domanda: str) -> tuple[str, str]:
        """domanda → asse. Ritorna (asse, motivo)."""
        punteggi = {a: _conta(domanda, g) for a, g in _LESSICO_ASSE.items()}
        massimo = max(punteggi.values())
        if massimo == 0:
            # Nessun appiglio: l'asse del presente accoglie la domanda nuda.
            return "sud", "nessun segnale forte: la domanda resta nel presente (sud)"
        asse = max(punteggi, key=lambda a: punteggi[a])
        return asse, f"la domanda risuona con l'asse {asse} ({ASSI[asse]})"

    def scegli_polarita(self, contesto: str) -> tuple[str, str]:
        """contesto → polarità. Ritorna (polarità, motivo)."""
        luce = _conta(contesto, _LESSICO_POLARITA["luce"])
        ombra = _conta(contesto, _LESSICO_POLARITA["ombra"])
        if luce == ombra:
            return "luce", "energia in equilibrio: si legge la faccia costruttiva (luce)"
        if luce > ombra:
            return "luce", "il contesto spinge verso l'apertura (luce)"
        return "ombra", "il contesto porta una tensione da attraversare (ombra)"

    # ── collasso ────────────────────────────────────────────────────────
    def collassa(self, carta: dict, asse: str, polarita: str) -> str:
        return carta[polarita][asse]

    def lettura(
        self,
        domanda: str = "",
        contesto: str = "",
        carta: Optional[str] = None,
        seme: Optional[int] = None,
    ) -> Lettura:
        """Esegue un collasso completo: estrae (o usa) una carta, deriva
        asse dalla domanda e polarità dal contesto, e fa emergere il significato."""
        rng = random.Random(seme) if seme is not None else random
        c = self.carta_per_nome(carta) if carta else None
        if c is None:
            c = self.estrai(rng)

        asse, asse_motivo = self.scegli_asse(domanda)
        polarita, pol_motivo = self.scegli_polarita(contesto)
        opposta = "ombra" if polarita == "luce" else "luce"
        opposta_art = "d'ombra" if opposta == "ombra" else "di luce"

        significato = self.collassa(c, asse, polarita)
        gemella = self.collassa(c, asse, opposta)

        formula = f"{c['nome']} · {asse.capitalize()} · {polarita.capitalize()} = {significato}"
        sintesi = (
            f"Sull'asse {asse} ({ASSI[asse]}), {c['nome']} collassa nella sua "
            f"faccia di {polarita}: «{significato}». La stessa energia, nella sua "
            f"manifestazione {opposta_art}, direbbe «{gemella}». "
            f"Nessuna delle due è il tuo destino: sono la scelta che hai davanti."
        )

        return Lettura(
            carta=c["nome"],
            simbolo=c.get("simbolo", ""),
            ciclo=c.get("ciclo", ""),
            asse=asse,
            asse_dominio=ASSI[asse],
            asse_motivo=asse_motivo,
            polarita=polarita,
            polarita_dominio=POLARITA[polarita],
            polarita_motivo=pol_motivo,
            significato=significato,
            manifestazione_gemella=gemella,
            formula=formula,
            sintesi=sintesi,
        )


# ── prova manuale ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    m = CanoneAlpha()
    print(f"Carte caricate: {len(m.carte)}")
    l = m.lettura(
        domanda="Devo fare un passo verso il futuro?",
        contesto="Ho paura e mi sento bloccato",
        carta="La Ferita",
    )
    print(l.formula)
    print(l.sintesi)
