"""/misura — la scheda «Misura» di /corpo, fatta davvero.

Registra un numero (peso, vita, passi, sonno…), ne guarda il trend
e dice se vai verso la meta, se sei fermo, o se stai andando
dalla parte sbagliata — in quel caso sgrida (su mandato del capitano).

Bilancio: 7700 kcal ≈ 1 kg di tessuto. Stima grezza, dichiarata tale.
Ancora biologica: BMI 22, forbice normopeso 18.5–24.9 (altezza da /palestra).
Il bot registra e conta. Non prescrive, non assolve.
"""

from __future__ import annotations

from datetime import datetime

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot import db
from bot.db import _now, connect

# tipo -> (unità, min, max). Tipi fuori lista: accettati, niente limiti.
TIPI_NOTI = {
    "peso": ("kg", 30.0, 300.0),
    "vita": ("cm", 40.0, 250.0),
    "passi": ("passi", 0.0, 200000.0),
    "sonno": ("ore", 0.0, 24.0),
}
SINONIMI = {"girovita": "vita", "circonferenza": "vita", "weight": "peso"}

KCAL_PER_KG = 7700          # stima di letteratura: 1 kg di tessuto ≈ 7700 kcal
SOGLIA_PESO_KG_SETT = 0.2   # sotto questo |delta|/settimana è rumore, non trend
SOGLIA_MUSCOLO_KG_SETT = 0.1  # chi costruisce muscolo sale piano per davvero
SOGLIA_REL_SETT = 0.01      # altri tipi: sotto l'1%/settimana è statico
MAX_PUNTI_TREND = 10

USO = """\
*Misura — un numero, novanta giorni*

Uso: /misura <tipo> <valore> [nota]

Tipi con limiti di buon senso: peso (kg), vita (cm), passi, sonno (ore).
Altri tipi liberi: /misura plank 90 secondi

Esempi:
/misura peso 78,5
/misura vita 92 dopo colazione
/misura passi 8k

Poi /misure peso per trend, bilancio e verdetto.
"""

SGRIDATA = (
    "*Verdetto: CONTRO LA META — sgridata tecnica.*\n"
    "Il numero va dalla parte sbagliata da {giorni:.0f} giorni ({delta:+.1f} kg).\n"
    "Nessun complotto, nessun «metabolismo traditore»: è entrata più energia "
    "di quanta ne è uscita. È aritmetica, non destino.\n"
    "La meta l'hai dichiarata tu con /palestra: il peso doveva andare dall'altra parte.\n"
    "Mossa onesta, oggi: −500 kcal *oppure* +3.000 passi. Domani di nuovo /misura peso.\n"
    "Il bot registra e conta. Non assolve."
)


def _init() -> None:
    with connect() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS misure (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                tipo TEXT NOT NULL,
                valore REAL NOT NULL,
                unita TEXT NOT NULL DEFAULT '',
                nota TEXT,
                created_at TEXT NOT NULL)"""
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_misure_utente_tipo "
            "ON misure(telegram_id, tipo, id)"
        )


def salva(tid: int, tipo: str, valore: float, unita: str, nota: str | None) -> int:
    _init()
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO misure (telegram_id, tipo, valore, unita, nota, created_at) "
            "VALUES (?,?,?,?,?,?)",
            (tid, tipo, valore, unita, (nota or "").strip() or None, _now()),
        )
        return int(cur.lastrowid)


def lista(tid: int, tipo: str | None = None, limit: int = 50) -> list[dict]:
    _init()
    with connect() as conn:
        if tipo:
            rows = conn.execute(
                "SELECT * FROM misure WHERE telegram_id=? AND tipo=? "
                "ORDER BY id DESC LIMIT ?",
                (tid, tipo, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM misure WHERE telegram_id=? ORDER BY id DESC LIMIT ?",
                (tid, limit),
            ).fetchall()
    return [dict(r) for r in rows]


def tipi_usati(tid: int) -> list[str]:
    _init()
    with connect() as conn:
        rows = conn.execute(
            "SELECT tipo, MAX(id) AS m FROM misure WHERE telegram_id=? "
            "GROUP BY tipo ORDER BY m DESC",
            (tid,),
        ).fetchall()
    return [r["tipo"] for r in rows]


def _parse_valore(s: str, tipo: str) -> float | None:
    s = (s or "").strip().lower().replace(",", ".")
    if tipo == "passi" and s.endswith("k"):
        try:
            return float(s[:-1]) * 1000
        except ValueError:
            return None
    for suf in ("kg", "cm", "ore"):
        if s.endswith(suf):
            s = s[: -len(suf)]
    try:
        return float(s)
    except ValueError:
        return None


def ancora_peso(altezza_cm: float) -> tuple[float, float, float]:
    """Forbice normopeso e punto di ancoraggio (BMI 22) dall'altezza."""
    h = altezza_cm / 100.0
    return (18.5 * h * h, 22.0 * h * h, 24.9 * h * h)


