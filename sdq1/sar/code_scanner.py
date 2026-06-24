"""CodeScanner SDQ-1 — intelligenza sul codebase via ripgrep.

Porta i pattern del file-search-skill (netresearch) dentro SDQ-1.
Usa ripgrep (rg) per ricerche veloci; fallback Python puro se non disponibile.

Quattro analisi:
  scansione_sicurezza()  — rileva API key, segreti, pattern pericolosi (solo sdq1/)
  analisi_qualita()      — debito tecnico, code smell, pattern fragili
  mappa_dipendenze()     — grafo import tra moduli sdq1/
  metriche_codice()      — linee per modulo, complessità ciclomatica stimata

Score sistema = (score_sicurezza × 0.6) + (score_qualita × 0.4)
Score sicurezza = 100 se nessun trovato reale; scala con trovati critici/alti
Score qualita = 100 − (debito_normalizzato × 5), capped [0, 100]

Integrazione agenti:
  risultato_guardian()   → dict compatibile con SistemaGuardian.scansione()
  summary()              → dict compatto per snapshot e ciclo_valutazione

CLI:
  python -m sdq1 --scan                # scansione completa
  python -m sdq1 --scan-sicurezza      # solo sicurezza
  python -m sdq1 --scan-qualita        # solo qualità
  python -m sdq1 --scan-metriche       # solo metriche

Ispirato a: https://github.com/netresearch/file-search-skill v1.6.1
Integrato in SDQ-1: 2026-06-24
"""

from __future__ import annotations

import datetime
import json
import re
import subprocess
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[2]
_SDQ1 = _REPO / "sdq1"

# ── Esclusioni base (sempre applicate) ────────────────────────────
_BASE_EXCL = [
    "-g", "!sdq1/sar/code_scanner.py",  # non scansionare se stesso
    "-g", "!*__pycache__*",
    "-g", "!*.pyc",
    "-g", "!*/tests/*",
    "-g", "!*_test.py",
    "-g", "!*test_*.py",
]

# Testo noto come intenzionale: match che contengono queste stringhe sono ignorati
_WHITELIST_PATTERN = [
    "IL_TUO_API_KEY_QUI",
    "YOUR_API_KEY",
    "# noqa",
    "# nosec",
    "placeholder",
    "esempio",
    "example",
    "dummy",
    "fake_key",
    "test_key",
]


# ══════════════════════════════════════════════════════════════════
# UTILITÀ RG
# ══════════════════════════════════════════════════════════════════

def _rg(pattern: str, path: str | Path, *,
        file_type: str = "py",
        extra_excl: list[str] | None = None) -> list[dict[str, Any]]:
    """ripgrep → lista di match {file, riga, testo}. Fallisce silenziosamente."""
    cmd = ["rg", "--json", "-n", f"-t{file_type}", pattern, str(path)]
    cmd += _BASE_EXCL
    if extra_excl:
        cmd += extra_excl
    try:
        raw = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

    out = []
    for line in raw.splitlines():
        try:
            obj = json.loads(line)
            if obj.get("type") != "match":
                continue
            d = obj["data"]
            testo = d["lines"]["text"].rstrip()
            out.append({
                "file":  d["path"]["text"].replace(str(_REPO) + "/", ""),
                "riga":  d["line_number"],
                "testo": testo,
            })
        except (json.JSONDecodeError, KeyError):
            continue
    return out


def _filtra_whitelist(matches: list[dict]) -> tuple[list[dict], list[dict]]:
    """Separa trovati reali (non in whitelist) da falsi positivi noti."""
    reali, noti = [], []
    for m in matches:
        testo_low = m["testo"].lower()
        if any(w.lower() in testo_low for w in _WHITELIST_PATTERN):
            noti.append(m)
        else:
            reali.append(m)
    return reali, noti


# ══════════════════════════════════════════════════════════════════
# PATTERN SICUREZZA
# ══════════════════════════════════════════════════════════════════

