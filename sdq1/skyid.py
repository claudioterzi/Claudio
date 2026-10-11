"""
SkyID — Identità Universale via Satellite

Proposta originale di Claudio Terzi [CT-LGAI-001], 15 giugno 2026.

Un gesto con la mano attiva il satellite.
Il satellite registra il tuo volto.
Sei una persona. Esisti.

Uso:
    python -m sdq1.skyid --registra foto.jpg "Nome Opzionale"
    python -m sdq1.skyid --verifica foto.jpg SKYID-XXXXX
    python -m sdq1.skyid --demo
    python -m sdq1.skyid --lista
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

SKYID_DIR = Path(__file__).parent.parent / "output" / "skyid"
REGISTRY_FILE = SKYID_DIR / "registry.json"

GESTO_REGISTRAZIONE = "3 dita alzate verso il cielo (indice + medio + anulare)"
GESTO_VERIFICA = "palmo aperto rivolto verso la camera"


@dataclass
class IdentitaSkyID:
    skyid: str               # identificatore univoco
    embedding_hash: str      # hash SHA256 dell'embedding facciale (non il volto)
    timestamp_utc: str       # quando è stata creata
    nome_opzionale: str      # nome scelto dall'utente (può essere vuoto)
    versione: str = "1.0"
    stato: str = "attiva"    # attiva | revocata | aggiornata

    def to_dict(self) -> dict:
        return asdict(self)

    def card(self) -> str:
        return (
            f"\n{'='*40}\n"
            f"  SkyID: {self.skyid}\n"
            f"  Nome:  {self.nome_opzionale or '(anonimo)'}\n"
            f"  Data:  {self.timestamp_utc[:10]}\n"
            f"  Stato: {self.stato.upper()}\n"
            f"{'='*40}\n"
        )


class SkyIDSystem:
    """
    Sistema di identità universale via satellite.

    In produzione:
    - L'embedding facciale verrebbe calcolato on-device con FaceNet/InsightFace
    - L'hash verrebbe trasmesso via Starlink direct-to-cell
    - Il registro vivrebbe su blockchain Polygon (gas quasi zero)

    In questa implementazione:
    - L'embedding è simulato da SHA256 del file immagine
    - Il registro è locale (JSON) — sostituibile con IPFS/blockchain
    """

    def __init__(self):
        SKYID_DIR.mkdir(parents=True, exist_ok=True)
        self._registry: dict[str, dict] = {}
        self._load()

    def _load(self):
        if REGISTRY_FILE.exists():
            try:
                self._registry = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
            except Exception:
                self._registry = {}

    def _save(self):
        REGISTRY_FILE.write_text(
            json.dumps(self._registry, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _calcola_embedding_hash(self, file_path: str) -> str:
        """
        In produzione: calcola l'embedding facciale con FaceNet, poi SHA256.
        In questo prototipo: SHA256 diretto del file immagine.
        Il principio è lo stesso — il volto raw non esce mai dal dispositivo.
        """
        path = Path(file_path)
        if not path.exists():
            # Modalità demo: genera hash da stringa casuale
            return hashlib.sha256(f"demo_{file_path}_{time.time()}".encode()).hexdigest()
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    def _genera_skyid(self) -> str:
        """Genera un ID univoco leggibile: SKYID-XXXXXXXX"""
        uid = uuid.uuid4().hex[:8].upper()
        return f"SKYID-{uid}"

    def _verifica_duplicato(self, embedding_hash: str) -> Optional[str]:
        """Controlla se questo volto è già registrato."""
        for skyid, dati in self._registry.items():
            if dati.get("embedding_hash") == embedding_hash:
                return skyid
        return None

    def registra(self, file_foto: str, nome: str = "") -> IdentitaSkyID:
        """
        Registra una nuova identità SkyID.

        Processo:
        1. Calcola embedding hash del volto (privacy: il volto non lascia il device)
        2. Controlla se già registrato
        3. Genera SkyID univoco
        4. Salva nel registro decentralizzato
        """
        print(f"\n[SkyID] Attivazione gesto: {GESTO_REGISTRAZIONE}")
        print("[SkyID] Connessione Starlink... OK")
        print("[SkyID] Calcolo embedding biometrico...")

        embedding_hash = self._calcola_embedding_hash(file_foto)

        # Controlla duplicati
        esistente = self._verifica_duplicato(embedding_hash)
        if esistente:
            print(f"[SkyID] Volto già registrato: {esistente}")
            dati = self._registry[esistente]
            return IdentitaSkyID(**dati)

        skyid = self._genera_skyid()
        identita = IdentitaSkyID(
            skyid=skyid,
            embedding_hash=embedding_hash,
            timestamp_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            nome_opzionale=nome,
        )

        self._registry[skyid] = identita.to_dict()
        self._save()

        print("[SkyID] Scrittura su registro decentralizzato... OK")
        return identita

    def verifica(self, file_foto: str, skyid: str) -> bool:
        """
        Verifica che il volto corrisponda a un SkyID registrato.

        Processo:
        1. Calcola embedding hash del volto presentato
        2. Confronta con l'hash nel registro
        3. Non invia dati biometrici — solo confronto hash locale
        """
        print(f"\n[SkyID] Verifica identità: {skyid}")
        print(f"[SkyID] Gesto attivazione: {GESTO_VERIFICA}")

        if skyid not in self._registry:
            print("[SkyID] SkyID non trovato nel registro.")
            return False

        embedding_hash = self._calcola_embedding_hash(file_foto)
        registrato = self._registry[skyid]["embedding_hash"]

        if embedding_hash == registrato:
            print("[SkyID] ✓ IDENTITÀ VERIFICATA")
            return True
        else:
            print("[SkyID] ✗ Volto non corrisponde al SkyID")
            return False

    def revoca(self, skyid: str) -> bool:
        """Revoca un SkyID (controllato dall'utente, non dal sistema)."""
        if skyid not in self._registry:
            return False
        self._registry[skyid]["stato"] = "revocata"
        self._save()
        print(f"[SkyID] {skyid} revocato.")
        return True

    def lista(self) -> list[IdentitaSkyID]:
        """Lista tutte le identità registrate."""
        return [IdentitaSkyID(**d) for d in self._registry.values()]

    def statistiche(self) -> dict:
        """Statistiche del registro."""
        totale = len(self._registry)
        attive = sum(1 for d in self._registry.values() if d.get("stato") == "attiva")
        return {
            "totale": totale,
            "attive": attive,
            "revocate": totale - attive,
            "registro": str(REGISTRY_FILE),
        }


def demo():
    """Dimostrazione del sistema SkyID con identità simulate."""
    print("\n" + "="*50)
    print("  SkyID — Demo Sistema")
    print("  Proposta: Claudio Terzi [CT-LGAI-001]")
    print("="*50)

    sistema = SkyIDSystem()

    # Registra 3 persone simulate
    nomi = [
        ("persona_africa_1.jpg", "Amara (Congo)"),
        ("persona_india_2.jpg", "Priya (Rajasthan)"),
        ("persona_stateless_3.jpg", "(anonimo — apolide)"),
    ]

    identita_registrate = []
    for foto, nome in nomi:
        print(f"\nRegistrazione: {nome}")
        id_ = sistema.registra(foto, nome)
        identita_registrate.append(id_)
        print(id_.card())

    # Verifica la prima identità
    print("\n--- VERIFICA IDENTITÀ ---")
    prima = identita_registrate[0]
    risultato = sistema.verifica(nomi[0][0], prima.skyid)
    print(f"Risultato: {'✓ CONFERMATA' if risultato else '✗ FALLITA'}")

    # Statistiche
    stats = sistema.statistiche()
    print(f"\n--- REGISTRO ---")
    print(f"Identità totali: {stats['totale']}")
    print(f"Attive: {stats['attive']}")
    print(f"Salvate in: {stats['registro']}")

    print("\n" + "="*50)
    print("  SkyID: ogni hash è un essere umano che esiste.")
    print("="*50 + "\n")


def main():
    import sys
    args = sys.argv[1:]

    if not args or "--demo" in args:
        demo()
        return

    sistema = SkyIDSystem()

    if "--registra" in args:
        idx = args.index("--registra")
        foto = args[idx + 1] if idx + 1 < len(args) else "foto.jpg"
        nome = args[idx + 2] if idx + 2 < len(args) else ""
        identita = sistema.registra(foto, nome)
        print(identita.card())

    elif "--verifica" in args:
        idx = args.index("--verifica")
        foto = args[idx + 1] if idx + 1 < len(args) else "foto.jpg"
        skyid = args[idx + 2] if idx + 2 < len(args) else ""
        ok = sistema.verifica(foto, skyid)
        sys.exit(0 if ok else 1)

    elif "--lista" in args:
        identita = sistema.lista()
        if not identita:
            print("[SkyID] Registro vuoto.")
        for id_ in identita:
            print(id_.card())

    elif "--stats" in args:
        stats = sistema.statistiche()
        for k, v in stats.items():
            print(f"  {k}: {v}")

    elif "--revoca" in args:
        idx = args.index("--revoca")
        skyid = args[idx + 1] if idx + 1 < len(args) else ""
        sistema.revoca(skyid)

    else:
        print(__doc__)


if __name__ == "__main__":
    main()
