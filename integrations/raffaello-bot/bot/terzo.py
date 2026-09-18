"""P5 operativo: l'esito arriva da un secondo account Telegram."""

from __future__ import annotations

import re
import secrets

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.config import CONVERSATION_TIMEOUT
from bot import db
from bot.states import FuoriState, TestimoneState

TESTIMONE_CHI = (
    "Il protocollo non si chiude in questa chat.\n\n"
    "Chi può vedere ciò che farai? Scrivi il suo nome."
)

TESTIMONE_ATTO = (
    "Cosa potrà controllare quella persona, oggi o nei prossimi giorni?\n\n"
    "Descrivi un fatto osservabile: una consegna, un arrivo, una chiamata, un lavoro fatto, un pagamento."
)

FUORI_PROMPT = (
    "Una cosa fatta oggi, fuori da Telegram.\n"
    "Se non l'hai ancora fatta, scrivi quella che farai prima di sera."
)

ESITI = {
    "si": "VISTO",
    "sì": "VISTO",
    "visto": "VISTO",
    "no": "NEGATO",
    "non visto": "NON_VERIFICABILE",
    "non ho visto": "NON_VERIFICABILE",
    "non_visto": "NON_VERIFICABILE",
    "non posso verificare": "NON_VERIFICABILE",
}

ESITO_LABEL = {
    "VISTO": "SÌ, L'HO VISTO",
    "NEGATO": "NO",
    "NON_VERIFICABILE": "NON POSSO VERIFICARLO",
}

WITNESS_START_RE = re.compile(r"^/start(?:@\w+)?\s+(w_[A-Za-z0-9_-]{8,60})\s*$")
VR_START_RE = re.compile(r"^/start(?:@\w+)?\s+vr\s*$", re.IGNORECASE)
CALLBACK_RE = re.compile(r"^witness\|(w_[A-Za-z0-9_-]{8,60})\|(VISTO|NEGATO|NON_VERIFICABILE)$")


def _start_payload(update: Update) -> str:
    text = (update.effective_message.text or "").strip() if update.effective_message else ""
    parts = text.split(maxsplit=1)
    return parts[1].strip() if len(parts) == 2 else ""


def _author_label(author: dict | None) -> str:
    if not author:
        return "Una persona"
    first = (author.get("first_name") or "").strip()
    username = (author.get("username") or "").strip()
    if first:
        return first
    if username:
        return "@" + username.lstrip("@")
    return "Una persona"


def _witness_keyboard(token: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("SÌ, L'HO VISTO", callback_data=f"witness|{token}|VISTO")],
            [InlineKeyboardButton("NO", callback_data=f"witness|{token}|NEGATO")],
            [
                InlineKeyboardButton(
                    "NON POSSO VERIFICARLO",
                    callback_data=f"witness|{token}|NON_VERIFICABILE",
                )
            ],
        ]
    )


async def testimone_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await db.ensure_user(
        update.effective_user.id,
        update.effective_user.username,
        update.effective_user.first_name,
    )
    text = (update.effective_message.text or "") if update.effective_message else ""
    context.user_data["testimone_source"] = "vr" if VR_START_RE.match(text.strip()) else "telegram"
    await update.effective_message.reply_text(TESTIMONE_CHI)
    return TestimoneState.WAITING_CHI


async def testimone_chi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nome = (update.message.text or "").strip()
    if not nome or nome.startswith("/"):
        await update.message.reply_text("Scrivi solo il nome di chi può vedere.")
        return TestimoneState.WAITING_CHI
    context.user_data["testimone_chi"] = nome[:80]
    await update.message.reply_text(TESTIMONE_ATTO)
    return TestimoneState.WAITING_ATTO


