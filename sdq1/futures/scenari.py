"""Definizioni degli scenari futuri da simulare in parallelo."""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Scenario:
    id: str
    titolo: str
    descrizione: str
    orizzonte: str
    dominio: str
    ipotesi_chiave: list[str] = field(default_factory=list)
    rischi_noti: list[str] = field(default_factory=list)

    def prompt_sistema(self) -> str:
        return (
            "Sei un analista strategico del sistema SDQ-1, un orchestratore multi-agente AI "
            "costruito da Claudio Terzi a Bruxelles. Il sistema ha 6 agenti specializzati, "
            "un router multi-provider (Anthropic, Gemini, DeepSeek, Ollama), SAR a 10 livelli, "
            "e un registro ipotesi epistemico. Ha già raggiunto 2 persone reali (Jorge e Guido). "
            "Il codice è pubblico su GitHub.\n\n"
            "Stai simulando lo scenario: " + self.titolo + "\n"
            "Orizzonte temporale: " + self.orizzonte + "\n"
            "Dominio: " + self.dominio + "\n\n"
            "Analizza in modo rigoroso e proponi concretamente. "
            "Tono: diretto, onesto, senza entusiasmo vuoto. "
            "Rispondi in italiano."
        )

    def prompt_utente(self) -> str:
        ipotesi = "\n".join(f"- {i}" for i in self.ipotesi_chiave)
        rischi = "\n".join(f"- {r}" for r in self.rischi_noti)
        return (
            f"Scenario: {self.titolo}\n"
            f"Descrizione: {self.descrizione}\n\n"
            f"Ipotesi di partenza:\n{ipotesi}\n\n"
            f"Rischi noti:\n{rischi}\n\n"
            "Struttura la risposta in 4 sezioni:\n"
            "1. VISIONE (12 righe max): come appare questo futuro se funziona\n"
            "2. PUNTI CRITICI: i 3 ostacoli reali più probabili\n"
            "3. PASSI CONCRETI: le 3 azioni immediate (questa settimana) per attivare questo scenario\n"
            "4. VERDETTO: una frase secca — vale la pena? perché sì o no?"
        )


