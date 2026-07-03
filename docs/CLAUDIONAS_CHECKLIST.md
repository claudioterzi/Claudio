# Claudionas — Checklist Backup & Sicurezza
*Synology DS223j · Hyper Backup 4.1.2 · task "Google Drive 1" (repo Claudionas_1.hbk)*
*Redatto 2026-07-03 dai parametri estratti dai file di backup su Drive.*

> Nota onesta: questo checklist si basa sul config del backup (`_Syno_TaskConfig`),
> non sul NAS dal vivo — al dispositivo sulla tua LAN non ho accesso. Le voci le
> verifichi/applichi tu sul NAS. Dove dico "verifica" è perché dal config non si
> può essere certi al 100%.

---

## 🔴 P1 — Verifica che il backup salvi DAVVERO i tuoi dati
Il config mostra `backup_apps: [AntiVirus, CloudSync]` e **`backup_folders: []`**.
Tradotto: il task sembra salvare solo le configurazioni di quelle due app e
**nessuna cartella dati**. Se è così, documenti e foto NON sono nel backup.

**Da fare (la più importante di tutte):**
- Hyper Backup → task "Google Drive 1" → sezione **Data Backup / Cartelle**
- Controlla se ci sono cartelle condivise selezionate (home, photo, documenti…)
- Se è vuoto → modifica il task e **seleziona le cartelle che ti importano**

## 🔴 P2 — Attiva la cifratura
`enable_data_encrypt: false` → il backup su Google Drive è **in chiaro**: chi
accede a quel Drive legge i tuoi dati.
- La cifratura NON si può aggiungere a un task esistente → va creato un **task nuovo cifrato**
- Nuovo task → abilita **cifratura client-side** → **salva la password/chiave** in
  un posto sicuro (se la perdi, il backup è irrecuperabile)

## 🟡 P3 — Regola del 3-2-1
Adesso hai **1 sola copia off-site** (Google Drive). Ideale: 3 copie, 2 supporti, 1 fuori sede.
- Aggiungi una seconda destinazione: **disco USB** attaccato al NAS (Hyper Backup → Local folder & USB), o un secondo cloud
- Protegge da: perdita account Google, ransomware, errore umano

## 🟡 P4 — `enable_delete: true` + rotazione
Le cancellazioni sulla sorgente si propagano al backup, e la rotazione
(`rotate_earliest`, `[1,256]`) pota le versioni vecchie (257 tracciate ora).
- Verifica di tenere abbastanza storico versioni per i tuoi bisogni
- Rischio ransomware: se un malware cifra i file sorgente, la rotazione potrebbe
  eliminare le versioni buone → una copia periodica **offline/immutabile** lo mitiga

## 🟢 P5 — Verifica integrità
L'`incheck` gira alle 15:40 — bene, il controllo integrità è attivo.
- Conferma che **passa**: Hyper Backup → task → log del controllo

---

## Verifica veloce (spunta sul NAS)
- [ ] Il task salva le **cartelle dati** (non solo le app)?
- [ ] **Cifratura** attiva?
- [ ] **Seconda copia** (USB o altro cloud)?
- [ ] Storico versioni sufficiente?
- [ ] Ultimo **integrity check** passato?

---

## Se vuoi il secondo livello indipendente
Posso progettarti uno script `rclone` (backup cifrato verso una destinazione tua,
schedulato) come copia extra che non dipende da Hyper Backup. Dimmi e lo scrivo.
