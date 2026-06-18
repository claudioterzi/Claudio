#!/usr/bin/env python3
"""
Portfolio Analyzer — SDQ-1
Legge holdings.json, aggiorna prezzi via CoinGecko, genera report markdown.
VINCOLO: sistema solo consultivo. Zero transazioni autonome.
"""

import json
import os
import time
import datetime
import urllib.request
import urllib.error
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
HOLDINGS_FILE = BASE_DIR / "portfolio" / "holdings.json"
OUTPUT_DIR = BASE_DIR / "output" / "portfolio"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

COINGECKO_API = "https://api.coingecko.com/api/v3"


def fetch_prices(coin_ids: list[str]) -> dict:
    """Recupera prezzi correnti da CoinGecko (free tier, no auth)."""
    ids_param = ",".join(coin_ids)
    url = f"{COINGECKO_API}/simple/price?ids={ids_param}&vs_currencies=eur&include_24hr_change=true&include_7d_change=true"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SDQ-1-PortfolioAnalyzer/1.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read())
    except Exception as e:
        print(f"[WARN] CoinGecko fetch failed: {e}. Usando last_known_price.")
        return {}


def fetch_market_context() -> dict:
    """Recupera BTC dominance e market cap globale per contesto."""
    url = f"{COINGECKO_API}/global"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SDQ-1-PortfolioAnalyzer/1.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read())
            return data.get("data", {})
    except Exception:
        return {}


def calculate_staking_annual_yield(holdings: list, staking_summary: dict) -> dict:
    """Calcola yield annuale stimato dallo staking."""
    results = {}
    price_map = {h["symbol"]: h.get("live_price_eur") or h["last_known_price_eur"] for h in holdings}

    for symbol, info in staking_summary.items():
        price = price_map.get(symbol, 0)
        staked_eur = info["amount"] * price
        annual_yield_eur = staked_eur * (info["apy_approx"] / 100)
        results[symbol] = {
            "staked_amount": info["amount"],
            "staked_value_eur": round(staked_eur, 2),
            "apy": info["apy_approx"],
            "annual_yield_eur": round(annual_yield_eur, 2),
            "monthly_yield_eur": round(annual_yield_eur / 12, 2),
        }
    return results


def analyze_concentration_risk(positions: list, total_eur: float) -> list:
    """Identifica posizioni con concentrazione >10% del portfolio."""
    risks = []
    for p in sorted(positions, key=lambda x: x["current_value_eur"], reverse=True):
        pct = (p["current_value_eur"] / total_eur * 100) if total_eur > 0 else 0
        if pct >= 10:
            risks.append({
                "symbol": p["symbol"],
                "pct": round(pct, 1),
                "value_eur": p["current_value_eur"],
                "risk": "ALTA" if pct >= 15 else "MEDIA"
            })
    return risks


def generate_recommendations(positions: list, total_eur: float, market_ctx: dict) -> list:
    """Genera raccomandazioni NON vincolanti. Zero azioni autonome."""
    recs = []
    btc_dominance = market_ctx.get("btc_dominance", 0)

    for p in positions:
        symbol = p["symbol"]
        pct_portfolio = (p["current_value_eur"] / total_eur * 100) if total_eur > 0 else 0
        change_24h = p.get("change_24h", 0) or 0
        change_7d = p.get("change_7d", 0) or 0

        rec = None
        reason = []

        # Posizioni stagnanti con alto valore nominale e prezzo micro
        if p["last_known_price_eur"] < 0.001 and p["amount"] > 100000:
            rec = "CONSIDERA USCITA"
            reason.append("prezzo micro + quantità enorme = difficile gestione")

        # Cali forti a 7 giorni su posizioni significative
        if change_7d < -20 and pct_portfolio > 3:
            rec = "ATTENZIONE"
            reason.append(f"calo 7g del {change_7d:.1f}% su posizione rilevante")

        # Posizioni in forte crescita: potrebbe essere momento di riduzione
        if change_7d > 30 and pct_portfolio > 5:
            rec = "VALUTA RIDUZIONE PARZIALE"
            reason.append(f"rialzo 7g del {change_7d:.1f}% — potrebbe ridurre rischio")

        # Staking attivo: mantenere
        if p.get("staked", 0) > 0 and p["staked"] == p["amount"]:
            rec = "MANTIENI (staking attivo)"
            reason.append(f"tutto in staking, APY ~{p.get('apy_hint', '?')}%")

        if rec:
            recs.append({
                "symbol": symbol,
                "raccomandazione": rec,
                "motivo": " + ".join(reason),
                "valore_eur": p["current_value_eur"],
                "pct_portfolio": round(pct_portfolio, 1)
            })

    return recs


def generate_category_breakdown(positions: list, total_eur: float) -> dict:
    """Raggruppa posizioni per categoria."""
    categories = {}
    for p in positions:
        cat = p.get("category", "Altro")
        if cat not in categories:
            categories[cat] = {"value_eur": 0, "positions": []}
        categories[cat]["value_eur"] += p["current_value_eur"]
        categories[cat]["positions"].append(p["symbol"])

    for cat in categories:
        categories[cat]["pct"] = round(categories[cat]["value_eur"] / total_eur * 100, 1) if total_eur > 0 else 0

    return dict(sorted(categories.items(), key=lambda x: x[1]["value_eur"], reverse=True))


