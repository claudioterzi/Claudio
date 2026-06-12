"""SAR Predittivo — Livello 11: proiezione stati futuri + generazione ipotesi.

Analizza lo stato attuale del sistema (ipotesi, battiti, contraddizioni, contatti)
e produce:
  - 3 scenari futuri (ottimistico / pessimistico / più probabile)
  - Nuove ipotesi H5+ generate da pattern osservati
  - Segnali precoci di degrado da monitorare
  - Valutazione accuratezza proiezioni precedenti (meta-apprendimento)

Output salvato in output/predittivo/ per confronto longitudinale.

Uso:
    from sdq1.sar.predittivo import SARPredittivo
    pred = SARPredittivo(llm_fn=my_llm)
    report = pred.proietta(orizzonte_giorni=30)
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

REPO = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO / "output" / "predittivo"

LLMFn = Callable[[str, str], str]


@dataclass
class Scenario:
    tipo: str           # "ottimistico" | "pessimistico" | "probabile"
    probabilita: float  # 0-1
    descrizione: str
    condizioni_necessarie: list[str]
    segnali_precoci: list[str]
    ipotesi_nuove: list[str]


@dataclass
class ProiezionePredittiva:
    timestamp: float = field(default_factory=time.time)
    data: str = ""
    orizzonte_giorni: int = 30
    stato_corrente: dict[str, Any] = field(default_factory=dict)
    scenari: list[Scenario] = field(default_factory=list)
    ipotesi_generate: list[dict[str, Any]] = field(default_factory=list)
    segnali_degrado: list[str] = field(default_factory=list)
    raccomandazione: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp":        self.timestamp,
            "data":             self.data,
            "orizzonte_giorni": self.orizzonte_giorni,
            "stato_corrente":   self.stato_corrente,
            "scenari": [
                {
                    "tipo":                   s.tipo,
                    "probabilita":            s.probabilita,
                    "descrizione":            s.descrizione,
                    "condizioni_necessarie":  s.condizioni_necessarie,
                    "segnali_precoci":        s.segnali_precoci,
                    "ipotesi_nuove":          s.ipotesi_nuove,
                }
                for s in self.scenari
            ],
            "ipotesi_generate":  self.ipotesi_generate,
            "segnali_degrado":   self.segnali_degrado,
            "raccomandazione":   self.raccomandazione,
        }


SISTEMA_PREDITTIVO = (
    "Sei il modulo predittivo della Scacchiera Auto-Riflessiva (SAR Livello 11). "
    "Il tuo compito è analizzare lo stato attuale di un sistema multi-agente creativo "
    "e proiettare stati futuri con rigore epistemico. "
    "Non sei ottimista per default. Non rassicuri. Identifici pattern reali. "
    "Le tue proiezioni sono falsificabili: specificano condizioni necessarie e segnali precoci. "
    "Generi ipotesi nuove solo se emergono dai dati, non per riempire spazio."
)


class SARPredittivo:
    """Livello 11 della SAR: proiezione predittiva e generazione ipotesi.

    Non sostituisce il ciclo 7-step (Livello 3): lo completa con una vista
    longitudinale. Mentre il ciclo analizza la tensione presente, il predittivo
    traccia la traiettoria del sistema nel tempo.
    """

    def __init__(self, llm_fn: LLMFn | None = None):
        self._llm = llm_fn
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # Raccolta stato                                                        #
    # ------------------------------------------------------------------ #

    def _leggi_ipotesi(self) -> dict[str, Any]:
        p = REPO / "registro_ipotesi.json"
        if not p.exists():
            return {}
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _leggi_battiti(self, ultimi: int = 5) -> list[dict[str, Any]]:
        battito_dir = REPO / "output" / "battito"
        if not battito_dir.exists():
            return []
        files = sorted(battito_dir.glob("battito_*.json"), reverse=True)[:ultimi]
        result = []
        for f in files:
            try:
                result.append(json.loads(f.read_text(encoding="utf-8")))
            except Exception:
                pass
        return result

    def _leggi_contraddizioni(self, ultime: int = 10) -> list[dict[str, Any]]:
        p = REPO / "sdq1" / "sar" / "_contraddittore_storico.jsonl"
        if not p.exists():
            return []
        righe = []
        try:
            for riga in p.read_text(encoding="utf-8").strip().splitlines():
                righe.append(json.loads(riga))
        except Exception:
            pass
        return righe[-ultime:]

    def _leggi_contatti(self, ultimi: int = 10) -> list[dict[str, Any]]:
        p = REPO / "output" / "contatti.jsonl"
        if not p.exists():
            return []
        righe = []
        try:
            for riga in p.read_text(encoding="utf-8").strip().splitlines():
                righe.append(json.loads(riga))
        except Exception:
            pass
        return righe[-ultimi:]

    def _leggi_proiezioni_precedenti(self, ultime: int = 3) -> list[dict[str, Any]]:
        files = sorted(OUTPUT_DIR.glob("proiezione_*.json"), reverse=True)[:ultime]
        result = []
        for f in files:
            try:
                result.append(json.loads(f.read_text(encoding="utf-8")))
            except Exception:
                pass
        return result

    def _aggrega_stato(self) -> dict[str, Any]:
        battiti = self._leggi_battiti()
        contatti = self._leggi_contatti()
        ipotesi = self._leggi_ipotesi()
        contraddizioni = self._leggi_contraddizioni()

        stato_battito = battiti[0]["stato"] if battiti else "SCONOSCIUTO"
        moduli_ok = battiti[0].get("moduli_ok", 0) if battiti else 0
        moduli_tot = battiti[0].get("moduli_totali", 0) if battiti else 0

        n_contatti = len(contatti)
        n_umani = sum(1 for c in contatti if c.get("umano") is True)
        persone = list({c.get("persona", "") for c in contatti if c.get("persona")})

        ipotesi_confermate = [k for k, v in ipotesi.items() if v.get("stato") == "CONFERMATA"]
        ipotesi_aperte = [k for k, v in ipotesi.items() if v.get("stato") == "APERTA"]

        n_contraddizioni = len(contraddizioni)
        regge_count = sum(1 for c in contraddizioni if c.get("regge") is True)
        non_regge_count = sum(1 for c in contraddizioni if c.get("regge") is False)

        return {
            "battito": {
                "stato":         stato_battito,
                "moduli_ok":     moduli_ok,
                "moduli_totali": moduli_tot,
                "ultimi_n":      len(battiti),
            },
            "contatti": {
                "totale":  n_contatti,
                "umani":   n_umani,
                "persone": persone,
            },
            "ipotesi": {
                "confermate": ipotesi_confermate,
                "aperte":     ipotesi_aperte,
                "totali":     len(ipotesi),
            },
            "contraddittore": {
                "totali":       n_contraddizioni,
                "regge":        regge_count,
                "non_regge":    non_regge_count,
                "tasso_regge":  round(regge_count / n_contraddizioni, 2) if n_contraddizioni else None,
            },
        }

    # ------------------------------------------------------------------ #
    # Proiezione LLM                                                       #
    # ------------------------------------------------------------------ #

    def _prompt_proiezione(self, stato: dict[str, Any], orizzonte: int,
                           precedenti: list[dict[str, Any]]) -> str:
        stato_compatto = {
            "battito_stato": stato["battito"]["stato"],
            "moduli": f"{stato['battito']['moduli_ok']}/{stato['battito']['moduli_totali']}",
            "contatti_umani": stato["contatti"]["umani"],
            "persone": stato["contatti"]["persone"],
            "ipotesi_confermate": stato["ipotesi"]["confermate"],
            "ipotesi_aperte": stato["ipotesi"]["aperte"],
            "contraddizioni_non_regge": stato["contraddittore"]["non_regge"],
        }
        return f"""Sistema SDQ-1 (multi-agente creativo, Bruxelles, 12/06/2026).
