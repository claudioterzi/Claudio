"""Regola di rifiuto del SEME R³∞ v1.1, eseguita invece che chiesta.

Il seme chiede a ogni nodo di rifiutare un handoff non conforme. Affidarlo al
modello significa sperare che obbedisca; qui il controllo è deterministico e
dà lo stesso verdetto su qualunque macchina.

Cosa controlla (forma, non verità):
  1. i cinque campi STATO / SCOPERTA / LIMITE / PROSSIMA MOSSA / EVIDENZA
     ci sono tutti, una volta sola, non vuoti;
  2. niente testo prima del primo campo (il seme: «esclusivamente questi 5 campi»);
  3. STATO non contiene mosse future: i «campi mescolati» del seme;
  4. EVIDENZA contiene almeno un riferimento che un terzo può aprire:
     un file con estensione, un hash, un URL. «Il documento che segue» non lo è;
  5. (v1.2) tutto ciò che segue una riga `ALLEGATO:` è carico, non handoff:
     non viene letto come campi. Se EVIDENZA cita `sha256:<hash>`, l'hash deve
     essere quello dell'allegato — la prova si ricalcola, non si dichiara.

Cosa NON controlla: che lo STATO sia vero. Un handoff può passare con
contenuto falso. Passare questo controllo è condizione necessaria, mai prova
(CLAUDE.md §7: un controllo interno non conferma niente).

    python handoff.py file.txt        # exit 0 conforme, 1 rifiutato
    cat file.txt | python handoff.py
"""
import hashlib
import re
import sys

CAMPI = ("STATO", "SCOPERTA", "LIMITE", "PROSSIMA MOSSA", "EVIDENZA")
ERRORE = ("[ERRORE HANDOFF: Formato non conforme. Riformulare secondo "
          "STATO / SCOPERTA / LIMITE / PROSSIMA MOSSA / EVIDENZA]")

# Intestazione di campo: a inizio riga, eventuale markup markdown, nome, due punti.
_INTESTAZIONE = re.compile(
    r"^[ \t>#*_\-]*(" + "|".join(CAMPI) + r")[ \t*_]*:[ \t*_]*(.*)$",
    re.MULTILINE,
)
# Confine fra handoff e carico allegato (v1.2).
_ALLEGATO = re.compile(r"^[ \t>#*_\-]*ALLEGATO[ \t*_]*:[ \t*_]*$", re.MULTILINE)
_SHA256 = re.compile(r"sha256:([0-9a-f]{64})", re.IGNORECASE)

# Marcatori di intenzione futura: non appartengono a STATO.
_FUTURO = re.compile(
    r"\b(prossim[aoei]|propong[oa]|dovr[eòà]\w*|far[òe]\w*|"
    r"da fare|occorre|bisogna|intendo|vorrei|procederò)\b",
    re.IGNORECASE,
)
# Riferimenti apribili da un terzo.
_RIFERIMENTO = re.compile(
    r"(https?://\S+"
    r"|\b[\w./-]+\.(?:py|md|json|jsonl|txt|zip|yaml|yml|csv|log|sh|html)\b"
    r"|\b(?=[0-9a-f]*\d)(?=[0-9a-f]*[a-f])[0-9a-f]{7,64}\b)",
    re.IGNORECASE,
)


def analizza(testo):
    """Ritorna (campi, errori). `campi` mappa nome -> contenuto."""
    errori = []
    allegato = None
    confine = _ALLEGATO.search(testo)
    if confine:
        testo, allegato = testo[:confine.start()], testo[confine.end():].strip()
    trovate = list(_INTESTAZIONE.finditer(testo))
    nomi = [m.group(1) for m in trovate]

    for c in CAMPI:
        n = nomi.count(c)
        if n == 0:
            errori.append(f"manca il campo {c}")
        elif n > 1:
            errori.append(f"campo {c} ripetuto {n} volte")

    if trovate and testo[:trovate[0].start()].strip():
        errori.append("testo prima del primo campo")

    campi = {}
    for i, m in enumerate(trovate):
        fine = trovate[i + 1].start() if i + 1 < len(trovate) else len(testo)
        corpo = (m.group(2) + testo[m.end():fine]).strip()
        campi.setdefault(m.group(1), corpo)
        if not corpo:
            errori.append(f"campo {m.group(1)} vuoto")

    stato = campi.get("STATO", "")
    futuro = _FUTURO.search(stato)
    if futuro:
        errori.append(f"STATO contiene una mossa futura («{futuro.group(0)}»)")

    if "EVIDENZA" in campi and campi["EVIDENZA"] and not _RIFERIMENTO.search(campi["EVIDENZA"]):
        errori.append("EVIDENZA senza riferimento verificabile (file, hash o URL)")

    citati = _SHA256.findall(campi.get("EVIDENZA", ""))
    if allegato is not None and citati:
        reale = hashlib.sha256(allegato.encode("utf-8")).hexdigest()
        if reale not in (h.lower() for h in citati):
            errori.append(f"sha256 dell'ALLEGATO non corrisponde (reale: {reale[:12]}…)")

    return campi, errori


def conforme(testo):
    return not analizza(testo)[1]


def main(argv):
    testo = open(argv[1], encoding="utf-8").read() if len(argv) > 1 else sys.stdin.read()
    _, errori = analizza(testo)
    if errori:
        print(ERRORE)
        for e in errori:
            print(f"  - {e}")
        return 1
    print("HANDOFF CONFORME (forma). Il contenuto resta da verificare.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
