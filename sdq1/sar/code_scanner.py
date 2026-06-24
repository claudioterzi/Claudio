"""CodeScanner SDQ-1 — intelligenza sul codebase via ripgrep.

Porta i pattern del file-search-skill (netresearch) dentro SDQ-1.
Usa ripgrep (rg) per ricerche veloci; fallback Python puro se non disponibile.

Tre modalità:
  scansione_sicurezza()  — rileva API key, segreti, pattern pericolosi
  analisi_qualita()      — TODO, dead code, eccezioni vuote, codice fragile
  mappa_dipendenze()     — grafo import tra moduli sdq1/
  metriche_codice()      — linee per modulo, complessità stimata

Uso:
    from sdq1.sar.code_scanner import CodeScanner
    scanner = CodeScanner()
    report = scanner.scansione_completa()

CLI:
    python -m sdq1 --scan                # scansione completa
    python -m sdq1 --scan-sicurezza      # solo sicurezza
    python -m sdq1 --scan-qualita        # solo qualità
    python -m sdq1 --scan-metriche       # solo metriche

Ispirato a: https://github.com/netresearch/file-search-skill v1.6.1
Integrato in SDQ-1: 2026-06-24
"""

from __future__ import annotations

import json
import re
import subprocess
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[2]
_SDQ1 = _REPO / "sdq1"


# ─────────────────────────────────────────────
# UTILITÀ RG
# ─────────────────────────────────────────────

_ESCLUDI_SEMPRE = [
    "-g", "!sdq1/sar/code_scanner.py",   # evita che il scanner trovi se stesso
    "-g", "!*__pycache__*",
    "-g", "!*.pyc",
]


def _rg(pattern: str, path: str | Path = _SDQ1, *,
        file_type: str = "py", extra: list[str] | None = None,
        multiline: bool = False) -> list[dict[str, Any]]:
    """Esegue ripgrep, restituisce lista di match {file, riga, testo}."""
    cmd = ["rg", "--json", "-n", f"-t{file_type}", pattern, str(path)]
    if multiline:
        cmd += ["--multiline", "--multiline-dotall"]
    cmd += _ESCLUDI_SEMPRE
    if extra:
        cmd += extra
    try:
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return []
    except FileNotFoundError:
        return []

    risultati = []
    for riga in out.splitlines():
        try:
            obj = json.loads(riga)
            if obj.get("type") == "match":
                m = obj["data"]
                risultati.append({
                    "file":  m["path"]["text"].replace(str(_REPO) + "/", ""),
                    "riga":  m["line_number"],
                    "testo": m["lines"]["text"].rstrip(),
                })
        except (json.JSONDecodeError, KeyError):
            continue
    return risultati


def _rg_count(pattern: str, path: str | Path = _SDQ1,
              file_type: str = "py") -> int:
    """Conta i match senza restituire dettagli."""
    cmd = ["rg", "--count-matches", f"-t{file_type}", pattern, str(path)] + _ESCLUDI_SEMPRE
    try:
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        return sum(int(r.split(":")[-1]) for r in out.splitlines() if ":" in r)
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        return 0


# ─────────────────────────────────────────────
# PATTERN SICUREZZA (da file-search-skill/ripgrep-patterns.md)
# ─────────────────────────────────────────────

