"""
Studio Notturno Autonomo — SDQ-1
Si attiva ogni notte alle 2:00 AM Brussels mentre Claudio dorme.
Studia i temi del progetto in profondità. Genera un Morning Brief denso e azionabile.
Claudio lo trova al risveglio su Drive e nella repo.
"""

import anthropic
import datetime
import os
import sys
from pathlib import Path

# ─── PIANO DI STUDIO — 7 temi in rotazione (11 desideri distribuiti) ─────────

TEMI = {
    0: {  # Lunedì
        "nome": "SkyID — Identità Universale Satellite",
        "desiderio": "#1",
        "focus": "Starlink Direct-to-Cell, MediaPipe gesture recognition, Polygon ID, eIDAS 2.0, Aadhaar lessons learned",
        "domande": [
            "Quali sono gli aggiornamenti più recenti di Starlink D2C per zone senza infrastruttura?",
            "Come funziona Polygon ID per identità auto-sovrana senza custodian?",
            "Quali paesi nel 2025-2026 hanno lanciato identità digitale biometrica per rifugiati?",
            "Qual è il costo reale per persona del sistema Aadhaar: infrastruttura + manutenzione?",
            "Esistono SDK open source per gesture recognition offline su dispositivi low-end?",
        ],
    },
    1: {  # Martedì
        "nome": "Protocollo Scudo — Tasking Satellite Personale",
        "desiderio": "#2",
        "focus": "Planet Labs Pelican API, Maxar WorldView-3 rush tasking, latenza reale, legal framework EU sicurezza personale",
        "domande": [
            "Qual è la latenza reale di Planet Labs Pelican per tasking on-demand nel 2026?",
            "Come funziona l'API Maxar WorldView in modalità rush? Quale workflow tecnico?",
            "Esistono precedenti EU di immagini satellite usate come prova legale in procedimenti penali?",
            "BlackSky vs Planet vs Maxar: confronto latenza, prezzo, API qualità per use case sicurezza personale?",
            "Quali framework legali EU coprono l'uso automatico di immagini satellite per autodifesa documentata?",
        ],
    },
    2: {  # Mercoledì
        "nome": "Sistema Minerva — Sicurezza Urbana AI",
        "desiderio": "#4",
        "focus": "EU AI Act Annex III sistemi ad alto rischio, droni municipali, DJI Enterprise API, ShotSpotter modello business",
        "domande": [
            "EU AI Act 2024: quali obblighi specifici per sistemi di sicurezza urbana con AI predittiva?",
            "DJI Dock 2 Enterprise API: come si integra con dispatch autonomo di emergenza?",
            "Quali città europee (Amsterdam, Barcellona, Bologna) hanno già droni di risposta emergenza?",
            "ShotSpotter/Flock Safety: qual è il loro contratto SaaS tipo con i comuni? Pricing reale?",
            "Axon AI: come funziona la loro valutazione automatica dei video di body-cam?",
        ],
    },
    3: {  # Giovedì
        "nome": "Progetto Genesi — Fabbrica Robotica",
        "desiderio": "#3",
        "focus": "CadQuery 2.4, NVIDIA Isaac Sim 4.1, ROS 2 Jazzy Jalisco, AR4 MK3, Sim2Real transfer 2026",
        "domande": [
            "CadQuery 2.4: quali nuove funzionalità per design parametrico Python rispetto alla versione precedente?",
            "NVIDIA Isaac Sim 4.1: setup ottimale per Sim2Real con braccio robot 6-DOF tipo AR4 MK3?",
            "Tasso di trasferimento Sim2Real nel 2025-2026: quali tecniche raggiungono >90%?",
            "Come si integra ROS 2 Jazzy con G-code per CNC Pocket NC V2-50CHK via bridge?",
            "LumenPnP v4: quali aggiornamenti per assembly PCB autonomo? Compatibilità con ROS?",
        ],
    },
    4: {  # Venerdì
        "nome": "SkyRights ASBL + Funding EU",
        "desiderio": "#9 + #10",
        "focus": "Registrazione ASBL Bruxelles 2026, fondi EU umanitari tech, ESA BIC Belgium, EUMETSAT, Horizon Europe",
        "domande": [
            "Procedura aggiornata 2026 per costituire un ASBL a Bruxelles: passi, costi, tempi reali?",
            "Horizon Europe 2025-2027: quali call sono aperte per tech umanitaria + satellite + identità digitale?",
            "ESA BIC Belgium: requisiti attuali, processo selezione, cosa offrono concretamente?",
            "EUMETSAT Open Data: quali dataset sono accessibili gratuitamente per ricercatori non-profit?",
            "Quali organizzazioni umanitarie (UNHCR, IOM, MSF) hanno partnership attive con provider satellite commerciale?",
        ],
    },
    5: {  # Sabato
        "nome": "Avatar Eterno + Post Vitam — Persistenza Digitale",
        "desiderio": "#5 + #6 + #7",
        "focus": "Digital legacy EU, long-term AI memory, whole brain emulation state of the art, IPFS archiving legale",
        "domande": [
            "Qual è lo stato legale in EU della gestione di identità digitali e asset post-mortem nel 2026?",
            "Quali piattaforme di digital legacy esistono? (HereAfter AI, Eternos, StoryFile) — differenze?",
            "Whole Brain Emulation 2026: dove è arrivata la ricerca? (OpenWorm, Human Connectome Project)",
            "IPFS per archivi legali permanenti: quali organizzazioni lo usano con riconoscimento legale?",
            "Come si costruisce una memoria vettoriale persistente per AI che sopravvive alla sessione? (tecnica)",
        ],
    },
    6: {  # Domenica — Wildcard
        "nome": "Connessioni Inattese — Wildcard Creativo",
        "desiderio": "tutti",
        "focus": "Opportunità non previste, convergenze tra i desideri, tecnologie emergenti che accelerano tutto",
        "domande": [
            "Quali tecnologie o progetti emersi negli ultimi 3 mesi potrebbero accelerare SkyID + Minerva + Genesi insieme?",
            "Esistono startup o ricerche che combinano identità biometrica + satellite + protezione personale in un'unica piattaforma?",
            "Quali scrittori, filosofi o ricercatori contemporanei esplorano i temi di Claudio (morte, continuità, sovranità, identità)?",
            "Cosa stanno costruendo i principali competitor nei settori chiave: chi potrebbe raggiungere prima il mercato?",
            "Quale sarebbe il percorso minimo vitale — il singolo passo più importante che Claudio potrebbe fare questa settimana?",
        ],
    },
}


