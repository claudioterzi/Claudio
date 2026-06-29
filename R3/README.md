# R³∞ — Test R3

Motore centrale R³∞: **RAFFAELLO CORE**, scacchiera quantica, Protocollo Rosso e
livello rituale. Architettura pulita, test in quiet mode, kill switch sempre
presente (controllo umano).

## Struttura

```
r3_core/     motore: engine (loop, stato, kill switch), pipeline, protocol_rosso,
             scacchiera (n=8), config (QSTP v11.0 APQ+)
rituals/     trigger (Rosso, Raffaello, Updater, Applica), mapping comandi→azioni
apps/        cli/ (comandi rituali) · service/ (controller-service-repository) · sandbox/
tests/       test quiet (-q) del core e dei riti
docs/        architettura, riti, roadmap
```

## Uso

```bash
pip install -e .[dev]
pytest -q                       # tutti i test
python -m apps.cli.r3_cli loop 10
python -m apps.cli.r3_cli trigger Rosso
python -m apps.cli.r3_cli kill  # dimostra il kill switch
```

## Principi

- **Kill switch** sempre disponibile: il loop si ferma all'istante. Il controllo
  resta umano (limite non negoziabile).
- **Determinismo**: a parità di `seed` la scacchiera è riproducibile.
- **Protocollo Rosso**: Rivelazione → Direzione → Mutazione → Fusione.
- **Riti**: gesti operativi (anche `pytest -q`, `git push`) mappati ad azioni R3.