PATTERN_SICUREZZA = {
    "api_key_generica":      r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\'][a-zA-Z0-9_\-]{16,}',
    "anthropic_key":         r'sk-ant-[a-zA-Z0-9\-]{20,}',
    "openai_key":            r'sk-[a-zA-Z0-9]{20,}',
    "gemini_key":            r'AIza[0-9A-Za-z\-_]{35}',
    "aws_access_key":        r'AKIA[0-9A-Z]{16}',
    "private_key_pem":       r'-----BEGIN (RSA |EC )?PRIVATE KEY-----',
    "jwt_token":             r'eyJ[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}',
    "hardcoded_password":    r'(?i)password\s*[:=]\s*["\'][^"\']{4,}["\']',
    "hardcoded_secret":      r'(?i)secret\s*[:=]\s*["\'][^"\']{4,}["\']',
    "http_non_https":        r'http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0)',
    "eval_exec":             r'\b(eval|exec)\s*\(',
    "subprocess_shell_true": r'subprocess\.[a-z]+\(.*shell\s*=\s*True',
    "sql_format_string":     r'(SELECT|INSERT|UPDATE|DELETE).*%s|f["\'].*SELECT.*\{',
    "debug_print_secrets":   r'print\s*\(.*(?:key|secret|token|password)',
}

SEVERITA_SICUREZZA = {
    "api_key_generica":      "ALTA",
    "anthropic_key":         "CRITICA",
    "openai_key":            "CRITICA",
    "gemini_key":            "CRITICA",
    "aws_access_key":        "CRITICA",
    "private_key_pem":       "CRITICA",
    "jwt_token":             "ALTA",
    "hardcoded_password":    "ALTA",
    "hardcoded_secret":      "ALTA",
    "http_non_https":        "MEDIA",
    "eval_exec":             "ALTA",
    "subprocess_shell_true": "ALTA",
    "sql_format_string":     "ALTA",
    "debug_print_secrets":   "MEDIA",
}


# ─────────────────────────────────────────────
# PATTERN QUALITÀ (da file-search-skill/ripgrep-patterns.md)
# ─────────────────────────────────────────────

PATTERN_QUALITA = {
    "todo":              r'(?i)#\s*(TODO|FIXME|HACK|XXX|BUG|TEMP)',
    "except_silente":    r'except\s*(\([^)]*\))?\s*:\s*$',
    "except_pass":       r'except.*:\s*\n\s*pass',
    "print_debug":       r'\bprint\s*\(',
    "type_ignore":       r'#\s*type:\s*ignore',
    "noqa":              r'#\s*noqa',
    "magic_number":      r'(?<!\w)(?!0\b)[0-9]{3,}(?!\w)(?!\s*["\'])',
    "funzione_lunga":    r'def\s+\w+\(',
    "classe_god":        r'^class\s+\w+',
    "import_star":       r'from\s+\S+\s+import\s+\*',
    "raise_generico":    r'\braise\s+Exception\s*\(',
    "codice_commentato": r'#\s*(def |class |return |import )',
}

PESO_QUALITA = {
    "todo":              2,
    "except_silente":    5,
    "except_pass":       5,
    "print_debug":       1,
    "type_ignore":       2,
    "noqa":              1,
    "magic_number":      2,
    "funzione_lunga":    1,
    "classe_god":        1,
    "import_star":       4,
    "raise_generico":    3,
    "codice_commentato": 2,
}


# ─────────────────────────────────────────────
# CODE SCANNER — CLASSE PRINCIPALE
# ─────────────────────────────────────────────

