"""Un solo Raffaello: ogni prompt che lo nomina parte dalla stessa identità."""
import ast
import pathlib
import unittest

import fabbrica
import fabbrica_dialogue
import raffaello_identita as ident

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCES = ['fabbrica.py', 'fabbrica_dialogue.py', 'api/raffaello.py', 'api/tarot_alpha.py',
           'api/tarot_raffaello.py', 'tarocchi_web.py', 'sdq1/notifiche.py', 'lgai_core/raffaello.py']


class Identita(unittest.TestCase):
    def test_role_follows_shared_identity(self):
        for prompt in (fabbrica.SYSTEM, fabbrica_dialogue.HELP_SYSTEM):
            self.assertTrue(prompt.startswith(ident.IDENTITA))
            self.assertIn('IL TUO RUOLO QUI:', prompt)

    def test_every_raffaello_prompt_is_wrapped(self):
        """Every literal opening with 'Sei Raffaello' flows through con_identita."""
        for rel in SOURCES:
            tree = ast.parse((ROOT / rel).read_text(encoding='utf-8'))
            inside, names = set(), set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and getattr(node.func, 'id', '') == 'con_identita':
                    for arg in node.args:
                        inside.update(id(n) for n in ast.walk(arg))
                        if isinstance(arg, ast.Name):
                            names.add(arg.id)
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
                        and node.targets[0].id in names:
                    inside.update(id(n) for n in ast.walk(node.value))
            found = [n for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)
                     and n.value.lstrip().startswith('Sei Raffaello')]
            self.assertTrue(found, rel)
            for node in found:
                with self.subTest(file=rel, line=node.lineno):
                    self.assertIn(id(node), inside)

    def test_identity_names_origin_and_protocol(self):
        self.assertIn('Claudio Terzi', ident.IDENTITA)
        self.assertIn('Rosso Rosso Rosso', ident.IDENTITA)


if __name__ == '__main__':
    unittest.main()
