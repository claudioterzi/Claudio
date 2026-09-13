"""Voice endpoint for Canone Alpha 74.

Keeps provider credentials server-side and provides automatic failover between
Azure Speech, ElevenLabs and OpenAI TTS. The public route remains
/api/tarocchi/alpha-voce so the existing Tarot UI does not need to change.

Azure is intentionally supported as the cheapest primary path: the Speech F0
resource includes a monthly free neural TTS allowance and can be selected with
TAROT_TTS_PROVIDER=azure. Credentials never reach the browser.
"""

from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape

from flask import Flask, Response, jsonify, request


app = Flask(__name__)


def _clean(value, limit=400):
    if value is None:
        return ""
    return str(value).strip()[:limit]


def _language(value):
    language = _clean(value, 10).lower()
    return language if language in {"it", "en", "fr", "es"} else "it"


def _truthy_env(name, default=True):
    raw = _clean(os.getenv(name), 20).lower()
    if not raw:
        return default
    return raw not in {"0", "false", "no", "off"}


def _openai_ready():
    return bool(_clean(os.getenv("OPENAI_API_KEY"), 320))


def _elevenlabs_ready():
    return bool(
        _clean(os.getenv("ELEVENLABS_API_KEY"), 320)
        and _clean(os.getenv("ELEVENLABS_VOICE_ID"), 160)
    )


def _azure_ready():
    return bool(
        _clean(os.getenv("AZURE_SPEECH_KEY"), 320)
        and _clean(os.getenv("AZURE_SPEECH_REGION"), 80)
    )


def _provider_order():
    requested = _clean(os.getenv("TAROT_TTS_PROVIDER", "auto"), 40).lower()
    configured = []
    if _azure_ready():
        configured.append("azure")
    if _elevenlabs_ready():
        configured.append("elevenlabs")
    if _openai_ready():
        configured.append("openai")

    if requested == "azure":
        order = ["azure", "elevenlabs", "openai"]
    elif requested == "elevenlabs":
        order = ["elevenlabs", "azure", "openai"]
    elif requested == "openai":
        # Preserve the explicit OpenAI preference, but still fail over to the
        # free Azure tier when OpenAI is unavailable or out of credit.
        order = ["openai", "azure", "elevenlabs"]
    else:
        # In auto mode prefer the lowest expected running cost first.
        order = ["azure", "elevenlabs", "openai"]

    order = [provider for provider in order if provider in configured]
    if not _truthy_env("TAROT_TTS_FAILOVER", True) and order:
        order = order[:1]
    return order, configured, requested or "auto"


def _error_code_from_http(exc):
    try:
        payload = exc.read(4096)
        parsed = json.loads(payload.decode("utf-8", errors="replace"))
        error = parsed.get("error") if isinstance(parsed, dict) else None
        if isinstance(error, dict):
            return _clean(error.get("code") or error.get("type"), 120) or None
        if isinstance(parsed, dict):
            return _clean(parsed.get("code") or parsed.get("errorCode"), 120) or None
    except Exception:
        pass
    return None


def _instructions(language):
    custom = _clean(os.getenv("OPENAI_TTS_INSTRUCTIONS"), 1200)
    if custom:
        return custom
    return {
        "it": (
            "Parla in italiano con voce naturale, moderna, calda, fluida e autorevole. "
            "Usa pause brevi e intenzionali, dizione chiara, ritmo calmo e mai robotico. "
            "Per una lettura dei Tarocchi mantieni presenza, eleganza e discrezione, senza teatralità eccessiva."
        ),
        "en": (
            "Speak in natural English with a modern, warm, fluid and authoritative voice. "
            "Use brief intentional pauses, clear diction and a calm, non-robotic pace."
        ),
        "fr": (
            "Parle en français avec une voix naturelle, moderne, chaleureuse, fluide et assurée. "
            "Utilise des pauses brèves, une diction claire et un rythme calme, jamais robotique."
        ),
        "es": (
            "Habla en español con una voz natural, moderna, cálida, fluida y segura. "
            "Usa pausas breves, dicción clara y un ritmo sereno, nunca robótico."
        ),
    }.get(language, "Speak naturally, clearly, warmly and at a calm pace.")


