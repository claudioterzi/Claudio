"""ANONIMA-008 — Il gate del consenso, eseguibile.

Carica anonima_catalogo.json e verifica che nessun pezzo violi le regole del
cancello. Esce con codice != 0 se qualcosa e' fuori posto. Il confine morale
non e' un commento: e' un test che deve passare prima di ogni esposizione.

    python3 anonima_gate.py            # verifica tutto il catalogo
    python3 anonima_gate.py --pubblicabili   # elenca solo i pezzi esponibili
"""
import json, sys, os

CATALOGO = os.path.join(os.path.dirname(__file__), "anonima_catalogo.json")


def carica():
    with open(CATALOGO, encoding="utf-8") as f:
        return json.load(f)


def viola(pezzo: dict, enum: dict) -> list[str]:
    """Ritorna la lista delle violazioni del gate per un pezzo. Vuota = ok."""
    err = []
    cons = pezzo.get("stato_consenso")
    esp = pezzo.get("livello_esposizione")
    anon = pezzo.get("anonimizzazione")
    ident = pezzo.get("elementi_identificanti_rilevati", [])

    # enum validi
    for campo, valori in enum.items():
        if campo in pezzo and pezzo[campo] not in valori:
            err.append(f"{campo}='{pezzo[campo]}' non e' tra {valori}")

    # Regola 1: pubblicabile richiede consenso verificato E anonimizzazione completata
    if esp == "pubblicabile":
        if cons != "verificato":
            err.append("pubblicabile ma stato_consenso != 'verificato'")
        if anon != "completata":
            err.append("pubblicabile ma anonimizzazione != 'completata'")

    # Regola 2: elementi identificanti aperti => non oltre 'solo-archivio' finche' non trattati
    if ident and anon != "completata" and esp != "solo-archivio":
        err.append(f"elementi identificanti non trattati ({ident}) ma esposizione='{esp}'")

    # Regola 3: consenso assente/insufficiente => massimo 'dettaglio-astratto'
    if cons in ("assente", "presunto-insufficiente") and esp == "pubblicabile":
        err.append(f"stato_consenso='{cons}' non consente 'pubblicabile'")

    return err


def main():
    cat = carica()
    enum = cat.get("enum", {})
    pezzi = cat.get("pezzi", [])

    if "--pubblicabili" in sys.argv:
        pub = [p["id"] for p in pezzi if p.get("livello_esposizione") == "pubblicabile"]
        print("Pezzi pubblicabili:", pub or "nessuno (gate chiuso)")
        return 0

    problemi = 0
    for p in pezzi:
        errori = viola(p, enum)
        if errori:
            problemi += 1
            print(f"✗ pezzo {p.get('id')}:")
            for e in errori:
                print(f"    - {e}")
    if problemi:
        print(f"\nGATE FALLITO: {problemi} pezzo/i violano le regole.")
        return 1
    print(f"✓ Gate ok: {len(pezzi)} pezzi conformi. "
          f"Pubblicabili: {sum(1 for p in pezzi if p.get('livello_esposizione') == 'pubblicabile')}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
