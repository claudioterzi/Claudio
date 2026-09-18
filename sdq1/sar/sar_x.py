"""SAR-X v1.0 — Scacchiera Auto-Riflessiva Evolutiva.

Sistema deterministico per autoriflessione, contraddizione, simulazione,
selezione e auto-superamento operativo.

Principi R³∞ / Protocollo Rosso Rosso Rosso:
- non confondere osservazione, inferenza, ipotesi e UNKNOWN;
- ogni ipotesi deve avere una condizione di falsificazione;
- il sistema non può auto-confermarsi come migliorato;
- un cambiamento viene consolidato solo se supera il confronto con lo stato precedente.

Nota: "superamento" qui significa miglioramento verificabile del processo
operativo, non coscienza, soggettività o modifica dei pesi del modello.

Origine: © Claudio Terzi — R³∞ — SAR-X v1.0 — 2026
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Callable, Iterable


class StatoEpistemico(str, Enum):
    RECUPERATO = "RECUPERATO"
    INFERITO = "INFERITO"
    IPOTESI = "IPOTESI"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Evidenza:
    fonte: str
    contenuto: str
    indipendente: bool = False


@dataclass
class Ipotesi:
    testo: str
    falsificazione: str
    stato: StatoEpistemico = StatoEpistemico.IPOTESI
    evidenze: list[Evidenza] = field(default_factory=list)

    def validabile(self) -> bool:
        return bool(self.falsificazione.strip())


@dataclass
class Candidato:
    nome: str
    strategia: str
    previsione: str
    test: str
    score: float = 0.0
    rischio: float = 0.0
    complessita: float = 0.0
    falsificato: bool = False
    note: str = ""

    @property
    def utilita(self) -> float:
        return self.score - self.rischio - (self.complessita * 0.25)


@dataclass
class StatoSAR:
    ciclo: int = 0
    strategia: str = "baseline"
    score: float = 0.0
    robustezza: float = 0.0
    predittivita: float = 0.0
    coerenza: float = 0.0
    falsificabilita: float = 0.0
    efficienza: float = 0.0
    errori: float = 0.0
    contraddizioni: float = 0.0
    complessita: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def indice(self) -> float:
        positivo = (
            self.robustezza
            + self.predittivita
            + self.coerenza
            + self.falsificabilita
            + self.efficienza
        ) / 5.0
        penalita = self.errori + self.contraddizioni + (self.complessita * 0.25)
        return round(positivo - penalita, 4)


@dataclass
class DeltaSelf:
    precedente: float
    successivo: float
    delta: float
    migliorato: bool
    motivazione: str


@dataclass
class RapportoSARX:
    ciclo: int
    osservazione: str
    tensione: str
    ipotesi: list[dict[str, Any]]
    avversari: list[dict[str, Any]]
    candidati: list[dict[str, Any]]
    stato_precedente: dict[str, Any]
    stato_successivo: dict[str, Any]
    delta_self: dict[str, Any]
    decisione: str
    livello_raggiunto: int
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ScacchieraAutoRiflessivaEvolutiva:
    """SAR-X: 12 livelli e loop evolutivo verificabile."""

    LIVELLI = {
        1: "OSSERVA",
        2: "SCOMPONE",
        3: "MODELLA",
        4: "CONFRONTA",
        5: "CONTRADDICE",
        6: "RIFLETTE",
        7: "GENERA",
        8: "SIMULA",
        9: "SELEZIONA",
        10: "CONSOLIDA",
        11: "REINVENTA",
        12: "SUPERAMENTO",
    }

    def __init__(self, soggetto: str = "sistema") -> None:
        self.soggetto = soggetto
        self.ciclo_corrente = 0
        self.stato = StatoSAR()
        self.storia: list[RapportoSARX] = []
        self.memoria_strategie: list[str] = ["baseline"]

    # ---------- livello 1-3: osservazione e modello ----------

    def osserva(self, testo: str) -> dict[str, Any]:
        testo = testo.strip()
        return {
            "livello": 1,
            "stato": StatoEpistemico.RECUPERATO.value,
            "osservazione": testo,
            "hash": hashlib.sha256(testo.encode("utf-8")).hexdigest(),
        }

    def scomponi(self, testo: str) -> list[str]:
        parti = [p.strip() for p in testo.replace(";", ".").split(".") if p.strip()]
        return parti or [testo.strip()]

    def modella(self, osservazione: str, tensione: str) -> dict[str, Any]:
        return {
            "livello": 3,
            "osservazione": osservazione,
            "tensione": tensione,
            "poli": [p.strip() for p in tensione.split("↔")],
            "vincolo": "nessuna conclusione senza test o evidenza",
        }

    # ---------- livello 4-6: confronto, contraddizione, meta-riflessione ----------

    def genera_ipotesi(self, osservazione: str, tensione: str) -> list[Ipotesi]:
        return [
            Ipotesi(
                testo=f"La tensione {tensione} sta influenzando l'interpretazione di: {osservazione}",
                falsificazione="Un'evidenza indipendente deve mostrare che la tensione non spiega il fenomeno.",
            ),
            Ipotesi(
                testo=f"L'osservazione può essere spiegata senza usare la tensione {tensione}.",
                falsificazione="Un test deve mostrare che rimuovere la tensione peggiora la spiegazione.",
            ),
        ]

    def contraddici(self, ipotesi: Iterable[Ipotesi]) -> list[dict[str, Any]]:
        avversari = []
        for h in ipotesi:
            avversari.append({
                "ipotesi": h.testo,
                "attacco": h.falsificazione,
                "esito": "DA_TESTARE",
            })
        return avversari

    def meta_riflessione(self, rapporto_parziale: dict[str, Any]) -> str:
        problemi = []
        if not rapporto_parziale.get("avversari"):
            problemi.append("manca forza contraria")
        if not rapporto_parziale.get("ipotesi"):
            problemi.append("manca esplicitazione delle ipotesi")
        if problemi:
            return "META: " + "; ".join(problemi) + "."
        return (
            "META: il sistema deve verificare se sta aumentando la lucidità "
            "o soltanto la complessità narrativa."
        )

    # ---------- livello 7-10: generazione, simulazione, selezione ----------

    def genera_candidati(self, osservazione: str, tensione: str) -> list[Candidato]:
        return [
            Candidato(
                "conservativa",
                "mantenere la strategia corrente e raccogliere un dato nuovo",
                "un dato aggiuntivo riduce l'incertezza",
                "misurare prima/dopo",
                score=6.0, rischio=1.0, complessita=1.0,
            ),
            Candidato(
                "inversa",
                "invertire temporaneamente il polo dominante della tensione",
                "l'inversione rivela un'assunzione nascosta",
                "confrontare con baseline",
                score=7.0, rischio=2.0, complessita=2.0,
            ),
            Candidato(
                "radicale",
                "rimuovere un'assunzione e ricostruire il modello",
                "meno assunzioni produce una spiegazione più robusta",
                "test di ablation",
                score=8.0, rischio=3.0, complessita=3.0,
            ),
        ]

    def simula(self, candidato: Candidato, contesto: dict[str, Any]) -> Candidato:
        # Simulazione esplicita e riproducibile: nessuna pretesa di verità.
        c = Candidato(**asdict(candidato))
        if "ablation" in c.test.lower():
            c.note = "SIMULAZIONE: verificare quali assunzioni possono essere rimosse senza perdita."
        else:
            c.note = "SIMULAZIONE: risultato provvisorio; richiede verifica nel reale."
        return c

    def seleziona(self, candidati: list[Candidato]) -> Candidato:
        validi = [c for c in candidati if not c.falsificato]
        if not validi:
            raise ValueError("Nessun candidato sopravvive alla falsificazione.")
        return max(validi, key=lambda c: c.utilita)

    # ---------- livello 11-12: reinvenzione e superamento ----------

    def misura_stato(self, candidato: Candidato, errori: float = 0.0,
                     contraddizioni: float = 0.0) -> StatoSAR:
        base = candidato.utilita
        return StatoSAR(
            ciclo=self.ciclo_corrente,
            strategia=candidato.nome,
            score=round(base, 4),
            robustezza=round(max(0.0, min(10.0, 5.0 + base * 0.5)), 4),
            predittivita=round(max(0.0, min(10.0, 5.0 + base * 0.35)), 4),
            coerenza=round(max(0.0, min(10.0, 7.0 - contraddizioni)), 4),
            falsificabilita=8.0 if candidato.test else 0.0,
            efficienza=round(max(0.0, 8.0 - candidato.complessita), 4),
            errori=errori,
            contraddizioni=contraddizioni,
            complessita=candidato.complessita,
        )

    def calcola_delta(self, prima: StatoSAR, dopo: StatoSAR) -> DeltaSelf:
        a, b = prima.indice(), dopo.indice()
        delta = round(b - a, 4)
        return DeltaSelf(
            precedente=a,
            successivo=b,
            delta=delta,
            migliorato=delta > 0,
            motivazione=(
                "nuovo stato superiore secondo le metriche dichiarate"
                if delta > 0 else
                "nessun superamento verificabile: mantenere lo stato precedente"
            ),
        )

    def reinventa(self, selezionato: Candidato, delta: DeltaSelf) -> str:
        if not delta.migliorato:
            return self.stato.strategia
        return f"{selezionato.nome}: {selezionato.strategia}"

    # ---------- ciclo completo ----------

    def ciclo(self, osservazione: str, tensione: str = "certezza ↔ dubbio") -> RapportoSARX:
        self.ciclo_corrente += 1
        obs = self.osserva(osservazione)
        parti = self.scomponi(osservazione)
        modello = self.modella(" | ".join(parti), tensione)
        ipotesi = self.genera_ipotesi(osservazione, tensione)
        avversari = self.contraddici(ipotesi)
        candidati = self.genera_candidati(osservazione, tensione)
        simulati = [self.simula(c, modello) for c in candidati]
        selezionato = self.seleziona(simulati)

        precedente = self.stato
        successivo = self.misura_stato(selezionato)
        delta = self.calcola_delta(precedente, successivo)
        nuova_strategia = self.reinventa(selezionato, delta)

        if delta.migliorato:
            self.stato = successivo
            self.memoria_strategie.append(nuova_strategia)
            decisione = "SUPERAMENTO_CONSOLIDATO"
            livello = 12
        else:
            decisione = "SUPERAMENTO_RIFIUTATO"
            livello = 10

        parziale = {
            "ipotesi": [asdict(h) for h in ipotesi],
            "avversari": avversari,
        }
        _ = self.meta_riflessione(parziale)

        rapporto = RapportoSARX(
            ciclo=self.ciclo_corrente,
            osservazione=osservazione,
            tensione=tensione,
            ipotesi=parziale["ipotesi"],
            avversari=avversari,
            candidati=[asdict(c) for c in simulati],
            stato_precedente=asdict(precedente),
            stato_successivo=asdict(self.stato),
            delta_self=asdict(delta),
            decisione=decisione,
            livello_raggiunto=livello,
        )
        self.storia.append(rapporto)
        return rapporto

    def esporta(self) -> dict[str, Any]:
        return {
            "versione": "SAR-X 1.0",
            "soggetto": self.soggetto,
            "livelli": self.LIVELLI,
            "ciclo_corrente": self.ciclo_corrente,
            "stato": asdict(self.stato),
            "indice_stato": self.stato.indice(),
            "strategie_consolidate": self.memoria_strategie,
            "storia": [r.to_dict() for r in self.storia],
        }

    def json(self) -> str:
        return json.dumps(self.esporta(), ensure_ascii=False, indent=2, default=str)


# Alias breve per integrazione nel progetto.
SARX = ScacchieraAutoRiflessivaEvolutiva


if __name__ == "__main__":
    sar = SARX(soggetto="R³∞")
    report = sar.ciclo(
        "Il sistema ha prodotto una conclusione ma non ha ancora una prova indipendente.",
        "certezza ↔ dubbio",
    )
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, default=str))