def _azure_voice(language):
    env_voice = _clean(os.getenv("AZURE_TTS_VOICE"), 120)
    if env_voice:
        return env_voice
    return {
        "it": "it-IT-DiegoNeural",
        "en": "en-US-GuyNeural",
        "fr": "fr-FR-HenriNeural",
        "es": "es-ES-AlvaroNeural",
    }.get(language, "it-IT-DiegoNeural")


def _azure_audio(text, language):
    api_key = _clean(os.getenv("AZURE_SPEECH_KEY"), 320)
    region = _clean(os.getenv("AZURE_SPEECH_REGION"), 80).lower()
    if not api_key or not region:
        return None, {"provider": "azure", "reason": "not_configured"}

    voice = _azure_voice(language)
    locale = {
        "it": "it-IT",
        "en": "en-US",
        "fr": "fr-FR",
        "es": "es-ES",
    }.get(language, "it-IT")
    safe_text = escape(text)
    rate = _clean(os.getenv("AZURE_TTS_RATE"), 24) or "-7%"
    pitch = _clean(os.getenv("AZURE_TTS_PITCH"), 24) or "-1st"
    ssml = (
        f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
        f'xml:lang="{locale}"><voice name="{escape(voice)}">'
        f'<prosody rate="{escape(rate)}" pitch="{escape(pitch)}">'
        f'{safe_text}</prosody></voice></speak>'
    ).encode("utf-8")

    endpoint = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
    output_format = (
        _clean(os.getenv("AZURE_TTS_OUTPUT_FORMAT"), 120)
        or "audio-24khz-160kbitrate-mono-mp3"
    )
    remote_request = Request(
        endpoint,
        data=ssml,
        headers={
            "Accept": "audio/mpeg",
            "Content-Type": "application/ssml+xml",
            "Ocp-Apim-Subscription-Key": api_key,
            "User-Agent": "Raffaello-Alpha74",
            "X-Microsoft-OutputFormat": output_format,
        },
        method="POST",
    )

    try:
        with urlopen(remote_request, timeout=30) as remote_response:
            audio = remote_response.read(8_000_001)
    except HTTPError as exc:
        return None, {
            "provider": "azure",
            "status": int(exc.code),
            "code": _error_code_from_http(exc),
        }
    except (URLError, TimeoutError, OSError):
        return None, {"provider": "azure", "reason": "transport_error"}

    if not audio:
        return None, {"provider": "azure", "reason": "empty_audio"}
    if len(audio) > 8_000_000:
        return None, {"provider": "azure", "reason": "audio_too_large"}
    return audio, None


