"""Synthetic generator regression tests; no real corpus or recipe regeneration."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

def load_builder(filename='build_opera_reader.py'):
    spec=importlib.util.spec_from_file_location('reader_builder_under_test',ROOT/'scripts'/filename)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def js_constant(html,name):
    marker='const '+name+' = '
    return json.JSONDecoder().raw_decode(html[html.index(marker)+len(marker):])[0]

class OperaGeneratorTests(unittest.TestCase):
    def test_first_document_updates_and_current_reader_survives_rebuild(self):
        with tempfile.TemporaryDirectory() as directory:
            isolated=Path(directory);(isolated/'public').mkdir();(isolated/'scripts').mkdir()
            template=(ROOT/'scripts/opera_reader_template.html').read_text(encoding='utf-8')
            (isolated/'scripts/opera_reader_template.html').write_text(template,encoding='utf-8',newline='\n')
            corpus=[{'gruppo':'Fittizio','titolo':'Prima versione','file':'fake/first.md','html':'<h2>Prima versione</h2>'}, {'gruppo':'Fittizio','titolo':'Secondo','file':'fake/second.md','html':'<p>Secondo documento</p>'}]
            source=isolated/'public/opera-corpus.json'
            builder=load_builder();builder.ROOT=isolated
            for title in ['Prima versione','Nuova versione </script> sicura']:
                corpus[0]['titolo']=title;corpus[0]['html']='<h2>'+title+'</h2>'
                source.write_text(json.dumps(corpus,ensure_ascii=False),encoding='utf-8',newline='\n')
                before=source.read_bytes()
                with contextlib.redirect_stdout(io.StringIO()): builder.build()
                html=(isolated/'public/opera.html').read_text(encoding='utf-8')
                first=js_constant(html,'FIRST_DOC');docs=js_constant(html,'DOCS')
                self.assertEqual(first,corpus[0])
                self.assertEqual(source.read_bytes(),before)
                self.assertEqual(len(docs),2)
                self.assertIn('· 2 documenti ·',html)
                self.assertIn('.lettore > section { flex:1; min-width:0; width:100%; max-width:100%; }',html)
                self.assertIn('Cerca un documento',html)
                self.assertIn('aria-busy',html)
                self.assertNotIn('__OPERA_',html)
                for doc,record in zip(corpus,docs):
                    content=(isolated/'public'/record['src']).read_bytes()
                    self.assertEqual(content,doc['html'].encode('utf-8'))
                    self.assertEqual(hashlib.sha256(content).hexdigest(),record['sha256'])
                if '</script>' in title: self.assertIn('<\\/script>',html)

    def test_empty_corpus_does_not_overwrite_a_reader(self):
        with tempfile.TemporaryDirectory() as directory:
            isolated=Path(directory);(isolated/'public').mkdir()
            source=isolated/'public/opera-corpus.json';source.write_text('[]',encoding='utf-8')
            reader=isolated/'public/opera.html';reader.write_text('previous reader',encoding='utf-8')
            builder=load_builder();builder.ROOT=isolated
            with self.assertRaisesRegex(ValueError,'at least one'): builder.build()
            self.assertEqual(reader.read_text(encoding='utf-8'),'previous reader')

class LibroGeneratorTests(unittest.TestCase):
    def test_derivatives_use_lf_and_integral_bytes_remain_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            isolated=Path(directory);public=isolated/'public';public.mkdir()
            source=public/'libro-integrale.html'
            original=(ROOT/'public/libro-integrale.html').read_bytes()
            source.write_bytes(original)
            builder=load_builder('build_libro_reader.py')
            builder.ROOT=isolated;builder.PUBLIC=public;builder.SOURCE=source;builder.DEST=public/'libro'
            with contextlib.redirect_stdout(io.StringIO()): builder.build()
            self.assertEqual(source.read_bytes(),original)
            manifest=json.loads((public/'libro/provenienza.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['source_sha256'],hashlib.sha256(original).hexdigest())
            self.assertEqual(manifest['git_blob_sha256'],hashlib.sha256(original.replace(b'\r\n',b'\n')).hexdigest())
            self.assertEqual(manifest['perfumes'],400)
            self.assertEqual(len(manifest['chapters']),12)
            for filename in ['libro.html','libro-classico.css','libro/indice.json','libro/provenienza.json']:
                with self.subTest(file=filename):
                    data=(public/filename).read_bytes()
                    self.assertNotIn(b'\r\n',data)
                    self.assertEqual(data,(ROOT/'public'/filename).read_bytes().replace(b'\r\n',b'\n'))
            for chapter in manifest['chapters']:
                data=(isolated/chapter['file']).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(),chapter['derived_fragment_sha256'])

if __name__=='__main__': unittest.main()
