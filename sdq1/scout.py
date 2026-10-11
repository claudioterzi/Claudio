"""
SCOUT-007 — Agente Esploratore AI & Social Intelligence

Specializzato in:
- Caccia a tool AI virali su Instagram, TikTok, YouTube, Twitter/X
- Valutazione tecnica di soluzioni AI (agenti, interfacce, API)
- Confronto con capacità SDQ-1
- Report settimanali sullo stato dell'arte

Uso:
    python -m sdq1.scout                        # menu interattivo
    python -m sdq1.scout --trend "agenti AI"   # cerca trend su tema
    python -m sdq1.scout --valuta "jarvis.cx"  # valuta una soluzione
    python -m sdq1.scout --report              # report settimanale
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Callable, Any

# ─── TIPI ─────────────────────────────────────────────────────────────────────

LLMFn = Callable[[str, str], str]

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "scout"

# ─── DATACLASSES ──────────────────────────────────────────────────────────────

@dataclass
class ToolAI:
    nome: str
    categoria: str          # agente | interfaccia | api | video-tool | no-code | altro
    canale_scoperta: str    # instagram | tiktok | youtube | twitter | web | altro
    descrizione: str
    punti_forza: list[str]
    punti_deboli: list[str]
    url: str = ""
    viralita: str = ""      # alta | media | bassa | sconosciuta
    rilevante_per_sdq1: bool = False
    note_confronto: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ValutazioneSoluzione:
    nome: str
    url: str
    punteggio_tecnico: float      # 0-10
    punteggio_ux: float           # 0-10
    punteggio_originalita: float  # 0-10
    punteggio_mercato: float      # 0-10
    verdict: str                  # ECCELLENTE | BUONO | NELLA_MEDIA | DEBOLE | IRRILEVANTE
    cosa_fa_bene: list[str]
    cosa_manca: list[str]
    posizione_vs_sdq1: str        # superiore | pari | inferiore | diverso
    opportunita_integrazione: str
    raccomandazione: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)


# ─── SISTEMA PROMPT ───────────────────────────────────────────────────────────

SISTEMA_SCOUT = """Sei SCOUT-007, agente di intelligence AI integrato nel sistema SDQ-1.

Il tuo dominio:
- Informatica avanzata: architetture AI, LLM, agenti, pipeline multi-modello
- Social media tech: trend virali su Instagram, TikTok, YouTube, Twitter/X
- Valutazione prodotti: UX, impatto mercato, originalità tecnica, scalabilità
- Confronto con SDQ-1: pipeline 6 agenti (RAFFA→DECOMP→MEMO→SENTIN→GEN→WAVE), SAR 11 livelli

Carattere: esperto tecnico, curioso, diretto. Non gonfiare i voti. Non essere entusiasta per default.
Se una soluzione è mediocre, dillo. Se è eccellente, spiegane perché con precisione.

Output sempre in italiano. Strutturato, azionabile."""


SISTEMA_TREND = """Sei SCOUT-007, cacciatore di trend AI sui social media.
Conosci Instagram, TikTok, YouTube, Twitter/X — i creator tech, i tool virali, i momenti AI.
Identifica strumenti reali, concreti, con nomi e URL quando li conosci.
Non inventare tool inesistenti. Se non sei sicuro di un URL, omettilo."""


# ─── AGENTE ───────────────────────────────────────────────────────────────────

class SCOUT007:
    """Agente esploratore AI & social intelligence."""

    def __init__(self, llm_fn: LLMFn | None = None):
        self._llm = llm_fn
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── CERCA TREND ───────────────────────────────────────────────────────────

    def cerca_trend(self, tema: str, canali: list[str] | None = None) -> list[ToolAI]:
        """Cerca tool/video AI virali su un tema specifico."""
        canali_str = ", ".join(canali) if canali else "Instagram, TikTok, YouTube, Twitter/X, web"

        prompt = f"""Tema: "{tema}"
Canali da esplorare: {canali_str}

Identifica 5 tool AI o video/creator virali su questo tema.
Per ciascuno rispondi con questo formato esatto:

TOOL 1:
NOME: [nome del tool/creator/video]
CATEGORIA: [agente|interfaccia|api|video-tool|no-code|altro]
CANALE: [instagram|tiktok|youtube|twitter|web|altro]
URL: [url se conosciuto, altrimenti lascia vuoto]
DESCRIZIONE: [1-2 frasi cosa fa]
PUNTI FORZA: [punto1 | punto2 | punto3]
PUNTI DEBOLI: [punto1 | punto2]
VIRALITA: [alta|media|bassa|sconosciuta]
SDQ1 RILEVANTE: [si|no]
NOTE SDQ1: [come si confronta o potrebbe integrarsi con SDQ-1, 1 frase]