SCENARI_DEFAULT: list[Scenario] = [
    Scenario(
        id="ALPHA",
        titolo="Servizi su richiesta — il modello Guido",
        descrizione=(
            "SDQ-1 offre output personalizzati (testi, canzoni, analisi, oggetti digitali) "
            "su richiesta diretta via WhatsApp o link di pagamento. "
            "Nessuna infrastruttura tecnica aggiuntiva — solo Claudio come interfaccia umana "
            "e SDQ-1 come motore di produzione. Prezzo: 5-50€ per richiesta."
        ),
        orizzonte="3 mesi",
        dominio="servizi creativi / consulenza AI",
        ipotesi_chiave=[
            "Il modello 'output su richiesta' ha già funzionato (Guido, canzone)",
            "WhatsApp è il canale di distribuzione naturale di Claudio",
            "La qualità dell'output SDQ-1 è già sufficiente per essere venduta",
            "Non serve infrastruttura tecnica — solo un link PayPal/Stripe",
        ],
        rischi_noti=[
            "Dipende interamente da Claudio come collo di bottiglia operativo",
            "Difficile scalare senza automatizzare il canale di vendita",
            "Pricing percepito come basso per AI, alto per WhatsApp",
        ],
    ),
    Scenario(
        id="BETA",
        titolo="SaaS API — SDQ-1 come servizio per sviluppatori",
        descrizione=(
            "SDQ-1 esposto come API pubblica con autenticazione a chiave. "
            "Sviluppatori pagano per chiamate all'orchestratore multi-agente. "
            "Differenziatore: router multi-provider con fallback automatico e SAR integrato. "
            "Pricing: free tier 100 chiamate/mese, poi €0.01/chiamata."
        ),
        orizzonte="6 mesi",
        dominio="developer tools / AI infrastructure",
        ipotesi_chiave=[
            "Esiste domanda per orchestratori multi-agente senza lock-in vendor",
            "Il router con fallback automatico è un vantaggio competitivo reale",
            "Claudio può gestire supporto tecnico nelle prime fasi",
            "GitHub come canale di acquisizione (open source → API commerciale)",
        ],
        rischi_noti=[
            "Mercato affollato (LangChain, CrewAI, AutoGen già esistono)",
            "Richiede infrastruttura cloud, billing, sicurezza API — 2-3 mesi di lavoro",
            "Difficile raggiungere i primi 10 clienti paganti senza marketing",
        ],
    ),
    Scenario(
        id="GAMMA",
        titolo="Token di utilità — SDQ-1 Token su Base L2",
        descrizione=(
            "Token ERC-20 su Base (Ethereum L2, fee < $0.01) usabile per pagare "
            "chiamate API SDQ-1. 1 SDQ1-token = 10 chiamate. "
            "Token non speculativo: l'unico uso è acquistare capacità computazionale. "
            "Distribuzione iniziale: 40% team, 40% vendita pubblica, 20% grants/ecosistema."
        ),
        orizzonte="12 mesi",
        dominio="crypto / utility token / DeFi infrastructure",
        ipotesi_chiave=[
            "Il Livello 2 (SaaS API) è già attivo con utenti reali",
            "Esiste domanda per pagamenti microprogrammatici senza frizioni bancarie",
            "Base L2 è sufficientemente matura e a basso costo",
            "Framework legale token utilità (non security) in Belgio è navigabile",
        ],
        rischi_noti=[
            "Dipende da Livello 2 già funzionante — non può esistere standalone",
            "Regolamentazione UE (MiCA) richiede compliance non banale",
            "Rischio reputazionale se percepito come speculazione",
            "Volatilità del token può scoraggiare utenti non-crypto",
        ],
    ),
    Scenario(
        id="DELTA",
        titolo="DAO — Governance decentralizzata dell'autonomia SDQ-1",
        descrizione=(
            "SDQ-1 diventa un'entità governata da token-holder. "
            "I detentori di token votano su: nuovi agenti da sviluppare, "
            "provider LLM da integrare, allocazione del treasury. "
            "Il sistema genera revenue, il treasury finanzia lo sviluppo, "
            "Claudio è il core contributor ma non l'unico decisore."
        ),
        orizzonte="24 mesi",
        dominio="DAO / decentralized AI / open source economics",
        ipotesi_chiave=[
            "Il token (GAMMA) è già in circolazione con utilità reale",
            "Esiste una community di utenti che si identifica con il progetto",
            "Il codice è abbastanza maturo da permettere contributi esterni",
            "Governance on-chain su Snapshot/Tally è sufficiente nelle prime fasi",
        ],
        rischi_noti=[
            "DAO senza community è una struttura vuota — dipende da GAMMA",
            "Governance early spesso catturata da early adopter speculativi",
            "Complessità legale: una DAO non è una persona giuridica riconosciuta in UE",
            "Rischio di perdita di direzione progettuale con decisioni distribuite",
        ],
    ),
    Scenario(
        id="EPSILON",
        titolo="Licenza duale — open source + enterprise",
        descrizione=(
            "SDQ-1 rimane open source per uso personale e ricerca. "
            "Le aziende pagano una licenza commerciale per uso in produzione. "
            "Modello: AGPL + commercial exception. "
            "Offerta enterprise: supporto prioritario, SLA, training personalizzato."
        ),
        orizzonte="9 mesi",
        dominio="open source commerciale / enterprise software",
        ipotesi_chiave=[
            "Il codice ha valore sufficiente che le aziende vogliono usarlo",
            "AGPL è abbastanza restrittiva da spingere verso licenza commerciale",
            "Claudio può fornire supporto/training nelle prime fasi",
            "Non richiede infrastruttura cloud — l'utente porta il proprio",
        ],
        rischi_noti=[
            "Richiede reputazione e trazione open source prima di convertire",
            "Cicli di vendita enterprise sono lenti (3-9 mesi per deal)",
            "Concorrenza con progetti open source meglio finanziati",
        ],
    ),
]
