from pathlib import Path
import json
import urllib.request

SENTINEL = Path(".ntfy_raffaello_test_sent")

def test_send_raffaello_crypto_ntfy_smoke():
    if SENTINEL.exists():
        return
    body = (
        "✅ TEST RAFFAELLO CRYPTO\n"
        "Canale operativo collegato.\n"
        "Origine: GitHub CI → ntfy → iPhone\n"
        "Questo è un test reale, non un ordine di trading."
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://ntfy.sh/raffaellocrypto",
        data=body,
        method="POST",
        headers={
            "Title": "RaffaelloCrypto · TEST REALE",
            "Priority": "high",
            "Tags": "white_check_mark,chart_with_upwards_trend",
            "Content-Type": "text/plain; charset=utf-8",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        payload = resp.read().decode("utf-8", errors="replace")
        print("NTFY_RESPONSE_STATUS", resp.status)
        print("NTFY_RESPONSE_BODY", payload)
        assert resp.status == 200
        parsed = json.loads(payload)
        assert parsed.get("topic") == "raffaellocrypto"
    SENTINEL.write_text("sent\n", encoding="utf-8")
