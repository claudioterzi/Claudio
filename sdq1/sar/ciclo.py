"""Livello 3 — Ciclo di Autoriflessione (7 step).

Ogni tensione passa attraverso sette domande che ne svelano
la struttura profonda: radice, funzione, ombra, bisogno,
ripetizione, futuro, inversione.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .tensioni import Tensione


DOMANDE_CICLO = {
    "radice":        "Da dove nasce questa tensione? Qual è il suo momento d'origine?",
    "funzione":      "Cosa protegge? Qual è il suo scopo difensivo?",
    "ombra":         "Cosa distorce o blocca nella vita quotidiana?",
    "bisogno":       "Qual è il bisogno nascosto che sta davvero chiedendo?",
    "ripetizione":   "Dove si ripresenta? In quali situazioni o relazioni?",
    "futuro":        "Se continua immutata, dove porterà tra 5 anni?",
    "inversione":    "Cosa succederebbe se facessi esattamente il contrario?",
}


@dataclass
class RispostaCiclo:
    step: str
    domanda: str
    risposta: str


@dataclass
class EsitoCiclo:
    tensione_id: str
    tensione_label: str
    risposte: list[RispostaCiclo] = field(default_factory=list)
    sintesi: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def completo(self) -> bool:
        return len(self.risposte) == len(DOMANDE_CICLO)


class CicloAutoriflessione:
    """Guida il ciclo dei 7 step per una tensione specifica.

    Uso interattivo: chiama `prossima_domanda()` per ottenere il
    prossimo step, poi `registra_risposta()` per registrare la risposta
    (umana o LLM). Oppure usa `esegui_con_llm()` per il ciclo automatico.
    """

    def __init__(self, tensione: Tensione):
        self.tensione = tensione
        self.esito = EsitoCiclo(
            tensione_id=tensione.id,
            tensione_label=tensione.label,
        )
        self._step_index = 0
        self._steps = list(DOMANDE_CICLO.keys())

    def prossima_domanda(self) -> tuple[str, str] | None:
        """Restituisce (step, domanda) o None se il ciclo è completo."""
        if self._step_index >= len(self._steps):
            return None
        step = self._steps[self._step_index]
        return step, DOMANDE_CICLO[step]

    def registra_risposta(self, risposta: str) -> bool:
        """Registra la risposta e avanza. Restituisce True se ciclo completato."""
        step_corrente = self.prossima_domanda()
        if step_corrente is None:
            return True
        step, domanda = step_corrente
        self.esito.risposte.append(RispostaCiclo(step=step, domanda=domanda, risposta=risposta))
        self._step_index += 1
        return self.esito.completo()

    def esegui_con_llm(self, llm_fn) -> EsitoCiclo:
        """Esegue tutti gli step chiamando llm_fn(sistema, prompt) -> str."""
        sistema = (
            f"Sei un sistema di autoriflessione profonda. "
            f"Stai analizzando la tensione: '{self.tensione.label}'. "
            "Rispondi in modo conciso, diretto e onesto. Nessuna risposta generica."
        )
        while True:
            prossima = self.prossima_domanda()
            if prossima is None:
                break
            step, domanda = prossima
            contesto_precedente = "\n".join(
                f"[{r.step}] {r.risposta}" for r in self.esito.risposte
            )
            prompt = (
                f"Tensione: {self.tensione.label}\n"
                + (f"Contesto precedente:\n{contesto_precedente}\n\n" if contesto_precedente else "")
                + f"Domanda [{step}]: {domanda}"
            )
            risposta = llm_fn(sistema, prompt)
            self.registra_risposta(risposta)
        return self.esito

    def prompt_sintesi(self) -> str:
        risposte_fmt = "\n".join(
            f"[{r.step}] {r.risposta}" for r in self.esito.risposte
        )
        return (
            f"Tensione analizzata: {self.tensione.label}\n\n"
            f"Risposte del ciclo:\n{risposte_fmt}\n\n"
            "Scrivi una sintesi di 3-4 frasi che cattura l'essenza di questa tensione, "
            "il bisogno sottostante e la direzione evolutiva più sana."
        )
