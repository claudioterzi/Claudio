"""Il router SDQ-1 trova un modello alternativo quando uno esaurisce i token."""

import time
import unittest
from unittest.mock import patch

from sdq1.llm import router as router_mod
from sdq1.llm.providers.base import ProviderBase
from sdq1.llm.router import LLMRouter, RegolaRouter


def _finto(nome: str, *, errore: str | None = None, stop: str = "end_turn",
           disponibile: bool = True):
    """Provider finto che fallisce con `errore` o risponde con stop reason `stop`."""

    class Finto(ProviderBase):
        chiamate = 0

        def _inizializza(self) -> bool:
            return disponibile

        def _completa_impl(self, sistema, utente):
            type(self).chiamate += 1
            if errore:
                raise RuntimeError(errore)
            return f"risposta completa di {nome}, abbastanza lunga da non sembrare debole", {
                "stop_reason": stop,
            }

    Finto.nome = nome
    return Finto


class TestRouterFallback(unittest.TestCase):
    def _router(self, registry, cascata, **opts):
        self._patch = patch.dict(router_mod.PROVIDER_REGISTRY, registry, clear=True)
        self._patch.start()
        self.addCleanup(self._patch.stop)
        return LLMRouter(opts_globali=opts, regole=[RegolaRouter("default", cascata)])

    def test_quota_esaurita_passa_al_successivo_e_pausa_lunga(self):
        r = self._router({
            "a": (_finto("a", errore="Error code: 400 - credit balance is too low"), "m-a"),
            "b": (_finto("b"), "m-b"),
            "stub": router_mod.PROVIDER_REGISTRY["stub"],
        }, ["a", "b", "stub"])
        esito = r.chiama("sys", "ciao", cache=False)
        self.assertEqual(esito.risposta.provider, "b")
        self.assertEqual(esito.provider_usati, ["a", "b"])
        # Crediti finiti: il circuito resta aperto ~30 min, non 60 s.
        self.assertGreater(r.stato_circuit_breaker()["a"]["ripristino_tra_s"], 1000)

    def test_cascata_esaurita_usa_provider_fuori_profilo(self):
        r = self._router({
            "a": (_finto("a", errore="429 rate limit"), "m-a"),
            "fuori": (_finto("fuori"), "m-fuori"),
            "spento": (_finto("spento", disponibile=False), "m-spento"),
            "stub": router_mod.PROVIDER_REGISTRY["stub"],
        }, ["a", "stub"])
        esito = r.chiama("sys", "ciao", cache=False)
        self.assertEqual(esito.risposta.provider, "fuori")
        self.assertEqual(esito.risposta.modello, "m-fuori")
        self.assertTrue(esito.risposta.metadata["fallback_globale"])
        self.assertNotIn("stub", esito.provider_usati)
        self.assertNotIn("spento", esito.provider_usati)

    def test_fallback_globale_disattivabile(self):
        r = self._router({
            "a": (_finto("a", errore="insufficient_quota"), "m-a"),
            "fuori": (_finto("fuori"), "m-fuori"),
            "stub": router_mod.PROVIDER_REGISTRY["stub"],
        }, ["a", "stub"], fallback_globale=False)
        esito = r.chiama("sys", "ciao", cache=False)
        self.assertEqual(esito.provider_usati, ["a", "stub"])

    def test_output_troncato_cerca_modello_che_completa(self):
        r = self._router({
            "a": (_finto("a", stop="max_tokens"), "m-a"),
            "b": (_finto("b", stop="stop"), "m-b"),
            "stub": router_mod.PROVIDER_REGISTRY["stub"],
        }, ["a", "b", "stub"])
        esito = r.chiama("sys", "ciao", cache=False)
        self.assertEqual(esito.risposta.provider, "b")

    def test_se_tutti_troncano_meglio_troncata_che_stub(self):
        r = self._router({
            "a": (_finto("a", stop="max_tokens"), "m-a"),
            "b": (_finto("b", stop="length"), "m-b"),
            "stub": router_mod.PROVIDER_REGISTRY["stub"],
        }, ["a", "b", "stub"])
        esito = r.chiama("sys", "ciao", cache=False)
        self.assertEqual(esito.risposta.provider, "a")
        self.assertTrue(esito.risposta.metadata["troncata"])

    def test_contesto_superato_prova_altro_modello_senza_pausa(self):
        r = self._router({
            "a": (_finto("a", errore="prompt is too long: 250000 tokens > 200000 maximum"), "m-a"),
            "b": (_finto("b"), "m-b"),
            "stub": router_mod.PROVIDER_REGISTRY["stub"],
        }, ["a", "b", "stub"])
        esito = r.chiama("sys", "ciao", cache=False)
        self.assertEqual(esito.risposta.provider, "b")
        # Dipende dal prompt, non dall'account: niente circuit breaker.
        self.assertNotIn("a", r.stato_circuit_breaker())

    def test_hedging_esaurito_ripiega_subito_su_alternativa(self):
        r = self._router({
            "a": (_finto("a", errore="insufficient_quota"), "m-a"),
            "b": (_finto("b", errore="429 too many requests"), "m-b"),
            "fuori": (_finto("fuori"), "m-fuori"),
            "stub": router_mod.PROVIDER_REGISTRY["stub"],
        }, ["a", "b", "stub"])
        r.HEDGE_WAIT_S = 0.05
        inizio = time.monotonic()
        esito = r.chiama("sys", "ciao", hedging=True, cache=False)
        self.assertEqual(esito.risposta.provider, "fuori")
        self.assertTrue(esito.hedged)
        # Entrambi falliscono in millisecondi: niente attesa del timeout di profilo (45 s).
        self.assertLess(time.monotonic() - inizio, 5)

    def test_tutto_esaurito_finisce_sullo_stub(self):
        r = self._router({
            "a": (_finto("a", errore="resource_exhausted"), "m-a"),
            "stub": router_mod.PROVIDER_REGISTRY["stub"],
        }, ["a", "stub"])
        esito = r.chiama("sys", "ciao", cache=False)
        self.assertEqual(esito.provider_usati, ["a", "stub"])


if __name__ == "__main__":
    unittest.main()
