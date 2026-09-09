import copy
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from tarocchi_web import app
from perfume_restore import restore

ROOT = Path(__file__).resolve().parents[1]


class RestoreTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.record = dict(schema_version=1, customer='Cliente Prova', intention='Luce e ferro',
            perfume=json.loads((ROOT/'studio/parfums/examples/cantiere.json').read_text()),
            presentation={'bottle':{'label':'Essenza'}})

    def post(self, record):
        return self.client.post('/atelier/riapri',data={'scheda':(io.BytesIO(json.dumps(record).encode()),'creazione.json')})

    def test_reopens_exact_formula_dedication_and_variant_without_ai_or_archive(self):
        with patch('tarocchi_web._atelier_componi_ai') as ai, patch('perfume_studio.save_record') as save:
            response = self.post(self.record)
        self.assertEqual(response.status_code,200)
        ai.assert_not_called(); save.assert_not_called()
        for value in ('Ferro di Luce','Cliente Prova','questa creazione è dedicata a te','FORMULA NON ARCHIVIATA','Riapri una scheda'):
            self.assertIn(value,response.text)
        result = restore(json.dumps(self.record).encode())
        self.assertEqual(result['perfume']['ricetta'],self.record['perfume']['ricetta'])
        self.assertEqual(result['perfume']['formula_code'],self.record['perfume']['formula_code'])
        self.assertEqual(result['restored_variant'],'Essenza')
        self.assertNotIn('generate-image',response.text)
        self.assertNotIn('Access-Control-Allow-Origin',response.headers)

    def test_modified_recipe_is_rejected_even_if_total_is_preserved(self):
        self.record['perfume']['ricetta'][0][2] += 1
        self.record['perfume']['ricetta'][1][2] -= 1
        self.assertEqual(self.post(self.record).status_code,400)

    def test_unknown_material_duplicate_nan_and_bad_shape_are_rejected(self):
        for mutation in ('unknown','duplicate','nan','shape'):
            record = copy.deepcopy(self.record)
            if mutation=='unknown':
                record['perfume'].pop('formula_code'); record['perfume']['ricetta'][0][1]=999999
            elif mutation=='duplicate':record['perfume']['ricetta'][1]=record['perfume']['ricetta'][0]
            elif mutation=='nan':record['perfume']['ricetta'][0][2]=float('nan')
            else:record['perfume']['ricetta'][0]=None
            with self.subTest(mutation=mutation):self.assertEqual(self.post(record).status_code,400)

    def test_file_claim_cannot_grant_archive_or_image_access(self):
        self.record.update(serial='TP-'+'A'*32,archived=True,image_token='forged')
        self.record['perfume']['flacone']={'prompt':'untrusted instruction','accenti':['fiction']}
        response=self.post(self.record)
        self.assertEqual(response.status_code,200)
        for forbidden in ('FORMULA ARCHIVIATA','generate-image','untrusted instruction','fiction'):
            self.assertNotIn(forbidden,response.text)

    def test_markup_escaped_links_validated_and_suggestions_not_restored(self):
        self.record['customer']='<script>alert(1)</script>'
        self.record['perfume']['ricerca']={'reference':'Prova','status':'sourced','summary':'Fonti nel file','consulted_at':'2026-09-09','sources':[{'title':'Source','url':'https://example.com/reference'}],'suggestions':'<script>never</script>'}
        response=self.post(self.record)
        self.assertEqual(response.status_code,200)
        self.assertNotIn('<script>alert(1)</script>',response.text)
        self.assertNotIn('never',response.text)
        self.record['perfume']['ricerca']['sources'][0]['url']='javascript:alert(1)'
        self.assertEqual(self.post(self.record).status_code,400)

    def test_malformed_and_large_uploads_rejected(self):
        response=self.client.post('/atelier/riapri',data={'scheda':(io.BytesIO(b'not json'),'file.json')})
        self.assertEqual(response.status_code,400)
        response=self.client.post('/atelier/riapri',data={'scheda':(io.BytesIO(b' '*310000),'file.json')})
        self.assertEqual(response.status_code,413)

    def test_laboratory_settings_preserved_but_production_claim_not_trusted(self):
        first = self.record['perfume']['ricetta'][0]
        self.record['laboratory'] = {'basis':'ml','concentration':'20','density':'0.85','support':'',
            'preparations':[{'n':first[1],'preparation':'Preparazione fittizia di test'}], 'production_validated':True}
        result = restore(json.dumps(self.record).encode())
        self.assertEqual(result['perfume']['lab_draft']['density'],'0.85')
        self.assertFalse(result['perfume']['lab_draft']['production_validated'])
        self.record['laboratory']['preparations'][0]['n']=99999
        self.assertEqual(self.post(self.record).status_code,400)


if __name__=='__main__':unittest.main()
