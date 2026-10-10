"""Real CLI/Telegram consumer entrypoints with all network effects mocked."""
from __future__ import annotations

import copy
import io
import json
import tempfile
import unittest
from contextlib import ExitStack, redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock, patch

from sdq1 import snapshot
from sdq1 import __main__ as cli
from sdq1 import notifiche


class SnapshotConsumers(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='r3-consumers-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = {
            'meta': {'data_ora': '2026-10-10 12:00:00', 'versione': '1.1.0'},
            'git': {'commit_short': 'fixture', 'branch': 'fixture', 'dirty': False},
            'codice': {'file_presenti': 0, 'file': {}, 'file_mancanti': []},
            'agenti': {'ok': True}, 'scanner': {}, 'output': {},
        }
        self.before = copy.deepcopy(self.source)
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(snapshot, '_SNAPSHOT_DIR', self.root))
        self.stack.enter_context(patch.object(snapshot, 'crea_snapshot', return_value=self.source))
        self.push = self.stack.enter_context(patch.object(snapshot, 'push_snapshot'))
        self.stack.enter_context(patch.object(cli, 'costruisci_sistema', return_value=tuple(MagicMock() for _ in range(7))))
        self.stack.enter_context(patch.object(cli.threading, 'Thread'))
        self.send = self.stack.enter_context(patch.object(notifiche, 'invia'))
        self.stack.enter_context(patch.object(notifiche, 'notifica_progresso'))
        self.finish = self.stack.enter_context(patch.object(notifiche, 'notifica_completato'))
        self.network = self.stack.enter_context(patch.object(notifiche.urllib.request, 'urlopen', side_effect=AssertionError('Network forbidden in consumer tests')))

    def saved(self):
        files = list(self.root.glob('snapshot_*.json'))
        self.assertEqual(len(files), 1)
        data = json.loads(files[0].read_bytes())
        self.assertEqual(data['meta']['data_ora'], self.before['meta']['data_ora'])
        self.assertIn('snapshot_id', data['meta'])
        self.assertEqual(self.source, self.before)
        self.network.assert_not_called()
        return files[0]

    def call_cli(self, *args):
        out = io.StringIO()
        with redirect_stdout(out):
            code = cli.main(['sdq1', *args])
        return code, out.getvalue()

    def test_cli_save_preserves_returned_path_contract(self):
        code, text = self.call_cli('--snapshot')
        self.assertEqual(code, 0)
        self.assertIn(str(self.saved()), text)
        self.push.assert_not_called()

    def test_cli_verified_push_returns_zero(self):
        self.push.return_value = True
        code, text = self.call_cli('--snapshot', '--push')
        self.assertEqual(code, 0)
        self.assertIn('Push GitHub: VERIFICATO', text)
        self.push.assert_called_once_with(self.saved())

    def test_cli_unverified_push_returns_failure(self):
        self.push.return_value = False
        code, text = self.call_cli('--snapshot', '--push')
        self.push.assert_called_once_with(self.saved())
        self.assertEqual(code, 1)
        self.assertIn('Push GitHub: NON VERIFICATO', text)

    def test_telegram_save_uses_actual_returned_filename(self):
        with redirect_stdout(io.StringIO()):
            notifiche._esegui_singolo_comando('snapshot')
        self.send.assert_called_once()
        self.assertIn(self.saved().name, self.send.call_args.args[0])
        self.push.assert_not_called()

    def test_telegram_verified_push_is_explicit(self):
        self.push.return_value = True
        with redirect_stdout(io.StringIO()):
            notifiche._esegui_singolo_comando('push')
        self.finish.assert_called_once()
        self.assertEqual(self.finish.call_args.args[0], 'Push verificato')
        self.push.assert_called_once_with(self.saved())

    def test_telegram_unverified_push_is_not_reported_as_completed(self):
        self.push.return_value = False
        with redirect_stdout(io.StringIO()):
            notifiche._esegui_singolo_comando('push')
        self.finish.assert_called_once()
        self.assertEqual(self.finish.call_args.args[0], 'Push non verificato')
        self.assertIn('NON VERIFICATO', '\n'.join(self.finish.call_args.args[1]))
        self.push.assert_called_once_with(self.saved())


if __name__ == '__main__':
    unittest.main(verbosity=2)
