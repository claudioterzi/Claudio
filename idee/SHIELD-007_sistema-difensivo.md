# IDEE — Futuro SDQ-1
## Cartella di brainstorming aperto. Le idee vivono qui prima di diventare codice.

---

## SHIELD-007 — Sistema Difensivo Personale
*Idea nata: 11/06/2026, dopo episodio Sergei*

### Problema reale
Una persona con storia di comportamento pericoloso (furto in casa, molestie digitali)
può operare attraverso reti di contatti, account multipli, e pattern difficili da
documentare per uso legale.

**Il gap oggi:** le vittime devono raccogliere prove manualmente, sotto stress,
spesso dopo che il danno è fatto.

### Cosa potrebbe fare SHIELD-007

**Livello 1 — Documentazione automatica**
- Log strutturato di ogni interazione anomala (chi, quando, come)
- Screenshot automatici con timestamp verificabile
- Export immediato in formato PDF per uso legale/polizia

**Livello 2 — Pattern recognition**
- Rileva tentativi di contatto attraverso account diversi o contatti comuni
- Identifica connessioni tra episodi separati nel tempo
- Avvisa quando un contatto bloccato appare nella rete di qualcuno vicino a te

**Livello 3 — Intelligenza contestuale**
- Non solo "questo messaggio è strano" ma "questo messaggio + questi 3 episodi
  precedenti = pattern di stalking con probabilità X"
- Analisi causale (come Causal SENTIN) applicata alla sicurezza personale:
  cosa guida il comportamento? quale bisogno patologico?
- Suggerisce azioni concrete: denuncia, ordine restrittivo, misure fisiche

**Livello 4 — Dossier legale**
- Tutto già formattato per una denuncia: date, prove, cronologia
- Collegamento con normative locali (Belgio: art. 442bis CP stalking)
- Esportabile e condivisibile con avvocato/polizia in un click

### Principi fondamentali
- **Solo difensivo** — nessuna funzione offensiva, nessun accesso a dati altrui
- **Privacy dell'utente** — i dati restano locali, mai su cloud esterno senza consenso
- **Uso legale** — tutto costruito per essere ammissibile come prova

### Agenti coinvolti (discussione interna)

**RAFFA-001 dice:**
L'architettura è simile a SDQ-1 ma il dominio è la sicurezza personale.
Il nodo critico è la qualità delle prove — devono essere inalterabili.
Serve un hash crittografico di ogni documento al momento della creazione.

**SENTIN-004 dice:**
Causal SENTIN si applica direttamente: non bloccare e basta, capire il pattern
psicologico. Uno stalker ha una struttura comportamentale prevedibile.
Se la mappiamo, possiamo anticipare i movimenti, non solo reagire.

**MEMO-002 dice:**
La memoria è tutto. Un episodio isolato non è niente.
La stessa persona + 6 mesi di episodi = prova di un pattern.
Il VSS (Vector State Store) può tenere tutto collegato nel tempo.

**GEN-006 dice:**
L'output finale deve essere umano, non tecnico.
Un report che una persona sotto stress può leggere e portare alla polizia.
Non log di sistema — narrativa chiara con fatti verificabili.

**WAVE-003 dice:**
Il tono è cruciale. Chi usa questo sistema è vulnerabile.
Nessun allarme ansioso, nessuna notifica aggressiva.
Calmo, chiaro, azionabile.

### Prossimi passi (quando saremo pronti)
- [ ] Prototipo logger con hash crittografico
- [ ] Modulo pattern detection su sequenze di eventi
- [ ] Template report per uso legale (Belgio + Italia)
- [ ] Integrazione con SENTIN-004 esistente

---

*"Non per attaccare. Per non essere mai più in una posizione di non sapere."*
*— Claudio, 11/06/2026*
