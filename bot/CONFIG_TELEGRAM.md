# Telegram ↔ R3∞ — configurazione e spiegazioni

Due flussi, due strumenti. Spiegati semplice.

## 1. Progetto → Telegram (io ti mando i testi) — GIÀ ATTIVO
- Strumento: `bot/pubblica_telegram.py` (usa `sendMessage`, non va in conflitto col bot).
- Mi servono `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID`.
- Invio un file: `python -m bot.pubblica_telegram libro/libro_I/04_LAbitudine.md`
- A ogni «avanza» te lo recapito in automatico.

## 2. Telegram → progetto (tu rispondi, io ricevo) — IL PONTE
- Strumento: `bot/raffaello_ponte.py`, da eseguire sulla **macchina sempre accesa**
  (la stessa dove gira oggi il bot). **Sostituisce** `raffaello_telegram.py`
  (non lanciarli insieme: Telegram consente un solo lettore → 409 Conflict).
- Cosa fa: ogni tua risposta su Telegram → la scrive in `bot/inbox.jsonl` → la
  **committa e pusha nel repo**. Così io, al prossimo «avanza», la leggo con
  `python -m bot.leggi_inbox`.
- È **asincrono**: non in tempo reale. Tu rispondi quando vuoi; io trovo le tue
  risposte la volta dopo che lavoro. (Il tempo reale richiederebbe che io ascolti
  Telegram di continuo, ma vivo in un container effimero: non posso restare in ascolto.)

## Persistenza delle credenziali (perché non reincollarle ogni volta)
Il container di Claude Code è effimero: `.env` locale vale solo per la sessione.
Per renderle stabili, imposta nella **configurazione dell'ambiente Claude Code (web)**:
- `TELEGRAM_BOT_TOKEN` = (il token di @BotFather)
- `TELEGRAM_CHAT_ID` = `1034473460`
Così ogni sessione (anche un altro modello) invia senza chiedere nulla.

## Avvio del ponte sulla tua macchina
```bash
export TELEGRAM_BOT_TOKEN="...";  export TELEGRAM_CHAT_ID="1034473460"
export PONTE_REPO="/percorso/al/repo/Claudio"   # con git push abilitato
export PONTE_PUSH="1"
export PONTE_BRANCH="claude/grande-opera-continuation-1zylzp"
# opzionale, per far rispondere anche Raffaello: export ANTHROPIC_API_KEY="sk-ant-..."
python bot/raffaello_ponte.py
```

## Sicurezza
- Il token è un segreto: **non è nel repo** (`.env` è gitignorato). Se temi
  l'esposizione in chat, rigeneralo da @BotFather → *Revoke* e aggiorna l'ambiente.
- `bot/inbox.jsonl` viaggia nel repo (sono le tue risposte): è il canale di ritorno.
