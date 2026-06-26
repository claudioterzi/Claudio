import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN non configurato")

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Stati conversazione
SCEGLI_MODALITA, INSERISCI_TARGET = range(2)

MODALITA = {
    "manifestazione": ("🌕", "Manifestazione", "Stai convocando. L'energia si concentra sul target e inizia ad attrarlo verso di te. Il campo è aperto."),
    "protezione":     ("🛡️", "Protezione",     "Scudo attivo. Il target è avvolto. Nulla di ostile passa senza essere riconosciuto e neutralizzato."),
    "spinta":         ("⚡", "Spinta",          "Impulso trasmesso. Il target riceve accelerazione — un vento favorevole che rimuove l'attrito e apre la strada."),
    "ricerca":        ("🔍", "Ricerca",         "Antenna dispiegata. Il sistema sta scansionando. Ciò che cerchi è già in movimento verso di te."),
    "strategica":     ("♟️", "Strategica",      "Posizione acquisita. Il target è sul tavolo. Ogni mossa da qui in poi è calcolata con vantaggio di campo."),
}

def tastiera_modalita():
    righe = []
    for chiave, (emoji, nome, _) in MODALITA.items():
        righe.append([InlineKeyboardButton(f"{emoji} {nome}", callback_data=chiave)])
    righe.append([InlineKeyboardButton("❌ Annulla", callback_data="annulla")])
    return InlineKeyboardMarkup(righe)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "♟️ *Scacchiera Quantica* — sistema attivo.\n\n"
        "Scrivi *Rosso Rosso Rosso* per attivare il protocollo.",
        parse_mode="Markdown",
    )

async def trigger_protocollo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔴🔴🔴 *Protocollo attivato.*\n\nScegli la modalità:",
        parse_mode="Markdown",
        reply_markup=tastiera_modalita(),
    )
    return SCEGLI_MODALITA

async def scegli_modalita(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "annulla":
        await query.edit_message_text("Protocollo annullato.")
        return ConversationHandler.END

    if query.data not in MODALITA:
        return SCEGLI_MODALITA

    context.user_data["modalita"] = query.data
    emoji, nome, _ = MODALITA[query.data]
    await query.edit_message_text(
        f"{emoji} *{nome}* selezionata.\n\nIndicami il *Target*:",
        parse_mode="Markdown",
    )
    return INSERISCI_TARGET

async def inserisci_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = update.message.text.strip()
    modalita_key = context.user_data.get("modalita", "manifestazione")
    emoji, nome, messaggio = MODALITA[modalita_key]

    await update.message.reply_text(
        f"{emoji} *Modalità: {nome}*\n"
        f"🎯 *Target: {target}*\n\n"
        f"{messaggio}\n\n"
        "——\n"
        "_Scrivi_ *Rosso Rosso Rosso* _per un nuovo ciclo._",
        parse_mode="Markdown",
    )
    return ConversationHandler.END

async def annulla(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Protocollo interrotto.")
    return ConversationHandler.END

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Errore: %s", context.error, exc_info=context.error)

def main():
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r"(?i)rosso\s+rosso\s+rosso"), trigger_protocollo)
        ],
        states={
            SCEGLI_MODALITA: [CallbackQueryHandler(scegli_modalita)],
            INSERISCI_TARGET: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, inserisci_target)
            ],
        },
        fallbacks=[CommandHandler("annulla", annulla)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_error_handler(error_handler)

    logger.info("Scacchiera Quantica — online")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