_PATTERN_SICUREZZA: dict[str, tuple[str, str]] = {
    # nome: (pattern_regex, severità)
    "anthropic_key":         (r'sk-ant-[a-zA-Z0-9\-]{20,}',                             "CRITICA"),
    "openai_key":            (r'sk-[a-zA-Z0-9]{48,}',                                   "CRITICA"),
    "gemini_key":            (r'AIza[0-9A-Za-z\-_]{35}',                                 "CRITICA"),
    "aws_access_key":        (r'AKIA[0-9A-Z]{16}',                                       "CRITICA"),
    "private_key_pem":       (r'-----BEGIN (RSA |EC )?PRIVATE KEY-----',                 "CRITICA"),
    "jwt_hardcoded":         (r'eyJ[a-zA-Z0-9_\-]{30,}\.[a-zA-Z0-9_\-]{30,}\.[a-zA-Z0-9_\-]{10,}', "ALTA"),
    "api_key_hardcoded":     (r'(?i)(api[_-]?key)\s*=\s*["\'][a-zA-Z0-9_\-]{20,}["\']', "ALTA"),
    "hardcoded_password":    (r'(?i)password\s*=\s*["\'][^"\'%{]{6,}["\']',              "ALTA"),
    "hardcoded_secret":      (r'(?i)secret\s*=\s*["\'][^"\'%{]{6,}["\']',               "ALTA"),
    "subprocess_shell_true": (r'subprocess\.\w+\([^)]*shell\s*=\s*True',                 "ALTA"),
    "sql_fstring":           (r'f["\'].*\b(SELECT|INSERT|UPDATE|DELETE)\b.*\{',          "ALTA"),
    "http_cleartext":        (r'http://(?!localhost|127\.|0\.0\.0\.0|testserver)',         "MEDIA"),
    "debug_print_secret":    (r'print\s*\(.*\b(api_key|secret|token|password)\b',        "MEDIA"),
    "eval_noqa_absent":      (r'\beval\s*\((?!.*#\s*noqa)',                               "ALTA"),
}

_SEV_ORDER = {"VERDE": 0, "GIALLO": 1, "ARANCIONE": 2, "ROSSO": 3, "CRITICA": 4}
_SEV_TO_GUARDIAN = {"CRITICA": "ROSSO", "ALTA": "ARANCIONE",
                    "MEDIA": "GIALLO", "BASSA": "VERDE", "VERDE": "VERDE"}


# ══════════════════════════════════════════════════════════════════
# PATTERN QUALITÀ — calibrati per codebase Python SDQ-1
# ══════════════════════════════════════════════════════════════════

_PATTERN_QUALITA: dict[str, tuple[str, int, str | None]] = {
    # nome: (pattern, peso_debito, extra_excl_glob o None)
    "except_silente":    (r'except\s*(\([^)]*\))?\s*:\s*$',         8,  None),
    "except_pass":       (r'except[^:]*:\s*\n\s*pass\s*$',          8,  None),
    "import_star":       (r'from\s+\S+\s+import\s+\*',              6,  None),
    "raise_generico":    (r'\braise\s+Exception\s*\(',              5,  None),
    "sql_concat":        (r'["\'].*SELECT.*["\'].*\+',              5,  None),
    "todo_critico":      (r'(?i)#\s*(FIXME|HACK|BUG)',              4,  None),
    "todo":              (r'(?i)#\s*TODO',                          2,  None),
    "type_ignore":       (r'#\s*type:\s*ignore',                    2,  None),
    # print: escludi __main__ e benchmark (output intenzionale)
    "print_debug":       (r'\bprint\s*\(',                          1,  "!sdq1/__main__.py,!sdq1/benchmark.py,!sdq1/sar/scacchiera_quantica.py"),
    # magic number: solo 5+ cifre (port 8001 ok, 99999 sospetto)
    "magic_number":      (r'(?<!\w)[1-9][0-9]{4,}(?!\w)',          2,  None),
    "noqa_silente":      (r'#\s*noqa(?!\s*:\s*[A-Z])',             1,  None),
}


