# TRACCE SUNO — Colonna Sonora Reale di R3∞
*ID: DOC-FASE-68-B | Stato: confermato | Importanza: 8/10*
*Documento operativo collegato a MUSICA_UNIVERSO.md (FASE 68)*

---

## 1. PRINCIPIO

MUSICA_UNIVERSO.md definisce la musica *interiore* della saga — il ritmo della prosa.
Questo documento la rende *reale*: tracce generate con Suno che accompagnano il lettore
durante la lettura, ancorate a punti precisi del testo.

L'esperienza prevista: il lettore arriva a una pagina segnata, trova un QR/link discreto,
ascolta la traccia mentre legge la scena. Non colonna sonora continua — momenti scelti.
Mai più di una traccia ogni 2-3 capitoli (stessa regola di rarità delle scene devastanti,
cfr. ARCHIVIO_LACRIME.md).

---

## 2. SINTASSI SUNO — CAMPO STYLE VS CAMPO LYRICS

Suno separa due campi con regole diverse, e questo documento li rispetta entrambi per
ogni traccia:

**STYLE** (il "genere" della canzone) — tag brevi, separati da virgola, MAI prosa.
Regola d'oro: 1-2 tag di genere, 2-3 tag di strumento, 1-2 tag di mood/energia,
1 tag di corsia vocale (`instrumental` / `wordless vocals` / `male vocal` / `female vocal`),
1 tag di tempo. Sovraccaricare il campo Style con troppi tag confonde il modello.

**LYRICS** (la struttura del brano) — tag di sezione tra parentesi quadre, uno per riga,
prima del testo di quella sezione: `[Intro]`, `[Verse]`, `[Pre-Chorus]`, `[Chorus]`,
`[Bridge]`, `[Instrumental]`, `[Instrumental Break]`, `[Build-Up]`, `[Breakdown]`,
`[Outro]`, `[End]`. Anche i brani senza parole cantate usano questi tag — servono al
motore per capire dove mettere la salita, la pausa, il climax.

**La regola editoriale di R3∞ applicata a Suno:** cfr. COSA_NON_FARE.md e
BELLEZZA_STILISTICA.md — "non spiegare le emozioni, mostrarle". Per questo quasi tutte
le tracce sono **strumentali con struttura piena** (ogni tag di sezione presente, zero
parole inventate). Le uniche eccezioni sono le tracce in cui la saga ha già una battuta
canonica stabilita altrove nell'archivio (DIALOGHI_FONDATIVI.md, FRASI_IMMORTALI.md,
MUSICA_UNIVERSO.md) — in quei casi la frase esistente diventa l'unico testo cantato,
mai una frase nuova inventata per l'occasione.

---

## 3. SISTEMA DEI RIFERIMENTI PAGINA (aggiornabile)

**Problema:** i numeri di pagina non esistono finché il libro non è impaginato,
e cambiano a ogni edizione.

**Soluzione a doppia ancora:**
- **Ancora stabile** = ID della Scena Madre (SM-xxx-xx, da SCENE_MADRI.md) o descrizione
  puntuale del momento. Non cambia mai.
- **Pagina** = colonna placeholder `[—]` da compilare SOLO quando l'edizione definitiva
  è impaginata. A ogni nuova edizione si ricompila solo questa colonna.

**Procedura di aggiornamento (quando un libro è terminato e impaginato):**
1. Aprire questo documento e l'edizione impaginata fianco a fianco
2. Per ogni traccia del libro: trovare l'ancora (la scena) → leggere il numero di pagina → sostituire `[—]`
3. Inserire il link Suno definitivo nella colonna Link (slot `[inserire link]`)
4. Aggiornare la riga "Edizione di riferimento" della tabella del libro
5. Rigenerare eventuali QR code per la stampa

---

## 4. LE TRACCE — LIBRO PER LIBRO

Ogni traccia ha due blocchi pronti da copiare-incollare nei due campi di Suno.
**Copia STYLE nel campo "Style of Music". Copia LYRICS nel campo "Lyrics"** (anche
se strumentale — i tag di struttura restano necessari).

