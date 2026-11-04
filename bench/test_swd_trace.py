import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from swd_trace import inspect

class DebugWriteEvidenceTests(unittest.TestCase):
    def test_readback_is_not_used_as_evidence_of_SWD_state(self):
        report={'first_4096_MMIO_events':[
            dict(op='write',address='0x40010004',size=4,value='0x02000000',step=1),
            dict(op='read',address='0x40010004',size=4,value='0x04000000',step=2)]}
        r=inspect(report)
        self.assertEqual(len(r['configuration_writes']),1)
        self.assertEqual(r['configuration_writes'][0]['SWJ_CFG'],2)
        self.assertFalse(r['recovery_proven'])
    def test_actual_disable_write_is_distinct_from_JTAG_only_disable(self):
        report={'first_4096_MMIO_events':[dict(op='write',address=0x40010004,size=4,value=0x04000000,step=3)]}
        self.assertEqual(inspect(report)['configuration_writes'][0]['meaning'],'JTAG and SWD disabled')

if __name__=='__main__':unittest.main()