async def testimone_atto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    atto = (update.message.text or "").strip()
    if not atto or atto.startswith("/"):
        await update.message.reply_text("Descrivi l'atto visibile, senza /.")
        return TestimoneState.WAITING_ATTO

    chi = context.user_data.get("testimone_chi") or "un terzo"
    source = context.user_data.get("testimone_source") or "telegram"
    token = "w_" + secrets.token_urlsafe(18)
    testo = f"testimone={chi} | {atto}"
    aid = db.add_action(
        update.effective_user.id,
        testo,
        how_verifiable="esito richiesto a un account Telegram distinto tramite token univoco",
    )
    tid = db.add_testimone(update.effective_user.id, chi, atto, witness_token=token)
    db.add_epistemic(
        update.effective_user.id,
        "TECNICO",
        testo,
        source=f"testimone-{source}",
        how_falls=f"cade se {chi}, da un account Telegram distinto, registra NO",
    )

    me = await context.bot.get_me()
    link = f"https://t.me/{me.username}?start={token}"
    await update.message.reply_text(
        f"Atto registrato (id {aid}, testimone #{tid}).\n\n"
        f"Invia questo link a {chi}:\n{link}\n\n"
        "Il link è univoco. L'esito deve arrivare dal suo account Telegram. "
        "Se lo apre lo stesso account dell'autore, P5 lo rifiuta."
    )
    context.user_data.pop("testimone_chi", None)
    context.user_data.pop("testimone_source", None)
    return ConversationHandler.END


async def witness_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = _start_payload(update)
    if not WITNESS_START_RE.match((update.effective_message.text or "").strip()):
        return
    row = db.get_testimone_by_token(token)
    if not row:
        await update.effective_message.reply_text("Questo invito non esiste o non è più valido.")
        return

    if int(row["telegram_id"]) == int(update.effective_user.id):
        await update.effective_message.reply_text(
            "P5: la stessa persona non può essere il proprio terzo. "
            "Invia questo link a un account Telegram distinto."
        )
        return

    if row.get("esito"):
        await update.effective_message.reply_text(
            f"Questo esito è già stato registrato: {ESITO_LABEL.get(row['esito'], row['esito'])}. "
            "Non può essere riscritto."
        )
        return

    await db.ensure_user(
        update.effective_user.id,
        update.effective_user.username,
        update.effective_user.first_name,
    )
    author = db.get_user(int(row["telegram_id"]))
    await update.effective_message.reply_text(
        f"{_author_label(author)} ha indicato questo fatto:\n\n"
        f"«{row['atto']}»\n\n"
        "Tu cosa hai osservato?",
        reply_markup=_witness_keyboard(token),
    )


async def witness_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    match = CALLBACK_RE.match(query.data or "")
    if not match:
        return
    await query.answer()
    token, esito = match.groups()
    status, row = db.record_witness_response(token, update.effective_user.id, esito)

    if status == "NOT_FOUND" or not row:
        await query.edit_message_text("Questo invito non esiste o non è più valido.")
        return
    if status == "P5_SELF":
        await query.edit_message_text(
            "P5: la stessa persona non può essere il proprio terzo. Nessun esito registrato."
        )
        return
    if status == "ALREADY":
        await query.edit_message_text(
            f"Esito già registrato: {ESITO_LABEL.get(row.get('esito'), row.get('esito') or '—')}. "
            "Il registro non consente di riscriverlo."
        )
        return

    label = ESITO_LABEL[esito]
    await query.edit_message_text(
        f"Registrato dal tuo account Telegram: {label}.\n\n"
        "Il bot verifica che l'account sia distinto da quello dell'autore; "
        "non pretende di dimostrare da solo la verità del fatto."
    )

    db.add_epistemic(
        int(row["telegram_id"]),
        "TECNICO",
        f"testimone Telegram distinto → {esito} su «{row['atto'][:240]}»",
        source="esito-testimone-diretto",
        how_falls=(
            "il dato prova chi ha premuto il pulsante su Telegram, non l'evento esterno; "
            "eventuale evidenza indipendente può ancora contraddirlo"
        ),
    )

    try:
        await context.bot.send_message(
            chat_id=int(row["telegram_id"]),
            text=(
                f"Testimone #{row['id']} — {row['chi']}\n"
                f"Esito ricevuto da un account Telegram distinto: {label}.\n\n"
                "Il giro è chiuso e l'esito non può essere riscritto."
            ),
        )
    except Exception:
        # L'esito resta salvato anche se l'autore ha bloccato il bot o la notifica fallisce.
        pass


async def fuori_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(FUORI_PROMPT)
    return FuoriState.WAITING_ATTO


