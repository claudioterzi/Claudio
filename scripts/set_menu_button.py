"""Imposta il Menu Button del bot Raffaello su Telegram.

Uso:
    python scripts/set_menu_button.py --url https://tuodominio.vercel.app/home
    python scripts/set_menu_button.py --url https://tuodominio.vercel.app/home --title "Agorà SDQ-1"
    python scripts/set_menu_button.py --status   # mostra menu button attuale
    python scripts/set_menu_button.py --reset    # ripristina menu button default
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path


def _carica_dotenv() -> None:
    env = Path(__file__).resolve().parent.parent / ".env"
    if not env.exists():
        return
    with env.open() as f:
        for riga in f:
            riga = riga.strip()
            if not riga or riga.startswith("#") or "=" not in riga:
                continue
            k, _, v = riga.partition("=")
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v


def _api(token: str, method: str, payload: dict | None = None) -> dict:
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = json.dumps(payload or {}).encode() if payload else b"{}"
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"HTTP {e.code}: {body}")
        sys.exit(1)


def main() -> None:
    _carica_dotenv()

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN non trovato nel .env")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Configura Menu Button bot Raffaello")
    parser.add_argument("--url",    help="URL HTTPS della Mini App (es. https://xyz.vercel.app/home)")
    parser.add_argument("--title",  default="Agorà SDQ-1", help="Testo del pulsante (default: Agorà SDQ-1)")
    parser.add_argument("--status", action="store_true", help="Mostra menu button attuale")
    parser.add_argument("--reset",  action="store_true", help="Ripristina menu button default")
    args = parser.parse_args()

    if args.status:
        r = _api(token, "getChatMenuButton", {"chat_id": os.environ.get("TELEGRAM_CHAT_ID", "")})
        print("📋 Menu button attuale:")
        print(json.dumps(r.get("result", {}), indent=2, ensure_ascii=False))
        return

    if args.reset:
        r = _api(token, "setChatMenuButton", {"menu_button": {"type": "default"}})
        if r.get("result"):
            print("✅ Menu button ripristinato al default")
        else:
            print(f"❌ Errore: {r}")
        return

    if not args.url:
        parser.print_help()
        print("\n⚠️  Specifica --url oppure --status / --reset")
        sys.exit(1)

    if not args.url.startswith("https://"):
        print("❌ L'URL deve essere HTTPS (Telegram richiede https://)")
        sys.exit(1)

    payload = {
        "menu_button": {
            "type": "web_app",
            "text": args.title,
            "web_app": {"url": args.url},
        }
    }
    r = _api(token, "setChatMenuButton", payload)
    if r.get("result"):
        print(f"✅ Menu button impostato!")
        print(f"   URL:   {args.url}")
        print(f"   Testo: {args.title}")
        print()
        print("Ora nel bot Raffaello compare il pulsante 📱 in basso.")
    else:
        print(f"❌ Errore: {r}")


if __name__ == "__main__":
    main()
