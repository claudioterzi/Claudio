"""Standalone Studio: shared bot identity for outbound messages/menu, never polling.

Run: python -m bot.music_main. This preserves the existing bot's sole update receiver.
SQLite uses DATABASE_PATH; a local ephemeral filesystem does not make it durable.
"""
from __future__ import annotations

import asyncio
from http.server import ThreadingHTTPServer
import json
import os
import signal
import threading

from telegram.ext import Application

from bot.config import require_token
from bot import db, music_backup, music_bot, music_service, music_store
from bot.main import _Health


class StudioHTTP(_Health):
    def do_GET(self):
        path = (self.path or "/").split("?", 1)[0]
        if path in ("/", "/health"):
            payload = {"service": "raffaello-studio", "mode": "assisted", "update_receiver": False,
                       "storage": "sqlite", "storage_backup": music_backup.status(),
                       "commit": os.getenv("RENDER_GIT_COMMIT", "unknown")}
            self._send(200, json.dumps(payload).encode(), "application/json")
        elif path == "/studio" or path.startswith(("/studio/", "/music/v1/")):
            super().do_GET()
        else:
            self._send(404, b'{"error":"not_found"}', "application/json")

    def do_POST(self):
        if (self.path or "").split("?", 1)[0].startswith("/music/v1/"):
            super().do_POST()
        else:
            self._send(404, b'{"error":"not_found"}', "application/json")

    def do_DELETE(self):
        self._send(405, b'{"error":"method_not_allowed"}', "application/json")


async def run(application=None, port=None, stop_event=None):
    db.init_db()
    music_store.init()
    app = application
    if app is None:
        try:
            token = require_token()
        except RuntimeError:
            token = ""
        if token:
            app = Application.builder().token(token).build()
    stop = stop_event if stop_event is not None else asyncio.Event()
    loop = asyncio.get_running_loop()
    if stop_event is None:
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, stop.set)
            except (NotImplementedError, RuntimeError):
                pass
    server = None
    initialized = started = False
    try:
        if app is not None:
            await app.initialize()
            initialized = True
            await app.start()  # Starts application tasks; Updater.start_polling is never called.
            started = True
            me = await app.bot.get_me()
            music_service.set_bot_username(me.username)
            try:
                await music_backup.startup(app.bot)
                await asyncio.to_thread(music_backup.mutate, music_store.recover_after_restart)
            except music_backup.BackupError:
                music_service.set_notifier(None)  # UI/config survive; writes remain closed until verified restore.
            else:
                await music_bot.attach(app, me.username, integrated=False)
        else:
            music_service.set_notifier(None)  # Public preview; signed APIs stay closed without a token.
        server = ThreadingHTTPServer(("0.0.0.0", int(os.getenv("PORT", "8080")) if port is None else port), StudioHTTP)
        worker = threading.Thread(target=server.serve_forever, daemon=True, name="studio-http")
        worker.start()
        await stop.wait()
    finally:
        if server is not None:
            await asyncio.to_thread(server.shutdown)
            server.server_close()
        music_service.set_notifier(None)
        if started:
            await app.stop()
        if initialized:
            await app.shutdown()


def main():
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
