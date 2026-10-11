"""Calcolo onesto: Mifflin-St Jeor + macro da letteratura, non un guru.

BMR: Mifflin 1990. Proteine 1.6–2.2 g/kg (ISSN). Deficit ~500 kcal.
Stima, non prescrizione medica.
"""

from __future__ import annotations

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.constants import ParseMode
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.config import CONVERSATION_TIMEOUT
from bot.db import _now, connect

OBIETTIVO, SESSO, ETA, ALTEZZA, PESO, ATTIVITA = range(6)

FATTORI = {
    "sedentario": 1.2,
    "2-3": 1.375,
    "4-5": 1.55,
    "6+": 1.725,
}

SCHEDE = {
    "dimagrire": (
        "*Scheda forza + cammino* (3 giorni, full body)\n"
        "1. Squat o leg press \u2014 3x8\n"
        "2. Panca o piegamenti \u2014 3x8\n"
        "3. Rematore o trazioni \u2014 3x8\n"
        "4. Hip hinge (stacco rumeno o hip thrust) \u2014 3x8\n"
        "5. Cammino 7–9.000 passi il resto della settimana\n\n"
        "Trasforma il fisico soprattutto il *deficit* + la proteina, non l'isolamento bicipiti."
    ),
    "muscolo": (
        "*Scheda ipertrofia* (4 giorni)\n"
        "A. Squat 4x6–8 + affondi 3x10\n"
        "B. Panca 4x6–8 + military 3x8 + dip 3x8\n"
        "C. Stacco 3x5 + rematore 4x8 + trazioni 3x max\n"
        "D. Hip thrust 3x10 + curl/push 3x12 + core\n\n"
        "Progressione: +1–2 kg quando fai tutte le ripetizioni."
    ),
    "mantenere": (
        "*Mantenimento* (3 giorni)\n"
        "Squat, panca, rematore, hinge — 3x8.\n"
        "Cammino quotidiano. Non aggiungere volume a caso."
    ),
}


