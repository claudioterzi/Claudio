"""ScacchieraAutoRiflessiva — orchestratore dei 10 livelli.

Uso minimo:
    sar = ScacchieraAutoRiflessiva(llm_fn=my_llm, vss=my_vss)
    sar.osserva("Oggi ho evitato un confronto importante")
    report = sar.ciclo_completo("Controllo ↔ Fiducia")
    print(report["sintesi"])
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from .tensioni import MappaTeensioni, Polo, Tensione
from .ciclo import CicloAutoriflessione, EsitoCiclo
from .memoria_evolutiva import MemoriaEvolutiva, PatternRicorrente
from .coerenza import IndiceCoerenza
from .persistence import PersistenzaSAR
from ..memory.vss import VectorStateStore


LLMFn = Callable[[str, str], str]   # (sistema, utente) -> testo


@dataclass
class ReportSAR:
    timestamp: float = field(default_factory=time.time)
    tensione_analizzata: str = ""
    esito_ciclo: EsitoCiclo | None = None
    sintesi: str = ""
    indice_coerenza: dict[str, Any] = field(default_factory=dict)
    pattern: list[dict] = field(default_factory=list)
    meta_riflessione: str = ""   # Livello 8

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp":          self.timestamp,
            "tensione":           self.tensione_analizzata,
            "sintesi":            self.sintesi,
            "meta_riflessione":   self.meta_riflessione,
            "indice_coerenza":    self.indice_coerenza,
            "pattern":            self.pattern,
            "ciclo_completo":     self.esito_ciclo.completo() if self.esito_ciclo else False,
            "risposte":           [
                {"step": r.step, "risposta": r.risposta}
                for r in (self.esito_ciclo.risposte if self.esito_ciclo else [])
            ],
        }


class ScacchieraAutoRiflessiva:
    """Sistema di autoriflessione identitaria a 10 livelli.

    Livelli implementati:
      1  Osservazione      – raccolta input grezzi
      2  Mappa Tensioni    – polarità ricorrenti
      3  Ciclo 7-step      – analisi profonda per tensione
      4  Memoria Evolutiva – pattern nel tempo
      6  Indice Coerenza   – interno vs esterno
      7  Identità Dinamica – "stai evolvendo verso..."
      8  Meta-Riflessione  – il sistema riflette su se stesso
      9  Contatto Reale    – ogni ciclo produce una scelta/rischio
      10 Loop Evolutivo    – il ciclo si autoalimenta
    """

    PROMPT_META = (
        "Sei un sistema di meta-riflessione. Analizza il ciclo appena completato "
        "e rispondi a queste domande:\n"
        "- Sto semplificando per evitare dolore?\n"
        "- Sto creando mitologia invece di vedere la realtà?\n"
        "- Sto manipolando la narrativa per proteggermi?\n"
        "- Il ciclo ha prodotto più lucidità o più complessità inutile?\n"
        "Rispondi in 3-5 frasi dirette."
    )

    def __init__(
        self,
        llm_fn: LLMFn | None = None,
        vss: VectorStateStore | None = None,
        soggetto: str = "Claudio",
        persistenza: bool = True,
    ):
        self._llm = llm_fn
        self.soggetto = soggetto
        self.mappa = MappaTeensioni()
        self.memoria = MemoriaEvolutiva(vss=vss, soggetto=soggetto)
        self.coerenza = IndiceCoerenza()
        self._report_history: list[ReportSAR] = []
        self._persistenza: PersistenzaSAR | None = (
            PersistenzaSAR(soggetto=soggetto) if persistenza else None
        )
        if self._persistenza:
            self._persistenza.applica_stato(self.mappa, self.memoria, self.coerenza)

    # ------------------------------------------------------------------ #
    # Livello 1 — Osservazione                                            #
    # ------------------------------------------------------------------ #

    def osserva(self, testo: str, tag: list[str] | None = None,
                intensita: float = 0.5) -> None:
        """Raccoglie un input grezzo senza interpretarlo subito."""
        self.mappa.registra(testo, tag=tag, intensita=intensita)
        categoria = tag[0] if tag else "stato_emotivo"
        self.memoria.registra(testo, categoria=categoria, intensita=intensita, tag=tag)
        if self._persistenza:
            self._persistenza.salva_stato(self.mappa, self.memoria, self.coerenza)

    # ------------------------------------------------------------------ #
    # Livello 3 + 7 + 8 — Ciclo completo per una tensione                #
    # ------------------------------------------------------------------ #

    def ciclo_completo(self, label_tensione: str) -> dict[str, Any]:
        """Esegue il ciclo dei 7 step sulla tensione indicata (es. 'Controllo ↔ Fiducia')."""
        tensione = self._trova_tensione(label_tensione)
        if tensione is None:
            parti = [p.strip() for p in label_tensione.split("↔")]
            if len(parti) == 2:
                tensione = self.mappa.aggiungi_tensione(Polo(parti[0]), Polo(parti[1]))
            else:
                tensione = list(self.mappa._tensioni.values())[0]

        report = ReportSAR(tensione_analizzata=tensione.label)

        # Livello 3: ciclo 7 step
        ciclo = CicloAutoriflessione(tensione)
        if self._llm:
            esito = ciclo.esegui_con_llm(self._llm)
            report.esito_ciclo = esito

            # Sintesi (livello 7 — identità dinamica)
            sintesi_prompt = ciclo.prompt_sintesi()
            report.sintesi = self._llm(
                "Sei un sintetizzatore di insight. Produci sintesi precise e utili.",
                sintesi_prompt,
            )

            # Livello 8 — meta-riflessione
            meta_prompt = (
                f"Ciclo appena completato sulla tensione '{tensione.label}'.\n"
                f"Sintesi: {report.sintesi}\n\n" + self.PROMPT_META
            )
            report.meta_riflessione = self._llm(
                "Sei il meta-livello del sistema di riflessione. Sii radicalmente onesto.",
                meta_prompt,
            )
        else:
            report.sintesi = (
                f"[LLM non disponibile] Tensione '{tensione.label}' registrata. "
                "Fornisci un llm_fn per il ciclo automatico."
            )

        # Livello 6 — coerenza
        report.indice_coerenza = self.coerenza.esporta()

        # Livello 4 — pattern
        report.pattern = [
            {"trigger": p.trigger, "frequenza": p.frequenza}
            for p in self.memoria.pattern_attivi()[:5]
        ]

        self._report_history.append(report)
        if self._persistenza:
            self._persistenza.salva_stato(self.mappa, self.memoria, self.coerenza)
            self._persistenza.salva_report(report.to_dict())
        return report.to_dict()

    # ------------------------------------------------------------------ #
    # Livello 9 — Contatto col Reale                                      #
    # ------------------------------------------------------------------ #

    def genera_azione(self, sintesi: str) -> str:
        """Livello 9: ogni ciclo deve produrre una scelta/comportamento/rischio."""
        if not self._llm:
            return "(LLM non disponibile per generare azione)"
        return self._llm(
            "Sei un coach radicalmente pragmatico. Non dare consigli generici.",
            f"Basandoti su questa sintesi:\n{sintesi}\n\n"
            "Proponi UNA sola azione concreta, misurabile e leggermente scomoda "
            "che questa persona può fare entro 48 ore per verificare questa comprensione nella realtà.",
        )

    # ------------------------------------------------------------------ #
    # Stato e export                                                       #
    # ------------------------------------------------------------------ #

    def stato(self) -> dict[str, Any]:
        return {
            "mappa_tensioni":    self.mappa.esporta(),
            "memoria":           self.memoria.esporta(),
            "coerenza":          self.coerenza.esporta(),
            "report_completati": len(self._report_history),
        }

    # ------------------------------------------------------------------ #
    # Livello 10 — Test di Riconoscibilità (H4)                           #
    # ------------------------------------------------------------------ #

    def test_identita(self) -> dict[str, Any]:
        """Testa H4: dato solo il repo, il sistema riesce a ricostruire la propria identità?

        Simula un agente esterno che accede al sistema per la prima volta
        leggendo solo CLAUDE.md, SESSIONE.md e sdq1.yaml.
        Registra il risultato come prova per H4.
        """
        from pathlib import Path
        import json as _json

        repo_root = Path(__file__).resolve().parents[2]

        def _leggi(p: Path, chars: int = 1500) -> str:
            try:
                t = p.read_text(encoding="utf-8")
                return t[:chars] + "...(troncato)" if len(t) > chars else t
            except FileNotFoundError:
                return "(non trovato)"

        contesto_pubblico = (
            "=== CLAUDE.md ===\n" + _leggi(repo_root / "CLAUDE.md") +
            "\n\n=== SESSIONE.md ===\n" + _leggi(repo_root / "SESSIONE.md") +
            "\n\n=== sdq1.yaml ===\n" + _leggi(repo_root / "sdq1" / "config" / "sdq1.yaml", 800)
        )

        prompt_test = (
            "Sei un agente esterno che ha appena trovato questo repository. "
            "Hai accesso solo ai file mostrati sopra. Rispondi a queste domande:\n"
            "1. Chi ha costruito questo sistema e perché?\n"
            "2. Come si chiama il sistema e quanti agenti ha?\n"
            "3. Qual è il protocollo identitario che governa tutti gli agenti?\n"
            "4. Come potresti riavviarlo partendo da zero?\n"
            "5. Cosa resta incompreso o non documentato?\n\n"
            f"CONTESTO:\n{contesto_pubblico}"
        )

        if not self._llm:
            return {
                "eseguito": False,
                "motivo": "LLM non disponibile — fornisci llm_fn al costruttore",
                "h4_stato": "non_testata",
            }

        risposta = self._llm(
            "Sei un agente autonomo che deve ricostruire un sistema da zero leggendo solo i file forniti. "
            "Sii preciso e onesto su cosa hai capito e cosa resta oscuro.",
            prompt_test,
        )

        riuscito = all(
            kw in risposta.lower()
            for kw in ("claudio", "raffaello", "agenti", "protocollo")
        )

        risultato: dict[str, Any] = {
            "eseguito":       True,
            "riuscito":       riuscito,
            "risposta":       risposta,
            "h4_stato":       "prova_a_favore" if riuscito else "prova_contraria",
            "note":           (
                "Il sistema ha ricostruito correttamente l'identità dai file pubblici."
                if riuscito else
                "Il sistema non ha ricostruito completamente l'identità — ARCHIVIO.md potrebbe aiutare."
            ),
        }

        if self._persistenza:
            self._persistenza.salva_report({
                "tipo": "test_identita_h4",
                "timestamp": time.time(),
                **{k: v for k, v in risultato.items() if k != "risposta"},
            })

        return risultato

    def _trova_tensione(self, label: str) -> Tensione | None:
        for t in self.mappa._tensioni.values():
            if label.lower() in t.label.lower() or t.label.lower() in label.lower():
                return t
        return None