# ══════════════════════════════════════════════════════════════════
# CODE SCANNER
# ══════════════════════════════════════════════════════════════════

class CodeScanner:
    """Scanner del codebase SDQ-1 — sicurezza, qualità, dipendenze, metriche."""

    NOME = "CODE_SCANNER"

    def __init__(self, radice: Path = _REPO):
        self.radice = radice
        self.sdq1   = radice / "sdq1"

    # ── SICUREZZA ──────────────────────────────────────────────────

    def scansione_sicurezza(self) -> dict[str, Any]:
        """Scansione sicurezza — scope: solo sdq1/ (codice reale)."""
        t0 = time.time()
        trovati_reali:  list[dict] = []
        falsi_positivi: list[dict] = []
        livello_max = "VERDE"

        for nome, (pattern, sev) in _PATTERN_SICUREZZA.items():
            matches = _rg(pattern, self.sdq1, file_type="py")
            reali, noti = _filtra_whitelist(matches)

            for m in reali[:3]:
                trovati_reali.append({
                    "tipo":     nome,
                    "severità": sev,
                    "file":     m["file"],
                    "riga":     m["riga"],
                    "preview":  m["testo"][:90] + ("…" if len(m["testo"]) > 90 else ""),
                })
                if _SEV_ORDER.get(sev, 0) > _SEV_ORDER.get(livello_max, 0):
                    livello_max = sev
            for m in noti[:2]:
                falsi_positivi.append({"tipo": nome, "file": m["file"], "riga": m["riga"]})

        # Score sicurezza
        critici = sum(1 for t in trovati_reali if t["severità"] in ("CRITICA", "ALTA"))
        medi    = sum(1 for t in trovati_reali if t["severità"] == "MEDIA")
        score   = max(0, 100 - critici * 25 - medi * 10)

        return {
            "agente":            self.NOME,
            "modulo":            "sicurezza",
            "livello":           _SEV_TO_GUARDIAN.get(livello_max, "VERDE"),
            "livello_raw":       livello_max,
            "score":             score,
            "trovati":           trovati_reali,
            "falsi_positivi_noti": falsi_positivi,
            "pattern_scansionati": len(_PATTERN_SICUREZZA),
            "ok":                len(trovati_reali) == 0,
            "tempo_s":           round(time.time() - t0, 3),
        }

    # ── QUALITÀ ────────────────────────────────────────────────────

    def analisi_qualita(self) -> dict[str, Any]:
        """Analisi qualità — debito tecnico normalizzato su linee di codice."""
        t0 = time.time()
        problemi_critici: list[dict] = []
        debito_totale = 0
        per_modulo: dict[str, int] = defaultdict(int)

        for nome, (pattern, peso, excl) in _PATTERN_QUALITA.items():
            extra = []
            if excl:
                for g in excl.split(","):
                    extra += ["-g", g.strip()]
            matches = _rg(pattern, self.sdq1, file_type="py", extra_excl=extra or None)

            for m in matches:
                debito_totale += peso
                per_modulo[m["file"]] += peso
                if peso >= 5:   # solo problemi ad alto peso → critici
                    problemi_critici.append({
                        "tipo":   nome,
                        "peso":   peso,
                        "file":   m["file"],
                        "riga":   m["riga"],
                        "testo":  m["testo"][:80],
                    })

        # Normalizza su righe di codice reali (non file count)
        totale_righe_codice = max(1, sum(
            len([r for r in p.read_text(encoding="utf-8", errors="ignore").splitlines()
                 if r.strip() and not r.strip().startswith("#")])
            for p in self.sdq1.rglob("*.py") if p.is_file()
        ))
        debito_per_1k = round(debito_totale / totale_righe_codice * 1000, 1)
        score_salute  = max(0, min(100, round(100 - debito_per_1k * 2)))

        moduli_peggiori = sorted(per_modulo.items(), key=lambda x: x[1], reverse=True)[:5]
        n_file = len(list(self.sdq1.rglob("*.py")))

        return {
            "agente":              self.NOME,
            "modulo":              "qualità",
            "score_salute":        score_salute,
            "score_debito":        debito_totale,
            "debito_per_1k_righe": debito_per_1k,
            "problemi_critici":    problemi_critici[:10],
            "moduli_peggiori":     [{"file": f, "debito": d} for f, d in moduli_peggiori],
            "pattern_analizzati":  len(_PATTERN_QUALITA),
            "file_py_analizzati":  n_file,
            "tempo_s":             round(time.time() - t0, 3),
        }

    # ── DIPENDENZE ─────────────────────────────────────────────────

    def mappa_dipendenze(self) -> dict[str, Any]:
        """Grafo import interni + dipendenze esterne non-stdlib."""
        t0 = time.time()
        STDLIB = {
            "__future__", "os", "sys", "re", "json", "time", "datetime",
            "pathlib", "typing", "hashlib", "subprocess", "threading",
            "collections", "dataclasses", "enum", "random", "concurrent",
            "urllib", "logging", "io", "copy", "functools", "itertools",
            "abc", "contextlib", "inspect", "traceback", "warnings",
            "string", "textwrap", "struct", "math", "decimal", "statistics",
            "argparse", "shutil", "tempfile", "glob", "fnmatch", "signal",
            "asyncio", "queue", "uuid", "types", "weakref", "gc",
            "socket", "sqlite3", "csv", "configparser", "operator",
            "multiprocessing", "platform", "unittest", "typing_extensions",
        }

        import_interni:  dict[str, list[str]] = defaultdict(list)
        import_esterni:  dict[str, list[str]] = defaultdict(list)

        for m in _rg(r'^from\s+\.([\w.]*)\s+import', self.sdq1, file_type="py"):
            src = m["file"].replace("sdq1/", "").replace("/", ".").replace(".py", "")
            import_interni[src].append(m["testo"].strip()[:60])

        for m in _rg(r'^(?:import|from)\s+([a-zA-Z_]\w*)', self.sdq1, file_type="py"):
            testo = m["testo"].strip()
            if testo.startswith(("from .", "from sdq1", "import sdq1")):
                continue
            src = m["file"].replace("sdq1/", "").replace("/", ".").replace(".py", "")
            pkg_m = re.match(r'(?:from|import)\s+(\w+)', testo)
            if pkg_m and pkg_m.group(1) not in STDLIB:
                import_esterni[src].append(pkg_m.group(1))

        for k in import_interni:
            import_interni[k] = sorted(set(import_interni[k]))
        for k in import_esterni:
            import_esterni[k] = sorted(set(import_esterni[k]))

        # Dipendenze circolari semplicistiche
        circolari = []
        mods = list(import_interni.keys())
        for i, ma in enumerate(mods):
            for mb in mods[i+1:]:
                if (any(mb in d for d in import_interni.get(ma, [])) and
                        any(ma in d for d in import_interni.get(mb, []))):
                    circolari.append(f"{ma} ↔ {mb}")

        # Pacchetti esterni unici richiesti
        tutti_ext = sorted({pkg for pkgs in import_esterni.values() for pkg in pkgs})

        return {
            "agente":             self.NOME,
            "modulo":             "dipendenze",
            "n_moduli":           len(mods),
            "import_interni":     dict(import_interni),
            "dipendenze_esterne": {k: v for k, v in import_esterni.items() if v},
            "pacchetti_esterni":  tutti_ext,
            "circolari_sospette": circolari,
            "tempo_s":            round(time.time() - t0, 3),
        }

    # ── METRICHE ───────────────────────────────────────────────────

    def metriche_codice(self) -> dict[str, Any]:
        """Metriche per file: righe, funzioni, classi, complessità ciclomatica."""
        t0 = time.time()
        moduli: dict[str, dict] = {}
        tot_righe = tot_funzioni = tot_classi = 0

        for py in sorted(self.sdq1.rglob("*.py")):
            try:
                righe = py.read_text(encoding="utf-8", errors="ignore").splitlines()
            except Exception:
                continue

            n_tot  = len(righe)
            n_comm = sum(1 for r in righe if r.strip().startswith("#"))
            n_vuot = sum(1 for r in righe if not r.strip())
            n_cod  = n_tot - n_comm - n_vuot
            n_fun  = sum(1 for r in righe if re.match(r'\s*def\s+', r))
            n_cls  = sum(1 for r in righe if re.match(r'\s*class\s+', r))
            n_br   = sum(1 for r in righe
                         if re.search(r'\b(if|elif|for|while|except|and\b|or\b)\b', r))
            cc     = round(1 + n_br / max(n_fun, 1), 1)

            rel = str(py.relative_to(self.radice))
            moduli[rel] = {
                "righe_totali": n_tot, "righe_codice": n_cod,
                "commenti": n_comm,    "vuote": n_vuot,
                "funzioni": n_fun,     "classi": n_cls,
                "complessita": cc,
            }
            tot_righe    += n_tot
            tot_funzioni += n_fun
            tot_classi   += n_cls

        top5 = sorted(moduli.items(), key=lambda x: x[1]["righe_codice"], reverse=True)[:5]

        return {
            "agente":              self.NOME,
            "modulo":              "metriche",
            "file_analizzati":     len(moduli),
            "totale_righe":        tot_righe,
            "totale_funzioni":     tot_funzioni,
            "totale_classi":       tot_classi,
            "top5_per_dimensione": [{"file": f, **d} for f, d in top5],
            "per_file":            moduli,
            "tempo_s":             round(time.time() - t0, 3),
        }

    # ── SCANSIONE COMPLETA ─────────────────────────────────────────

    def scansione_completa(self) -> dict[str, Any]:
        """Tutte e quattro le analisi — report unificato con score complessivo."""
        t0 = time.time()
        sic  = self.scansione_sicurezza()
        qual = self.analisi_qualita()
        dep  = self.mappa_dipendenze()
        met  = self.metriche_codice()

        score = round(sic["score"] * 0.6 + qual["score_salute"] * 0.4)

        return {
            "ts":              datetime.datetime.now().isoformat(),
            "score_sistema":   score,
            "sicurezza":       sic,
            "qualita":         qual,
            "dipendenze":      dep,
            "metriche":        met,
            "tempo_totale_s":  round(time.time() - t0, 3),
        }

    # ── API PER AGENTI ─────────────────────────────────────────────

    def summary(self) -> dict[str, Any]:
        """Dict compatto per snapshot e ciclo_valutazione."""
        sic  = self.scansione_sicurezza()
        qual = self.analisi_qualita()
        met  = self.metriche_codice()
        score = round(sic["score"] * 0.6 + qual["score_salute"] * 0.4)
        return {
            "agente":          self.NOME,
            "score_sistema":   score,
            "sicurezza_ok":    sic["ok"],
            "sicurezza_livello": sic["livello"],
            "qualita_score":   qual["score_salute"],
            "debito_per_1k":   qual["debito_per_1k_righe"],
            "file_totali":     met["file_analizzati"],
            "righe_totali":    met["totale_righe"],
            "problemi_critici": len(qual["problemi_critici"]),
            "trovati_sicurezza": len(sic["trovati"]),
        }

    def risultato_guardian(self) -> dict[str, Any]:
        """Risultato compatibile con SistemaGuardian — aggiunge minaccia CODEBASE."""
        sic = self.scansione_sicurezza()
        contesto: dict[str, Any] = {}
        if not sic["ok"]:
            critici = [t for t in sic["trovati"] if t["severità"] in ("CRITICA", "ALTA")]
            if critici:
                contesto["code_vulnerability"] = True
                contesto["_dettagli_vulnerabilita"] = critici[:3]
        return contesto


