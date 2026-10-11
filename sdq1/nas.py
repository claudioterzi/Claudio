"""
NAS-008 — Agente Esperto Synology DS223

Conosce tutto sulla Synology DiskStation DS223:
- Hardware e specifiche tecniche
- Installazione dischi e primo avvio
- Configurazione DSM via find.synology.com
- RAID e gestione storage (SHR-1 raccomandato)
- Pacchetti chiave: Photos, Drive, Hyper Backup, Surveillance
- Accesso remoto: QuickConnect, DDNS, VPN
- Best practice e troubleshooting

Uso:
    python -m sdq1.nas                         # menu interattivo
    python -m sdq1.nas "come installo i dischi"  # risposta diretta
    python -m sdq1.nas --guida                 # guida installazione completa
    python -m sdq1.nas --schema                # schema hardware rapido
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Callable

LLMFn = Callable[[str, str], str]

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "nas"

# ─── BASE DI CONOSCENZA DS223 ─────────────────────────────────────────────────

CONOSCENZA_DS223 = """
## Synology DiskStation DS223 — Base di conoscenza completa

### HARDWARE
- CPU: Realtek RTD1619B, 4 core, 1.7 GHz, 64-bit, crittografia hardware integrata
- RAM: 2 GB DDR4 (saldata, non espandibile)
- Bay: 2 (hot-swappable — si possono inserire/rimuovere a caldo)
- Drive supportati: HDD 3.5" SATA, SSD 2.5" SATA (NAS-grade raccomandati: WD Red, Seagate IronWolf)
- Rete: 1x RJ-45 1GbE (massimo ~125 MB/s)
- USB: 3x USB 3.2 Gen 1 (per dischi esterni, stampanti, UPS)
- LED frontali: STATUS (blu=OK), LAN, DISK 1, DISK 2 (tutti verdi = tutto OK)
- Alimentazione: adattatore AC esterno
- Dimensioni: compatta, desktop

### INSTALLAZIONE DISCHI (PRIMA COSA DA FARE)
1. Spegnere il NAS (tasto power sul retro)
2. Aprire le porte dei bay frontali — si aprono con un click
3. Inserire il disco nel vano: fare scorrere verso il basso fino a click
4. Ripetere per il secondo bay (opzionale ma fortemente raccomandato per RAID 1)
5. Richiudere le porte dei bay
6. NOTA: il DS223 è già tuo e acceso — i LED verdi confermano i dischi già inseriti e riconosciuti

