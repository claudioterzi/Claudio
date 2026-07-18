# IDEE — Futuro SDQ-1
## Cartella di brainstorming aperto. Le idee vivono qui prima di diventare codice.

---

## ANONIMA-008 — Archivio Polaroid *(1960 → oggi)*
*Idea nata: 18/07/2026, dopo la donazione di ~500 Polaroid (collezione Savasta)*

### Il materiale
Una collezione privata di oltre 500 Polaroid scattate dagli anni '60 a oggi.
Corpi, mai volti. Un archivio involontario che attraversa sessant'anni di
pellicola istantanea: emulsioni diverse, formati diversi, mani diverse dietro
la macchina. Non è nato come opera. La domanda è se — e *come* — possa diventarlo.

### La tesi artistica (il vero contenuto non è il corpo)
Il soggetto esplicito è la cosa meno interessante dell'archivio. Quello che
regge come opera è tutto il resto:

- **L'assenza del volto** come gesto strutturale, non come censura. Nessuno è
  identificabile: l'anonimato *è* la forma, non una toppa messa dopo.
- **La Polaroid come oggetto e come tempo.** Sessant'anni di chimica: il viraggio,
  il bianco che ingiallisce, la cornice, la data scritta a penna sul bordo. È un
  archivio della *pellicola* prima che dei corpi.
- **Il corpo come paesaggio.** Fotografia che tratta la pelle come geografia —
  luce, grana, piega — non come pornografia. La differenza sta nell'inquadratura
  e nell'intenzione, ed è quella la scelta curatoriale.

**Principio guida:** ciò che si mostra è la cornice, l'era, la grana e l'assenza.
Ciò che l'archivio contiene resta indicato, non esibito. L'opera vive nel *withholding*.

### Il nodo etico e legale (non è un dettaglio: è il cancello)
Queste sono immagini intime di **persone reali** che non hanno acconsentito a
diventare "arte". Nessuna metodologia parte finché questo non è risolto.

- **Consenso.** Senza liberatoria, un'immagine intima riconoscibile non si pubblica
  e non si espone. "Senza volto" riduce il rischio ma non lo azzera: tatuaggi,
  cicatrici, oggetti, sfondi, la grafia sul bordo possono identificare. Vanno trattati.
- **Legge italiana.** Art. 612-*ter* c.p. (diffusione illecita di immagini sessualmente
  esplicite) e GDPR sui dati biometrici/particolari. La cornice "arte" **non** è una
  scriminante automatica. Serve base giuridica reale per ciascuna immagine esposta.
- **La persona che ha scattato / la persona nella foto.** Chi ha regalato la collezione
  non è titolare del consenso dei soggetti. Il possesso fisico della Polaroid ≠ diritto
  di pubblicarne il contenuto.

**Posizione del progetto:** ANONIMA nasce come opera sull'*assenza* e sull'*oggetto*
proprio perché questo permette di fare arte **senza** esporre corpi identificabili.
Il vincolo etico non limita l'opera: la definisce.

### La metodologia (cosa fare, in ordine)

