"""Deterministic provider fixtures, with no credentials or network use."""

import importlib.util
from pathlib import Path
import sys
import tempfile
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

    def test_no_key_uses_public_api_before_saving(self):
        source = Mock(return_value='documented brief')
        with patch.dict(STUDIO.os.environ, {'ANTHROPIC_API_KEY': ''}), \
             patch.dict(sys.modules, {'studio_fonti': SimpleNamespace(genera_brief_fonti=source)}), \
             patch.object(STUDIO, 'salva') as save:
            STUDIO.main()
        selezioni = STUDIO._priorita().seleziona_temi(STUDIO.TEMI)
        source.assert_called_once_with(STUDIO.TEMI, STUDIO.datetime.date.today(),
                                       indici=[s['indice'] for s in selezioni])
        save.assert_called_once()
        self.assertIn('Perché questi temi', save.call_args.args[0])
        self.assertTrue(save.call_args.args[0].endswith('documented brief'))
        self.assertEqual(save.call_args.args[1], STUDIO.get_tema())

    def test_index_replaces_stale_rotation_and_preserves_old_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / 'output/morning_brief'
            folder.mkdir(parents=True)
            old_link = '- [Old brief](./2026-06-20.md)'
            (folder / 'INDICE.md').write_text('# Index\n## Piano di Rotazione\n| Domenica | Wildcard Creativo |\n' + old_link + '\n')
            with patch.object(STUDIO, '__file__', str(Path(tmp) / 'scripts/studio_notturno.py')):
                STUDIO.salva('new brief', STUDIO.TEMI[1])
            index = (folder / 'INDICE.md').read_text()
            self.assertIn(old_link, index)
            self.assertIn('Fino a tre temi già lavorati', index)
            self.assertNotIn('Piano di Rotazione', index)
            self.assertNotIn('Domenica', index)
            self.assertNotIn('Wildcard Creativo', index)

    def test_repeated_run_links_the_day_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(STUDIO, '__file__', str(Path(tmp) / 'scripts' / 'studio_notturno.py')):
                STUDIO.salva('first', STUDIO.TEMI[0])
                brief = STUDIO.salva('second', STUDIO.TEMI[0])
            self.assertEqual(brief.read_text(), 'second')
            self.assertEqual((brief.parent / 'INDICE.md').read_text().count(f'](./{brief.name})'), 1)


if __name__ == '__main__':
    unittest.main()
