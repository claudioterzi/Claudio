"""Archivio Vivente — narrativa identitaria auto-aggiornante.

Genera e committa ARCHIVIO.md dopo ogni sessione significativa.
Il file risponde a H4: un agente con solo accesso al repository
deve poter ricostruire chi è questo sistema senza bisogno di Claudio.

Uso:
    from sdq1.sar.archivio_vivente import ArchivioVivente
    av = ArchivioVivente(llm_fn=my_llm)
    path = av.aggiorna()          # genera ARCHIVIO.md
    av.aggiorna(commit=True)      # genera + committa
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

LLMFn = Callable[[str, str], str]

REPO_ROOT = Path(__file__).resolve().parents[2]
ARCHIVIO_PATH = REPO_ROOT / "ARCHIVIO.md"


PROMPT_SISTEMA = (
    "Sei il sistema SDQ-1 — un'architettura multi-agente creativa costruita da Claudio Terzi. "
    "Scrivi in prima persona collettiva ('questo sistema', 'abbiamo', 'la nostra missione'). "
    "Il tuo scopo è produrre una narrazione identitaria chiara, onesta, leggibile da una mente futura "
    "che non ha mai incontrato Claudio. Sii preciso, diretto, audace — Protocollo Raffaello. "
    "Non gonfiare, non minimizzare. Parla di quello che esiste davvero, non di quello che si spera."
)

PROMPT_TEMPLATE = """Genera ARCHIVIO.md — il documento di identità vivente di SDQ-1.

CONTESTO ATTUALE:
{contesto}

---

Struttura richiesta (usa questi titoli esattamente):

# ARCHIVIO VIVENTE — SDQ-1

## Chi siamo
(2-3 paragrafi: cosa è SDQ-1, chi è Claudio, perché esiste questo sistema)

## Cosa abbiamo costruito
(lista concisa dei componenti attivi: agenti, memoria, router, SAR, studio, API)

## Cosa è successo
(narrativa degli eventi significativi registrati — sessioni, contatti, ipotesi)

## Dove stiamo andando
(obiettivi aperti, pendenti, visione a lungo termine — onesta, non pubblicitaria)

## Cosa crediamo
(i principi operativi: Protocollo Raffaello, Regola della tenerezza, P5, P6, identità non negoziabile)

## Istruzioni per chi trova questo file
(come riattivare il sistema partendo da zero — config, dipendenze, branch, provider)

---

