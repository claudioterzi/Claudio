"""Raffaello's Telegram surface: free text, explicit analysis, private continuity."""
from __future__ import annotations

import asyncio
import re

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CallbackQueryHandler, CommandHandler, ConversationHandler

from bot import db
from bot import raffaello_engine as engine
from bot import raffaello_store as store


def web_url(path="/dialogo-raffaello"):
    return engine.site_url() + path


async def private(update):
    if not update.effective_user or not update.effective_chat or update.effective_chat.type != "private":
        if update.callback_query:
            await update.callback_query.answer("Apri la chat privata con il bot.", show_alert=True)
        elif update.effective_message:
            await update.effective_message.reply_text("Per il dialogo personale, apri la chat privata con il bot.")
        return False
    if not engine.allowed(update.effective_user.id):
        if update.callback_query:
            await update.callback_query.answer("Account non abilitato a Raffaello.", show_alert=True)
        else:
            await update.effective_message.reply_text(
                "Questo account non è ancora abilitato al dialogo personale con Raffaello.\n\n"
                f"Il tuo ID Telegram: {update.effective_user.id}\n"
                "Comunica questo numero a chi configura il tuo accesso."
            )
        return False
    return True


def actions(did=None, rid=None):
    rows = []
    if did:
        rows.append([InlineKeyboardButton("Analizza", callback_data="r3:a:" + did)])
    suffix = "?lettura=" + rid if rid else ""
    rows.append([InlineKeyboardButton("Apri sul sito", url=web_url() + suffix)])
    return InlineKeyboardMarkup(rows)


async def start(update, context):
    if not await private(update):
        return
    user = update.effective_user
    await db.ensure_user(user.id, user.username, user.first_name)
    arg = (context.args or [""])[0]
    if re.fullmatch(r"r3_[a-f0-9]{32}", arg):
        await open_reading(update, arg[3:])
        return
    await update.effective_message.reply_text(
        "Raffaello · Rosso Rosso Rosso\n\n"
        "Portami una domanda, un'idea o qualcosa che vuoi capire. Scrivi liberamente, poi premi Analizza.\n\n"
        "Se riprendiamo Alpha 74, conserverò le carte, le direzioni e la lettura già fatta. "
        "Per collegare il sito usa /collega; per ritrovare una lettura, /letture.\n\n"
        "/nuovo apre un nuovo dialogo. I registri del Protocollo restano in /rrr.", reply_markup=ReplyKeyboardRemove())
    await update.effective_message.reply_text("Da dove vuoi partire?", reply_markup=actions())


async def stage(update, context):
    if not await private(update):
        return
    try:
        user = update.effective_user
        await db.ensure_user(user.id, user.username, user.first_name)
        task = store.stage(user.id, update.effective_message.text or "", f"tg:{update.effective_chat.id}:{update.effective_message.message_id}", use_current=True)
        label = "Domanda pronta."
        if task["reading_id"]:
            snapshot = store.reading(user.id, task["reading_id"])["snapshot"]
            label += " Riprendo la lettura: " + (snapshot["domanda"] or ", ".join(c["carta"] for c in snapshot["carte"]))
        await update.effective_message.reply_text(label + "\nPremi Analizza quando vuoi la risposta.", reply_markup=actions(task["id"], task["reading_id"]))
    except store.Problem as exc:
        await update.effective_message.reply_text(str(exc))


async def callback(update, context):
    if not await private(update):
        return
    query = update.callback_query
    await query.answer()
    match = re.fullmatch(r"r3:([ar]):([a-f0-9]{32})", query.data or "")
    if not match:
        return
    try:
        if match[1] == "r":
            await open_reading(update, match[2])
            return
        await update.effective_message.reply_text("Sto analizzando la tua domanda…")
        result = await asyncio.to_thread(engine.analyze, update.effective_user.id, match[2])
        text = result["risposta"]
        # Plain text avoids interpreting user/model Markdown as Telegram entities.
        for index in range(0, len(text), 3500):
            await update.effective_message.reply_text(text[index:index+3500])
        url = web_url() + "?richiesta=" + match[2]
        await update.effective_message.reply_text("Puoi continuare a scrivermi o ritrovare questa risposta sul sito.", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Ascolta sul sito", url=url + "&ascolto=1"), InlineKeyboardButton("Apri sul sito", url=url)]
        ]))
    except store.Problem as exc:
        await update.effective_message.reply_text(str(exc))


async def open_reading(update, rid):
    owner = update.effective_user.id
    try:
        item = store.reading(owner, rid)
        store.select(owner, rid)
        data = item["snapshot"]
        cards = "\n".join(f"{c['posizione_label']} · {c['carta']}\n{c['asse'].capitalize()} · {c['polarita'].capitalize()} — {c['significato_canonico']}" for c in data["carte"])
        await update.effective_message.reply_text("Alpha 74 · La tua lettura\n\n" + cards)
        text = data["lettura"]["messaggio"]
        for index in range(0, len(text), 3500):
            await update.effective_message.reply_text(text[index:index+3500])
        url = web_url() + "?lettura=" + rid
        await update.effective_message.reply_text("Scrivi la domanda che vuoi approfondire, poi premi Analizza.", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Ascolta sul sito", url=url + "&ascolto=1"), InlineKeyboardButton("Apri sul sito", url=url)]
        ]))
    except store.Problem as exc:
        await update.effective_message.reply_text(str(exc))


async def readings(update, context):
    if not await private(update):
        return
    rows = store.readings(update.effective_user.id)
    if not rows:
        await update.effective_message.reply_text("Non hai ancora collegato una lettura. Sul sito, dopo l'analisi, scegli Continua su Telegram.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Apri Alpha 74", url=web_url("/tarocchi-manuale"))]]))
        return
    keyboard = [[InlineKeyboardButton((r["domanda"] or ", ".join(r["carte"]))[:60], callback_data="r3:r:" + r["id"])] for r in rows[:10]]
    await update.effective_message.reply_text("Quale lettura vuoi riprendere?", reply_markup=InlineKeyboardMarkup(keyboard))


async def link(update, context):
    if not await private(update):
        return
    code = store.link_code(update.effective_user.id)
    await update.effective_message.reply_text("Collega il tuo sito a questa chat.\n\n" + code + "\n\nIncolla il codice nella pagina qui sotto entro 10 minuti. È personale e vale una sola volta.", reply_markup=actions())


async def unlink(update, context):
    if not await private(update):
        return
    store.revoke(update.effective_user.id)
    await update.effective_message.reply_text("Collegamenti al sito revocati. Le letture e i registri restano conservati.")


async def new(update, context):
    if not await private(update):
        return
    store.select(update.effective_user.id)
    await update.effective_message.reply_text("Nuovo dialogo. Scrivi ciò che vuoi analizzare. Le letture precedenti restano in /letture.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def handlers():
    return [CommandHandler("start", start), CommandHandler("collega", link),
            CommandHandler("scollega", unlink), CommandHandler("letture", readings),
            CommandHandler("nuovo", new), CallbackQueryHandler(callback, pattern=r"^r3:")]