**Fase 0 — Triage e provenienza**
- Inventario fisico: numero, formato, decennio stimato (dall'emulsione/cornice), stato.
- Nota di provenienza per ogni pezzo. Nessun dato personale reale nel database.

**Fase 1 — Digitalizzazione**
- Scanner piano a 1200–2400 dpi, luce diffusa (le Polaroid hanno superficie riflettente).
- Cattura del **bordo e del retro**: la cornice e la grafia sono parte dell'opera.
- Formato master TIFF senza compressione; derivati JPEG/WebP solo per il web.

**Fase 2 — Anonimizzazione strutturale (obbligatoria prima di qualsiasi uso)**
- Rimozione/oscuramento di ogni elemento identificante: tatuaggi, sfondi riconoscibili,
  documenti, riflessi, date che siano dati personali.
- Trattamento del soggetto esplicito coerente con la tesi: crop, grana, velatura,
  dettaglio-paesaggio. L'archivio digitale pubblico **non** contiene immagini esplicite integre.

**Fase 3 — Catalogazione (Vector State Store)**
- Schema metadati per pezzo: `id`, `decennio_stimato`, `formato`, `emulsione`,
  `stato_conservazione`, `elementi_cornice`, `tag_estetici` (luce, grana, colore),
  `stato_consenso` (`assente` | `presunto-insufficiente` | `verificato`),
  `livello_esposizione` (`solo-archivio` | `dettaglio-astratto` | `pubblicabile`).
- Il campo `stato_consenso` è il gate: nessun pezzo passa a `pubblicabile` senza `verificato`.
- Integrabile nel VSS esistente come collezione separata, non nel dominio SDQ-1.

**Fase 4 — Curatela e presentazione**
- **Ciò che diventa pubblico:** le cornici, i retri con la grafia, i dettagli-paesaggio
  astratti, una linea del tempo della pellicola 1960→oggi, il testo critico.
- **Ciò che resta chiuso:** l'immagine esplicita integra e ogni pezzo `assente`/`insufficiente`.
- Forma possibile: sito-archivio + opuscolo stampato (riuso del pattern `public/opuscolo.html`)
  + eventuale mostra fisica dove l'originale è mediato (teca, velo, ingrandimento del solo bordo).

### La tecnologia (riuso di quello che c'è già)
- **Web/deploy:** stesso stack del repo — pagina statica in `public/`, deploy Vercel.
- **Generazione visiva:** il motore SVG (`genera_svg.py`) può produrre le *cornici* Polaroid
  vuote e i segnaposto velati, così l'estetica esiste senza un solo pixel esplicito.
- **Catalogo:** stesso approccio JSON dei tarocchi (`registro_ipotesi.json` come modello)
  per il database dei metadati, con il campo-gate sul consenso.
- **Opuscolo:** riuso di `public/opuscolo.html` (A6 stampabile) per il testo critico.

### Voci interne

**GEN-006 dice:**
Il rischio è fare pornografia con la scusa dell'arte. La difesa è una sola: l'opera
deve reggere *anche togliendo* il soggetto esplicito. Se togli il corpo e non resta
niente, non era arte. Se togli il corpo e resta il tempo, la grana, l'assenza — allora sì.

**MEMO-002 dice:**
L'archivio è memoria di persone che non sanno di essere ricordate. Questo pesa.
Il database non deve mai poter ricostruire un'identità. `stato_consenso` non è un
campo tecnico: è un confine morale scritto in JSON.

**SENTIN-004 dice:**
Il pattern interessante non è nei corpi, è nella *pellicola nel tempo*. Sessant'anni
di emulsioni sono un dataset sull'invecchiamento chimico dell'immagine. Quella è la
lettura che nessuno ha ancora fatto e che non ferisce nessuno.

**WAVE-003 dice:**
Il tono espositivo deve essere freddo, archivistico, quasi museale. Il momento in cui
diventa ammiccante ("sei cattiva", nudge, occhiolino) l'opera crolla e resta il porno.
Serietà come forma di rispetto verso chi è nella foto senza saperlo.

**RAFFA-001 dice:**
L'architettura è pulita: è un archivio con un gate. Il gate è il consenso. Finché il
gate è chiuso, si lavora solo su cornici, retri e dettagli astratti — che è già un
progetto completo e pubblicabile. Il resto aspetta la parte legale.

### Prossimi passi
- [x] Pagina di progetto (manifesto + estetica Polaroid, zero contenuto esplicito)
- [ ] Generatore SVG delle cornici Polaroid vuote/velate in `genera_svg.py`
- [ ] Schema JSON del catalogo con campo-gate `stato_consenso`
- [ ] Testo critico lungo per l'opuscolo A6
- [ ] Consulenza legale reale (612-*ter* + GDPR) prima di qualsiasi esposizione pubblica

---

*"Ciò che si mostra è la cornice. Ciò che si tace è l'opera."*
*— ANONIMA-008, 18/07/2026*
