"""
============================================================
SDQ-1 — bus_onda.py
ONDA v1.1.1 — il bus nervoso degli agenti SDQ-1
Fornisce le primitive che ogni nodo ONDA condivide:
  - Busta      → la lettera che viaggia sul bus (serializzabile, mutabile)
  - BusONDA    → il canale: pub/sub Redis async + registro + epoca + audit
  - AgenteONDA → il contratto base di un nodo (registro, heartbeat, ACK,
                 dedup idempotente v1.1.1, riti SYNC/epoca)
  - scrivi_audit → la memoria di ciò che è passato (lista Redis limitata)

Regole del protocollo (le stesse che RAFFA-001 cita):
  §1  Un solo emittente su CANALE_COMANDI: l'Architetto (RAFFA-001).
  §3  ACK entro TIMEOUT_ACK, un reinvio con lo STESSO id, poi ack_mancato.
  §5  Instradamento per CAPACITÀ, letta dal registro — mai liste cablate.
  Rito 1  All'avvio un agente chiede la SYNC all'Architetto.
  Rito 3  Solo l'Architetto dichiara una nuova epoca.

Idempotenza v1.1.1: un COMANDO con un id già visto NON viene rieseguito;
si rimanda l'ACK (e, se c'era, la RISPOSTA in cache). Così un reinvio §3 o
una riassegnazione sullo stesso id non producono doppi effetti.

Config via ambiente: SDQ1_REDIS_HOST (127.0.0.1), SDQ1_REDIS_PORTA (6379),
SDQ1_REDIS_DB (0). Senza il pacchetto `redis`, BusONDA alza un errore chiaro
alla costruzione; il resto del modulo (Busta, costanti) resta importabile.
Dipendenze: redis>=4.2 (redis.asyncio)
© Claudio Terzi
============================================================
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import asdict, dataclass, field, fields

log = logging.getLogger("onda")

try:  # il bus vive su Redis async; il modulo resta importabile senza di esso
    import redis.asyncio as aioredis
    _AIOREDIS_OK = True
except Exception:  # noqa: BLE001
    aioredis = None  # type: ignore[assignment]
    _AIOREDIS_OK = False


# ============================================================
# Costanti e nomi (una sola fonte di verità per tutti i nodi)
# ============================================================

PROTOCOLLO = "1.1.1"

#: Radice di ogni chiave/canale del bus. CANALE_COMANDI combacia con la
#: Regola §1 ("sdq1:bus:comandi": un solo emittente, l'Architetto).
PREFISSO = "sdq1:bus:"

CANALE_COMANDI = PREFISSO + "comandi"
CANALE_RISPOSTE = PREFISSO + "risposte"
CANALE_EVENTI = PREFISSO + "eventi"

CHIAVE_EPOCA = PREFISSO + "epoca"
CHIAVE_AUDIT = PREFISSO + "audit"

#: Il registro di un agente scade da solo: se il nodo muore e smette di
#: rinnovarlo (heartbeat), sparisce dalla discovery §5 entro TTL_REGISTRO.
TTL_REGISTRO = 30                 # secondi
INTERVALLO_HEARTBEAT = 10         # secondi (< TTL_REGISTRO: rinnova in tempo)
TTL_STATO = 60                    # secondi, per la chiave di stato

#: §3 — l'Architetto attende l'ACK per questo tempo prima del reinvio.
TIMEOUT_ACK = 2.0                 # secondi

MAX_AUDIT = 1000                  # righe trattenute nella lista di audit
MAX_VISTI = 4096                  # id ricordati per la dedup idempotente


def chiave_registro(id_agente: str) -> str:
    """Chiave Redis del registro di capacità di un agente (§5)."""
    return f"{PREFISSO}registro:{id_agente}"


def chiave_stato(id_agente: str) -> str:
    """Chiave Redis dello stato dichiarato da un agente."""
    return f"{PREFISSO}stato:{id_agente}"


def chiave_heartbeat(id_agente: str) -> str:
    """Chiave Redis dell'ultimo battito di un agente (la osserva SENTIN)."""
    return f"{PREFISSO}battito:{id_agente}"


def canale_agente(id_agente: str) -> str:
    """Canale privato di un nodo (es. risposta diretta a una SYNC)."""
    return f"{PREFISSO}agente:{id_agente}"


# ============================================================
# Busta — la lettera che viaggia sul bus
# ============================================================

@dataclass
class Busta:
    """Un messaggio ONDA. Mutabile: la riassegnazione §3 riscrive il
    `destinatario` tenendo lo stesso `id_messaggio` (idempotenza)."""

    mittente: str
    destinatario: str
    tipo: str                                   # COMANDO/ACK/RISPOSTA/EVENTO/SYNC_*
    payload: dict = field(default_factory=dict)
    richiedi_ack: bool = False
    id_messaggio: str = field(default_factory=lambda: uuid.uuid4().hex)
    id_correlazione: str | None = None          # id del messaggio a cui si risponde
    epoca: int | None = None
    ts: float = field(default_factory=time.time)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

    @classmethod
    def from_json(cls, raw: str | bytes) -> "Busta":
        dati = json.loads(raw)
        noti = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in dati.items() if k in noti})


