# Ripresa delle creazioni e protezioni dell’archivio

Concept e direzione: Claudio Terzi. Aggiornamento del 9 settembre 2026.

## Funzioni effettive

- `/atelier/riapri` accetta la scheda JSON esportata dall’Atelier, massimo 300 KB.
  Riapre la stessa ricetta e il codice TRZ1, nome cliente, dedica, testi di
  ispirazione e variante Scultura/Essenza. Nessuna chiamata AI e nessuna scrittura
  nell’archivio durante l’importazione.
- La nuova esportazione completa include anche densità, concentrazione,
  supporto e preparazioni compilate nel laboratorio. I vecchi file restano
  leggibili; i dati che non contengono non possono essere recuperati.
- Il controllo verifica il catalogo della revisione TRZ1, ingredienti distinti,
  dosi e totale. Il codice non è una firma dell’autore. La pagina distingue
  una scheda caricata da una registrazione verificata nell’archivio.
- Flacone ricostruito dalla ricetta. Prompt, token di accesso, attestazioni di
  archiviazione e HTML eseguibile presenti nel file non sono accettati come
  autorità. I testi conservano l’escape; le fonti possono usare solo HTTPS.

## Backend privato preparato, non ancora attivato in produzione

- Password hash supportata con `PERFUME_ARCHIVE_PASSWORD_HASH`; compatibilità
  con la precedente password solo server. Nessuna password nel codice pubblico.
- Sessioni di un’ora, identificativi casuali e revoca sul server all’uscita.
  Il cambio della credenziale invalida le sessioni precedenti.
- CSRF per login e logout, cookie HttpOnly/SameSite Strict, Secure su Vercel.
- Limite condiviso atomico: cinque tentativi per indirizzo visto dal runtime e
  trenta complessivi per finestra di 15 minuti. Gli header di inoltro forniti
  dal client non determinano l’identità; gli indirizzi sono pseudonimizzati.
  La configurazione dell’indirizzo reale dietro proxy richiede collaudo quando
  sarà collegato il database; il limite globale resta condiviso.
- Redis in produzione, SQLite solo locale. Un guasto al database non concede
  accesso. CORS pubblico rimosso dalle risposte Atelier/profumo; niente cache,
  niente referrer e protezione dall’incorporamento in altri siti.

## Dipendenze e limiti verificati

La lettura dei nomi delle variabili Vercel con il token autorizzato ha risposto
HTTP 200: nessun REDIS_URL/KV_URL, OPENAI_API_KEY o segreto/password dell’archivio.
Il connettore progetto ha risposto 403. La lettura CLI delle opzioni Upstash non
si è conclusa: autorizzazione di rete annullata. Nessuna risorsa storage è stata
creata, nessuna variabile modificata. Non è stata ripetuta la creazione di AI
Gateway già respinta dall’approvazione automatica per nuovo accesso e costi.

Percorso proposto: Upstash Redis dal Marketplace, collegato a questo progetto;
confermare piano, persistenza, assenza di eviction e backup prima di attivare
la registrazione. Poi configurare credenziale server e collaudare accesso,
salvataggio, riapertura da altro dispositivo e revoca. Le fotografie AI
automatiche necessitano ancora di accesso al servizio immagini e archiviazione.

## Verifica

72 test Python superati. Tre file di test JavaScript superati: invio Atelier,
flaconi e laboratorio. Il file Ferro di Luce scaricato nella sessione precedente
è leggibile, conserva le 12 materie e la variante Essenza. I test verificano
anche codice/ricetta discordanti, materiale sconosciuto, dose NaN, file grande,
markup e URL pericolosi, false attestazioni di accesso, CSRF, revoca della
sessione copiata, scadenza, rotazione password e indisponibilità del database.
Collaudo pubblico completato. Il primo commit `9ab6cbea` è stato pubblicato;
la prima importazione live ha respinto la scheda valida. Correzione `7a450aff`:
il catalogo già incluso nel compositore viene usato solo quando coincide con
la revisione TRZ1; gli snapshot storici restano vincolanti e sono inclusi nella
funzione. Due test aggiunti coprono l’assenza della directory statica e una
revisione storica. Entrambi i commit hanno ricevuto Vercel success.

Prova Chrome completa dopo la correzione: caricamento nativo del vecchio JSON,
riapertura, modifica di dati fittizi di laboratorio, nuova esportazione e
seconda riapertura. Ricetta, codice, dedica e geometria Essenza sono identici
ai dati del file precedente. Recuperati 20%, densità fittizia 0,85, supporto
scelto e una preparazione di prova; le altre 11 rimangono da dichiarare.
Anteprima stampa ricetta verificata con 50/100/200 ml e pesate coerenti.
Nessuna nuova verifica di stampante fisica, Safari/iPhone o WebGL GPU.
La nuova pagina usa l’atmosfera Memoria. L’archivio cloud rimane non attivo.
Evidenze: `docs/evidenze/RECUPERO_TEST_2026-09-09.json` e screenshot associato.

Fonti operative consultate:
- [Vercel: variabili progetto](https://vercel.com/docs/rest-api/projects/retrieve-the-environment-variables-of-a-project-by-id-or-name)
- [Vercel: integrazioni CLI](https://vercel.com/docs/cli/integration)
- [Upstash nel Marketplace Vercel](https://vercel.com/marketplace/upstash)
- [OWASP: autenticazione](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OWASP: CSRF](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
