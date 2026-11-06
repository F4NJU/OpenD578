import unittest
from indicator_qualification import assess_status_led

class IndicatorQualificationTests(unittest.TestCase):
    def fixture(self):
        return dict(stop=dict(kind='instruction_budget'),hardware=dict(board_outputs=dict(indicators=dict(radio_status=dict(
            decoded=True,pending_bits=0,total_frames=4,raw_command=0x46,
            frames=[dict(step=2,value=0x4e),dict(step=4,value=0x46),dict(step=6,value=0x56),dict(step=8,value=0x46)])))),
            inputs=[dict(step=1,input=dict(control='RF_RX',carrier=True)),dict(step=3,input=dict(control='RF_RX',carrier=False)),
                    dict(step=5,input=dict(control='MIC_KEYS',keys=['PTT'])),dict(step=7,input=dict(control='MIC_KEYS',keys=[]))])
    def test_new_firmware_does_not_need_oem_ram_flags(self):self.assertEqual(assess_status_led(self.fixture())['status'],'passed')
    def test_wrong_led_colour_fails(self):
        r=self.fixture();r['hardware']['board_outputs']['indicators']['radio_status']['frames'][0]['value']=0x56
        self.assertEqual(assess_status_led(r)['status'],'failed')
    def test_missing_or_truncated_evidence_is_incomplete(self):
        r=self.fixture();r['hardware']['board_outputs']['indicators']['radio_status']['total_frames']=100
        self.assertEqual(assess_status_led(r)['status'],'incomplete')
if __name__=='__main__':unittest.main()
