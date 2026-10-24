"""
Test del bus ONDA v1.1.1 — nessun Redis richiesto.

Un FakeRedis async in-process fornisce la superficie usata dal bus
(set/get/incr/scan_iter/rpush/ltrim + pub/sub). Così il protocollo si
verifica davvero end-to-end: registro §5, ACK §3, RISPOSTA, dedup
idempotente. Eseguibile con pytest o da solo: `python test_onda.py`.
"""

from __future__ import annotations

import asyncio
import fnmatch
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))  # abilita gli import piatti dei nodi

import bus_onda  # noqa: E402
from bus_onda import (  # noqa: E402
    AgenteONDA, Busta, BusONDA,
    CANALE_COMANDI, CANALE_RISPOSTE,
    PROTOCOLLO, TIMEOUT_ACK, chiave_registro, canale_agente,
)
from raffa_001 import Raffa  # noqa: E402  (verifica anche l'import piatto `import bus_onda`)


# ---------- Fake Redis async (solo per i test) ----------

class _FakePubSub:
    def __init__(self, broker: "_FakeRedis"):
        self.broker = broker
        self.queue: asyncio.Queue = asyncio.Queue()
        self.canali: set[str] = set()

    async def subscribe(self, *canali):
        for c in canali:
            self.canali.add(c)
            self.broker._subs.setdefault(c, set()).add(self.queue)

    async def unsubscribe(self, *canali):
        for c in (canali or tuple(self.canali)):
            self.broker._subs.get(c, set()).discard(self.queue)
            self.canali.discard(c)

    async def aclose(self):
        await self.unsubscribe()

    async def listen(self):
        while True:
            yield await self.queue.get()


class _FakeRedis:
    def __init__(self):
        self._kv: dict[str, str] = {}
        self._lists: dict[str, list] = {}
        self._subs: dict[str, set] = {}

    async def set(self, k, v, ex=None):
        self._kv[k] = v

    async def get(self, k):
        return self._kv.get(k)

    async def incr(self, k):
        self._kv[k] = str(int(self._kv.get(k, "0")) + 1)
        return int(self._kv[k])

    async def scan_iter(self, match="*"):
        for k in list(self._kv.keys()):
            if fnmatch.fnmatch(k, match):
                yield k

    async def rpush(self, k, v):
        self._lists.setdefault(k, []).append(v)

    async def ltrim(self, k, start, end):
        lst = self._lists.get(k, [])
        self._lists[k] = lst[start:] if end == -1 else lst[start:end + 1]

    async def publish(self, canale, data):
        for q in list(self._subs.get(canale, set())):
            q.put_nowait({"type": "message", "channel": canale, "data": data})

    def pubsub(self):
        return _FakePubSub(self)


# ---------- Un agente esecutore di prova ----------

class Salutatore(AgenteONDA):
    RUOLO = "Salutatore"
    CASELLE = [1]
    CAPACITA = ["saluta"]

    def __init__(self, id_agente="SALUTA-001", **kw):
        super().__init__(id_agente, **kw)
        self.esecuzioni = 0

    async def esegui_comando(self, busta: Busta) -> dict:
        self.esecuzioni += 1
        return {"testo": f"ciao da {self.id}", "azione": busta.payload.get("azione")}


# ---------- Test unitari (senza rete) ----------

def test_costanti_e_nomi():
    assert bus_onda.CANALE_COMANDI == "sdq1:bus:comandi"      # Regola §1
    assert PROTOCOLLO == "1.1.1"
    assert TIMEOUT_ACK == 2.0                                  # §3
    assert chiave_registro("X-1") == "sdq1:bus:registro:X-1"
    assert canale_agente("X-1") == "sdq1:bus:agente:X-1"


def test_busta_roundtrip_e_tollerante():
    b = Busta(mittente="A", destinatario="B", tipo="COMANDO",
              payload={"x": 1}, richiedi_ack=True)
    b2 = Busta.from_json(b.to_json())
    assert b2.id_messaggio == b.id_messaggio
    assert b2.payload == {"x": 1} and b2.richiedi_ack is True
    # campi extra ignorati, campi mancanti tollerati
    grezzo = '{"mittente":"A","destinatario":"B","tipo":"EVENTO","sconosciuto":9}'
    b3 = Busta.from_json(grezzo)
    assert b3.tipo == "EVENTO" and b3.payload == {}


# ---------- Test d'integrazione end-to-end ----------

async def _scenario_end_to_end():
    r = _FakeRedis()                       # un solo Redis condiviso da tutti i nodi
    raffa = Raffa(bus=BusONDA(r=r))
    worker = Salutatore(bus=BusONDA(r=r))

    # worker: avvio completo (registro + ascolto comandi) come task
    t_worker = asyncio.create_task(worker.avvia())
    # raffa: mi basta che ascolti le risposte per gestire ACK/RISPOSTA
    raffa.attivo = True
    t_raffa_risp = asyncio.create_task(
        raffa.bus.ascolta([CANALE_RISPOSTE], raffa._su_risposta))

    await asyncio.sleep(0.2)               # lascia completare registro + subscribe

    # il worker dev'essere nel registro, trovabile per capacità (§5)
    cand = await raffa.agenti_con_capacita("saluta")
    assert cand == ["SALUTA-001"], f"discovery §5 fallita: {cand}"

    # comando con ACK+RISPOSTA
    risp = await raffa.comanda("saluta", "parla")
    assert risp is not None, "nessuna risposta"
    assert risp.tipo == "RISPOSTA" and risp.payload.get("ok") is True
    assert risp.payload.get("testo") == "ciao da SALUTA-001"
    assert worker.esecuzioni == 1

    # idempotenza v1.1.1: rispedisco lo STESSO id → niente doppia esecuzione
    dup = Busta(mittente=raffa.id, destinatario=worker.id, tipo="COMANDO",
                richiedi_ack=True, payload={"azione": "parla"})
    dup.id_messaggio = risp.id_correlazione     # riuso l'id del comando già servito
    await raffa.bus.pubblica(CANALE_COMANDI, dup)
    await asyncio.sleep(0.2)
    assert worker.esecuzioni == 1, "il comando duplicato è stato rieseguito!"

    for t in (t_worker, t_raffa_risp):
        t.cancel()
    await asyncio.gather(t_worker, t_raffa_risp, return_exceptions=True)
    return True


def test_integrazione_end_to_end():
    assert asyncio.run(asyncio.wait_for(_scenario_end_to_end(), timeout=10))


if __name__ == "__main__":
    test_costanti_e_nomi()
    test_busta_roundtrip_e_tollerante()
    test_integrazione_end_to_end()
    print("ONDA v%s — tutti i test passati ✓" % PROTOCOLLO)
