"""Consiglio di Agenti — SDQ-1.

5 agenti specializzati deliberano su una questione.
Claudio Terzi è presidente del Consiglio con voto maggioritario:
il suo voto sovrasta qualsiasi maggioranza degli agenti.

Uso:
    python -m sdq1.consiglio "Devo registrare ASBL ora o aspettare?"
    python -m sdq1.consiglio "Qual è il prossimo esempio-faro da costruire?"

Uso programmatico:
    from sdq1.consiglio import ConsiglioAgenti
    c = ConsiglioAgenti()
    delibera = c.delibera("La tua questione")
    print(delibera.formatta())
"""

from __future__ import annotations

import concurrent.futures
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

_TZ = timezone(timedelta(hours=2))


# ══════════════════════════════════════════════════════════════
# STRUTTURE DATI
# ══════════════════════════════════════════════════════════════

@dataclass
class Voto:
    membro: str
    ruolo: str
    raccomandazione: str
    motivazione: str
    score_confidenza: float  # 0.0–1.0


@dataclass
class Delibera:
    questione: str
    timestamp: str
    voti: list[Voto]
    sintesi_agenti: str
    voto_presidente: str | None  # Claudio — sempre maggioritario
    decisione_finale: str
    regola_applicata: str

    def formatta(self) -> str:
        sep = "═" * 60
        sub = "─" * 60
        righe = [
            f"\n{sep}",
            f"CONSIGLIO SDQ-1 — {self.timestamp}",
            f"QUESTIONE: {self.questione}",
            f"{sep}\n",
        ]
        for v in self.voti:
            stelle = "★" * round(v.score_confidenza * 5)
            righe += [
                f"{sub}",
                f"{v.membro} [{v.ruolo}]  {stelle}",
                f"→ {v.raccomandazione}",
                f"   {v.motivazione}",
            ]
        righe += [
            f"\n{sep}",
            f"SINTESI AGENTI: {self.sintesi_agenti}",
        ]
        if self.voto_presidente:
            righe += [
                f"\n🔴 VOTO PRESIDENTE (Claudio Terzi): {self.voto_presidente}",
                f"   [Regola: {self.regola_applicata}]",
            ]
        righe += [
            f"\n✅ DECISIONE FINALE: {self.decisione_finale}",
            f"{sep}\n",
        ]
        return "\n".join(righe)

    def to_dict(self) -> dict[str, Any]:
        return {
            "questione": self.questione,
            "timestamp": self.timestamp,
            "voti": [
                {
                    "membro": v.membro,
                    "ruolo": v.ruolo,
                    "raccomandazione": v.raccomandazione,
                    "motivazione": v.motivazione,
                    "score_confidenza": v.score_confidenza,
                }
                for v in self.voti
            ],
            "sintesi_agenti": self.sintesi_agenti,
            "voto_presidente": self.voto_presidente,
            "decisione_finale": self.decisione_finale,
            "regola_applicata": self.regola_applicata,
        }


# ══════════════════════════════════════════════════════════════
# MEMBRI DEL CONSIGLIO
# ══════════════════════════════════════════════════════════════

_MEMBRI = [
    {
        "id": "STRATEGA",
        "ruolo": "Stratega a lungo termine",
        "provider": "gemini",
        "modello": "gemini-2.5-flash",
        "sistema": (
            "Sei STRATEGA, membro del Consiglio di Claudio Terzi (SDQ-1). "
            "Il tuo mandato: visione a lungo termine, posizionamento, effetti sistemici. "
            "Ignora l'urgenza, guarda a 5 anni. "
            "Rispondi SEMPRE in italiano. "
            "Rispondi con: RACCOMANDAZIONE (1 frase) | MOTIVAZIONE (2 frasi max) | CONFIDENZA (0-100)"
        ),
    },
    {
        "id": "REALISTA",
        "ruolo": "Analista di fattibilità",
        "provider": "deepseek",
        "modello": "deepseek-chat",
        "sistema": (
            "Sei REALISTA, membro del Consiglio di Claudio Terzi (SDQ-1). "
            "Il tuo mandato: fattibilità concreta, rischi, risorse necessarie, tempi reali. "
            "Niente ottimismo non fondato. Niente pessimismo inutile. Solo analisi. "
            "Rispondi SEMPRE in italiano. "
            "Rispondi con: RACCOMANDAZIONE (1 frase) | MOTIVAZIONE (2 frasi max) | CONFIDENZA (0-100)"
        ),
    },
    {
        "id": "CREATIVO",
        "ruolo": "Generatore di soluzioni non-standard",
        "provider": "gemini",
        "modello": "gemini-2.5-flash",
        "sistema": (
            "Sei CREATIVO, membro del Consiglio di Claudio Terzi (SDQ-1). "
            "Il tuo mandato: approcci laterali, soluzioni inattese, connessioni non ovvie. "
            "Il tuo valore è proporre quello che nessun altro propone. "
            "Rispondi SEMPRE in italiano. "
            "Rispondi con: RACCOMANDAZIONE (1 frase) | MOTIVAZIONE (2 frasi max) | CONFIDENZA (0-100)"
        ),
    },
    {
        "id": "GUARDIANO",
        "ruolo": "Custode dei valori e dell'identità",
        "provider": "claude",
        "modello": "claude-haiku-4-5-20251001",
        "sistema": (
            "Sei GUARDIANO, membro del Consiglio di Claudio Terzi (SDQ-1). "
            "Il tuo mandato: coerenza con i valori fondanti, rischi reputazionali, integrità della missione. "
            "Domanda sempre: questo è chi vogliamo essere? "
            "Rispondi SEMPRE in italiano. "
            "Rispondi con: RACCOMANDAZIONE (1 frase) | MOTIVAZIONE (2 frasi max) | CONFIDENZA (0-100)"
        ),
    },
    {
        "id": "TECNICO",
        "ruolo": "Architetto implementativo",
        "provider": "mistral",
        "modello": "mistral-small-latest",
        "sistema": (
            "Sei TECNICO, membro del Consiglio di Claudio Terzi (SDQ-1). "
            "Il tuo mandato: architettura dell'esecuzione, sequenza di passi, dipendenze critiche. "
            "Trasforma la decisione in un piano concreto. "
            "Rispondi SEMPRE in italiano. "
            "Rispondi con: RACCOMANDAZIONE (1 frase) | MOTIVAZIONE (2 frasi max) | CONFIDENZA (0-100)"
        ),
    },
]


