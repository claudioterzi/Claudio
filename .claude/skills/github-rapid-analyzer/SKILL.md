---
name: github-rapid-analyzer
description: Analisi rapida R³∞ di repository, commit, PR e diff GitHub con provenienza verificata. Usare quando si revisiona una PR o un commit, si valuta la prontezza al merge, si controllano CI/check o si cerca il punto di revisione più rilevante in un diff.
---

# GitHub Rapid Analyzer (replica Claude Code)

Fonte canonica: `skills/github-rapid-analyzer/SKILL.md`. **Leggerla per intero prima di procedere**; in caso di divergenza vale la versione canonica.

## Flusso operativo
`changed_files → checks/statuses → focus Jev → diff mirato → falsificatore → decisione`

1. Raccogliere i fatti GitHub autorevoli (strumenti `mcp__github__*`): SHA base/head, file modificati, diff, check/status, mergeability, review.
2. Costruire il pacchetto limitato:
   ```python
   from sdq1.github_rapid_analyzer import build_github_state, assess_github_state, rapid_plan
   state = build_github_state(repository=..., target=..., changed_files=..., checks=..., statuses=...)
   advisory = assess_github_state(state)   # Jev via TypeSafe, solo consultivo
   plan = rapid_plan(state, advisory)
   ```
3. Se Jev non è configurato/disponibile (`status != "evaluated"`), passare subito alla revisione deterministica.
4. Ispezionare prima i file/check di massimo valore indicati da `plan["focus"]`.
5. Applicare P5/P6: nessuna affermazione su merge, CI verde, deploy, permessi o sicurezza senza prova GitHub.
6. Materiale privato R³∞: classificare PUBLIC | PRIVATE | SEALED; in pubblico solo hash/riferimenti.

Regola capillare: riusare questo analizzatore condiviso, non creare un altro motore di revisione GitHub.