def _init() -> None:
    with connect() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS corpo_profilo (
                telegram_id INTEGER PRIMARY KEY,
                sesso TEXT, eta INTEGER, altezza_cm REAL, peso_kg REAL,
                attivita TEXT, obiettivo TEXT,
                kcal INTEGER, proteine_g INTEGER, grassi_g INTEGER, carbo_g INTEGER,
                updated_at TEXT)"""
        )


def salva(tid: int, d: dict) -> None:
    _init()
    with connect() as conn:
        conn.execute(
            """INSERT INTO corpo_profilo
            (telegram_id,sesso,eta,altezza_cm,peso_kg,attivita,obiettivo,
             kcal,proteine_g,grassi_g,carbo_g,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(telegram_id) DO UPDATE SET
             sesso=excluded.sesso, eta=excluded.eta, altezza_cm=excluded.altezza_cm,
             peso_kg=excluded.peso_kg, attivita=excluded.attivita,
             obiettivo=excluded.obiettivo, kcal=excluded.kcal,
             proteine_g=excluded.proteine_g, grassi_g=excluded.grassi_g,
             carbo_g=excluded.carbo_g, updated_at=excluded.updated_at""",
            (
                tid, d["sesso"], d["eta"], d["altezza_cm"], d["peso_kg"],
                d["attivita"], d["obiettivo"], d["kcal"], d["proteine_g"],
                d["grassi_g"], d["carbo_g"], _now(),
            ),
        )


def carica(tid: int) -> dict | None:
    _init()
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM corpo_profilo WHERE telegram_id=?", (tid,)
        ).fetchone()
    return dict(row) if row else None


def _num(s: str) -> float | None:
    s = (s or "").strip().replace(",", ".").replace("cm", "").replace("kg", "")
    try:
        return float(s)
    except ValueError:
        return None


def calcola(sesso: str, eta: int, h: float, w: float, att: str, ob: str) -> dict:
    bmr = 10 * w + 6.25 * h - 5 * eta + (5 if sesso == "m" else -161)
    tdee = bmr * FATTORI[att]
    if ob == "dimagrire":
        kcal = max(1200, tdee - 500)
        prot_kg = 1.8
    elif ob == "muscolo":
        kcal = tdee + 250
        prot_kg = 2.0
    else:
        kcal = tdee
        prot_kg = 1.6
    prot = round(prot_kg * w)
    fat = round(max(0.8 * w, 0.25 * kcal / 9))
    carb = max(0, round((kcal - prot * 4 - fat * 9) / 4))
    return {
        "bmr": round(bmr),
        "tdee": round(tdee),
        "kcal": round(kcal),
        "proteine_g": prot,
        "grassi_g": fat,
        "carbo_g": carb,
    }


def _scheda_testo(d: dict) -> str:
    ob = d["obiettivo"]
    return (
        f"*Profilo salvato* — stima, non prescrizione\n\n"
        f"{d['sesso'].upper()}, {d['eta']} anni, {d['altezza_cm']:.0f} cm, {d['peso_kg']:.1f} kg\n"
        f"Obiettivo: *{ob}* \u00b7 attività: {d['attivita']}\n\n"
        f"BMR ~ `{d.get('bmr', '?')}` kcal\n"
        f"Manutenzione (TDEE) ~ `{d.get('tdee', d['kcal'])}` kcal\n"
        f"*Target oggi:* `{d['kcal']}` kcal\n"
        f"Proteine `{d['proteine_g']}` g \u00b7 grassi `{d['grassi_g']}` g \u00b7 carbo `{d['carbo_g']}` g\n\n"
        f"Grassi alimentari: olio extravergine, uova, pesce, frutta secca. "
        f"Non servono olio di cocco miracoloso né zero grassi.\n\n"
        f"{SCHEDE[ob]}\n\n"
        f"P6: se in 4 settimane il peso non si muove di 0.3–0.6 kg (dimagrire) "
        f"o non sale la forza (muscolo), ricalcola con /palestra. "
        f"Cade se copi le kcal e salti gli allenamenti.\n"
        f"Fonti: Mifflin-St Jeor 1990; ISSN proteine 1.6–2.2 g/kg."
    )


async def cmd_palestra(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["corpo"] = {}
    await update.message.reply_text(
        "Obiettivo? Stima da formule pubblicate, non magia.",
        reply_markup=ReplyKeyboardMarkup(
            [["dimagrire", "muscolo"], ["mantenere", "/annulla"]],
            resize_keyboard=True,
        ),
    )
    return OBIETTIVO


async def cmd_scheda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    row = carica(update.effective_user.id)
    if not row:
        await update.message.reply_text("Nessun profilo. /palestra per crearne uno.")
        return
    # ricalcolo bmr per display se manca
    extra = calcola(
        row["sesso"], row["eta"], row["altezza_cm"], row["peso_kg"],
        row["attivita"], row["obiettivo"],
    )
    row.update(extra)
    await update.message.reply_text(_scheda_testo(row), parse_mode=ParseMode.MARKDOWN)


async def set_obiettivo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    t = (update.message.text or "").strip().lower()
    if t not in ("dimagrire", "muscolo", "mantenere"):
        await update.message.reply_text("Scrivi: dimagrire, muscolo o mantenere.")
        return OBIETTIVO
    context.user_data.setdefault("corpo", {})["obiettivo"] = t
    await update.message.reply_text(
        "Sesso biologico per la formula BMR:",
        reply_markup=ReplyKeyboardMarkup([["m", "f"], ["/annulla"]], resize_keyboard=True),
    )
    return SESSO


async def set_sesso(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    t = (update.message.text or "").strip().lower()
    if t not in ("m", "f"):
        await update.message.reply_text("m oppure f.")
        return SESSO
    context.user_data["corpo"]["sesso"] = t
    await update.message.reply_text("Età (anni):", reply_markup=ReplyKeyboardRemove())
    return ETA


async def set_eta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    n = _num(update.message.text or "")
    if n is None or n < 14 or n > 90:
        await update.message.reply_text("Età tra 14 e 90.")
        return ETA
    context.user_data["corpo"]["eta"] = int(n)
    await update.message.reply_text("Altezza in cm (es. 178):")
    return ALTEZZA


async def set_altezza(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    n = _num(update.message.text or "")
    if n and n < 3:
        n *= 100
    if n is None or n < 140 or n > 220:
        await update.message.reply_text("Altezza in cm, tipo 178.")
        return ALTEZZA
    context.user_data["corpo"]["altezza_cm"] = n
    await update.message.reply_text("Peso in kg (es. 78.5):")
    return PESO


async def set_peso(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    n = _num(update.message.text or "")
    if n is None or n < 40 or n > 220:
        await update.message.reply_text("Peso in kg, tipo 78.")
        return PESO
    context.user_data["corpo"]["peso_kg"] = n
    await update.message.reply_text(
        "Quante volte ti muovi / palestra a settimana?",
        reply_markup=ReplyKeyboardMarkup(
            [["sedentario", "2-3"], ["4-5", "6+"]], resize_keyboard=True
        ),
    )
    return ATTIVITA


async def set_attivita(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    t = (update.message.text or "").strip().lower()
    if t not in FATTORI:
        await update.message.reply_text("sedentario, 2-3, 4-5 oppure 6+.")
        return ATTIVITA
    d = context.user_data["corpo"]
    d["attivita"] = t
    calc = calcola(d["sesso"], d["eta"], d["altezza_cm"], d["peso_kg"], t, d["obiettivo"])
    d.update(calc)
    salva(update.effective_user.id, d)
    await update.message.reply_text(
        _scheda_testo(d),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Calcolo interrotto.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def build_palestra_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("palestra", cmd_palestra),
            CommandHandler("fisico", cmd_palestra),
        ],
        states={
            OBIETTIVO: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_obiettivo)],
            SESSO: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_sesso)],
            ETA: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_eta)],
            ALTEZZA: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_altezza)],
            PESO: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_peso)],
            ATTIVITA: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_attivita)],
        },
        fallbacks=[CommandHandler("annulla", cancel)],
        name="palestra",
        persistent=True,
        conversation_timeout=CONVERSATION_TIMEOUT,
        allow_reentry=True,
    )