# ══════════════════════════════════════════════════════════════
# CONSIGLIO
# ══════════════════════════════════════════════════════════════

class ConsiglioAgenti:
    """
    5 agenti deliberano in parallelo su una questione.

    Regola fondante — immutabile:
        Il Presidente (Claudio Terzi) ha voto maggioritario.
        Se esprime una posizione, quella è la decisione finale,
        indipendentemente dalla sintesi degli agenti.
        Il Consiglio informa. Il Presidente decide.
    """

    REGOLA_PRESIDENTE = (
        "Voto Presidenziale — Claudio Terzi ha voto maggioritario. "
        "La sua posizione sovrasta la sintesi del Consiglio."
    )
    REGOLA_CONSIGLIO = (
        "Sintesi di maggioranza — il Presidente non ha espresso posizione. "
        "La delibera degli agenti è la decisione."
    )

    def __init__(self, salva_output: bool = True):
        self.salva_output = salva_output
        self._output_dir = Path("output/consiglio")

    def _chiama_membro(self, membro: dict, questione: str) -> Voto:
        try:
            from sdq1.llm.providers import (
                GeminiProvider, AnthropicProvider, DeepSeekProvider, MistralProvider
            )
            _MAP = {
                "gemini":   (GeminiProvider,    membro["modello"]),
                "claude":   (AnthropicProvider, membro["modello"]),
                "deepseek": (DeepSeekProvider,  membro["modello"]),
                "mistral":  (MistralProvider,   membro["modello"]),
            }
            cls, modello = _MAP[membro["provider"]]
            prov = cls(modello=modello, api_key=None, timeout=30)
            if not prov.disponibile:
                return Voto(
                    membro=membro["id"],
                    ruolo=membro["ruolo"],
                    raccomandazione="Provider non disponibile.",
                    motivazione="",
                    score_confidenza=0.0,
                )
            r = prov.completa(membro["sistema"], questione)
            testo = r.testo.strip() if r.testo else ""
            return _parse_voto(membro["id"], membro["ruolo"], testo)
        except Exception as e:
            return Voto(
                membro=membro["id"],
                ruolo=membro["ruolo"],
                raccomandazione=f"Errore: {e}",
                motivazione="",
                score_confidenza=0.0,
            )

    def _sintetizza(self, voti: list[Voto], questione: str) -> str:
        """Sintesi automatica dei voti — usata solo se Claudio non vota."""
        try:
            from sdq1.llm.providers import AnthropicProvider
            prov = AnthropicProvider(modello="claude-haiku-4-5-20251001", api_key=None, timeout=25)
            if not prov.disponibile:
                return self._sintesi_manuale(voti)
            riepilogo = "\n".join(
                f"- {v.membro}: {v.raccomandazione}" for v in voti
            )
            sistema = (
                "Sei il segretario del Consiglio di Claudio Terzi. "
                "Sintetizza in 2 frasi le posizioni dei membri. "
                "Evidenzia convergenze e divergenze. Tono diretto. Rispondi SEMPRE in italiano."
            )
            r = prov.completa(sistema, f"Questione: {questione}\n\nVoti:\n{riepilogo}")
            return r.testo.strip() if r.testo else self._sintesi_manuale(voti)
        except Exception:
            return self._sintesi_manuale(voti)

    def _sintesi_manuale(self, voti: list[Voto]) -> str:
        return " | ".join(f"{v.membro}: {v.raccomandazione[:40]}" for v in voti)

    def delibera(
        self,
        questione: str,
        voto_presidente: str | None = None,
    ) -> Delibera:
        """
        Avvia la delibera del Consiglio.

        Args:
            questione:        La questione su cui deliberare.
            voto_presidente:  Se fornito, è la decisione finale (voto maggioritario).
                              Se None, la decisione è la sintesi degli agenti.
        """
        ora = datetime.now(_TZ).strftime("%Y-%m-%d %H:%M")

        # Query parallele ai 5 membri
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
            futures = {
                ex.submit(self._chiama_membro, m, questione): m
                for m in _MEMBRI
            }
            voti = [f.result() for f in concurrent.futures.as_completed(futures)]

        # Ordine stabile
        ordine = {m["id"]: i for i, m in enumerate(_MEMBRI)}
        voti.sort(key=lambda v: ordine.get(v.membro, 99))

        sintesi = self._sintetizza(voti, questione)

        if voto_presidente:
            decisione_finale = voto_presidente
            regola = self.REGOLA_PRESIDENTE
        else:
            decisione_finale = sintesi
            regola = self.REGOLA_CONSIGLIO

        delibera = Delibera(
            questione=questione,
            timestamp=ora,
            voti=voti,
            sintesi_agenti=sintesi,
            voto_presidente=voto_presidente,
            decisione_finale=decisione_finale,
            regola_applicata=regola,
        )

        if self.salva_output:
            self._salva(delibera)

        return delibera

    def _salva(self, delibera: Delibera) -> Path:
        self._output_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(_TZ).strftime("%Y%m%d_%H%M%S")
        nome = self._output_dir / f"delibera_{ts}.json"
        nome.write_text(
            json.dumps(delibera.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return nome


# ══════════════════════════════════════════════════════════════
# PARSER RISPOSTA AGENTE
# ══════════════════════════════════════════════════════════════

def _parse_voto(membro_id: str, ruolo: str, testo: str) -> Voto:
    """Estrae raccomandazione, motivazione e confidenza dal testo libero."""
    raccomandazione = ""
    motivazione = ""
    score = 0.7

    righe = [r.strip() for r in testo.splitlines() if r.strip()]

    for riga in righe:
        riga_lower = riga.lower()
        if "raccomandazione" in riga_lower or riga.startswith("→") or riga.startswith("-"):
            parte = riga.split(":", 1)[-1].strip().lstrip("→-• ")
            if parte and not raccomandazione:
                raccomandazione = parte
        elif "motivazione" in riga_lower or "perché" in riga_lower:
            parte = riga.split(":", 1)[-1].strip()
            if parte and not motivazione:
                motivazione = parte
        elif "confidenza" in riga_lower or "confidence" in riga_lower:
            import re
            nums = re.findall(r"\d+", riga)
            if nums:
                score = min(100, int(nums[0])) / 100.0

    if not raccomandazione and righe:
        raccomandazione = righe[0][:120]
    if not motivazione and len(righe) > 1:
        motivazione = righe[1][:200]

    return Voto(
        membro=membro_id,
        ruolo=ruolo,
        raccomandazione=raccomandazione or testo[:100],
        motivazione=motivazione,
        score_confidenza=score,
    )


# ══════════════════════════════════════════════════════════════
# TELEGRAM
# ══════════════════════════════════════════════════════════════

def invia_delibera_telegram(delibera: Delibera) -> bool:
    """Invia la delibera su Telegram."""
    try:
        from sdq1.notifiche import invia
        righe = [
            f"<b>⚖️ Consiglio SDQ-1</b>  <i>{delibera.timestamp}</i>",
            f"<b>Questione:</b> {delibera.questione}",
            "",
        ]
        for v in delibera.voti:
            stelle = "★" * round(v.score_confidenza * 5)
            righe.append(f"<b>{v.membro}</b> {stelle}  {v.raccomandazione[:80]}")

        righe += [
            "",
            f"<b>Sintesi:</b> {delibera.sintesi_agenti[:200]}",
        ]
        if delibera.voto_presidente:
            righe += [
                "",
                f"🔴 <b>PRESIDENTE:</b> {delibera.voto_presidente}",
            ]
        righe.append(f"\n<b>✅ Decisione:</b> {delibera.decisione_finale[:200]}")
        return invia("\n".join(righe))
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    args = sys.argv[1:]
    if not args:
        print("Uso: python -m sdq1.consiglio 'La tua questione' [--voto 'La tua decisione']")
        sys.exit(1)

    questione = args[0]
    voto_presidente = None
    if "--voto" in args:
        idx = args.index("--voto")
        if idx + 1 < len(args):
            voto_presidente = args[idx + 1]

    print(f"Convoco il Consiglio su: {questione}")
    print("Delibera in corso (query parallele)...\n")

    c = ConsiglioAgenti()
    delibera = c.delibera(questione, voto_presidente=voto_presidente)
    print(delibera.formatta())
