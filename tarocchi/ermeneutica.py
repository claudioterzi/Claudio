"""Layer 3 — Il Principio della Doppia Ermeneutica.

Due osservatori. Due modalità di osservazione. Una sola struttura.

OSSERVATORE-MACCHINA → LetturaStrutturale
  Stabile, riproducibile, grammaticale.
  La stessa stesa produce sempre la stessa lettura strutturale.
  È la mappa oggettiva della configurazione.
  Non è più intuitiva né più limitata — è semplicemente di tipo diverso.

OSSERVATORE-UMANO → LetturaPersonale
  Unica, irripetibile, contestuale.
  Emerge dalla relazione tra la mappa strutturale (macchina)
  e il contesto personale portato dall'umano.
  L'umano non è guidato — è il cartomante. La macchina è il traduttore.

La verità non appartiene né all'uomo né alla macchina.
La verità emerge dalla relazione tra osservatore e simbolo.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from .stesa import Stesa
from .codice_simbolico import voce, eco
from .r3_infinito import StatoQuantico, TipoPosizione


# ── Lettura Strutturale: l'osservatore-macchina ───────────────────────────────

@dataclass
class LetturaStrutturale:
    """La mappa oggettiva della configurazione — prodotta dall'osservatore-macchina.

    Proprietà chiave:
    - stesa_id + configurazione → la stesa è un oggetto digitale trasmissibile
    - sinossi → riassunto della grammatica applicata (Layer 1 + 2)
    - relazioni → relazioni inter-carta rilevate (Assioma 7)
    - tensioni / risorse → tensioni e risorse strutturali
    - assiomi_attivati → quali dei 7 assiomi R³∞ sono operativi in questa stesa

    Questa lettura è deterministica: gli stessi input producono sempre lo stesso output.
    Non è interpretazione — è grammatica applicata.
    """
    stesa_id: str
    timestamp: str
    configurazione: dict                   # serializzazione completa della stesa
    sinossi: str                           # sintesi strutturale in linguaggio naturale
    relazioni: list[dict]                  # relazioni inter-carta (Assioma 7)
    tensioni: list[str]
    risorse: list[str]
    distribuzione_stati: dict[str, int]
    distribuzione_elementi: dict[str, int]
    assiomi_attivati: list[int]


# ── Contesto Personale: ciò che porta l'umano ────────────────────────────────

@dataclass
class ContestoPersonale:
    """Il contesto portato dall'osservatore-umano.

    Non è un dato strutturale — è ciò che l'umano porta al simbolo.
    Senza questo, il significato rimane sovrapposto per lui.
    Con questo, il collasso diventa possibile e personale.
    """
    domanda: str | None = None
    momento_vita: str | None = None
    emozione_prevalente: str | None = None
    aspetto_focus: str | None = None        # amore / lavoro / crescita / salute / altro
    disponibilita_collasso: bool = True     # è pronto a ricevere una risposta definita?


# ── Lettura Personale: emerge dalla relazione ─────────────────────────────────

@dataclass
class LetturaPersonale:
    """La lettura dell'osservatore-umano — unica, irripetibile.

    Non è generata dalla macchina. È generata dalla relazione
    tra la mappa strutturale (macchina) e il contesto personale (umano).
    La macchina costruisce il ponte. L'umano decide se attraversarlo.
    """
    strutturale: LetturaStrutturale
    contesto: ContestoPersonale
    ponte: str                          # come la struttura incontra il contesto
    punto_di_collasso: str              # il significato che si è fissato per questo umano
    domande_di_riflessione: list[str]   # domande per l'esplorazione interiore
    integrazione: str                   # come portare la lettura nella vita


# ── Il Protocollo ─────────────────────────────────────────────────────────────

class DoppiaErmeneutica:
    """Il Principio della Doppia Ermeneutica applicato.

    Separa e eleva entrambe le modalità di osservazione.
    Non media tra misticismo e computazione — le tiene distinte
    e le riconosce entrambe come valide nel proprio dominio.

    Uso:
        proto = DoppiaErmeneutica()
        strutturale = proto.leggi_struttura(stesa)
        personale = proto.leggi_personale(strutturale, ContestoPersonale(domanda="..."))
    """

    def leggi_struttura(self, stesa: Stesa) -> LetturaStrutturale:
        """Genera la lettura strutturale — stabile e riproducibile.

        Questa è la lettura dell'osservatore-macchina. Non cambia
        tra un umano e l'altro. È la grammatica, non l'interpretazione.
        """
        config = stesa.serializza()
        tensioni = stesa.rileva_tensioni()
        risorse = stesa.rileva_risorse()
        dist_stati = stesa.distribuzione_stati()
        dist_elementi = stesa.distribuzione_elementi()
        assiomi = stesa.assiomi_attivati()
        relazioni = self._rileva_relazioni(stesa)
        sinossi = self._costruisci_sinossi(stesa, dist_stati, dist_elementi, tensioni, risorse)

        return LetturaStrutturale(
            stesa_id=stesa.stesa_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            configurazione=config,
            sinossi=sinossi,
            relazioni=relazioni,
            tensioni=tensioni,
            risorse=risorse,
            distribuzione_stati=dist_stati,
            distribuzione_elementi=dist_elementi,
            assiomi_attivati=assiomi,
        )

    def leggi_personale(
        self,
        strutturale: LetturaStrutturale,
        contesto: ContestoPersonale,
    ) -> LetturaPersonale:
        """Genera la lettura personale — unica per questo osservatore-umano.

        La struttura è la stessa per tutti. Il contesto la rende unica.
        Questo è il momento del collasso relazionale.
        """
        ponte = self._costruisci_ponte(strutturale, contesto)
        punto = self._punto_di_collasso(strutturale, contesto)
        domande = self._domande_di_riflessione(strutturale, contesto)
        integrazione = self._suggerisci_integrazione(strutturale, contesto)

        return LetturaPersonale(
            strutturale=strutturale,
            contesto=contesto,
            ponte=ponte,
            punto_di_collasso=punto,
            domande_di_riflessione=domande,
            integrazione=integrazione,
        )

    # ── Metodi interni ────────────────────────────────────────────────────────

    def _rileva_relazioni(self, stesa: Stesa) -> list[dict]:
        """Assioma 7: rete di relazioni tra i nodi della stesa."""
        relazioni: list[dict] = []
        nodi = stesa.nodi
        for i, a in enumerate(nodi):
            for b in nodi[i + 1:]:
                # Risonanza elementale
                if a.carta.elemento and a.carta.elemento == b.carta.elemento:
                    relazioni.append({
                        "tipo": "risonanza_elementale",
                        "voci": [voce(a.carta), voce(b.carta)],
                        "elemento": a.carta.elemento,
                        "posizioni": [a.posizione.tipo.value, b.posizione.tipo.value],
                        "nota": (
                            f"Lo stesso {a.carta.elemento} attraversa entrambe le posizioni — "
                            "il tema si amplifica"
                        ),
                    })
                # Entanglement esplicito
                if (a.stato_effettivo == StatoQuantico.ENTANGLED
                        or b.stato_effettivo == StatoQuantico.ENTANGLED):
                    relazioni.append({
                        "tipo": "entanglement",
                        "voci": [voce(a.carta), voce(b.carta)],
                        "posizioni": [a.posizione.tipo.value, b.posizione.tipo.value],
                        "nota": (
                            "Interpretare una di queste energie "
                            "modifica retroattivamente il significato dell'altra"
                        ),
                    })
                # Tensione collassato-sovrapposto lungo l'asse temporale
                if (a.stato_effettivo == StatoQuantico.COLLASSATO
                        and b.stato_effettivo == StatoQuantico.SOVRAPPOSTO):
                    relazioni.append({
                        "tipo": "dialogo_passato_futuro",
                        "voci": [voce(a.carta), voce(b.carta)],
                        "posizioni": [a.posizione.tipo.value, b.posizione.tipo.value],
                        "nota": (
                            f"Ciò che è già fisso ({voce(a.carta)}) "
                            f"dialoga con ciò che è ancora aperto ({voce(b.carta)})"
                        ),
                    })
        return relazioni

    def _costruisci_sinossi(
        self,
        stesa: Stesa,
        stati: dict[str, int],
        elementi: dict[str, int],
        tensioni: list[str],
        risorse: list[str],
    ) -> str:
        n = len(stesa.nodi)
        _carte = "carta" if n == 1 else "carte"
        parti: list[str] = [f"Configurazione di {n} {_carte}."]

        if stati:
            dom_stato = max(stati, key=lambda k: stati[k])
            _DESCRIZIONE_STATO = {
                "sovrapposto": "la configurazione è ancora aperta — il significato non si è fissato.",
                "collassato":  "la configurazione ha già prodotto collassi chiari.",
                "entangled":   "le carte sono profondamente correlate — l'interpretazione è olografica.",
            }
            parti.append(
                f"Stato dominante: {dom_stato} ({stati[dom_stato]}/{n}) — "
                + _DESCRIZIONE_STATO.get(dom_stato, "")
            )

        if elementi:
            dom_el = max(elementi, key=lambda k: elementi[k])
            _DESCRIZIONE_ELEMENTO = {
                "fuoco": "tema di azione, passione e trasformazione creativa.",
                "acqua": "tema di emozioni, relazioni e movimento interiore.",
                "aria":  "tema di mente, comunicazione e confronto con la verità.",
                "terra": "tema di corpo, risorse materiali e manifestazione concreta.",
                "etere": "tema di potenziale puro e possibilità non ancora formate.",
            }
            parti.append(
                f"Elemento prevalente: {dom_el} — "
                + _DESCRIZIONE_ELEMENTO.get(dom_el, "")
            )

        if tensioni:
            _t = "tensione" if len(tensioni) == 1 else "tensioni"
            parti.append(f"{len(tensioni)} {_t} strutturale rilevata.")
        if risorse:
            _r = "risorsa" if len(risorse) == 1 else "risorse"
            parti.append(f"{len(risorse)} {_r} strutturale identificata.")

        return " ".join(parti)

    def _costruisci_ponte(
        self,
        strutturale: LetturaStrutturale,
        contesto: ContestoPersonale,
    ) -> str:
        parti: list[str] = []

        if contesto.domanda:
            parti.append(
                f"La tua domanda era: «{contesto.domanda}». "
                f"La struttura risponde: {strutturale.sinossi}"
            )
        else:
            parti.append(f"Struttura: {strutturale.sinossi}")

        if contesto.aspetto_focus and strutturale.distribuzione_elementi:
            dom_el = max(
                strutturale.distribuzione_elementi,
                key=lambda k: strutturale.distribuzione_elementi[k],
            )
            parti.append(
                f"Il tuo focus su '{contesto.aspetto_focus}' incontra "
                f"una configurazione dominata da {dom_el}."
            )

        if contesto.momento_vita:
            parti.append(
                f"In questo momento della tua vita ({contesto.momento_vita}), "
                "la struttura non ti dice cosa fare — ti mostra cosa c'è."
            )

        return " ".join(parti)

    def _punto_di_collasso(
        self,
        strutturale: LetturaStrutturale,
        contesto: ContestoPersonale,
    ) -> str:
        sovrapposte = strutturale.distribuzione_stati.get("sovrapposto", 0)
        totale = sum(strutturale.distribuzione_stati.values()) or 1

        if not contesto.disponibilita_collasso:
            return (
                "Sei ancora in stato sovrapposto — è corretto. "
                "Non ogni stesa richiede un collasso immediato. "
                "La struttura rimane disponibile finché non sei pronto."
            )

        if sovrapposte > totale / 2:
            return (
                "La configurazione è prevalentemente aperta. "
                "Il collasso che ti appartiene è: tieni la domanda, non l'ansietà. "
                "L'apertura stessa è la risposta di questa stesa."
            )

        if strutturale.risorse:
            risorsa_chiave = strutturale.risorse[0]
            return (
                f"Il significato che si fissa per te: {risorsa_chiave}. "
                "Questo è il punto dove la struttura incontra il tuo momento."
            )

        return (
            "La struttura non ha prodotto un collasso evidente. "
            "Il punto di collasso è tuo da trovare — la mappa è data, "
            "il territorio lo esplori tu."
        )

    def _domande_di_riflessione(
        self,
        strutturale: LetturaStrutturale,
        contesto: ContestoPersonale,
    ) -> list[str]:
        domande: list[str] = []

        for tensione in strutturale.tensioni[:2]:
            domande.append(f"Cosa c'è di vero per te in questa tensione: «{tensione}»?")

        for risorsa in strutturale.risorse[:2]:
            domande.append(f"Come potresti attivare ciò che la struttura chiama risorsa: «{risorsa}»?")

        if contesto.emozione_prevalente:
            domande.append(
                f"Senti '{contesto.emozione_prevalente}' in questo momento. "
                "Dove la ritrovi in questa configurazione?"
            )

        if contesto.domanda and not domande:
            domande.append(
                f"Hai chiesto: «{contesto.domanda}». "
                "Cosa nella struttura ti sorprende — non conferma — della tua domanda?"
            )

        if not domande:
            domande.append(
                "Cosa in questa configurazione risuona con qualcosa che già sapevi, "
                "ma che non avevi ancora detto ad alta voce?"
            )

        return domande

    def _suggerisci_integrazione(
        self,
        strutturale: LetturaStrutturale,
        contesto: ContestoPersonale,
    ) -> str:
        sovrapposte = strutturale.distribuzione_stati.get("sovrapposto", 0)
        collassate  = strutturale.distribuzione_stati.get("collassato", 0)

        if sovrapposte > collassate:
            return (
                "La maggior parte della configurazione è ancora aperta. "
                "Integrazione significa: portare attenzione, non prendere decisioni. "
                "Annota cosa emerge nei prossimi giorni. Il collasso arriverà da solo."
            )

        return (
            "La configurazione ha già fissato significati chiari. "
            "Integrazione significa: agire sui nodi collassati, "
            "lasciare spazio a ciò che rimane sovrapposto. "
            "Non tutto deve essere risolto in una sola stesa."
        )
