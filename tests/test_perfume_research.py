import json
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import tarocchi_web as w
from perfume_research import reference_from,research_reference

class ResearchTests(unittest.TestCase):
 def test_detect_and_explicit(self):
  self.assertEqual(reference_from('ispirato a Chanel N° 5'),'Chanel N° 5')
  self.assertEqual(reference_from('un giardino','Dior Eau de Parfum'),'Dior Eau de Parfum')
  self.assertEqual(reference_from('un giardino'),'')
 def test_no_key_never_claims_sources(self):
  with patch.dict('os.environ',{},clear=True):
   self.assertEqual(research_reference('Chanel')['status'],'unavailable')
 def test_unsubstantiated_response_not_sourced(self):
  raw=json.dumps({'candidates':[{'content':{'parts':[{'text':'Inventato'}]},'groundingMetadata':{}}]}).encode()
  with patch.dict('os.environ',{'GOOGLE_API_KEY':'test'}),patch('urllib.request.urlopen') as net:
   net.return_value.__enter__.return_value.read.return_value=raw
   self.assertEqual(research_reference('Test')['status'],'unavailable')
 def test_constraints_and_full_text(self):
  org=w._carica_organo_atelier()['materie']
  core=[m['n'] for m in org if m['livello']=='CORE' and m['tipo']!='SOL' and m['ruolo_scia']=='-']
  trail=[m['n'] for m in org if m['livello']=='CORE' and m['ruolo_scia']!='-' and m['tipo']!='SOL']
  prop={'nome':'Test','testa':core[:2],'cuore':core[2:4],'fondo':core[4:6],'scia':trail[:2],'ragionamento':'a'*850,'riferimento':'b'*900}
  class Fake:
   disponibile=True
   def __init__(self,**kw):pass
   def completa(self,s,u):return SimpleNamespace(testo=json.dumps(prop))
  with patch('sdq1.llm.providers.GeminiProvider',Fake),patch('perfume_research.research_reference',return_value={'status':'not_requested','reference':''}):
   p,err=w._atelier_componi_ai('Giardino','',0,stile='ellena')
   self.assertIsNone(err);self.assertEqual(len(p['ricetta']),8);self.assertEqual(len(p['ragionamento']),850);self.assertEqual(len(p['riferimento']),900)
   self.assertEqual(sum(r[2] for r in p['ricetta']),100)
   prop['testa'][0]=next(m['n'] for m in org if m['livello']=='MASTER')
   p,err=w._atelier_componi_ai('Giardino','',0,stile='ellena')
   self.assertIsNone(p);self.assertIsNotNone(err)
 def test_grounded_sources_and_safe_scheme(self):
  grounding={'webSearchQueries':['Test perfume'],'groundingSupports':[{'segment':{'text':'Note floreali'},'groundingChunkIndices':[0]}], 'groundingChunks':[{'web':{'uri':'https://example.com/perfume','title':'Source'}},{'web':{'uri':'javascript:alert(1)','title':'Unsafe'}}]}
  raw=json.dumps({'candidates':[{'content':{'parts':[{'text':'Note floreali'}]},'groundingMetadata':grounding}]}).encode()
  with patch.dict('os.environ',{'GOOGLE_API_KEY':'test'}),patch('urllib.request.urlopen') as net:
   net.return_value.__enter__.return_value.read.return_value=raw
   r=research_reference('Test');self.assertEqual(r['status'],'sourced');self.assertEqual(len(r['sources']),1)
   payload=json.loads(net.call_args.args[0].data)
   self.assertEqual(payload['tools'],[{'google_search':{}}])
 def test_reference_passed_from_page(self):
  with patch('tarocchi_web._atelier_componi_ai',return_value=(None,'test')) as compose:
   with w.app.test_client() as client:
    client.post('/profumo',data={'q':'un omaggio','stile':'ellena','riferimento':'Chanel N° 5 EDP'})
   self.assertEqual(compose.call_args.kwargs['stile'],'ellena')
   self.assertEqual(compose.call_args.kwargs['riferimento'],'Chanel N° 5 EDP')