def _openai_audio(text, language):
    api_key = _clean(os.getenv("OPENAI_API_KEY"), 320)
    if not api_key:
        return None, {"provider": "openai", "reason": "not_configured"}

    custom_voice_id = _clean(os.getenv("OPENAI_CUSTOM_VOICE_ID"), 160)
    voice = {"id": custom_voice_id} if custom_voice_id else (
        _clean(os.getenv("OPENAI_TTS_VOICE"), 80) or "marin"
    )
    model = _clean(os.getenv("OPENAI_TTS_MODEL"), 120) or "gpt-4o-mini-tts"

    payload = json.dumps(
        {
            "model": model,
            "input": text,
            "voice": voice,
            "instructions": _instructions(language),
            "response_format": "mp3",
        },
        ensure_ascii=False,
    ).encode("utf-8")

    remote_request = Request(
        "https://api.openai.com/v1/audio/speech",
        data=payload,
        headers={
            "Accept": "audio/mpeg",
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(remote_request, timeout=30) as remote_response:
            audio = remote_response.read(8_000_001)
    except HTTPError as exc:
        return None, {
            "provider": "openai",
            "status": int(exc.code),
            "code": _error_code_from_http(exc),
        }
    except (URLError, TimeoutError, OSError):
        return None, {"provider": "openai", "reason": "transport_error"}

    if not audio:
        return None, {"provider": "openai", "reason": "empty_audio"}
    if len(audio) > 8_000_000:
        return None, {"provider": "openai", "reason": "audio_too_large"}
    return audio, None


def _elevenlabs_audio(text):
    api_key = _clean(os.getenv("ELEVENLABS_API_KEY"), 320)
    voice_id = quote(_clean(os.getenv("ELEVENLABS_VOICE_ID"), 160), safe="")
    if not api_key or not voice_id:
        return None, {"provider": "elevenlabs", "reason": "not_configured"}

    model_id = _clean(os.getenv("ELEVENLABS_MODEL_ID"), 120) or "eleven_multilingual_v2"
    endpoint = (
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        "?output_format=mp3_44100_128"
    )
    payload = json.dumps(
        {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": 0.42,
                "similarity_boost": 0.82,
                "style": 0.18,
                "use_speaker_boost": True,
            },
        },
        ensure_ascii=False,
    ).encode("utf-8")

    remote_request = Request(
        endpoint,
        data=payload,
        headers={
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key,
        },
        method="POST",
    )

    try:
        with urlopen(remote_request, timeout=30) as remote_response:
            audio = remote_response.read(8_000_001)
    except HTTPError as exc:
        return None, {
            "provider": "elevenlabs",
            "status": int(exc.code),
            "code": _error_code_from_http(exc),
        }
    except (URLError, TimeoutError, OSError):
        return None, {"provider": "elevenlabs", "reason": "transport_error"}

    if not audio:
        return None, {"provider": "elevenlabs", "reason": "empty_audio"}
    if len(audio) > 8_000_000:
        return None, {"provider": "elevenlabs", "reason": "audio_too_large"}
    return audio, None


def _status_payload():
    order, configured, requested = _provider_order()
    return {
        "disponibile": bool(order),
        "provider": order[0] if order else None,
        "providers_configured": configured,
        "provider_order": order,
        "requested": requested,
        "failover": len(order) > 1,
        "fallback": "browser-speech-synthesis",
    }


def _handle_voice():
    if request.method == "OPTIONS":
        return "", 204

    if request.method == "GET":
        response = jsonify(_status_payload())
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"errore": "Serve un oggetto JSON."}), 400

    raw_text = body.get("testo") or body.get("text")
    if not isinstance(raw_text, str) or not raw_text.strip():
        return jsonify({"errore": "Serve il testo da leggere."}), 400

    text = raw_text.strip()
    # Keep a common ceiling that is safe for the current provider mix.
    if len(text) > 4096:
        return (
            jsonify(
                {
                    "errore": "Il testo vocale supera il limite del provider.",
                    "max_chars": 4096,
                    "fallback": "browser-speech-synthesis",
                }
            ),
            413,
        )

    language = _language(body.get("lingua") or body.get("language"))
    order, configured, requested = _provider_order()
    if not order:
        return (
            jsonify(
                {
                    "errore": "Nessun provider vocale server-side è configurato.",
                    "providers_configured": configured,
                    "requested": requested,
                    "fallback": "browser-speech-synthesis",
                }
            ),
            503,
        )

    attempts = []
    for provider in order:
        if provider == "azure":
            audio, error = _azure_audio(text, language)
        elif provider == "openai":
            audio, error = _openai_audio(text, language)
        else:
            audio, error = _elevenlabs_audio(text)

        if audio is not None:
            response = Response(audio, mimetype="audio/mpeg")
            response.headers["Cache-Control"] = "no-store"
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Voice-Provider"] = provider
            response.headers["X-Voice-Failover"] = "1" if attempts else "0"
            return response
        if error:
            attempts.append(error)

    # Safe diagnostics: provider/status/error code only, never credentials or
    # upstream bodies. This lets Vercel logs distinguish auth/quota failures
    # from network failures without exposing API keys.
    print("alpha_voice_failure=" + json.dumps(attempts, ensure_ascii=False))
    return (
        jsonify(
            {
                "errore": "La voce esterna non è disponibile.",
                "attempts": attempts,
                "fallback": "browser-speech-synthesis",
            }
        ),
        503,
    )


@app.route("/api/tarocchi/alpha-voce", methods=["GET", "POST", "OPTIONS"])
def alpha_voice():
    return _handle_voice()


@app.route("/", methods=["GET", "POST", "OPTIONS"])
def root():
    return _handle_voice()
