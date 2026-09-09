import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4
from PIL import Image

from perfume_photo import prepare_photo, analyze_photo, PhotoInvalid, PhotoUnavailable, PHOTO_INTENTION
from tarocchi_web import app

def picture():
    output = io.BytesIO()
    im = Image.new('RGB', (80, 40), '#bd692d')
    exif = Image.Exif(); exif[270] = 'PRIVATE_METADATA'
    im.save(output, 'JPEG', exif=exif)
    return output.getvalue()

ANALYSIS = dict(osservazioni=['Luce ambrata sul metallo'],
    associazioni=[dict(elemento='Luce ambrata', evocazione='Un accordo caldo e asciutto')],
    direzione='Contrasto fra freschezza e calore.', incertezze='Il materiale non è certo.')

class PhotoTests(unittest.TestCase):
    def test_bytes_validated_metadata_removed(self):
        raw = picture(); clean = prepare_photo(io.BytesIO(raw))
        self.assertIn(b'PRIVATE_METADATA', raw)
        self.assertNotIn(b'PRIVATE_METADATA', clean['data'])
        self.assertEqual(clean['mime_type'], 'image/jpeg')
        self.assertEqual(len(clean['sha256']), 64)
        for invalid in (b'<svg></svg>', b'x' * 3_000_001, b''):
            with self.assertRaises(PhotoInvalid): prepare_photo(io.BytesIO(invalid))

    def test_vision_is_actual_image_call_and_whitelists_metadata(self):
        photo = prepare_photo(io.BytesIO(picture()))
        reply = dict(ANALYSIS, private_upload='must not survive')
        body = json.dumps({'candidates':[{'content':{'parts':[{'text':json.dumps(reply)}]}}]}).encode()
        with patch.dict(os.environ, {'GOOGLE_API_KEY':'test-only'}, clear=True), patch('perfume_photo.urllib.request.urlopen') as urlopen:
            urlopen.return_value.__enter__.return_value.read.return_value = body
            result = analyze_photo(photo)
            payload = json.loads(urlopen.call_args.args[0].data)
            self.assertNotIn('key=', urlopen.call_args.args[0].full_url)
            self.assertEqual(urlopen.call_args.args[0].get_header('X-goog-api-key'), 'test-only')
            self.assertTrue(payload['contents'][0]['parts'][0]['inline_data']['data'])
            self.assertEqual(result['osservazioni'], ANALYSIS['osservazioni'])
            self.assertNotIn('private_upload', result)
            self.assertNotIn('data', result)
            self.assertEqual(result['image_sha256'], photo['sha256'])

    def test_pasted_key_whitespace_is_removed_and_blank_primary_uses_configured_secondary(self):
        photo = prepare_photo(io.BytesIO(picture()))
        body = json.dumps({'candidates':[{'content':{'parts':[{'text':json.dumps(ANALYSIS)}]}}]}).encode()
        for env in ({'GOOGLE_API_KEY':' test-only\n'},
                    {'GOOGLE_API_KEY':' \n', 'GEMINI_API_KEY':'test-only'}):
            with self.subTest(env=list(env)), patch.dict(os.environ, env, clear=True), patch('perfume_photo.urllib.request.urlopen') as net:
                net.return_value.__enter__.return_value.read.return_value = body
                result = analyze_photo(photo)
                self.assertEqual(net.call_args.args[0].get_header('X-goog-api-key'), 'test-only')
                self.assertEqual(result['status'], 'interpreted')

    def test_invalid_or_unavailable_analysis_never_becomes_invented_success(self):
        photo = prepare_photo(io.BytesIO(picture()))
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(PhotoUnavailable): analyze_photo(photo)
        with patch.dict(os.environ, {'GOOGLE_API_KEY':'test-only'}, clear=True), patch('perfume_photo.urllib.request.urlopen') as urlopen:
            urlopen.return_value.__enter__.return_value.read.return_value = b'{}'
            with self.assertRaises(PhotoUnavailable): analyze_photo(photo)
            self.assertEqual(urlopen.call_count, 1)

    def test_incomplete_or_blocked_provider_response_never_becomes_success(self):
        photo = prepare_photo(io.BytesIO(picture()))
        cases = [({'promptFeedback':{'blockReason':'SAFETY'}}, 'vision_invalid_provider_blocked'),
                 ({'candidates':[{'finishReason':'MAX_TOKENS'}]}, 'vision_invalid_truncated'),
                 ({'candidates':[]}, 'vision_invalid_no_candidates')]
        for reply, expected in cases:
            with self.subTest(expected=expected), patch.dict(os.environ, {'GOOGLE_API_KEY':'test-only'}, clear=True), patch('perfume_photo.urllib.request.urlopen') as net:
                net.return_value.__enter__.return_value.read.return_value = json.dumps(reply).encode()
                with self.assertRaises(PhotoUnavailable) as failure:
                    analyze_photo(photo)
                self.assertEqual(failure.exception.code, expected)
                self.assertEqual(net.call_count, 1)

    def test_photo_only_native_post_archives_interpretation_and_replays(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'PERFUME_DB_PATH':str(Path(directory)/'archive.db')}, clear=True):
            client = app.test_client(); creation = str(uuid4()); photo = prepare_photo(io.BytesIO(picture()))
            perfume = dict(nome='Ferro di Luce', fam='Legnosa', ricetta=[], foto=dict(ANALYSIS, image_sha256=photo['sha256']))
            def form(): return {'foto':(io.BytesIO(picture()),'private-name.jpg'), 'creation_id':creation}
            with patch('tarocchi_web._atelier_componi_ai', return_value=(perfume,None)) as compose:
                first = client.post('/profumo', data=form())
                second = client.post('/profumo', data=form())
                self.assertEqual(first.status_code,200); self.assertEqual(second.status_code,200)
                self.assertIn('Dalla foto al profumo',first.text)
                self.assertNotIn('private-name', first.text)
                self.assertEqual(compose.call_args.args[0], PHOTO_INTENTION)
                self.assertTrue(compose.call_args.kwargs['foto']['data'])
                compose.assert_called_once()

    def test_failure_blocks_composition_and_example_is_allowlisted(self):
        with patch.dict(os.environ, {'VERCEL':'1'}, clear=True):
            client=app.test_client()
            with patch('tarocchi_web._atelier_componi_ai', side_effect=PhotoUnavailable('Analisi non disponibile')) as compose:
                response=client.post('/profumo',data={'foto':(io.BytesIO(picture()),'x.jpg')})
                self.assertEqual(response.status_code,503)
                self.assertIn('Analisi non disponibile',response.text)
                self.assertEqual(client.post('/profumo',data={'foto_esempio':'../../private'}).status_code,400)
                self.assertEqual(compose.call_count,1)

if __name__ == '__main__': unittest.main()
