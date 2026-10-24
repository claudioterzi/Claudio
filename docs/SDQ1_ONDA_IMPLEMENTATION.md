# SDQ-1 ONDA/1.0 — Implementazione iniziale e limiti

## Stato
Questa implementazione aggiunge un validatore deterministico e transport-agnostic per la busta ONDA/1.0. Non equivale a un bus Redis distribuito in produzione.

## Regole coperte
- Schema minimo della busta, UUID, correlazione e timestamp ISO-8601 con fuso.
- Validazione dell'epoca corrente e scadenza dei messaggi.
- Tipi e priorità ammesse; payload JSON limitato in byte.
- Solo RAFFA-001 può inviare COMANDO; solo SENTIN-004 può inviare EMERGENZA.
- HEARTBEAT broadcast; COMANDO e RISPOSTA richiedono correlazione.
- Modello di riferimento SENTIN per 3 heartbeat mancati a intervalli di 10 secondi.
- Costruzione degli argomenti Redis SET ... NX EX 30 per lock distribuiti.

## Limiti espliciti
- Nessun client Redis, processo agente, riconnessione o orchestrazione reale viene avviato da questo modulo.
- La regola di autorità deve essere applicata anche al livello di autenticazione/ACL Redis; il campo mittente da solo non autentica un agente.
- La gestione di STOP/RIPRENDI, il cambio d'epoca atomico, l'idempotenza, le risposte obbligatorie ai comandi e la persistenza dei checkpoint richiedono l'adapter runtime e test d'integrazione.
- Il token budget viene lasciato nel payload applicativo: non è contabilizzato da questo modulo.
- Nessun agente riceve permessi di auto-modifica del kernel o delle policy. Il kernel evolutivo esistente resta il gate separato per le proposte di modifica.

## Test
Eseguire:
```bash
python -m unittest tests.test_onda_protocol -v
python -m py_compile sdq1/onda_protocol.py tests/test_onda_protocol.py
```

I test unitari verificano i guardrail del validatore in isolamento; non provano disponibilità Redis né resilienza multi-processo.
