"""Caricamento e validazione della configurazione SDQ-1."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:
    raise ImportError(
        "PyYAML non installato. Aggiungi 'pyyaml>=6.0' a requirements.txt"
    ) from exc


CONFIG_PATH_DEFAULT = Path(__file__).resolve().parent / "sdq1.yaml"


@dataclass
class AgenteConfig:
    id: str
    ruolo: str
    casella: int
    modello: str
    critico: bool = False


@dataclass
class SDQ1Config:
    sistema: dict[str, Any]
    redis: dict[str, Any]
    modello: dict[str, Any]
    caselle_attive: list[int]
    agenti: list[AgenteConfig]
    orchestratore: dict[str, Any]
    memoria: dict[str, Any]
    sicurezza: dict[str, Any]
    log: dict[str, Any]
    raw: dict[str, Any] = field(repr=False, default_factory=dict)

    def agente_per_casella(self, casella: int) -> AgenteConfig | None:
        for a in self.agenti:
            if a.casella == casella:
                return a
        return None

    def agente_per_id(self, agente_id: str) -> AgenteConfig | None:
        for a in self.agenti:
            if a.id == agente_id:
                return a
        return None


def carica_config(path: str | Path | None = None) -> SDQ1Config:
    config_path = Path(path) if path else CONFIG_PATH_DEFAULT
    if not config_path.exists():
        raise FileNotFoundError(f"Config non trovata: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    agenti = [AgenteConfig(**a) for a in data.get("agenti_attivi", [])]
    caselle_dichiarate = set(data.get("caselle_attive", []))
    caselle_agenti = {a.casella for a in agenti}
    mancanti = caselle_dichiarate - caselle_agenti
    if mancanti:
        raise ValueError(
            f"Caselle attive senza agente assegnato: {sorted(mancanti)}"
        )

    return SDQ1Config(
        sistema=data["sistema"],
        redis=data["redis"],
        modello=data["modello"],
        caselle_attive=sorted(caselle_dichiarate),
        agenti=agenti,
        orchestratore=data["orchestratore"],
        memoria=data["memoria"],
        sicurezza=data["sicurezza"],
        log=data["log"],
        raw=data,
    )
