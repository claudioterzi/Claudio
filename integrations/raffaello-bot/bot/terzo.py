"""Il pezzo che mancava: un terzo, fuori da questa chat."""

from telegram import Update
from telegram.ext import (
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
    "Chi può *vedere* l'atto? Un nome basta. Non un numero, non un link.\n"
    "Esempio: Fabri"
)

TESTIMONE_ATTO = (
    "Cosa può controllare quella persona, oggi o in questi giorni?\n\n"
    "Deve essere visibile senza credere al bot: una chiamata, un arrivo, un lavoro fatto, un debito pagato."
)

FUORI_PROMPT = (
    "Una cosa fatta *oggi*, fuori da Telegram.\n"
    "Se non l'hai ancora fatta, scrivi quella che farai prima di sera."
)

ESITI = {
    "si": "VISTO",
    "sì": "VISTO",
    "visto": "VISTO",
    "no": "NEGATO",
    "non visto": "NON_VISTO",
    "non ho visto": "NON_VISTO",
    "non_visto": "NON_VISTO",
}


async def testimone_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await db.ensure_user(
        update.effective_user.id,
        update.effective_user.username,
        update.effective_user.first_name,
    )
    await update.message.reply_text(TESTIMONE_CHI)
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
    testo = f"testimone={chi} | {atto}"
    aid = db.add_action(update.effective_user.id, testo)
    tid = db.add_testimone(update.effective_user.id, chi, atto)
    db.add_epistemic(
        update.effective_user.id,
        "TECNICO",
        testo,
        source="testimone",
        how_falls=f"cade se {chi} dice che non è accaduto",
    )
    biglietto = (
        f"Da incollare a {chi}, se vuoi:\n\n"
        f"«Non ti chiedo di capire il bot. Ti chiedo se vedi questa cosa: {atto}. "
        f"Se non la vedi, il protocollo qui ha fallito.»\n\n"
        f"Registrato nello strato tecnico (id {aid}, testimone #{tid}).\n"
        f"Quando {chi} risponde, chiudi il giro con:\n"
        f"/esito {tid} sì   ·   /esito {tid} no   ·   /esito {tid} non visto\n\n"
        f"Il bot non l'ha mandata al posto tuo. Tocca a te uscire."
    )
    await update.message.reply_text(biglietto)
    return ConversationHandler.END


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
    args = context.args or []
    if not args:
        aperti = db.list_testimoni(update.effective_user.id, solo_aperti=True)
        if not aperti:
            await update.message.reply_text(
                "Nessun testimone in attesa. Il giro è chiuso, o mai aperto."
            )
            return
        righe = ["Testimoni in attesa di risposta:"]
        for t in aperti:
            righe.append(f"#{t['id']} — {t['chi']}: {t['atto'][:60]}")
        righe.append("\nChiudi con: /esito <id> sì · no · non visto")
        await update.message.reply_text("\n".join(righe))
        return
    try:
        tid = int(args[0].lstrip("#"))
    except ValueError:
        await update.message.reply_text("Uso: /esito <id> sì · no · non visto")
        return
    parola = " ".join(args[1:]).strip().lower()
    esito = ESITI.get(parola)
    if not esito:
        await update.message.reply_text(
            f"«{parola or '…'}» non è un esito. Vale: sì · no · non visto"
        )
        return
    t = db.get_testimone(update.effective_user.id, tid)
    if not t:
        await update.message.reply_text(
            f"Testimone #{tid} non trovato. /esito senza argomenti elenca gli aperti."
        )
        return
    if t["esito"]:
        await update.message.reply_text(
            f"#{tid} è già chiuso: {t['esito']}. Un esito non si riscrive."
        )
        return
    db.set_esito_testimone(update.effective_user.id, tid, esito)
    if esito == "VISTO":
        chiusura = "P5 rispettata su questo atto: non hai parlato due volte."
    elif esito == "NEGATO":
        chiusura = "L'atto è caduto. Resta scritto che è caduto — il registro non lo nasconde (P6)."
    else:
        chiusura = "Non visto non è falso: è non verificato. Resta aperto il fatto, chiuso il giro."
    db.add_epistemic(
        update.effective_user.id,
        "TECNICO",
        f"esito testimone #{tid} ({t['chi']}): {esito} su «{t['atto'][:120]}»",
        source="esito-testimone",
        how_falls="riportato da te: il bot non può verificare la parola del terzo",
    )
    await update.message.reply_text(
        f"Registrato: {t['chi']} → {esito}.\n{chiusura}\n\n"
        "Nota onesta: l'esito è la tua parola sulla sua parola. "
        "Il bot registra, non verifica."
    )


def build_terzo_conversations():
    testimone = ConversationHandler(
        entry_points=[CommandHandler("testimone", testimone_entry)],
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
    return [testimone, fuori, CommandHandler("esito", cmd_esito)]