async def fuori_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    atto = (update.message.text or "").strip()
    if not atto or atto.startswith("/"):
        await update.message.reply_text("Una riga, fuori da questa chat.")
        return FuoriState.WAITING_ATTO
    aid = db.add_action(update.effective_user.id, f"fuori | {atto}")
    db.add_epistemic(
        update.effective_user.id,
        "TECNICO",
        atto,
        source="fuori",
        how_falls="cade se è accaduto solo in questa chat",
    )
    await update.message.reply_text(
        f"Fuori registrato (id {aid}).\n"
        "Se è rimasto solo qui, non è fuori. Vai."
    )
    return ConversationHandler.END


async def terzo_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Niente registrato. Il terzo non è stato coinvolto.")
    return ConversationHandler.END


async def cmd_esito(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Compatibilità con i vecchi record; i nuovi esiti arrivano dal link del terzo."""
    args = context.args or []
    if not args:
        aperti = db.list_testimoni(update.effective_user.id, solo_aperti=True)
        if not aperti:
            await update.message.reply_text("Nessun testimone in attesa.")
            return
        righe = ["Testimoni in attesa:"]
        for t in aperti:
            stato = "link al terzo" if t.get("witness_token") else "legacy /esito"
            righe.append(f"#{t['id']} — {t['chi']}: {t['atto'][:60]} — {stato}")
        await update.message.reply_text("\n".join(righe))
        return

    try:
        tid = int(args[0].lstrip("#"))
    except ValueError:
        await update.message.reply_text("Uso legacy: /esito <id> sì · no · non visto")
        return

    t = db.get_testimone(update.effective_user.id, tid)
    if not t:
        await update.message.reply_text(f"Testimone #{tid} non trovato.")
        return
    if t.get("witness_token"):
        await update.message.reply_text(
            "Questo è un record P5 nuovo: l'autore non può inserire l'esito. "
            "Deve rispondere il terzo dal link Telegram univoco."
        )
        return
    if t.get("esito"):
        await update.message.reply_text(
            f"#{tid} è già chiuso: {t['esito']}. Un esito non si riscrive."
        )
        return

    parola = " ".join(args[1:]).strip().lower()
    esito = ESITI.get(parola)
    if not esito:
        await update.message.reply_text("Vale: sì · no · non visto")
        return
    if not db.set_esito_testimone(update.effective_user.id, tid, esito):
        await update.message.reply_text("Esito non registrato: il record è già chiuso o richiede il terzo diretto.")
        return

    db.add_epistemic(
        update.effective_user.id,
        "TECNICO",
        f"esito legacy testimone #{tid}: {esito} su «{t['atto'][:120]}»",
        source="esito-testimone-legacy",
        how_falls="riportato dall'autore: non costituisce conferma indipendente P5",
    )
    await update.message.reply_text(
        f"Registrato come esito legacy: {esito}.\n"
        "Nota P5: è ancora la tua dichiarazione sulla risposta del terzo; non vale come conferma indipendente."
    )


def build_terzo_conversations():
    witness_link = MessageHandler(filters.Regex(WITNESS_START_RE), witness_start)
    witness_result = CallbackQueryHandler(witness_callback, pattern=CALLBACK_RE)

    testimone = ConversationHandler(
        entry_points=[
            CommandHandler("testimone", testimone_entry),
            MessageHandler(filters.Regex(VR_START_RE), testimone_entry),
        ],
        states={
            TestimoneState.WAITING_CHI: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, testimone_chi),
            ],
            TestimoneState.WAITING_ATTO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, testimone_atto),
            ],
        },
        fallbacks=[CommandHandler("annulla", terzo_cancel)],
        name="testimone",
        persistent=True,
        conversation_timeout=CONVERSATION_TIMEOUT,
    )
    fuori = ConversationHandler(
        entry_points=[CommandHandler("fuori", fuori_entry)],
        states={
            FuoriState.WAITING_ATTO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, fuori_save),
            ],
        },
        fallbacks=[CommandHandler("annulla", terzo_cancel)],
        name="fuori",
        persistent=True,
        conversation_timeout=CONVERSATION_TIMEOUT,
    )
    return [witness_link, testimone, witness_result, fuori, CommandHandler("esito", cmd_esito)]
