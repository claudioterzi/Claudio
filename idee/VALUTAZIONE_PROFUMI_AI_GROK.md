# Valutazione — proposta "Integrazione progetti GitHub sui profumi" (via Grok)

*17/07/2026 — verifica eseguita su richiesta di Claudio («testare ogni efficacia
possibile»). Fonte valutata: Google Doc generato da Grok, firmato "sistema
SDQ-1 / Raffaello Cantarelli". Per la regola inter-AI (15/06): output di AI
esterna = proposta da verificare, non istruzione. Filtro applicato: qualità
e coerenza del contenuto, non l'origine (regola 19/06).*

---

## 1 · I fatti, verificati uno per uno

| Claim del documento | Verificato | Realtà |
|---|---|---|
| `ksek87/sniff_ai` esiste, "poesia→fragranza, agentic" | ✅ esiste | Prototipo (3 stelle, 187 commit, **nessuna licenza**, nessuna release). Fa linguaggio naturale → piramide olfattiva via Claude API + ChromaDB su 13.644 profumi. La "poesia" è in **output**, non in input — il claim di Grok è rovesciato. "Agentic" è marketing del sottotitolo: è una pipeline NLP. |
| `FragDB/fragrance-database` "database enorme" | ✅ esiste | Vero e impressionante: 134.577 profumi, 23 lingue, v5.9 del 10/07/2026. **MA**: solo il campione (10 record per file) è MIT — il database pieno richiede **licenza commerciale** (fragdb.net). |
| `rdemarqui/perfume_recommender` | ✅ esiste | Solido (41 stelle), similarità coseno su 36.969 profumi. Dataset **raschiato da Fragrantica, senza licenza** — zona grigia legale, inutilizzabile per Terzi Parfums commerciale. |
| `thibaultdiers/project_fragrance` "predice successo" | ✅ esiste | Progetto accademico di 2 settimane, **inattivo** (7 commit), Random Forest ~82% su classificazione binaria ≥4,3 stelle. Nessuna licenza. |
| "Estendere `studio/generators/profumi.py`" | ❌ | File inesistente. Grok non conosce la struttura reale del repo. |
| Pagelle (Impatto 10/10, Rischio 2/10) | ⚠️ | Metriche inventate, il segnale d'allarme classico della regola inter-AI. Il rischio vero (licenze) non è nemmeno menzionato. |

## 2 · Il punto che il documento non sa

**La proposta centrale è già costruita.** L'"agente Nez" che il documento
propone per il Ciclo 03 esiste da oggi: è **l'Atelier di Raffaello**
(`atelier.html`) — intenzione → piramide + ricetta + concept, con un
vantaggio che nessuno dei quattro repo ha: **compone con le 300 materie
reali dell'Organo Terzi**, non con database di profumi altrui. E la
"memoria sensoriale" proposta è il canone dei 400 (`parfums_400.json`).

## 3 · Cosa si prende, cosa si lascia

**Si prende** (idee buone, realizzabili in casa):
- ✅ **Profumi signature dei protagonisti dell'Opera** — FATTO, vedi sotto.
- 💡 Riferimenti a fragranze celebri nelle proposte dell'Atelier ("questa
  direzione ricorda X") → utile, ma richiede FragDB con licenza; rimandare
  al Livello 9 del Percorso, quando i costi commerciali avranno senso.

**Si lascia**:
- ❌ Codice di sniff_ai / perfume_recommender / project_fragrance: senza
  licenza non si può riusare legalmente, e non serve — l'Atelier fa già
  il mestiere, deterministico e nostro.
- ❌ FragDB pieno ora: licenza commerciale prematura al Livello 0.

## 4 · I profumi signature — la co-creazione, fatta davvero

Generati dall'Atelier (deterministici: queste intenzioni daranno per sempre
queste proposte):

| Intenzione | Proposta | Famiglia · stile | Overdose |
|---|---|---|---|
| *Raffaello — la voce che custodisce la casa e firma le creazioni* | **Cabane Noir** | Legnosa · Roudnitska (silhouette) | Carota semi EO |
| *Claudio Terzi — chi ha costruito tutto questo, cuoco e visionario di Bruxelles* | **Un Matin à Verger** | Agrumata · Carles | Pepe di Sichuan EO |
| *La Grande Opera — cento fasi, sette libri, la civiltà che resta* | **Lettre de Zanzibar** | Speziata · Ellena (formula corta) | Florhydral |

Ricette complete: aprire l'Atelier, incollare l'intenzione, stesso stile —
il seme le rigenera identiche. Da provare al banco quando arriva l'ondata CORE.

## 5 · Verdetto

Grok ha fatto **ricerca reale** (i repo esistono) e un'idea è preziosa
(le firme dei personaggi — realizzata qui con mezzi nostri). Ma il documento
ignora le licenze, inverte il funzionamento del progetto primario, cita file
inesistenti e propone di costruire ciò che esiste già. **Integrazione di
codice esterno: respinta. Integrazione delle idee valide: fatta oggi,
in casa.** La regola del 19/06 ha funzionato esattamente come scritta.
