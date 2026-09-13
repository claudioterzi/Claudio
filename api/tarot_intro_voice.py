from flask import Flask, Response, jsonify
from api import tarot_voice as voice

app = Flask(__name__)

TEXT = (
    "Questo è Alpha 74, il Canone originale ideato e disegnato da Claudio Terzi. "
    "Settantquattro carte originali. Ogni carta può essere osservata in quattro direzioni: Nord, Est, Sud e Ovest. "
    "Cambiando direzione cambia il punto di vista e cambia la funzione del simbolo. "
    "Ogni stato esiste poi in due polarità: Luce e Ombra. La Luce mostra ciò che emerge e si apre. "
    "L'Ombra mostra ciò che si ritrae, si complica o chiede di essere compreso. "
    "Per questo le settantaquattro carte diventano cinquecentonovantadue stati elementari. "
    "Nel carosello sei tu a scegliere la carta con il dito. La carta resta davanti a te finché vuoi. "
    "Puoi ruotarla nelle quattro direzioni e girarla dalla Luce all'Ombra. "
    "Con una stesa da una a sette carte, identità, ordine, direzione e polarità entrano realmente nella configurazione interpretata da Raffaello. "
    "Non settantaquattro risposte: un linguaggio."
)

@app.get("/")
@app.get("/api/tarocchi/alpha-presentazione-voce")
def presentation_voice():
    order, _, _ = voice._provider_order()
    errors = []
    for provider in order:
        if provider == "openai":
            audio, error = voice._openai_audio(TEXT, "it")
        else:
            audio, error = voice._elevenlabs_audio(TEXT)
        if audio:
            response = Response(audio, mimetype="audio/mpeg")
            response.headers["Cache-Control"] = "private, no-store"
            response.headers["X-Voice-Provider"] = provider
            response.headers["X-Content-Type-Options"] = "nosniff"
            return response
        if error:
            errors.append(error)
    return jsonify({"errore": "Voce non disponibile", "dettagli": errors}), 503
