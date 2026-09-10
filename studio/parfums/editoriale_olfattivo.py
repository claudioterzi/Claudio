"""Inserto olfattivo del Libro dei 400. Concept: Claudio Terzi, 2026."""
from studio.parfums.genera_esperienze import qr_block


def rubrica_libro():
    rows = ''.join(
        '<tr><th scope="row">' + str(row) + '</th>' + ''.join(
            f'<td><strong>{letter}{row}</strong><span class="olf-blank">Campione __________</span></td>'
            for letter in 'ABCDE') + '</tr>' for row in range(1, 4))
    return '''
<section id="rubrica-olfattiva" class="olf-insert" aria-labelledby="rubrica-titolo">
  <div class="olf-eyebrow">Il Libro dei 400 · Edizione sensoriale · Progetto</div>
  <h1 id="rubrica-titolo">Le pagine si annusano</h1>
  <p class="olf-lead">Una rubrica di mouillette estraibili accompagna le quattrocento ricette.
  La lettura incontra il campione: lo trovi, lo sfili, lo confronti e annoti ciò che senti.</p>
  <p>Idea e direzione: <strong>Claudio Terzi</strong> · <span class="olf-signature">C.Terzi</span></p>
  <div class="olf-actions olf-no-print">
    <button type="button" data-olf-print="insert">Stampa questo inserto</button>
    <a href="magazine.html">Il magazine mensile</a>
  </div>
  <h2>Una coordinata per ritrovare il campione</h2>
  <p>Lettere <strong>A, B, C, D, E</strong> in orizzontale e numeri sulla sinistra.
  <strong>C3</strong> indica la posizione C, terza fila. La corrispondenza tra posizione
  e pagina fisica sarà definita nel prototipo di rilegatura.</p>
  <div class="olf-table-wrap"><table class="olf-grid">
    <caption>Matrice dimostrativa · tre righe di esempio, non il limite del libro</caption>
    <thead><tr><th scope="col">Riga</th>''' + ''.join(
        f'<th scope="col">{letter}</th>' for letter in 'ABCDE') + '''</tr></thead>
    <tbody>''' + rows + '''</tbody>
  </table></div>
  <p class="olf-note">Per più inserti, aggiungere il riferimento del volume o del modulo:
  <strong>volume / modulo / C3</strong>. La posizione si assegna quando il campione viene
  preparato: non è ricavata automaticamente dal numero della ricetta.</p>
  <h2>Il gesto e la costruzione</h2>
  <ol class="olf-steps">
    <li><strong>Sfili.</strong> Mouillette stretta, afferrabile con pollice e indice;
    estrazione laterale da sinistra verso destra.</li>
    <li><strong>Isoli.</strong> Ogni striscia ha un alloggiamento orizzontale separato.
    Per l'edizione fisica è previsto un involucro individuale: tenuta e trasferimento
    degli odori vanno verificati sul prototipo.</li>
    <li><strong>Confronti.</strong> Una lunghezza corta in A per essenze forti/concentrate;
    una lunghezza maggiore in E, vicina alle mouillette da profumeria.
    Le lunghezze intermedie e le misure restano da collaudare.</li>
    <li><strong>Ritrovi.</strong> Lo stesso riferimento compare su striscia,
    alloggiamento e scheda del profumo; nome e data restano leggibili dopo l'estrazione.</li>
  </ol>
  <p class="olf-note">Lunghezza, quantità depositata e diluizione sono parametri distinti.
  Questa stampa fornisce indice e schede; l'inserimento dei campioni richiede
  preparazione e assemblaggio fisici.</p>
  <h2>Tre riferimenti, tre funzioni</h2>
  <table class="olf-table"><thead><tr><th scope="col">Riferimento</th><th scope="col">Che cosa identifica</th></tr></thead>
    <tbody><tr><th scope="row">N° 001–400</th><td>La creazione nel libro.</td></tr>
    <tr><th scope="row">TRZ1…</th><td>La formula ricostruibile nell'archivio digitale.</td></tr>
    <tr><th scope="row">Volume / modulo / C3</th><td>Il posto della mouillette fisica.</td></tr></tbody></table>
  <h2>Registro dell'inserto</h2>
  <p>Volume / modulo: ____________________ · Preparazione: ____________________</p>
  <table class="olf-table olf-register"><thead><tr><th scope="col">Posizione</th><th scope="col">N° / campione</th><th scope="col">Lotto · diluizione · data</th></tr></thead>
    <tbody>''' + ''.join('<tr><td>________</td><td>________________</td><td>________________________</td></tr>' for _ in range(3)) + '''</tbody></table>
  <p class="olf-note">Proposta editoriale del 10 settembre 2026. Dimensioni, rilegatura,
  numero di campioni per inserto e conservazione da validare prima della produzione.</p>
</section>
'''


def riferimento_campione(numero):
    return f'''
    <div class="olf-sample" aria-label="Campione fisico del profumo {numero}">
      <strong>Mouillette · N° {numero:03d}</strong>
      <p>Volume / modulo __________ · Posizione ________</p>
      <p>Lotto __________ · Diluizione __________ · Data __________</p>
      <p>Prima impressione __________________________________________</p>
      <p>Evoluzione · ora ________ ___________________________________</p>
      <span class="olf-signature">C.Terzi</span>
    </div>{qr_block(f'P{numero:03d}')}'''
