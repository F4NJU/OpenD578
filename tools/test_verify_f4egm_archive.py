import hashlib
from pathlib import Path
import tempfile
import unittest
import zipfile
from verify_f4egm_archive import verify_archive


class ArchiveVerificationTest(unittest.TestCase):
    def test_valid_members_are_checked_without_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / 'sample.zip'
            with zipfile.ZipFile(archive, 'w') as output:
                output.writestr('capture.bin', b'example')
            profile = {'capture.bin': (7, hashlib.sha256(b'example').hexdigest())}
            self.assertEqual(verify_archive(archive, profile)['capture.bin']['bytes'], 7)
            self.assertFalse((Path(directory) / 'capture.bin').exists())
            with self.assertRaises(ValueError):
                verify_archive(archive, {'capture.bin': (7, '0' * 64)})

    def test_unexpected_and_duplicate_members_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            for member in ['../capture.bin', 'unexpected.bin']:
                archive = Path(directory) / 'sample.zip'
                with zipfile.ZipFile(archive, 'w') as output:
                    output.writestr(member, b'example')
                with self.assertRaises(ValueError):
                    verify_archive(archive, {'capture.bin': (7, hashlib.sha256(b'example').hexdigest())})


if __name__ == '__main__':
    unittest.main()
