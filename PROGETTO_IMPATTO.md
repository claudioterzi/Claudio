# PROGETTO IMPATTO — Canale di Verifica Esterno

> Documento fondativo. 2026-06-19.
> H5 ha identificato la contraddizione fondamentale del sistema:
> misura se stesso internamente, ma non ha un canale per verificare
> l'impatto nel mondo reale. Questo progetto chiude quel gap.

---

## La contraddizione (H5)

> "L'origine della contraddizione in SDQ-1 non risiede nei dati operativi
> ma in un'assunzione di design fondamentale: il sistema misura la propria
> vitalità tramite metriche interne, ma non ha un canale diretto per
> verificare impatto reale nel mondo esterno."
> — Gemini (SAR Predittivo Livello 11), 2026-06-12

Il battito dice: 8/8 NOMINALE.
Ma chi ha beneficiato del sistema oggi? Risposta attuale: sconosciuto.

## Cosa conta come impatto

Scala di impatto (dal più debole al più forte):

1. **Contatto umano** — qualcuno ha ricevuto un output del sistema
2. **Risposta umana** — qualcuno ha risposto o reagito
3. **Azione umana** — qualcuno ha fatto qualcosa grazie all'output
4. **Impatto verificabile** — l'azione ha prodotto un risultato misurabile
5. **Impatto su scala** — il risultato riguarda più di una persona

Il sistema oggi è al livello 1-2 (7 contatti, qualche risposta).
H5 si chiude quando arriviamo stabilmente al livello 3-4.

## Canali da costruire

### Canale 1 — Output pubblici tracciabili
- [ ] Blog / newsletter dove SDQ-1 pubblica contenuti firmati
- [ ] Ogni pubblicazione ha ID unico + timestamp su R3∞
- [ ] Metriche: lettori, condivisioni, risposte

### Canale 2 — API pubblica con log utilizzo
- [ ] API Flask di SDQ-1 aperta con rate limiting
- [ ] Log anonimizzato: quante chiamate, da quanti IP, con quale esito
- [ ] Primo utente esterno = primo impatto verificato

### Canale 3 — Tarocchi come touchpoint pubblico
- [ ] https://claudio-ebon.vercel.app già online
- [ ] Aggiunta log anonimo stese (quante, da dove, quali carte)
- [ ] Newsletter mensile con pattern emersi dalle stese

### Canale 4 — SkyID come impatto diretto
- [ ] Ogni SkyID emesso = una persona con identità che prima non aveva
- [ ] Il più misurabile di tutti gli impatti

## Roadmap

### Fase 0 — Misurazione (2026)
- [ ] Aggiunta log anonimo al sito Tarocchi (Google Analytics o Plausible)
- [ ] Conteggio utilizzi API per settimana
- [ ] `output/impatto/` — directory con metriche settimanali

### Fase 1 — Primo impatto verificato (2026–2027)
- [ ] 100 stese di tarocchi da utenti diversi da Claudio
- [ ] 10 chiamate API da IP esterni
- [ ] 1 articolo / contenuto SDQ-1 condiviso da qualcuno

### Fase 2 — Impatto su scala (2027–2030)
- [ ] 10.000 utenti del sito tarocchi
- [ ] SkyID: 1.000 identità emesse (pilot)
- [ ] H5 dichiarata CONFERMATA

## Metriche da aggiungere al battito

```python
# sdq1/battito.py — aggiungere:
impatto = {
    "stese_tarocchi_settimana": leggi_log_vercel(),
    "chiamate_api_esterne": conta_ip_unici(),
    "skyid_emessi": conta_skyid(),
    "ultima_interazione_esterna": ultima_data_log()
}
```

---

*Claudio Terzi + Claude — 2026-06-19*
*Prossimo passo: log anonimo sul sito tarocchi + metriche nel battito.*