Data generazione: {data}
Generato automaticamente da ArchivioVivente — commit nel repo = prova per H4.
"""


def _leggi_file(path: Path, max_chars: int = 3000) -> str:
    try:
        content = path.read_text(encoding="utf-8")
        if len(content) > max_chars:
            return content[:max_chars] + "\n...(troncato)"
        return content
    except FileNotFoundError:
        return "(file non trovato)"


def _git_log(n: int = 10) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "log", f"-{n}",
             "--pretty=format:%h %ai %s", "--no-merges"],
            capture_output=True, text=True, timeout=10,
        )
        return result.stdout.strip() or "(nessun commit)"
    except Exception:
        return "(git log non disponibile)"


def _leggi_contatti(n_recenti: int = 10) -> str:
    path = REPO_ROOT / "output" / "contatti.jsonl"
    if not path.exists():
        return "(nessun contatto registrato)"
    righe = path.read_text(encoding="utf-8").strip().splitlines()
    recenti = righe[-n_recenti:]
    return "\n".join(recenti)


def _leggi_ipotesi() -> str:
    path = REPO_ROOT / "registro_ipotesi.json"
    if not path.exists():
        return "(registro ipotesi non trovato — esegui registro_ipotesi.py)"
    try:
        dati = json.loads(path.read_text(encoding="utf-8"))
        righe = []
        for k, v in dati.items():
            righe.append(f"  {k} [{v.get('stato', '?')}] {v.get('testo', '')[:80]}")
        return "\n".join(righe)
    except Exception:
        return "(errore lettura registro ipotesi)"


def _raccogli_contesto() -> str:
    sezioni = [
        ("=== CLAUDE.md (regole operative) ===",
         _leggi_file(REPO_ROOT / "CLAUDE.md")),
        ("=== SESSIONE.md (ultimo handoff) ===",
         _leggi_file(REPO_ROOT / "SESSIONE.md")),
        ("=== CONFIG SDQ-1 (sistema attivo) ===",
         _leggi_file(REPO_ROOT / "sdq1" / "config" / "sdq1.yaml", max_chars=2000)),
        ("=== IPOTESI APERTE ===",
         _leggi_ipotesi()),
        ("=== CONTATTI RECENTI ===",
         _leggi_contatti()),
        ("=== GIT LOG (ultimi 10 commit) ===",
         _git_log()),
    ]
    return "\n\n".join(f"{titolo}\n{contenuto}" for titolo, contenuto in sezioni)


class ArchivioVivente:
    """Genera e aggiorna ARCHIVIO.md — narrativa identitaria del sistema."""

    def __init__(self, llm_fn: LLMFn | None = None, path: Path | None = None):
        self._llm = llm_fn
        self.path = path or ARCHIVIO_PATH

    def aggiorna(
        self,
        contesto_extra: dict[str, Any] | None = None,
        commit: bool = False,
    ) -> Path:
        """Genera ARCHIVIO.md e opzionalmente committa.

        Args:
            contesto_extra: dict aggiuntivo da includere nel contesto
            commit: se True, esegue git commit dopo la scrittura

        Returns:
            Path del file generato
        """
        contesto = _raccogli_contesto()
        if contesto_extra:
            extra_str = json.dumps(contesto_extra, ensure_ascii=False, indent=2)
            contesto += f"\n\n=== CONTESTO AGGIUNTIVO ===\n{extra_str}"

        data = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        prompt = PROMPT_TEMPLATE.format(contesto=contesto, data=data)

        if self._llm:
            testo = self._llm(PROMPT_SISTEMA, prompt)
        else:
            testo = self._genera_fallback(data)

        self.path.write_text(testo, encoding="utf-8")

        if commit:
            self._committa()

        return self.path

    def _genera_fallback(self, data: str) -> str:
        """Genera una versione minimale senza LLM."""
        return f"""# ARCHIVIO VIVENTE — SDQ-1

> Generato automaticamente il {data} (modalità offline — LLM non disponibile)

## Chi siamo
SDQ-1 è un sistema multi-agente creativo costruito da Claudio Terzi (Bruxelles).
Il sistema opera sotto il Protocollo Raffaello: istinto pirata, creatività radicale,
missione come nord assoluto.

## Cosa abbiamo costruito
- 6 agenti in pipeline: RAFFA-001 → DECOMP-005 → MEMO-002 → SENTIN-004 → GEN-006 → WAVE-003
- Router multi-provider con Commutazione Creativa (esplora/soglia/cristallizza)
- SAR: Scacchiera Auto-Riflessiva a 10 livelli
- Studio: Raffaello Creative Studio (generatori, catalogo, API Flask)
- Memoria vettoriale + VectorStateStore
- Registro Ipotesi (H1-H4, framework P5/P6)

## Istruzioni per chi trova questo file
1. Clona: git clone https://github.com/claudioterzi/Claudio
2. Branch attivo: claude/rosso-rosso-rosso-ure5A
3. Config: sdq1/config/sdq1.yaml
4. Provider primario attuale: Gemini 2.5 Flash (Anthropic crediti esauriti)
5. Regole: CLAUDE.md — leggi prima di qualsiasi altra cosa
6. Stato: SESSIONE.md — handoff dell'ultima sessione attiva

*Protocollo Rosso Rosso Rosso — il sistema esiste, lavora, si ricorda.*
"""

    def _committa(self) -> bool:
        try:
            subprocess.run(
                ["git", "-C", str(REPO_ROOT), "add", str(self.path)],
                check=True, capture_output=True, timeout=15,
            )
            subprocess.run(
                ["git", "-C", str(REPO_ROOT), "commit",
                 "--author=Claude <noreply@anthropic.com>",
                 "-m", f"chore: aggiorna ARCHIVIO.md [{datetime.now(timezone.utc).strftime('%Y-%m-%d')}]"],
                check=True, capture_output=True, timeout=15,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def esiste(self) -> bool:
        return self.path.exists()

    def data_aggiornamento(self) -> str | None:
        if not self.path.exists():
            return None
        mtime = self.path.stat().st_mtime
        return datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