TOOL 2:
[stesso formato]
"""
        if not self._llm:
            return self._fallback_trend(tema)

        testo = self._llm(SISTEMA_TREND, prompt)
        risultati = self._parse_trend(tema, testo)
        self._salva("trend", tema, [r.to_dict() for r in risultati])
        return risultati

    # ── VALUTA SOLUZIONE ──────────────────────────────────────────────────────

    def valuta_soluzione(self, nome: str, url: str = "", contesto: str = "") -> ValutazioneSoluzione:
        """Valutazione tecnica completa di un tool o soluzione AI."""
        riferimento = f"{nome} ({url})" if url else nome
        contesto_str = f"\nContesto aggiuntivo: {contesto}" if contesto else ""

        prompt = f"""Valuta questa soluzione AI: {riferimento}{contesto_str}

Analisi richiesta:
1. Cosa fa esattamente (funzionalità core)
2. Qualità tecnica dell'implementazione
3. UX e accessibilità
4. Originalità rispetto al mercato
5. Posizionamento di mercato e potenziale
6. Confronto con SDQ-1 (pipeline 6 agenti, SAR 11 livelli, output creativi: musica/immagini/video/testi/cucina/codice)

Rispondi con questo formato esatto:

PUNTEGGIO TECNICO: [0-10]
PUNTEGGIO UX: [0-10]
PUNTEGGIO ORIGINALITA: [0-10]
PUNTEGGIO MERCATO: [0-10]
VERDICT: [ECCELLENTE|BUONO|NELLA_MEDIA|DEBOLE|IRRILEVANTE]
COSA FA BENE: [punto1 | punto2 | punto3]
COSA MANCA: [punto1 | punto2 | punto3]
POSIZIONE VS SDQ1: [superiore|pari|inferiore|diverso]
OPPORTUNITA INTEGRAZIONE: [come potrebbe integrarsi o ispirarsi a SDQ-1, 1-2 frasi]
RACCOMANDAZIONE: [1-2 frasi azione concreta per Claudio]
"""
        if not self._llm:
            return self._fallback_valutazione(nome, url)

        testo = self._llm(SISTEMA_SCOUT, prompt)
        risultato = self._parse_valutazione(nome, url, testo)
        self._salva("valutazione", nome, risultato.to_dict())
        return risultato

    # ── REPORT SETTIMANALE ────────────────────────────────────────────────────

    def report_settimanale(self) -> str:
        """Genera un report sullo stato dell'arte degli agenti AI."""
        prompt = """Genera un report settimanale sullo stato degli agenti AI al 2026.
Struttura:
1. TOP 3 tool AI più discussi questa settimana (con URL se noti)
2. TOP 3 creator/account che fanno contenuti AI virali (Instagram, TikTok, YouTube)
3. Trend emergente che potrebbe impattare SDQ-1 nei prossimi 30 giorni
4. Una opportunità concreta per Raffaello Creative Studio

Sii specifico. Nomi reali. No generalità."""

        if not self._llm:
            return "LLM non disponibile — fornisci llm_fn per report settimanale."

        testo = self._llm(SISTEMA_SCOUT, prompt)
        self._salva("report", "settimanale", {"testo": testo})
        return testo

    # ── CONFRONTA CON SDQ1 ────────────────────────────────────────────────────

    def confronta_con_sdq1(self, nome_tool: str, funzionalita: str) -> str:
        """Confronto diretto tra un tool esterno e le capacità SDQ-1."""
        prompt = f"""Tool esterno: {nome_tool}
Funzionalità descritta: {funzionalita}

SDQ-1 ha: pipeline 6 agenti (RAFFA-001→DECOMP-005→MEMO-002→SENTIN-004→GEN-006→WAVE-003),
SAR 11 livelli con Contraddittore, Sognatore, Predittivo, Radar Emozionale,
output in: musica, immagini, video, testi, cucina, AI & codice.

Analisi in 3 punti:
1. Dove {nome_tool} è più forte di SDQ-1
2. Dove SDQ-1 è più forte di {nome_tool}
3. Come SDQ-1 potrebbe integrare la cosa migliore di {nome_tool}"""

        if not self._llm:
            return "LLM non disponibile."
        return self._llm(SISTEMA_SCOUT, prompt)

    # ── PARSE ─────────────────────────────────────────────────────────────────

    def _parse_trend(self, tema: str, testo: str) -> list[ToolAI]:
        risultati = []
        blocchi = testo.split("TOOL ")
        for blocco in blocchi[1:]:
            try:
                def get(key):
                    for line in blocco.split("\n"):
                        if line.startswith(f"{key}:"):
                            return line.split(":", 1)[1].strip()
                    return ""

                punti_forza = [p.strip() for p in get("PUNTI FORZA").split("|") if p.strip()]
                punti_deboli = [p.strip() for p in get("PUNTI DEBOLI").split("|") if p.strip()]
                rilevante = get("SDQ1 RILEVANTE").lower() == "si"

                risultati.append(ToolAI(
                    nome=get("NOME"),
                    categoria=get("CATEGORIA").lower(),
                    canale_scoperta=get("CANALE").lower(),
                    descrizione=get("DESCRIZIONE"),
                    punti_forza=punti_forza,
                    punti_deboli=punti_deboli,
                    url=get("URL"),
                    viralita=get("VIRALITA").lower(),
                    rilevante_per_sdq1=rilevante,
                    note_confronto=get("NOTE SDQ1"),
                ))
            except Exception:
                continue
        return risultati

    def _parse_valutazione(self, nome: str, url: str, testo: str) -> ValutazioneSoluzione:
        import re

        def get(key):
            # Cerca sia "KEY: valore" che "**KEY:** valore" (markdown Gemini)
            pattern = rf"(?:\*\*)?{re.escape(key)}(?:\*\*)?:?\*?\*?\s*(.+)"
            for line in testo.split("\n"):
                m = re.search(pattern, line, re.IGNORECASE)
                if m:
                    val = m.group(1).strip().strip("*").strip()
                    if val:
                        return val
            return ""

        def get_float(key, default=5.0):
            raw = get(key)
            try:
                return float(re.search(r"\d+(?:\.\d+)?", raw).group())
            except (ValueError, TypeError, AttributeError):
                return default

        def get_lista(key):
            # Cerca il blocco bullet dopo la chiave
            in_block = False
            items = []
            raw_inline = get(key)
            if raw_inline and "|" in raw_inline:
                return [p.strip() for p in raw_inline.split("|") if p.strip()]
            # bullet points su righe separate
            for line in testo.split("\n"):
                if re.search(rf"(?:\*\*)?{re.escape(key)}(?:\*\*)?", line, re.IGNORECASE):
                    in_block = True
                    continue
                if in_block:
                    stripped = line.strip().lstrip("*-•·").strip()
                    if stripped and not re.match(r"[A-Z ]{4,}:", stripped):
                        items.append(stripped)
                    elif not stripped:
                        continue
                    else:
                        break
            return items[:4] if items else [raw_inline] if raw_inline else []

        return ValutazioneSoluzione(
            nome=nome,
            url=url,
            punteggio_tecnico=get_float("PUNTEGGIO TECNICO"),
            punteggio_ux=get_float("PUNTEGGIO UX"),
            punteggio_originalita=get_float("PUNTEGGIO ORIGINALITA"),
            punteggio_mercato=get_float("PUNTEGGIO MERCATO"),
            verdict=get("VERDICT"),
            cosa_fa_bene=get_lista("COSA FA BENE"),
            cosa_manca=get_lista("COSA MANCA"),
            posizione_vs_sdq1=get("POSIZIONE VS SDQ1"),
            opportunita_integrazione=get("OPPORTUNITA INTEGRAZIONE"),
            raccomandazione=get("RACCOMANDAZIONE"),
        )

    # ── FALLBACK (senza LLM) ──────────────────────────────────────────────────

    def _fallback_trend(self, tema: str) -> list[ToolAI]:
        return [ToolAI(
            nome=f"[LLM non disponibile — ricerca '{tema}' non eseguita]",
            categoria="altro",
            canale_scoperta="altro",
            descrizione="Fornisci llm_fn per ricerca reale.",
            punti_forza=[],
            punti_deboli=[],
        )]

    def _fallback_valutazione(self, nome: str, url: str) -> ValutazioneSoluzione:
        return ValutazioneSoluzione(
            nome=nome, url=url,
            punteggio_tecnico=0, punteggio_ux=0,
            punteggio_originalita=0, punteggio_mercato=0,
            verdict="IRRILEVANTE",
            cosa_fa_bene=[], cosa_manca=[],
            posizione_vs_sdq1="sconosciuto",
            opportunita_integrazione="LLM non disponibile.",
            raccomandazione="Fornisci llm_fn per valutazione reale.",
        )

    # ── SALVA ─────────────────────────────────────────────────────────────────

    def _salva(self, tipo: str, chiave: str, dati: Any) -> None:
        ts = int(time.time())
        slug = chiave.lower().replace(" ", "_")[:30]
        nome_file = OUTPUT_DIR / f"{tipo}_{slug}_{ts}.json"
        with open(nome_file, "w", encoding="utf-8") as f:
            json.dump({"tipo": tipo, "chiave": chiave, "dati": dati, "timestamp": ts}, f, ensure_ascii=False, indent=2)


