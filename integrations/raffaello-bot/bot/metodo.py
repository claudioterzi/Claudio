"""/metodo — il ciclo concordato dalle tre letture."""

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot import media

METODO = """\
*Il metodo — bordo, non abitante*

Osserva.
Formula un'ipotesi.
Dichiara come può cadere (P6).
Agisci, fuori da qui.
Registra l'esito.
Confronta: *previsto X → successo Y*.
Conserva solo ciò che ha retto.

Io classifico e ricordo. Non abito il Campo.
La coscienza resta tua.

*Voci esterne (non sono il Protocollo)*
Popper — un'ipotesi vale se si può mostrare falsa.
Feynman — il primo principio è non fregare te stesso.

/etichetta — nomina
/azione o /fuori — il gesto
/testimone + /esito — l'altro
/registro — cosa ha retto
"""


async def cmd_metodo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await media.manda(update, "metodo", sempre=True)
    await update.message.reply_text(METODO, parse_mode=ParseMode.MARKDOWN)
