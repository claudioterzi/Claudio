"""Fixture deterministiche per il percorso senza chiave."""

import datetime
import unittest
from unittest.mock import patch

from scripts import studio_fonti as studio


OGGI = datetime.date(2026, 11, 6)  # venerdì
TEMI = {i: {"nome": f"Nome riservato {i}"} for i in range(7)}


def articolo(titolo, doi, data=(2025, 7)):
    return {"title": [titolo], "DOI": doi, "published": {"date-parts": [list(data)]}}


def progetto(**modifiche):
    dati = {"code": "101123456", "id": "corda_____he::fixture", "title": "Digital Identity Mission",
            "startDate": "2025-09-01", "fundings": [{"shortName": "EC"}]}
    return {**dati, **modifiche}


def risposta(url, parametri):
    if "openaire" in url:
        return {"results": [progetto()]}
    query = parametri["query.title"]
    return {"message": {"items": [articolo(query, "10.1234/" + query.replace(" ", "-"))]}}


class StudioFontiTests(unittest.TestCase):
    def test_tutti_i_temi_lavorati_e_query_pubbliche(self):
        for indici in ([1, 4, 0], [2, 3, 5]):
            with self.subTest(indici=indici), patch.object(studio, "_json", side_effect=risposta) as api:
                testo = studio.genera_brief_fonti(TEMI, OGGI, indici=indici)
                self.assertEqual(testo.count("\n## "), 3)
                self.assertEqual(testo.count("[DOI]("), 3)
                for indice in indici:
                    self.assertIn(TEMI[indice]["nome"], testo)
                self.assertNotIn(TEMI[6]["nome"], testo)
                self.assertEqual(testo.count("**Indicazione di lettura.**"), 3)
                self.assertNotIn("riservato", str(api.call_args_list))
                self.assertEqual("CORDIS 101123456" in testo, 4 in indici)
                self.assertIn("Non è una revisione completa", testo)

    def test_rifiuta_wildcard_duplicati_e_selezione_vuota(self):
        for indici in ([6], [], [0, 0], [0, 1, 2, 3], [-1], [False]):
            with self.subTest(indici=indici), patch.object(studio, "_json") as api:
                with self.assertRaises(ValueError):
                    studio.genera_brief_fonti(TEMI, OGGI, indici=indici)
                api.assert_not_called()

    def test_articoli_validi_unici_date_parziali_e_titoli_sicuri(self):
        valido = articolo("Digital legacy [analyses]", "10.1234/AB(1)")
        record = [
            articolo("Altro argomento", "10.1234/altro"),
            articolo("Digital legacy", "url-errato"),
            articolo("Digital legacy", "10.1234/vecchio", (2020,)),
            articolo("Digital legacy", "10.1234/futuro", (2026, 12)),
            articolo("Digital legacy", "10.1234/errore", (2026, 2, 31)),
            articolo("Digital legacy", "10.1234/usato"),
            valido, valido, articolo("Digital legacy II", "10.1234/b", (2025,)),
        ]
        with patch.object(studio, "_json", return_value={"message": {"items": record}}):
            righe = studio._articoli(studio.PISTE[5], OGGI - datetime.timedelta(days=730), OGGI, {"10.1234/usato"})
        self.assertEqual(len(righe), 2)
        self.assertIn(r"Digital legacy \[analyses\] · 2025-07", righe[0])
        self.assertIn("https://doi.org/10.1234/ab%281%29", righe[0])
        self.assertIn(" · 2025 · ", righe[1])

    def test_scudo_esclude_scheduling_computazionale_senza_immagini(self):
        record = [articolo("Satellite task scheduling in edge computing", "10.1234/a"),
                  articolo("Satellite image acquisition scheduling", "10.1234/b")]
        with patch.object(studio, "_json", return_value={"message": {"items": record}}):
            righe = studio._articoli(studio.PISTE[1], OGGI - datetime.timedelta(days=730), OGGI, set())
        self.assertEqual(len(righe), 1)
        self.assertIn('10.1234/b', righe[0])

    def test_stesso_titolo_con_doi_diversi_non_diventa_due_articoli(self):
        record = [articolo("Digital legacy", "10.1234/a"), articolo("Digital legacy", "10.1234/b")]
        with patch.object(studio, "_json", return_value={"message": {"items": record}}):
            righe = studio._articoli(studio.PISTE[5], OGGI - datetime.timedelta(days=730), OGGI, set())
        self.assertEqual(len(righe), 1)

    def test_progetto_richiede_fonte_cordis_fondo_ec_data_e_titolo_pertinente(self):
        record = [
            progetto(id="altro::record"), progetto(fundings=[{"shortName": "NSF"}]),
            progetto(startDate="2027-01-01"), progetto(title="Altro oggetto"),
            progetto(code="non-numerico"), progetto(), progetto(),
        ]
        with patch.object(studio, "_json", return_value={"results": record}):
            righe = studio._progetti_ue(OGGI - datetime.timedelta(days=730), OGGI)
        self.assertEqual(len(righe), 1)
        self.assertIn("avvio 2025-09-01", righe[0])

    def test_mancata_copertura_blocca_il_brief(self):
        for mancante in ("Crossref", "OpenAIRE"):
            def incompleta(url, parametri):
                if mancante == "OpenAIRE" and "openaire" in url:
                    return {"results": []}
                if mancante == "Crossref" and parametri.get("query.title") == studio.PISTE[1][0]:
                    return {"message": {"items": []}}
                return risposta(url, parametri)

            with self.subTest(mancante=mancante), patch.object(studio, "_json", side_effect=incompleta):
                with self.assertRaisesRegex(RuntimeError, mancante):
                    studio.genera_brief_fonti(TEMI, OGGI, indici=[1, 4, 0])


if __name__ == "__main__":
    unittest.main()
