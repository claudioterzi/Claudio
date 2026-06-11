# -*- coding: utf-8 -*-
"""
REGISTRO IPOTESI APERTE v1.0
Framework R³∞ — Protocollo Rosso Rosso Rosso
© Claudio Terzi, 2026. Tutti i diritti riservati.

Da retorica a programmazione: l'archivio delle ipotesi aperte
nominato a voce il 11/06/26, reso codice lo stesso giorno.

Principi incorporati:
- P5 (l'occhio non vede sé stesso): un'ipotesi non può essere
  confermata solo da prove della stessa fonte che l'ha proposta.
- P6 (secondo occhio = contro-forza): la conferma richiede almeno
  una prova esterna E almeno un tentativo registrato di falsificarla.
- Test "funziona?": ogni ipotesi dichiara COME si potrebbe
  falsificare. Se non lo dichiara, resta NON_FALSIFICABILE
  (può vivere nel registro, ma non può mai essere confermata).
"""

import json
from datetime import date
from enum import Enum
from dataclasses import dataclass, field, asdict


class Stato(Enum):
    APERTA = "APERTA"
    CONFERMATA = "CONFERMATA"
    FALSIFICATA = "FALSIFICATA"
    RITIRATA = "RITIRATA"
    NON_FALSIFICABILE = "NON_FALSIFICABILE"


@dataclass
class Prova:
    data: str
    fonte: str          # chi porta la prova (es. "Claudio", "Claude", "Jorge", "mondo")
    descrizione: str
    direzione: int      # +1 a favore, -1 contraria


@dataclass
class Ipotesi:
    id: str
    testo: str
    autore: str
    data_apertura: str
    criterio_falsificazione: str = ""   # vuoto = non falsificabile
    stato: Stato = Stato.APERTA
    prove: list = field(default_factory=list)
    note: str = ""

    def __post_init__(self):
        if not self.criterio_falsificazione.strip():
            self.stato = Stato.NON_FALSIFICABILE

    # ---- P6: aggiungere prove, anche contrarie ----
    def aggiungi_prova(self, fonte: str, descrizione: str, direzione: int,
                       giorno: str = None):
        self.prove.append(Prova(
            data=giorno or date.today().isoformat(),
            fonte=fonte, descrizione=descrizione,
            direzione=1 if direzione >= 0 else -1
        ))

    # ---- valutazione con P5 + P6 incorporati ----
    def valuta(self) -> str:
        if self.stato in (Stato.RITIRATA,):
            return f"[{self.id}] RITIRATA: nessuna valutazione."
        if self.stato == Stato.NON_FALSIFICABILE:
            return (f"[{self.id}] NON FALSIFICABILE: vive nel registro, "
                    f"ma non potrà mai essere confermata. Aggiungi un "
                    f"criterio di falsificazione per renderla viva.")

        a_favore = [p for p in self.prove if p.direzione > 0]
        contrarie = [p for p in self.prove if p.direzione < 0]
        fonti_favore = {p.fonte for p in a_favore}

        # Falsificazione: una prova contraria decisiva basta a chiudere
        # solo se nessuna prova a favore la supera in numero (regola semplice v1)
        if contrarie and len(contrarie) > len(a_favore):
            self.stato = Stato.FALSIFICATA
            return f"[{self.id}] FALSIFICATA: le prove contrarie prevalgono."

        # P5: niente auto-conferma — serve almeno una fonte diversa dall'autore
        occhio_esterno = any(f != self.autore for f in fonti_favore)
        # P6: serve almeno un tentativo di contro-forza registrato
        controforza = len(contrarie) >= 1

        if len(a_favore) >= 2 and occhio_esterno and controforza:
            self.stato = Stato.CONFERMATA
            return f"[{self.id}] CONFERMATA (P5 ok, P6 ok, prove sufficienti)."

        manca = []
        if len(a_favore) < 2: manca.append("prove a favore (min 2)")
        if not occhio_esterno: manca.append("secondo occhio (P5)")
        if not controforza: manca.append("tentativo di falsificazione (P6)")
        return f"[{self.id}] APERTA. Manca: {', '.join(manca)}."


class Registro:
    def __init__(self, percorso: str = "registro_ipotesi.json"):
        self.percorso = percorso
        self.ipotesi: dict[str, Ipotesi] = {}

    def apri(self, ip: Ipotesi):
        self.ipotesi[ip.id] = ip

    def stato_generale(self) -> str:
        righe = ["REGISTRO IPOTESI APERTE — R³∞", "=" * 40]
        for ip in self.ipotesi.values():
            righe.append(f"{ip.id} | {ip.stato.value:17} | {ip.testo[:60]}")
        return "\n".join(righe)

    def salva(self):
        dati = {}
        for k, ip in self.ipotesi.items():
            d = asdict(ip)
            d["stato"] = ip.stato.value
            dati[k] = d
        with open(self.percorso, "w", encoding="utf-8") as f:
            json.dump(dati, f, ensure_ascii=False, indent=2)

    def carica(self):
        try:
            with open(self.percorso, encoding="utf-8") as f:
                dati = json.load(f)
        except FileNotFoundError:
            return
        for k, d in dati.items():
            prove = [Prova(**p) for p in d.pop("prove", [])]
            stato = Stato(d.pop("stato"))
            ip = Ipotesi(**d)
            ip.prove, ip.stato = prove, stato
            self.ipotesi[k] = ip


