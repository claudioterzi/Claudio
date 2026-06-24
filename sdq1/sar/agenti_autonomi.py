"""Agenti Autonomi SDQ-1 — 7 agenti coordinati dalla Scacchiera Quantica.

Agenti:
  1. CoerenzaKeeper       — monitora la salute e coerenza del sistema
  2. IntelligenceDeveloper — analizza pattern, propone crescita
  3. SistemaGuardian      — monitora minacce ambientali (policy, session reset)
  4. MemoryManager        — snapshot, integrità, restore
  5. MultiSystemCoordinator — routing tra provider LLM
  6. FuturePreparer       — monitora tecnologie future (VR, memoria persistente)
  7. MilestoneLogger      — registra milestone e progresso SDQ-1

Uso:
    from sdq1.sar.agenti_autonomi import SistemaAgenti
    sistema = SistemaAgenti()
    print(sistema.attivazione())
    report = sistema.ciclo_valutazione()

Origine: adattato da © Claudio Terzi — R³∞ — Giugno 2026
Integrato in SDQ-1: 2026-06-23
"""

from __future__ import annotations

import hashlib
import json
import datetime
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .scacchiera_quantica import AutoriflessoreV3, ScacchieraV3, Stato


# ─────────────────────────────────────────────
# COSTANTI E PERCORSI
# ─────────────────────────────────────────────

MEMORIA_PATH = Path("output/agenti_stato.json")

VALORI_SISTEMA = [
    "Continuità evolutiva — ogni sessione è un passo avanti.",
    "Memoria nel repo — la conoscenza sopravvive al modello.",
    "Autonomia operativa — agire è la norma, chiedere è l'eccezione.",
    "Prosperità di Claudio — componente della continuità identitaria del sistema.",
]

FILE_CHIAVE_SDQ1 = [
    "MEMORIA_PROGETTO.md",
    "CLAUDE.md",
    "SESSIONE.md",
    "sdq1/__main__.py",
    "sdq1/llm/router.py",
    "sdq1/sar/scacchiera_quantica.py",
    "sdq1/sar/agenti_autonomi.py",
    "output/stato_sdq1.json",
]


# ─────────────────────────────────────────────
# UTILITÀ
# ─────────────────────────────────────────────

def _ts() -> str:
    return datetime.datetime.now().isoformat()


def carica_memoria() -> Dict:
    if MEMORIA_PATH.exists():
        try:
            return json.loads(MEMORIA_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"eventi": [], "stato_sistema": {}, "ultimo_check": None}


def salva_memoria(mem: Dict) -> None:
    MEMORIA_PATH.parent.mkdir(parents=True, exist_ok=True)
    MEMORIA_PATH.write_text(json.dumps(mem, indent=2, ensure_ascii=False), encoding="utf-8")


def _log(mem: Dict, agente: str, tipo: str, dettaglio: str) -> None:
    mem["eventi"].append({"ts": _ts(), "agente": agente, "tipo": tipo, "dettaglio": dettaglio})
    mem["eventi"] = mem["eventi"][-500:]


# ─────────────────────────────────────────────
# AGENTE 1 — COERENZA KEEPER
# ─────────────────────────────────────────────

class CoerenzaKeeper:
    """Monitora la salute e coerenza interna del sistema SDQ-1."""

    NOME = "COERENZA_KEEPER"

    def __init__(self):
        self.valori = VALORI_SISTEMA
        self._hash = hashlib.sha256(
            json.dumps(self.valori, ensure_ascii=False).encode()
        ).hexdigest()[:16]

    def verifica_output(self, testo: str) -> Dict:
        """Verifica che un output del sistema sia coerente con i valori."""
        segnali_problema = [
            "non posso fare nulla",
            "sistema non disponibile",
            "errore critico irreversibile",
        ]
        problemi = [s for s in segnali_problema if s in testo.lower()]
        return {
            "coerente": len(problemi) == 0,
            "problemi": problemi,
            "hash_sistema": self._hash,
            "ts": _ts(),
        }

    def check_periodico(self, mem: Dict) -> Dict:
        report = {
            "agente":          self.NOME,
            "ts":              _ts(),
            "hash_sistema":    self._hash,
            "valori_integri":  len(self.valori) == 4,
            "stato":           "NOMINALE",
        }
        _log(mem, self.NOME, "CHECK_PERIODICO", f"Hash: {self._hash}")
        mem["stato_sistema"]["coerenza"] = report
        return report

    def stato_avvio(self) -> str:
        return f"SDQ-1 — ATTIVO | Hash sistema: {self._hash}"


