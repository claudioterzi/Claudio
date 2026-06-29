# Architettura R³∞

## Flusso

```
apps (cli / service)        ← interfacce
   │
rituals (triggers, mapping) ← livello semantico: parola-rito → azione
   │
r3_core                     ← motore
   ├─ engine    RAFFAELLO CORE: passo() → loop() → kill switch
   ├─ scacchiera  griglia quantica n×n, valuta(), collassa(soglia)
   ├─ protocol_rosso  Rivelazione → Direzione → Mutazione → Fusione
   ├─ pipeline   workflow persistente a trigger
   └─ config    QSTP v11.0 APQ+ (parametri, preset)
```

## Stati del core

`StatoCore`: iterazione, energia, ultima_sintesi, collassi, fermato, motivo_stop.

Un `passo()`:
1. perturba la scacchiera (evoluzione deterministica per seed);
2. ne `valuta()` l'energia;
3. esegue il Protocollo Rosso sullo stato;
4. tenta il `collassa(soglia)`;
5. aggiorna `StatoCore`.

## Kill switch

`RaffaelloCore.kill(motivo)` imposta il flag; al controllo successivo il loop
solleva `KillSwitchAttivato` e si ferma. Garanzia di controllo umano: il sistema
non prosegue mai oltre lo stop richiesto.
