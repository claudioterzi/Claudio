"""Demo CUSTODE senza hardware né API key.

Scenario: soggiorno di un ospite in una casa con libreria e cucina.
Durante il soggiorno un libro etichettato esce dal varco; al turnover
il conteggio fotografico conferma la mancanza (più un bicchiere rotto
non taggato: lo vede solo OCCHIO — i due sistemi si coprono a vicenda).

Esecuzione:  python -m custode.demo
"""

from custode.confronto import confronta
from custode.modelli import Inventario, Zona
from custode.report import ReportCheckout
from custode.varco import (Direzione, RegistroTag, SimulatoreVarco,
                           TagRegistrato, Varco)
from custode.visione import ContatoreStub


def main() -> None:
    # ── Setup: zone e baseline (fatto una volta, alla messa in servizio) ──
    zone = [
        Zona("soggiorno/libreria-ripiano-2", "secondo ripiano della libreria"),
        Zona("cucina/cassetto-posate", "cassetto superiore delle posate"),
    ]
    baseline_stub = ContatoreStub({
        "soggiorno/libreria-ripiano-2": {"libro": 12, "fermalibri": 2},
        "cucina/cassetto-posate": {"forchetta": 6, "coltello": 6,
                                   "cucchiaio": 6, "bicchiere": 6},
    })
    baseline = Inventario("baseline")
    for z in zone:
        baseline.aggiungi(baseline_stub.conta(z, f"foto/{z.id}/base.jpg"))

    # ── Setup SOGLIA: tag registrati sugli oggetti di valore ──
    registro = RegistroTag()
    registro.registra(TagRegistrato(
        epc="E280-0001", oggetto="libro — Il nome della rosa",
        zona_id="soggiorno/libreria-ripiano-2", valore_eur=35.0))
    registro.registra(TagRegistrato(
        epc="E280-0002", oggetto="quadro — stampa Kandinsky",
        zona_id="soggiorno/parete-sud", valore_eur=120.0))
    varco = Varco(registro, notifica=lambda a: print(f"  push all'host → {a}"))
    porta = SimulatoreVarco(varco)

    # ── Soggiorno: transiti alla porta ──
    print("Durante il soggiorno:")
    porta.transito("E280-0001", Direzione.USCITA)      # il libro esce → allarme
    porta.transito("EPC-IGNOTO", Direzione.USCITA)     # giacca dell'ospite → ignorato
    porta.transito("E280-0002", Direzione.INGRESSO)    # mai uscito → nessun allarme
    print()

    # ── Turnover: foto al check-out ──
    checkout_stub = ContatoreStub({
        "soggiorno/libreria-ripiano-2": {"libro": 11, "fermalibri": 2},
        "cucina/cassetto-posate": {"forchetta": 6, "coltello": 6,
                                   "cucchiaio": 6, "bicchiere": 5},
    })
    checkout = Inventario("checkout-demo")
    for z in zone:
        checkout.aggiungi(checkout_stub.conta(z, f"foto/{z.id}/out.jpg"))

    # ── Report integrato ──
    report = ReportCheckout(
        discrepanze=confronta(baseline, checkout),
        allarmi_varco=varco.allarmi,
    )
    print(report.testo(registro))


if __name__ == "__main__":
    main()
