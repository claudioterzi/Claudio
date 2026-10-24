"""
============================================================
SDQ-1 — raffa_001.py
RAFFA-001 · L'Architetto — orchestratore gerarchico, ONDA v1.1.1
Responsabilità:
  - UNICO emittente su sdq1:bus:comandi (Regola 1)
  - Instradamento per CAPACITÀ via registro (§5) — mai liste cablate
  - ACK: attesa 2 s, UN reinvio stesso id, poi ack_mancato (§3)
  - Risponde alle SYNC_RICHIESTA (Rito 1 degli agenti)
  - Ascolta agente_offline da SENTIN → riassegna i compiti pendenti
  - Autorità sul cambio d'epoca (Rito 3)
Dipendenze: bus_onda.py
© Claudio Terzi
============================================================
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid

import bus_onda
from bus_onda import (
    AgenteONDA, Busta, BusONDA, scrivi_audit,
    CANALE_COMANDI, CANALE_RISPOSTE, CANALE_EVENTI,
    canale_agente, chiave_registro, PREFISSO,
)

log = logging.getLogger("raffa")


class CompitoPendente:
    def __init__(self, busta: Busta, assegnato_a: str):
        self.busta = busta
        self.assegnato_a = assegnato_a
        self.ack = asyncio.Event()
        self.risposta: Busta | None = None
        self.risposta_evento = asyncio.Event()
        self.reinviato = False


class Raffa(AgenteONDA):
    RUOLO = "Architetto"
    CASELLE = [0]
    CAPACITA = ["orchestro"]

    def __init__(self, id_agente: str = "RAFFA-001", **kw):
        super().__init__(id_agente, **kw)
        self.pendenti: dict[str, CompitoPendente] = {}   # id_messaggio → compito

    # ---------- Avvio ----------

    async def avvia(self) -> None:
        r = self.bus.r
        await r.set(chiave_registro(self.id), json.dumps({
            "id": self.id, "ruolo": self.RUOLO, "caselle": self.CASELLE,
            "capacita": self.CAPACITA, "versione_protocollo": bus_onda.PROTOCOLLO,
        }), ex=bus_onda.TTL_REGISTRO)
        await self._scrivi_stato("ATTIVO")
        self.attivo = True
        log.info("[%s] Architetto al comando.", self.id)
        await asyncio.gather(
            self._loop_heartbeat(),
            self.bus.ascolta([CANALE_RISPOSTE], self._su_risposta),
            self.bus.ascolta([CANALE_EVENTI], self._su_evento),
        )

    # ---------- Discovery: chi sa fare cosa (§5) ----------

    async def agenti_con_capacita(self, capacita: str,
                                  escludi: set[str] | None = None) -> list[str]:
        escludi = escludi or set()
        trovati: list[str] = []
        async for chiave in self.bus.r.scan_iter(f"{PREFISSO}registro:*"):
            raw = await self.bus.r.get(chiave)
            if not raw:
                continue
            reg = json.loads(raw)
            if capacita in reg.get("capacita", []) and reg["id"] not in escludi \
                    and reg["id"] != self.id:
                trovati.append(reg["id"])
        return trovati

    # ---------- Invio comando con ACK e reinvio (§3) ----------

    async def comanda(self, capacita: str, azione: str, parametri: dict | None = None,
                      casella: int = 0, timeout_risposta: float = 30.0,
                      escludi: set[str] | None = None) -> Busta | None:
        candidati = await self.agenti_con_capacita(capacita, escludi)
        if not candidati:
            log.error("[%s] nessun agente con capacità '%s'", self.id, capacita)
            return None
        dest = candidati[0]

        busta = Busta(mittente=self.id, destinatario=dest, tipo="COMANDO",
                      richiedi_ack=True,
                      payload={"azione": azione, "parametri": parametri or {},
                               "casella": casella})
        compito = CompitoPendente(busta, dest)
        self.pendenti[busta.id_messaggio] = compito
        await self.bus.pubblica(CANALE_COMANDI, busta)

        # Attesa ACK 2 s → un reinvio stesso id → ack_mancato
        try:
            await asyncio.wait_for(compito.ack.wait(), timeout=bus_onda.TIMEOUT_ACK)
        except asyncio.TimeoutError:
            log.warning("[%s] ACK mancato da %s, reinvio %s",
                        self.id, dest, busta.id_messaggio[:8])
            compito.reinviato = True
            await self.bus.pubblica(CANALE_COMANDI, busta)  # stesso id: dedup lato agente
            try:
                await asyncio.wait_for(compito.ack.wait(), timeout=bus_onda.TIMEOUT_ACK)
            except asyncio.TimeoutError:
                ev = Busta(mittente=self.id, destinatario="*", tipo="EVENTO",
                           payload={"evento": "ack_mancato",
                                    "dettagli": {"agente": dest,
                                                 "id_messaggio": busta.id_messaggio}})
                await self.bus.pubblica(CANALE_EVENTI, ev)
                await scrivi_audit(self.bus.r, ev, nota="ack mancato dopo reinvio")
                # riassegnazione immediata a un altro candidato, se esiste
                return await self._riassegna(busta, motivo="ack_mancato",
                                             timeout_risposta=timeout_risposta)

        # ACK ricevuto: attendo la RISPOSTA
        try:
            await asyncio.wait_for(compito.risposta_evento.wait(), timeout=timeout_risposta)
            return compito.risposta
        except asyncio.TimeoutError:
            log.error("[%s] risposta mai arrivata per %s (l'offline lo gestisce SENTIN)",
                      self.id, busta.id_messaggio[:8])
            return None
        finally:
            self.pendenti.pop(busta.id_messaggio, None)

    async def _riassegna(self, busta: Busta, motivo: str,
                         timeout_risposta: float = 30.0) -> Busta | None:
        """Stesso id_messaggio: l'idempotenza v1.1.1 protegge dai doppi effetti."""
        vecchio = busta.destinatario
        alternativi = await self.agenti_con_capacita(
            capacita=busta.payload.get("_capacita", ""), escludi={vecchio})
        # se la capacità non è nel payload, ricavo i candidati dall'azione
        if not alternativi:
            alternativi = [a for a in await self.agenti_con_capacita(
                busta.payload.get("azione", "")) if a != vecchio]
        if not alternativi:
            log.error("[%s] riassegnazione impossibile (%s): nessun sostituto", self.id, motivo)
            return None
        nuovo = alternativi[0]
        log.warning("[%s] riassegno %s: %s → %s (%s)",
                    self.id, busta.id_messaggio[:8], vecchio, nuovo, motivo)
        busta.destinatario = nuovo
        compito = CompitoPendente(busta, nuovo)
        self.pendenti[busta.id_messaggio] = compito
        await self.bus.pubblica(CANALE_COMANDI, busta)
        try:
            await asyncio.wait_for(compito.risposta_evento.wait(), timeout=timeout_risposta)
            return compito.risposta
        except asyncio.TimeoutError:
            return None
        finally:
            self.pendenti.pop(busta.id_messaggio, None)

    # ---------- Ricezione: ACK, RISPOSTA, SYNC ----------

    async def _su_risposta(self, canale: str, busta: Busta) -> None:
        if busta.tipo == "ACK" and busta.id_correlazione in self.pendenti:
            self.pendenti[busta.id_correlazione].ack.set()
            return
        if busta.tipo == "RISPOSTA" and busta.id_correlazione in self.pendenti:
            c = self.pendenti[busta.id_correlazione]
            c.risposta = busta
            c.risposta_evento.set()
            return
        if busta.tipo == "SYNC_RICHIESTA":
            compiti = [c.busta.id_messaggio for c in self.pendenti.values()
                       if c.assegnato_a == busta.mittente]
            sync = Busta(mittente=self.id, destinatario=busta.mittente,
                         tipo="SYNC_RISPOSTA", id_correlazione=busta.id_messaggio,
                         payload={"epoca": await self.bus.epoca_corrente(),
                                  "stato_grafo": {}, "compiti_pendenti": compiti})
            await self.bus.pubblica(canale_agente(busta.mittente), sync)

    # ---------- Eventi da SENTIN: la morte di un agente ----------

    async def _su_evento(self, canale: str, busta: Busta) -> None:
        if busta.tipo != "EVENTO":
            return
        if busta.payload.get("evento") == "agente_offline":
            caduto = busta.payload.get("dettagli", {}).get("id")
            orfani = [c for c in self.pendenti.values() if c.assegnato_a == caduto]
            if orfani:
                log.warning("[%s] %s offline: %d compiti orfani da riassegnare",
                            self.id, caduto, len(orfani))
            for c in orfani:
                asyncio.create_task(self._riassegna(c.busta, motivo="agente_offline"))

    # ---------- Autorità sull'epoca (Rito 3) ----------

    async def cambia_epoca(self) -> int:
        epoca = await self.bus.nuova_epoca()
        ev = Busta(mittente=self.id, destinatario="*", tipo="EVENTO",
                   payload={"evento": "nuova_epoca", "dettagli": {"epoca": epoca}})
        await self.bus.pubblica(CANALE_EVENTI, ev)
        await scrivi_audit(self.bus.r, ev, nota="cambio epoca")
        log.info("[%s] epoca %d dichiarata", self.id, epoca)
        return epoca

    async def esegui_comando(self, busta: Busta):
        raise ValueError("RAFFA orchestra, non esegue")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
    asyncio.run(Raffa().avvia())
