"""Backup Universale — snapshot verificabile e restore dello stato SDQ-1.

Il backup privilegia recuperabilità e semplicità:
- scrittura atomica;
- hash SHA-256 del payload;
- stato esplicito dei componenti, senza promuovere backup parziali a completi;
- restore compatibile con backup legacy, ma rifiuto dei backup nuovi manomessi.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_BACKUP_DIR = Path("output/backups")
_SAR_DIR = Path.home() / ".sdq1" / "sar"
_BACKUP_SCHEMA = "r3-backup/2"


class BackupIntegrityError(RuntimeError):
    """Il contenuto del backup non corrisponde alla sua impronta registrata."""


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    try:
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)


def _canonical_bytes(snapshot: dict[str, Any]) -> bytes:
    payload = {k: v for k, v in snapshot.items() if k != "integrity"}
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")


def _snapshot_sha256(snapshot: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(snapshot)).hexdigest()


def _leggi_sar_con_stato() -> tuple[dict[str, Any], list[str]]:
    sar_data: dict[str, Any] = {}
    errors: list[str] = []
    if not _SAR_DIR.exists():
        return sar_data, errors

    for f in _SAR_DIR.glob("*.json"):
        try:
            sar_data[f.name] = json.loads(f.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{f.name}:{type(exc).__name__}")
            logger.warning("SAR non acquisito nel backup: %s", f.name)

    for f in _SAR_DIR.glob("*.jsonl"):
        try:
            sar_data[f.name] = [
                json.loads(riga)
                for riga in f.read_text(encoding="utf-8").splitlines()
                if riga
            ]
        except Exception as exc:
            errors.append(f"{f.name}:{type(exc).__name__}")
            logger.warning("SAR jsonl non acquisito nel backup: %s", f.name)

    return sar_data, errors


def _leggi_sar() -> dict[str, Any]:
    """Compatibilità: restituisce i dati SAR leggibili."""
    return _leggi_sar_con_stato()[0]


def _component_status(provided: bool) -> str:
    return "pending" if provided else "not_provided"


def crea_backup(
    memoria=None,
    vss=None,
    router=None,
    config=None,
    etichetta: str = "",
) -> Path:
    """Crea un backup atomico, auto-verificabile e restituisce il path."""
    _BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
    nome = f"backup_{ts}{'_' + etichetta if etichetta else ''}.json"
    dest = _BACKUP_DIR / nome

    sar, sar_errors = _leggi_sar_con_stato()
    status = {
        "sar": "partial" if sar_errors else "ok",
        "memoria": _component_status(memoria is not None),
        "vss": _component_status(vss is not None),
        "router": _component_status(router is not None),
        "config": _component_status(config is not None),
    }
    errors = [f"sar:{item}" for item in sar_errors]

    snapshot: dict[str, Any] = {
        "meta": {
            "timestamp": time.time(),
            "data_ora": ts,
            "versione": "1.5.1",
            "schema": _BACKUP_SCHEMA,
            "etichetta": etichetta,
        },
        "component_status": status,
        "errors": errors,
        "sar": sar,
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
            status["memoria"] = "ok"
        except Exception as exc:
            status["memoria"] = "error"
            errors.append(f"memoria:{type(exc).__name__}")
            logger.warning("Esportazione memoria fallita", exc_info=True)

    if vss is not None:
        try:
            snapshot["vss"] = vss.esporta()
            status["vss"] = "ok"
        except Exception as exc:
            status["vss"] = "error"
            errors.append(f"vss:{type(exc).__name__}")
            logger.warning("Esportazione VSS fallita", exc_info=True)

    if router is not None:
        try:
            snapshot["provider_attivi"] = router.provider_attivi()
            snapshot["circuit_breaker"] = router.stato_circuit_breaker()
            status["router"] = "ok"
        except Exception as exc:
            status["router"] = "error"
            errors.append(f"router:{type(exc).__name__}")
            logger.warning("Stato router non disponibile per backup", exc_info=True)

    if config is not None:
        try:
            snapshot["config"] = {
                "sistema": config.sistema,
                "modello": config.modello,
                "router_profili": [r["profilo"] for r in config.router.get("regole", [])],
            }
            status["config"] = "ok"
        except Exception as exc:
            status["config"] = "error"
            errors.append(f"config:{type(exc).__name__}")
            logger.warning("Serializzazione config fallita", exc_info=True)

    complete = all(value == "ok" for value in status.values())
    snapshot["meta"]["complete"] = complete
    snapshot["integrity"] = {
        "algorithm": "sha256",
        "payload_sha256": _snapshot_sha256(snapshot),
    }

    _atomic_write_text(
        dest,
        json.dumps(snapshot, indent=2, ensure_ascii=False, default=str),
    )

    # Postcondizione locale: il file appena scritto deve verificarsi da solo.
    verifica = verifica_backup(dest)
    if not verifica["verified"]:
        dest.unlink(missing_ok=True)
        raise BackupIntegrityError("Verifica post-scrittura del backup fallita")

    try:
        from sdq1.notifiche import notifica_completato

        notifica_completato(
            "Backup completato" if complete else "Backup parziale conservato",
            [
                f"📁 {dest.name}",
                f"SAR: {len(snapshot['sar'])} file | Memoria: {len(snapshot['memoria'])} voci",
                f"Dimensione: {round(dest.stat().st_size / 1024, 1)} KB",
            ],
        )
    except Exception:
        pass
    return dest


def verifica_backup(path: str | Path) -> dict[str, Any]:
    """Verifica integrità del backup senza modificarne il contenuto."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Backup non trovato: {path}")

    data = json.loads(p.read_text(encoding="utf-8"))
    integrity = data.get("integrity")
    if not isinstance(integrity, dict) or not integrity.get("payload_sha256"):
        return {
            "verified": False,
            "legacy_unverified": True,
            "expected_sha256": None,
            "actual_sha256": _snapshot_sha256(data),
            "complete": data.get("meta", {}).get("complete"),
        }

    actual = _snapshot_sha256(data)
    expected = str(integrity.get("payload_sha256"))
    return {
        "verified": actual == expected,
        "legacy_unverified": False,
        "expected_sha256": expected,
        "actual_sha256": actual,
        "complete": bool(data.get("meta", {}).get("complete", False)),
    }


