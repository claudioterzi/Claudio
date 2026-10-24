---
name: google-drive-rapid-analyzer
description: Analisi rapida R³∞ di cartelle, file e revisioni Google Drive preservando provenienza, privacy e continuità GitHub↔Drive. Usare quando si controlla un file o una cartella Drive, si confrontano versioni, si cercano duplicati o divergenze con il repo, o prima di spostare/sovrascrivere un documento su Drive.
---

# Google Drive Rapid Analyzer (replica Claude Code)

Fonte canonica: `skills/google-drive-rapid-analyzer/SKILL.md`. **Leggerla per intero prima di procedere**; in caso di divergenza vale la versione canonica.

## Flusso operativo
`metadata → delta revisioni/cartella → focus Jev → lettura mirata → postcondizione`

1. Leggere i fatti Drive (strumenti `mcp__Google_Drive__*`): metadati, cartella madre, permessi, revisioni, contenuto limitato, allineamento con l'artefatto GitHub.
2. Costruire il pacchetto limitato:
   ```python
   from sdq1.drive_rapid_analyzer import build_drive_state, assess_drive_state, rapid_plan
   state = build_drive_state(target=..., metadata=..., revisions=..., folder_items=..., git_alignment=...)
   advisory = assess_drive_state(state)    # Jev via TypeSafe, solo consultivo
   plan = rapid_plan(state, advisory)
   ```
3. Jev non stabilisce proprietà, condivisione, revisione, completezza, posizione canonica né esito di sincronizzazioni: servono prove Drive.
4. Prima di ogni modifica: verificare destinazione, versione, permessi e autorizzazione. Dopo: rileggere metadati/revisione come postcondizione.
5. Privacy: PUBLIC | PRIVATE | SEALED. Il materiale privato non va in cartelle pubbliche per sincronizzare.
6. Divergenza GitHub↔Drive = da risolvere, mai sovrascrivere alla cieca nessuno dei due lati.

Regola capillare: riusare questo analizzatore condiviso, non creare un altro motore Drive globale.
