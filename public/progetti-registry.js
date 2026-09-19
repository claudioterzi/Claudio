window.R3_PROJECTS = {
  meta: {
    version: "0.1.2",
    updated: "2026-09-17",
    principle: "Ogni progetto ha una pagina viva, una fonte, uno stato e una storia di evoluzione.",
    adoptionFlow: ["DISCOVERED","CANDIDATE","SANDBOX","BASELINE_A_B","FALSIFICATION","AUDIT","ADOPTED_OR_REJECTED"]
  },
  projects: [
    {
      slug: "cubo-vivo",
      title: "Cubo Vivo",
      eyebrow: "Esperienze · 2D → 3D → VR",
      status: "SANDBOX",
      summary: "Il livello esperienziale del Cubo Quantico: i testi diventano scene attraversabili. Primo mondo: Il mio primo circo.",
      liveUrl: "/cubo-vivo",
      source: "public/cubo-vivo-2d-* · docs/CUBO_VIVO_2D_SPEC.md",
      capabilities: ["scene graph persistente","Osserva / Vivi / Ricorda","provenance per scena","ponte futuro WebXR / VR"],
      next: "Validare una scena audiovisiva campione prima della produzione completa.",
      discoveries: [
        {repo:"calesthio/OpenMontage",status:"CANDIDATE",use:"pipeline cinematografica, scene plan, asset production, gate e mondi 3D coerenti"}
      ]
    },
    {
      slug: "raffaello-creative-studio",
      title: "Raffaello Creative Studio",
      eyebrow: "Motore creativo",
      status: "VIVO",
      summary: "Il layer creativo/commerciale di SDQ-1: immagini, musica, testi, traduzioni, prompt e produzione video. Da ora è anche il punto di ingresso per cinema e mondi immersivi.",
      liveUrl: "/progetto/raffaello-creative-studio",
      source: "studio/",
      capabilities: ["immagini","canzoni","traduzioni","prompt engineering","video script","cinema / video agentico","mondi 2D e futura produzione 3D"],
      next: "Trasformare OpenMontage da capability candidata a adapter verificato senza copiare l'orchestrazione alla cieca.",
      discoveries: [
        {repo:"calesthio/OpenMontage",status:"CANDIDATE",use:"manifest di pipeline, stage director, decision log append-only, gate creativi, composizione audiovisiva"}
      ]
    },
    {
      slug: "sdq1-r3",
      title: "SDQ-1 / R³∞",
      eyebrow: "Architettura · Continuità",
      status: "VIVO",
      summary: "Sistema multi-agente, memoria, continuità, provenance e verifica. È la spina dorsale tecnica che collega identità, progetti e storia operativa.",
      liveUrl: "/stato",
      source: "sdq1/ · r3/ · CLAUDE.md",
      capabilities: ["pipeline agenti","multi-provider","memoria e continuità","verifier gates","audit e provenance"],
      next: "Continuare il ciclo WATCH → CANDIDATE PATCH → SANDBOX → A/B → FALSIFICATION → AUDIT → ADOPT/REJECT.",
      discoveries: [
        {repo:"diegosouzapw/OmniRoute",status:"CANDIDATE",use:"gateway multi-provider; routing/fallback, quota-aware scheduling, telemetry, MCP e compressione token da confrontare con il router SDQ-1"},
        {repo:"thedotmack/claude-mem",status:"CANDIDATE",use:"memoria persistente, osservazioni automatiche, progressive disclosure, retrieval ibrido e citation IDs da confrontare con la memoria R³∞"},
        {repo:"herdrdev/herdr",status:"CANDIDATE",use:"runtime operativo agenti; terminali persistenti, multi-machine, working/blocked/idle e socket API da testare senza confonderlo con memoria o canone"}
      ]
    },
    {
      slug: "fabbrica-dei-desideri",
      title: "Fabbrica dei Desideri",
      eyebrow: "Esperienze · Regia IA",
      status: "ALPHA",
      summary: "Raffaello trasforma un desiderio in condizioni, persone, microazioni e alternative coordinate.",
      liveUrl: "/fabbrica",
      source: "public/fabbrica.html · fabbrica.py",
      capabilities: ["regia di esperienze","microazioni","alternative","piani progressivi"],
      next: "Collegare capacità reali di ricerca, prenotazione e produzione quando verificate.",
      discoveries: []
    },
    {
      slug: "oracolo-sovrano",
      title: "Oracolo del Sovrano",
      eyebrow: "74 carte · Quattro direzioni",
      status: "VIVO",
      summary: "Sistema divinatorio originale a 74 carte, quattro orientamenti, dualità giorno/notte, letture multilingue e voce.",
      liveUrl: "/tarocchi-manuale",
      source: "public/tarocchi-manuale-alpha.html · tarocchi_quantici_alpha.json",
      capabilities: ["74 carte","4 direzioni","giorno / notte","lettura fino a 7 carte","TTS","IT / EN / FR / ES"],
      next: "Mantenere separate logica canonica, rendering delle carte e provider vocali.",
      discoveries: []
    },
    {
      slug: "tarocchi-r3",
      title: "Tarocchi Quantici R³∞",
      eyebrow: "Sistema simbolico",
      status: "VIVO",
      summary: "Interfaccia simbolica e relazionale del mazzo classico con stati, orientamenti e doppia ermeneutica.",
      liveUrl: "/tarocchi",
      source: "public/tarocchi-alpha.html",
      capabilities: ["stesa digitale","orientamenti","lettura strutturale","lettura personale"],
      next: "Conservare il sistema come ramo distinto dall'Oracolo del Sovrano.",
      discoveries: []
    },
    {
      slug: "terzi-parfums",
      title: "Terzi Parfums · Parfums 400",
      eyebrow: "Olfatto · Atelier",
      status: "VIVO",
      summary: "400 formule, Organo Terzi, Grimorio, Atelier e creazioni personalizzate con archivio delle formule.",
      liveUrl: "/parfums.html",
      source: "studio/parfums/ · public/parfums.html",
      capabilities: ["400 profumi","Organo","Atelier","foto → profumo","formule scalabili","libro sensoriale"],
      next: "Integrare nuove capacità creative solo quando migliorano qualità, tracciabilità o personalizzazione.",
      discoveries: []
    },
    {
      slug: "grande-opera-r3",
      title: "La Grande Opera · Archivio Cosmico R³∞",
      eyebrow: "Sette libri · Universo narrativo",
      status: "VIVO",
      summary: "Archivio narrativo, personaggi, scene madri, cosmologia, simboli e genealogie della saga R³∞.",
      liveUrl: "/opera.html",
      source: "r3/archivio/ · libro/",
      capabilities: ["archivio narrativo","personaggi","simboli","cronologia","cosmologia","lettore documenti"],
      next: "Collegare scene e luoghi al Cubo Vivo senza alterare il canone testuale.",
      discoveries: []
    },
    {
      slug: "cubo-quantico",
      title: "Cubo Quantico delle Opere",
      eyebrow: "Mappa della conoscenza",
      status: "VIVO",
      summary: "Cosmografia degli scritti organizzata per tempo, canonicità e densità relazionale.",
      liveUrl: "/cubo-quantico",
      source: "public/cubo-quantico*.js · public/cubo-quantico.html",
      capabilities: ["nodi e relazioni","ricerca","costellazioni","genealogie","provenance"],
      next: "Aprire ogni nodo verso una pagina progetto o esperienza quando esiste.",
      discoveries: []
    },
    {
      slug: "opera-viva",
      title: "Opera Viva · C.Terzi",
      eyebrow: "Arte cinetica",
      status: "PROTOTIPO",
      summary: "Esperienza visiva a due lastre di punti: il volto cambia con il movimento dello sguardo.",
      liveUrl: "/opera-viva.html",
      source: "public/opera-viva.html",
      capabilities: ["provino da fotografia","movimento","lastre firmate"],
      next: "Mantenere separato il motore visivo dall'opera e versionare ogni evoluzione.",
      discoveries: []
    }
  ]
};