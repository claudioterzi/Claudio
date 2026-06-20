"""Backup Universale — snapshot e restore dello stato SDQ-1.

Salva in output/backups/backup_YYYY-MM-DD_HH-MM-SS.json:
  - Memoria vettoriale (testi + metadata)
  - VSS entries (run_id, agente, testo)
  - Stato SAR su disco (~/.sdq1/sar/)
  - Config attiva (sdq1.yaml serializzata)
  - Metadati (versione, timestamp, provider_attivi)
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_BACKUP_DIR = Path("output/backups")
_SAR_DIR = Path.home() / ".sdq1" / "sar"


def _leggi_sar() -> dict[str, Any]:
    """Raccoglie tutti i file SAR su disco."""
    sar_data: dict[str, Any] = {}
    if _SAR_DIR.exists():
        for f in _SAR_DIR.glob("*.json"):
            try:
                sar_data[f.name] = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                logger.debug("Lettura SAR fallita: %s", f.name, exc_info=True)
        for f in _SAR_DIR.glob("*.jsonl"):
            try:
                sar_data[f.name] = [
                    json.loads(riga) for riga in f.read_text(encoding="utf-8").splitlines() if riga
                ]
            except Exception:
                logger.debug("Lettura SAR jsonl fallita: %s", f.name, exc_info=True)
    return sar_data


def crea_backup(
    memoria=None,
    vss=None,
    router=None,
    config=None,
    etichetta: str = "",
) -> Path:
    """Crea un backup completo e restituisce il path del file."""
    _BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nome = f"backup_{ts}{'_' + etichetta if etichetta else ''}.json"
    dest = _BACKUP_DIR / nome

    snapshot: dict[str, Any] = {
        "meta": {
            "timestamp": time.time(),
            "data_ora": ts,
            "versione": "1.5.0",
            "etichetta": etichetta,
        },
        "sar": _leggi_sar(),
        "memoria": [],
        "vss": [],
        "provider_attivi": {},
        "circuit_breaker": {},
    }

    if memoria is not None:
        try:
            snapshot["memoria"] = [
                {"testo": e["testo"], "metadata": e.get("metadata", {})}
                for e in memoria.esporta()
            ]
        except Exception:
            logger.debug("Esportazione memoria fallita", exc_info=True)

    if vss is not None:
        try:
            snapshot["vss"] = vss.esporta()
        except Exception:
            logger.debug("Esportazione VSS fallita", exc_info=True)

    if router is not None:
        try:
            snapshot["provider_attivi"] = router.provider_attivi()
            snapshot["circuit_breaker"] = router.stato_circuit_breaker()
        except Exception:
            logger.debug("Stato router non disponibile per backup", exc_info=True)

    if config is not None:
        try:
            snapshot["config"] = {
                "sistema": config.sistema,
                "modello": config.modello,
                "router_profili": [r["profilo"] for r in config.router.get("regole", [])],
            }
        except Exception:
            logger.debug("Serializzazione config fallita", exc_info=True)

    dest.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False, default=str),
                    encoding="utf-8")
    return dest


def lista_backup() -> list[dict[str, Any]]:
    """Elenca backup disponibili, dal più recente."""
    if not _BACKUP_DIR.exists():
        return []
    files = sorted(_BACKUP_DIR.glob("backup_*.json"), reverse=True)
    result = []
    for f in files:
        try:
            meta = json.loads(f.read_text(encoding="utf-8")).get("meta", {})
            result.append({
                "file": str(f),
                "data_ora": meta.get("data_ora", "?"),
                "etichetta": meta.get("etichetta", ""),
                "dimensione_kb": round(f.stat().st_size / 1024, 1),
            })
        except Exception:
            logger.debug("Lettura metadati backup fallita: %s", f.name, exc_info=True)
    return result


def ripristina_backup(path: str | Path) -> dict[str, Any]:
    """Carica un backup e ripristina lo stato SAR su disco."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Backup non trovato: {path}")

    data = json.loads(p.read_text(encoding="utf-8"))

    # Ripristino SAR
    sar = data.get("sar", {})
    if sar:
        _SAR_DIR.mkdir(parents=True, exist_ok=True)
        for nome_file, contenuto in sar.items():
            dest = _SAR_DIR / nome_file
            if isinstance(contenuto, list):
                dest.write_text(
                    "\n".join(json.dumps(r, ensure_ascii=False) for r in contenuto),
                    encoding="utf-8",
                )
            else:
                dest.write_text(json.dumps(contenuto, indent=2, ensure_ascii=False),
                                encoding="utf-8")

    return {
        "ripristinato": str(p),
        "meta": data.get("meta", {}),
        "file_sar_ripristinati": list(sar.keys()),
        "memoria_entries": len(data.get("memoria", [])),
        "vss_entries": len(data.get("vss", [])),
    }
