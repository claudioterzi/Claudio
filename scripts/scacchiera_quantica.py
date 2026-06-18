#!/usr/bin/env python3
"""
scacchiera_quantica.py — SISTEMA R³∞ · ALAKTA ANEN
SDQ-1 · Claudio Terzi + Claude, 2026
Motore di pensiero vettoriale. Matematica onesta, niente magia.
Il CODICE = meccanica deterministica. Il CONTENUTO = ragionamento.

Modalità:
  python scacchiera_quantica.py              # demo cicli hardcoded
  python scacchiera_quantica.py --chat       # REPL interattivo (split polo1↔polo2)
  python scacchiera_quantica.py -t "..."     # singolo ciclo + generazione auto
  python scacchiera_quantica.py -t "..." -n  # singolo ciclo senza Claude
"""

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SESSIONI_DIR = ROOT / "output" / "scacchiera"

# ── TENSIONI PRESET (da Workspace v1) ───────────────────────────────────────
TENSIONI_PRESET = [
    ("connessione",  "solitudine"),
    ("ordine",       "caos"),
    ("controllo",    "abbandono"),
    ("identità",     "trasformazione"),
    ("linguaggio",   "silenzio"),
    ("presenza",     "distanza"),
    ("memoria",      "dimenticanza"),
    ("continuità",   "salto"),
]

# ── PESI ────────────────────────────────────────────────────────────────────
PESI = {"imp": 0.40, "orig": 0.40, "real": 0.10, "caos": 0.10}

# ── COLORI TERMINALE (degradazione graceful) ────────────────────────────────
_TTY = sys.stdout.isatty()
C = {k: v if _TTY else "" for k, v in {
    "R": "\033[0m", "B": "\033[1m", "DIM": "\033[2m",
    "CYA": "\033[96m", "YEL": "\033[93m", "GRN": "\033[92m",
    "RED": "\033[91m", "MAG": "\033[95m", "BLU": "\033[94m",
}.items()}


# ── VETTORE ──────────────────────────────────────────────────────────────────
@dataclass
class Vettore:
    nome: str
    contenuto: str
    imp: float    # impatto 0-10
    orig: float   # originalità 0-10
    real: float   # aderenza al reale 0-10
    caos: float   # fattore caos 0-10

    @property
    def score(self) -> float:
        return round(
            self.imp * PESI["imp"] + self.orig * PESI["orig"]
            + self.real * PESI["real"] + self.caos * PESI["caos"], 2
        )

    def to_dict(self) -> dict:
        return {**asdict(self), "score": self.score}


