"""Mini App API, independent from the existing private site bridge."""
from __future__ import annotations

from pathlib import Path
import re

from bot import config as bot_config, music_backup as persistence, music_service as service, music_store as store
from bot.music_auth import MusicError, is_owner, validate_init_data


def authenticate(headers):
    return validate_init_data(headers.get("X-Telegram-Init-Data"), bot_config.TELEGRAM_BOT_TOKEN)


def dispatch(method, path, headers, body, viewer=None):
    viewer = authenticate(headers) if viewer is None else viewer
    actor = viewer["id"]
    if method == "GET" and path == "/session":
        return {"viewer": {"first_name": viewer["first_name"], "is_owner": is_owner(actor)}, "mode": "assisted"}
    persistence.mutate(store.recover_expired)
    if method == "GET" and path == "/requests":
        return {"requests": persistence.mutate(store.list_requests, actor)}
    if method == "GET" and path == "/library":
        return {"songs": persistence.mutate(store.list_requests, actor, library=True)}
    if method == "POST" and path == "/requests":
        return {"request": service.create_request(actor, body)}
    match = re.fullmatch(r"/requests/([0-9a-fA-F-]{36})(?:/(prepare|result|keep|discard|retry))?", path)
    if not match:
        raise MusicError("Percorso non disponibile.", 404, "not_found")
    rid, action = store.request_id(match[1]), match[2]
    if method == "GET" and action is None:
        return {"request": persistence.mutate(store.get, actor, rid)}
    if method == "POST" and action:
        if action != "result" and body:
            raise MusicError("Questa operazione non accetta altri campi.")
        if action == "prepare":
            request = service.start_prepare(actor, rid)
        elif action == "result":
            request = service.result(actor, rid, body)
        elif action == "retry":
            request = service.retry(actor, rid)
        else:
            request = persistence.mutate(store.decide, actor, rid, keep=action == "keep")
        return {"request": request}
    raise MusicError("Metodo non disponibile.", 405, "method_not_allowed")


def static_asset(path):
    names = {"/studio": ("index.html", "text/html; charset=utf-8"),
             "/studio/": ("index.html", "text/html; charset=utf-8"),
             "/studio/studio.js": ("studio.js", "application/javascript; charset=utf-8"),
             "/studio/studio.css": ("studio.css", "text/css; charset=utf-8"),
             "/studio/musica-data.js": ("musica-data.js", "application/javascript; charset=utf-8")}
    asset = names.get(path)
    if asset is None:
        raise MusicError("Risorsa non disponibile.", 404, "not_found")
    target = Path(__file__).resolve().parent / "studio_static" / asset[0]
    if asset[0] == "musica-data.js":
        target = Path(__file__).resolve().parents[3] / "public/musica-data.js"
    try:
        if target.stat().st_size > 2 * 1024 * 1024:
            raise MusicError("Risorsa non disponibile.", 503, "asset_unavailable")
        return target.read_bytes(), asset[1]
    except OSError as exc:
        raise MusicError("Lo Studio non è ancora disponibile.", 503, "asset_unavailable") from exc
