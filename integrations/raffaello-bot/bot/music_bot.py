"""Telegram entry points and delivery on the bot's existing asyncio loop."""
from __future__ import annotations

import asyncio
import logging
import uuid

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonWebApp, WebAppInfo
from telegram.error import NetworkError
from telegram.ext import CallbackQueryHandler, CommandHandler

from bot import music_backup as persistence, music_service as service, music_store as store, raffaello
from bot.music_auth import MusicError, is_owner, owner_ids

logger = logging.getLogger("protocollo.music")
_application = None
_integrated_callbacks = True


def studio_markup():
    url = service.studio_url()
    return InlineKeyboardMarkup([[InlineKeyboardButton("Apri Raffaello Studio", web_app=WebAppInfo(url))]]) if url else None


async def studio(update, context):
    if not update.effective_chat or update.effective_chat.type != "private":
        await update.effective_message.reply_text("Apri lo Studio nella chat privata con il bot.")
        return
    message = "Raffaello Studio · la tua storia diventa una canzone.\n\nRaccontami cosa desideri, scegli atmosfera e genere, poi segui la richiesta nello Studio."
    if not service.studio_url():
        message += "\n\nIl collegamento allo Studio deve essere configurato."
    await update.effective_message.reply_text(message, reply_markup=studio_markup())


async def start(update, context):
    if (context.args or [""])[0] in ("studio", "music", "canzone"):
        await studio(update, context)
    else:
        await raffaello.start(update, context)


async def canzone(update, context):
    if not context.args or not update.effective_chat or update.effective_chat.type != "private":
        await studio(update, context)
        return
    user = update.effective_user
    try:
        client_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"telegram-song:{update.effective_chat.id}:{update.effective_message.message_id}"))
        request = await asyncio.to_thread(service.create_request, user.id,
                                         {"story": " ".join(context.args), "client_id": client_id})
        await update.effective_message.reply_text("La tua richiesta è salvata. Puoi seguirla nello Studio.", reply_markup=studio_markup())
    except MusicError as exc:
        await update.effective_message.reply_text(str(exc), reply_markup=studio_markup())


async def callback(update, context):
    query = update.callback_query
    if not update.effective_user or not is_owner(update.effective_user.id) or not update.effective_chat or update.effective_chat.type != "private":
        await query.answer("Questa scelta è riservata a Claudio.", show_alert=True)
        return
    try:
        _, action, rid = query.data.split(":", 2)
        await asyncio.to_thread(persistence.mutate, store.decide, update.effective_user.id, rid, action == "keep")
        await query.answer("Conservata" if action == "keep" else "Scartata")
    except MusicError as exc:
        await query.answer(str(exc), show_alert=True)


async def deliver(rid):
    claim = await asyncio.to_thread(persistence.mutate, store.claim_delivery, rid)
    if not claim:
        return
    try:
        request = await asyncio.to_thread(persistence.mutate, store.internal, rid)
        if request["state"] not in ("ready", "kept"):
            await asyncio.to_thread(persistence.mutate, store.complete_delivery, rid, claim)
            return
        rows = [[InlineKeyboardButton("Ascolta su Suno", url=request["suno_url"])]]
        if service.studio_url():
            rows.append([InlineKeyboardButton("Apri lo Studio", web_app=WebAppInfo(service.studio_url()))])
        if _integrated_callbacks and is_owner(request["requester"]):
            rows.append([InlineKeyboardButton("Conserva", callback_data="music:keep:" + rid),
                         InlineKeyboardButton("Scarta", callback_data="music:discard:" + rid)])
        message = await _application.bot.send_message(
            chat_id=request["requester"],
            text="La tua canzone è pronta: " + request["title"] + "\n\nAscolto confermato da Claudio. Apri il link per ascoltarla in Suno.",
            reply_markup=InlineKeyboardMarkup(rows))
        await asyncio.to_thread(persistence.mutate, store.complete_delivery, rid, claim, message.message_id, rollback_on_failure=False)
    except persistence.BackupError as exc:
        logger.warning("Consegna musicale: persistenza non verificata (%s)", exc.code)
    except Exception as exc:
        await asyncio.to_thread(persistence.mutate, store.complete_delivery, rid, claim, uncertain=isinstance(exc, (NetworkError, TimeoutError)))
        logger.warning("Consegna Telegram fallita: %s", type(exc).__name__)


async def notify_owner(rid):
    claim = await asyncio.to_thread(persistence.mutate, store.claim_owner_notice, rid)
    if not claim:
        return
    sent = False
    request = await asyncio.to_thread(persistence.mutate, store.internal, rid)
    for owner in owner_ids():
        try:
            await _application.bot.send_message(
                chat_id=owner, text="Una nuova canzone aspetta nello Studio.\n\n" + request["story"][:700],
                reply_markup=studio_markup())
            sent = True
        except Exception as exc:
            logger.warning("Avviso musicale owner fallito: %s", type(exc).__name__)
    await asyncio.to_thread(persistence.mutate, store.complete_owner_notice, rid, claim, sent, rollback_on_failure=not sent)


async def attach(application, username, integrated=True):
    global _application, _integrated_callbacks
    _application = application
    _integrated_callbacks = integrated
    loop = asyncio.get_running_loop()
    service.set_bot_username(username)
    service.set_notifier(lambda rid: asyncio.run_coroutine_threadsafe(deliver(rid), loop),
                         lambda rid: asyncio.run_coroutine_threadsafe(notify_owner(rid), loop))
    url = service.studio_url()
    if url:
        await application.bot.set_chat_menu_button(menu_button=MenuButtonWebApp(text="Studio", web_app=WebAppInfo(url)))
    for rid in await asyncio.to_thread(persistence.mutate, store.pending_notices):
        service._owner_notifier(rid)


def handlers():
    return [CommandHandler("start", start), CommandHandler("studio", studio), CommandHandler("canzone", canzone),
            CallbackQueryHandler(callback, pattern=r"^music:(keep|discard):[0-9a-fA-F-]{36}$")]