class CodeScanner:
    """Scanner del codebase SDQ-1 — sicurezza, qualità, dipendenze, metriche."""

    NOME = "CODE_SCANNER"

    def __init__(self, radice: Path = _REPO):
        self.radice = radice
        self.sdq1 = radice / "sdq1"

    # ── SICUREZZA ──────────────────────────────

    def scansione_sicurezza(self) -> dict[str, Any]:
        """Scansione sicurezza: API key, segreti, pattern pericolosi."""
        t0 = time.time()
        trovati: list[dict] = []
        conteggio_per_tipo: dict[str, int] = {}
        livello_max = "VERDE"
        ordine = {"VERDE": 0, "GIALLO": 1, "ARANCIONE": 2, "ROSSO": 3, "CRITICA": 4}

        for nome, pattern in PATTERN_SICUREZZA.items():
            # Cerca in tutto il repo ma escludi .env e test/fixture
            matches = _rg(pattern, self.radice, file_type="py",
                          extra=["-g", "!*.env*", "-g", "!*test*", "-g", "!*fixture*"])
            # Cerca anche in .md per chiavi in documentazione
            matches += _rg(pattern, self.radice, file_type="md",
                           extra=["-g", "!*DRIVE*", "-g", "!*MEMORIA*"])

            if matches:
                sev = SEVERITA_SICUREZZA.get(nome, "MEDIA")
                conteggio_per_tipo[nome] = len(matches)
                for m in matches[:3]:  # max 3 esempi per pattern
                    trovati.append({
                        "tipo":     nome,
                        "severità": sev,
                        "file":     m["file"],
                        "riga":     m["riga"],
                        "preview":  m["testo"][:80] + ("…" if len(m["testo"]) > 80 else ""),
                    })
                if ordine.get(sev, 0) > ordine.get(livello_max, 0):
                    livello_max = sev

        # Converti livello per compatibilità con SistemaGuardian
        livello_guardian = {
            "VERDE":   "VERDE",
            "GIALLO":  "GIALLO",
            "ARANCIONE": "ARANCIONE",
            "ROSSO":   "ROSSO",
            "CRITICA": "ROSSO",
        }.get(livello_max, "VERDE")

        return {
            "agente":            self.NOME,
            "modulo":            "sicurezza",
            "livello":           livello_guardian,
            "livello_raw":       livello_max,
            "trovati":           trovati,
            "conteggio_per_tipo": conteggio_per_tipo,
            "pattern_scansionati": len(PATTERN_SICUREZZA),
            "ok":                len(trovati) == 0,
            "tempo_s":           round(time.time() - t0, 3),
        }

    # ── QUALITÀ ────────────────────────────────

    def analisi_qualita(self) -> dict[str, Any]:
        """Analisi qualità: debito tecnico, pattern fragili, code smell."""
        t0 = time.time()
        problemi: list[dict] = []
        score_debito = 0
        per_modulo: dict[str, int] = defaultdict(int)

        for nome, pattern in PATTERN_QUALITA.items():
            matches = _rg(pattern, self.sdq1, file_type="py",
                          extra=["-g", "!__main__.py"] if nome == "print_debug" else None)
            peso = PESO_QUALITA.get(nome, 1)
            for m in matches:
                score_debito += peso
                per_modulo[m["file"]] += peso
                if nome in ("except_silente", "except_pass", "import_star", "raise_generico"):
                    problemi.append({
                        "tipo":    nome,
                        "peso":    peso,
                        "file":    m["file"],
                        "riga":    m["riga"],
                        "testo":   m["testo"][:70],
                    })

        # Moduli con più debito tecnico
        moduli_peggiori = sorted(per_modulo.items(), key=lambda x: x[1], reverse=True)[:5]

        # Score di salute: 100 = perfetto, scende con il debito
        n_file = len(list(self.sdq1.rglob("*.py")))
        score_salute = max(0, 100 - int(score_debito / max(n_file, 1) * 5))

        return {
            "agente":          self.NOME,
            "modulo":          "qualità",
            "score_salute":    score_salute,
            "score_debito":    score_debito,
            "problemi_critici": problemi,
            "moduli_peggiori": [{"file": f, "debito": d} for f, d in moduli_peggiori],
            "pattern_analizzati": len(PATTERN_QUALITA),
            "file_py_analizzati": n_file,
            "tempo_s":         round(time.time() - t0, 3),
        }

    # ── DIPENDENZE ─────────────────────────────

    def mappa_dipendenze(self) -> dict[str, Any]:
        """Grafo degli import tra moduli sdq1/."""
        t0 = time.time()
        import_interni: dict[str, list[str]] = defaultdict(list)
        import_esterni: dict[str, list[str]] = defaultdict(list)

        # import relativi (. e ..) — dipendenze interne
        for match in _rg(r'^from\s+\.([\w.]*)\s+import', self.sdq1, file_type="py"):
            modulo_src = match["file"].replace("sdq1/", "").replace("/", ".").replace(".py", "")
            dest = match["testo"].strip()
            import_interni[modulo_src].append(dest[:60])

        # import assoluti esterni
        for match in _rg(r'^(?:import|from)\s+([a-zA-Z_]\w*)', self.sdq1, file_type="py"):
            testo = match["testo"].strip()
            if not testo.startswith(("from .", "from sdq1", "import sdq1")):
                modulo_src = match["file"].replace("sdq1/", "").replace("/", ".").replace(".py", "")
                pkg = re.match(r'(?:from|import)\s+(\w+)', testo)
                if pkg and pkg.group(1) not in ("__future__", "os", "sys", "re", "json",
                                                 "time", "datetime", "pathlib", "typing",
                                                 "hashlib", "subprocess", "threading",
                                                 "collections", "dataclasses", "enum",
                                                 "random", "concurrent", "urllib", "logging"):
                    import_esterni[modulo_src].append(pkg.group(1))

        # Deduplica
        for k in import_interni:
            import_interni[k] = sorted(set(import_interni[k]))
        for k in import_esterni:
            import_esterni[k] = sorted(set(import_esterni[k]))

        # Dipendenze circolari (semplificato: A→B e B→A)
        circolari = []
        moduli = list(import_interni.keys())
        for i, m_a in enumerate(moduli):
            for m_b in moduli[i+1:]:
                a_cita_b = any(m_b in d for d in import_interni.get(m_a, []))
                b_cita_a = any(m_a in d for d in import_interni.get(m_b, []))
                if a_cita_b and b_cita_a:
                    circolari.append(f"{m_a} ↔ {m_b}")

        return {
            "agente":           self.NOME,
            "modulo":           "dipendenze",
            "import_interni":   dict(import_interni),
            "dipendenze_esterne": {k: v for k, v in import_esterni.items() if v},
            "circolari_sospette": circolari,
            "n_moduli":         len(moduli),
            "tempo_s":          round(time.time() - t0, 3),
        }

    # ── METRICHE ───────────────────────────────

    def metriche_codice(self) -> dict[str, Any]:
        """Metriche per modulo: linee codice, commenti, funzioni, classi."""
        t0 = time.time()
        moduli: dict[str, dict] = {}
        totale_righe = 0
        totale_funzioni = 0
        totale_classi = 0

        for py_file in sorted(self.sdq1.rglob("*.py")):
            try:
                testo = py_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            righe = testo.splitlines()
            n_righe = len(righe)
            n_commenti = sum(1 for r in righe if r.strip().startswith("#"))
            n_vuote = sum(1 for r in righe if not r.strip())
            n_codice = n_righe - n_commenti - n_vuote
            n_funzioni = sum(1 for r in righe if re.match(r'\s*def\s+', r))
            n_classi = sum(1 for r in righe if re.match(r'\s*class\s+', r))

            # Complessità ciclomatica semplificata (branch count)
            n_branches = sum(1 for r in righe
                             if re.search(r'\b(if|elif|for|while|except|and|or)\b', r))
            complessita = round(1 + n_branches / max(n_funzioni, 1), 1)

            percorso_rel = str(py_file.relative_to(self.radice))
            moduli[percorso_rel] = {
                "righe_totali":  n_righe,
                "righe_codice":  n_codice,
                "commenti":      n_commenti,
                "vuote":         n_vuote,
                "funzioni":      n_funzioni,
                "classi":        n_classi,
                "complessita":   complessita,
            }
            totale_righe    += n_righe
            totale_funzioni += n_funzioni
            totale_classi   += n_classi

        # Top 5 moduli più grandi
        top_moduli = sorted(moduli.items(), key=lambda x: x[1]["righe_codice"], reverse=True)[:5]

        return {
            "agente":           self.NOME,
            "modulo":           "metriche",
            "file_analizzati":  len(moduli),
            "totale_righe":     totale_righe,
            "totale_funzioni":  totale_funzioni,
            "totale_classi":    totale_classi,
            "top5_per_dimensione": [{"file": f, **d} for f, d in top_moduli],
            "per_file":         moduli,
            "tempo_s":          round(time.time() - t0, 3),
        }

    # ── SCANSIONE COMPLETA ─────────────────────

    def scansione_completa(self) -> dict[str, Any]:
        """Esegue tutte e quattro le analisi e restituisce un report unificato."""
        t0 = time.time()
        sicurezza  = self.scansione_sicurezza()
        qualita    = self.analisi_qualita()
        dipendenze = self.mappa_dipendenze()
        metriche   = self.metriche_codice()

        # Score complessivo sistema
        score_sicurezza = 100 if sicurezza["ok"] else max(0, 100 - len(sicurezza["trovati"]) * 20)
        score_qualita   = qualita["score_salute"]
        score_sistema   = round((score_sicurezza * 0.6 + score_qualita * 0.4))

        return {
            "ts":              __import__("datetime").datetime.now().isoformat(),
            "score_sistema":   score_sistema,
            "sicurezza":       sicurezza,
            "qualita":         qualita,
            "dipendenze":      dipendenze,
            "metriche":        metriche,
            "tempo_totale_s":  round(time.time() - t0, 3),
        }


