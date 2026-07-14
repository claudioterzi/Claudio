"""Interfaccia web CUSTODE — schede oggetti + il bottone "Analizza mancanti".

In locale:   python -m custode.web   →  http://localhost:5001/custode
Su Vercel:   montata da tarocchi_web.py sotto /custode (stesso progetto
             dei Tarocchi). Variabili d'ambiente in produzione:
             CUSTODE_PASSWORD  — login (obbligatoria online)
             ANTHROPIC_API_KEY — visione per la schedatura a due foto
             REDIS_URL         — persistenza del catalogo (es. Upstash)

- Schedatura rapida: foto al frontespizio + foto al tag → scheda
  precompilata dalla visione, da controllare e salvare.
- Inventario: EPC letti dal palmare → bottone → analisi mancanti.
"""

import os
import tempfile

from flask import (Blueprint, Flask, redirect, render_template_string,
                   request, session, url_for)

from custode.archivio import crea_archivio
from custode.catalogo import Catalogo, SchedaOggetto
from custode.schedatura import crea_schedatore

PERCORSO_CATALOGO = os.environ.get(
    "CUSTODE_CATALOGO", os.path.join("output", "catalogo_custode.json"))

custode_bp = Blueprint("custode", __name__)
catalogo = Catalogo(archivio=crea_archivio(PERCORSO_CATALOGO))
schedatore = crea_schedatore()

PAGINA = """<!doctype html><html lang="it"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CUSTODE — Catalogo e inventario</title><style>
 body{font-family:Georgia,serif;max-width:880px;margin:2rem auto;padding:0 1rem;
      background:#f4f1ea;color:#2b2b2b}
 h1{font-style:italic} h2{border-bottom:2px solid #b3532e;padding-bottom:.2rem}
 table{width:100%;border-collapse:collapse;background:#fff}
 td,th{border:1px solid #ddd;padding:.4rem .6rem;text-align:left;font-size:.95rem}
 form.scheda{display:grid;grid-template-columns:1fr 1fr;gap:.5rem;background:#fff;
      padding:1rem;border:1px solid #ddd}
 input,textarea,select{padding:.4rem;border:1px solid #bbb;font:inherit;width:100%;
      box-sizing:border-box}
 .largo{grid-column:1 / -1}
 button{background:#b3532e;color:#fff;border:0;padding:.7rem 1.4rem;font:inherit;
      cursor:pointer} button:hover{background:#8f4225}
 .bottone-inventario{font-size:1.15rem;font-weight:bold;width:100%}
 .mancante{background:#fde8e8} .ok{color:#2e7d32}
 .esito{background:#fff;border:2px solid #b3532e;padding:1rem;white-space:pre-wrap;
      font-family:monospace}
 .avviso{background:#fff3cd;border:1px solid #d9b64c;padding:.6rem 1rem}
</style></head><body>
<h1>CUSTODE · Catalogo &amp; Inventario</h1>
{% if effimero %}<p class="avviso">⚠ Archivio temporaneo: le schede si perdono
al riavvio. Configura <code>REDIS_URL</code> su Vercel (Upstash, gratuito).</p>
{% endif %}

{% if esito %}<h2>Esito inventario</h2>
<div class="esito">{{ esito }}</div>
<p><a href="{{ url_for('custode.home') }}">← torna al catalogo</a></p>
{% else %}

<h2>Inventario ({{ schede|length }} oggetti a catalogo)</h2>
<form method="post" action="{{ url_for('custode.inventario') }}">
 <p>EPC letti dal palmare — uno per riga (in v2 arrivano dal lettore Bluetooth):</p>
 <textarea name="epc_letti" rows="5" placeholder="E280-0001&#10;E280-0002"></textarea>
 <p><button class="bottone-inventario" type="submit">🔍 ANALIZZA OGGETTI MANCANTI</button></p>
</form>

<h2>Schede</h2>
<table><tr><th>Categoria</th><th>Nome</th><th>Dettagli</th><th>Zona</th>
<th>Valore €</th><th>Tag nascosto</th><th>EPC</th></tr>
{% for s in schede %}
<tr><td>{{ s.categoria }}</td><td><b>{{ s.nome }}</b></td>
<td>{% for k, v in s.campi.items() %}{{ k }}: {{ v }}<br>{% endfor %}{{ s.note }}</td>
<td>{{ s.zona_id }}</td><td>{{ "%.2f"|format(s.valore_eur) }}</td>
<td>{{ s.posizione_tag }}</td><td><code>{{ s.epc }}</code></td></tr>
{% endfor %}</table>

<h2>📷 Schedatura rapida — due foto e basta</h2>
<p>Foto 1: frontespizio del libro (o l'oggetto). Foto 2: il tag prima di
nasconderlo. La scheda si compila da sola — controlla e salva.</p>
<form class="scheda" method="post" action="{{ url_for('custode.schedatura') }}"
      enctype="multipart/form-data">
 <label>1 · Frontespizio / oggetto<br>
  <input type="file" name="foto_oggetto" accept="image/*" capture="environment" required></label>
 <label>2 · Tag RFID<br>
  <input type="file" name="foto_tag" accept="image/*" capture="environment"></label>
 <button class="largo" type="submit">📷 Crea scheda dalle foto</button>
</form>

<h2>Scheda {{ "precompilata — controlla e salva" if pre else "manuale" }}</h2>
<form class="scheda" method="post" action="{{ url_for('custode.nuova_scheda') }}">
 <input name="epc" placeholder="EPC del tag (obbligatorio)" required
        value="{{ pre.get('epc','') }}">
 <select name="categoria">
  {% for c in ["libro","elettronica","biancheria","arredo","cucina","oggetto"] %}
  <option value="{{ c }}" {{ "selected" if pre.get("categoria")==c }}>{{ c }}</option>
  {% endfor %}
 </select>
 <input class="largo" name="nome" placeholder="Nome / titolo (obbligatorio)" required
        value="{{ pre.get('nome','') }}">
 <input name="autore" placeholder="Autore (per i libri)"
        value="{{ pre.get('autore','') }}">
 <input name="isbn" placeholder="ISBN (per i libri)"
        value="{{ pre.get('isbn','') }}">
 <input name="zona_id" placeholder="Zona, es. soggiorno/libreria-ripiano-2"
        value="{{ pre.get('zona_id','') }}">
 <input name="valore_eur" type="number" step="0.01" min="0" placeholder="Valore €"
        value="{{ pre.get('valore_eur','') }}">
 <input class="largo" name="posizione_tag"
        placeholder="Dove è nascosto il tag, es. incollato tra pagina 142 e 143"
        value="{{ pre.get('posizione_tag','') }}">
 <textarea class="largo" name="note" rows="2"
        placeholder="Note">{{ pre.get('note','') }}</textarea>
 <button class="largo" type="submit">Salva scheda</button>
</form>
{% endif %}
</body></html>"""

