import struct,unittest
from usb_cdc import CdcHost,cdc_configuration
import test_hardware_extended as hardware
from cps_bridge import relay_step,Client
from types import SimpleNamespace

# An original fixture with different interface numbers/endpoints from the D578.
CONFIG=bytes.fromhex('090243000201008032090402000102020100052400100105240100030424020205240602030705860308000a09040300020a0000000705040240000007058502400000')
class CdcTests(unittest.TestCase):
    def test_configuration_is_discovered_not_hardcoded(self):
        d=cdc_configuration(CONFIG);self.assertEqual((d['control_interface'],d['data_interface'],d['bulk_in'],d['bulk_out']),(2,3,0x85,4))
        with self.assertRaises(ValueError):cdc_configuration(CONFIG[:-1])
        with self.assertRaises(ValueError):cdc_configuration(bytes(67))
    def test_multi_packet_control_reads_exact_firmware_bytes(self):
        u=hardware.UsbHostTests().ready();h=CdcHost(u);h.state='enumerating';h.ep0_size=64
        h.request('fixture',0x80,6,0x200,0,67)
        h.tick(1);self.assertEqual(h.control['stage'],'in')
        # Firmware acknowledges SETUP, then fills TX PMA in two packets.
        u.regs[0]&=~0x8800
        for n,chunk in enumerate((CONFIG[:64],CONFIG[64:])):
            u.table(0,0,128);u.table(0,2,len(chunk));u.packet_bytes(128,len(chunk),chunk)
            u.regs[0]=(u.regs[0]&~0xB0)|0x30
            h.tick((n+1)*4096)
        self.assertEqual(bytes(h.control['data']),CONFIG);self.assertEqual(h.control['stage'],'status_out')
        u.regs[0]=(u.regs[0]&~0x3000)|0x3000;h.tick(12288)
        self.assertIsNone(h.control)
    def test_bulk_bytes_are_read_from_firmware_PMA_with_backpressure(self):
        u=hardware.UsbHostTests().ready();h=CdcHost(u);h.state='ready';h.layout=cdc_configuration(CONFIG)
        u.regs[4]=0x3004;u.table(1,4,192);u.table(1,6,0x8400)
        h.queue(b'PROGRAM');h.tick(1)
        self.assertEqual(u.packet_bytes(192,7),b'PROGRAM');self.assertEqual(h.sent_total,7)
        h.tick(4096);self.assertEqual(h.received_total,0) # no invented ACK
        u.regs[8]=0x0035;u.table(2,0,256);u.table(2,2,3);u.packet_bytes(256,3,b'QX\x06')
        h.tick(8192)
        self.assertEqual(h.received,b'QX\x06')
        # Subsequent INs NAK until the firmware rearms the endpoint.
        h.tick(12288);self.assertEqual(h.received_total,3)
    def test_bridge_preserves_partial_serial_writes(self):
        received=[b'abcdef',b''];sent=[];written=[]
        client=SimpleNamespace(write=lambda data:sent.append(data),read=lambda:received.pop(0))
        port=SimpleNamespace(read=lambda:b'PROGRAM',write=lambda data:written.append(bytes(data[:2])) or 2)
        pending=bytearray();relay_step(client,port,pending);relay_step(client,port,pending)
        self.assertEqual(b''.join(written),b'abcd');self.assertEqual(pending,b'ef')
        self.assertEqual(sent,[b'PROGRAM',b'PROGRAM'])
    def test_bridge_refuses_remote_endpoint(self):
        for url in ['https://example.com','http://example.com','http://user:password@localhost:8765']:
            with self.assertRaises(ValueError):Client(url)
    def test_bridge_detects_receive_overrun_and_session_replacement(self):
        client=Client.__new__(Client);client.session='old';client.cursor=0
        client.get=lambda path:dict(session='new',state='ready')
        with self.assertRaisesRegex(RuntimeError,'session stopped or changed'):client.read()
        client.get=lambda path:dict(session='old',state='ready',received_base=10)
        with self.assertRaisesRegex(RuntimeError,'receive overflow'):client.read()
    def test_probe_rejects_corrupted_read_checksum(self):
        from cps_probe import check_read
        frame=b'W'+bytes.fromhex('0080000010')+bytes(range(16));frame+=bytes([sum(frame[1:])&255,6])
        self.assertEqual(check_read(frame,0x00800000),bytes(range(16)))
        with self.assertRaisesRegex(ValueError,'checksum'):check_read(frame[:-2]+b'\0\x06',0x00800000)

if __name__=='__main__':unittest.main()
