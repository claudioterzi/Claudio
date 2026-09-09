import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from types import SimpleNamespace
import base64

from tarocchi_web import app
import perfume_studio as studio

FORMULA = {'nome':'Ambre de Minuit','fam':'Orientale','liv':'étude','concept':'Un’ambra luminosa.',
           'ricetta':[['Bergamotto',1,20,'testa',False],['Accordo ambrato',2,80,'fondo',False]]}

class PerfumeStudioTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {'PERFUME_DB_PATH':str(Path(self.temp.name)/'archive.db'),
            'PERFUME_ARCHIVE_SECRET':'x'*40,'PERFUME_ARCHIVE_PASSWORD':'test-only-password'}, clear=True)
        self.env.start(); self.client = app.test_client(); self.creation_id = str(uuid4())
    def tearDown(self):
        self.env.stop(); self.temp.cleanup()
    def test_save_survives_reopen_and_is_immutable(self):
        r = studio.save_record(self.creation_id,'Cliente prova','Ambra',FORMULA)
        self.assertEqual(studio.read_record(r['serial']),r)
        changed = dict(FORMULA,nome='Altro')
        self.assertEqual(studio.save_record(self.creation_id,'Cliente prova','Ambra',changed),r)
        self.assertEqual(len(r['formula_sha256']),64)
        with self.assertRaises(ValueError):studio.save_record(self.creation_id,'Altro cliente','Ambra',FORMULA)
    def test_unique_serials(self):
        a=studio.save_record(str(uuid4()),'A','Ambra',FORMULA)
        b=studio.save_record(str(uuid4()),'A','Ambra',FORMULA)
        self.assertNotEqual(a['serial'],b['serial'])
    def test_post_creates_exact_label_and_replay_reuses_formula(self):
        with patch('tarocchi_web._atelier_componi_ai',return_value=(FORMULA,None)) as compose:
            data=dict(q='Ambra',cliente='Cliente <prova>',creation_id=self.creation_id,ondata='0')
            first=self.client.post('/profumo',data=data)
            second=self.client.post('/profumo',data=data)
            self.assertEqual(first.status_code,200);self.assertEqual(second.status_code,200)
            self.assertIn('Cliente &lt;prova&gt;',first.text)
            self.assertIn(studio.serial_for(self.creation_id),first.text)
            self.assertIn('FORMULA ARCHIVIATA',first.text)
            compose.assert_called_once()
    def test_production_without_storage_never_claims_archived(self):
        with patch.dict(os.environ,{'VERCEL':'1'}),patch('tarocchi_web._atelier_componi_ai',return_value=(FORMULA,None)):
            r=self.client.post('/profumo',data=dict(q='Ambra',cliente='Prova',creation_id=self.creation_id))
            self.assertEqual(r.status_code,200)
            self.assertIn('FORMULA NON ARCHIVIATA',r.text)
            self.assertNotIn(studio.serial_for(self.creation_id),r.text)
    def test_archive_requires_auth_and_lists_saved_record(self):
        r=studio.save_record(self.creation_id,'Cliente riservato','Ambra',FORMULA)
        unauth=self.client.get('/atelier/archivio')
        self.assertNotIn('Cliente riservato',unauth.text)
        self.assertEqual(self.client.post('/atelier/archivio',data={'password':'wrong'}).status_code,401)
        self.assertEqual(self.client.post('/atelier/archivio',data={'password':'test-only-password'}).status_code,302)
        self.assertIn('Cliente riservato',self.client.get('/atelier/archivio').text)
        detail=self.client.get('/atelier/archivio',query_string={'serial':r['serial']})
        self.assertIn(FORMULA['nome'],detail.text)
        self.assertEqual(detail.headers['Cache-Control'],'no-store')
    def test_images_disabled_without_explicit_configuration(self):
        self.assertEqual(self.client.post('/api/profumo/immagine',json={'token':'x'}).status_code,503)
    def test_image_tokens_reject_forgery(self):
        with patch.dict(os.environ,{'OPENAI_API_KEY':'test-not-a-real-key','REDIS_URL':'redis://test','PERFUME_IMAGES_ENABLED':'1'}):
            self.assertEqual(self.client.post('/api/profumo/immagine',json={'token':'forged'}).status_code,403)
    def test_cached_image_does_not_call_provider(self):
        record=studio.save_record(self.creation_id,'Private Client','Private intention',FORMULA)
        cached=b'RIFFxxxxWEBPtest'
        with patch.dict(os.environ,{'OPENAI_API_KEY':'test-not-a-real-key','REDIS_URL':'redis://test','PERFUME_IMAGES_ENABLED':'1'}):
            redis=MagicMock();redis.get.return_value=cached
            token=studio._image_signer().dumps(record['serial'])
            with patch.object(studio,'read_record',return_value=record),patch.object(studio,'_redis',return_value=redis):
                response=self.client.post('/api/profumo/immagine',json={'token':token})
                self.assertEqual(response.status_code,200)
                self.assertEqual(response.data,cached)
                redis.eval.assert_not_called()

    def test_read_missing_image_never_starts_generation(self):
        record=studio.save_record(self.creation_id,'Private Client','Private intention',FORMULA)
        with patch.dict(os.environ,{'OPENAI_API_KEY':'test','REDIS_URL':'redis://test','PERFUME_IMAGES_ENABLED':'1'}):
            redis=MagicMock();redis.get.return_value=None
            token=studio._image_signer().dumps(record['serial'])
            with patch.object(studio,'read_record',return_value=record),patch.object(studio,'_redis',return_value=redis):
                response=self.client.post('/api/profumo/immagine',json={'token':token,'action':'read'})
                self.assertEqual(response.status_code,404);redis.eval.assert_not_called();redis.set.assert_not_called()

    def test_original_generation_is_recipe_bound_private_and_saved_without_expiry(self):
        record=studio.save_record(self.creation_id,'PRIVATE CLIENT','PRIVATE STORY',FORMULA)
        raw=b'RIFFxxxxWEBPtest'
        with patch.dict(os.environ,{'OPENAI_API_KEY':'test','REDIS_URL':'redis://test','PERFUME_IMAGES_ENABLED':'1'}):
            redis=MagicMock();redis.get.return_value=None;redis.eval.return_value=1
            token=studio._image_signer().dumps(record['serial'])
            API=MagicMock()
            with patch.object(studio,'read_record',return_value=record),patch.object(studio,'_redis',return_value=redis),patch.dict('sys.modules',{'openai':SimpleNamespace(OpenAI=API)}):
                api=API.return_value.__enter__.return_value
                api.images.generate.return_value=SimpleNamespace(data=[SimpleNamespace(b64_json=base64.b64encode(raw).decode())],usage=None)
                response=self.client.post('/api/profumo/immagine',json={'token':token})
                self.assertEqual(response.status_code,200);api.images.edit.assert_not_called()
                prompt=api.images.generate.call_args.kwargs['prompt']
                for private in ('PRIVATE CLIENT','PRIVATE STORY',record['serial']):self.assertNotIn(private,prompt)
                self.assertIn('original',prompt);self.assertIn('Claudio Terzi',prompt)
                redis.set.assert_any_call('terzi:image:'+record['serial'],raw)
                metadata=json.loads(redis.set.call_args.args[1]);self.assertEqual(metadata['status'],'complete')
                self.assertEqual(len(metadata['image_sha256']),64)

    def test_visual_changes_with_formula_and_ignores_customer_data(self):
        from perfume_visual import bottle_brief
        a=bottle_brief(FORMULA)
        b=bottle_brief(dict(FORMULA,ricetta=[['Anything',21,100,'cuore',False]]))
        self.assertNotEqual(a['recipe_fingerprint'],b['recipe_fingerprint'])
        self.assertNotEqual(a['accenti'],b['accenti'])
        self.assertEqual(a,bottle_brief(dict(FORMULA,customer='PRIVATE',concept='PRIVATE',nome='PRIVATE')))

    def test_dedication_and_print_controls_are_personalized_and_escaped(self):
        from perfume_visual import personal_dedication
        self.assertEqual(personal_dedication(FORMULA,''),'')
        text=personal_dedication(FORMULA,'Claudio')
        self.assertIn('Claudio, questa creazione è dedicata a te.',text)
        self.assertIn(FORMULA['nome'],text)
        with patch('tarocchi_web._atelier_componi_ai',return_value=(FORMULA,None)):
            response=self.client.post('/profumo',data={'q':'Ambra','cliente':'<script>prova</script>','creation_id':self.creation_id})
        self.assertEqual(response.status_code,200)
        self.assertNotIn('<script>prova</script>',response.text)
        self.assertIn('&lt;script&gt;prova&lt;/script&gt;',response.text)
        for control in ('print-recipe','print-inspiration','print-label','bottle-sculpture','bottle-essence'):
            self.assertIn('id="'+control+'"',response.text)

if __name__ == '__main__':unittest.main()
