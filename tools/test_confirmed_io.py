from pathlib import Path
import json,unittest
R=Path(__file__).resolve().parents[1]
class ConfirmedIO(unittest.TestCase):
 def test_all_gpio_visible_in_both_mcu_connections(self):
  expected={p+str(n)for p in ['PA','PB','PC','PD','PE']for n in range(16)}
  for f in (R/'hardware/models').glob('*.json'):
   m=json.loads(f.read_text());mid='mcu_plus'if 'plus' in m['id']else'mcu';pins={p['from_pin'] for e in m['edges'] if e['source']==mid for p in e['pins']}
   self.assertFalse(expected-pins,(m['id'],expected-pins))
 def test_bank_names_do_not_claim_lo_if_and_preserve_old_ids(self):
  for f in (R/'hardware/models').glob('*.json'):
   m=json.loads(f.read_text());nodes={n['id']:n for n in m['nodes']}
   for i,(id,cs)in enumerate(zip(['qa_lo_a','qa_lo_b','qa_if_a','qa_if_b'],['PB5','PB2','PC13','PE1'])):
    self.assertIn('banque '+str(i),nodes[id]['label']);self.assertIn(cs,nodes[id]['subtitle'])
    e=next(e for e in m['edges']if e['id']=='rfspi-'+id);self.assertEqual(e['status'],'oem_trace');self.assertEqual({p['from_pin']for p in e['pins']},{'PB3','PB4',cs})
