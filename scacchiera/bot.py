"""
Scacchiera Quantica — bot Telegram bidirezionale.

Direzione IN  (Claudio → bot):
    "Rosso Rosso Rosso"       → protocollo modale
    /start /status /help      → comandi base
    /scan /agenti /push       → relay verso SDQ-1 (se SDQ1_URL configurato)
    testo libero              → echo / risposta

Direzione OUT (sistema → Claudio):
    HTTP POST /send           → qualunque servizio esterno può spingere messaggi
    Header: Authorization: Bearer <SCACCHIERA_SECRET>
    Body: {"text": "...", "parse_mode": "HTML"}   (parse_mode opzionale)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone, timedelta

from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ── Config ────────────────────────────────────────────────────────────────────

TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")      # chat_id di Claudio
SECRET  = os.environ.get("SCACCHIERA_SECRET", "")     # auth per /send HTTP
PORT    = int(os.environ.get("PORT", "8080"))
TZ      = timezone(timedelta(hours=2))

if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN non configurato")

logging.basicConfig(format="%(asctime)s  %(levelname)-8s  %(message)s", level=logging.INFO)
log = logging.getLogger("scacchiera")

# ── Stato runtime ─────────────────────────────────────────────────────────────

_app: Application | None = None     # riferimento globale per l'HTTP handler
_chat_id_live: str = CHAT_ID        # aggiornato al primo messaggio ricevuto

# ── Scacchiera: dati ─────────────────────────────────────────────────────────

SCEGLI_MODALITA, INSERISCI_TARGET = range(2)

MODALITA = {
    "manifestazione": ("🌕", "Manifestazione",
        "Stai convocando. L'energia si concentra sul target e inizia ad attrarlo. Il campo è aperto."),
    "protezione":     ("🛡️", "Protezione",
        "Scudo attivo. Il target è avvolto. Nulla di ostile passa senza essere riconosciuto e neutralizzato."),
    "spinta":         ("⚡", "Spinta",
        "Impulso trasmesso. Il target riceve accelerazione — un vento che rimuove l'attrito e apre la strada."),
    "ricerca":        ("🔍", "Ricerca",
        "Antenna dispiegata. Il sistema sta scansionando. Ciò che cerchi è già in movimento verso di te."),
    "strategica":     ("♟️", "Strategica",
        "Posizione acquisita. Il target è sul tavolo. Ogni mossa da qui in poi è calcolata con vantaggio di campo."),
}

def _tastiera_modalita() -> InlineKeyboardMarkup:
    righe = [
        [InlineKeyboardButton(f"{e} {n}", callback_data=k)]
        for k, (e, n, _) in MODALITA.items()
    ]
    righe.append([InlineKeyboardButton("❌ Annulla", callback_data="annulla")])
    return InlineKeyboardMarkup(righe)

def _ora() -> str:
    return datetime.now(TZ).strftime("%H:%M")

# ── Utilità: cattura chat_id ──────────────────────────────────────────────────

def _aggiorna_chat_id(update: Update) -> None:
    global _chat_id_live
    cid = str(update.effective_chat.id) if update.effective_chat else ""
    if cid and cid != _chat_id_live:
        log.info("chat_id aggiornato → %s", cid)
        _chat_id_live = cid

# ── Handler IN: Scacchiera ───────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    _aggiorna_chat_id(update)
    await update.message.reply_text(
        "♟️ *Scacchiera Quantica* — sistema attivo.\n\n"
        "Scrivi *Rosso Rosso Rosso* per attivare il protocollo.\n"
        "Comandi: /status /help",
        parse_mode="Markdown",
    )

async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    _aggiorna_chat_id(update)
    cid = _chat_id_live or "—"
    await update.message.reply_text(
        f"📊 *Scacchiera Quantica — status*\n\n"
        f"  Bot: ✅ online  [{_ora()}]\n"
        f"  Chat ID: `{cid}`\n"
        f"  HTTP /send: {'✅ auth attiva' if SECRET else '⚠️ nessun secret'}\n\n"
        "_Canale bidirezionale operativo._",
        parse_mode="Markdown",
    )

async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    _aggiorna_chat_id(update)
    await update.message.reply_text(
        "🗺️ *Comandi disponibili*\n\n"
        "*Rosso Rosso Rosso* — attiva il protocollo modale\n"
        "/status — stato del sistema\n"
        "/annulla — interrompi il protocollo corrente\n"
        "/help — questo messaggio\n\n"
        "*Canale OUT (HTTP)*\n"
        "`POST /send` con body JSON:\n"
        '`{"text": "messaggio", "parse_mode": "HTML"}`\n'
        "Header: `Authorization: Bearer <SCACCHIERA_SECRET>`",
        parse_mode="Markdown",
    )

async def trigger_protocollo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    _aggiorna_chat_id(update)
    await update.message.reply_text(
        "🔴🔴🔴 *Protocollo attivato.*\n\nScegli la modalità:",
        parse_mode="Markdown",
        reply_markup=_tastiera_modalita(),
    )
    return SCEGLI_MODALITA

async def scegli_modalita(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "annulla":
        await query.edit_message_text("Protocollo annullato.")
        return ConversationHandler.END
    if query.data not in MODALITA:
        return SCEGLI_MODALITA
    ctx.user_data["modalita"] = query.data
    emoji, nome, _ = MODALITA[query.data]
    await query.edit_message_text(
        f"{emoji} *{nome}* selezionata.\n\nIndicami il *Target*:",
        parse_mode="Markdown",
    )
    return INSERISCI_TARGET

async def inserisci_target(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    target = update.message.text.strip()
    k = ctx.user_data.get("modalita", "manifestazione")
    emoji, nome, messaggio = MODALITA[k]
    await update.message.reply_text(
        f"{emoji} *Modalità: {nome}*\n"
        f"🎯 *Target: {target}*\n\n"
        f"{messaggio}\n\n"
        "——\n"
        "_Scrivi_ *Rosso Rosso Rosso* _per un nuovo ciclo._",
        parse_mode="Markdown",
    )
    return ConversationHandler.END

async def cmd_annulla(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    _aggiorna_chat_id(update)
    await update.message.reply_text("Protocollo interrotto.")
    return ConversationHandler.END

async def error_handler(update: object, ctx: ContextTypes.DEFAULT_TYPE):
    log.error("Errore Telegram: %s", ctx.error, exc_info=ctx.error)

# ── Handler OUT: HTTP /send ───────────────────────────────────────────────────

async def http_send(request: web.Request) -> web.Response:
    """Riceve POST /send e inoltra il messaggio a Claudio via Telegram."""
    # Autenticazione
    if SECRET:
        auth = request.headers.get("Authorization", "")
        if auth != f"Bearer {SECRET}":
            return web.Response(status=401, text="Unauthorized")

    # Payload
    try:
        body = await request.json()
    except Exception:
        return web.Response(status=400, text="JSON non valido")

    text = body.get("text", "").strip()
    if not text:
        return web.Response(status=400, text="Campo 'text' mancante")

    parse_mode = body.get("parse_mode", "HTML")
    chat = _chat_id_live

    if not chat:
        return web.Response(status=503, text="chat_id non disponibile — scrivi /start al bot prima")

    try:
        assert _app is not None
        await _app.bot.send_message(chat_id=chat, text=text, parse_mode=parse_mode)
        log.info("OUT → %s: %s", chat, text[:60])
        return web.Response(text="ok")
    except Exception as e:
        log.error("Errore invio: %s", e)
        return web.Response(status=500, text=str(e))

async def http_health(request: web.Request) -> web.Response:
    return web.Response(text=json.dumps({"status": "ok", "ora": _ora()}), content_type="application/json")

# ── Main: polling + HTTP in parallelo ────────────────────────────────────────

async def _avvia():
    global _app

    # Costruisci Application
    _app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r"(?i)rosso\s+rosso\s+rosso"), trigger_protocollo)],
        states={
            SCEGLI_MODALITA: [CallbackQueryHandler(scegli_modalita)],
            INSERISCI_TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, inserisci_target)],
        },
        fallbacks=[CommandHandler("annulla", cmd_annulla)],
    )

    _app.add_handler(CommandHandler("start",  cmd_start))
    _app.add_handler(CommandHandler("status", cmd_status))
    _app.add_handler(CommandHandler("help",   cmd_help))
    _app.add_handler(CommandHandler("annulla", cmd_annulla))
    _app.add_handler(conv)
    _app.add_error_handler(error_handler)

    # HTTP server (aiohttp)
    web_app = web.Application()
    web_app.router.add_post("/send",   http_send)
    web_app.router.add_get("/health",  http_health)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    log.info("HTTP server su 0.0.0.0:%d", PORT)

    # Avvia polling in background
    async with _app:
        await _app.start()
        await _app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        log.info("Scacchiera Quantica — binario bidirezionale attivo")

        # Notifica avvio se chat_id disponibile
        if _chat_id_live:
            try:
                await _app.bot.send_message(
                    chat_id=_chat_id_live,
                    text=f"♟️ <b>Scacchiera Quantica online</b>  [{_ora()}]\n"
                         f"Canale bidirezionale attivo.\n"
                         f"Scrivi <b>Rosso Rosso Rosso</b> per attivare il protocollo.",
                    parse_mode="HTML",
                )
            except Exception:
                pass

        # Loop infinito
        await asyncio.Event().wait()

        await _app.updater.stop()
        await _app.stop()

    await runner.cleanup()

def main():
    asyncio.run(_avvia())

if __name__ == "__main__":
    main()