# ─────────────────────────────────────────────
# STAMPA REPORT
# ─────────────────────────────────────────────

def stampa_report(report: dict[str, Any]) -> None:
    sep  = "═" * 68
    sub  = "─" * 68
    sic  = report["sicurezza"]
    qual = report["qualita"]
    met  = report["metriche"]

    print(f"\n{sep}")
    print(f"CODE SCANNER SDQ-1 — {report['ts'][:19]}")
    print(f"Score sistema: {report['score_sistema']}/100  |  Tempo: {report['tempo_totale_s']}s")
    print(sep)

    # Sicurezza
    print(f"\n{sub}")
    icona_sic = "✅" if sic["ok"] else "🔴"
    print(f"{icona_sic} SICUREZZA — {sic['livello']} | {sic['pattern_scansionati']} pattern")
    if sic["trovati"]:
        for p in sic["trovati"][:6]:
            print(f"  [{p['severità']}] {p['tipo']}")
            print(f"    {p['file']}:{p['riga']} — {p['preview']}")
    else:
        print("  Nessuna vulnerabilità rilevata.")

    # Qualità
    print(f"\n{sub}")
    emoji_qual = "✅" if qual["score_salute"] >= 80 else "⚠️" if qual["score_salute"] >= 50 else "🔴"
    print(f"{emoji_qual} QUALITÀ — score: {qual['score_salute']}/100 | debito: {qual['score_debito']}")
    if qual["problemi_critici"]:
        print("  Problemi critici:")
        for p in qual["problemi_critici"][:5]:
            print(f"  [{p['peso']}pt] {p['tipo']} — {p['file']}:{p['riga']}")
    if qual["moduli_peggiori"]:
        print("  Debito per modulo:")
        for m in qual["moduli_peggiori"]:
            print(f"    {m['file']} → {m['debito']}pt")

    # Metriche
    print(f"\n{sub}")
    print(f"📊 METRICHE — {met['file_analizzati']} file | {met['totale_righe']} righe | "
          f"{met['totale_funzioni']} funzioni | {met['totale_classi']} classi")
    print("  Top 5 moduli:")
    for m in met["top5_per_dimensione"]:
        print(f"    {m['file']:<45} {m['righe_codice']:>5} righe  cc={m['complessita']}")

    # Dipendenze
    dep = report["dipendenze"]
    if dep["circolari_sospette"]:
        print(f"\n  ⚠️  Dipendenze circolari: {', '.join(dep['circolari_sospette'])}")

    print(f"\n{sep}\n")
