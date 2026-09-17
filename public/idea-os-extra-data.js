/* IDEA OS — delta del 17/09/2026 recuperato cross-chat.
   Append-only, deduplicato per IDEA-ID. Il Master Google Drive resta la fonte canonica. */
(function(){
'use strict';
var portfolio=window.IDEA_OS_PORTFOLIO;
if(!portfolio||!Array.isArray(portfolio.ideas))return;
var extras=[
  {
    id:'IDEA-014',
    title:'R³∞ MetaBrand · Nucleo di Convergenza',
    maturity:'M1',
    depth:'D0',
    status:'ACTIVE · HTML REPORT EXISTS',
    engine:'R³ METHOD LAB / Communication & Conseil',
    horizon:'H0/H1',
    secure:false,
    origin:'Conversazioni Claudio × Raffaello del 17/09/2026. Il nucleo nasce dalla Scacchiera Quantica / Matrice dei Possibili come filosofia operativa e dalla richiesta di trasformare i risultati eccezionali ottenuti con il metodo in un sistema coerente di identità, sigillo e riconoscimento fisico.',
    problem:'Un metodo complesso può perdere riconoscibilità quando resta disperso fra documenti, simboli e risultati. Serve distinguere chiaramente identità del sistema, prova del risultato e premio assegnato ai casi eccezionali.',
    thesis:'Costruire una grammatica unica: Scacchiera Quantica / Matrice dei Possibili come logica operativa; un segno/sigillo come identificatore; il Nucleo di Convergenza come premio fisico collezionabile e illuminato assegnato soltanto a risultati verificati, non come logo decorativo.',
    buyer:'Uso interno chiaro per R³∞ / IDEA OS; beneficiari esterni potenziali sono clienti o progetti che raggiungono risultati eccezionali verificati. Nessun mercato o prezzo dichiarato.',
    evidence:'Esiste già il report HTML “IDEA_OS_MetaBrand_Nucleo_v1_audio.html” del 17/09/2026. Originalità, disponibilità marchio, design registrabile e valore economico restano NON VERIFICATI.',
    currentTech:'H0: identità visiva, sigillo digitale, sistema di livelli, certificato/URL/QR, mockup e report audio sono realizzabili ora. H1: prototipo fisico illuminato, materiali, serializzazione e produzione ripetibile.',
    capability:'Non richiede tecnologia futura per il nucleo. Eventuali oggetti con verifica digitale, NFC o provenance avanzata restano integrazioni H1 da testare.',
    constraints:'BRAND_DISTINCTIVENESS · IP_PRIOR_ART · MANUFACTURING · EVIDENCE_OF_OUTCOME',
    assumptions:'Il premio deve essere percepito come prova di risultato e appartenenza a un sistema, non come gadget generico o trofeo tecnologico. La Scacchiera Quantica è trattata come metafora/combinatoria operativa, non come claim scientifico di fisica quantistica.',
    nextTest:'Confrontare 3 direzioni visive e un mockup fisico/3D del Nucleo; verificare se osservatori indipendenti distinguono in pochi secondi: metodo, sigillo e premio, e comprendono che il premio viene assegnato per risultati verificati.',
    baseline:'Logo o trofeo generico senza grammatica comune e senza collegamento esplicito a evidenze/risultati.',
    kpi:'Comprensione corretta del ruolo del premio; memorabilità del segno; confusione logo/premio; riconoscibilità tra supporti; percentuale di interpretazioni “gadget/crypto/tech generico”.',
    falsifier:'Se il sistema aumenta confusione, viene percepito come claim pseudo-scientifico o il premio non comunica un risultato verificato meglio di una soluzione semplice, comprimere o riprogettare il concept.',
    risk:'Medio. Prima di uso esterno servono ricerca marchi/design/prior art e regole di attribuzione del premio. Non dichiarare unicità, registrazione, valore di mercato o brevettabilità senza prova.',
    relations:'RELATED alla Scacchiera Quantica storica e all’IDEA OS; non sostituisce il metodo. Il Nucleo di Convergenza è il premio, non il logo. Global Address/IGA può fornire l’identità digitale persistente del riconoscimento.',
    updates:[
      'Report HTML audio esistente su Drive: IDEA_OS_MetaBrand_Nucleo_v1_audio.html · ID 1VjAzcLYwpysJTs9S-XULT4NOOm_RX7Ie.',
      'Estensione IGA: il premio fisico può essere collegato a ID/URL/manifest/QR-NFC senza rendere pubbliche informazioni riservate.'
    ],
    dossier:null
  },
  {
    id:'IDEA-015',
    title:'CUBO VIVO 2D · Il mio primo circo',
    maturity:'M0',
    status:'ACTIVE · PROTOTYPE / BASELINE',
    engine:'Creative Studio / R³∞ Experience Lab',
    horizon:'H0 → H1',
    secure:false,
    origin:'Conversazione del 17/09/2026 sul passaggio da testi e Cubo Quantico a mondi abitabili. Primo mondo: “Il mio primo circo”.',
    problem:'Testi, immagini e scene possono restare contenuti passivi; il concept esplora come trasformarli in un mondo persistente che l’utente può osservare, vivere e ricordare prima del salto a 3D/VR.',
    thesis:'Usare un scene graph persistente e tre modalità — OSSERVA / VIVI / RICORDA — per trasformare una sequenza narrativa 2D in una memoria spaziale coerente e riapribile, usando il 2D come ponte verificabile verso esperienze 3D/VR.',
    buyer:'Uso interno chiaro come laboratorio creativo R³∞ e primo caso d’uso del Creative Studio; eventuali buyer esterni NON VERIFICATI.',
    evidence:'È stato registrato un prototipo/baseline su branch feature/cubo-vivo-2d, Draft PR #50, con specifica CUBO_VIVO_2D_SPEC.md e otto scene persistenti. La qualità dell’esperienza e il valore esterno non sono ancora verificati.',
    currentTech:'H0: scene graph, persistenza, navigazione 2D, stati Osserva/Vivi/Ricorda e composizione multimediale sono realizzabili con stack web corrente.',
    capability:'H1: transizione a 3D/VR, continuità spaziale più ricca, asset generation e montaggio multimodale; OpenMontage resta capability candidate, non dipendenza adottata automaticamente.',
    constraints:'UX_CONTINUITY · ASSET_PIPELINE · STATE_PERSISTENCE · PERFORMANCE',
    assumptions:'La persistenza narrativa/spaziale deve aumentare presenza e memoria senza rendere il sistema pesante o fragile. Il passaggio a VR deve essere giustificato da un miglioramento osservabile, non dal solo effetto wow.',
    nextTest:'Ripetere il micro-test su più scene verificando persistenza del scene graph, ritorno allo stato precedente, comprensione delle tre modalità e continuità 2D→mockup 3D senza perdita di contesto.',
    baseline:'Sequenza lineare di immagini/testo senza stato persistente né memoria spaziale.',
    kpi:'Scene recuperate correttamente; errori di stato; tempo di riapertura; elementi ricordati; continuità percepita; performance su mobile.',
    falsifier:'Se la persistenza non migliora orientamento/memoria o introduce più frizione e peso della narrazione lineare, non espandere verso 3D/VR finché il nucleo 2D non è stabile.',
    risk:'Basso/medio. OpenMontage e altri repository restano CANDIDATE finché non passano sandbox, test e audit; nessuna dipendenza esterna viene adottata per sola somiglianza.',
    relations:'UPDATE/RELATED al Creative Studio. OpenMontage è capability candidate per Video/Cinema/Mondi 2D, non nuova idea separata. Il Cubo Vivo è il primo caso d’uso.',
    updates:[
      'Pipeline candidate Creative Studio: research → proposal → script → scene_plan → assets → edit → compose.',
      'Processo repo: DISCOVERED → CANDIDATE → SANDBOX → test/audit → ADOPTED oppure REJECTED.'
    ],
    dossier:null
  }
];
extras.forEach(function(extra){
  if(!portfolio.ideas.some(function(x){return x.id===extra.id}))portfolio.ideas.push(extra);
});
portfolio.meta.snapshot='2026-09-17';
})();