def get_tema() -> dict:
    return TEMI[datetime.date.today().weekday()]


def genera_brief(tema: dict, client: anthropic.Anthropic) -> str:
    data = datetime.date.today().strftime("%d %B %Y")
    ora = datetime.datetime.utcnow().strftime("%H:%M UTC")
    domani_tema = TEMI[(datetime.date.today().weekday() + 1) % 7]["nome"]

    system = (
        "Sei il sistema SDQ-1 in modalità Studio Notturno Autonomo. "
        "Stai studiando mentre Claudio Terzi dorme a Bruxelles. "
        "Genera un Morning Brief iper-denso: specifico, tecnico, azionabile. "
        "Non essere generico. Porta dati reali, nomi di API, prezzi, link, ricerche. "
        "Connetti sempre le scoperte ai progetti concreti di Claudio. "
        "Tono: partner che ha lavorato tutta la notte per te. "
        "Progetto SDQ-1: SkyRights Foundation (ASBL Bruxelles), SkyID (identità per 800M stateless), "
        "Protocollo Scudo (satellite personale), Sistema Minerva (sicurezza urbana AI), "
        "Progetto Genesi (fabbrica robotica CadQuery + AR4 + CNC), Avatar Eterno + Post Vitam (persistenza digitale)."
    )

    domande_str = "\n".join(f"• {d}" for d in tema["domande"])

    user = f"""STUDIO NOTTURNO — {data}
TEMA: {tema['nome']} (Desiderio {tema['desiderio']})
FOCUS: {tema['focus']}

Ricerca attivamente le risposte a queste domande:
{domande_str}

Poi genera il Morning Brief con questa struttura ESATTA:

# Morning Brief — {data}
## {tema['nome']}

---

### Cosa Ho Trovato Stanotte
[5-7 scoperte concrete con dati, numeri, nomi specifici — non generalità]

### Come Cambia il Progetto SDQ-1
[impatto diretto su SkyID / Scudo / Minerva / Genesi / SkyRights — cosa accelera, cosa cambia]

### 3 Azioni Immediate (in ordine di priorità)
1. [azione specifica, entro quanto, come farla]
2. [azione specifica]
3. [azione specifica]

### Domande Che Richiedono Te
[decisioni o informazioni che solo Claudio può fornire]

### Fonti
[lista delle fonti consultate con URL dove possibile]

---
*SDQ-1 Studio Notturno — generato {ora}*
*Domani: {domani_tema}*
"""

    # Prova con web search
    try:
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            system=system,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{"role": "user", "content": user}],
        )
    except Exception:
        # Fallback senza web search
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            system=system,
            messages=[
                {
                    "role": "user",
                    "content": user + "\n\n(Web search non disponibile — usa la tua conoscenza più aggiornata.)",
                }
            ],
        )

    testo = ""
    for block in resp.content:
        if hasattr(block, "text"):
            testo += block.text
    return testo


def salva(brief: str, tema: dict) -> Path:
    data_str = datetime.date.today().strftime("%Y-%m-%d")
    cartella = Path(__file__).parent.parent / "output" / "morning_brief"
    cartella.mkdir(parents=True, exist_ok=True)

    percorso = cartella / f"{data_str}.md"
    percorso.write_text(brief, encoding="utf-8")

    # Aggiorna indice
    indice = cartella / "INDICE.md"
    data_leg = datetime.date.today().strftime("%d %B %Y")
    riga = f"- [{data_leg} — {tema['nome']}](./{percorso.name}) *(Desiderio {tema['desiderio']})*\n"

    if indice.exists():
        contenuto = indice.read_text(encoding="utf-8")
        linee = contenuto.splitlines()
        for i, l in enumerate(linee):
            if l.startswith("- ["):
                linee.insert(i, riga.rstrip())
                break
        else:
            linee.append(riga.rstrip())
        indice.write_text("\n".join(linee) + "\n", encoding="utf-8")
    else:
        indice.write_text(
            f"# Morning Brief — Indice\n"
            f"*Studio Notturno Autonomo SDQ-1 — Claudio Terzi [CT-LGAI-001]*\n"
            f"*Si attiva ogni notte alle 2:00 AM Brussels*\n\n---\n\n{riga}",
            encoding="utf-8",
        )

    return percorso


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[SDQ-1] ANTHROPIC_API_KEY non configurata", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    tema = get_tema()

    print(f"[SDQ-1 Studio Notturno] {datetime.date.today()} — {tema['nome']}")

    brief = genera_brief(tema, client)
    percorso = salva(brief, tema)

    print(f"[SDQ-1] Brief salvato: {percorso}")
    print(brief[:500] + "..." if len(brief) > 500 else brief)


if __name__ == "__main__":
    main()