# ============================================================
# BusONDA — il canale (pub/sub + registro + epoca + audit)
# ============================================================

class BusONDA:
    """Involucro sottile su Redis async. `self.r` è il client grezzo, usato
    direttamente dai nodi per registro/discovery (set/get/scan_iter)."""

    def __init__(self, r=None, *, host: str | None = None,
                 porta: int | None = None, db: int | None = None):
        if r is not None:
            self.r = r  # iniezione (test, fakeredis, client condiviso)
            return
        if not _AIOREDIS_OK:
            raise RuntimeError(
                "redis.asyncio non disponibile: installa 'redis>=4.2' "
                "(pip install redis) per usare il bus ONDA."
            )
        self.r = aioredis.Redis(
            host=host or os.getenv("SDQ1_REDIS_HOST", "127.0.0.1"),
            port=porta or int(os.getenv("SDQ1_REDIS_PORTA", "6379")),
            db=db if db is not None else int(os.getenv("SDQ1_REDIS_DB", "0")),
            decode_responses=True,
        )

    # ---------- pub/sub ----------

    async def pubblica(self, canale: str, busta: Busta) -> None:
        await self.r.publish(canale, busta.to_json())

    async def ascolta(self, canali: list[str], handler) -> None:
        """Si iscrive ai canali e consegna ogni Busta ad `handler(canale, busta)`.
        Gira finché il task non viene cancellato."""
        pubsub = self.r.pubsub()
        await pubsub.subscribe(*canali)
        try:
            async for msg in pubsub.listen():
                if msg.get("type") != "message":
                    continue
                try:
                    busta = Busta.from_json(msg["data"])
                except Exception as exc:  # noqa: BLE001 — una lettera storta non ferma il bus
                    log.warning("[bus] busta illeggibile su %s: %s", msg.get("channel"), exc)
                    continue
                try:
                    await handler(msg["channel"], busta)
                except Exception:  # noqa: BLE001 — un handler che cade non uccide l'ascolto
                    log.exception("[bus] handler in errore su %s", msg.get("channel"))
        finally:
            try:
                await pubsub.unsubscribe(*canali)
                await pubsub.aclose()
            except Exception:  # noqa: BLE001
                pass

    # ---------- epoca (Rito 3) ----------

    async def epoca_corrente(self) -> int:
        v = await self.r.get(CHIAVE_EPOCA)
        return int(v) if v else 0

    async def nuova_epoca(self) -> int:
        return int(await self.r.incr(CHIAVE_EPOCA))


# ============================================================
# Audit — la memoria di ciò che è passato
# ============================================================

async def scrivi_audit(r, busta: Busta, nota: str | None = None) -> None:
    """Appende una riga alla lista di audit (limitata a MAX_AUDIT)."""
    rec = {
        "ts": time.time(),
        "mittente": busta.mittente,
        "destinatario": busta.destinatario,
        "tipo": busta.tipo,
        "id_messaggio": busta.id_messaggio,
        "payload": busta.payload,
        "nota": nota,
    }
    try:
        await r.rpush(CHIAVE_AUDIT, json.dumps(rec, ensure_ascii=False, default=str))
        await r.ltrim(CHIAVE_AUDIT, -MAX_AUDIT, -1)
    except Exception as exc:  # noqa: BLE001 — l'audit non deve mai bloccare il flusso
        log.warning("[bus] audit non scritto: %s", exc)


# ============================================================
# AgenteONDA — il contratto base di un nodo
# ============================================================