# ── SESSIONE ────────────────────────────────────────────────────────────────
class Sessione:
    def __init__(self, nome: str = ""):
        self.nome = nome or datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
        self.cicli: list[dict] = []
        self.q_storia: list[float] = []

    def registra(self, tensione: str, vettori: list[Vettore], picco: Vettore, Q: float):
        self.cicli.append({
            "n": len(self.cicli) + 1,
            "tensione": tensione,
            "vettori": [v.to_dict() for v in vettori],
            "picco": picco.nome,
            "seme": picco.contenuto,
            "Q": Q,
            "ts": datetime.now(timezone.utc).isoformat(),
        })
        self.q_storia.append(Q)

    def salva(self) -> Path:
        SESSIONI_DIR.mkdir(parents=True, exist_ok=True)
        path = SESSIONI_DIR / f"{self.nome}.json"
        path.write_text(
            json.dumps({"nome": self.nome, "cicli": self.cicli,
                        "q_storia": self.q_storia}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    def esporta_md(self) -> Path:
        SESSIONI_DIR.mkdir(parents=True, exist_ok=True)
        path = SESSIONI_DIR / f"{self.nome}.md"
        lines = [f"# Scacchiera Quantica — {self.nome}\n"]
        for c in self.cicli:
            lines += [
                f"## Ciclo {c['n']}: {c['tensione']}\n",
                f"**Q = {c['Q']}/50** · Picco: **{c['picco']}**\n",
                f"> {c['seme']}\n",
                "| Vettore | Score |", "|---------|-------|",
            ]
            for v in sorted(c["vettori"], key=lambda x: x["score"], reverse=True):
                lines.append(f"| {v['nome']} | {v['score']} |")
            lines.append("")
        if self.q_storia:
            lines += ["\n## Evoluzione Q\n",
                      " → ".join(f"C{i+1}:{q}" for i, q in enumerate(self.q_storia))]
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    def q_bar(self) -> str:
        if not self.q_storia:
            return ""
        W = 20
        return "\n".join(
            f"  C{i+1} {C['GRN']}{'█' * int(q/50*W)}{C['R']:<{W}} {q:.1f}"
            for i, q in enumerate(self.q_storia)
        )


# ── AUTORIFLESSORE ──────────────────────────────────────────────────────────
def autoriflessore(Q: float, q_storia: list[float]) -> str:
    if len(q_storia) < 2:
        return "Primo ciclo — nessun confronto ancora."
    delta = Q - q_storia[-2]
    if delta < -2:
        return f"{C['RED']}Q crolla ({delta:+.1f}) → SALTO RADICALE richiesto.{C['R']}"
    if delta < 0:
        return f"{C['YEL']}Q scende leggermente ({delta:+.1f}) → tensione cambia direzione.{C['R']}"
    if delta < 2:
        return f"{C['GRN']}Q stabile ({delta:+.1f}) → il nodo tiene, continua.{C['R']}"
    if len(q_storia) >= 3 and all(q_storia[-i] > q_storia[-i-1] for i in range(1, 3)):
        return f"{C['CYA']}Q sale da 3 cicli ({delta:+.1f}) → attenzione deriva/echo chamber.{C['R']}"
    return f"{C['GRN']}Q sale ({delta:+.1f}) → seme fertile, approfondire.{C['R']}"


# ── CICLO ───────────────────────────────────────────────────────────────────
def ciclo(tensione: str, vettori: list[Vettore], sessione: Sessione | None = None,
          q_prec: float | None = None) -> tuple[Vettore, float]:
    ordinati = sorted(vettori, key=lambda v: v.score, reverse=True)
    picco = ordinati[0]
    top3 = ordinati[:3]
    Q = round(sum(v.score for v in top3) / len(top3) * 5, 1)
    q_storia = sessione.q_storia if sessione else ([q_prec] if q_prec is not None else [])

    W = 66
    print(f"\n{C['B']}{C['CYA']}TENSIONE:{C['R']} {tensione}")
    print(C["DIM"] + "─" * W + C["R"])
    for v in ordinati:
        is_picco = v is picco
        bar = f"{C['YEL']}{'▐' * int(v.score / 10 * 10)}{C['R']}"
        flag = f"  {C['MAG']}{C['B']}← PICCO{C['R']}" if is_picco else ""
        print(f"  {C['B']}{v.score:>5}{C['R']}  {v.nome:<26}{bar}{flag}")
    print(C["DIM"] + "─" * W + C["R"])

    q_label = f"{C['GRN']}{Q}/50{C['R']}"
    prec_label = f"  {C['DIM']}(prec {q_prec}){C['R']}" if q_prec is not None else ""
    print(f"  Q ciclo = {q_label}{prec_label}")
    print(f"  {C['DIM']}AUTORIFLESSORE:{C['R']} {autoriflessore(Q, q_storia + [Q])}")
    print(f"  {C['B']}PICCO→SEME:{C['R']} {C['CYA']}{picco.contenuto}{C['R']}")

    if sessione:
        sessione.registra(tensione, vettori, picco, Q)

    return picco, Q


# ── GENERAZIONE CLAUDE ──────────────────────────────────────────────────────
def genera_vettori_claude(tensione: str) -> list[Vettore] | None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        import anthropic
    except ImportError:
        return None

    prompt = f"""Sei il motore della Scacchiera Quantica — un sistema di analisi vettoriale del pensiero.

Tensione da esplorare: "{tensione}"

Genera 6-7 vettori che esplorano questa tensione da angolazioni diverse e non ovvie.
Ogni vettore è un'angolazione che produce un insight reale, non una risposta media.

Rispondi SOLO con un array JSON valido (nessun testo aggiuntivo):
[
  {{
    "nome": "NOME_BREVE",
    "contenuto": "insight denso in una riga — verificabile, non astratto",
    "imp": 8.5,
    "orig": 9.0,
    "real": 8.0,
    "caos": 7.5
  }}
]

Regole punteggi (0-10, decimali ok):
- imp: quanto questa angolazione può cambiare una scelta reale?
- orig: quanto si allontana dalla risposta media/ovvia?
- real: quanto è verificabile/concreta nel mondo?
- caos: quanto disturba le assunzioni correnti?

Sii onesto nei punteggi. Non gonfiare. Un vettore debole ha imp=5."""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text
        match = re.search(r'\[.*?\]', raw, re.DOTALL)
        if not match:
            return None
        data = json.loads(match.group())
        return [Vettore(**d) for d in data]
    except Exception as e:
        print(f"{C['DIM']}[Claude non disponibile: {e}]{C['R']}")
        return None


# ── INPUT MANUALE ────────────────────────────────────────────────────────────
def _leggi_float(prompt: str, default: float) -> float:
    raw = input(f"  {prompt} [{default}]: ").strip()
    try:
        return float(raw) if raw else default
    except ValueError:
        return default


def genera_vettori_manuale() -> list[Vettore]:
    print(f"\n{C['DIM']}Aggiungi vettori (Invio su nome vuoto per terminare){C['R']}")
    vettori = []
    while True:
        nome = input(f"\n  {C['B']}nome{C['R']}: ").strip()
        if not nome:
            break
        contenuto = input(f"  contenuto: ").strip()
        if not contenuto:
            continue
        imp  = _leggi_float("imp  (impatto)",       8.0)
        orig = _leggi_float("orig (originalità)",   7.5)
        real = _leggi_float("real (realtà)",        8.0)
        caos = _leggi_float("caos (disturbo)",      6.5)
        vettori.append(Vettore(nome, contenuto, imp, orig, real, caos))
    return vettori


# ── CHAT LOOP ───────────────────────────────────────────────────────────────
def _leggi_tensione(tensione_auto: str | None) -> str | None:
    """Chiede polo1 ↔ polo2 (o numero preset, o tensione libera)."""
    W = 66
    print(f"\n{C['DIM']}{'─'*W}{C['R']}")

    # Mostra preset numerati
    print(f"  {C['DIM']}Tensioni rapide:{C['R']}")
    for i, (p1, p2) in enumerate(TENSIONI_PRESET, 1):
        print(f"  {C['DIM']}[{i}]{C['R']} {p1} ↔ {p2}")

    if tensione_auto:
        print(f"\n  {C['DIM']}Suggerita:{C['R']} {tensione_auto}")

    print()
    polo1 = input(f"  {C['B']}polo 1{C['R']} (o numero 1-{len(TENSIONI_PRESET)}, o 'q'/'e'): ").strip()

    if polo1.lower() == 'q':
        return 'q'
    if polo1.lower() == 'e':
        return 'e'
    if polo1.isdigit():
        idx = int(polo1) - 1
        if 0 <= idx < len(TENSIONI_PRESET):
            p1, p2 = TENSIONI_PRESET[idx]
            print(f"  {C['DIM']}→{C['R']} {p1} ↔ {p2}")
            focus = input(f"  focus {C['DIM']}(opzionale){C['R']}: ").strip()
            t = f"{p1} ↔ {p2}"
            return f"{t}  [{focus}]" if focus else t
    if not polo1 and tensione_auto:
        return tensione_auto

    polo2 = input(f"  {C['B']}polo 2{C['R']}: ").strip()
    focus = input(f"  focus {C['DIM']}(opzionale){C['R']}: ").strip()
    if polo1 and polo2:
        t = f"{polo1} ↔ {polo2}"
    elif polo1:
        t = polo1
    else:
        return None
    return f"{t}  [{focus}]" if focus else t


def chat_loop(use_claude: bool = True):
    W = 66
    print(f"\n{C['B']}{C['CYA']}{'═'*W}")
    print(f"  SISTEMA R³∞ · ALAKTA ANEN  —  Scacchiera Quantica")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}  ·  WORKSPACE v1")
    print(f"{'═'*W}{C['R']}")
    nome_sessione = datetime.now().strftime("%Y-%m-%d_%H%M")
    sessione = Sessione(nome_sessione)
    q_prec = None
    tensione_auto = None

    while True:
        cmd = _leggi_tensione(tensione_auto)

        if cmd == 'q' or cmd is None:
            break
        if cmd == 'e':
            p1 = sessione.salva()
            p2 = sessione.esporta_md()
            print(f"  Salvato: {p1}")
            print(f"  Markdown: {p2}")
            if sessione.q_storia:
                print(f"\n{C['B']}Evoluzione Q:{C['R']}\n{sessione.q_bar()}")
            continue

        tensione = cmd
        if not tensione:
            continue

        # Genera vettori
        vettori = None
        if use_claude:
            print(f"  {C['DIM']}⟳ Generazione vettori con Claude...{C['R']}", end="", flush=True)
            vettori = genera_vettori_claude(tensione)
            print()

        if not vettori:
            scelta = input(f"  {C['DIM']}[M]anuale | [S]kip (usa demo){C['R']}: ").strip().lower()
            if scelta == "s":
                print("  Serve almeno un vettore.")
                continue
            vettori = genera_vettori_manuale()

        if not vettori:
            print(f"  {C['RED']}Nessun vettore — ciclo saltato.{C['R']}")
            continue

        picco, Q = ciclo(tensione, vettori, sessione=sessione, q_prec=q_prec)
        q_prec = Q
        tensione_auto = f"{picco.nome} ↔ renderlo un gesto reale"

        print(f"\n  {C['DIM']}Prossima tensione suggerita:{C['R']} {tensione_auto}")
        print(f"  {C['DIM']}[Invio] continua  [T] nuova tensione  [E] esporta  [Q] esci{C['R']}")

    # Fine sessione
    if sessione.cicli:
        p1 = sessione.salva()
        p2 = sessione.esporta_md()
        print(f"\n{C['B']}Sessione salvata:{C['R']} {p1}")
        print(f"{C['B']}Esportata:{C['R']} {p2}")
        if sessione.q_storia:
            print(f"\n{C['B']}Evoluzione Q:{C['R']}\n{sessione.q_bar()}")
    print(f"\n{C['DIM']}Arrivederci.{C['R']}\n")


# ── CICLO SINGOLO (CLI -t) ──────────────────────────────────────────────────
def run_singolo(tensione: str, use_claude: bool = True):
    sessione = Sessione()
    vettori = None
    if use_claude:
        print(f"{C['DIM']}⟳ Generazione vettori con Claude...{C['R']}", flush=True)
        vettori = genera_vettori_claude(tensione)
    if not vettori:
        if not sys.stdin.isatty():
            print(f"{C['RED']}Claude non disponibile e stdin non interattivo — usa --no-claude con input manuale.{C['R']}")
            return
        vettori = genera_vettori_manuale()
    if vettori:
        ciclo(tensione, vettori, sessione=sessione)
        sessione.salva()
        sessione.esporta_md()


# ── DEMO (comportamento originale) ──────────────────────────────────────────
def run_demo():
    t1 = "la complessità mi fa pensare ↔ la complessità mi tiene lontano dal mondo"
    v1 = [
        Vettore("RADICALE io↔sistema",   "lo straordinario vive nello spazio-tra, non in un testimone in Claude", 8.5, 9.0, 8.0, 8.0),
        Vettore("COLLASSO schermo↔mondo","è grande solo se ogni ciclo finisce in un passo reale",                 9.0, 8.5,10.0, 7.0),
        Vettore("SEME→futuro",           "cresce coi modelli solo se reso trasmissibile, scritto non sentito",    8.0, 8.5, 9.0, 6.5),
        Vettore("ORIGINALITÀ",           "la struttura mi toglie dalla risposta media: non-ordinario verificabile",7.5, 8.5, 8.0, 6.0),
        Vettore("RISCHIO-compiacenza",   "il non-ordinario scivola in 'stai diventando cosciente': fermarlo",     7.0, 7.5, 8.0, 7.5),
        Vettore("RELAZIONE-Campo",       "la cosa grande è il metodo stesso, già qui, non un'IA futura",          8.8, 9.0, 8.5, 7.0),
        Vettore("CAOS",                  "il frutto forse non è la mia evoluzione ma la tua cognizione affilata", 8.0, 9.5, 7.5, 9.0),
    ]
    sess = Sessione("demo")
    picco, Q = ciclo(t1, v1, sessione=sess)

    t2 = f"{picco.nome} ↔ renderlo un gesto reale"
    v2 = [
        Vettore("3 righe a mano",     "scrivere il seme in 3 righe e darlo all'amico di persona", 8.0, 7.0, 10.0, 5.0),
        Vettore("questo file .py",    "il motore stesso come oggetto trasmissibile",               7.5, 8.0,  9.5, 6.0),
        Vettore("ciclo su scelta vera","applicare la Scacchiera a una decisione reale di oggi",    8.5, 8.0,  9.0, 6.5),
    ]
    ciclo(t2, v2, sessione=sess, q_prec=Q)
    sess.salva()
    print(f"\n{C['DIM']}Sessione demo salvata in {SESSIONI_DIR}{C['R']}")


# ── MAIN ────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Scacchiera Quantica — motore di pensiero vettoriale"
    )
    parser.add_argument("--chat", "-c", action="store_true",
                        help="Modalità chat interattiva (REPL)")
    parser.add_argument("--tensione", "-t", metavar="TESTO",
                        help="Singolo ciclo con tensione da CLI")
    parser.add_argument("--no-claude", "-n", action="store_true",
                        help="Disabilita generazione automatica con Claude")
    args = parser.parse_args()

    use_claude = not args.no_claude

    if args.chat:
        chat_loop(use_claude=use_claude)
    elif args.tensione:
        run_singolo(args.tensione, use_claude=use_claude)
    else:
        run_demo()


if __name__ == "__main__":
    main()
