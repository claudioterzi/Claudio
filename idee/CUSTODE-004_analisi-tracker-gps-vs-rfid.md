# CUSTODE-004 — Analisi: tracker Bluetooth/GPS (tipo AirTag) vs RFID

> Domanda di Claudio (2026-07-10): esistono anche sistemi GPS, tipo tag per
> chiavi — magari costano meno e danno anche la posizione. Analisi.

## Le tre famiglie a confronto

| | **Inlay RFID UHF** (scelta SOGLIA) | **Tracker Bluetooth** (AirTag, Tile, SmartTag) | **GPS vero** (LTE-M/NB-IoT) |
|---|---|---|---|
| Costo per oggetto | **0,05–0,25 $** | ~29–35 € (4-pack ~99 $) | 30–100 € |
| Canone | zero | 0 € (AirTag) / ~3 $/mese (Tile Smart Alerts) | **8–15 $/mese per tag** |
| Dimensioni | foglio di carta, **incollabile in una pagina** | disco 32 mm × 8 mm, 11 g — non nascondibile in un libro | scatoletta, ancora più grande |
| Batteria | **nessuna** (passivo) | CR2032, ~1 anno, da cambiare | ricaricabile, settimane–mesi |
| Posizione | no — solo passaggio al varco / presenza in casa | sì, tramite rete crowd-sourced (serve gente con iPhone/Android vicino) | sì, ovunque, in tempo reale |
| Su 150 oggetti | **~40 €**, zero manutenzione | **~4.500 €** + 150 batterie/anno | ~7.500 € + **~1.500 $/mese** di canoni |

## Il difetto strutturale dei tracker per l'antifurto

I tracker Bluetooth **sono progettati per NON funzionare come antifurto**.
Per proteggere le persone dallo stalking:

1. **Il telefono dell'ospite lo segnala da solo**: iPhone e Android
   mostrano l'avviso "un AirTag sconosciuto si sta muovendo con te" —
   chi porta via l'oggetto viene avvertito automaticamente e butta il tag.
2. **Il tag suona** quando è lontano dal suo proprietario da qualche ora.
3. Tile ha una "Anti-Theft Mode" che nasconde il tag dalle scansioni, ma
   Apple/Google non lo permettono, e attivarla apre problemi legali seri.

E c'è il punto **legale, ancora più netto**: seguire la *posizione* di un
oggetto uscito con l'ospite significa **tracciare la persona** — GDPR e
codice penale (atti persecutori/interferenze illecite) rendono la cosa
indifendibile per un host. Il varco RFID invece registra solo "l'oggetto X
ha attraversato la soglia alle 15:32": nessuna posizione, nessuna persona.
È esattamente il confine giusto.

## Dove i tracker hanno DAVVERO senso (ruolo complementare)

| Uso | Perché funziona |
|---|---|
| **Mazzi di chiavi della casa** (il "tag per chiavi" che dicevi) | Le chiavi sono dell'host, non seguono l'ospite: ritrovarle evita di cambiare serratura (100–200 €). Caso d'uso perfetto, dichiarabile, ~29 €. |
| Oggetti da esterno di alto valore (bici, e-bike, barbecue, kayak) | Troppo grandi per sparire in valigia, il furto avviene "sul posto": il ritrovamento post-furto è l'unico rimedio e lì la posizione serve davvero. |
| Valigetta manutenzione / attrezzi che girano tra le case | Asset dell'host in movimento legittimo: tracciarli è lecito e utile. |

## Verdetto

- **Non costano meno**: costano **100–600 volte di più per oggetto**, hanno
  batterie da gestire e non si nascondono in una pagina di libro.
- **La posizione che regalano è proprio ciò che non possiamo usare**
  legalmente contro un ospite — e l'anti-stalking li fa scoprire comunque.
- **Decisione**: SOGLIA resta su RFID UHF. Si aggiunge una voce opzionale
  al preventivo: **2–4 AirTag (~60–120 €)** per mazzi di chiavi e oggetti
  da esterno. Nessun GPS con canone.

### Aggiornamento preventivo SOGLIA (voce opzionale)

| Voce | Dettaglio | Costo |
|---|---|---:|
| 2–4 AirTag / SmartTag | chiavi di casa + oggetti da esterno | 60–120 € |
| Canoni | nessuno (rete Find My / SmartThings gratuita) | 0 €/anno |

## Fonti

- Confronto e prezzi 2026: https://www.tapo.com/us/news/1923/ e https://www.eufy.com/blogs/smart-tracker/tile-vs-airtag
- AirTag non è un antifurto (avvisi anti-stalking): https://discussions.apple.com/thread/255885700
- Tile Anti-Theft Mode e rischi: https://www.androidcentral.com/accessories/tiles-unencrypted-flaw-could-let-anyone-track-your-location
- Costi GPS LTE-M e batterie: https://logistimatics.com/blogs/guides/best-small-gps-trackers e https://www.invoxia.com/product/gps-tracker-pro-max
- Tracker senza canone (limiti): https://hubble.com/community/comparisons/best-gps-tracker-for-equipment-in-2026-without-monthly-fees-what-s-actually-possible/
