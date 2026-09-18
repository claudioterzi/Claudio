"""Flusso Telegram: Scacchiera + libro paginato."""

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

from bot.config import CONVERSATION_TIMEOUT
from bot import db
from bot import libro as book
from bot import media
from bot import scacchiera as sq
from bot.states import LibroState, ScacchieraState


async def scacchiera_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await db.ensure_user(
        update.effective_user.id,
        update.effective_user.username,
        update.effective_user.first_name,
    )
    await media.manda(update, "scacchiera", sempre=True)
    await update.message.reply_text(
        sq.INTRO + "\n" + sq.elenco(),
        parse_mode=ParseMode.MARKDOWN,
    )
    return ScacchieraState.WAITING_CASA


async def scacchiera_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw = (update.message.text or "").strip()
    hit = sq.trova(raw)
    if not hit:
        await update.message.reply_text(
            "Scrivi un numero da 1 a 15, o una delle due parole della coppia."
        )
        return ScacchieraState.WAITING_CASA
    n, coppia = hit
    a, b, _nota = coppia
    db.add_epistemic(
        update.effective_user.id,
        "UNKNOWN",
        f"casa {n}: {a}/{b}",
        source="scacchiera",
        how_falls="cade se la tensione non produce alcun effetto osservabile",
    )
    await update.message.reply_text(sq.posizione(n, coppia), parse_mode=ParseMode.MARKDOWN)
    return ConversationHandler.END


async def scacchiera_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Scacchiera chiusa. Nessuna casa è stata occupata.")
    return ConversationHandler.END


async def libro_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["libro_i"] = 0
    await media.manda(update, "libro", p=0.7)
    await update.message.reply_text(book.indice())
    _i, corpo = book.pagina(0)
    await update.message.reply_text(corpo)
    return LibroState.WAITING_PAGE


async def libro_nav(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw = (update.message.text or "").strip().lower()
    i = int(context.user_data.get("libro_i") or 0)
    if raw in {"fine", "esci", "stop", "chiudi"}:
        await update.message.reply_text("Libro chiuso. Niente è stato creduto al posto tuo.")
        return ConversationHandler.END
    if raw in {"indice", "menu"}:
        await update.message.reply_text(book.indice())
        return LibroState.WAITING_PAGE
    if raw in {"avanti", "dopo", "next", "+", ">"}:
        i += 1
    elif raw in {"indietro", "prima", "prev", "-", "<"}:
        i -= 1
    elif raw.isdigit():
        i = int(raw)
    else:
        await update.message.reply_text("Scrivi avanti, indietro, un numero, indice o fine.")
        return LibroState.WAITING_PAGE
    i, corpo = book.pagina(i)
    context.user_data["libro_i"] = i
    await update.message.reply_text(corpo)
    return LibroState.WAITING_PAGE


async def libro_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Libro chiuso.")
    return ConversationHandler.END


def build_scacchiera_conversation():
    return ConversationHandler(
        entry_points=[CommandHandler("scacchiera", scacchiera_entry)],
        states={
            ScacchieraState.WAITING_CASA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, scacchiera_choice),
            ],
        },
        fallbacks=[CommandHandler("annulla", scacchiera_cancel)],
        name="scacchiera",
        persistent=True,
        conversation_timeout=CONVERSATION_TIMEOUT,
    )


def build_libro_conversation():
    return ConversationHandler(
        entry_points=[CommandHandler("libro", libro_entry)],
        states={
            LibroState.WAITING_PAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, libro_nav),
            ],
        },
        fallbacks=[CommandHandler("annulla", libro_cancel), CommandHandler("fine", libro_cancel)],
        name="libro",
        persistent=True,
        conversation_timeout=CONVERSATION_TIMEOUT,
    )


def scacchiera_command_handlers():
    return []