class AgenteONDA(ABC):
    """Nodo generico del bus. L'Architetto (RAFFA-001) sovrascrive `avvia`
    perché è il solo a emettere comandi; un agente esecutore usa invece
    l'`avvia` di default: si registra, batte il cuore, ascolta i comandi a
    lui destinati, risponde con ACK + RISPOSTA e rispetta la dedup §idempotenza.

    Sottoclassi dichiarano RUOLO, CASELLE, CAPACITA come attributi di classe.
    """

    RUOLO: str = "Agente"
    CASELLE: list[int] = []
    CAPACITA: list[str] = []

    def __init__(self, id_agente: str, bus: BusONDA | None = None):
        self.id = id_agente
        self.bus = bus or BusONDA()
        self.attivo = False
        # dedup idempotente: id_messaggio → RISPOSTA in cache (o None se in corso)
        self._visti: "OrderedDict[str, Busta | None]" = OrderedDict()

    # ---------- registro, stato, battito ----------

    def _descrittore(self) -> dict:
        return {
            "id": self.id, "ruolo": self.RUOLO, "caselle": self.CASELLE,
            "capacita": self.CAPACITA, "versione_protocollo": PROTOCOLLO,
        }

    async def _registra(self) -> None:
        await self.bus.r.set(
            chiave_registro(self.id), json.dumps(self._descrittore()),
            ex=TTL_REGISTRO,
        )

    async def _scrivi_stato(self, stato: str) -> None:
        await self.bus.r.set(
            chiave_stato(self.id),
            json.dumps({"id": self.id, "stato": stato, "ts": time.time()}),
            ex=TTL_STATO,
        )

    async def _batti(self) -> None:
        await self.bus.r.set(chiave_heartbeat(self.id), str(time.time()), ex=TTL_REGISTRO)

    async def _loop_heartbeat(self) -> None:
        """Rinnova registro + battito finché il nodo è attivo: se muore, il
        registro scade e la discovery §5 smette di proporlo."""
        while self.attivo:
            try:
                await self._registra()
                await self._batti()
            except Exception as exc:  # noqa: BLE001
                log.warning("[%s] heartbeat fallito: %s", self.id, exc)
            await asyncio.sleep(INTERVALLO_HEARTBEAT)

    # ---------- avvio di default (nodo esecutore) ----------

    async def avvia(self) -> None:
        await self._registra()
        await self._scrivi_stato("ATTIVO")
        self.attivo = True
        log.info("[%s] %s in ascolto.", self.id, self.RUOLO)
        await self._sync_con_architetto()          # Rito 1
        await asyncio.gather(
            self._loop_heartbeat(),
            self.bus.ascolta([CANALE_COMANDI], self._su_comando),
            self.bus.ascolta([CANALE_EVENTI], self._su_evento),
            self.bus.ascolta([canale_agente(self.id)], self._su_privato),
        )

    # ---------- Rito 1: chiedo la sync all'Architetto ----------

    async def _sync_con_architetto(self) -> None:
        richiesta = Busta(mittente=self.id, destinatario="RAFFA-001",
                          tipo="SYNC_RICHIESTA", payload={})
        await self.bus.pubblica(CANALE_RISPOSTE, richiesta)

    async def _su_privato(self, canale: str, busta: Busta) -> None:
        if busta.tipo == "SYNC_RISPOSTA":
            log.info("[%s] sync ricevuta: epoca %s, %d pendenti",
                     self.id, busta.payload.get("epoca"),
                     len(busta.payload.get("compiti_pendenti", [])))

    # ---------- ricezione comandi + dedup idempotente ----------

    async def _su_comando(self, canale: str, busta: Busta) -> None:
        if busta.tipo != "COMANDO":
            return
        if busta.destinatario not in (self.id, "*"):
            return  # §1/§5: eseguo solo ciò che è instradato a me

        # idempotenza v1.1.1: id già visto → non rieseguo, rimando ACK (+ risposta)
        if busta.id_messaggio in self._visti:
            if busta.richiedi_ack:
                await self._invia_ack(busta)
            cached = self._visti[busta.id_messaggio]
            if cached is not None:
                await self.bus.pubblica(CANALE_RISPOSTE, cached)
            return

        self._ricorda(busta.id_messaggio, None)
        if busta.richiedi_ack:
            await self._invia_ack(busta)

        try:
            esito = await self.esegui_comando(busta)
            risposta = Busta(
                mittente=self.id, destinatario=busta.mittente, tipo="RISPOSTA",
                id_correlazione=busta.id_messaggio,
                payload={"ok": True, **(esito or {})},
            )
        except Exception as exc:  # noqa: BLE001
            log.exception("[%s] comando %s fallito", self.id, busta.id_messaggio[:8])
            risposta = Busta(
                mittente=self.id, destinatario=busta.mittente, tipo="RISPOSTA",
                id_correlazione=busta.id_messaggio,
                payload={"ok": False, "errore": str(exc)},
            )
        self._ricorda(busta.id_messaggio, risposta)
        await self.bus.pubblica(CANALE_RISPOSTE, risposta)

    async def _invia_ack(self, busta: Busta) -> None:
        ack = Busta(mittente=self.id, destinatario=busta.mittente, tipo="ACK",
                    id_correlazione=busta.id_messaggio, payload={})
        await self.bus.pubblica(CANALE_RISPOSTE, ack)

    def _ricorda(self, id_messaggio: str, risposta: Busta | None) -> None:
        self._visti[id_messaggio] = risposta
        self._visti.move_to_end(id_messaggio)
        while len(self._visti) > MAX_VISTI:
            self._visti.popitem(last=False)

    # ---------- eventi comuni (epoca, ecc.) ----------

    async def _su_evento(self, canale: str, busta: Busta) -> None:
        """Gancio sovrascrivibile. Di default reagisce al cambio d'epoca
        ri-sincronizzandosi con l'Architetto (Rito 3 → Rito 1)."""
        if busta.tipo == "EVENTO" and busta.payload.get("evento") == "nuova_epoca":
            await self._sync_con_architetto()

    # ---------- il lavoro vero del nodo ----------

    @abstractmethod
    async def esegui_comando(self, busta: Busta) -> dict | None:
        """Esegue il COMANDO e restituisce il payload della RISPOSTA.
        L'Architetto NON esegue: la sua implementazione alza un errore."""
