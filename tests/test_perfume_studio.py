import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from uuid import uuid4

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

if __name__ == '__main__':unittest.main()
