"""Input routing regressions, using synthetic captures rather than OEM data."""
import hashlib
import tempfile
import unittest
import zipfile
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

import prepare_inputs as inputs
from web_server import Laboratory


def digest(data):
    return hashlib.sha256(data).hexdigest()


class InputRoutingTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.source, self.cache = self.root/'source', self.root/'cache'
        self.source.mkdir()
        self.app = b'synthetic application'
        self.flash = bytes(0x6000) + self.app
        self.sct = b'synthetic SCT reference'
        self.nand = {'nand_main_256MiB.bin': b'main', 'nand_oob64_8MiB.bin': b'oob',
                     'nand_ecc_status_128KiB.bin': b'ecc'}
        self.stack.enter_context(patch.multiple(inputs, FIRMWARE_SIZE=len(self.app),
            EXPECTED_SHA=digest(self.app), FULL_SIZE=len(self.flash), FULL_SHA=digest(self.flash),
            SCT_SIZE=len(self.sct), SCT_SHA=digest(self.sct),
            EXPECTED_FILES={name: (len(data), digest(data)) for name, data in self.nand.items()}))
        (self.source/'full_flash_pass1.bin').write_bytes(self.flash)

    def extracted(self):
        for name, data in self.nand.items():
            (self.source/name).write_bytes(data)
        (self.source/inputs.SCT_NAME).write_bytes(self.sct)

    def test_two_user_files_report_exact_three_missing_inputs(self):
        (self.source/'nand_main_256MiB.bin').write_bytes(self.nand['nand_main_256MiB.bin'])
        self.assertEqual(inputs.missing_inputs(self.source, self.cache), [
            'nand_oob64_8MiB.bin', 'nand_ecc_status_128KiB.bin', inputs.SCT_NAME])
        lab = Laboratory(self.source, self.cache, self.root/'run')
        with patch('web_server.subprocess.Popen') as process:
            with self.assertRaisesRegex(ValueError, 'Fichiers manquants.*nand_oob64'):
                lab.start({})
            process.assert_not_called()

    def test_extracted_route_recovers_reference_application_and_keeps_sources(self):
        self.extracted()
        inputs.check_inputs(self.source, self.cache)
        firmware, nand = inputs.prepare(self.source, self.cache)
        self.assertEqual(firmware.read_bytes(), self.app)
        for name, data in self.nand.items():
            self.assertEqual((nand/name).read_bytes(), data)
            self.assertEqual((self.source/name).read_bytes(), data)
        self.assertEqual(inputs.prepare_sct_reference(self.source, self.cache).read_bytes(), self.sct)
        self.assertEqual((self.source/'full_flash_pass1.bin').read_bytes(), self.flash)

    def test_original_archives_still_work_with_nested_members(self):
        with zipfile.ZipFile(self.source/inputs.OEM_ARCHIVE, 'w') as z:
            z.writestr('firmware/'+inputs.FIRMWARE_NAME, self.app)
            z.writestr('DSP/'+inputs.SCT_NAME, self.sct)
        with zipfile.ZipFile(self.source/inputs.NAND_ARCHIVE, 'w') as z:
            for name, data in self.nand.items():
                z.writestr('NAND_ORIGINAUX/'+name, data)
        inputs.check_inputs(self.source, self.cache)
        firmware, nand = inputs.prepare(self.source, self.cache)
        self.assertEqual(firmware.read_bytes(), self.app)
        self.assertEqual((nand/'nand_main_256MiB.bin').read_bytes(), b'main')
        self.assertEqual(inputs.prepare_sct_reference(self.source, self.cache).read_bytes(), self.sct)

    def test_mixed_cache_and_extracted_sources_work(self):
        self.extracted()
        inputs.prepare(self.source, self.cache)
        for name in self.nand:
            (self.source/name).unlink()
        inputs.check_inputs(self.source, self.cache)
        inputs.prepare(self.source, self.cache)

    def test_corrupt_full_capture_is_rejected_before_deriving_application(self):
        self.extracted()
        (self.source/'full_flash_pass1.bin').write_bytes(b'x'*len(self.flash))
        with self.assertRaisesRegex(ValueError, 'SHA256'):
            inputs.prepare(self.source, self.cache)
        self.assertFalse((self.cache/inputs.FIRMWARE_NAME).exists())

    def test_corrupt_extracted_oob_is_rejected(self):
        self.extracted()
        (self.source/'nand_oob64_8MiB.bin').write_bytes(b'bad')
        with self.assertRaisesRegex(ValueError, 'SHA256'):
            inputs.prepare(self.source, self.cache)
        self.assertFalse((self.cache/'NAND_ORIGINAUX/nand_oob64_8MiB.bin').exists())

    def test_duplicate_archive_member_is_not_accepted(self):
        archive=self.source/inputs.OEM_ARCHIVE
        with zipfile.ZipFile(archive, 'w') as z:
            z.writestr('first/'+inputs.SCT_NAME, self.sct)
            z.writestr('second/'+inputs.SCT_NAME, self.sct)
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            inputs.prepare_sct_reference(self.source, self.cache)

    def test_external_full_flash_override_is_used(self):
        self.extracted()
        external=self.root/'external.bin'
        (self.source/'full_flash_pass1.bin').rename(external)
        inputs.check_inputs(self.source, self.cache, external)
        firmware, _ = inputs.prepare(self.source, self.cache, external)
        self.assertEqual(firmware.read_bytes(), self.app)

    def test_optional_bluetooth_is_only_required_when_enabled(self):
        self.extracted()
        self.assertEqual(inputs.missing_inputs(self.source, self.cache), [])
        self.assertEqual(inputs.missing_inputs(self.source, self.cache, bluetooth='et12'),
                         ['B707_Audio_AGHF_ET12_QX-V10043.bin'])

    def test_cache_cannot_hide_a_missing_physical_flash_capture(self):
        self.extracted()
        inputs.prepare(self.source, self.cache)
        (self.source/'full_flash_pass1.bin').unlink()
        self.assertEqual(inputs.missing_inputs(self.source, self.cache),
                         [str(self.source/'full_flash_pass1.bin')])


if __name__ == '__main__':
    unittest.main()
