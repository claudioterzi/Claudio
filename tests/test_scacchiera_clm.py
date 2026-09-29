import os
import unittest
from unittest.mock import patch

from sdq1.sar.scacchiera_clm import ScacchieraCLM


def _rank_ultimo(context, question, answers, **kwargs):
    # Finto CLM: preferisce sempre l'ultimo candidato.
    return {
        "model": "clm-test",
        "_r3_provider": "clm",
        "ranked": [
            {"rank": i + 1, "candidate": a, "prob": round(1 / (i + 1), 3)}
            for i, a in enumerate(reversed(answers))
        ],
    }


class TestScacchieraCLM(unittest.TestCase):
    def test_clm_rank_decide_la_scelta(self):
        sc = ScacchieraCLM(rank_fn=_rank_ultimo)
        percorso = sc.ciclo(max_livelli=4)
        self.assertEqual(len(percorso), 5)
        for nodo in percorso[1:]:
            self.assertEqual(nodo.selezione, "clm_rank")
            self.assertEqual(nodo.provenienza_selezione, "clm")
        stats = sc.statistiche_selezione()
        self.assertEqual(stats["clm_rank"], 4)
        self.assertEqual(stats["fallback_casuale"], 0)

    def test_senza_clm_fallback_dichiarato(self):
        with patch.dict(os.environ, {}, clear=True):
            sc = ScacchieraCLM()
            percorso = sc.ciclo(max_livelli=3)
        for nodo in percorso[1:]:
            self.assertEqual(nodo.selezione, "fallback_casuale")
        self.assertEqual(sc.statistiche_selezione()["clm_rank"], 0)

    def test_rank_su_jev_non_emulato(self):
        env = {"TYPESAFE_API_KEY": "k"}
        with patch.dict(os.environ, env, clear=True):
            sc = ScacchieraCLM()
            percorso = sc.ciclo(max_livelli=2)
        for nodo in percorso[1:]:
            self.assertEqual(nodo.selezione, "fallback_casuale")
            self.assertEqual(nodo.provenienza_selezione, "SystemOneCapabilityUnavailable")

    def test_risposta_invalida_fallback(self):
        sc = ScacchieraCLM(rank_fn=lambda *a, **k: {"ranked": [{"rank": 1, "candidate": "inesistente"}]})
        percorso = sc.ciclo(max_livelli=2)
        self.assertTrue(all(n.selezione == "fallback_casuale" for n in percorso[1:]))


if __name__ == "__main__":
    unittest.main()
