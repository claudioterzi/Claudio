# Riti e trigger

I riti sono parole che attivano azioni del motore. Registro in
`rituals/triggers.py`.

| Rito        | Azione                                              |
|-------------|-----------------------------------------------------|
| `Rosso`     | esegue il Protocollo Rosso sullo stato corrente     |
| `Raffaello` | un passo del RAFFAELLO CORE                          |
| `Updater`   | segna che il sistema va ri-sincronizzato            |
| `Applica`   | conferma e applica lo stato (committabile)          |

## Mappatura comandi → riti (`rituals/mapping.py`)

| Comando        | Rito      |
|----------------|-----------|
| `pytest -q`    | Updater   |
| `git push`     | Applica   |
| `rosso`        | Rosso     |
| `raffaello`    | Raffaello |

Esempio:

```python
from rituals.triggers import esegui_rito
from rituals.mapping import risolvi

esegui_rito(risolvi("pytest -q"))   # → Updater
```

Sequenza completa di attivazione: `python -m rituals.scripts.attiva`
(Rosso → Raffaello → Updater → Applica).
