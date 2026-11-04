import unittest
from timers import Timer
from backup_rtc import BackupRtc
from lighting import LightingBus
from emulate_clock_v121 import StopModel


class TimerTests(unittest.TestCase):
    def test_prescaled_overflow_and_irq_clear(self):
        t=Timer('TIMER6')
        t.write(0x28,2,999)
        t.write(0x2C,2,119)
        t.write(0x14,2,1)
        t.write(0x10,2,0xFFFE)
        t.write(0xC,2,1)
        t.write(0,2,1)
        t.advance(119999)
        self.assertFalse(t.irq)
        t.advance(120000)
        self.assertTrue(t.irq)
        self.assertEqual(t.regs[0x24],0)
        t.write(0x10,2,0xFFFE)
        self.assertFalse(t.irq)

    def test_clock_gating_stops_counter(self):
        t=Timer('TIMER1',clock_enabled=lambda:False)
        t.write(0,2,1)
        t.advance(999999)
        self.assertEqual(t.regs[0x24],0)

    def test_unsupported_external_clock_mode_stops(self):
        t=Timer('TIMER1')
        t.write(0,2,1)
        t.write(8,2,7)
        with self.assertRaisesRegex(StopModel,'up-counting'):t.advance(10)


class BackupTests(unittest.TestCase):
    def test_backup_write_protection(self):
        b=BackupRtc(write_enabled=lambda:False)
        b.write(4,2,0x5050,True)
        self.assertEqual(b.read(4,2,True),0)

    def test_synchronization_and_write_completion(self):
        b=BackupRtc()
        b.write(4,2,0x10)
        b.write(12,2,0x7FFF)
        b.write(4,2,0)
        self.assertEqual(b.read(4,2)&0x28,0)
        b.read(4,2)
        self.assertEqual(b.read(4,2)&0x28,0x28)

    def test_counter_second_and_alarm_flags(self):
        b=BackupRtc()
        b.regs[12]=0x7FFF
        b.regs[32]=0
        b.regs[36]=1
        b.regs[0]=3
        b.advance(120000000)
        self.assertEqual(b.regs[28],1)
        self.assertEqual(b.regs[4]&3,3)
        self.assertTrue(b.irq)
        b.write(4,2,0x28)
        self.assertFalse(b.irq)

    def test_clock_stopped_and_configuration_freeze(self):
        b=BackupRtc(enabled=lambda:False)
        b.advance(120000000)
        self.assertEqual(b.regs[28],0)

    def test_counter_write_requires_configuration_mode(self):
        with self.assertRaisesRegex(StopModel,'configuration'):BackupRtc().write(28,2,1)


class LightingTests(unittest.TestCase):
    def frame(self,bus,address,value):
        bus.gpio(0x20,0,0,0,1)
        word=(address<<8)|value
        for bit in range(11,-1,-1):
            data=16 if word & (1<<bit) else 0
            bus.gpio(0,0,data,data|8,2)
            bus.gpio(0,0,data|8,data,3)
        bus.gpio(0,0x20,0,0,4)

    def test_brightness_is_decoded_from_twelve_gpio_edges(self):
        b=LightingBus()
        b.armed=True
        b.expected.append((8,128))
        self.frame(b,8,128)
        self.assertEqual(b.describe()['lcd_brightness'],128)
        self.assertEqual(b.crosschecks,1)

    def test_bus_mismatch_is_not_silently_accepted(self):
        b=LightingBus()
        b.armed=True
        b.expected.append((8,255))
        with self.assertRaisesRegex(StopModel,'disagrees'):self.frame(b,8,0)


if __name__=='__main__':unittest.main()
