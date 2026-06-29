# Roadmap R³∞

## Fatto (0.1.0)
- Core: engine + kill switch, scacchiera n=8, Protocollo Rosso, pipeline persistente.
- Riti: Rosso / Raffaello / Updater / Applica + mapping comandi.
- App: CLI, pattern controller-service-repository.
- Test quiet (-q): 19 verdi. CI/Release workflow.

## Prossimo
- Collegare `Updater` all'indicizzatore reale del progetto (memoria condivisa).
- Collegare `Applica` a commit/push controllati.
- Service esposto via API HTTP (riusa il controller).
- Persistenza dello stato del core tra esecuzioni (oltre alla pipeline).

## Inevitabili
- Mantenere il kill switch come invariante: nessuna evoluzione lo aggira.
- Determinismo per seed nei test.
