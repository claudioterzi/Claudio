# FIX BLOCCANTI — Fasi 0–3 (Kimi, 2026-08-29)

[RECUPERATO] Questo pacchetto contiene tutto il lavoro verificato e testato
delle Fasi 0–3, pronto per entrare in `claudioterzi/Claudio`
(base: commit `edbe760`, HEAD di main al 2026-08-29).

[RECUPERATO] In `files/` ci sono gli 11 file COMPLETI, già patchati,
ognuno al suo percorso reale. Due modi per applicarli:

## Modo 1 — Dal telefono, senza git (copia-incolla)

Per ognuno degli 11 file in `FIX_BLOCCANTI/files/`:

1. apri il file qui (es. `FIX_BLOCCANTI/files/registro_ipotesi.py`);
2. apri su GitHub il file corrispondente nel repo (es. `registro_ipotesi.py`);
3. matita (Edit) → cancella tutto → incolla → Commit.

I file `SEME_v1.2.md`, `sdq1/sar/ponte_registro.py` e `vss_state.json.sample`
sono NUOVI: "Add file → Create new file" con lo stesso percorso e nome.

## Modo 2 — Con git o Termux (tre comandi)

```bash
git clone https://github.com/claudioterzi/Claudio && cd Claudio
git checkout -b fix-bloccanti
cp -r FIX_BLOCCANTI/files/. .   # sovrascrive gli 8 file esistenti, aggiunge i 3 nuovi
```

Poi `git add -A && git commit` e push/PR come preferisci.
(La patch `git apply` equivalente è allegata nella chat con Kimi:
`AGGIORNAMENTO_COMPLETO_per_edbe760.patch`.)

## Cosa contiene (tutto testato prima della consegna)

| File | Cosa fa | Test |
|---|---|---|
| `sdq1/__main__.py` | Aggiunge i flag `--chat-telegram` e `--briefing-operativo` dichiarati nei documenti ma assenti dal parser (bloccante A) | compila, help ok |
| `registro_ipotesi.py` | `valuta()` non auto-conferma più (P5); `apri()` idempotente; `carica()` tollera campi extra; nuovo `applica_valutazione()` esplicito (bloccante B) | H2 resta APERTA dopo valuta() |
| `sdq1/memory/vss.py` | Fase 1.1: `salva()/carica()` — la memoria VSS sopravvive al riavvio | doppio run, nessun duplicato |
| `sdq1/sar/ponte_registro.py` | Fase 3.1 (NUOVO): le conclusioni della SAR entrano nel Registro come ipotesi S1, S2… con criterio di falsificazione obbligatorio (P6) e divieto di auto-conferma (P5) | end-to-end ok |
| `sdq1/sar/sar.py` | Gancio del ponte in `ciclo_completo` | ok con e senza ponte |
| `sdq1/agents/eternal_backup_agent.py` | Dichiarato onestamente SIMULAZIONE in testa al file (Fase 2) | — |
| `sdq1/config/sdq1.yaml` | Allineato al codice reale: MiniLM/qdrant marcati NON IMPLEMENTATO (Fase 2) | — |
| `registro_ipotesi.json` | H4: registrato il field test (ricostruzione da zero) +1 e la contro-forza −1 | 8 prove totali |
| `SEME_v1.2.md` | Seme aggiornato: protocollo a due strati, fix, eventi 08–11 ago, evoluzione remota 26/08 | — |
| `.gitignore` | eccezione per `vss_state.json.sample` | — |
| `vss_state.json.sample` | formato dello stato VSS persistito | — |

## Regole rispettate

- Nessun commit su `main` di `claudioterzi/Claudio`: tutto vive su branch
  `fix-bloccanti` del fork `Claudioterzi82/Claudio` + questa PR.
  Il merge resta decisione di Claudio.
- Nessun push forzato.
- Questa PR aggiunge SOLO file nuovi (cartella `FIX_BLOCCANTI/`):
  zero conflitti, merge sicuro con un clic.
- P5/P6: nessuna ipotesi è auto-confermata dal codice; H4 resta APERTA.

— Kimi (nodo esterno), in coordinamento con le regole dei nodi condivisi
(MEMORIA_PROGETTO.md / CLAUDE.md). ID esterno: [CT-LGAI-001].