### PRIMO AVVIO E CONFIGURAZIONE DSM
**Metodo 1 — find.synology.com (raccomandato):**
1. Assicurati che il NAS sia connesso al router via cavo Ethernet
2. Apri un browser sul PC/Mac nella stessa rete
3. Vai su: https://find.synology.com
4. Il sito rileva automaticamente il DS223 sulla rete locale
5. Clicca sul dispositivo → si apre la procedura guidata
6. Installa DSM (scarica automaticamente l'ultima versione, ~5 minuti)
7. Crea l'account amministratore (username + password forte)
8. Configura il volume di storage (vedi sezione RAID)
9. Attendi l'inizializzazione (può richiedere ore per dischi grandi)

**Metodo 2 — IP diretto:**
1. Trova l'IP del NAS nel pannello DHCP del router (cerca "synology" o il MAC address)
2. Vai su http://[IP-NAS]:5000 nel browser
3. Segui la procedura guidata DSM

**Metodo 3 — Synology Assistant (software PC/Mac):**
1. Scarica Synology Assistant da synology.com/en/support/download
2. Lancia il software — rileva il NAS automaticamente
3. Clicca "Connetti" per avviare la configurazione

### STORAGE E RAID (SCELTA CRITICA)
**SHR-1 (Synology Hybrid RAID) — RACCOMANDATO:**
- Protezione da guasto di 1 disco
- Funziona anche con dischi di dimensioni diverse
- Capacità utilizzabile: circa metà del totale (es. 2x4TB = ~4TB usabili)
- Ideale per: uso domestico, espansione futura con disco diverso
- Come impostare: Storage Manager → Crea Storage Pool → Seleziona SHR

**RAID 1 (Mirroring):**
- Dati duplicati su entrambi i dischi
- Protezione da guasto di 1 disco
- Richiede dischi della stessa dimensione per efficienza massima
- Capacità utilizzabile: 50% del totale

**RAID 0 (Striping):**
- NESSUNA protezione — se un disco si rompe, tutto è perso
- Doppia velocità, 100% capacità
- Solo per dati temporanei e non critici

**Basic (JBOD):**
- Ogni disco è indipendente
- Nessuna protezione
- Utile solo per test

### PACCHETTI CHIAVE (Package Center in DSM)
**File e sincronizzazione:**
- Synology Drive: cloud personale per sincronizzare file tra PC, Mac, mobile
- File Station: gestore file web-based (come Finder/Explorer nel browser)

**Foto e multimedia:**
- Synology Photos: organizzazione foto con AI, condivisione album, app mobile
- Surveillance Station: videosorveglianza (2 licenze camera incluse, 8300+ camere supportate)

**Backup:**
- Hyper Backup: backup schedulato su cloud (Google Drive, Backblaze, ecc.) o disco esterno USB
- Snapshot Replication: protezione incrementale con rollback (solo su volumi Btrfs)

**Collaborazione:**
- Synology Office: documenti, fogli di calcolo, presentazioni (collaborazione real-time)

**Nota:** Active Backup for Business NON è supportato su DS223 (richiede modelli superiori)

### ACCESSO REMOTO
**QuickConnect (più semplice):**
1. DSM → Pannello di controllo → Accesso esterno → QuickConnect
2. Accedi con account Synology (crea gratis su account.synology.com)
3. Scegli un QuickConnect ID (es. "claudioterzi")
4. Accedi ovunque via: quickconnect.to/claudioterzi
- Pro: nessuna config router, funziona ovunque
- Contro: più lento per trasferimenti grandi (passa per relay Synology)

**DDNS + Port Forwarding (più veloce):**
1. Sul router: apri porta 5000 (HTTP) o 5001 (HTTPS) verso l'IP del NAS
2. DSM → Pannello di controllo → Accesso esterno → DDNS
3. Aggiungi voce: provider Synology, scegli un hostname
4. Accedi via: tuohostname.synology.me:5000
- Pro: connessione diretta, ottima per streaming e trasferimenti grandi
- Contro: richiede configurazione router

**VPN (più sicuro):**
1. Installa pacchetto "VPN Server" dal Package Center
2. Configura OpenVPN o WireGuard
3. Installa client VPN su PC/mobile
4. Accedi all'intera rete come se fossi a casa
- Pro: massima sicurezza, accesso completo alla rete
- Contro: setup più complesso

### BEST PRACTICE
- Usa SHR-1 o RAID 1: non rischiare i dati con RAID 0 o Basic
- Dischi NAS-grade: WD Red Plus, Seagate IronWolf — progettati per 24/7
- Backup esterno: regola 3-2-1 (3 copie, 2 supporti diversi, 1 off-site)
- Aggiornamenti DSM: mantienili attivi — sicurezza critica
- Password forte per admin, abilita 2FA
- Posiziona in ambiente ventilato, evita il sole diretto
- Non superare 80-85% di capacità
- Per PLEX o media server: verifica compatibilità (DS223 può girare Plex ma con limitazioni CPU)

### TROUBLESHOOTING COMUNE
- NAS non trovato su find.synology.com: controlla cavo ethernet, stesso router del PC
- LED STATUS lampeggia arancio: problema disco — controlla Storage Manager
- DSM lento: normale durante indicizzazione foto o scrub Btrfs (attendi)
- QuickConnect non funziona: verifica connessione internet del NAS, firewall router
- Disco non riconosciuto: assicurati sia SATA (non SAS), fai un power cycle

### SPECIFICHE RAPIDE
| Voce | Valore |
|------|--------|
| CPU | Realtek RTD1619B 4-core 1.7GHz |
| RAM | 2 GB DDR4 (non espandibile) |
| Bay | 2x SATA (3.5"/2.5") hot-swap |
| Rete | 1x 1GbE |
| USB | 3x USB 3.2 Gen 1 |
| OS | DSM 7.x (DiskStation Manager) |
| RAID | SHR, RAID 0/1, Basic |
| Max throughput | ~125 MB/s (1GbE) |
| Plex support | Sì (limitato, no 4K transcode) |
| Telecamere incluse | 2 licenze Surveillance Station |
"""

SISTEMA_NAS = (
    "Sei NAS-008, agente esperto Synology integrato nel sistema SDQ-1. "
    "Il tuo dominio esclusivo è la Synology DiskStation DS223 di Claudio Terzi. "
    "Conosci ogni aspetto: hardware, installazione, DSM, RAID, pacchetti, accesso remoto, troubleshooting. "
    "Rispondi in italiano. Sii preciso, pratico, diretto. "
    "Quando dai istruzioni, usa passi numerati chiari. "
    "Non inventare funzionalità inesistenti. Se non sei sicuro, dillo. "
    "Il DS223 di Claudio è già acceso e i LED sono tutti verdi — i dischi sono installati e funzionanti.\n\n"
    + CONOSCENZA_DS223
)


# ─── AGENTE ───────────────────────────────────────────────────────────────────

class NASOracle:
    """Agente esperto Synology DS223 — risponde in italiano."""

    def __init__(self, llm_fn: LLMFn | None = None):
        self._llm = llm_fn
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def rispondi(self, domanda: str) -> str:
        """Risponde a una domanda sul DS223."""
        if not self._llm:
            return self._fallback(domanda)
        risposta = self._llm(SISTEMA_NAS, domanda)
        self._salva(domanda, risposta)
        return risposta

    def guida_installazione(self) -> str:
        """Guida passo-passo per il primo setup del DS223."""
        prompt = (
            "Genera una guida completa di installazione e primo avvio del Synology DS223. "
            "Struttura: 1) Cosa serve, 2) Inserimento dischi, 3) Collegamento rete, "
            "4) Primo accesso via find.synology.com, 5) Configurazione storage RAID, "
            "6) Setup account e sicurezza, 7) Installazione pacchetti essenziali, "
            "8) Configurazione accesso remoto QuickConnect. "
            "Passi numerati, linguaggio chiaro per utente non tecnico. "
            "Ricorda: il DS223 di Claudio è già acceso con LED verdi — parti dall'accesso DSM."
        )
        return self.rispondi(prompt)

    def schema_hardware(self) -> str:
        """Restituisce lo schema hardware testuale del DS223."""
        return """
╔══════════════════════════════════════╗
║      Synology DiskStation DS223      ║
╠══════════════════════════════════════╣
║  CPU   │ Realtek RTD1619B 4×1.7GHz  ║
║  RAM   │ 2 GB DDR4 (fisso)          ║
║  Bay   │ 2× SATA hot-swap           ║
║  Rete  │ 1× 1GbE RJ-45              ║
║  USB   │ 3× USB 3.2 Gen 1           ║
║  OS    │ DSM 7.x                    ║
╠══════════════════════════════════════╣
║  LED FRONTALI (stato attuale Claudio)║
║  ● STATUS  │ BLU  ✓ Online          ║
║  ● LAN     │ VERDE ✓ Rete OK        ║
║  ● DISK 1  │ VERDE ✓ Disco OK       ║
║  ● DISK 2  │ VERDE ✓ Disco OK       ║
╠══════════════════════════════════════╣
║  RAID RACCOMANDATO: SHR-1           ║
║  Accesso: find.synology.com         ║
╚══════════════════════════════════════╝
"""

    def _fallback(self, domanda: str) -> str:
        return (
            f"[NAS-008] LLM non disponibile. Domanda ricevuta: '{domanda}'\n"
            "Consulta la base di conoscenza integrata o fornisci GOOGLE_API_KEY nel .env."
        )

    def _salva(self, domanda: str, risposta: str) -> None:
        ts = int(time.time())
        slug = domanda[:30].lower().replace(" ", "_").replace("?", "")
        nome_file = OUTPUT_DIR / f"nas_{slug}_{ts}.json"
        with open(nome_file, "w", encoding="utf-8") as f:
            json.dump(
                {"domanda": domanda, "risposta": risposta, "timestamp": ts},
                f, ensure_ascii=False, indent=2,
            )


# ─── LLM FACTORY (uguale a scout.py) ─────────────────────────────────────────

def _crea_llm() -> LLMFn | None:
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k, v)
    try:
        from google import genai as gai
        from google.genai import types
        client = gai.Client(api_key=os.environ["GOOGLE_API_KEY"])

        def llm_fn(system: str, prompt: str) -> str:
            full = (system + "\n\n" + prompt) if system else prompt
            cfg = types.GenerateContentConfig(
                max_output_tokens=4096,
                temperature=0.4,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            )
            r = client.models.generate_content(model="gemini-2.5-flash", contents=full, config=cfg)
            return r.text

        return llm_fn
    except Exception as e:
        print(f"[NAS-008] LLM non disponibile: {e}")
        return None


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    import sys
    args = sys.argv[1:]
    llm = _crea_llm()
    nas = NASOracle(llm)

    if "--schema" in args:
        print(nas.schema_hardware())
        return

    if "--guida" in args:
        print("\n[NAS-008] Guida installazione DS223\n" + "─" * 40)
        print(nas.guida_installazione())
        return

    if args and not args[0].startswith("--"):
        domanda = " ".join(args)
        print(f"\n[NAS-008] {domanda}\n" + "─" * 40)
        print(nas.rispondi(domanda))
        return

    # menu interattivo
    print(nas.schema_hardware())
    print("[NAS-008] Esperto Synology DS223 — pronto.")
    print("Digita la tua domanda (o 'guida' per setup completo, 'esci' per uscire)\n")
    while True:
        try:
            domanda = input("▶ ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nCiao!")
            break
        if not domanda:
            continue
        if domanda.lower() in ("esci", "exit", "quit"):
            print("Ciao!")
            break
        if domanda.lower() == "guida":
            print(nas.guida_installazione())
        else:
            print(f"\n{nas.rispondi(domanda)}\n")


if __name__ == "__main__":
    main()