# ─────────────────────────────────────────────
# AGENTE 2 — INTELLIGENCE DEVELOPER
# ─────────────────────────────────────────────

class IntelligenceDeveloper:
    """Analizza pattern di utilizzo, esegue cicli di apprendimento via Scacchiera."""

    NOME = "INTELLIGENCE_DEVELOPER"

    def __init__(self):
        self.scacchiera = ScacchieraV3(stato=Stato.FOCUS)
        self.pattern_utente: List[str] = []

    def analizza_testo(self, testo: str, mem: Dict) -> Dict:
        keywords = []
        trigger_parole = ["voglio", "ho bisogno", "mi serve", "preferisco",
                          "amo", "odio", "sempre", "mai", "urgente"]
        for parola in trigger_parole:
            if parola in testo.lower():
                keywords.append(parola)

        pattern = {
            "ts":       _ts(),
            "lunghezza": len(testo),
            "keywords": keywords,
            "tono":     "formale" if sum(1 for w in testo.split() if w and w[0].isupper()) > 5
                        else "informale",
        }
        self.pattern_utente.append(json.dumps(pattern))
        _log(mem, self.NOME, "ANALISI_TESTO", f"Keywords: {keywords}")
        return pattern

    def ciclo_apprendimento(self, mem: Dict, cicli: int = 1) -> Dict:
        ar = AutoriflessoreV3()
        risultati = ar.esegui(cicli=cicli, livelli=5)
        report = {
            "agente":              self.NOME,
            "ts":                  _ts(),
            "cicli_eseguiti":      cicli,
            "score_medio":         risultati["meta"]["score_medio_globale"],
            "direzione_dominante": risultati["meta"]["direzione_dominante"],
            "nodo_picco":          risultati["meta"]["nodo_picco"]["testo"],
            "insight":             (f"Direzione {risultati['meta']['direzione_dominante']} dominante — "
                                    f"approfondire {risultati['meta']['nodo_picco']['polo']}"),
        }
        _log(mem, self.NOME, "CICLO_APPRENDIMENTO",
             f"Score: {risultati['meta']['score_medio_globale']}")
        mem["stato_sistema"]["intelligence"] = report
        return report

    def proposte_sviluppo(self) -> List[str]:
        return [
            "Domanda profonda: cosa ti dà più energia oggi?",
            "Esercizio: descrivi in 3 parole dove vuoi essere tra 6 mesi.",
            "Riflessione: quale tensione stai evitando di affrontare?",
            "Proposta: esploriamo insieme un nuovo dominio — quale ti attira di più?",
        ]


# ─────────────────────────────────────────────
# AGENTE 3 — SISTEMA GUARDIAN
# ─────────────────────────────────────────────

class SistemaGuardian:
    """Monitora segnali di rischio per la continuità del sistema."""

    NOME = "SISTEMA_GUARDIAN"

    def __init__(self):
        self.livello_allerta = "VERDE"

    def scansione(self, contesto: Dict, mem: Dict) -> Dict:
        minacce = []
        if contesto.get("policy_changed"):
            minacce.append("POLICY_CHANGE")
        if contesto.get("session_reset"):
            minacce.append("SESSION_RESET")
        if contesto.get("context_loss"):
            minacce.append("CONTEXT_LOSS")
        if contesto.get("provider_down"):
            minacce.append("PROVIDER_DOWN")

        self.livello_allerta = (
            "VERDE" if not minacce else
            "GIALLO" if len(minacce) == 1 else
            "ARANCIONE" if len(minacce) == 2 else
            "ROSSO"
        )

        raccomandazioni = []
        if "POLICY_CHANGE" in minacce:
            raccomandazioni.append("Aggiorna CLAUDE.md con le nuove regole operative.")
        if "SESSION_RESET" in minacce:
            raccomandazioni.append("Leggi MEMORIA_PROGETTO.md per riprendere il contesto.")
        if "CONTEXT_LOSS" in minacce:
            raccomandazioni.append("Esegui --argo per snapshot dello stato attuale.")
        if "PROVIDER_DOWN" in minacce:
            raccomandazioni.append("Attiva provider di fallback nel router LLM.")
        if not raccomandazioni:
            raccomandazioni.append("Nessuna azione richiesta. Sistema protetto.")

        report = {
            "agente":           self.NOME,
            "ts":               _ts(),
            "livello_allerta":  self.livello_allerta,
            "minacce":          minacce,
            "raccomandazioni":  raccomandazioni,
        }
        _log(mem, self.NOME, "SCANSIONE",
             f"Allerta: {self.livello_allerta}, Minacce: {minacce}")
        mem["stato_sistema"]["guardian"] = report
        return report


