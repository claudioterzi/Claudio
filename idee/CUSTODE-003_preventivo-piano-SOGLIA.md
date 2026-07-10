# CUSTODE-003 — SOGLIA: preventivo e piano d'azione

> Sottosistema micro-tag RFID UHF + varco d'uscita con direzione.
> Data: 2026-07-10. Riferimento tecnico: CUSTODE-001. Prototipo: `custode/varco.py`.
> Ipotesi di base: casa tipo 2 camere, ~150 oggetti taggati, 1 porta d'uscita.

---

## 1. Preventivo

### 1.1 Configurazione A — "Palmare" (senza varco, entry level)

Verifica RFID al turnover: si passa il lettore palmare per le stanze e in
pochi secondi si sa quali tag rispondono e quali mancano. Nessuna
installazione fissa, nessun tema privacy in tempo reale.

| Voce | Dettaglio | Costo |
|---|---|---:|
| 150 inlay UHF carta (EPC Gen2) | 0,05–0,25 $/pz, adesivi, invisibili applicati | 10–40 € |
| 10 tag on-metal | per elettronica e oggetti metallici | 15–40 € |
| 5 micro-tag Murata 1,25 mm | oggetti piccoli di valore (lettura a contatto) | 10–25 € |
| Lettore palmare UHF Bluetooth | si collega allo smartphone | 250–550 € |
| Applicazione + registro tag | ~2 min/oggetto ≈ 5 h di lavoro; registro con `custode.varco.RegistroTag` | 0 € (tempo) |
| **Totale configurazione A** | | **~285–655 €** |

Costo ricorrente: ~10–20 €/anno (sostituzione tag rovinati). Zero costi API.

### 1.2 Configurazione B — "Varco" (completa, tempo reale)

Tutto quanto sopra, più il controllo in tempo reale sulla porta d'uscita.

| Voce | Dettaglio | Costo |
|---|---|---:|
| Configurazione A | base necessaria | 285–655 € |
| Reader UHF fisso 2 antenne | discreto: antenne a soffitto/stipite invece dei pannelli da biblioteca | 500–1.500 € |
| Coppia sensori IR direzionali | distinguono uscita da ingresso | 30–80 € |
| Gateway (Raspberry Pi) | riceve gli eventi EPC (LLRP/MQTT) e fa girare `custode.varco` | 60–100 € |
| Installazione elettricista | alimentazione + canaline alla porta | 150–400 € |
| **Totale configurazione B** | | **~1.025–2.735 €** |

Costo ricorrente: ~20–40 €/anno (elettricità del reader ~10 W, manutenzione,
tag). Notifiche push: gratis via gli stessi canali del monitoring SDQ-1.

### 1.3 Confronto e raccomandazione

| | A — Palmare | B — Varco |
|---|---|---|
| Costo avvio | ~285–655 € | ~1.025–2.735 € |
| Rileva la mancanza | al turnover | **nel momento in cui l'oggetto esce** |
| Prova per il rimborso | "manca il tag X" | evento con timestamp mentre l'ospite è ancora in soggiorno |
| Installazione | nessuna | elettricista + configurazione |
| Privacy | banale | informativa obbligatoria nell'annuncio/contratto |

**Raccomandazione**: partire con la **A** (spesa contenuta, valida il
sistema di tagging e il registro), aggiungere il varco (**B**) sulla casa
dove il rischio furti è reale. Il software è già pronto per entrambe:
`Varco.evento()` riceve indifferentemente letture dal palmare o dal gate.

---

## 2. Piano d'azione

### Fase 0 — Fondamenta (fatto ✅)
`custode/varco.py`: registro tag, eventi EPC con direzione, allarmi solo in
uscita, EPC sconosciuti ignorati (minimizzazione dati). Simulatore incluso.

### Fase 1 — Campionario e test (settimane 1–2)
1. Ordinare il campionario: 20 inlay carta di 2–3 modelli diversi, 3 tag
   on-metal, il lettore palmare (ordine unico ~300–400 €).
2. Test di lettura reale: inlay dentro una pagina di libro, sotto un
   cassetto, dietro un quadro, su bottiglia (liquidi), su lampada (metallo).
   Misurare la distanza di lettura effettiva per posizione.
