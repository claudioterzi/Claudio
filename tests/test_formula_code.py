import json
import unittest
from unittest.mock import patch
from pathlib import Path
from studio.parfums.formula_code import ROOT,encode,decode

class FormulaCodeTests(unittest.TestCase):
 def test_all_400_roundtrip(self):
  ps=json.loads((ROOT/'studio/parfums/parfums_400.json').read_text())['parfums']
  self.assertEqual(len(ps),400)
  for p in ps:
   self.assertEqual(decode(encode(p['ricetta'])),[{k:r[k] for k in ('n','nome','parti','livello','micro')} for r in p['ricetta']])
 def test_typo_rejected(self):
  ps=json.loads((ROOT/'studio/parfums/parfums_400.json').read_text())['parfums']
  code=encode(ps[0]['ricetta'])
  with self.assertRaises(ValueError):decode(code.replace(':90:',':91:',1))
 def test_current_revision_decodes_without_static_directory_in_function(self):
  ps=json.loads((ROOT/'studio/parfums/parfums_400.json').read_text())['parfums']
  code=encode(ps[0]['ricetta'])
  read=Path.read_bytes
  def runtime_read(path):
   if 'public/formule' in str(path):raise FileNotFoundError('Static assets are served by the CDN')
   return read(path)
  with patch.object(Path,'read_bytes',runtime_read):
   self.assertEqual(len(decode(code)),len(ps[0]['ricetta']))
 def test_old_revision_still_uses_immutable_snapshot(self):
  ps=json.loads((ROOT/'studio/parfums/parfums_400.json').read_text())['parfums']
  code=encode(ps[0]['ricetta'])
  with patch('studio.parfums.formula_code.catalog_bytes',return_value=b'{"materie":[]}'):
   self.assertEqual(len(decode(code)),len(ps[0]['ricetta']))