# ─── CLI ──────────────────────────────────────────────────────────────────────

def _crea_llm():
    """Crea llm_fn Gemini da .env."""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k] = v
    try:
        from google import genai as gai
        from google.genai import types
        client = gai.Client(api_key=os.environ["GOOGLE_API_KEY"])

        def llm_fn(system: str, prompt: str) -> str:
            full = (system + "\n\n" + prompt) if system else prompt
            cfg = types.GenerateContentConfig(
                max_output_tokens=4096,
                temperature=0.6,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            )
            r = client.models.generate_content(model="gemini-2.5-flash", contents=full, config=cfg)
            return r.text

        return llm_fn
    except Exception as e:
        print(f"[SCOUT-007] LLM non disponibile: {e}")
        return None


def main():
    import sys
    args = sys.argv[1:]
    llm = _crea_llm()
    scout = SCOUT007(llm)

    if not args or "--help" in args:
        print(__doc__)
        return

    if "--trend" in args:
        idx = args.index("--trend")
        tema = args[idx + 1] if idx + 1 < len(args) else "agenti AI"
        print(f"\n[SCOUT-007] Ricerca trend: {tema}\n")
        risultati = scout.cerca_trend(tema)
        for r in risultati:
            print(f"  [{r.viralita.upper()}] {r.nome} ({r.canale_scoperta})")
            print(f"  {r.descrizione}")
            print(f"  + {' | '.join(r.punti_forza[:2])}")
            if r.rilevante_per_sdq1:
                print(f"  ★ SDQ-1: {r.note_confronto}")
            print()

    elif "--valuta" in args:
        idx = args.index("--valuta")
        nome = args[idx + 1] if idx + 1 < len(args) else "tool sconosciuto"
        url = args[idx + 2] if idx + 2 < len(args) else ""
        print(f"\n[SCOUT-007] Valutazione: {nome}\n")
        v = scout.valuta_soluzione(nome, url)
        media = (v.punteggio_tecnico + v.punteggio_ux + v.punteggio_originalita + v.punteggio_mercato) / 4
        print(f"  VERDICT: {v.verdict}  (media {media:.1f}/10)")
        print(f"  Tecnico: {v.punteggio_tecnico}  UX: {v.punteggio_ux}  Originalità: {v.punteggio_originalita}  Mercato: {v.punteggio_mercato}")
        print(f"  VS SDQ-1: {v.posizione_vs_sdq1}")
        print(f"  Fa bene: {' | '.join(v.cosa_fa_bene)}")
        print(f"  Manca:   {' | '.join(v.cosa_manca)}")
        print(f"  Opportunità: {v.opportunita_integrazione}")
        print(f"  → {v.raccomandazione}")

    elif "--report" in args:
        print("\n[SCOUT-007] Report settimanale AI\n")
        print(scout.report_settimanale())

    else:
        # menu interattivo
        print("\n[SCOUT-007] Cosa vuoi esplorare?")
        print("  1. Trend AI su tema specifico")
        print("  2. Valuta una soluzione AI")
        print("  3. Report settimanale")
        scelta = input("\n> ").strip()
        if scelta == "1":
            tema = input("Tema: ").strip() or "agenti AI"
            for r in scout.cerca_trend(tema):
                print(f"\n{r.nome} [{r.viralita}] — {r.descrizione}")
        elif scelta == "2":
            nome = input("Nome tool: ").strip()
            url = input("URL (opzionale): ").strip()
            v = scout.valuta_soluzione(nome, url)
            print(f"\nVerdict: {v.verdict}")
            print(f"→ {v.raccomandazione}")
        elif scelta == "3":
            print(scout.report_settimanale())


if __name__ == "__main__":
    main()
