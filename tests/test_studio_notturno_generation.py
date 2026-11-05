"""Deterministic provider fixtures, with no credentials or network use."""

import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/studio_notturno.py'
SPEC = importlib.util.spec_from_file_location('studio_notturno_under_test', SCRIPT)
STUDIO = importlib.util.module_from_spec(SPEC)
with patch.dict(sys.modules, {'anthropic': SimpleNamespace(Anthropic=object)}):
    SPEC.loader.exec_module(STUDIO)


def text_block(text):
    return SimpleNamespace(type='text', text=text)


class StudioGenerationTests(unittest.TestCase):
    def client(self, responses):
        return SimpleNamespace(messages=SimpleNamespace(create=Mock(side_effect=responses)))

    def test_empty_response_is_rejected(self):
        client = self.client([SimpleNamespace(content=[])])
        with self.assertRaisesRegex(RuntimeError, 'vuota'):
            STUDIO.genera_brief(STUDIO.TEMI[0], client)

    def test_whitespace_response_is_rejected(self):
        client = self.client([SimpleNamespace(content=[text_block(' \n')])])
        with self.assertRaisesRegex(RuntimeError, 'vuota'):
            STUDIO.genera_brief(STUDIO.TEMI[0], client)

    def test_tool_available_but_unused_is_not_web_research(self):
        client = self.client([SimpleNamespace(content=[text_block('Fixture synthesis')])])
        result = STUDIO.genera_brief(STUDIO.TEMI[0], client)
        self.assertTrue(result.startswith('**Stato fonti: nessun risultato web'))

    def test_fallback_is_explicitly_labeled(self):
        client = self.client([RuntimeError('fixture tool failure'), SimpleNamespace(content=[text_block('Fixture synthesis')])])
        result = STUDIO.genera_brief(STUDIO.TEMI[0], client)
        self.assertIn('non e una ricerca aggiornata verificata', result)
        self.assertEqual(client.messages.create.call_count, 2)
        fallback = client.messages.create.call_args.kwargs
        self.assertNotIn('tools', fallback)
        self.assertIn('Non dichiarare ricerca aggiornata', fallback['messages'][0]['content'])

    def test_actual_results_are_counted_without_claiming_verified_truth(self):
        web = SimpleNamespace(type='web_search_tool_result', content=[SimpleNamespace(type='web_search_result'), {'type': 'web_search_result'}])
        client = self.client([SimpleNamespace(content=[web, text_block('Fixture synthesis')])])
        result = STUDIO.genera_brief(STUDIO.TEMI[0], client)
        self.assertIn('2 risultati restituiti', result)
        self.assertIn('restano da verificare', result)

    def test_web_error_is_not_a_source(self):
        web = SimpleNamespace(type='web_search_tool_result', content=SimpleNamespace(type='web_search_tool_result_error'))
        client = self.client([SimpleNamespace(content=[web, text_block('Fixture synthesis')])])
        self.assertIn('nessun risultato web', STUDIO.genera_brief(STUDIO.TEMI[0], client))

    def test_double_api_failure_propagates(self):
        client = self.client([RuntimeError('fixture first'), RuntimeError('fixture second')])
        with self.assertRaisesRegex(RuntimeError, 'fixture second'):
            STUDIO.genera_brief(STUDIO.TEMI[0], client)

    def test_failed_parallel_section_does_not_return_a_brief(self):
        with patch.object(STUDIO, 'genera_brief', side_effect=RuntimeError('empty section')):
            with self.assertRaisesRegex(RuntimeError, 'empty section'):
                STUDIO.genera_brief_parallelo(None)


if __name__ == '__main__':
    unittest.main()
