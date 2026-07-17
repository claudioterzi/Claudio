/* La Costellazione — barra di navigazione comune a tutte le pagine.
   Una riga, oro su nero, pagina corrente evidenziata. Nascosta in stampa. */
(function () {
  var VOCI = [
    ["index.html", "Tarocchi"],
    ["alpha.html", "Alpha"],
    ["parfums.html", "Parfums"],
    ["organo.html", "Organo"],
    ["libro.html", "Libro"],
    ["atelier.html", "Atelier"],
    ["opera.html", "Opera"],
    ["creazioni.html", "Creazioni"],
    ["opuscolo.html", "Opuscolo"],
  ];
  var qui = location.pathname.split("/").pop() || "index.html";

  var stile = document.createElement("style");
  stile.textContent =
    ".nav-costellazione{text-align:center;padding:0.55rem 0.5rem 0.7rem;" +
    "border-bottom:1px solid #2a2a32;margin:-2rem -1rem 2rem;" +
    "font-family:Georgia,'Times New Roman',serif;font-size:0.78rem;" +
    "letter-spacing:0.14em;text-transform:uppercase;line-height:2}" +
    ".nav-costellazione a{color:#7a7468;text-decoration:none;margin:0 0.7rem;" +
    "white-space:nowrap}" +
    ".nav-costellazione a:hover{color:#c9a84c}" +
    ".nav-costellazione a.qui{color:#c9a84c;border-bottom:1px solid #8a6f2e;" +
    "padding-bottom:2px}" +
    "@media print{.nav-costellazione{display:none}}";
  document.head.appendChild(stile);

  var nav = document.createElement("nav");
  nav.className = "nav-costellazione";
  nav.innerHTML = VOCI.map(function (v) {
    return '<a href="' + v[0] + '"' +
      (v[0] === qui ? ' class="qui"' : '') + '>' + v[1] + '</a>';
  }).join("");

  function monta() { document.body.insertBefore(nav, document.body.firstChild); }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", monta);
  } else {
    monta();
  }
})();