LOGIN = """<!doctype html><html lang="it"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CUSTODE — Accesso</title><style>
 body{font-family:Georgia,serif;max-width:400px;margin:4rem auto;padding:0 1rem;
      background:#f4f1ea;color:#2b2b2b;text-align:center}
 input,button{padding:.7rem;font:inherit;width:100%;box-sizing:border-box;margin:.3rem 0}
 button{background:#b3532e;color:#fff;border:0;cursor:pointer}
</style></head><body>
<h1><i>CUSTODE</i></h1>
{% if errore %}<p style="color:#b3532e">Password errata.</p>{% endif %}
<form method="post">
 <input type="password" name="password" placeholder="Password" autofocus required>
 <button type="submit">Entra</button>
</form></body></html>"""


def _pagina(**kwargs):
    kwargs.setdefault("schede", catalogo.tutte())
    kwargs.setdefault("esito", None)
    kwargs.setdefault("pre", {})
    kwargs.setdefault("effimero", getattr(catalogo.archivio, "effimero", False))
    return render_template_string(PAGINA, **kwargs)


@custode_bp.before_request
def _controllo_accesso():
    password = os.environ.get("CUSTODE_PASSWORD")
    if not password or session.get("custode_auth"):
        return None
    if request.method == "POST" and request.endpoint == "custode.home":
        if request.form.get("password") == password:
            session["custode_auth"] = True
            return redirect(url_for("custode.home"))
        return render_template_string(LOGIN, errore=True)
    return render_template_string(LOGIN, errore=False)


@custode_bp.route("/", methods=["GET", "POST"])
def home():
    return _pagina()


@custode_bp.route("/schedatura", methods=["POST"])
def schedatura():
    """Due foto → scheda precompilata dalla visione, da controllare e salvare."""
    def _salva_upload(nome_campo):
        f = request.files.get(nome_campo)
        if not f or not f.filename:
            return None
        suffisso = os.path.splitext(f.filename)[1] or ".jpg"
        percorso = tempfile.mktemp(suffix=suffisso)
        f.save(percorso)
        return percorso

    pre = {}
    foto_oggetto = _salva_upload("foto_oggetto")
    foto_tag = _salva_upload("foto_tag")
    try:
        if foto_oggetto:
            dati = schedatore.scheda_da_foto(foto_oggetto)
            campi = dati.get("campi", {})
            pre = {
                "nome": dati.get("nome", ""),
                "categoria": dati.get("categoria", "oggetto"),
                "autore": campi.get("autore", ""),
                "isbn": campi.get("isbn", ""),
                "valore_eur": dati.get("valore_eur", ""),
                "note": dati.get("note", ""),
            }
        if foto_tag:
            pre["epc"] = schedatore.epc_da_foto(foto_tag)
    finally:
        for p in (foto_oggetto, foto_tag):
            if p and os.path.exists(p):
                os.remove(p)
    return _pagina(pre=pre)


@custode_bp.route("/scheda", methods=["POST"])
def nuova_scheda():
    campi = {k: request.form[k].strip()
             for k in ("autore", "isbn") if request.form.get(k, "").strip()}
    catalogo.aggiungi(SchedaOggetto(
        epc=request.form["epc"].strip(),
        nome=request.form["nome"].strip(),
        categoria=request.form.get("categoria", "oggetto"),
        zona_id=request.form.get("zona_id", "").strip(),
        valore_eur=float(request.form.get("valore_eur") or 0),
        posizione_tag=request.form.get("posizione_tag", "").strip(),
        note=request.form.get("note", "").strip(),
        campi=campi,
    ))
    return redirect(url_for("custode.home"))


@custode_bp.route("/inventario", methods=["POST"])
def inventario():
    epc_letti = {r.strip() for r in request.form.get("epc_letti", "").splitlines()
                 if r.strip()}
    risultato = catalogo.analizza_mancanti(epc_letti)
    return _pagina(esito=risultato.testo())


def registra_custode(app: Flask, prefisso: str = "/custode") -> None:
    """Monta CUSTODE su un'app Flask esistente (usato da tarocchi_web.py)."""
    if not app.secret_key:
        app.secret_key = os.environ.get(
            "SECRET_KEY", os.environ.get("CUSTODE_PASSWORD", "custode-dev"))
    app.register_blueprint(custode_bp, url_prefix=prefisso)


if __name__ == "__main__":
    app = Flask(__name__)
    registra_custode(app)
    app.run(host="0.0.0.0", port=5001, debug=False)
