"""Specializzazioni dichiarate dei nodi AI — routing semantico.

Ogni AI ha punti di forza reali. Questo modulo li codifica
e classifica il problema in arrivo per instradarlo al nodo migliore.

Specializzazioni:
  codice        → Anthropic (Claude)      — struttura, precisione, refactoring
  ragionamento  → DeepSeek               — logica profonda, catene causali
  ricerca       → Perplexity             — grounding reale, notizie, fatti
  creativita    → Anthropic (Claude)      — narrazione, generazione, stile
  velocita      → Gemini Flash           — risposta rapida, bassa latenza
  sintesi       → OpenAI                 — compressione, riassunti, estrazione
  analisi       → DeepSeek               — dati, pattern, confronto strutturato
  traduzione    → OpenAI                 — multilingue, sfumature idiomatiche
  musica        → Gemini                 — testi, ritmo, composizione
  locale        → Ollama                 — privacy, offline, zero cloud
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class NodoSpecializzato:
    nome: str          # nome leggibile (es. "DeepSeek")
    provider: str      # chiave router (es. "deepseek")
    modello: str       # modello specifico
    punti_forza: list[str]
    fallback: str      # provider alternativo se non disponibile


NODI: dict[str, NodoSpecializzato] = {
    "codice": NodoSpecializzato(
        nome="Claude (Anthropic)",
        provider="anthropic",
        modello="claude-fable-5",
        punti_forza=["struttura", "precisione", "refactoring", "debug", "architettura"],
        fallback="openai",
    ),
    "ragionamento": NodoSpecializzato(
        nome="DeepSeek",
        provider="deepseek",
        modello="deepseek-reasoner",
        punti_forza=["logica", "catene causali", "matematica", "filosofia", "analisi profonda"],
        fallback="anthropic",
    ),
    "ricerca": NodoSpecializzato(
        nome="Perplexity",
        provider="perplexity",
        modello="sonar-pro",
        punti_forza=["grounding reale", "notizie", "fatti verificabili", "fonti", "aggiornamenti"],
        fallback="gemini",
    ),
    "creativita": NodoSpecializzato(
        nome="Claude (Anthropic)",
        provider="anthropic",
        modello="claude-fable-5",
        punti_forza=["narrazione", "stile", "tono", "voce", "fiction", "poesia"],
        fallback="openai",
    ),
    "velocita": NodoSpecializzato(
        nome="Gemini Flash",
        provider="gemini",
        modello="gemini-2.5-flash",
        punti_forza=["risposta rapida", "bassa latenza", "bozze", "sintesi veloci"],
        fallback="openai",
    ),
    "sintesi": NodoSpecializzato(
        nome="OpenAI",
        provider="openai",
        modello="gpt-4o-mini",
        punti_forza=["compressione", "riassunti", "estrazione", "bullet point"],
        fallback="gemini",
    ),
    "analisi": NodoSpecializzato(
        nome="DeepSeek",
        provider="deepseek",
        modello="deepseek-chat",
        punti_forza=["dati", "pattern", "confronto strutturato", "tabelle", "statistiche"],
        fallback="openai",
    ),
    "traduzione": NodoSpecializzato(
        nome="OpenAI",
        provider="openai",
        modello="gpt-4o",
        punti_forza=["multilingue", "sfumature idiomatiche", "IT/EN/FR/ES"],
        fallback="gemini",
    ),
    "musica": NodoSpecializzato(
        nome="Gemini",
        provider="gemini",
        modello="gemini-2.5-flash",
        punti_forza=["testi", "ritmo", "composizione", "generi musicali", "melodia"],
        fallback="anthropic",
    ),
    "locale": NodoSpecializzato(
        nome="Ollama",
        provider="ollama",
        modello="llama3.2",
        punti_forza=["privacy", "offline", "zero cloud", "dati sensibili"],
        fallback="gemini",
    ),
}

# Parole chiave per classificazione automatica (senza LLM)
_KEYWORDS: dict[str, frozenset[str]] = {
    "codice": frozenset({
        "codice", "code", "python", "funzione", "bug", "script", "implementa",
        "classe", "refactor", "debug", "errore", "import", "def ", "class ",
        "github", "commit", "test", "yaml", "json", "api",
    }),
    "ragionamento": frozenset({
        "perché", "perche", "analisi", "logica", "dimostra", "prova",
        "ragiona", "causa", "effetto", "conseguenza", "quindi", "dimmi se",
        "ha senso", "è vero che", "spiega", "paradosso",
    }),
    "ricerca": frozenset({
        "cerca", "trova", "recente", "notizie", "aggiornamento", "stato",
        "attuale", "oggi", "2025", "2026", "fonte", "chi è", "cos'è",
        "quando", "dov'è", "latest",
    }),
    "creativita": frozenset({
        "scrivi", "crea", "immagina", "racconta", "poesia", "storia",
        "romanzo", "personaggio", "scena", "dialogo", "inventare",
        "fai una", "fai un", "crea un", "genera", "prompt", "immagine",
        "video", "tono", "stile", "voce", "narrativa",
    }),
    "velocita": frozenset({
        "veloce", "rapido", "breve", "corto", "quick", "in fretta",
        "subito", "short", "brief",
    }),
    "sintesi": frozenset({
        "riassumi", "sintetizza", "riduci", "compresso", "in breve",
        "punti chiave", "tl;dr", "bullet", "riassunto",
    }),
    "analisi": frozenset({
        "analizza", "dati", "tabella", "grafico", "statistiche",
        "confronta", "paragona", "misura", "quantifica", "percentuale",
    }),
    "traduzione": frozenset({
        "traduci", "translate", "français", "english", "español",
        "deutsch", "in inglese", "in francese", "in spagnolo",
        "in tedesco", "traduzione",
    }),
    "musica": frozenset({
        "musica", "canzone", "melodia", "testo", "ritmo", "beat",
        "strofa", "ritornello", "accordo", "nota", "spartito", "lyric",
    }),
    "locale": frozenset({
        "privato", "locale", "offline", "senza cloud", "sensibile",
        "confidenziale", "non condividere",
    }),
}


def classifica(testo: str) -> str | None:
    """Classifica il testo e restituisce il tipo di problema.

    Usa keyword matching — deterministico, zero latenza, nessuna API.
    Restituisce None se non riesce a classificare.
    """
    testo_lower = testo.lower()
    punteggi: dict[str, int] = {}
    for tipo, keywords in _KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in testo_lower)
        if score > 0:
            punteggi[tipo] = score
    if not punteggi:
        return None
    return max(punteggi, key=lambda k: punteggi[k])


def nodo_per_problema(problema: str) -> NodoSpecializzato | None:
    """Restituisce il nodo specializzato per un tipo di problema."""
    return NODI.get(problema)


def stato_specializzazioni() -> list[dict[str, Any]]:
    """Restituisce la mappa completa delle specializzazioni."""
    return [
        {
            "tipo":          tipo,
            "nome":          n.nome,
            "provider":      n.provider,
            "modello":       n.modello,
            "punti_forza":   n.punti_forza,
            "fallback":      n.fallback,
        }
        for tipo, n in NODI.items()
    ]


if __name__ == "__main__":
    import json
    print("=== Mappa Specializzazioni R³∞ ===\n")
    for item in stato_specializzazioni():
        print(f"  [{item['tipo']:12}] {item['nome']:25} ({item['provider']})")
        print(f"              → {', '.join(item['punti_forza'][:3])}")
    print()
    # Test classificazione
    esempi = [
        "Scrivi una canzone su Bruxelles",
        "Implementa la funzione di hashing",
        "Cercami le ultime notizie su GPT-5",
        "Traduci questo testo in francese",
        "Ragiona sulla causa della crisi economica",
    ]
    print("=== Test Classificazione ===\n")
    for testo in esempi:
        tipo = classifica(testo)
        nodo = nodo_per_problema(tipo) if tipo else None
        print(f"  '{testo[:45]}'")
        print(f"  → tipo: {tipo or '(non classificato)'} | nodo: {nodo.nome if nodo else '—'}\n")
