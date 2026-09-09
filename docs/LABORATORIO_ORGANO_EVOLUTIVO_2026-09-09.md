# Laboratorio e organo evolutivo — 9 settembre 2026

Concept e direzione: Claudio Terzi · © 2026 Claudio Terzi.

## Dosi

La ricetta resta la proporzione originale delle preparazioni in massa.
Il calcolatore usa massa finita = volume × densità misurata; miscela = massa
finita × concentrazione/100; pesata ingrediente = miscela × parti/100;
supporto aggiuntivo = massa finita − miscela. Non usa equivalenze ml = g.
Concentrazione iniziale di progetto 20% p/p della miscela delle preparazioni,
modificabile: non equivale alla concentrazione delle sostanze pure.
La densità è richiesta per le colonne da 50, 100 e 200 ml; in alternativa si
può lavorare su lotti di 50, 100 e 200 grammi senza ipotizzare una densità.
Preparazioni e supporto vanno dichiarati. Il codice TRZ1 conserva la ricetta;
il file di laboratorio conserva separatamente i parametri del lotto e riporta
production_validated=false. Nessuna certificazione IFRA automatica.

Fonte tecnica: https://ifrafragrance.org/using-the-standards
Le restrizioni si valutano sul prodotto finito e includono le contribuzioni
provenienti da altre materie, come gli oli essenziali. Il catalogo non dispone
ancora delle specifiche complete delle forniture e delle diluizioni reali.

## Prezzi

Listino di progetto fisso: 50 ml 220 EUR; 100 ml 340 EUR; 200 ml 590 EUR.
Scelta di posizionamento creativo autorizzata da Claudio, non prezzo dedotto
matematicamente dalla formula. Non dimostra margini, vendibilità o domanda.
Prima di un preventivo vincolante confermare costi effettivi, confezione,
lavorazione e imposte. Non è stato aggiunto alcun pagamento automatico.
Riferimento primario consultato il 2026-09-09: Maison Francis Kurkdjian,
Baccarat Rouge 540 EDP, 70 ml 265 EUR e 200 ml 525 EUR:
https://www.franciskurkdjian.com/eu-fr/p/baccarat-rouge-540-eau-de-parfum-RA12232.html
Il riferimento serve a confrontare il posizionamento, non a promettere qualità
identica o a copiare il prodotto.

## Continuità

Il ripristino foto è riuscito nel browser: Ciel de Forges, 12 materie canoniche
su 100 parti. Evidenza in docs/evidenze/PHOTO_TEST_2026-09-09.json.
L’archivio privato e le quote guest richiedono ancora la configurazione
persistente; non vengono presentati come attivi.

## Organo evolutivo

Il registro separa proposte, ammissioni e sospensioni. Solo le materie attive del
catalogo entrano nel compositore e nell’Atelier generato. Le proposte da sole
non entrano in alcuna formula. Nessuna sostanza è stata acquistata né rimossa
dall’inventario corrente. Nuove ammissioni assegnano il numero successivo,
conservano lo snapshot precedente e ne creano uno nuovo; niente riuso degli ID.

Comandi di gestione nel repository, dopo aver raccolto i dati necessari:

```bash
python -m studio.parfums.organo_evolution suspend 146 --reason "Motivazione documentata"
python -m studio.parfums.organo_evolution restore 146 --reason "Motivazione documentata"
python -m studio.parfums.organo_evolution admit EV-001 evidenza-materiale.json
python studio/parfums/genera_atelier.py
python studio/parfums/genera_organo.py
```

Gli esempi di sospensione sono sintassi, non comandi già eseguiti. Pubblicare
catalogo, registro, snapshot e pagine rigenerate nello stesso commit. Non
inserire fatture o dati riservati nell’evidenza pubblica: indicare prodotto,
preparazione e riferimenti tecnici. Per sostituire una fornitura o identità
chimica usare un nuovo ID, mantenendo decodificabili tutte le ricette storiche.

Proposte documentate:
- Nympheal, molecola Givaudan: https://www.givaudan.com/fragrance-beauty/fragrance-ingredients-business/fragrance-molecules/nympheal
- Dreamwood Base, base composta dsm-firmenich: https://studio.dsm-firmenich.com/product/dreamwoodr-base-pe-184270-b
- Paradise Molecule, miscela Fraterworks distinta da Paradisone: https://fraterworks.com/products/paradise-molecule

Sono opportunità da confrontare con l’organo esistente, non miglioramenti
sensoriali già dimostrati. Disponibilità commerciale, lotti, documenti e
preparazione vanno confermati prima dell’ammissione. Il pannello pubblico è
un registro leggibile; non espone comandi amministrativi al visitatore.