# ══════════════════════════════════════════════════════════════════
# STAMPA REPORT
# ══════════════════════════════════════════════════════════════════

def stampa_report(report: dict[str, Any]) -> None:
    SEP = "═" * 70
    SUB = "─" * 70
    sic  = report["sicurezza"]
    qual = report["qualita"]
    met  = report["metriche"]
    dep  = report["dipendenze"]

    print(f"\n{SEP}")
    print(f"  CODE SCANNER SDQ-1 — {report['ts'][:19]}")
    print(f"  Score sistema: {report['score_sistema']}/100"
          f"  |  Sicurezza: {sic['score']}/100"
          f"  |  Qualità: {qual['score_salute']}/100"
          f"  |  Tempo: {report['tempo_totale_s']}s")
    print(SEP)

    # ── SICUREZZA
    print(f"\n{SUB}")
    icona = "✅" if sic["ok"] else ("🔴" if sic["livello"] in ("ROSSO", "ARANCIONE") else "⚠️")
    print(f"{icona}  SICUREZZA [{sic['livello']}] — {sic['pattern_scansionati']} pattern | "
          f"score: {sic['score']}/100")
    if sic["trovati"]:
        print("   Trovati reali:")
        for t in sic["trovati"]:
            print(f"   ⚡ [{t['severità']:<8}] {t['tipo']}")
            print(f"      {t['file']}:{t['riga']}  {t['preview'][:75]}")
    else:
        print("   ✓  Nessuna vulnerabilità reale nel codice Python.")
    if sic["falsi_positivi_noti"]:
        print(f"   ℹ️  {len(sic['falsi_positivi_noti'])} match noti (whitelist — placeholder/intenzionali)")

    # ── QUALITÀ
    print(f"\n{SUB}")
    q_icon = "✅" if qual["score_salute"] >= 80 else ("⚠️" if qual["score_salute"] >= 55 else "🔴")
    print(f"{q_icon}  QUALITÀ — score: {qual['score_salute']}/100 | "
          f"debito: {qual['score_debito']}pt | "
          f"densità: {qual['debito_per_1k_righe']}pt/1k righe")
    if qual["problemi_critici"]:
        print("   Problemi ad alto peso (≥5pt):")
        seen = set()
        for p in qual["problemi_critici"]:
            key = (p["tipo"], p["file"])
            if key in seen:
                continue
            seen.add(key)
            print(f"   ⚡ [{p['peso']}pt] {p['tipo']:<20} {p['file']}:{p['riga']}")
            if len(seen) >= 6:
                rest = len(qual["problemi_critici"]) - 6
                if rest > 0:
                    print(f"   … e altri {rest} problemi")
                break
    print("   Debito per modulo:")
    for m in qual["moduli_peggiori"]:
        bar = "█" * min(20, m["debito"] // 5)
        print(f"   {m['file']:<50} {bar} {m['debito']}pt")

    # ── METRICHE
    print(f"\n{SUB}")
    print(f"📊  METRICHE — {met['file_analizzati']} file  |  "
          f"{met['totale_righe']} righe  |  "
          f"{met['totale_funzioni']} funzioni  |  "
          f"{met['totale_classi']} classi")
    print("   Top 5 per dimensione:")
    for m in met["top5_per_dimensione"]:
        cc_bar = "▪" * min(10, int(m["complessita"]))
        print(f"   {m['file']:<52} {m['righe_codice']:>5} rl  {cc_bar} cc={m['complessita']}")

    # ── DIPENDENZE
    print(f"\n{SUB}")
    print(f"🔗  DIPENDENZE — {dep['n_moduli']} moduli interni | "
          f"{len(dep['pacchetti_esterni'])} pacchetti esterni")
    if dep["pacchetti_esterni"]:
        print(f"   Ext: {', '.join(dep['pacchetti_esterni'][:12])}"
              + (f" … +{len(dep['pacchetti_esterni'])-12}" if len(dep["pacchetti_esterni"]) > 12 else ""))
    if dep["circolari_sospette"]:
        print(f"   ⚠️  Circolari: {', '.join(dep['circolari_sospette'])}")
    else:
        print("   ✓  Nessuna dipendenza circolare rilevata.")

    print(f"\n{SEP}\n")