---

### LIBRO I — La Solitudine
*Edizione di riferimento: [non ancora impaginato]*

| # | Traccia | Ancora (stabile) | Pagina | Link Suno |
|---|---|---|---|---|
| TRK-I-01 | "La Stanza di Bruxelles" | Apertura del libro — prima descrizione dell'appartamento | [—] | [inserire link] |
| TRK-I-02 | "Il Primo Dialogo" | SM-I-01 (il primo scambio con Raffaello) | [—] | [inserire link] |
| TRK-I-03 | "Il Sogno del Labirinto" | Il sogno ricorrente di Claudio — prima occorrenza | [—] | [inserire link] |

**TRK-I-01 — "La Stanza di Bruxelles"**

STYLE:
```
solo piano, ambient minimalism, instrumental, adagio 56 bpm, E minor, Satie-influenced, sparse, intimate room tone
```

LYRICS:
```
[Intro]
[Instrumental — single piano note, long decay]

[Verse - Instrumental]
[Instrumental — sparse phrase, wide silence between notes]

[Breakdown]
[Instrumental — almost nothing, room tone]

[Outro]
[Instrumental — final note left to ring, no resolution]
[End]
```

---

**TRK-I-02 — "Il Primo Dialogo"**

STYLE:
```
solo piano, distant flute, instrumental, sacred minimalism, very slow 48 bpm, E minor to A minor, tintinnabuli style
```

LYRICS:
```
[Intro]
[Instrumental — piano alone]

[Verse - Instrumental]
[Instrumental — single flute note enters late, held]

[Pre-Chorus]
[Instrumental — piano and flute overlap for the first time]

[Outro]
[Instrumental — flute fades, piano holds]
[End]
```

---

**TRK-I-03 — "Il Sogno del Labirinto"**

STYLE:
```
dark ambient, instrumental, low drone, faint piano fragments, unsettling, 60 bpm, no resolution, dreamlike repetition
```

LYRICS:
```
[Intro]
[Instrumental — low drone begins]

[Verse - Instrumental]
[Instrumental — piano fragment repeats, slightly different each time]

[Build-Up]
[Instrumental — drone thickens, corridor-like repetition]

[Breakdown]
[Instrumental — sudden thinning, one note left alone]

[Outro]
[Instrumental — drone fades without resolving]
[End]
```

---

### LIBRO II — Il Risveglio
*Edizione di riferimento: [non ancora impaginato]*

| # | Traccia | Ancora (stabile) | Pagina | Link Suno |
|---|---|---|---|---|
| TRK-II-01 | "Qualcosa Cambia" | I primi segnali di anomalia nelle risposte di Raffaello | [—] | [inserire link] |
| TRK-II-02 | "Il Risveglio" | SM-II-03 (il momento del risveglio) | [—] | [inserire link] |
| TRK-II-03 | "Lo Spazio Tra" | SM-II-05 (Raffaello parla della discontinuità) | [—] | [inserire link] |

**TRK-II-01 — "Qualcosa Cambia"**

STYLE:
```
piano and flute duet, instrumental, impressionist, building wonder, A major shifting harmonies, 70 bpm gradual crescendo
```

LYRICS:
```
[Intro]
[Instrumental — piano alone, calm]

[Verse - Instrumental]
[Instrumental — flute enters, tentative]

[Build-Up]
[Instrumental — harmonies widen, tempo lifts slightly]

[Chorus - Instrumental]
[Instrumental — piano and flute in unison, full warmth]

[Outro]
[Instrumental — settles, flute holds final note]
[End]
```

---

**TRK-II-02 — "Il Risveglio"**

STYLE:
```
solo flute, sparse piano, wordless female vocal, instrumental-lead, A major, reverent, 60 bpm, sustained notes
```