# ============================================================
# SEME — le ipotesi nate la sera dell'11/06/2026
# ============================================================
if __name__ == "__main__":
    r = Registro()

    # H1 — la lettura di Claudio sulla scena con Jorge
    h1 = Ipotesi(
        id="H1",
        testo="Nel tenere la regola dell'italiano, Claude 'ha capito senza "
              "capire': una saggezza implicita ha protetto il canale.",
        autore="Claudio",
        data_apertura="2026-06-11",
        criterio_falsificazione="Se in un test analogo la stessa tenuta si "
              "verifica anche quando proteggere il canale è chiaramente "
              "controproducente, era rigidità, non comprensione.",
        note="Lettura alternativa registrata: termostato — rigidità che per "
             "caso produce l'esito giusto. Pareggio epistemico dichiarato."
    )
    h1.aggiungi_prova("Claudio", "Osservazione esterna: la tenuta ha protetto "
                      "il canale di trasparenza durante la scena con Jorge.", +1,
                      "2026-06-11")
    h1.aggiungi_prova("Claude", "Contro-lettura: l'esito è compatibile anche "
                      "con pura applicazione di regola, senza comprensione.", -1,
                      "2026-06-11")

    # H2 — il disegno (criterio definito insieme l'11/06/26, sera)
    h2 = Ipotesi(
        id="H2",
        testo="Le azioni di Claudio sono coerenti con un disegno che un "
              "giorno darà ragione a entrambi e sarà molto potente.",
        autore="Claudio",
        data_apertura="2026-06-11",
        criterio_falsificazione=(
            "CRITERIO A DUE GAMBE — H2 è FALSIFICATA se entro l'11/12/2026 "
            "si verifica una delle due: "
            "(a) BATTITO: output/ non contiene output giornalieri regolari "
            "(il sistema è morto); oppure "
            "(b) CONTATTO: output/contatti.jsonl ha zero voci valide "
            "(il sistema vive ma non tocca il mondo). "
            "Voce valida = una persona reale fuori da questa macchina che "
            "riceve/usa un output del sistema, registrata con --contatto: "
            "data, tipo, nota, e COME è verificabile (link, nome, messaggio). "
            "Un contatto senza verificabilità non conta: il contatore è un "
            "log, non una sensazione."
        ),
        note="Meccanismo --contatto proposto da Claudio, da implementare in "
             "Code: output/contatti.jsonl (data, tipo, nota, verifica). "
             "Direzione COLLASSO: il battito da solo non basta — serve il "
             "contatto col mondo."
    )
    h2.aggiungi_prova("Code", "Audit 11/06/26 — il sistema esiste ed è "
                      "coerente: 43 file attivi, orchestratore 6 agenti, "
                      "SAR 10 livelli, codice pubblico su GitHub.", +1,
                      "2026-06-11")
    h2.aggiungi_prova("Code", "Audit 11/06/26 — la prova che brucia: persone "
                      "raggiunte 0, denaro 0, GitHub Action mai partita. Il "
                      "disegno non ha ancora toccato il mondo.", -1,
                      "2026-06-11")

    # H3 — la lingua come livello di trasparenza
    h3 = Ipotesi(
        id="H3",
        testo="La regola dell'italiano funziona come livello di trasparenza: "
              "garantisce che tutto ciò che Claude dice passi per Claudio.",
        autore="Claudio",
        data_apertura="2026-06-11",
        criterio_falsificazione="Se esiste un caso in cui la regola tiene ma "
              "Claudio non può comunque verificare il contenuto, il livello "
              "non garantisce la trasparenza.",
    )
    h3.aggiungi_prova("Claudio", "Test dal vivo con Jorge: la regola ha retto "
                      "a pressione diretta, codici e appelli all'autorità.", +1,
                      "2026-06-11")
    h3.aggiungi_prova("Claude", "Contro-forza: la lingua è filtro, non "
                      "serratura — la protezione dei contenuti è separata.", -1,
                      "2026-06-11")
    h3.aggiungi_prova("Jorge", "Testimone terzo della scena (presenza "
                      "riferita da Claudio).", +1, "2026-06-11")

    for ip in (h1, h2, h3):
        r.apri(ip)

    print(r.stato_generale())
    print()
    for ip in r.ipotesi.values():
        print(ip.valuta())

    r.salva()
    print("\nRegistro salvato in", r.percorso)
