import unittest
from fm_i2c import FmI2c
from sct_hpi import SctHpi
from emulate_clock_v121 import StopModel
from emulate_clock_v121 import ClockModel
from usbd_idle import UsbdIdle
from rf_spi import RfSpi


class ExternalBusTests(unittest.TestCase):
    def test_APRS_control_readback_requires_exact_bank_page_and_prior_write(self):
        rf=RfSpi();rf.control_readback_keys={(0,1,0x17)}
        rf.bank=0;rf.pages[0]=1;rf.command=0x97
        with self.assertRaises(StopModel):rf.prepare_read()
        rf.registers[0,1,0x17]=0x03B8
        with self.assertRaises(StopModel):rf.prepare_read()
        rf.written.add((0,1,0x17));rf.prepare_read()
        self.assertEqual(rf.read_value,0x03B8)
        rf.pages[0]=0;rf.registers[0,0,0x17]=0x1234;rf.written.add((0,0,0x17))
        with self.assertRaises(StopModel):rf.prepare_read()

    def send_i2c(self,device,values):
        level=0xC0
        def drive(new):
            nonlocal level
            device.gpio(level,new,3,3,0)
            level=new
        drive(0x80)
        drive(0)
        acks=[]
        for value in values:
            for bit in range(7,-1,-1):
                data=0x40 if value&(1<<bit) else 0
                drive(data);drive(data|0x80);drive(data)
            drive(0x40);drive(0xC0)
            acks.append(device.input_bit())
            drive(0x40)
        drive(0);drive(0x80);drive(0xC0)
        return acks

    def test_fm_only_known_address_acknowledges(self):
        fm=FmI2c()
        self.assertEqual(self.send_i2c(fm,[0x6A]),[1])
        self.assertEqual(fm.absent_addresses,{0x35:1})
        self.assertEqual(self.send_i2c(fm,[0x20,0x80,0]),[0,0,0])
        self.assertEqual(fm.registers[2],0x8000)
        self.assertEqual(fm.frames[0]['payload'],[0x80,0])

    def test_fm_status_is_not_invented(self):
        with self.assertRaisesRegex(StopModel,'status read'):
            self.send_i2c(FmI2c(),[0x21])

    def test_sct_boot_is_checked_and_fifo_status_tracks_reads(self):
        sct=SctHpi()
        sct.start_boot(b'\x12\x34')
        sct.gpio(4,0,0x33333333)
        sct.gpio(0x1200,0x1208,0x33333333)
        sct.gpio(0x3400,0x3408,0x33333333)
        self.assertTrue(sct.boot_complete)
        self.assertEqual(sct.status(),0)
        actual=[]
        for unused in range(8):
            sct.gpio(0x18,8,0x88888888)
            actual.append(sct.input_data()>>8)
            sct.gpio(8,0x18,0x88888888)
        self.assertEqual(bytes(actual),bytes.fromhex('84 a9 61 00 02 20 17 01'))
        self.assertEqual(sct.status(),0x20)
        with self.assertRaisesRegex(StopModel,'empty output FIFO'):
            sct.gpio(0x18,8,0x88888888)

    def test_sct_corrupt_boot_stops(self):
        sct=SctHpi();sct.start_boot(b'\x12\x34')
        with self.assertRaisesRegex(StopModel,'differs from OEM'):
            sct.gpio(0x1100,0x1108,0x33333333)

    def test_sct_unknown_packet_stops(self):
        sct=SctHpi();sct.start_boot(b'\x00');sct.write_byte(0)
        with self.assertRaisesRegex(StopModel,'outside qualified'):
            for byte in bytes.fromhex('84 a9 61 00 01 23 32 00'):sct.write_byte(byte)

    def test_sct_configuration_requires_known_field_and_valid_length(self):
        sct=SctHpi()
        sct.process_packet(bytes.fromhex('84a9610002002d01'))
        self.assertEqual(sct.controls[0x2D],b'\x01')
        self.assertEqual(bytes(sct.rx),bytes.fromhex('84a9610002002d00'))
        with self.assertRaisesRegex(StopModel,'outside qualified'):
            sct.process_packet(bytes.fromhex('84a9610003002d0102'))

    def test_sct_codec_bypass_tracks_pages(self):
        sct=SctHpi();sct.controls[0x2D]=b'\x01'
        sct.process_packet(bytes.fromhex('84a961000640000112080000'))
        self.assertEqual(sct.codec_writes[1],dict(page=1,register=0x12,value=8))
        self.assertEqual(sct.codec_page,0)

    def test_irc48_readonly_calibration_and_ready(self):
        clock=ClockModel()
        self.assertEqual(clock.read_word(0xC0),0x80000000)
        clock.write_word(0xC0,0xFF030001)
        self.assertEqual(clock.read_word(0xC0),0x80030001)
        clock.write_word(0xC0,0)
        self.assertEqual(clock.read_word(0xC0),0x80000000)

    def test_usb_host_absent_does_not_create_received_packets(self):
        usb=UsbdIdle()
        usb.write(0x40,4,1);usb.write(0x40,4,0xFF00)
        usb.write(0x44,4,0xFFFF)
        self.assertEqual(usb.read(0x44,4),0)
        usb.write(0,4,0x0030)
        self.assertEqual(usb.read(0,4),0x30)
        usb.write(0,4,0x0010)
        self.assertEqual(usb.read(0,4),0x20)
        usb.memory_write(4,4,0x1234)
        self.assertEqual(usb.memory_read(4,4),0x1234)


if __name__=='__main__':unittest.main()
