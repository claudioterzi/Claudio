"""Meaningful protection against wrong associations and loss of image history."""
import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image
from studio.parfums.sincronizza_foto import import_image, sync


class PhotosTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        (self.root / 'studio/parfums').mkdir(parents=True)
        (self.root / 'studio/parfums/parfums_400.json').write_text(json.dumps({'parfums': [
            {'numero': 1, 'nome': 'Uno'}, {'numero': 2, 'nome': 'Due'}]}))
        self.a, self.b = self.root / 'a.png', self.root / 'b.png'
        Image.new('RGB', (80, 100), 'red').save(self.a)
        Image.new('RGB', (80, 100), 'blue').save(self.b)

    def add(self, source=None, number=1):
        return import_image(source or self.a, number, root=self.root)

    def test_number_association(self):
        file, added = self.add(number=2)
        records, pending = sync(self.root)
        self.assertTrue(added)
        self.assertFalse(pending)
        self.assertFalse(records[1]['photos'])
        self.assertEqual(records[2]['primary'], file.relative_to(self.root / 'public').as_posix())

    def test_unknown_number_never_imported(self):
        with self.assertRaises(ValueError):
            self.add(number=3)
        self.assertFalse((self.root / 'public').exists())

    def test_duplicate_is_idempotent(self):
        first, _ = self.add()
        second, added = self.add()
        self.assertFalse(added)
        self.assertEqual(first, second)
        self.assertEqual(len(sync(self.root)[0][1]['photos']), 1)

    def test_new_photo_becomes_primary_and_retains_old(self):
        first, _ = self.add()
        sync(self.root)
        second, _ = self.add(self.b)
        records, _ = sync(self.root)
        self.assertEqual(len(records[1]['photos']), 2)
        self.assertTrue(first.exists())
        self.assertEqual(records[1]['primary'], second.relative_to(self.root / 'public').as_posix())

    def test_unlabelled_photo_is_unassigned(self):
        first, _ = self.add()
        (first.parent / 'senza-numero.png').write_bytes(self.b.read_bytes())
        records, pending = sync(self.root)
        self.assertEqual(len(records[1]['photos']), 1)
        self.assertEqual(len(pending), 1)

    def test_overwrite_cannot_erase_registry(self):
        first, _ = self.add()
        sync(self.root)
        registry = self.root / 'studio/parfums/foto_400.json'
        before = registry.read_bytes()
        first.write_bytes(self.b.read_bytes())
        with self.assertRaises(ValueError):
            sync(self.root)
        self.assertEqual(registry.read_bytes(), before)

    def test_deletion_cannot_erase_registry(self):
        first, _ = self.add()
        sync(self.root)
        first.unlink()
        with self.assertRaises(ValueError):
            sync(self.root)

    def test_invalid_image_not_imported(self):
        self.a.write_text('not an image')
        with self.assertRaises(OSError):
            self.add()
        self.assertFalse((self.root / 'public').exists())

    def test_repeated_sync_does_not_change_output(self):
        self.add()
        sync(self.root)
        registry = self.root / 'studio/parfums/foto_400.json'
        before = registry.read_bytes(), registry.stat().st_mtime_ns
        sync(self.root)
        self.assertEqual(before, (registry.read_bytes(), registry.stat().st_mtime_ns))


if __name__ == '__main__':
    unittest.main()
