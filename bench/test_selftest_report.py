import json,tempfile,unittest,xml.etree.ElementTree as ET
from pathlib import Path
from selftest_report import build_report,junit,ROOT
from oem_discovery import discover

class SelftestReportTests(unittest.TestCase):
    def setUp(self):self.catalog=json.loads((ROOT/'qualification_data/catalog.json').read_text())
    def test_catalog_has_no_duplicate_ids_and_keeps_required_hardware(self):
        ids=[f['id'] for f in self.catalog['features']];self.assertEqual(len(ids),len(set(ids)))
        self.assertTrue({'audio.mic_speaker','ihm.status_led','ihm.mic_led_rt','bluetooth.firmware','satellite.doppler','gps.fix','aprs.modulation'}<=set(ids))
    def test_passing_logical_case_does_not_qualify_full_hardware(self):
        r=build_report(self.catalog,[dict(scenario='FM',status='passed',reason='logical only')]);self.assertEqual(r['status'],'incomplete')
        self.assertTrue(all(f['status']=='incomplete' for f in r['features']))
    def test_junit_preserves_failures_and_skips_and_escapes_xml(self):
        r=build_report(self.catalog,[dict(scenario='GPS',status='failed',reason='bad <data> & missing response')])
        self.assertEqual(r['status'],'failed')
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'junit.xml';junit(r,p);root=ET.parse(p).getroot()
            self.assertEqual(len(root.findall('testcase/skipped')),len(self.catalog['features']))
            self.assertEqual(root.find('testcase/failure').get('message'),'bad <data> & missing response')
    def test_unknown_verdict_is_rejected(self):
        with self.assertRaises(ValueError):build_report(self.catalog,[dict(status='probably_ok')])
    def test_shared_firmware_menu_string_is_not_capability_proof(self):
        catalog=dict(features=[dict(id='aprs.receive',keyword='APRS Receive')])
        data=b'\0'*16+b'APRS Receive\0'+b'\0'*8
        r=discover(data,0x08006000,0x08006000,catalog)
        self.assertEqual(r['features'][0]['matching_strings'],1)
        self.assertFalse(r['features'][0]['presence_proven']);self.assertFalse(r['complete'])
if __name__=='__main__':unittest.main()
