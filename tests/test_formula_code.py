import json
import unittest
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
