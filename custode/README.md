# custode/ — prototipo CUSTODE-001

Sistema integrale di custodia per case Airbnb. Due sottosistemi che si
coprono a vicenda, un unico report di check-out.

> Studio completo (tecnologie, hardware, costi, privacy, roadmap):
> [`idee/CUSTODE-001_sistema-custode-airbnb.md`](../idee/CUSTODE-001_sistema-custode-airbnb.md)

## Sottosistemi

- **OCCHIO** — inventario fotografico di precisione a zone.
  `visione.py` (motori di conteggio: Claude vision oppure stub) +
  `confronto.py` (baseline vs check-out → discrepanze).
- **SOGLIA** — micro-tag RFID UHF + varco d'uscita con direzione.
  `varco.py` (registro tag, eventi EPC, allarmi solo in uscita,
  EPC sconosciuti ignorati per minimizzazione dati).
- **Report** — `report.py` incrocia le due fonti: una mancanza vista
  in foto E confermata dal varco è evidenza doppia per AirCover/deposito.

- **Catalogo** — `catalogo.py`: la scheda di ogni oggetto taggato
  (per un libro: autore, ISBN, valore, **dove è nascosto il tag** —
  es. "incollato tra pagina 142 e 143"), persistenza JSON, e il metodo
  `analizza_mancanti(epc_letti)`: catalogo − letti = mancanti.
- **Schedatura rapida** — `schedatura.py`: due foto e basta. Foto al
  frontespizio → la visione compila la scheda (titolo, autore, ISBN,
  stima del valore); foto al tag → legge l'EPC stampato sull'inlay e
  lo associa. ~20 secondi a oggetto.
- **Web** — `web.py` (Flask, mobile-first): da iPhone/Android la
  fotocamera si apre direttamente dai campi foto (`capture`).
  Schedatura rapida, scheda precompilata da controllare e salvare,
  e il bottone **"🔍 Analizza oggetti mancanti"** (in v2 il lettore
  Bluetooth riempirà il campo EPC da solo).

## Uso

```bash
python -m custode.demo          # demo completa, senza hardware né API key
python -m custode.test_custode  # test
python -m custode.web           # interfaccia web → http://localhost:5001
```

Con `ANTHROPIC_API_KEY` impostata (e `pip install anthropic`),
`crea_contatore()` usa Claude vision per contare da foto reali;
altrimenti fallback automatico allo stub, come in `sdq1.llm`.

## Stato

v0 — prototipo software. Il collegamento al gate reader UHF reale
(eventi EPC via LLRP/MQTT) è previsto in v2: `Varco.evento()` è già
il punto d'ingresso disegnato per quel flusso.