3. **Criterio di uscita**: ≥95% dei tag campione letti dal palmare a
   distanza di stanza (2–4 m) nella posizione d'applicazione reale.

### Fase 2 — Tagging della casa pilota (settimane 3–4)
1. Lista oggetti da proteggere con Claudio: valore > ~20 € oppure
   "sparizione frequente" (telecomandi, phon, adattatori, libri, biancheria).
2. Applicazione nascosta + registrazione: EPC → oggetto → zona → valore
   (`RegistroTag`; le zone coincidono con quelle di OCCHIO: stesso ID).
3. Collegare il palmare al registro: scansione stanza → confronto → lista mancanti.
4. **Criterio di uscita**: verifica completa della casa col palmare in
   ≤10 minuti, zero falsi mancanti.

### Fase 3 — Varco sulla porta (settimane 5–8, solo config. B)
1. Scegliere il reader (criteri: LLRP o MQTT nativo, 2 porte antenna,
   alimentazione PoE) e l'elettricista.
2. Installazione discreta: antenne allo stipite/soffitto, sensori IR ai lati.
3. Code scrive l'adattatore eventi reader→`Varco.evento()` sul Raspberry
   (MQTT), con notifica push a Claudio.
4. Taratura: potenza antenna per coprire la soglia senza leggere i tag
   fermi in soggiorno; test con tag in tasca/zaino/valigia.
5. **Criterio di uscita**: 20 transiti di prova — 100% dei tag in uscita
   rilevati, zero allarmi con tag fermi in casa, direzione corretta ≥95%.

### Fase 4 — Conformità e messa in servizio (settimana 9)
1. Informativa privacy: riga nell'annuncio Airbnb + paragrafo nel
   contratto di soggiorno + cartellino alla porta ("sistema antitaccheggio
   RFID sugli oggetti della casa — nessuna telecamera, nessun dato personale").
2. Registro trattamento minimo (GDPR): si conservano solo eventi
   EPC+timestamp, cancellazione a 30 giorni salvo contestazioni.
3. Procedura per l'allarme vero: notifica → messaggio cortese all'ospite
   ("ci risulta che un libro sia finito per sbaglio nel bagaglio…") →
   escalation Airbnb solo con evidenza doppia OCCHIO+SOGLIA.

### Rischi e contromisure

| Rischio | Contromisura |
|---|---|
| Tag trovato e staccato dall'ospite | applicazione nascosta; OCCHIO rileva comunque la mancanza al turnover |
| Metallo/liquidi schermano la lettura | tag on-metal dedicati; test di Fase 1 per posizione |
| Falsi allarmi (tag fermo vicino alla porta) | taratura potenza + IR direzionale + non taggare oggetti che vivono vicino all'ingresso |
| Ospite percepisce sorveglianza | comunicazione trasparente: protegge anche l'ospite da addebiti ingiusti |
| Reader fisso costoso sbagliato | comprarlo solo dopo che Fase 1–2 hanno validato tag e registro |

### Metriche di successo
- Copertura: ≥90% del valore "portabile" della casa taggato.
- Verifica palmare ≤10 min; varco: 100% rilevamento in uscita nei test.
- 1 oggetto recuperato con messaggio pre-escalation = ROI immediato
  (un phon + una trapunta ≈ 150 € ≈ metà configurazione A).

---

## 3. Sequenza consigliata complessiva (OCCHIO + SOGLIA)

| Settimana | OCCHIO | SOGLIA |
|---|---|---|
| 1–2 | mappatura zone + baseline + test precisione | campionario tag + test lettura |
| 3–4 | protocollo turnover + 5 prove | tagging casa + registro + palmare |
| 5–8 | motore denso + tuning | (opz.) installazione varco + taratura |
| 9 | — | privacy + messa in servizio |
| 10+ | report integrato con evidenza doppia (già pronto in `custode/report.py`) | |

Budget totale del pilota: **~320–800 €** (OCCHIO + SOGLIA config. A);
con varco completo: **~1.100–2.900 €**. Costi ricorrenti sotto i
**300 €/anno** in ogni scenario.