def format_report(positions: list, total_eur: float, staking_yields: dict,
                  concentration_risks: list, recommendations: list,
                  categories: dict, market_ctx: dict, snapshot_date: str) -> str:

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    btc_dom = market_ctx.get("btc_dominance", 0)
    total_mcap = market_ctx.get("total_market_cap", {}).get("eur", 0)

    lines = [
        f"# Portfolio Crypto — Analisi Giornaliera",
        f"*Generato da SDQ-1 · {now} Brussels*",
        f"*Snapshot di riferimento: {snapshot_date}*",
        "",
        "---",
        "",
        "## Sommario",
        "",
    ]

    # Calcola totale corrente
    live_total = sum(p["current_value_eur"] for p in positions)
    delta = live_total - total_eur
    delta_pct = (delta / total_eur * 100) if total_eur > 0 else 0

    delta_sign = "+" if delta >= 0 else ""
    lines += [
        f"| Metrica | Valore |",
        f"|---------|--------|",
        f"| **Valore Totale Live** | **€{live_total:,.2f}** |",
        f"| Snapshot precedente | €{total_eur:,.2f} |",
        f"| Variazione | {delta_sign}€{delta:,.2f} ({delta_sign}{delta_pct:.1f}%) |",
        f"| Posizioni attive | {len(positions)} |",
    ]

    if btc_dom:
        lines.append(f"| BTC Dominance | {btc_dom:.1f}% |")
    if total_mcap:
        mcap_b = total_mcap / 1e9
        lines.append(f"| Market Cap Globale | €{mcap_b:,.0f}B |")

    lines += ["", "---", "", "## Top 10 Posizioni", ""]
    lines += ["| # | Asset | Quantità | Prezzo EUR | Valore EUR | 24h | 7g | Categoria |"]
    lines += ["|---|-------|----------|-----------|-----------|-----|----|----|"]

    top10 = sorted(positions, key=lambda x: x["current_value_eur"], reverse=True)[:10]
    for i, p in enumerate(top10, 1):
        c24 = p.get("change_24h", 0) or 0
        c7d = p.get("change_7d", 0) or 0
        c24_str = f"{'▲' if c24 >= 0 else '▼'}{abs(c24):.1f}%"
        c7d_str = f"{'▲' if c7d >= 0 else '▼'}{abs(c7d):.1f}%"
        qty_str = f"{p['amount']:,.4f}" if p['amount'] < 100 else f"{p['amount']:,.2f}" if p['amount'] < 10000 else f"{p['amount']:,.0f}"
        price_str = f"€{p['live_price_eur']:,.4f}" if p['live_price_eur'] < 0.01 else f"€{p['live_price_eur']:,.2f}"
        staked_note = " *(staking)*" if p.get("staked", 0) > 0 else ""
        lines.append(f"| {i} | **{p['symbol']}**{staked_note} | {qty_str} | {price_str} | **€{p['current_value_eur']:,.2f}** | {c24_str} | {c7d_str} | {p.get('category', '?')} |")

    lines += ["", "---", "", "## Staking — Rendimento Attivo", ""]
    total_annual = sum(s["annual_yield_eur"] for s in staking_yields.values())
    total_monthly = sum(s["monthly_yield_eur"] for s in staking_yields.values())
    lines += [
        f"**Rendimento annuale stimato totale: €{total_annual:,.2f}**",
        f"**Rendimento mensile stimato: €{total_monthly:,.2f}**",
        "",
        "| Asset | Importo Staked | APY Est. | Yield Mensile | Yield Annuale |",
        "|-------|---------------|----------|---------------|---------------|",
    ]
    for sym, s in staking_yields.items():
        lines.append(f"| {sym} | {s['staked_amount']:,.2f} | {s['apy']}% | €{s['monthly_yield_eur']:,.2f} | €{s['annual_yield_eur']:,.2f} |")

    lines += ["", "---", "", "## Distribuzione per Categoria", ""]
    lines += ["| Categoria | Valore EUR | % Portfolio | Assets |"]
    lines += ["|-----------|-----------|-------------|--------|"]
    for cat, data in categories.items():
        assets_str = ", ".join(data["positions"])
        lines.append(f"| {cat} | €{data['value_eur']:,.2f} | {data['pct']}% | {assets_str} |")

    if concentration_risks:
        lines += ["", "---", "", "## Rischio Concentrazione", "", "> Posizioni superiori al 10% del portfolio:", ""]
        for r in concentration_risks:
            emoji = "🔴" if r["risk"] == "ALTA" else "🟡"
            lines.append(f"- {emoji} **{r['symbol']}**: {r['pct']}% del portfolio (€{r['value_eur']:,.2f}) — rischio {r['risk']}")

    if recommendations:
        lines += ["", "---", "", "## Raccomandazioni"]
        lines += ["", "> ⚠️ **Questo sistema è SOLO consultivo. Nessuna azione viene eseguita automaticamente.**", ""]
        for rec in recommendations:
            emoji = {"CONSIDERA USCITA": "🔴", "ATTENZIONE": "🟡", "VALUTA RIDUZIONE PARZIALE": "🟠", "MANTIENI (staking attivo)": "🟢"}.get(rec["raccomandazione"], "⚪")
            lines.append(f"- {emoji} **{rec['symbol']}** ({rec['pct_portfolio']}% — €{rec['valore_eur']:,.2f}): {rec['raccomandazione']}")
            lines.append(f"  *{rec['motivo']}*")

    lines += ["", "---", "", f"*Analisi generata da SDQ-1 portfolio agent · {now}*"]
    lines += [f"*Prossimo aggiornamento: domani alle 05:00 Brussels (integrato nel morning brief)*"]

    return "\n".join(lines)


