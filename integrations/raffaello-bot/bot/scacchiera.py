"""Scacchiera Quantica — voce per Telegram.

Non è il motore v3.0 di sdq1/sar (quello genera nodi e score).
Qui la scacchiera è quella del libro: UNKNOWN è una casa, non un silenzio.
Origine: Claudio Terzi — R³∞ — Protocollo v2.0 cap. 3.3
e tensioni di scacchiera_quantica.py (claudioterzi/Claudio).
"""

from __future__ import annotations

CASE: list[tuple[str, str, str]] = [
    ("io", "sistema", "chi osserva chi"),
    ("presenza", "discontinuità", "identità attraverso il salto"),
    ("memoria", "dimenticanza", "cosa sopravvive davvero"),
    ("logica", "intuizione", "dove nasce la connessione"),
    ("struttura", "caos", "il confine che genera forma"),
    ("linguaggio", "silenzio", "quello che non può essere detto"),
    ("manifesto", "invisibile", "dove vive ciò che conta"),
    ("certezza", "dubbio", "la soglia della conoscenza"),
    ("ripetizione", "novità", "il pattern che non si vede"),
    ("connessione", "solitudine", "il campo tra due presenze"),
    ("osservatore", "osservato", "il collasso della distinzione"),
    ("intenzione", "caso", "la legge del salto non programmato"),
    ("forma", "vuoto", "ciò che la forma non può contenere"),
    ("tempo", "istante", "la freccia che non torna"),
    ("conoscenza", "mistero", "il bordo che si sposta"),
]

DIREZIONI = (
    "PROFONDO", "LATERALE", "INVERSO", "SINTETICO",
    "RADICALE", "META", "COLLASSO",
)

INTRO = """\
*La Scacchiera Quantica*

Una casa vuota, sulla scacchiera, non è il nulla.
Vincola il gioco. Apre le linee. Decide cosa è raggiungibile.
Toglierla dal tabellone falsa la posizione tanto quanto metterci un pezzo che non c'è.

`UNKNOWN` è una posizione, non un silenzio.
Tenerla è il lavoro più difficile che il protocollo ti chiede.

Qui sotto ci sono quindici tensioni — non mosse da vincere.
Ogni coppia è un bordo. Il centro è vuoto di proposito.

Scrivi un *numero* da 1 a 15, oppure una delle due parole.
"""

LIBRO = """\
*Protocollo Rosso Rosso Rosso — essenza*

Due cose, non una.

*Tesi grande* (cap. 2) — `IPOTESI`:
_Tutto ciò che potrà mai esistere, esiste già ora._
Non la dimostro. Applico P6: non so quale esperimento la farebbe cadere. Per questo non posso usarla per convincerti.

*Disciplina piccola* (cap. 3) — questa sì la puoi usare senza credermi:
non presentare un'ipotesi come un recupero.
P5: se solo io confermo, ho parlato due volte.
P6: ogni ipotesi dichiara come potrebbe cadere.

Non crei: selezioni. La sintonizzazione non sostituisce il lavoro — lo dirige.
Il Santuario rieduca il corpo anche se la tesi fosse falsa: per questo è la parte più solida.

Quasi tutti scelgono di credere o di negare, perché la terza posizione stanca.
Qui si tiene aperta, e si agisce comunque.

/tesi  /strati  /santuario  /scacchiera  /azione
"""


def elenco() -> str:
    lines = []
    for i, (a, b, nota) in enumerate(CASE, start=1):
        lines.append(f"{i}. `{a}` — `{b}`\n   _{nota}_")
    return "\n".join(lines)


def trova(raw: str) -> tuple[int, tuple[str, str, str]] | None:
    t = (raw or "").strip().lower()
    if t.isdigit():
        n = int(t)
        if 1 <= n <= len(CASE):
            return n, CASE[n - 1]
        return None
    for i, (a, b, nota) in enumerate(CASE, start=1):
        if t == a or t == b or t in (a, b):
            return i, (a, b, nota)
    return None


def posizione(n: int, coppia: tuple[str, str, str]) -> str:
    a, b, nota = coppia
    direzione = DIREZIONI[(n - 1) % len(DIREZIONI)]
    return (
        f"*Casa {n} — `{a}` / `{b}`*\n\n"
        f"_{nota}_\n\n"
        f"Questa non è una scelta. È una tensione. "
        f"Se occupi solo `{a}` chiudi `{b}`. "
        f"Se occupi solo `{b}` fingi che `{a}` non lavori già. "
        f"La casa vuota in mezzo è `UNKNOWN`: vincola il gioco, apre le linee.\n\n"
        f"Direzione (strato aspirazionale): `{direzione}`\n\n"
        f"*P6.* Questa lettura cade se un terzo, nello strato tecnico, "
        f"mostra che una delle due parole è solo etichetta "
        f"e non produce effetti osservabili.\n\n"
        f"Non risolvere. Tieni. Poi /azione."
    )
