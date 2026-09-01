/* La Soglia — velo d'ingresso del sito.
   Chiede la parola una volta per browser (localStorage).
   Nota di coscienza: è una soglia rituale, non una cassaforte —
   il contenuto resta nel repository pubblico. */
(function () {
  var ATTESO = "8d81f19b997ea6e0e4032eb9b33d8cbeb488aa4dd98ac932610bc31d923183ff";
  var CHIAVE = "soglia_terzi";

  try {
    if (localStorage.getItem(CHIAVE) === ATTESO) return;
  } catch (e) { /* storage negato: si chiede a ogni visita */ }

  document.documentElement.style.visibility = "hidden";

  function sha256hex(testo) {
    var dati = new TextEncoder().encode(testo);
    return crypto.subtle.digest("SHA-256", dati).then(function (buf) {
      return Array.from(new Uint8Array(buf))
        .map(function (b) { return b.toString(16).padStart(2, "0"); }).join("");
    });
  }

  function apri(velo) {
    try { localStorage.setItem(CHIAVE, ATTESO); } catch (e) {}
    velo.remove();
    document.body.style.overflow = "";
  }

  function mostra() {
    document.documentElement.style.visibility = "";
    var velo = document.createElement("div");
    velo.setAttribute("style",
      "position:fixed;inset:0;z-index:99999;background:#0c0c0e;" +
      "display:flex;align-items:center;justify-content:center;" +
      "font-family:Georgia,'Times New Roman',serif;");
    velo.innerHTML =
      '<div style="text-align:center;padding:2rem;max-width:420px;width:100%">' +
      '<div style="font-size:0.7rem;letter-spacing:0.35em;color:#8a6f2e;' +
      'text-transform:uppercase">Terzi &middot; Claudio</div>' +
      '<div style="font-size:2rem;color:#c9a84c;letter-spacing:0.12em;' +
      'margin:1rem 0 0.4rem">La Soglia</div>' +
      '<div style="color:#7a7468;font-style:italic;font-size:0.9rem;' +
      'margin-bottom:1.6rem">Di&rsquo; la parola.</div>' +
      '<input id="soglia-parola" type="password" autocomplete="off" ' +
      'style="background:#141418;border:1px solid #2a2a32;color:#e8e4d8;' +
      'border-radius:8px;padding:0.6rem 1rem;width:100%;font-family:inherit;' +
      'font-size:1rem;text-align:center;letter-spacing:0.2em;outline:none">' +
      '<div><button id="soglia-entra" style="margin-top:1rem;background:none;' +
      'border:1px solid #8a6f2e;color:#c9a84c;border-radius:999px;' +
      'padding:0.45rem 1.6rem;font-family:inherit;font-size:0.9rem;' +
      'letter-spacing:0.1em;cursor:pointer">Entra</button></div>' +
      '<div id="soglia-msg" style="min-height:1.4em;margin-top:0.9rem;' +
      'color:#8b1c1c;font-size:0.85rem;font-style:italic"></div>' +
      '</div>';
    document.body.appendChild(velo);
    document.body.style.overflow = "hidden";

    var input = velo.querySelector("#soglia-parola");
    var msg = velo.querySelector("#soglia-msg");

    function prova() {
      var parola = input.value.trim().toLowerCase();
      if (!parola) return;
      var verifica = (crypto && crypto.subtle)
        ? sha256hex(parola)
        : Promise.resolve(parola === atob("YWxha3Rh") ? ATTESO : "");
      verifica.then(function (h) {
        if (h === ATTESO) { apri(velo); }
        else {
          msg.textContent = "Non è la parola.";
          input.value = "";
          input.focus();
        }
      });
    }

    velo.querySelector("#soglia-entra").addEventListener("click", prova);
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter") prova();
    });
    input.focus();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mostra);
  } else {
    mostra();
  }
})();
