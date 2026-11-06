"""Service-option masking and isolation from captured storage."""
import unittest
from oem_options import decode_options,enable_virtual_full_test,CAPTURE_SHA256,LOCAL_INFO_BLOCKS
from nand_overlay import OverlayNand


class FixtureNand(OverlayNand):
    def __init__(self):
        self.overlay={}
        self.sources={'nand_main_256MiB.bin':{'sha256':CAPTURE_SHA256}}
        self.original={}
        for n,address in enumerate(LOCAL_INFO_BLOCKS):
            page=bytearray((i*17+n)%256 for i in range(2112))
            page[2]=0;page[6]=8
            self.original[address//2048]=bytes(page)
    def page_image(self,row):
        return self.overlay.get(row,self.original[row])


class ServiceOptionsTests(unittest.TestCase):
    def test_other_band_bits_do_not_enable_entry(self):
        record=bytearray(14);record[6]=8
        options=decode_options(record)
        self.assertFalse(options['V121_entry_permission'])
        self.assertEqual(options['other_band_bits'],8)

    def test_band_only_is_not_full_adjustment(self):
        record=bytearray(14);record[6]=9
        options=decode_options(record)
        self.assertTrue(options['V121_entry_permission'])
        self.assertFalse(options['V121_full_adjustment_permission'])

    def test_legacy_gate_and_option_checkbox_are_distinct(self):
        record=bytearray(14);record[2]=2
        options=decode_options(record)
        self.assertTrue(options['V121_entry_permission'])
        self.assertFalse(options['full_test_option_bit'])

    def test_overlay_changes_only_four_permission_bytes(self):
        nand=FixtureNand();before=nand.original.copy()
        evidence=enable_virtual_full_test(nand)
        self.assertEqual(nand.original,before)
        self.assertEqual(len(evidence['changes']),4)
        for row,old in before.items():
            new=nand.page_image(row)
            self.assertEqual([i for i,(a,b) in enumerate(zip(old,new)) if a!=b],[2,6])
            self.assertEqual(new[2],1);self.assertEqual(new[6],9)
            self.assertEqual(new[2048:],old[2048:])

    def test_fixture_is_idempotent(self):
        nand=FixtureNand();enable_virtual_full_test(nand)
        self.assertEqual(enable_virtual_full_test(nand)['changes'],[])

    def test_rejects_other_capture_before_mutating(self):
        nand=FixtureNand();nand.sources['nand_main_256MiB.bin']['sha256']='unknown'
        with self.assertRaises(ValueError):enable_virtual_full_test(nand)
        self.assertEqual(nand.overlay,{})


if __name__=='__main__':unittest.main()
