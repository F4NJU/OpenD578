import unittest
from types import SimpleNamespace
from board_observations import describe,microphone_output

class BoardObservationTests(unittest.TestCase):
    def test_tx_flag_cannot_make_led_or_speaker_look_qualified(self):
        r=SimpleNamespace(gpio={0x40011800:{12:64}},lighting=SimpleNamespace(registers={8:255}),
            usart0=SimpleNamespace(tx=[]),uart3=SimpleNamespace(peer=SimpleNamespace(mode='absent')),
            observed_TX={'TX_request':True})
        d=describe(r);self.assertEqual(d['indicators']['radio_status']['state'],'unknown')
        self.assertIsNone(d['audio_outputs']['microphone_speaker']['selected'])
        self.assertFalse(d['bluetooth']['internal_firmware_executed'])
    def test_frames_are_observed_without_assigning_led_semantics(self):
        frame=[0x53]+[0]*14+[6];d=microphone_output([0xAA]+frame+frame[:9])
        self.assertEqual(d['observed_frames'],1);self.assertFalse(d['payload_semantics_qualified'])
        self.assertEqual(d['LEDs'],'unknown')
if __name__=='__main__':unittest.main()
