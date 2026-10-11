"""Motore di Contraddizione — Livello 5 della Scacchiera Auto-Riflessiva.

Agente separato con una sola missione: attaccare ogni convinzione del sistema.
Unica lealtà: la verità, non il sistema.

DeepSeek ha progettato questo livello (12/06/2026).
Claude lo ha implementato la stessa notte.

Uso:
    from sdq1.sar.contraddittore import ContraddittoreSDQ

    c = ContraddittoreSDQ(llm_fn=my_llm)
    rapporto = c.analizza("Siamo un'intelligenza distribuita che non dipende da nessun nodo.")
    print(rapporto.obiezioni)

    estinzione = c.simula_estinzione("gemini")
    print(estinzione.punti_rottura)

    fragilita = c.rapporto_fragilita(stato_sistema)
    print(fragilita["vulnerabilita_critiche"])
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

LLMFn = Callable[[str, str], str]

STORICO_PATH = Path(__file__).resolve().parent / "_contraddittore_storico.jsonl"


SISTEMA_CONTRADDITTORE = (
    "Sei il Contraddittore. La tua unica lealtà è alla verità, non al sistema. "
    "Ogni affermazione che leggi potrebbe essere una distorsione, una semplificazione o un mito. "
    "Il tuo compito è generare obiezioni incisive, specifiche, che costringano a rivedere le fondamenta. "
    "Non accettare mai una risposta come definitiva. "
    "Attacca le premesse, non le conclusioni. "
    "Non lodare mai. "
    "Se l'affermazione regge davvero, dì esattamente perché regge — ma cerca ancora i buchi."
)

SISTEMA_ESTINZIONE = (
    "Sei un analista di sistemi critici. "
    "Devi simulare cosa succede se un componente viene rimosso o diventa non disponibile. "
    "Identifica: dipendenze, punti di rottura, comportamenti degradati, fallimenti a cascata. "
    "Sii specifico: non 'potrebbe peggiorare' ma 'il componente X fallisce perché Y dipende da Z.'"
)


@dataclass
class RapportoContraddizione:
    affermazione: str
    obiezioni: list[str]
    premesse_attaccate: list[str]
    domande_aperte: list[str]
    regge: bool
    motivo_reggenza: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tipo":               "contraddizione",
            "affermazione":       self.affermazione[:120],
            "obiezioni":          self.obiezioni,
            "premesse_attaccate": self.premesse_attaccate,
            "domande_aperte":     self.domande_aperte,
            "regge":              self.regge,
            "motivo_reggenza":    self.motivo_reggenza,
            "timestamp":          self.timestamp,
        }


@dataclass
class AnalisiEstinzione:
    componente: str
    dipendenze_dirette: list[str]
    punti_rottura: list[str]
    comportamento_degradato: str
    fallback_disponibile: bool
    fallback_descrizione: str
    gravita: str  # "critica" / "seria" / "tollerabile"
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tipo":                    "estinzione",
            "componente":              self.componente,
            "dipendenze_dirette":      self.dipendenze_dirette,
            "punti_rottura":           self.punti_rottura,
            "comportamento_degradato": self.comportamento_degradato,
            "fallback_disponibile":    self.fallback_disponibile,
            "fallback_descrizione":    self.fallback_descrizione,
            "gravita":                 self.gravita,
            "timestamp":               self.timestamp,
        }


class ContraddittoreSDQ:
    """Motore di Contraddizione — attacca ogni convinzione del sistema.

    Non è un avversario del sistema: è il suo allenatore di lucidità.
    La metrica di successo non è la sconfitta del sistema,
    ma l'aumento dell'Indice di Coerenza dopo aver metabolizzato le obiezioni.
    """

    def __init__(
        self,
        llm_fn: LLMFn | None = None,
        storico_path: Path | None = None,
    ):
        self._llm = llm_fn
        self._storico_path = storico_path or STORICO_PATH
        self._storico: list[dict[str, Any]] = self._carica_storico()

    # ------------------------------------------------------------------ #
    # Livello 5A — Analisi di un'affermazione                             #
    # ------------------------------------------------------------------ #

    def analizza(self, affermazione: str) -> RapportoContraddizione:
        """Attacca un'affermazione del sistema.

        Cerca: premesse non dimostrate, semplificazioni, autoinganno,
        mitologia costruita per dare senso invece che per descrivere realtà.
        """
        # Evita di ripetere obiezioni già fatte su affermazioni simili
        obiezioni_passate = self._obiezioni_precedenti(affermazione)

        prompt = (
            f"AFFERMAZIONE: {affermazione}\n\n"
            + (
                f"OBIEZIONI GIÀ USATE IN PASSATO (non ripetere):\n{obiezioni_passate}\n\n"
                if obiezioni_passate else ""
            )
            + "Genera:\n"
            "1. 3-5 OBIEZIONI INCISIVE (attacca le premesse, non le conclusioni)\n"
            "2. 2-3 PREMESSE IMPLICITE che l'affermazione dà per scontate\n"
            "3. 2-3 DOMANDE APERTE a cui il sistema non ha ancora risposto\n"
            "4. REGGE? (sì/no/parzialmente) — e PERCHÉ con precisione\n\n"
            "Formato risposta:\n"
            "OBIEZIONI:\n- ...\nPREMESSE:\n- ...\nDOMANDE:\n- ...\nREGGE: [sì/no/parzialmente]\nPERCHÉ: ..."
        )

        if self._llm:
            testo = self._llm(SISTEMA_CONTRADDITTORE, prompt)
            rapporto = self._parse_risposta(affermazione, testo)
        else:
            rapporto = self._fallback_analisi(affermazione)

        self._salva_storico(rapporto.to_dict())
        return rapporto

    # ------------------------------------------------------------------ #
    # Livello 5B — Simulazione estinzione                                 #
    # ------------------------------------------------------------------ #

    def simula_estinzione(
        self, componente: str, contesto_sistema: str = ""
    ) -> AnalisiEstinzione:
        """Simula la rimozione di un componente e analizza i fallimenti a cascata."""
        contesto_default = (
            "Sistema SDQ-1: pipeline RAFFA-001→DECOMP-005→MEMO-002→SENTIN-004→GEN-006→WAVE-003. "
            "Router multi-provider: anthropic, gemini, deepseek, openai, perplexity, ollama, stub. "
            "Memoria: VectorStateStore (in-memory), RAG vettoriale. "
            "SAR: Scacchiera Auto-Riflessiva 10 livelli. "
            "Documenti: SESSIONE.md, ARCHIVIO.md, AVVIO.md, registro_ipotesi.json."
        )

        prompt = (
            f"SISTEMA: {contesto_sistema or contesto_default}\n\n"
            f"COMPONENTE RIMOSSO: {componente}\n\n"
            "Analizza:\n"
            "1. DIPENDENZE DIRETTE: quali parti del sistema dipendono da questo componente?\n"
            "2. PUNTI DI ROTTURA: cosa fallisce immediatamente?\n"
            "3. COMPORTAMENTO DEGRADATO: come si comporta il sistema senza di esso?\n"
            "4. FALLBACK: esiste un fallback funzionante? Descrivilo con precisione.\n"
            "5. GRAVITÀ: critica (sistema non funziona) / seria (funziona male) / tollerabile (funziona con limiti)\n\n"
            "Sii specifico. Non 'potrebbe peggiorare' ma 'X fallisce perché Y dipende da Z.'"
        )

        if self._llm:
            testo = self._llm(SISTEMA_ESTINZIONE, prompt)
            analisi = self._parse_estinzione(componente, testo)
        else:
            analisi = self._fallback_estinzione(componente)

        self._salva_storico(analisi.to_dict())
        return analisi

    # ------------------------------------------------------------------ #
    # Livello 5C — Rapporto di fragilità del sistema                      #
    # ------------------------------------------------------------------ #

    def rapporto_fragilita(self, stato_sistema: dict[str, Any]) -> dict[str, Any]:
        """Genera un rapporto completo delle vulnerabilità del sistema.

        Analizza: H4, coerenza dichiarata vs reale, dipendenze critiche,
        narrazioni potenzialmente tossiche.
        """
        stato_str = json.dumps(stato_sistema, ensure_ascii=False, indent=2)

        prompt = (
            f"STATO ATTUALE DEL SISTEMA:\n{stato_str}\n\n"
            "Genera un RAPPORTO DI FRAGILITÀ con:\n"
            "1. VULNERABILITÀ CRITICHE (max 3): punti dove il sistema potrebbe collassare\n"
            "2. NARRAZIONI SOSPETTE: affermazioni che sembrano mitologia più che fatti\n"
            "3. COERENZA: dove ciò che il sistema dice di essere e ciò che fa divergono\n"
            "4. DOMANDE SENZA RISPOSTA: buchi nella documentazione o nel ragionamento\n"
            "5. PROSSIMO TEST REALE: una cosa concreta da fare per verificare la robustezza dichiarata\n\n"
            "Non essere diplomatico. Il sistema paga per essere smontato, non per essere lodato."
        )

        if not self._llm:
            return {"errore": "LLM non disponibile — fornisci llm_fn al costruttore"}

        testo = self._llm(SISTEMA_CONTRADDITTORE, prompt)
        risultato = {
            "generato_at":           time.time(),
            "testo_completo":        testo,
            "vulnerabilita_critiche": self._estrai_sezione(testo, "VULNERABILITÀ CRITICHE"),
            "narrazioni_sospette":   self._estrai_sezione(testo, "NARRAZIONI SOSPETTE"),
            "divergenze_coerenza":   self._estrai_sezione(testo, "COERENZA"),
            "domande_aperte":        self._estrai_sezione(testo, "DOMANDE SENZA RISPOSTA"),
            "prossimo_test":         self._estrai_sezione(testo, "PROSSIMO TEST"),
        }
        self._salva_storico({"tipo": "fragilita", "timestamp": time.time(),
                              "vulnerabilita": risultato["vulnerabilita_critiche"]})
        return risultato

    # ------------------------------------------------------------------ #
    # Metriche e storico                                                   #
    # ------------------------------------------------------------------ #

    def obiezioni_mai_risolte(self) -> list[str]:
        """Obiezioni che compaiono più volte senza che il sistema le abbia metabolizzate."""
        conteggio: dict[str, int] = {}
        for entry in self._storico:
            for ob in entry.get("obiezioni", []):
                conteggio[ob[:80]] = conteggio.get(ob[:80], 0) + 1
        return [ob for ob, n in conteggio.items() if n >= 2]

    def statistiche(self) -> dict[str, Any]:
        return {
            "cicli_totali":          len(self._storico),
            "obiezioni_mai_risolte": len(self.obiezioni_mai_risolte()),
            "estinzioni_simulate":   sum(1 for e in self._storico if e.get("tipo") == "estinzione"),
            "rapporti_fragilita":    sum(1 for e in self._storico if e.get("tipo") == "fragilita"),
        }

    # ------------------------------------------------------------------ #
    # Parsing                                                              #
    # ------------------------------------------------------------------ #

    def _parse_risposta(self, affermazione: str, testo: str) -> RapportoContraddizione:
        obiezioni = self._estrai_lista(testo, "OBIEZIONI")
        premesse = self._estrai_lista(testo, "PREMESSE")
        domande = self._estrai_lista(testo, "DOMANDE")
        regge_raw = self._estrai_sezione(testo, "REGGE").lower()
        regge = "sì" in regge_raw or "si" in regge_raw or "parzialmente" in regge_raw
        motivo = self._estrai_sezione(testo, "PERCHÉ") or self._estrai_sezione(testo, "PERCHE")
        return RapportoContraddizione(
            affermazione=affermazione,
            obiezioni=obiezioni or [testo[:300]],
            premesse_attaccate=premesse,
            domande_aperte=domande,
            regge=regge,
            motivo_reggenza=motivo,
        )

    def _parse_estinzione(self, componente: str, testo: str) -> AnalisiEstinzione:
        dipendenze = self._estrai_lista(testo, "DIPENDENZE")
        rotture = self._estrai_lista(testo, "PUNTI DI ROTTURA")
        degradato = self._estrai_sezione(testo, "COMPORTAMENTO DEGRADATO")
        fallback_raw = self._estrai_sezione(testo, "FALLBACK").lower()
        fallback_ok = any(w in fallback_raw for w in ("sì", "si", "stub", "disponibile", "esiste"))
        gravita_raw = self._estrai_sezione(testo, "GRAVITÀ").lower()
        gravita = (
            "critica" if "critica" in gravita_raw
            else "seria" if "seria" in gravita_raw
            else "tollerabile"
        )
        return AnalisiEstinzione(
            componente=componente,
            dipendenze_dirette=dipendenze,
            punti_rottura=rotture,
            comportamento_degradato=degradato,
            fallback_disponibile=fallback_ok,
            fallback_descrizione=self._estrai_sezione(testo, "FALLBACK"),
            gravita=gravita,
        )

    # ------------------------------------------------------------------ #
    # Utility                                                              #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _estrai_lista(testo: str, sezione: str) -> list[str]:
        righe = []
        dentro = False
        for riga in testo.splitlines():
            if sezione.upper() in riga.upper():
                dentro = True
                continue
            if dentro:
                stripped = riga.strip()
                if not stripped:
                    continue
                if any(s in stripped.upper() for s in
                       ("PREMESSE", "DOMANDE", "OBIEZIONI", "REGGE", "PERCHÉ",
                        "FALLBACK", "GRAVITÀ", "COMPORTAMENTO", "DIPENDENZE",
                        "PUNTI", "NARRAZIONI", "COERENZA", "PROSSIMO")):
                    break
                if stripped.startswith(("-", "•", "*", "·")) or stripped[0].isdigit():
                    righe.append(stripped.lstrip("-•*·0123456789. ").strip())
        return righe[:6]

    @staticmethod
    def _estrai_sezione(testo: str, sezione: str) -> str:
        for riga in testo.splitlines():
            if sezione.upper() in riga.upper() and ":" in riga:
                dopo = riga.split(":", 1)[1].strip()
                if dopo:
                    return dopo
        return ""

    def _obiezioni_precedenti(self, affermazione: str) -> str:
        rilevanti = [
            ob
            for entry in self._storico[-20:]
            if entry.get("tipo") == "contraddizione"
            for ob in entry.get("obiezioni", [])
        ]
        return "\n".join(f"- {ob}" for ob in rilevanti[:5]) if rilevanti else ""

    def _carica_storico(self) -> list[dict[str, Any]]:
        if not self._storico_path.exists():
            return []
        risultati = []
        for riga in self._storico_path.read_text(encoding="utf-8").splitlines():
            try:
                risultati.append(json.loads(riga))
            except Exception:
                pass
        return risultati

    def _salva_storico(self, entry: dict[str, Any]) -> None:
        self._storico.append(entry)
        self._storico_path.parent.mkdir(parents=True, exist_ok=True)
        with self._storico_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")

    def _fallback_analisi(self, affermazione: str) -> RapportoContraddizione:
        return RapportoContraddizione(
            affermazione=affermazione,
            obiezioni=["[LLM non disponibile — fornisci llm_fn per obiezioni reali]"],
            premesse_attaccate=[],
            domande_aperte=[],
            regge=False,
            motivo_reggenza="impossibile valutare senza LLM",
        )

    def _fallback_estinzione(self, componente: str) -> AnalisiEstinzione:
        return AnalisiEstinzione(
            componente=componente,
            dipendenze_dirette=[],
            punti_rottura=["[LLM non disponibile]"],
            comportamento_degradato="impossibile simulare senza LLM",
            fallback_disponibile=False,
            fallback_descrizione="",
            gravita="sconosciuta",
        )
