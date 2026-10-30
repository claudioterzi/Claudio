# Prova SFTP su loopback — 30 ottobre 2026

Richiesta: «Testa ora», dopo il merge #164. Sorgente testato: `aaaa5c356fab5a6ce735d89094dbca6192fac1cf` (main recuperato nuovamente).

## Esiti osservati

- Suite IONOS ripetuta sul main: **52 passati, 6 sotto-test**.
- Probe con un vero server SSH/SFTP Paramiko 5.1.0 legato esclusivamente a `127.0.0.1`, host key temporanea fissata in known_hosts e credenziali casuali effimere: **3/3 casi passati**.
- Pubblicazione normale: trasferimento reale, nuovo contenuto riletto dal filesystem del server; rollback con ripristino del contenuto precedente.
- Rename staging→target respinto dal server: upload fallito, recupero riuscito e vecchio contenuto presente.
- Rename di pubblicazione e rename di recupero entrambi respinti: nessun falso successo, richiesta esplicita di recupero manuale e copia precedente conservata.

Il probe non sostituisce i metodi del deployer con mock: usa IONOSSFTPDeployer e le connessioni Paramiko reali. Il server di prova inietta i due errori come risposte SFTP. Il filesystem, le chiavi e le credenziali temporanee vengono eliminati a fine prova. Il processo ha terminato con exit code 0. Lo stderr conserva due messaggi di reset connessione durante la chiusura dei trasporti; non sono soppressi né interpretati come ulteriori casi riusciti.

## Limite della prova richiesta sull'hosting

**Nessun server IONOS è stato contattato.** Non risultano variabili IONOS configurate nell'esecutore. Sul PC Claudio online sono stati controllati soltanto metadati di configurazione: nessuna variabile IONOS nei livelli Process/User/Machine, nessuna sessione WinSCP, nessun file SSH config o configurazione FileZilla. Questo controllo non dimostra assenza di credenziali in qualsiasi altro luogo.

Per completare il collaudo IONOS serve un accesso SFTP/SSH utilizzabile, con verifica della host key, e una cartella dedicata estranea al sito attivo. La presenza di un dominio IONOS non prova che sia disponibile un servizio di hosting con tale accesso. Nessun DNS, sito, account o file remoto è stato modificato.

## Riproduzione

In un ambiente con Paramiko installato: `python docs/evidenze/R3_IONOS_SFTP_LOOPBACK_20261030/probe.py`. La prova usa solo loopback e directory temporanee. [Risultato strutturato](result.json), [stderr](transport-stderr.log). Non prova FTPS reale, server IONOS, crash persistente o mutua esclusione di publisher concorrenti.
