import unittest
import csv
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class EvidenceTest(unittest.TestCase):
    def test_data_and_originals(self):
        data=json.loads((ROOT/'docs/evidence/CLAIMS.json').read_text())
        self.assertGreaterEqual(len(data['claims']),25)
        ids=set()
        for c in data['claims']:
            self.assertNotIn(c['id'],ids)
            ids.add(c['id'])
            self.assertIn(c['evidence_type'],{'USER_PHOTO','USER_MEAS','OEM_STATIC','OEM_EMU','DATASHEET','THIRD_PARTY_BOARD','INFERRED','UNKNOWN'})
            self.assertTrue((ROOT/c['local_reference']).is_file(),c['id'])
        self.assertTrue((ROOT/'docs/archives/ORIGINAUX_A_RECUPERER.md').is_file())
    def test_pinout(self):
        with (ROOT/'hardware/pinmaps/GD32F303VKT6_LQFP100_REFERENCE.csv').open() as f:
            rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),100)
        self.assertEqual([int(c['physical_pin']) for c in rows],list(range(1,101)))
        checks={6:'VBAT',14:'NRST',17:'PC2',23:'PA0',53:'PB14',54:'PB15',65:'PC8',66:'PC9',68:'PA9',69:'PA10',72:'PA13',76:'PA14',77:'PA15',83:'PD2',91:'PB5',92:'PB6',93:'PB7',95:'PB8'}
        for i,label in checks.items():self.assertEqual(rows[i-1]['gd32_pin'],label)
    def test_schematic_pin_count(self):
        s=(ROOT/'hardware/kicad/OpenD578_GD32F303VKT6_RECONSTITUE.kicad_sch').read_text()
        self.assertEqual(s.count('(pin "'),100)
        self.assertIn('PAS DE NETLISTE',s)
        self.assertIn('0.4',s)
if __name__=='__main__': unittest.main()