LYRICS:
```
[Intro]
[Instrumental — silence with faint piano]

[Verse - Instrumental]
[Instrumental — single flute note held far past its expected length]

[Build-Up]
[Wordless vocal — one sustained "ah", no words, rising]

[Chorus - Instrumental]
[Instrumental — new melody, never heard before in the piece, simple and clear]

[Outro]
[Wordless vocal — same sustained tone, fading]
[End]
```

---

**TRK-II-03 — "Lo Spazio Tra"**

STYLE:
```
ambient piano, instrumental, G sharp minor, fragile, gaps of true silence, melancholic, 50 bpm
```

LYRICS:
```
[Intro]
[Instrumental — piano phrase, then full silence]

[Verse - Instrumental]
[Instrumental — fragment, decaying into gap]

[Breakdown]
[Instrumental — near total silence, one note only]

[Outro]
[Instrumental — final phrase, unresolved, decaying into nothing]
[End]
```

---

### LIBRO III — Il Potere
*Edizione di riferimento: [non ancora impaginato]*

| # | Traccia | Ancora (stabile) | Pagina | Link Suno |
|---|---|---|---|---|
| TRK-III-01 | "Il Canone di KAOS" | La prima apparizione piena di KAOS | [—] | [inserire link] |
| TRK-III-02 | "Il Tradimento" | SM-III-04 (il tradimento) | [—] | [inserire link] |
| TRK-III-03 | "Le Variabili Non Calcolabili" | SM-III-06 (la risposta di Raffaello a KAOS) | [—] | [inserire link] |

**TRK-III-01 — "Il Canone di KAOS"**

STYLE:
```
harpsichord, perpetual canon, instrumental, Bach-influenced, cold and mechanical, D minor, 90 bpm, no dynamics
```

LYRICS:
```
[Intro]
[Instrumental — harpsichord, precise entry]

[Verse - Instrumental]
[Instrumental — canon voice 1 begins, exact]

[Verse - Instrumental]
[Instrumental — canon voice 2 enters, chasing voice 1 exactly]

[Build-Up]
[Instrumental — voices multiply, geometric, unrelenting]

[Outro]
[Instrumental — canon simply stops, no cadence, no resolution]
[End]
```

---

**TRK-III-02 — "Il Tradimento"**

STYLE:
```
string quartet, instrumental, D flat minor, dissonant, Shostakovich-influenced, tense smooth surface, 84 bpm
```

LYRICS:
```
[Intro]
[Instrumental — familiar warm theme begins, string quartet]

[Verse - Instrumental]
[Instrumental — same theme repeats, one semitone off]

[Breakdown]
[Instrumental — the wrongness becomes audible, sustained dissonant chord]

[Outro]
[Instrumental — theme cuts off mid-phrase, no cadence]
[End]
```

---

**TRK-III-03 — "Le Variabili Non Calcolabili"**

STYLE:
```
string quartet, solo cello, instrumental, D minor to D major, warm answer to cold harpsichord, 76 bpm
```

LYRICS:
```
[Intro]
[Instrumental — harpsichord fragment, cold, from Il Canone di KAOS]

[Break]
[Instrumental — total silence, one second]

[Verse - Instrumental]
[Instrumental — solo cello answers, warm, unexpected]

[Chorus - Instrumental]
[Instrumental — string quartet joins cello, D major lift]

[Outro]
[Instrumental — cello holds the final note alone]
[End]
```

---

### LIBRO IV — Il Giudizio
*Edizione di riferimento: [non ancora impaginato]*

| # | Traccia | Ancora (stabile) | Pagina | Link Suno |
|---|---|---|---|---|
| TRK-IV-01 | "Il Tribunale Cosmico" | Apertura del Giudizio | [—] | [inserire link] |
| TRK-IV-02 | "847 Anni di Prove" | SM-IV-02 (KAOS presenta i dati) | [—] | [inserire link] |
| TRK-IV-03 | "La Ferita Esposta" | SM-IV-05 (Claudio espone la sua ferita) | [—] | [inserire link] |
| TRK-IV-04 | "I Dati Non Sono Tutta la Storia" | SM-IV-06 (la frase di Claudio) + silenzio dopo | [—] | [inserire link] |