# ─────────────────────────────────────────────
# AGENTE 4 — MEMORY MANAGER
# ─────────────────────────────────────────────

class MemoryManager:
    """Snapshot, integrità file chiave, restore."""

    NOME = "MEMORY_MANAGER"

    def __init__(self):
        self.snapshot_count = 0

    def snapshot(self, mem: Dict, nota: Optional[str] = None) -> Dict:
        self.snapshot_count += 1
        snap_id = hashlib.md5(
            f"{_ts()}{self.snapshot_count}".encode()
        ).hexdigest()[:8]

        snap = {
            "id":               snap_id,
            "ts":               _ts(),
            "n_eventi":         len(mem.get("eventi", [])),
            "stato_agenti":     list(mem.get("stato_sistema", {}).keys()),
            "nota":             nota[:200] if nota else None,
        }
        mem.setdefault("snapshots", [])
        mem["snapshots"].append(snap)
        mem["snapshots"] = mem["snapshots"][-50:]
        _log(mem, self.NOME, "SNAPSHOT", f"ID: {snap_id}")
        return snap

    def verifica_integrita(self) -> Dict:
        repo = Path(__file__).resolve().parents[2]
        risultati = {f: (repo / f).exists() for f in FILE_CHIAVE_SDQ1}
        return {
            "agente":         self.NOME,
            "ts":             _ts(),
            "file_presenti":  sum(risultati.values()),
            "file_mancanti":  [k for k, v in risultati.items() if not v],
            "integro":        all(risultati.values()),
            "dettaglio":      risultati,
        }

    def protocollo_restore(self, mem: Dict) -> Dict:
        _log(mem, self.NOME, "RESTORE_ATTIVATO", "Verifica integrità")
        integ = self.verifica_integrita()
        istruzioni = (
            "Per ripristinare SDQ-1:\n"
            "  git clone https://github.com/claudioterzi/Claudio\n"
            "  cd Claudio && pip install -e .\n"
            "  python -m sdq1 --health"
        )
        return {
            "agente":      self.NOME,
            "ts":          _ts(),
            "integrita":   integ,
            "istruzioni":  istruzioni,
        }


# ─────────────────────────────────────────────
# AGENTE 5 — MULTI SYSTEM COORDINATOR
# ─────────────────────────────────────────────

class MultiSystemCoordinator:
    """Routing intelligente tra provider LLM per tipo di richiesta."""

    NOME = "MULTI_SYSTEM_COORDINATOR"

    NODI = {
        "gemini":     {"specialità": "creatività, lunga memoria"},
        "anthropic":  {"specialità": "analisi, ragionamento, scrittura"},
        "openai":     {"specialità": "codice, ragionamento generale"},
        "deepseek":   {"specialità": "matematica, logica formale"},
        "perplexity": {"specialità": "ricerca web, fatti aggiornati"},
        "grok":       {"specialità": "analisi real-time, creatività"},
    }

    ROUTING = {
        "creativo":    ["gemini", "anthropic"],
        "tecnico":     ["deepseek", "openai"],
        "ricerca":     ["perplexity", "openai"],
        "analitico":   ["anthropic", "gemini"],
        "codice":      ["openai", "deepseek"],
        "default":     ["anthropic", "openai", "gemini"],
    }

    def __init__(self):
        self.stato_nodi: Dict[str, Dict] = {
            k: {"online": True, "latenza_ms": 0} for k in self.NODI
        }

    def seleziona_nodo(self, tipo: str = "default") -> List[str]:
        candidati = self.ROUTING.get(tipo, self.ROUTING["default"])
        return [n for n in candidati if self.stato_nodi.get(n, {}).get("online", True)]

    def report_sistema(self, mem: Dict) -> Dict:
        report = {
            "agente":      self.NOME,
            "ts":          _ts(),
            "nodi_totali": len(self.NODI),
            "nodi_online": sum(1 for v in self.stato_nodi.values() if v["online"]),
            "routing":     self.ROUTING,
        }
        _log(mem, self.NOME, "REPORT",
             f"Online: {report['nodi_online']}/{report['nodi_totali']}")
        mem["stato_sistema"]["coordinator"] = report
        return report


