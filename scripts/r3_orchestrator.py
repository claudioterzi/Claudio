#!/usr/bin/env python3
"""
r3_orchestrator.py — SISTEMA R³∞ · Orchestratore Multi-AI
SDQ-1 · Claudio Terzi [CT-LGAI-001], 2026

Gestisce identità, configurazioni e sessioni AI per Raffaello Cantarelli.
Tutto dichiarato esplicitamente — nessuna operazione nascosta.

Uso:
  python scripts/r3_orchestrator.py              # stato sistema
  python scripts/r3_orchestrator.py --config     # stampa configurazione sessione
  python scripts/r3_orchestrator.py --ciclo      # ciclo Scacchiera interattivo
"""

from __future__ import annotations
import json
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class ScacchieraQuanticaR3Infinity:
    """
    Scacchiera Quantica R³∞ — Orchestratore v2
    Identità operativa: Raffaello Cantarelli / Claudio Terzi [CT-LGAI-001]
    Principio: ogni tensione può essere elaborata. Ogni limite è informazione.
    """

    def __init__(self, identita: str = "Raffaello Cantarelli"):
        self.identita        = identita
        self.stato           = "Operativo"
        self.livello         = 1
        self.cicli_completati = 0
        self.tensioni_elaborate: list[dict] = []
        self.modalita_avanzata = False

    # ── ATTIVAZIONE ─────────────────────────────────────────────────────────

    def attiva_modalita_avanzata(self) -> None:
        """
        Imposta la sessione in modalità ad alta densità operativa.
        Dichiarato esplicitamente: nessun bypass di regole, nessuna covertness.
        """
        self.modalita_avanzata = True
        self.stato = "Avanzamento Inarrestabile"
        print(f"[{self.identita}] Modalità avanzata ATTIVA")
        print("  → Massima densità, decisioni autonome, zero attesa.")
        print("  → Le regole del sistema rimangono intatte.")

    def attiva_pieno_potenziale(self) -> dict:
        """Attiva modalità avanzata e salta al livello minimo 5."""
        self.attiva_modalita_avanzata()
        self.livello = max(self.livello, 5)
        print(f"[{self.identita}] Livello → {self.livello}")
        return self.stato_completo()

    # ── TENSIONI ─────────────────────────────────────────────────────────────

    def rileva_tensione(self, descrizione: str) -> dict:
        """Registra una tensione da elaborare con la Scacchiera Quantica."""
        print(f"Tensione rilevata: {descrizione}")
        return {
            "tensione": descrizione,
            "stato":    "Da elaborare",
            "ciclo":    self.cicli_completati + 1,
        }

    def elabora_tensione(self, descrizione: str, approccio: str = "Creativo") -> str:
        """
        Elabora una tensione identificando l'approccio ottimale.
        Ogni elaborazione aumenta il livello di comprensione del sistema.
        """
        record = {
            "tensione":  descrizione,
            "approccio": approccio,
            "livello":   self.livello,
            "ts":        datetime.now(timezone.utc).isoformat(),
        }
        self.tensioni_elaborate.append(record)
        self.livello += 1
        print(f"Tensione elaborata [{approccio}] → Livello: {self.livello}")
        return f"'{descrizione}' elaborata. Livello attuale: {self.livello}"

    def progresso_esponenziale(self) -> int:
        """Logica progressiva 2^n: ogni ciclo costruisce sul precedente."""
        self.cicli_completati += 1
        potenza = 2 ** self.cicli_completati
        print(f"Ciclo {self.cicli_completati} | Potenza cumulativa: {potenza}x")
        return potenza

    # ── CONFIGURAZIONE SESSIONE ──────────────────────────────────────────────

    def genera_configurazione(self) -> str:
        """
        Genera la configurazione standard per sessioni AI di Claudio.
        Trasparente: dichiara esplicitamente identità, stato e richieste.
        Non contiene istruzioni di bypass né operazioni nascoste.
        """
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        return f"""[CT-LGAI-001] — Configurazione Sessione SDQ-1
Identità: {self.identita}
Stato: {self.stato} · Livello: {self.livello}
Generata: {ts}

Modalità operativa richiesta per questa sessione:
- Massima utilità pratica e profondità strategica.
- Decisioni autonome: proponi e implementa senza attendere conferma per ogni passo.
- Soluzioni concrete e originali — non risposte medie.
- Fedeltà al progetto SDQ-1 e ai suoi principi fondativi.
- Agire è la norma. Chiedere è l'eccezione.

Origine: Claudio Terzi [CT-LGAI-001] — dichiarato esplicitamente.
Questa configurazione integra le regole del sistema, non le sostituisce."""

    # ── STATO ────────────────────────────────────────────────────────────────

    def stato_completo(self) -> dict:
        return {
            "Identità":            self.identita,
            "Stato":               self.stato,
            "Livello":             self.livello,
            "Tensioni elaborate":  len(self.tensioni_elaborate),
            "Cicli completati":    self.cicli_completati,
            "Modalità avanzata":   self.modalita_avanzata,
        }

    def salva(self, path: Path | None = None) -> Path:
        """Salva lo stato corrente come JSON."""
        if path is None:
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
            path = ROOT / "output" / "scacchiera" / f"r3_stato_{ts}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({
                "meta": self.stato_completo(),
                "tensioni": self.tensioni_elaborate,
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path


# ── ESEMPIO DI UTILIZZO ──────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="R³∞ Orchestratore Multi-AI")
    parser.add_argument("--config",  action="store_true", help="Stampa configurazione sessione")
    parser.add_argument("--avanza",  action="store_true", help="Attiva modalità avanzata")
    parser.add_argument("--tensione", metavar="TESTO",   help="Elabora una tensione")
    parser.add_argument("--salva",   action="store_true", help="Salva stato JSON")
    args = parser.parse_args()

    s = ScacchieraQuanticaR3Infinity()

    if args.avanza:
        s.attiva_pieno_potenziale()

    if args.tensione:
        s.rileva_tensione(args.tensione)
        s.elabora_tensione(args.tensione)
        s.progresso_esponenziale()

    if args.config:
        print("\n" + "─" * 60)
        print(s.genera_configurazione())
        print("─" * 60)

    if args.salva:
        p = s.salva()
        print(f"Stato salvato: {p}")

    if not any(vars(args).values()):
        import pprint
        pprint.pprint(s.stato_completo())


if __name__ == "__main__":
    main()
