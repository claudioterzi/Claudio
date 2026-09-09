# Ripristino del percorso di composizione

Segnalazione: la richiesta di un profumo ispirato a Chanel N° 5 sembra non funzionare dopo gli interventi grafici.

Riprodotto nel browser: con intenzione valorizzata e nome cliente vuoto, il pulsante resta nell’Atelier e richiede obbligatoriamente il cliente. Questo vincolo è stato aggiunto con la personalizzazione del flacone. Prima il nome non era richiesto.

Verifica separata del server: POST /profumo con la stessa intenzione e senza cliente risponde HTTP 200 con L’Esprit du Numéro Cinq, riferimento olfattivo e formula. Non è stata dimostrata l’equivalenza olfattiva con il prodotto citato.

Correzione circoscritta: cliente facoltativo; identificativo generato dal server quando randomUUID non è disponibile nel browser. Restano invariati compositore, formule, gestione archivio e grafica del risultato. Non è stato necessario ripristinare l’intero backend. Test di regressione: invio senza cliente con e senza UUID disponibile; intenzione conservata.

L’archivio permanente rimane non configurato. La correzione riguarda l’avvio della composizione, non il salvataggio permanente.