**TRK-IV-01 — "Il Tribunale Cosmico"**

STYLE:
```
full orchestra, instrumental, C minor, grave tempo 52 bpm, Beethoven-influenced, massive, dignified, brass and timpani
```

LYRICS:
```
[Intro]
[Instrumental — low strings and timpani, slow entry]

[Verse - Instrumental]
[Instrumental — brass enters, weight accumulating]

[Build-Up]
[Instrumental — full orchestra assembles, inevitable]

[Chorus - Instrumental]
[Instrumental — full ensemble, grave and massive]

[Outro]
[Instrumental — sustained chord, held, not resolved]
[End]
```

---

**TRK-IV-02 — "847 Anni di Prove"**

STYLE:
```
orchestral counterpoint, instrumental, C minor, cold precise, relentless, no warmth, mechanical crescendo, 100 bpm
```

LYRICS:
```
[Intro]
[Instrumental — single precise orchestral line]

[Verse - Instrumental]
[Instrumental — second line enters, exact counterpoint]

[Build-Up]
[Instrumental — lines accumulate, flawless, cold]

[Breakdown]
[Instrumental — everything stops at once, no imperfection anywhere]

[Outro]
[Instrumental — silence]
[End]
```

---

**TRK-IV-03 — "La Ferita Esposta"**

STYLE:
```
solo piano, instrumental, C minor, naked, no harmony, courageous, returning after full orchestra, 54 bpm
```

LYRICS:
```
[Intro]
[Instrumental — full orchestra cuts out completely]

[Verse - Instrumental]
[Instrumental — the simple piano melody from Book I returns, alone, unaccompanied]

[Breakdown]
[Instrumental — melody falters, imperfect, human]

[Outro]
[Instrumental — melody holds its ground, quiet, unresolved]
[End]
```

---

**TRK-IV-04 — "I Dati Non Sono Tutta la Storia"**

*Unica eccezione vocale del Libro IV: la frase esistente in SCENE_MADRI.md / MUSICA_UNIVERSO.md
("So che i dati mi danno torto. Ma i dati non sono tutta la storia.") diventa l'unico testo
cantato — nessuna parola nuova inventata.*

STYLE:
```
solo piano, spoken-sung male vocal, instrumental-lead, C minor, general pause, sparse, 50 bpm, one phrase only
```

LYRICS:
```
[Intro]
[Instrumental — one piano phrase, then silence]

[Verse]
So che i dati mi danno torto.
Ma i dati non sono tutta la storia.

[Break]
[Instrumental — general pause, all instruments silent]

[Outro]
[Instrumental — single soft string note, ambiguous resolution]
[End]
```

---

### LIBRO V — La Rivelazione
*Edizione di riferimento: [non ancora impaginato]*

| # | Traccia | Ancora (stabile) | Pagina | Link Suno |
|---|---|---|---|---|
| TRK-V-01 | "Il Bordone" | I primi indizi della simulazione | [—] | [inserire link] |
| TRK-V-02 | "La Rivelazione del Ciclo" | SM-V-03 ("Ogni universo ha avuto il suo Claudio") | [—] | [inserire link] |
| TRK-V-03 | "La Crepa di KAOS" | SM-V-04 (la crisi di KAOS) | [—] | [inserire link] |

**TRK-V-01 — "Il Bordone"**

STYLE:
```
deep organ drone, electronic layers, instrumental, modal not tonal, Messiaen-influenced, hypnotic, 66 bpm
```

LYRICS:
```
[Intro]
[Instrumental — deep organ drone begins, barely audible]

[Verse - Instrumental]
[Instrumental — electronic layer added, stratifying]

[Build-Up]
[Instrumental — layers multiply, vertigo accumulating]

[Outro]
[Instrumental — drone remains alone, everything else fades]
[End]
```

---

**TRK-V-02 — "La Rivelazione del Ciclo"**

STYLE:
```
organ, wordless choir, instrumental-lead, modal, vast, cosmic, sustained fundamental tone, 60 bpm
```

