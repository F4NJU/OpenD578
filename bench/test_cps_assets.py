"""CPS static routing checks; does not execute firmware or require OEM inputs."""
import tempfile
import unittest
from pathlib import Path
from cps_assets import read_cps_asset


class CpsAssetsTest(unittest.TestCase):
    def test_assets_are_confined_to_build_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'dist'
            root.mkdir()
            (root / 'index.html').write_text('CPS', encoding='utf-8')
            (Path(temporary) / 'private.json').write_text('secret', encoding='utf-8')
            (root / 'private.py').write_text('private', encoding='utf-8')
            self.assertEqual(read_cps_asset(root, '/cps/'), (b'CPS', 'text/html; charset=utf-8'))
            for route in ['/cps/../private.json', '/cps/%2e%2e/private.json',
                          '/cps/%2fprivate.json', '/cps/..%5cprivate.json',
                          '/cps/private.py', '/cps/C:/private.json', '/other/']:
                with self.subTest(route=route), self.assertRaises(ValueError):
                    read_cps_asset(root, route)

    def test_missing_build_is_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(FileNotFoundError):
                read_cps_asset(Path(temporary) / 'missing', '/cps/')


if __name__ == '__main__':
    unittest.main()
