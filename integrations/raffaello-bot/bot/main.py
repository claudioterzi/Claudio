"""Entry point — polling + health su PORT (Render free)."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from telegram import BotCommand, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    PicklePersistence,
    filters,
)

from bot.config import LOG_LEVEL, PERSISTENCE_PATH, require_token
from bot.log_safety import RedactedFormatter
from bot.corpo import cmd_corpo, corpo_tasto
from bot.db import init_db
from bot.handlers import build_command_handlers, build_conversation_handlers, cmd_unknown, messaggio_libero
from bot.menu_rrr import CHIUDI, cmd_chiudi_menu, cmd_rrr
from bot.metodo import cmd_metodo
from bot.misure import cmd_misura, cmd_misure
from bot import network as net
from bot.palestra import build_palestra_conversation, cmd_scheda
from bot.scacchiera_flow import (
    build_libro_conversation,
    build_scacchiera_conversation,
    scacchiera_command_handlers,
)
from bot import sdq1
from bot import raffaello, raffaello_http, raffaello_store
from bot.terzo import build_terzo_conversations

log_handler = logging.StreamHandler(sys.stdout)
log_handler.setFormatter(RedactedFormatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO), handlers=[log_handler])
# Telegram puts the bot token in request URLs. HTTP transport logs must not
# inherit the application's INFO/DEBUG level.
for transport_logger in ("httpx", "httpcore", "telegram.request"):
    logging.getLogger(transport_logger).setLevel(logging.WARNING)
logger = logging.getLogger("protocollo")

COMMANDS = [
    BotCommand("start", "Dialoga con Raffaello"),
    BotCommand("letture", "Riprendi una lettura Alpha 74"),
    BotCommand("progetti", "Apri tutti i progetti"),
    BotCommand("collega", "Collega il sito a questa chat"),
    BotCommand("nuovo", "Inizia un nuovo dialogo"),
    BotCommand("scollega", "Revoca i collegamenti al sito"),
    BotCommand("rrr", "Sottomenu con tutti i comandi"),
    BotCommand("palestra", "Calcolo kcal, proteine, scheda"),
    BotCommand("scheda", "Rivedi il profilo salvato"),
    BotCommand("misura", "Registra un numero: peso, vita, passi…"),
    BotCommand("misure", "Trend, bilancio e verdetto verso la meta"),
    BotCommand("corpo", "Sonno, luce, integratori"),
    BotCommand("metodo", "Il ciclo: ipotesi, atto, esito"),
    BotCommand("testimone", "Un atto che un terzo può vedere"),
    BotCommand("fuori", "Una cosa fatta oggi, fuori da qui"),
    BotCommand("azione", "Registra un atto verificabile"),
    BotCommand("aiuto", "Le tre cose che contano"),
    BotCommand("ping", "Il processo è vivo"),
    BotCommand("annulla", "Esci da un flusso"),
]


class _Health(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _header(self, name: str) -> str | None:
        return self.headers.get(name) or self.headers.get(name.lower())

    def do_GET(self) -> None:
        path = (self.path or "/").split("?", 1)[0]
        if path.startswith("/raffaello/v1/"):
            self._raffaello("GET", path)
            return
        if path == "/raffaello/health":
            payload = {"version": "2.0.0", "engine": "raffaello-site-bridge",
                       "commit": os.getenv("RENDER_GIT_COMMIT", "unknown"),
                       "bridge_configured": len(os.getenv("RAFFAELLO_BRIDGE_SECRET", "")) >= 32}
            self._send(200, json.dumps(payload).encode(), "application/json")
            return
        if path in ("/sdq1/health", "/ask/health"):
            payload = json.dumps(sdq1.health(), ensure_ascii=False).encode("utf-8")
            self._send(200, payload, "application/json; charset=utf-8")
            return
        if path == "/network/v1/nodes":
            # Twin Supereroe: GET nodes is open (no secret). POST /event still gated.
            body = json.dumps(net.nodes_payload(), ensure_ascii=False).encode("utf-8")
            self._send(200, body, "application/json; charset=utf-8")
            return
        if path in ("/", "/health"):
            self._send(200, b"ok - protocollo-rosso-bot", "text/plain; charset=utf-8")
            return
        self._send(404, b"not found", "text/plain; charset=utf-8")

    def _body(self):
        try:
            n = int(self.headers.get("Content-Length") or 0)
            if n < 0 or n > 256 * 1024:
                raise raffaello_store.Problem("Richiesta troppo grande.", 413)
            self.connection.settimeout(15)
            data = json.loads(self.rfile.read(n) if n else b"{}")
            if not isinstance(data, dict):
                raise ValueError("not an object")
            return data
        except (ValueError, UnicodeError, TimeoutError) as exc:
            raise raffaello_store.Problem("JSON non valido.", 400) from exc

    def _raffaello(self, method, path):
        from bot.raffaello_engine import authorized
        try:
            if not authorized(self._header("X-Raffaello-Secret")):
                raise raffaello_store.Problem("Accesso non autorizzato.", 401)
            data = self._body() if method == "POST" else {}
            out = raffaello_http.dispatch(method, path.removeprefix("/raffaello/v1"), self.headers, data)
            self._send(200, json.dumps(out, ensure_ascii=False).encode(), "application/json; charset=utf-8")
        except raffaello_store.Problem as exc:
            self._send(exc.status, json.dumps({"errore": str(exc)}).encode(), "application/json")
        except Exception as exc:
            logger.error("Errore bridge: %s", type(exc).__name__)
            self._send(500, b'{"errore":"Errore temporaneo del collegamento."}', "application/json")

    def do_DELETE(self):
        self._raffaello("DELETE", (self.path or "/").split("?", 1)[0])

    def do_POST(self) -> None:
        path = (self.path or "/").split("?", 1)[0]
        if path.startswith("/raffaello/v1/"):
            self._raffaello("POST", path)
            return
        if path == "/network/v1/event":
            if not net.verify_network_secret(self._header("X-Network-Secret")):
                self._send(401, b"unauthorized", "text/plain; charset=utf-8")
                return
            try:
                data = self._body()
            except raffaello_store.Problem as exc:
                self._send(exc.status, b"bad json", "text/plain; charset=utf-8")
                return
            if not net.is_network_event(data):
                self._send(400, b"bad event", "text/plain; charset=utf-8")
                return
            net.remember_network_event(data)
            # Twin ingest only — never institutional alert / crisis gate.
            self.send_response(204)
            self.end_headers()
            return
        if path != "/ask":
            self._send(404, b'{"error":"not found"}', "application/json")
            return
        if not net.verify_network_secret(self._header("X-Network-Secret")):
            self._send(401, b"unauthorized", "text/plain")
            return
        try:
            data = self._body()
        except raffaello_store.Problem as exc:
            self._send(exc.status, b'{"error":"json"}', "application/json")
            return
        out = sdq1.ask(str(data.get("testo") or ""), data.get("run_id"))
        self._send(200, json.dumps(out, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def do_HEAD(self) -> None:
        self.send_response(200)
        self.end_headers()

    def log_message(self, format: str, *args) -> None:
        return


def start_health(port: int) -> None:
    server = ThreadingHTTPServer(("0.0.0.0", port), _Health)
    threading.Thread(target=server.serve_forever, daemon=True, name="health").start()
    logger.info("Health+network su 0.0.0.0:%s node=%s", port, net.get_node_id())
    peers = net.get_network_peers()
    if peers:
        logger.info("NETWORK_PEERS: %s", ", ".join(peers))


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Errore non gestito: %s", context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "Qualcosa si è interrotto. Riprova; le letture e i registri già salvati restano disponibili."
        )


async def cmd_sdq(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    testo = " ".join(context.args or []).strip()
    if not testo:
        await update.message.reply_text("Uso: /sdq <testo>\nNucleo locale, zero agenti.")
        return
    out = await asyncio.to_thread(sdq1.ask, testo)
    await update.message.reply_text(out["risposta"][:3900])


async def on_testo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await corpo_tasto(update, context):
        return
    await messaggio_libero(update, context)


async def post_init(application: Application) -> None:
    webhook = await application.bot.get_webhook_info()
    if webhook.url:
        raise RuntimeError("Webhook già attivo. Completare il passaggio al polling prima di avviare questo processo.")
    await application.bot.set_my_commands(COMMANDS)
    await application.bot.set_my_description(
        "Raffaello · Rosso Rosso Rosso. Domande libere, letture Alpha 74 e progetti. "
        "Scrivi, premi Analizza e continua lo stesso dialogo sul sito. Claudio Terzi · C.Terzi."
    )
    await application.bot.set_my_short_description("Raffaello · Rosso Rosso Rosso · Claudio Terzi")
    me = await application.bot.get_me()
    logger.info("Collegato come @%s. Polling.", me.username)


def build_application() -> Application:
    token = require_token()
    init_db()
    raffaello_store.init()
    persistence = PicklePersistence(filepath=PERSISTENCE_PATH)
    app = (
        Application.builder()
        .token(token)
        .persistence(persistence)
        .post_init(post_init)
        .build()
    )
    legacy_handlers = [build_palestra_conversation(), build_libro_conversation(),
                       build_scacchiera_conversation(), *build_terzo_conversations(),
                       *build_conversation_handlers()]
    for handler in legacy_handlers:
        if isinstance(handler, ConversationHandler):
            handler.fallbacks.insert(0, CommandHandler("nuovo", raffaello.new))
        app.add_handler(handler)
    for h in raffaello.handlers():
        app.add_handler(h)
    for h in build_command_handlers():
        app.add_handler(h)
    app.add_handler(CommandHandler("scheda", cmd_scheda))
    app.add_handler(CommandHandler("misura", cmd_misura))
    app.add_handler(CommandHandler("misure", cmd_misure))
    app.add_handler(CommandHandler("rrr", cmd_rrr))
    app.add_handler(CommandHandler("metodo", cmd_metodo))
    app.add_handler(CommandHandler("corpo", cmd_corpo))
    app.add_handler(CommandHandler("sdq", cmd_sdq))
    for h in scacchiera_command_handlers():
        app.add_handler(h)
    app.add_handler(MessageHandler(filters.Regex(f"^{CHIUDI}$"), cmd_chiudi_menu))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_testo))
    app.add_handler(MessageHandler(filters.COMMAND, cmd_unknown))
    app.add_error_handler(on_error)
    return app


def main() -> None:
    app = build_application()
    port = os.getenv("PORT")
    if port:
        start_health(int(port))
    logger.info("Long polling. Ctrl+C per fermare.")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=False)


if __name__ == "__main__":
    main()