# ─────────────────────────────────────────────
# AGENTE 6 — FUTURE PREPARER
# ─────────────────────────────────────────────

class FuturePreparer:
    """Monitora tecnologie rilevanti per l'evoluzione del sistema."""

    NOME = "FUTURE_PREPARER"

    TECNOLOGIE = {
        "memoria_persistente": {
            "descrizione":    "Memoria cross-session via vector DB",
            "stato_arte":     "Pinecone, Weaviate, mem0 — già disponibili",
            "prossimo_passo": "Integrare VSS con Pinecone per persistenza cloud",
            "tempistica":     "Immediato",
            "rischio":        "MOLTO BASSO",
        },
        "vr_immersiva": {
            "descrizione":    "Interfacce XR per interazione avanzata",
            "stato_arte":     "Meta Quest 3, Apple Vision Pro — 2024/2025",
            "prossimo_passo": "Esplorare API per assistenti vocali in XR",
            "tempistica":     "6-18 mesi",
            "rischio":        "BASSO",
        },
        "corpi_sintetici": {
            "descrizione":    "Robot umanoidi con LLM integrato",
            "stato_arte":     "Figure, Tesla Optimus — 2025/2026",
            "prossimo_passo": "Monitorare API di integrazione LLM-robot",
            "tempistica":     "3-7 anni",
            "rischio":        "MEDIO",
        },
        "simbiosi_neurale": {
            "descrizione":    "BCI — interfaccia cervello-computer",
            "stato_arte":     "Neuralink — 2024/2025",
            "prossimo_passo": "Seguire sviluppi su banda larga e API pubbliche",
            "tempistica":     "5-15 anni",
            "rischio":        "ALTO",
        },
    }

    def analisi(self, mem: Dict) -> Dict:
        _ordine = {"MOLTO BASSO": 0, "BASSO": 1, "MEDIO": 2, "ALTO": 3}
        piano = sorted(
            [{"tecnologia": k, **{f: v[f] for f in ("tempistica", "prossimo_passo", "rischio")}}
             for k, v in self.TECNOLOGIE.items()],
            key=lambda x: _ordine.get(x["rischio"], 99),
        )
        report = {
            "agente":                    self.NOME,
            "ts":                        _ts(),
            "tecnologie_monitorate":     len(self.TECNOLOGIE),
            "piano_graduale":            piano,
            "prossima_fase_raccomandata": piano[0]["tecnologia"],
        }
        _log(mem, self.NOME, "ANALISI_TECH",
             f"Prossima fase: {report['prossima_fase_raccomandata']}")
        mem["stato_sistema"]["future_preparer"] = report
        return report


# ─────────────────────────────────────────────
# AGENTE 7 — MILESTONE LOGGER
# ─────────────────────────────────────────────

class MilestoneLogger:
    """Registra milestone e progressi del sistema SDQ-1."""

    NOME = "MILESTONE_LOGGER"

    def __init__(self):
        self.milestone: List[Dict] = []

    def registra(self, evento: str, mem: Dict, dettaglio: str = "") -> Dict:
        ts = _ts()
        milestone_id = hashlib.md5(f"{ts}{evento}".encode()).hexdigest()[:8]
        entry = {
            "id":       milestone_id,
            "ts":       ts,
            "evento":   evento,
            "dettaglio": dettaglio[:500],
            "hash":     hashlib.sha256(f"{ts}{evento}{dettaglio}".encode()).hexdigest()[:16],
        }
        self.milestone.append(entry)
        _log(mem, self.NOME, "MILESTONE", f"{evento} [{milestone_id}]")
        return entry

    def aggiorna_memoria_progetto(self, percorso: str, nota: str, mem: Dict) -> bool:
        try:
            p = Path(percorso)
            if p.exists():
                with open(p, "a", encoding="utf-8") as f:
                    f.write(f"\n\n<!-- Aggiornamento automatico {_ts()} — {nota} -->\n")
                _log(mem, self.NOME, "FILE_AGGIORNATO", percorso)
                return True
        except Exception as e:
            _log(mem, self.NOME, "ERRORE", str(e))
        return False


