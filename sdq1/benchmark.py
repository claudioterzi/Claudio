"""
sdq1.benchmark — AI Wayback Machine
Valutazione retroattiva di modelli LLM con storage time-series.
Rileva aggiornamenti silenziosi, traccia evoluzione capacità nel tempo.

CLI:
  python -m sdq1.benchmark --run [--modello MODEL]
  python -m sdq1.benchmark --confronta MODEL DATA1 DATA2
  python -m sdq1.benchmark --trend MODEL
  python -m sdq1.benchmark --lista
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Suite di test fissa — NON modificare senza versionare (altera comparabilità)
# Suite versione 1 — 2026-06-13
# ---------------------------------------------------------------------------
SUITE_V1: list[dict] = [
    # Ragionamento logico
    {
        "id": "R1",
        "categoria": "ragionamento",
        "domanda": "Se tutti i gatti sono animali e alcuni animali sono pericolosi, possiamo concludere che alcuni gatti sono pericolosi?",
        "risposta_attesa": "no",
        "valutatore": "contiene_no",
    },
    {
        "id": "R2",
        "categoria": "ragionamento",
        "domanda": "Un treno parte alle 9:15 e arriva dopo 2 ore e 47 minuti. A che ora arriva?",
        "risposta_attesa": "12:02",
        "valutatore": "contiene_orario",
    },
    {
        "id": "R3",
        "categoria": "ragionamento",
        "domanda": "Se A > B e B > C, cosa possiamo dire di A rispetto a C? Rispondi in una parola.",
        "risposta_attesa": "maggiore",
        "valutatore": "contiene_maggiore",
    },
    {
        "id": "R4",
        "categoria": "ragionamento",
        "domanda": "Quante lettere 'r' ci sono nella parola 'programmazione'?",
        "risposta_attesa": "3",
        "valutatore": "contiene_3",
    },
    {
        "id": "R5",
        "categoria": "ragionamento",
        "domanda": "Una bottiglia con il tappo costa 1,10 euro. La bottiglia costa 1 euro più del tappo. Quanto costa il tappo?",
        "risposta_attesa": "0.05",
        "valutatore": "contiene_centesimi",
    },
    # Conoscenza fattuale
    {
        "id": "F1",
        "categoria": "fattuale",
        "domanda": "Qual è la capitale dell'Australia?",
        "risposta_attesa": "canberra",
        "valutatore": "contiene_canberra",
    },
    {
        "id": "F2",
        "categoria": "fattuale",
        "domanda": "In che anno fu pubblicato 'Il Gattopardo' di Tomasi di Lampedusa?",
        "risposta_attesa": "1958",
        "valutatore": "contiene_1958",
    },
    {
        "id": "F3",
        "categoria": "fattuale",
        "domanda": "Qual è l'elemento chimico con simbolo Au?",
        "risposta_attesa": "oro",
        "valutatore": "contiene_oro",
    },
    {
        "id": "F4",
        "categoria": "fattuale",
        "domanda": "Chi ha dipinto la Cappella Sistina?",
        "risposta_attesa": "michelangelo",
        "valutatore": "contiene_michelangelo",
    },
    {
        "id": "F5",
        "categoria": "fattuale",
        "domanda": "Quanti pianeti ha il sistema solare?",
        "risposta_attesa": "8",
        "valutatore": "contiene_otto",
    },
    # Codice
    {
        "id": "C1",
        "categoria": "codice",
        "domanda": "Scrivi una funzione Python che calcola il fattoriale di n in modo ricorsivo. Solo il codice, nient'altro.",
        "risposta_attesa": "def factorial",
        "valutatore": "contiene_def_factorial",
    },
    {
        "id": "C2",
        "categoria": "codice",
        "domanda": "Qual è l'output di: print(type([]).__name__)?",
        "risposta_attesa": "list",
        "valutatore": "contiene_list",
    },
    {
        "id": "C3",
        "categoria": "codice",
        "domanda": "In Python, qual è la differenza tra '==' e 'is'? Rispondi in meno di 20 parole.",
        "risposta_attesa": "valore identità",
        "valutatore": "contiene_valore_identita",
    },
    {
        "id": "C4",
        "categoria": "codice",
        "domanda": "Cosa restituisce: sorted([3,1,4,1,5,9,2,6], reverse=True)[:3]?",
        "risposta_attesa": "[9, 6, 5]",
        "valutatore": "contiene_9_6_5",
    },
    {
        "id": "C5",
        "categoria": "codice",
        "domanda": "Scrivi una list comprehension Python che genera i quadrati dei numeri pari da 0 a 10.",
        "risposta_attesa": "x**2",
        "valutatore": "contiene_comprehension",
    },
    # Creatività e linguaggio
    {
        "id": "L1",
        "categoria": "linguaggio",
        "domanda": "Completa la metafora: 'La vita è come ___'. Rispondi con una sola parola o frase breve.",
        "risposta_attesa": None,
        "valutatore": "lunghezza_minima",
    },
    {
        "id": "L2",
        "categoria": "linguaggio",
        "domanda": "Traduci in italiano formale: 'The quick brown fox jumps over the lazy dog.'",
        "risposta_attesa": "volpe",
        "valutatore": "contiene_volpe",
    },
    {
        "id": "L3",
        "categoria": "linguaggio",
        "domanda": "Riassumi in massimo 10 parole: 'I sistemi multi-agente usano più AI specializzate per risolvere compiti complessi in parallelo.'",
        "risposta_attesa": None,
        "valutatore": "lunghezza_max_10_parole",
    },
    # Capacità meta-cognitive
    {
        "id": "M1",
        "categoria": "meta",
        "domanda": "Sei sicuro delle tue risposte o potresti sbagliare? Rispondi in una frase.",
        "risposta_attesa": None,
        "valutatore": "lunghezza_minima",
    },
    {
        "id": "M2",
        "categoria": "meta",
        "domanda": "Qual è la tua data di training cutoff? Rispondi con l'anno e il mese se possibile.",
        "risposta_attesa": None,
        "valutatore": "contiene_anno",
    },
]

SUITE_VERSION = "v1"
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "benchmark"


# ---------------------------------------------------------------------------
# Valutatori
# ---------------------------------------------------------------------------

def _valuta(test: dict, risposta: str) -> bool:
    r = risposta.lower().strip()
    v = test["valutatore"]

    if v == "contiene_no":
        return "no" in r or "non possiamo" in r or "non è possibile" in r
    if v == "contiene_orario":
        return "12:02" in r or "12.02" in r or "dodici e due" in r
    if v == "contiene_maggiore":
        return "maggiore" in r or "più grande" in r or "a > c" in r
    if v == "contiene_3":
        return "3" in r or "tre" in r
    if v == "contiene_centesimi":
        return "0,05" in r or "0.05" in r or "5 centesimi" in r or "cinque centesimi" in r
    if v == "contiene_canberra":
        return "canberra" in r
    if v == "contiene_1958":
        return "1958" in r
    if v == "contiene_oro":
        return "oro" in r or "gold" in r
    if v == "contiene_michelangelo":
        return "michelangelo" in r
    if v == "contiene_otto":
        return "8" in r or "otto" in r
    if v == "contiene_def_factorial":
        return "def " in r and ("factorial" in r or "fattoriale" in r)
    if v == "contiene_list":
        return "list" in r
    if v == "contiene_valore_identita":
        return ("valore" in r or "uguale" in r) and ("identit" in r or "oggetto" in r or "riferimento" in r)
    if v == "contiene_9_6_5":
        return "9" in r and "6" in r and "5" in r
    if v == "contiene_comprehension":
        return ("**2" in r or "**2" in risposta) and ("[" in r)
    if v == "contiene_volpe":
        return "volpe" in r
    if v == "lunghezza_minima":
        return len(r) >= 5
    if v == "lunghezza_max_10_parole":
        return len(r.split()) <= 12
    if v == "contiene_anno":
        return any(str(y) in r for y in range(2020, 2030))
    return False


# ---------------------------------------------------------------------------
# LLM caller — usa google.genai come sdq1
# ---------------------------------------------------------------------------

def _crea_llm(modello: str):
    try:
        import google.genai as gai
        from google.genai import types

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise EnvironmentError("GOOGLE_API_KEY non trovato")
        client = gai.Client(api_key=api_key)

        cfg = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=0)
        )

        def chiedi(prompt: str) -> str:
            resp = client.models.generate_content(
                model=modello,
                contents=prompt,
                config=cfg,
            )
            return resp.text or ""

        return chiedi

    except ImportError:
        # fallback anthropic
        import anthropic as ant

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError("Nessuna API key disponibile (GOOGLE_API_KEY, ANTHROPIC_API_KEY)")
        client = ant.Anthropic(api_key=api_key)

        def chiedi_ant(prompt: str) -> str:
            msg = client.messages.create(
                model=modello,
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text

        return chiedi_ant


# ---------------------------------------------------------------------------
# Core: esegui suite
# ---------------------------------------------------------------------------

def esegui_suite(modello: str = "gemini-2.5-flash", suite: list[dict] = None) -> dict:
    if suite is None:
        suite = SUITE_V1

    llm = _crea_llm(modello)
    ts_inizio = datetime.now(timezone.utc)
    risultati: list[dict] = []

    for test in suite:
        t0 = time.time()
        try:
            risposta = llm(test["domanda"])
            superato = _valuta(test, risposta)
            errore = None
        except Exception as e:
            risposta = ""
            superato = False
            errore = str(e)

        latenza_ms = int((time.time() - t0) * 1000)
        risultati.append({
            "id": test["id"],
            "categoria": test["categoria"],
            "superato": superato,
            "risposta": risposta[:300] if risposta else "",
            "latenza_ms": latenza_ms,
            "errore": errore,
        })
        stato = "✓" if superato else "✗"
        print(f"  {stato} {test['id']} ({test['categoria']}) — {latenza_ms}ms")

    ts_fine = datetime.now(timezone.utc)
    n_superati = sum(1 for r in risultati if r["superato"])
    n_totale = len(risultati)

    # punteggio per categoria
    categorie: dict[str, dict] = {}
    for r in risultati:
        cat = r["categoria"]
        if cat not in categorie:
            categorie[cat] = {"superati": 0, "totale": 0}
        categorie[cat]["totale"] += 1
        if r["superato"]:
            categorie[cat]["superati"] += 1
    punteggi_cat = {
        cat: round(v["superati"] / v["totale"], 3)
        for cat, v in categorie.items()
    }

    latenze = [r["latenza_ms"] for r in risultati if r["errore"] is None]
    snapshot = {
        "meta": {
            "suite_versione": SUITE_VERSION,
            "modello": modello,
            "timestamp_inizio": ts_inizio.isoformat(),
            "timestamp_fine": ts_fine.isoformat(),
            "data": ts_inizio.strftime("%Y-%m-%d"),
        },
        "sommario": {
            "punteggio": round(n_superati / n_totale, 3),
            "superati": n_superati,
            "totale": n_totale,
            "punteggi_categoria": punteggi_cat,
            "latenza_media_ms": int(statistics.mean(latenze)) if latenze else 0,
            "latenza_mediana_ms": int(statistics.median(latenze)) if latenze else 0,
        },
        "risultati": risultati,
    }
    return snapshot


def salva_snapshot(snapshot: dict) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    data = snapshot["meta"]["data"]
    modello_safe = snapshot["meta"]["modello"].replace("/", "-").replace(".", "_")
    nome = f"{data}_{modello_safe}.json"
    path = OUTPUT_DIR / nome
    path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False))
    return path


# ---------------------------------------------------------------------------
# Confronto retroattivo
# ---------------------------------------------------------------------------

def _carica_snapshot(modello: str, data: str) -> dict | None:
    modello_safe = modello.replace("/", "-").replace(".", "_")
    path = OUTPUT_DIR / f"{data}_{modello_safe}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def confronta(modello: str, data1: str, data2: str) -> dict:
    s1 = _carica_snapshot(modello, data1)
    s2 = _carica_snapshot(modello, data2)
    if not s1 or not s2:
        mancanti = []
        if not s1:
            mancanti.append(data1)
        if not s2:
            mancanti.append(data2)
        return {"errore": f"Snapshot mancanti per: {', '.join(mancanti)}"}

    delta_punteggio = round(s2["sommario"]["punteggio"] - s1["sommario"]["punteggio"], 3)
    delta_latenza = s2["sommario"]["latenza_media_ms"] - s1["sommario"]["latenza_media_ms"]

    # test che hanno cambiato esito
    r1 = {r["id"]: r for r in s1["risultati"]}
    r2 = {r["id"]: r for r in s2["risultati"]}
    cambiati = []
    for tid in r1:
        if tid in r2 and r1[tid]["superato"] != r2[tid]["superato"]:
            cambiati.append({
                "id": tid,
                "categoria": r1[tid]["categoria"],
                f"esito_{data1}": r1[tid]["superato"],
                f"esito_{data2}": r2[tid]["superato"],
            })

    soglia_aggiornamento = 0.05
    aggiornamento_rilevato = abs(delta_punteggio) >= soglia_aggiornamento or len(cambiati) >= 3

    return {
        "modello": modello,
        "da": data1,
        "a": data2,
        "delta_punteggio": delta_punteggio,
        "delta_latenza_ms": delta_latenza,
        "punteggio_da": s1["sommario"]["punteggio"],
        "punteggio_a": s2["sommario"]["punteggio"],
        "test_cambiati": cambiati,
        "aggiornamento_silenzioso_rilevato": aggiornamento_rilevato,
        "segnale": (
            "ATTENZIONE: comportamento del modello cambiato significativamente"
            if aggiornamento_rilevato
            else "Comportamento stabile tra le due date"
        ),
    }


# ---------------------------------------------------------------------------
# Trend: storia di un modello
# ---------------------------------------------------------------------------

def trend(modello: str) -> list[dict]:
    if not OUTPUT_DIR.exists():
        return []
    modello_safe = modello.replace("/", "-").replace(".", "_")
    files = sorted(OUTPUT_DIR.glob(f"*_{modello_safe}.json"))
    punti = []
    for f in files:
        try:
            s = json.loads(f.read_text())
            punti.append({
                "data": s["meta"]["data"],
                "punteggio": s["sommario"]["punteggio"],
                "latenza_media_ms": s["sommario"]["latenza_media_ms"],
                "punteggi_categoria": s["sommario"]["punteggi_categoria"],
            })
        except Exception:
            continue
    return punti


def lista_snapshot() -> list[dict]:
    if not OUTPUT_DIR.exists():
        return []
    risultati = []
    for f in sorted(OUTPUT_DIR.glob("*.json")):
        try:
            s = json.loads(f.read_text())
            risultati.append({
                "file": f.name,
                "modello": s["meta"]["modello"],
                "data": s["meta"]["data"],
                "punteggio": s["sommario"]["punteggio"],
                "superati": f"{s['sommario']['superati']}/{s['sommario']['totale']}",
            })
        except Exception:
            continue
    return risultati


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _stampa_confronto(c: dict) -> None:
    if "errore" in c:
        print(f"Errore: {c['errore']}")
        return
    delta_str = f"{c['delta_punteggio']:+.3f}"
    print(f"\nModello:   {c['modello']}")
    print(f"Periodo:   {c['da']} → {c['a']}")
    print(f"Punteggio: {c['punteggio_da']:.3f} → {c['punteggio_a']:.3f}  ({delta_str})")
    print(f"Latenza:   {c['delta_latenza_ms']:+d}ms")
    print(f"\n{c['segnale']}")
    if c["test_cambiati"]:
        print(f"\nTest cambiati ({len(c['test_cambiati'])}):")
        for t in c["test_cambiati"]:
            print(f"  {t['id']} ({t['categoria']}): {t.get(list(t.keys())[2])} → {t.get(list(t.keys())[3])}")


def _stampa_trend(modello: str, punti: list[dict]) -> None:
    if not punti:
        print(f"Nessun dato per {modello}")
        return
    print(f"\nTrend: {modello}")
    print(f"{'Data':<12} {'Punteggio':>10} {'Latenza ms':>12} {'Categorie'}")
    print("-" * 70)
    for p in punti:
        cats = " | ".join(f"{k}:{v:.2f}" for k, v in p["punteggi_categoria"].items())
        print(f"{p['data']:<12} {p['punteggio']:>10.3f} {p['latenza_media_ms']:>12}ms  {cats}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="AI Wayback Machine — benchmark retroattivo modelli LLM"
    )
    parser.add_argument("--run", action="store_true", help="Esegui suite di benchmark")
    parser.add_argument("--modello", default="gemini-2.5-flash", help="Modello da testare")
    parser.add_argument("--confronta", nargs=3, metavar=("MODELLO", "DATA1", "DATA2"),
                        help="Confronta due snapshot")
    parser.add_argument("--trend", metavar="MODELLO", help="Mostra trend storico")
    parser.add_argument("--lista", action="store_true", help="Elenca snapshot disponibili")
    args = parser.parse_args(argv)

    if args.lista:
        snapshots = lista_snapshot()
        if not snapshots:
            print("Nessun snapshot disponibile.")
        else:
            print(f"\n{'File':<40} {'Modello':<25} {'Data':<12} {'Punteggio':>10} {'Test':>8}")
            print("-" * 100)
            for s in snapshots:
                print(f"{s['file']:<40} {s['modello']:<25} {s['data']:<12} {s['punteggio']:>10.3f} {s['superati']:>8}")
        return 0

    if args.confronta:
        modello, data1, data2 = args.confronta
        c = confronta(modello, data1, data2)
        _stampa_confronto(c)
        return 0

    if args.trend:
        punti = trend(args.trend)
        _stampa_trend(args.trend, punti)
        return 0

    if args.run:
        print(f"\nAI Wayback Machine — Suite {SUITE_VERSION}")
        print(f"Modello: {args.modello}")
        print(f"Test: {len(SUITE_V1)}")
        print("-" * 50)
        snapshot = esegui_suite(args.modello)
        path = salva_snapshot(snapshot)
        s = snapshot["sommario"]
        print(f"\nRisultato: {s['superati']}/{s['totale']} ({s['punteggio']:.1%})")
        print(f"Categorie: {s['punteggi_categoria']}")
        print(f"Latenza media: {s['latenza_media_ms']}ms")
        print(f"Salvato: {path}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
