import sys
import tempfile
import json
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from qa4818n_trace import encode_frequency_hz,decode_frequency_half_hz,analyse,load_frames,compare_reports

class QA4818TraceTest(unittest.TestCase):
    def test_frequency_pairs(self):
        for hz,expected in [(38550000,(0x0009,0x6960)),(38850000,(0x0009,0x7c20)),
                            (145500000,(0x0023,0x85c0)),(435000000,(0x006a,0x3380))]:
            self.assertEqual(encode_frequency_hz(hz),expected)
            self.assertEqual(decode_frequency_half_hz(*expected),hz*2)

    def test_classification_and_pages(self):
        frames=[dict(step=1,bank=0,page=1,register=0x29,value=0x29,direction='write'),
                dict(step=2,bank=1,page=0,register=0x29,value=0x002c,direction='write'),
                dict(step=3,bank=1,page=0,register=0x2a,value=0xef20,direction='write'),
                dict(step=4,bank=3,page=0,register=0x29,value=0x9,direction='write'),
                dict(step=5,bank=3,page=0,register=0x2a,value=0x6960,direction='write')]
        got=analyse(frames,145500000,'RX_A')
        self.assertEqual(len(got['frequency_events']),2)
        self.assertIn('OL injection haute +38.550 MHz',got['frequency_events'][0]['candidates'])
        self.assertIn('FI 38.550 MHz (candidat reception IF)',got['frequency_events'][1]['candidates'])

    def test_no_fake_pair_from_read(self):
        got=analyse([dict(bank=0,page=0,register=0x29,value=5,direction='read'),
                     dict(bank=0,page=0,register=0x2a,value=0x1234,direction='write')])
        self.assertEqual(got['frequency_events'],[])

    def test_malformed(self):
        self.assertEqual(len(analyse([dict(bank=5,page=0,register=1,value=1,direction='write')])['malformed_frames']),1)

    def test_capture_diff_and_30_status(self):
        one=analyse([dict(bank=0,page=0,register=0x30,value=0x4024,direction='write'),
                    dict(bank=0,page=0,register=0x29,value=0x23,direction='write'),
                    dict(bank=0,page=0,register=0x2a,value=0x85c0,direction='write')],145500000,'RX_1')
        two=analyse([dict(bank=0,page=0,register=0x30,value=0x4044,direction='write'),
                    dict(bank=0,page=0,register=0x29,value=0x23,direction='write'),
                    dict(bank=0,page=0,register=0x2a,value=0x88e0,direction='write')],145550000,'TX_1')
        self.assertTrue(one['critical_command_timeline'][0]['bits_AT1846S_only']['rx_on'])
        self.assertFalse(one['critical_command_timeline'][0]['bits_AT1846S_only']['tx_on'])
        changes=compare_reports([one,two])['adjacent_capture_diffs'][0]['changed_or_unobserved_registers']
        self.assertTrue(any(c['bank_page_register']=='0:0:30' for c in changes))
        self.assertTrue(any(c['bank_page_register']=='0:0:2A' for c in changes))

    def test_formats(self):
        sample=[dict(bank=0,page=0,register=0x29,value=0x23,direction='write'),
                dict(bank=0,page=0,register=0x2a,value=0x85c0,direction='write')]
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'x.json'
            p.write_text(json.dumps({'RF_control_spi':{'frames':sample}}))
            self.assertEqual(load_frames(p),sample)
            p.write_text(json.dumps({'radio':{'frames':sample}}))
            self.assertEqual(load_frames(p),sample)

if __name__=='__main__':unittest.main()