def verdetto(
    tipo: str,
    punti: list[tuple[float, datetime]],
    obiettivo: str | None = None,
) -> dict:
    """Trend e giudizio tecnico. `punti` in ordine cronologico: (valore, istante)."""
    if len(punti) < 2:
        return {"stato": "POCHE_MISURE", "n": len(punti)}
    (v0, t0), (v1, t1) = punti[0], punti[-1]
    giorni = max((t1 - t0).total_seconds() / 86400.0, 1.0)
    delta = v1 - v0
    out = {
        "n": len(punti),
        "giorni": giorni,
        "delta": delta,
        "delta_sett": delta / giorni * 7.0,
        "da": v0,
        "a": v1,
        "direzione": "su" if delta > 0 else ("giù" if delta < 0 else "fermo"),
    }
    if tipo == "peso":
        soglia = SOGLIA_MUSCOLO_KG_SETT if obiettivo == "muscolo" else SOGLIA_PESO_KG_SETT
        statico = abs(out["delta_sett"]) < soglia
    else:
        statico = abs(out["delta_sett"]) / max(abs(v0), 1e-9) < SOGLIA_REL_SETT
    if statico:
        out["stato"] = "STATICO"
        return out
    if obiettivo == "mantenere":
        out["stato"] = "DERIVA"  # chi mantiene e si muove, si allontana
    elif obiettivo in ("dimagrire", "muscolo"):
        verso = (obiettivo == "dimagrire" and delta < 0) or (
            obiettivo == "muscolo" and delta > 0
        )
        out["stato"] = "VERSO_META" if verso else "CONTRO_META"
    else:
        out["stato"] = "SENZA_META"
    if tipo == "peso":
        out["kcal_giorno"] = delta * KCAL_PER_KG / giorni
    return out


def _fmt_delta(x: float, unita: str) -> str:
    return (f"{x:+.2f} {unita}".rstrip("0").rstrip(".")).replace(".", ",")


def _testo_verdetto(tipo: str, unita: str, v: dict, profilo: dict | None) -> str:
    if v["stato"] == "POCHE_MISURE":
        return (
            "Serve almeno un'altra misura per vedere una direzione.\n"
            "Un punto è un dato. Due sono una freccia."
        )
    u = unita or ""
    righe = [
        f"Trend: {v['da']:g} → {v['a']:g} {u} in {v['giorni']:.0f} giorni "
        f"({v['n']} misure, {_fmt_delta(v['delta_sett'], u)}/settimana)"
    ]
    stato = v["stato"]
    if stato == "STATICO":
        righe.append(
            "*Verdetto: STATICO.*\n"
            "Il movimento è sotto il rumore di misura: non è un trend, è un'attesa.\n"
            "E l'attesa non avvicina la meta — se il numero non si muove, il piano è teatro."
        )
    elif stato == "VERSO_META":
        righe.append(
            "*Verdetto: VERSO LA META.*\n"
            "La freccia punta dove hai detto tu. Lo dice il tuo numero, non il bot: "
            "è un FATTO, continua così."
        )
        if (
            tipo == "peso"
            and (profilo or {}).get("obiettivo") == "muscolo"
            and v["delta_sett"] > 0.5
        ):
            righe.append(
                "_Nota onesta: sopra +0,5 kg/settimana è più grasso che muscolo. "
                "Rallenta il surplus._"
            )
    elif stato == "CONTRO_META":
        righe.append(SGRIDATA.format(giorni=v["giorni"], delta=v["delta"]))
    elif stato == "DERIVA":
        righe.append(
            "*Verdetto: DERIVA.*\n"
            "Obiettivo mantenere, e il numero si muove. "
            "Per chi mantiene, muoversi è già allontanarsi."
        )
    else:
        righe.append(
            f"*Verdetto: il numero va {v['direzione']}, ma non c'è una meta dichiarata.*\n"
            "Fai /palestra per fissare l'ancora: da lì il verdetto diventa pieno."
        )
    if "kcal_giorno" in v:
        segno = "deficit" if v["kcal_giorno"] < 0 else "surplus"
        righe.append(
            f"Bilancio stimato: {v['kcal_giorno']:+.0f} kcal/giorno ({segno}).\n"
            "_7700 kcal ≈ 1 kg: stima grezza. Acqua e glicogeno fanno rumore — "
            "la bilancia, sul breve, mente._"
        )
    if tipo == "peso" and profilo and profilo.get("altezza_cm"):
        lo, target, hi = ancora_peso(float(profilo["altezza_cm"]))
        dist = v["a"] - target
        dentro = "dentro" if lo <= v["a"] <= hi else "fuori"
        righe.append(
            f"Ancora biologica (BMI 22 su {profilo['altezza_cm']:.0f} cm): "
            f"*{target:.1f} kg* · forbice normopeso {lo:.1f}–{hi:.1f} kg.\n"
            f"Sei {dentro} la forbice ({dist:+.1f} kg dall'ancora)."
        )
    return "\n\n".join(righe)


