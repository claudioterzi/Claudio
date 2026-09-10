# Archivio persistente — configurazione pronta per l’attivazione

Claudio Terzi · Protocollo Rosso Rosso Rosso · verifica 2026-09-09.

## Aggiornamento 2026-09-10 — collegamento completato, test online in corso

Dopo «Fatto» dell’utente, installazione e database esistente verificati.
Risorsa `store_04ygMomSUbCgQkT3`, nome `upstash-kv-coffee-lens`, installazione
`icfg_9piBJI2TaOe0EPLxV5EtGc1M`. Piano Free, regione iad1 selezionata
nell’account, eviction false, autoUpgrade false, prodPack false.
Collegata al progetto Claudio, esclusivamente in produzione. Le variabili
REDIS_URL, KV_URL e REST sono state iniettate dall’integrazione. REDIS_URL
usa TLS. Creati due segreti server sensitive per hash password e sessioni.
Nessun database duplicato; nessun piano a pagamento attivato.

La documentazione sotto conserva la proposta precedente fra1, che non è stata
applicata perché il database era già stato creato dall’utente in iad1.
25 test archivio/recupero e 4 sottotest superati. Ping TCP dal laboratorio
non riuscito (ConnectionError): attendere il collaudo del runtime Vercel prima
di dichiarare attivo il salvataggio. Non sono ancora verificati backup e
ripristino del provider.

## Stato verificato in questa ripresa

- GitHub main: `7911b58e5c6357d86949f8a3e0abb02ca0766e4e`; stato Vercel success.
- GET delle configurazioni integrazioni del team: HTTP 200, elenco vuoto.
- GET del prodotto Upstash e dei piani Redis: HTTP 200.
- Nessuna creazione di database, modifica di credenziali o accettazione delle
  condizioni effettuata. Il precedente rifiuto per AI Gateway resta distinto
  e non è stato aggirato o ritentato.

## Configurazione proposta, non ancora applicata

| Campo | Valore |
| --- | --- |
| Progetto | Claudio (`prj_NfWglC7AYRQs6W5pJBB6nf3lDqXN`) |
| Team | claudio-terzi-s-projects (`team_dO423fnEAekxtan0rF3u2CQt`) |
| Integrazione | upstash (`oac_V3R1GIpkoJorr6fqyiwdhl17`) |
| Prodotto | upstash-kv (`iap_gpfB8wWHssmOi6P1`) |
| Nome risorsa proposto | terzi-archivio |
| Piano per il collaudo | free |
| Regione proposta | fra1 |
| Eviction dei dati a capacità esaurita | false |
| Auto Upgrade | false |
| Prod Pack | false |

L’API del piano Free dichiara 500.000 comandi mensili, una sola banca dati per
account, nessun metodo di pagamento richiesto e preautorizzazione zero. Il
piano è presentato per prove. Upstash documenta persistenza su disco sempre
attiva; la replica aggiuntiva è riservata ai piani a pagamento. Prima di
affidargli l’archivio definitivo, collaudare anche backup, limiti e ripristino.
Non usare il database temporaneo di 72 ore pubblicizzato per gli agenti come
archivio permanente.

## Passaggio richiesto all’utente

Aprire [Upstash for Redis su Vercel](https://vercel.com/marketplace/upstash/upstash-kv),
avviare Install nel proprio account e accettare le condizioni dell’integrazione
per il team sopra. Per il collaudo scegliere Free se richiesto; non selezionare
upgrade o Prod Pack. Nessuna password o credenziale va incollata nella chat.

Il codice ufficiale Vercel, in modalità agente senza un’installazione esistente,
restituisce `INTEGRATION_TERMS_ACCEPTANCE_REQUIRED` e `userActionRequired: true`.
Non simulare l’accettazione manuale attraverso parametri REST. La skill Vercel
Marketplace richiede di lasciare all’utente questo passaggio dell’account.

## Ripresa tecnica dopo l’accettazione

1. Rileggere le installazioni: se la risorsa è già stata creata dall’utente,
   usarla e verificarne piano e impostazioni; non crearne un duplicato.
2. Collegare il database al progetto e verificare KV_URL/REDIS_URL in produzione
   senza mostrarne il valore. Il backend già supporta entrambe le variabili.
3. Configurare la credenziale dell’archivio attraverso segreti server, poi
   collaudare sessione, seriale immutabile, recupero e revoca. Non hardcodificare
   nel frontend il codice citato in chat e non trattare questa accettazione
   come autorizzazione a creare credenziali per altri servizi.
4. Usare una creazione fittizia per verificare riapertura da una seconda sessione,
   indisponibilità controllata, limiti login e backup/ripristino su destinazione
   di prova. Mantenere il recupero JSON disponibile.
5. Pubblicare solo lo stato effettivamente verificato. Il generatore fotografico
   AI resta una dipendenza separata, non attivata da questo collegamento.

## Fonti

- [Configurazioni Vercel](https://vercel.com/docs/rest-api/integrations/get-configurations-for-the-authenticated-user-or-team)
- [Procedura ufficiale Vercel per le condizioni](https://github.com/vercel/vercel/blob/main/packages/cli/src/util/integration/accept-terms-via-browser.ts)
- [Percorso di installazione](https://github.com/vercel/vercel/blob/main/packages/cli/src/commands/integration/add-auto-provision.ts)
- [Persistenza Upstash](https://upstash.com/docs/redis/features/durability)
- [Backup e ripristino](https://upstash.com/docs/redis/features/backup)