def run_analysis() -> str:
    """Esegue l'analisi completa del portfolio. Restituisce il path del report."""

    print("[SDQ-1] Avvio analisi portfolio...")

    with open(HOLDINGS_FILE) as f:
        data = json.load(f)

    holdings = data["positions"]
    staking_summary = data["staking_summary"]
    snapshot_date = data["meta"]["snapshot_date"]
    total_eur_snapshot = data["meta"]["total_value_eur"]

    # Costruisci mappa APY per uso nelle raccomandazioni
    apy_map = {sym: info["apy_approx"] for sym, info in staking_summary.items()}

    # Raccoglie tutti i coingecko IDs validi
    coin_ids = [h["coingecko_id"] for h in holdings if h.get("coingecko_id")]

    print(f"[SDQ-1] Fetching prezzi per {len(coin_ids)} asset...")
    prices = fetch_prices(coin_ids)

    # Aspetta tra richieste per rispettare rate limit free tier
    time.sleep(1.5)
    market_ctx = fetch_market_context()

    # Arricchisci posizioni con prezzi live
    for h in holdings:
        cg_id = h.get("coingecko_id", "")
        price_data = prices.get(cg_id, {})
        live_price = price_data.get("eur") or h["last_known_price_eur"]
        h["live_price_eur"] = live_price
        h["current_value_eur"] = round(h["amount"] * live_price, 2)
        h["change_24h"] = price_data.get("eur_24h_change")
        h["change_7d"] = price_data.get("eur_7d_change")
        h["apy_hint"] = apy_map.get(h["symbol"])

    total_live = sum(h["current_value_eur"] for h in holdings)

    staking_yields = calculate_staking_annual_yield(holdings, staking_summary)
    concentration_risks = analyze_concentration_risk(holdings, total_live)
    recommendations = generate_recommendations(holdings, total_live, market_ctx)
    categories = generate_category_breakdown(holdings, total_live)

    report = format_report(
        holdings, total_eur_snapshot, staking_yields,
        concentration_risks, recommendations, categories,
        market_ctx, snapshot_date
    )

    today = datetime.date.today().isoformat()
    report_path = OUTPUT_DIR / f"portfolio_{today}.md"

    with open(report_path, "w") as f:
        f.write(report)

    # Aggiorna il snapshot nel holdings.json con i prezzi correnti
    data["meta"]["last_analysis"] = datetime.datetime.now().isoformat()
    data["meta"]["last_total_live_eur"] = round(total_live, 2)
    with open(HOLDINGS_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"[SDQ-1] Report salvato: {report_path}")
    print(f"[SDQ-1] Valore portfolio: €{total_live:,.2f} (snapshot: €{total_eur_snapshot:,.2f})")

    return str(report_path)


def get_portfolio_summary_for_brief() -> str:
    """Restituisce un sommario compatto per il morning brief."""
    try:
        with open(HOLDINGS_FILE) as f:
            data = json.load(f)

        last_total = data["meta"].get("last_total_live_eur", data["meta"]["total_value_eur"])
        snapshot = data["meta"]["total_value_eur"]
        delta = last_total - snapshot
        delta_sign = "+" if delta >= 0 else ""

        staking = data["staking_summary"]
        total_annual_yield = 0
        price_map = {h["symbol"]: h.get("last_known_price_eur", 0) for h in data["positions"]}

        for sym, info in staking.items():
            price = price_map.get(sym, 0)
            staked_eur = info["amount"] * price
            total_annual_yield += staked_eur * (info["apy_approx"] / 100)

        top3 = sorted(data["positions"], key=lambda x: x.get("last_known_value_eur", 0), reverse=True)[:3]
        top3_str = " · ".join(f"{p['symbol']} (€{p['last_known_value_eur']:,.0f})" for p in top3)

        staking_assets = list(staking.keys())

        lines = [
            f"**Portfolio:** €{last_total:,.2f} ({delta_sign}€{delta:,.0f} vs snapshot)",
            f"**Top 3:** {top3_str}",
            f"**Staking attivo:** {', '.join(staking_assets)} → ~€{total_annual_yield:,.0f}/anno",
            f"→ [report completo](../output/portfolio/)",
        ]
        return "\n".join(lines)

    except Exception as e:
        return f"*Portfolio: dati non disponibili ({e})*"


if __name__ == "__main__":
    run_analysis()
