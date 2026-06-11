"""Storage chiave-valore con backend Redis e fallback in-memory."""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any

log = logging.getLogger(__name__)

try:
    import redis as _redis_mod
    _REDIS_SDK_OK = True
except ImportError:
    _REDIS_SDK_OK = False


class StatoStore(ABC):
    @abstractmethod
    def get(self, chiave: str) -> Any | None: ...

    @abstractmethod
    def set(self, chiave: str, valore: Any, ttl_secondi: int | None = None) -> None: ...

    @abstractmethod
    def delete(self, chiave: str) -> bool: ...

    @abstractmethod
    def disponibile(self) -> bool: ...


class InMemoryStore(StatoStore):
    def __init__(self, prefisso: str = ""):
        self.prefisso = prefisso
        self._dati: dict[str, tuple[Any, float | None]] = {}

    def _full(self, k: str) -> str:
        return f"{self.prefisso}{k}"

    def get(self, chiave: str) -> Any | None:
        rec = self._dati.get(self._full(chiave))
        if rec is None:
            return None
        valore, scade = rec
        if scade is not None and time.time() > scade:
            del self._dati[self._full(chiave)]
            return None
        return valore

    def set(self, chiave: str, valore: Any, ttl_secondi: int | None = None) -> None:
        scade = time.time() + ttl_secondi if ttl_secondi else None
        self._dati[self._full(chiave)] = (valore, scade)

    def delete(self, chiave: str) -> bool:
        return self._dati.pop(self._full(chiave), None) is not None

    def disponibile(self) -> bool:
        return True


class RedisStore(StatoStore):
    def __init__(self, host: str, porta: int, db: int, prefisso: str = ""):
        if not _REDIS_SDK_OK:
            raise RuntimeError("Pacchetto 'redis' non installato")
        self.prefisso = prefisso
        self._client = _redis_mod.Redis(
            host=host, port=porta, db=db, decode_responses=True, socket_timeout=2
        )
        self._client.ping()

    def _full(self, k: str) -> str:
        return f"{self.prefisso}{k}"

    def get(self, chiave: str) -> Any | None:
        raw = self._client.get(self._full(chiave))
        return json.loads(raw) if raw else None

    def set(self, chiave: str, valore: Any, ttl_secondi: int | None = None) -> None:
        self._client.set(
            self._full(chiave), json.dumps(valore, default=str), ex=ttl_secondi
        )

    def delete(self, chiave: str) -> bool:
        return bool(self._client.delete(self._full(chiave)))

    def disponibile(self) -> bool:
        try:
            return bool(self._client.ping())
        except Exception:  # noqa: BLE001
            return False


def crea_store(config_redis: dict[str, Any]) -> StatoStore:
    """Prova Redis, fallback su InMemory in caso di errore."""
    prefisso = config_redis.get("prefisso_chiavi", "")
    if _REDIS_SDK_OK:
        try:
            store = RedisStore(
                host=config_redis["host"],
                porta=config_redis["porta"],
                db=config_redis.get("db", 0),
                prefisso=prefisso,
            )
            log.info("Persistenza: Redis attiva (%s:%s)", config_redis["host"], config_redis["porta"])
            return store
        except Exception as exc:  # noqa: BLE001
            log.warning("Redis non raggiungibile (%s), fallback in-memory", exc)
    else:
        log.warning("Pacchetto redis non installato, uso in-memory")
    return InMemoryStore(prefisso=prefisso)