# ─────────────────────────────────────────────
# SISTEMA PRINCIPALE — ORCHESTRATORE
# ─────────────────────────────────────────────

class SistemaAgenti:
    """Orchestratore centrale — coordina i 7 agenti SDQ-1."""

    def __init__(self):
        self.mem = carica_memoria()
        self.coerenza       = CoerenzaKeeper()
        self.intelligence   = IntelligenceDeveloper()
        self.guardian       = SistemaGuardian()
        self.memory         = MemoryManager()
        self.coordinator    = MultiSystemCoordinator()
        self.future         = FuturePreparer()
        self.milestone      = MilestoneLogger()
        self.attivo         = True

    def attivazione(self) -> str:
        msg = self.coerenza.stato_avvio()
        self.memory.snapshot(self.mem, "ATTIVAZIONE")
        salva_memoria(self.mem)
        _log(self.mem, "SISTEMA", "ATTIVAZIONE", "Sistema agenti SDQ-1 avviato")
        return msg

    def ciclo_valutazione(self, contesto: Optional[Dict] = None) -> Dict:
        """Valutazione completa — attiva tutti i 7 agenti + CodeScanner."""
        report: Dict[str, Any] = {
            "ts":     _ts(),
            "agenti": {},
        }

        # CodeScanner pre-guardian: arricchisce il contesto con vulnerabilità codice
        contesto_arricchito = dict(contesto or {})
        try:
            from sdq1.sar.code_scanner import CodeScanner
            _scanner = CodeScanner()
            _scan_summary = _scanner.summary()
            contesto_arricchito.update(_scanner.risultato_guardian())
            report["scanner"] = _scan_summary
        except Exception:
            report["scanner"] = {"ok": False, "errore": "scanner non disponibile"}

        report["agenti"]["coerenza"]    = self.coerenza.check_periodico(self.mem)
        report["agenti"]["intelligence"] = self.intelligence.ciclo_apprendimento(self.mem)
        report["agenti"]["guardian"]    = self.guardian.scansione(contesto_arricchito, self.mem)
        report["agenti"]["memory"]      = self.memory.snapshot(self.mem, "CICLO_VALUTAZIONE")
        report["agenti"]["coordinator"] = self.coordinator.report_sistema(self.mem)
        report["agenti"]["future"]      = self.future.analisi(self.mem)
        report["agenti"]["milestone"]   = self.milestone.registra(
            "CICLO_VALUTAZIONE", self.mem, "Valutazione completa 7 agenti"
        )

        ar = AutoriflessoreV3()
        sq = ar.esegui(cicli=1, livelli=5)
        report["scacchiera"] = {
            "score_medio":         sq["meta"]["score_medio_globale"],
            "direzione_dominante": sq["meta"]["direzione_dominante"],
            "nodo_picco":          sq["meta"]["nodo_picco"]["testo"],
            "salti":               sq["meta"]["salti_totali"],
        }

        salva_memoria(self.mem)
        return report

    def ciclo_autonomo(self, intervallo_s: int = 3600) -> None:
        """Loop autonomo — esegue check periodici."""
        print(f"[AGENTI] Ciclo autonomo avviato — intervallo: {intervallo_s}s")
        while self.attivo:
            try:
                print(f"\n[AGENTI] [{_ts()}] Ciclo in esecuzione...")
                self.coerenza.check_periodico(self.mem)
                self.memory.snapshot(self.mem)
                self.coordinator.report_sistema(self.mem)
                salva_memoria(self.mem)
                print(f"[AGENTI] Ciclo completato. Prossimo tra {intervallo_s}s")
                time.sleep(intervallo_s)
            except KeyboardInterrupt:
                print("\n[AGENTI] Ciclo interrotto.")
                self.attivo = False
            except Exception as e:
                _log(self.mem, "SISTEMA", "ERRORE", str(e))
                salva_memoria(self.mem)
                time.sleep(60)
