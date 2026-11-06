import unittest
from status_led import StatusLedBus

class StatusLedTests(unittest.TestCase):
    def send(self,bus,value):
        for i in range(8):
            v=8 if value&(1<<i) else 0
            bus.gpio(v,v|16,0x00033000,i)
            bus.gpio(v|16,v,0x00033000,i)
    def test_real_observed_rx_idle_tx_idle_commands(self):
        b=StatusLedBus();self.assertEqual(b.describe()['state'],'unknown')
        for value,state in [(0x4E,'green'),(0x46,'off'),(0x56,'red'),(0x46,'off')]:
            self.send(b,value);self.assertEqual(b.describe()['state'],state)
        self.assertFalse(b.describe()['physical_mapping_verified'])
    def test_bootloader_blink_and_unknown_bits(self):
        b=StatusLedBus()
        for value,state in [(0,'off'),(0x10,'red'),(0x80,'off'),(0x18,'red+green')]:
            self.send(b,value);self.assertEqual(b.describe()['state'],state)
    def test_partial_clock_or_input_mode_is_not_a_complete_command(self):
        b=StatusLedBus();b.gpio(0,16,0x33000,0);self.assertEqual(b.describe()['state'],'unknown')
        b.gpio(0,16,0,1);self.assertEqual(b.describe()['pending_bits'],0)
        for i in range(8):b.gpio(8,24,0,i)
        self.assertEqual(b.describe()['state'],'unknown')
if __name__=='__main__':unittest.main()
