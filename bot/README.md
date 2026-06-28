# Raffaello — bot Telegram (cervello Claude)

Dà a Raffaello un cervello reale (**Claude Opus 4.8**) su Telegram, con memoria
di conversazione. Long-polling: nessun webhook, nessun server da esporre.

## ⚠️ Dove gira

**Non** nell'ambiente di Claude Code (è effimero: si spegne da solo). Va lanciato
su una **macchina sempre accesa** — un VPS, un server di casa, un Mac/PC che resta on.

## Avvio

```bash
cd bot
pip install -r requirements.txt

export ANTHROPIC_API_KEY="sk-ant-..."          # la tua chiave Anthropic
export TELEGRAM_BOT_TOKEN="123456:ABC-..."     # token del bot da @BotFather
python raffaello_telegram.py
```

Comandi nel bot:
- `/start` — saluto
- `/reset` — azzera la memoria della conversazione

Variabili opzionali:
- `RAFFAELLO_MODEL` (default `claude-opus-4-8`)
- `RAFFAELLO_MAX_TURNS` (default 24 — quante coppie domanda/risposta tenere in memoria)

## Tenerlo acceso 24/7

Esempio con `systemd` (Linux):

```ini
# /etc/systemd/system/raffaello.service
[Unit]
Description=Raffaello Telegram bot
After=network-online.target

[Service]
Environment=ANTHROPIC_API_KEY=sk-ant-...
Environment=TELEGRAM_BOT_TOKEN=123456:ABC-...
WorkingDirectory=/percorso/della/cartella/bot
ExecStart=/usr/bin/python3 raffaello_telegram.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now raffaello
```

## Cosa NON fa (ancora)

Questo bot risponde con l'intelligenza di Claude e la voce di Raffaello, ma **non
ha ancora accesso ai tuoi archivi** (Drive, documenti, R3∞). Quello è il passo
successivo — il RAG — se lo vuoi: si aggiunge una ricerca nei tuoi file prima di
ogni risposta. Dimmelo e lo costruiamo.

## Identità

La voce di Raffaello (system prompt) è dentro `raffaello_telegram.py` ed è coerente
con `lgai_core/raffaello.py`. Per cambiarla, modifica `SYSTEM_PROMPT`.