async def cmd_misura(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text(USO, parse_mode=ParseMode.MARKDOWN)
        return
    tipo = SINONIMI.get(args[0].strip().lower(), args[0].strip().lower())
    valore = _parse_valore(args[1], tipo)
    if valore is None:
        await update.message.reply_text(
            "Non leggo il numero. Esempio: /misura peso 78,5"
        )
        return
    unita = ""
    if tipo in TIPI_NOTI:
        unita, lo, hi = TIPI_NOTI[tipo]
        if not (lo <= valore <= hi):
            await update.message.reply_text(
                f"{tipo}: accetto valori tra {lo:g} e {hi:g} {unita}. "
                "Se il numero è davvero quello, ricontrolla lo strumento (P5)."
            )
            return
    elif valore < 0:
        await update.message.reply_text("Un numero vero, maggiore di zero.")
        return
    nota = " ".join(args[2:]).strip()[:120] or None
    tid = update.effective_user.id
    mid = salva(tid, tipo, valore, unita, nota)
    db.add_epistemic(
        tid,
        "TECNICO",
        f"misura {tipo}: {valore:g} {unita}".strip(),
        source="misura",
        how_falls="cade se lo strumento (bilancia, nastro, contapassi) è stato letto o usato male",
    )
    prev = lista(tid, tipo, limit=2)
    extra = ""
    if len(prev) == 2:
        d = valore - float(prev[1]["valore"])
        if d:
            extra = f"\nΔ vs ultima: {_fmt_delta(d, unita)}"
    await update.message.reply_text(
        f"Registrato ({tipo} #{mid}): *{valore:g} {unita}*.{extra}\n"
        f"/misure {tipo} per trend, bilancio e verdetto.",
        parse_mode=ParseMode.MARKDOWN,
    )


async def cmd_misure(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tid = update.effective_user.id
    args = context.args or []
    tipo = SINONIMI.get(args[0].strip().lower(), args[0].strip().lower()) if args else None
    if not tipo:
        usati = tipi_usati(tid)
        if not usati:
            await update.message.reply_text(
                "Nessuna misura ancora.\n"
                "/misura peso 78,5 per cominciare — un numero, novanta giorni."
            )
            return
        tipo = usati[0]
    righe = lista(tid, tipo, limit=MAX_PUNTI_TREND)
    if not righe:
        await update.message.reply_text(
            f"Nessuna misura di tipo «{tipo}». /misura {tipo} <valore> per registrarla."
        )
        return
    unita = righe[0]["unita"] or ""
    elenco = []
    for r in righe[:5]:
        giorno = (r["created_at"] or "")[:10]
        nota = f" — _{r['nota']}_" if r.get("nota") else ""
        elenco.append(f"• `{giorno}` *{r['valore']:g} {r['unita']}*{nota}")
    punti = []
    for r in reversed(righe):
        try:
            punti.append((float(r["valore"]), datetime.fromisoformat(r["created_at"])))
        except (TypeError, ValueError):
            continue
    profilo = None
    if tipo == "peso":
        try:
            from bot.palestra import carica as carica_profilo

            profilo = carica_profilo(tid)
        except Exception:
            profilo = None
    v = verdetto(tipo, punti, (profilo or {}).get("obiettivo") if tipo == "peso" else None)
    blocchi = [
        f"*Misure — {tipo}* (ultime {min(5, len(righe))} di {len(righe)})\n"
        + "\n".join(elenco),
        _testo_verdetto(tipo, unita, v, profilo),
    ]
    await update.message.reply_text(
        "\n\n".join(blocchi)[:3900], parse_mode=ParseMode.MARKDOWN
    )
