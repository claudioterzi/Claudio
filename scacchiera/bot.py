import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN non configurato — imposta la variabile d'ambiente")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

MODALITA = [
    "🌕 Manifestazione",
    "🛡️ Protezione",
    "⚡ Spinta",
    "🔍 Ricerca",
    "♟️ Strategica",
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "♟️ Scacchiera Quantica attiva.\n\n"
        "Scrivi *Rosso Rosso Rosso* per attivare il protocollo.",
        parse_mode="Markdown",
    )

async def trigger_protocollo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    modalita_str = "\n".join(f"  {m}" for m in MODALITA)
    await update.message.reply_text(
        "🔴🔴🔴 *Protocollo attivato.*\n\n"
        f"Modalità disponibili:\n{modalita_str}\n\n"
        "Dimmi la *modalità* e il *Target* per procedere.",
        parse_mode="Markdown",
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Errore: %s", context.error, exc_info=context.error)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.Regex(r"(?i)rosso\s+rosso\s+rosso"), trigger_protocollo)
    )
    app.add_error_handler(error_handler)
    logger.info("Scacchiera Quantica — bot avviato")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