Stato: {json.dumps(stato_compatto, ensure_ascii=False)}
Proietta {orizzonte} giorni. Rispondi con SOLO questo JSON (breve, max 400 parole totali):
{{"scenari":[{{"tipo":"ottimistico","probabilita":0.25,"descrizione":"1 frase","condizioni_necessarie":["max 2"],"segnali_precoci":["max 2"],"ipotesi_nuove":[]}},{{"tipo":"pessimistico","probabilita":0.35,"descrizione":"1 frase","condizioni_necessarie":["max 2"],"segnali_precoci":["max 2"],"ipotesi_nuove":[]}},{{"tipo":"probabile","probabilita":0.40,"descrizione":"1 frase","condizioni_necessarie":["max 2"],"segnali_precoci":["max 2"],"ipotesi_nuove":["H5: testo falsificabile"]}}],"segnali_degrado":["max 3 segnali brevi"],"raccomandazione":"1 azione concreta entro {orizzonte//3} giorni"}}
Regole: probabilità somma 1.0, H5+ solo se supportate dai dati, SOLO JSON nessun testo extra."""

    def _parse_risposta(self, risposta: str) -> dict[str, Any]:
        """Estrae il JSON dalla risposta LLM, robusto a prefissi/suffissi."""
        s = risposta.strip()
        # trova il primo { e l'ultimo }
        start = s.find("{")
        end = s.rfind("}") + 1
        if start == -1 or end == 0:
            return {}
        try:
            return json.loads(s[start:end])
        except json.JSONDecodeError:
            return {}

    # ------------------------------------------------------------------ #
    # Valutazione accuratezza                                              #
    # ------------------------------------------------------------------ #

    def valuta_accuratezza(self, proiezione_passata: dict[str, Any],
                           stato_attuale: dict[str, Any]) -> dict[str, Any]:
        """Confronta una proiezione passata con lo stato attuale.

        Restituisce un dizionario con score e note per ogni scenario.
        Usato per il meta-apprendimento: le proiezioni migliorano nel tempo.
        """
        if not self._llm:
            return {"valutato": False}

        prompt = (
            f"Confronta questa proiezione passata con lo stato attuale e valuta l'accuratezza.\n\n"
            f"PROIEZIONE ({proiezione_passata.get('data', '?')}, "
            f"orizzonte {proiezione_passata.get('orizzonte_giorni', '?')} giorni):\n"
            f"{json.dumps(proiezione_passata.get('scenari', []), indent=2, ensure_ascii=False)}\n\n"
            f"STATO ATTUALE:\n"
            f"{json.dumps(stato_attuale, indent=2, ensure_ascii=False)}\n\n"
            "Rispondi con JSON:\n"
            '{"accuratezza_ottimistico": 0.0-1.0, "accuratezza_pessimistico": 0.0-1.0, '
            '"accuratezza_probabile": 0.0-1.0, "note": "..."}'
        )
        risposta = self._llm(
            "Sei un valutatore di proiezioni. Sii preciso e calibrato.",
            prompt,
        )
        parsed = self._parse_risposta(risposta)
        parsed["valutato"] = True
        return parsed

    # ------------------------------------------------------------------ #
    # API pubblica                                                         #
    # ------------------------------------------------------------------ #

    def proietta(self, orizzonte_giorni: int = 30) -> ProiezionePredittiva:
        """Genera una proiezione predittiva del sistema.

        Args:
            orizzonte_giorni: quanti giorni nel futuro proiettare (default 30)

        Returns:
            ProiezionePredittiva con 3 scenari + ipotesi nuove + segnali degrado
        """
        ora = datetime.now(timezone.utc)
        stato = self._aggrega_stato()
        precedenti = self._leggi_proiezioni_precedenti()

        proiezione = ProiezionePredittiva(
            timestamp=time.time(),
            data=ora.strftime("%Y-%m-%d"),
            orizzonte_giorni=orizzonte_giorni,
            stato_corrente=stato,
        )

        if not self._llm:
            proiezione.raccomandazione = (
                "[LLM non disponibile — fornisci llm_fn per la proiezione completa]"
            )
            proiezione.segnali_degrado = [
                "LLM non configurato: impossibile generare proiezioni",
            ]
            self._salva(proiezione)
            return proiezione

        prompt = self._prompt_proiezione(stato, orizzonte_giorni, precedenti)
        risposta = self._llm(SISTEMA_PREDITTIVO, prompt)
        dati = self._parse_risposta(risposta)

        # Popola scenari
        for s_raw in dati.get("scenari", []):
            proiezione.scenari.append(Scenario(
                tipo=s_raw.get("tipo", "?"),
                probabilita=float(s_raw.get("probabilita", 0.33)),
                descrizione=s_raw.get("descrizione", ""),
                condizioni_necessarie=s_raw.get("condizioni_necessarie", []),
                segnali_precoci=s_raw.get("segnali_precoci", []),
                ipotesi_nuove=s_raw.get("ipotesi_nuove", []),
            ))

        proiezione.segnali_degrado = dati.get("segnali_degrado", [])
        proiezione.raccomandazione = dati.get("raccomandazione", "")

        # Raccogli ipotesi nuove da tutti gli scenari
        seen: set[str] = set()
        for s in proiezione.scenari:
            for h in s.ipotesi_nuove:
                if h not in seen:
                    seen.add(h)
                    # Costruisce una voce ipotesi compatibile con registro_ipotesi.json
                    proiezione.ipotesi_generate.append({
                        "testo": h,
                        "fonte": "SAR_Predittivo",
                        "data": ora.strftime("%Y-%m-%d"),
                        "scenario": s.tipo,
                        "stato": "GENERATA",
                    })

        self._salva(proiezione)
        return proiezione

    def _salva(self, proiezione: ProiezionePredittiva) -> Path:
        ts = datetime.fromtimestamp(proiezione.timestamp, tz=timezone.utc)
        nome = f"proiezione_{ts.strftime('%Y%m%d_%H%M%S')}.json"
        path = OUTPUT_DIR / nome
        path.write_text(
            json.dumps(proiezione.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return path

    def ultima_proiezione(self) -> dict[str, Any] | None:
        files = sorted(OUTPUT_DIR.glob("proiezione_*.json"), reverse=True)
        if not files:
            return None
        try:
            return json.loads(files[0].read_text(encoding="utf-8"))
        except Exception:
            return None