def lista_backup() -> list[dict[str, Any]]:
    """Elenca backup disponibili, dal più recente, con stato di integrità."""
    if not _BACKUP_DIR.exists():
        return []
    files = sorted(_BACKUP_DIR.glob("backup_*.json"), reverse=True)
    result = []
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            meta = data.get("meta", {})
            verifica = verifica_backup(f)
            result.append(
                {
                    "file": str(f),
                    "data_ora": meta.get("data_ora", "?"),
                    "etichetta": meta.get("etichetta", ""),
                    "dimensione_kb": round(f.stat().st_size / 1024, 1),
                    "complete": meta.get("complete"),
                    "verified": verifica["verified"],
                    "legacy_unverified": verifica["legacy_unverified"],
                }
            )
        except Exception:
            logger.debug("Lettura metadati backup fallita: %s", f.name, exc_info=True)
    return result


def _serialize_sar_file(contenuto: Any) -> str:
    if isinstance(contenuto, list):
        return "\n".join(json.dumps(r, ensure_ascii=False) for r in contenuto)
    return json.dumps(contenuto, indent=2, ensure_ascii=False)


def ripristina_backup(path: str | Path) -> dict[str, Any]:
    """Ripristina SAR solo dopo verifica; i backup legacy restano compatibili."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Backup non trovato: {path}")

    data = json.loads(p.read_text(encoding="utf-8"))
    verifica = verifica_backup(p)
    if not verifica["legacy_unverified"] and not verifica["verified"]:
        raise BackupIntegrityError(
            f"Backup alterato: expected={verifica['expected_sha256']} "
            f"actual={verifica['actual_sha256']}"
        )

    sar = data.get("sar", {})
    rendered: dict[str, str] = {}
    if isinstance(sar, dict):
        # Preflight completo prima della prima scrittura.
        for nome_file, contenuto in sar.items():
            if "/" in nome_file or "\\" in nome_file or nome_file in {".", ".."}:
                raise BackupIntegrityError(f"Nome SAR non sicuro: {nome_file!r}")
            rendered[nome_file] = _serialize_sar_file(contenuto)

    if rendered:
        _SAR_DIR.mkdir(parents=True, exist_ok=True)
        for nome_file, text in rendered.items():
            _atomic_write_text(_SAR_DIR / nome_file, text)

    return {
        "ripristinato": str(p),
        "meta": data.get("meta", {}),
        "integrity_verified": verifica["verified"],
        "legacy_unverified": verifica["legacy_unverified"],
        "backup_complete": data.get("meta", {}).get("complete"),
        "file_sar_ripristinati": list(rendered.keys()),
        "memoria_entries": len(data.get("memoria", [])),
        "vss_entries": len(data.get("vss", [])),
    }
