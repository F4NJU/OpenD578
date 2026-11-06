import unittest
from audit_bluetooth_strings import scan
from decode_bt_uart import parse_hex,decode_payload

class BluetoothResearchTests(unittest.TestCase):
    def test_scan_ascii_and_utf16(self):
        image=b'\x00'*8+b'AT+VER?'+b'\x00'*8+'Bluetooth'.encode('utf-16le')
        found=scan(image,0x08006000,('AT+VER?','Bluetooth'))
        self.assertEqual([(v['token'],v['encoding']) for v in found],
                        [('AT+VER?','ascii'),('Bluetooth','utf16le')])
        self.assertEqual(found[0]['address'],'0x08006008')
    def test_frames(self):
        d=parse_hex('41 54 2B 56 45 52 3F 0d 0a')
        self.assertEqual(decode_payload(d)[0]['meaning'],'Requete de version ET12')
    def test_incomplete(self):
        out=decode_payload(b'AT+AGHF=1')
        self.assertFalse(out[0]['complete_crlf'])
    def test_unknown_never_gets_ok(self):
        self.assertIn('NON DECODE',decode_payload(b'AT+UNRECOGNIZED\r\n')[0]['meaning'])
    def test_invalid_hex(self):
        with self.assertRaises(ValueError):parse_hex('41 ?0')

if __name__=='__main__':unittest.main()
