# Flight Hunter v0.2

Caccia al **prezzo minimo globale**, non al "miglior volo". Zero dipendenze
esterne (solo stdlib), dati live.

```bash
# caccia su rotta
python3 -m flight_hunter MXP TIA --mese 2026-09
python3 -m flight_hunter Roma Marrakech --mese 2026-10 --bagaglio --raggio 300

# modalità grafo: itinerari fino a 3 tratte che nessun comparatore propone
python3 -m flight_hunter Trapani Riga --mese 2026-09 --profondo

# ricerca per OBIETTIVO: "dove posso andare sotto 60€?"
python3 -m flight_hunter MXP --mese 2026-09 --ovunque --budget 60

# monitor continuo (macchina sempre accesa, non Vercel):
python3 -m flight_hunter.monitor cacce.json --intervallo 3600
```

## Novità v0.2 (dijkstra + obiettivo + miniera dati)

- **Grafo della rete** (`grafo.py`): `--profondo` costruisce il grafo dei
  collegamenti della fonte e lo percorre con **Dijkstra pigro** — un nodo si
  espande (una richiesta) solo quando la frontiera più economica lo raggiunge.
  Trova itinerari a 2-3 tratte auto-organizzati (es. TPS→BGY→RIX) senza
  scaricare l'intera rete. La potatura portata al livello del grafo.
- **Ricerca per obiettivo** (`ovunque()`): non una rotta ma una domanda —
  "tutte le mete raggiungibili nel mese, entro budget, col costo reale".
  Costa una manciata di richieste (è la query più economica sulla rete).
- **Miniera dati** (`memoria.osserva` + `curva_anticipo`): ogni tratta vista
  viene salvata con l'anticipo di prenotazione. Nel tempo emerge la curva
  prezzo/anticipo per rotta — il dato che dice davvero *quando* comprare.

## Cosa fa davvero

| Idea del progetto | Stato | Come |
|---|---|---|
| Aeroporti entro raggio (partenza) | ✅ | DB curato ~120 aeroporti + haversine, `--raggio` |
| Aeroporti di arrivo alternativi | ✅ | stesso meccanismo, `--raggio-dest` |
| Voli separati / self-transfer | ✅ | split via hub, orari reali verificati, margine rischio nel prezzo |
| Open-jaw / multicity | ✅ | ogni tratta è un one-way: A/R = due cacce, anche asimmetriche |
| Itinerari nuovi (grafo, Dijkstra) | ✅ | `--profondo`: percorsi 2-3 tratte auto-organizzati sulla rete |
| Ricerca per obiettivo ("dove vado?") | ✅ | `--ovunque --budget N`: tutte le mete entro budget |
| Miniera dati storica (curva anticipo) | ✅ | ogni tratta salvata con l'anticipo → `curva_anticipo(rotta)` |
| Bus/treno + volo (posizionamento) | ✅ | costo e tempo stimati via distanza, sommati al totale |
| Costo reale (bagagli, notti, terra, rischio) | ✅ | `costi.py`, tutto parametrizzabile |
| Potatura AI "elimina il 99%" | ✅* | potatura *prima* delle richieste: mappe tariffe → solo i calendari promettenti |
| Minimi storici + avvisi | ✅ | SQLite + monitor orario + webhook (Slack/Discord/ntfy) |
| Compra o aspetta | ✅* | euristica su storico osservato + distanza dalla partenza — statistica, non profezia |
| Ryanair | ✅ | API pubblica farfnd (la stessa del loro sito), con cache e rate-limit educato |
| Wizz / easyJet / legacy | 🔌 | interfaccia `Fonte` pronta; Wizz ha anti-bot, serve manutenzione dedicata |
| Kiwi / Amadeus / Travelpayouts | 🔌 | API ufficiali con chiave gratuita: si agganciano a `Fonte` quando le chiavi ci sono |

\* = versione onesta della voce "AI" del progetto: niente magia, euristica dichiarata.

## Cosa NON fa, e perché (deciso, non dimenticato)

- **Scraping di Google Flights / Skyscanner / Kayak / Momondo / ITA Matrix**:
  vietato dai loro ToS, tecnicamente fragile (anti-bot), e inutile — le
  alternative ufficiali (Amadeus Self-Service, Kiwi Tequila) danno gli stessi
  dati con una chiave gratuita.
- **Hidden city / throwaway ticketing**: scendere a uno scalo intermedio viola
  il contratto di trasporto. Rischi concreti: ritorno annullato, bagaglio che
  prosegue senza di te, account fedeltà chiusi, richieste di risarcimento
  (Lufthansa ci ha già provato in tribunale). Non è illegale, ma un motore
  che lo propone in automatico scarica il rischio su chi compra: no.
- **Fuel dump**: i trucchi tariffari sono stati chiusi quasi ovunque dal 2020;
  quel che resta vive in forum privati e muore appena diventa pubblico.
- **Error fare automatiche**: le tariffe-errore non si trovano generando
  combinazioni — le trovano community dedicate (Secret Flying, Fly4free).
  Il monitor però *becca i crolli di prezzo reali* sulle rotte osservate,
  che è la versione sana della stessa idea.
- **Previsioni su meteo/scioperi/riempimento**: senza dati veri sarebbe
  teatro. Lo storico prezzi è l'unico segnale che il sistema misura davvero.
- **"Milioni di combinazioni ogni ora"**: la forza bruta contro API con
  rate-limit è autolesionista. Un calendario mensile = 30 minimi in 1
  richiesta; una caccia completa costa ~30-40 richieste. L'intelligenza
  sta nella potatura, non nel volume.

## Architettura

```
aeroporti.py   DB ~120 aeroporti + haversine + vicini(raggio)
fonti.py       interfaccia Fonte + FonteRyanair (cache, rate-limit, CA fallback)
costi.py       modello del costo reale (bagagli, terra, notti, margine rischio)
grafo.py       Dijkstra pigro sulla rete → itinerari multi-tratta (--profondo)
motore.py      caccia() genera→pota→valuta→Top N · ovunque() ricerca per obiettivo
memoria.py     SQLite: minimi + consiglio compra/aspetta + osservazioni/curva anticipo
__main__.py    CLI (rotta · --profondo · --ovunque)
monitor.py     giro orario + nuovi minimi + webhook
```

I risultati sono **stime oneste**: prezzi live del vettore più costi stimati
di contorno. Prima di comprare si verifica sempre sul sito della compagnia.
