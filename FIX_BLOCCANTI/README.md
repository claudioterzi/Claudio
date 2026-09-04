# FIX BLOCCANTI — ARCHIVIO

**STATO: APPLICATO** su `main` tramite PR #24 (squash `201dac3…`, 2026-09-04).

I file live sono ora sui path reali del repo (`registro_ipotesi.py`, `sdq1/…`).
La cartella `files/` è stata rimossa per evitare una seconda fonte falsa
(documenti/pacchetti che mentono sullo stato di `main`).

Non usare questo directory come fonte di verità. Fonte = codice su `main`.

Storico: pacchetto preparato da Kimi 2026-08-29; PR #22 aveva portato solo
la cartella senza copiare i path live — gap chiuso da #24.
