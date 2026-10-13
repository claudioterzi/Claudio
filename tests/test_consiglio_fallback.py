"""Il Consiglio delibera anche se il modello di un membro manca o ha finito i token."""

import unittest
from unittest.mock import patch

from sdq1.consiglio import ConsiglioAgenti
from sdq1.llm import router as router_mod
from sdq1.llm.providers.base import ProviderBase


def _finto(nome, *, disponibile=True, errore=None):
    class Finto(ProviderBase):
        def _inizializza(self):
            return disponibile

        def _completa_impl(self, sistema, utente):
            if errore:
                raise RuntimeError(errore)
            return f"Raccomandazione: procedi con {nome}\nMotivazione: prova\nConfidenza: 80", {}

    Finto.nome = nome
    return Finto


class TestConsiglioFallback(unittest.TestCase):
    def test_import_dei_provider_non_rompe_piu(self):
        from sdq1.llm.providers import MistralProvider  # noqa: F401
        self.assertIn("mistral", router_mod.PROVIDER_REGISTRY)

    def test_membri_senza_chiave_votano_con_un_alternativo(self):
        registro = {
            "gemini": (_finto("gemini", disponibile=False), "g"),
            "anthropic": (_finto("anthropic", errore="credit balance is too low"), "a"),
            "deepseek": (_finto("deepseek", disponibile=False), "d"),
            "mistral": (_finto("mistral", disponibile=False), "m"),
            "openai": (_finto("openai"), "o-mini"),
            "stub": router_mod.PROVIDER_REGISTRY["stub"],
        }
        with patch.dict(router_mod.PROVIDER_REGISTRY, registro, clear=True):
            delibera = ConsiglioAgenti(salva_output=False).delibera("Prova")
        self.assertEqual(len(delibera.voti), 5)
        for voto in delibera.voti:
            self.assertEqual(voto.modello, "openai/o-mini")
            self.assertIn("procedi con openai", voto.raccomandazione)

    def test_nessun_modello_disponibile_lo_dice_chiaro(self):
        registro = {
            "gemini": (_finto("gemini", disponibile=False), "g"),
            "stub": router_mod.PROVIDER_REGISTRY["stub"],
        }
        with patch.dict(router_mod.PROVIDER_REGISTRY, registro, clear=True):
            delibera = ConsiglioAgenti(salva_output=False).delibera("Prova")
        self.assertTrue(all(v.raccomandazione == "Nessun modello ha risposto." for v in delibera.voti))

    def test_disco_in_sola_lettura_non_ferma_la_delibera(self):
        from pathlib import Path
        registro = {
            "openai": (_finto("openai"), "o-mini"),
            "stub": router_mod.PROVIDER_REGISTRY["stub"],
        }
        c = ConsiglioAgenti(salva_output=True)
        c._output_dir = Path("/proc/sola-lettura/consiglio")  # come /var/task su Vercel
        with patch.dict(router_mod.PROVIDER_REGISTRY, registro, clear=True):
            delibera = c.delibera("Prova")
        self.assertEqual(len(delibera.voti), 5)


if __name__ == "__main__":
    unittest.main()