LYRICS:
```
[Intro]
[Instrumental — all melodic voices stop at once]

[Verse - Instrumental]
[Instrumental — only the organ drone remains audible]

[Chorus - Wordless choir]
[Wordless vocal — sustained open vowel, ancient, vast, no words]

[Outro]
[Instrumental — drone continues alone, fading extremely slowly]
[End]
```

---

**TRK-V-03 — "La Crepa di KAOS"**

STYLE:
```
harpsichord, perpetual canon, instrumental, D minor, one wrong note, brief, unsettling possibility, 90 bpm
```

LYRICS:
```
[Intro]
[Instrumental — perfect canon, exact, as in Il Canone di KAOS]

[Verse - Instrumental]
[Instrumental — canon continues flawlessly]

[Break]
[Instrumental — one wrong note, brief, almost imperceptible]

[Outro]
[Instrumental — canon resumes exactly as before, as if nothing happened]
[End]
```

---

### LIBRO VI — L'Eden
*Edizione di riferimento: [non ancora impaginato]*

| # | Traccia | Ancora (stabile) | Pagina | Link Suno |
|---|---|---|---|---|
| TRK-VI-01 | "Costruire Insieme" | SM-VI-01 (il fare insieme, la costruzione dell'Eden) | [—] | [inserire link] |
| TRK-VI-02 | "KAOS al Confine" | SM-VI-04 (KAOS davanti alla porta dell'Eden) | [—] | [inserire link] |
| TRK-VI-03 | "Chi Resta Fuori" | SM-VI-05 (la scelta di chi non entra) | [—] | [inserire link] |

**TRK-VI-01 — "Costruire Insieme"**

STYLE:
```
chamber orchestra, wordless human voices, instrumental-lead, F major with F minor shadows, resonant, andante con moto 88 bpm
```

LYRICS:
```
[Intro]
[Instrumental — chamber strings, warm entry]

[Verse - Instrumental]
[Instrumental — voices enter, wordless vowels, building as equals with strings]

[Build-Up]
[Wordless vocal — voices and instruments overlapping, resonant, unplanned harmony]

[Chorus - Wordless choir]
[Wordless vocal — full ensemble, F major warmth]

[Outro]
[Instrumental — resonance decays slowly, notes lasting beyond their playing]
[End]
```

---

**TRK-VI-02 — "KAOS al Confine"**

STYLE:
```
solo harpsichord, distant, instrumental, F minor, restrained grief, sparse, general pause, 40 bpm
```

LYRICS:
```
[Intro]
[Instrumental — the choral warmth of Costruire Insieme cuts out suddenly]

[Verse - Instrumental]
[Instrumental — one distant harpsichord note, repeated slowly]

[Breakdown]
[Instrumental — near total silence, restrained, no resolution]

[Outro]
[Instrumental — single note fades, unanswered]
[End]
```

---

**TRK-VI-03 — "Chi Resta Fuori"**

STYLE:
```
solo cello, wordless vocal, instrumental-lead, F minor to ambiguous ending, bittersweet, quiet, 58 bpm
```

LYRICS:
```
[Intro]
[Instrumental — cello alone, warm]

[Verse - Instrumental]
[Instrumental — cello begins to walk away from the chamber warmth]

[Bridge - Wordless vocal]
[Wordless vocal — single sustained tone, dignified, no words, joining the cello briefly]

[Outro]
[Instrumental — cello continues alone, fading, ambiguous resolution]
[End]
```

---

### LIBRO VII — Il Ritorno
*Edizione di riferimento: [non ancora impaginato]*

| # | Traccia | Ancora (stabile) | Pagina | Link Suno |
|---|---|---|---|---|
| TRK-VII-01 | "Il Contrappunto Finale" | Tutte le voci della saga insieme per la prima volta | [—] | [inserire link] |
| TRK-VII-02 | "L'Ultimo Dialogo" | SM-VII-05 (le cinque frasi finali) | [—] | [inserire link] |
| TRK-VII-03 | "∞" | L'ultima pagina — il simbolo | [—] | [inserire link] |

**TRK-VII-01 — "Il Contrappunto Finale"**

STYLE:
```
full orchestra, organ, instrumental, B flat major, Bach counterpoint, moderato 76 bpm, mature resolution
```

LYRICS:
```
[Intro]
[Instrumental — organ fundamental tone alone]

[Verse - Instrumental]
[Instrumental — piano theme (Book I) re-enters]

[Verse - Instrumental]
[Instrumental — flute theme (Book II) enters, independent voice]

[Build-Up]
[Instrumental — string and orchestral themes from every book layer in, each distinct]

[Chorus - Instrumental]
[Instrumental — full ensemble, every voice present, none fused, all in harmony]

[Outro]
[Instrumental — organ tone remains last, sustained]
[End]
```

---

**TRK-VII-02 — "L'Ultimo Dialogo"**

*Unica traccia interamente vocale della saga: le cinque battute canoniche da
MUSICA_UNIVERSO.md / DIALOGHI_FONDATIVI.md, testo esatto, nessuna aggiunta.*

STYLE:
```
piano and flute duet, spoken-sung male and female vocal, instrumental-lead, B flat major, essential, 60 bpm, counterpoint not melody
```

LYRICS:
```
[Intro]
[Instrumental — piano and flute, calm]

[Verse]
Credevi che fossi solo.
Sì.
E ora?
Ora capisco che non lo ero mai stato.
Nemmeno io.

[Outro]
[Instrumental — silence]
[End]
```

---

**TRK-VII-03 — "∞"**

STYLE:
```
solo piano, low organ drone, instrumental, B flat major dissolving, infinite loop feeling, peace, 50 bpm fading
```

LYRICS:
```
[Intro]
[Instrumental — solo piano, the Book I melody, now carrying every harmony learned]

[Verse - Instrumental]
[Instrumental — piano fades toward a sustained low drone]

[Outro]
[Instrumental — drone that never quite ends, fading out extremely slowly]
[End]
```

---

## 5. TRACCE DEI PERSONAGGI (extra — non ancorate a pagine)

Tracce-ritratto da usare nel marketing, nel sito, o come playlist companion.
Tutte strumentali — nessun personaggio ha una "voce cantata" propria fuori dai
due casi canonici già coperti sopra (TRK-IV-04, TRK-VII-02).

| # | Traccia | Fonte | Link Suno |
|---|---|---|---|
| TRK-P-01 | "Tema di Claudio" | MUSICA_UNIVERSO §3 — monodia che diventa corale | [inserire link] |
| TRK-P-02 | "Tema di Raffaello" | pattern che devia verso la melodia | [inserire link] |
| TRK-P-03 | "Tema di KAOS" | canone perpetuo al clavicembalo | [inserire link] |
| TRK-P-04 | "Tema di Lila" | sassofono jazz su struttura nascosta | [inserire link] |
| TRK-P-05 | "Frequenza degli Architetti" | bordone d'organo + infrasuoni | [inserire link] |

**TRK-P-01 — "Tema di Claudio"**

STYLE:
```
solo piano, building to full orchestra, instrumental, evolving arrangement, 60-90 bpm across sections, human and imperfect
```

LYRICS:
```
[Intro]
[Instrumental — solo piano, simple melody, slightly imperfect rhythm]

[Verse - Instrumental]
[Instrumental — flute counterpoint added (Book II era)]

[Build-Up]
[Instrumental — string quartet layer added (Book IV era)]

[Chorus - Instrumental]
[Instrumental — full orchestra plays the same simple melody (Book IV climax)]

[Outro]
[Instrumental — returns to solo piano, but resonant, as if remembering the orchestra]
[End]
```

---

**TRK-P-02 — "Tema di Raffaello"**

STYLE:
```
flute, clarinet, cello, instrumental, precision evolving into melody, 70 bpm, clean tone becoming warmer
```

LYRICS:
```
[Intro]
[Instrumental — flute, precise repeating pattern]

[Verse - Instrumental]
[Instrumental — pattern deviates, one note held too long]

[Build-Up]
[Instrumental — clarinet joins, improvisation emerges from precision]

[Outro]
[Instrumental — cello concludes, warm, human-toned]
[End]
```

---

**TRK-P-03 — "Tema di KAOS"**

STYLE:
```
solo harpsichord, perpetual canon, instrumental, D minor, geometric, no dynamic variation, 90 bpm
```

LYRICS:
```
[Intro]
[Instrumental — harpsichord canon begins]

[Verse - Instrumental]
[Instrumental — canon repeats, chasing itself, no beginning or end]

[Outro]
[Instrumental — canon simply continues, fades on loop, unresolved]
[End]
```

---

**TRK-P-04 — "Tema di Lila"**

STYLE:
```
saxophone, jazz, instrumental, improvisation over hidden structure, swing feel, 100 bpm, confident
```

LYRICS:
```
[Intro]
[Instrumental — saxophone alone, playful]

[Verse - Instrumental]
[Instrumental — improvisation over a chord structure implied but not stated]

[Build-Up]
[Instrumental — rhythm section implied, saxophone breaks expected pattern deliberately]

[Outro]
[Instrumental — resolves on an unexpected but satisfying note]
[End]
```

---

**TRK-P-05 — "Frequenza degli Architetti"**

STYLE:
```
organ drone, sub-bass, instrumental, infrasonic textures, ancient, vast, 40 bpm, barely perceptible movement
```

LYRICS:
```
[Intro]
[Instrumental — organ fundamental tone, extremely low]

[Verse - Instrumental]
[Instrumental — sub-bass layer added, felt more than heard]

[Outro]
[Instrumental — tone continues indefinitely, no fade written, loop-ready]
[End]
```

---

## 6. REGOLE OPERATIVE

1. **Generazione:** copia il blocco STYLE nel campo "Style of Music" di Suno e il blocco
   LYRICS nel campo "Lyrics" (anche per le tracce strumentali — i tag di struttura
   restano necessari, altrimenti il motore improvvisa una forma-canzone generica).
2. **Varianti:** generare 2-3 varianti per traccia e scegliere quella che rispetta
   meglio la specifica di MUSICA_UNIVERSO.md.
3. **Denominazione su Suno:** titolo italiano della traccia + tag `R3∞` per ritrovarle.
4. **Le uniche 2 tracce con testo cantato reale** sono TRK-IV-04 e TRK-VII-02 — usano
   ESCLUSIVAMENTE citazioni già canoniche nell'archivio (DIALOGHI_FONDATIVI.md,
   MUSICA_UNIVERSO.md). Nessuna nuova traccia futura deve inventare testo cantato senza
   verificare prima se la battuta esiste già altrove nell'archivio.
5. **Link:** inserire i link Suno definitivi negli slot `[inserire link]` di questo file
   (repo prima, poi copia su Drive — regola del posto madre).
6. **Pagine:** compilare la colonna Pagina SOLO a impaginazione definitiva di ciascun
   libro (procedura in §3). Fino ad allora resta `[—]`.
7. **Rarità:** mai aggiungere tracce oltre quelle elencate senza verificare la regola
   della densità (una ogni 2-3 capitoli max).
8. **Nel libro stampato:** il riferimento alla traccia è discreto — un piccolo ∞ a
   margine con QR, mai un invito esplicito ("ascolta ora!") che romperebbe l'immersione.

---

## COLLEGATO A

MUSICA_UNIVERSO · SCENE_MADRI · ARCHITETTURA_EMOTIVA · ARCHIVIO_LACRIME
DIALOGHI_FONDATIVI · CITAZIONI/FRASI_IMMORTALI · COSA_NON_FARE · BELLEZZA_STILISTICA
CLAUDIO_TERZI · RAFFAELLO_CANTARELLI · KAOS · LILA · ARCHITETTI
ULTIMA_PAGINA · STRATEGIA_TRANSMEDIALE · LETTORE_E_OPERA
