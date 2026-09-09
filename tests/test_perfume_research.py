import json
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import tarocchi_web as w
from perfume_research import reference_from,research_reference,resolve_references

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
 def test_pasted_credentials_work_for_both_research_and_composer(self):
  from sdq1.llm.providers import GeminiProvider
  body=json.dumps({'candidates':[{'content':{'parts':[{'text':'Test'}]}}]}).encode()
  with patch.dict('os.environ',{'GOOGLE_API_KEY':' test-only\n'},clear=True),patch('urllib.request.urlopen') as net:
   net.return_value.__enter__.return_value.read.return_value=body
   research_reference('Chanel N° 5')
   self.assertEqual(net.call_args.args[0].get_header('X-goog-api-key'),'test-only')
   self.assertNotIn('key=',net.call_args.args[0].full_url)
   provider=GeminiProvider(modello='gemini-2.5-flash',api_key=None,max_retries=0)
   self.assertTrue(provider.disponibile)
   provider._completa_impl('Sistema','Intenzione')
   self.assertEqual(net.call_args.args[0].get_header('X-goog-api-key'),'test-only')
   self.assertNotIn('key=',net.call_args.args[0].full_url)
 def test_reference_passed_from_page(self):
  with patch('tarocchi_web._atelier_componi_ai',return_value=(None,'test')) as compose:
   with w.app.test_client() as client:
    client.post('/profumo',data={'q':'un omaggio','stile':'ellena','riferimento':'Chanel N° 5 EDP'})
   self.assertEqual(compose.call_args.kwargs['stile'],'ellena')
   self.assertEqual(compose.call_args.kwargs['riferimento'],'Chanel N° 5 EDP')

class PreferenceTests(unittest.TestCase):
 def response(self, items):
  return json.dumps({'candidates':[{'content':{'parts':[{'text':json.dumps({'items':items})}]}}]}).encode()
 def test_explicit_list_deduplicated_without_provider(self):
  with patch('urllib.request.urlopen') as net:
   r=resolve_references('Un ricordo','Chanel N° 5\nDior J’adore;Chanel N° 5')
   self.assertEqual([x['name'] for x in r['items']],['Chanel N° 5','Dior J’adore'])
   self.assertEqual(r['origin'],'field');net.assert_not_called()
 def test_explicit_limits_not_silently_truncated(self):
  for value in (';'.join(str(i) for i in range(6)), 'a'*181):
   with self.assertRaises(ValueError):resolve_references('x',value)
 def test_context_positive_and_negative_kept_separate(self):
  intention='Adoro Chanel N° 5 ma non amo Dior Sauvage; desidero più freschezza.'
  items=[dict(name='Chanel N° 5',evidence='Adoro Chanel N° 5',relation='preferito',clarification=''),
         dict(name='Dior Sauvage',evidence='non amo Dior Sauvage',relation='evitare',clarification='Quale versione?')]
  with patch.dict('os.environ',{'GOOGLE_API_KEY':'test'}),patch('urllib.request.urlopen') as net:
   net.return_value.__enter__.return_value.read.return_value=self.response(items)
   r=resolve_references(intention)
   self.assertEqual(r['status'],'recognized');self.assertEqual(r['items'],items)
   self.assertNotIn('tools',json.loads(net.call_args.args[0].data))
   self.assertEqual(net.call_args.kwargs['timeout'],6)
 def test_no_mention_is_not_a_reference(self):
  with patch.dict('os.environ',{'GOOGLE_API_KEY':'test'}),patch('urllib.request.urlopen') as net:
   net.return_value.__enter__.return_value.read.return_value=self.response([])
   self.assertEqual(resolve_references('come un giardino di rose')['items'],[])
   self.assertEqual(reference_from('come un giardino di rose'),'')
 def test_invented_name_rejected_and_failure_does_not_block(self):
  with patch.dict('os.environ',{'GOOGLE_API_KEY':'test'}),patch('urllib.request.urlopen') as net:
   net.return_value.__enter__.return_value.read.return_value=self.response([
    dict(name='Chanel N° 5',evidence='Un giardino',relation='preferito',clarification='')])
   r=resolve_references('Un giardino');self.assertEqual(r['items'],[]);self.assertEqual(r['status'],'unavailable')
   net.side_effect=TimeoutError()
   self.assertEqual(resolve_references('Un giardino')['status'],'unavailable')
 def test_multiple_references_reach_composition_and_result(self):
  prop=dict(nome='Essai',famiglia='Floreale',testa=[2,4],cuore=[21,40],fondo=[36,7],scia=[32,38],
            overdose=21,concept='Luce',ragionamento='Materie selezionate',riferimento='Non verificato',
            gusti_cliente='Preferenze dichiarate, interpretazione prudente.')
  calls=[]
  class Fake:
   disponibile=True
   def __init__(self,**kw):pass
   def completa(self,s,u):calls.append((s,u));return SimpleNamespace(testo=json.dumps(prop))
  with patch('sdq1.llm.providers.GeminiProvider',Fake),patch('perfume_research.research_reference',return_value={'status':'unavailable','reference':'Chanel N° 5\nDior J’adore'}) as research:
   p,err=w._atelier_componi_ai('Più fresco',stile='ellena',riferimento='Chanel N° 5\nDior J’adore')
   self.assertIsNone(err);research.assert_called_once_with('Chanel N° 5\nDior J’adore')
   self.assertIn('Dior J’adore',calls[0][1]);self.assertIn('non è un modello positivo',calls[0][0])
   self.assertEqual(p['gusti_cliente'],prop['gusti_cliente']);self.assertEqual(len(p['preferenze']['items']),2)
   self.assertIn('flacone',p);self.assertEqual(sum(r[2] for r in p['ricetta']),100)
   with w.app.test_request_context():
    page=w.render_result('Più fresco',p)
    self.assertIn('I gusti, prima della formula',page);self.assertIn('Chanel N° 5',page)
    self.assertIn('non sono verificate',page)
 def test_second_provider_recovers_recognition(self):
  from unittest.mock import MagicMock
  item=dict(name='Chanel N° 5',evidence='Adoro Chanel N° 5',relation='preferito',clarification='')
  class Fallback:
   disponibile=True;nome='anthropic'
   def __init__(self,**kw):
    self._client=MagicMock();self._client.with_options.return_value=self._client
   def completa(self,*args):
    self._client.with_options.assert_called_once_with(max_retries=0)
    return SimpleNamespace(testo=json.dumps({'items':[item]}))
  with patch.dict('os.environ',{'GOOGLE_API_KEY':'test','ANTHROPIC_API_KEY':'test'}),patch('urllib.request.urlopen',side_effect=TimeoutError()),patch('sdq1.llm.providers.AnthropicProvider',Fallback):
   r=resolve_references('Adoro Chanel N° 5')
   self.assertEqual(r['status'],'recognized');self.assertEqual(r['provider'],'anthropic')
   self.assertEqual(r['items'],[item])
