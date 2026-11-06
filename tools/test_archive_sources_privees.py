"""Offline regression tests for the personal source archiver.

Never contact the network or include any third-party source files.
"""
import importlib.util
from pathlib import Path
import tempfile
import unittest

MODULE_PATH = Path(__file__).with_name('archive_sources_privees.py')
spec = importlib.util.spec_from_file_location('archive_sources_privees', MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class OfflineArchiverTests(unittest.TestCase):
    def test_percent_encodes_space_without_doubling_existing_escape(self):
        self.assertEqual(
            mod.normal('https://radio.carstenbauer.net/578 head connections.jpg'),
            'https://radio.carstenbauer.net/578%20head%20connections.jpg')
        self.assertEqual(
            mod.normal('https://radio.carstenbauer.net/578%20head%20connections.jpg'),
            'https://radio.carstenbauer.net/578%20head%20connections.jpg')

    def test_rejects_unsafe_schemes(self):
        self.assertIsNone(mod.normal('file:///etc/passwd'))
        self.assertIsNone(mod.normal('javascript:alert(1)'))
        self.assertIsNone(mod.normal(''))

    def test_optional_tools_filtered_until_authorized(self):
        with tempfile.TemporaryDirectory() as d:
            a = mod.PrivateArchive(Path(d)/'a',source='f1dmg_anytone',include_tools=False)
            before=len(a.todo)
            a.add('http://f1dmg.free.fr/Exemple-v1.11-2020.rdt','asset',None)
            self.assertEqual(before, len(a.todo))
            b = mod.PrivateArchive(Path(d)/'b',source='f1dmg_anytone',include_tools=True)
            b.add('http://f1dmg.free.fr/Exemple-v1.11-2020.rdt','asset',None)
            self.assertEqual(3,len(b.todo))

    def test_apache_sort_variations_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            a = mod.PrivateArchive(Path(d),source='f1dmg_anytone')
            before=len(a.todo)
            a.add('http://f1dmg.free.fr/CMD/?C=M;O=D','page',None)
            self.assertEqual(before,len(a.todo))

    def test_third_party_links_not_downloaded(self):
        with tempfile.TemporaryDirectory() as d:
            a=mod.PrivateArchive(Path(d),source='f1dmg_anytone',include_tools=True)
            before=len(a.todo)
            a.add('https://unrelated.example.com/trojans.exe','asset',None)
            self.assertEqual(before,len(a.todo))


if __name__ == '__main__':
    unittest.main()
