import unittest,tempfile,struct
from pathlib import Path
from lab_inputs import nmea,gps_sentences,microphone_frame,validate_keys
from firmware_input import inspect_image,validate_vectors

class LaboratoryInputs(unittest.TestCase):
    def test_published_RMC_checksum(self):
        body='GPRMC,083559.00,A,4717.11437,N,00833.91522,E,0.004,77.52,091202,,,A'
        self.assertEqual(nmea(body),('$'+body+'*57\r\n').encode())
        self.assertEqual(nmea('PMTK010,001'),b'$PMTK010,001*2E\r\n')
    def test_GPS_loss_and_acquisition_are_wire_stimuli(self):
        good=gps_sentences();bad=gps_sentences(fix=False)
        self.assertIn(b',A,4800.0000,N,00200.0000,E,',good)
        self.assertIn(b',V,4800.0000,N,00200.0000,E,',bad)
        self.assertIn(b',0,00,1.0,',bad)
        self.assertEqual(good.count(b'\r\n'),3)
    def test_GPS_out_of_range_and_nonfinite_rejected(self):
        for lat,lon in [(91,0),(0,181),(float('nan'),0)]:
            with self.assertRaises(ValueError):gps_sentences(lat,lon)
    def test_PTT_and_UP_preserved_in_same_captured_frame(self):
        self.assertEqual(microphone_frame(['PTT','UP']),bytes.fromhex('41 01 01 00 10 00 00 06'))
        self.assertEqual(microphone_frame([],last_code=16),bytes.fromhex('41 00 00 00 10 00 00 06'))
    def test_long_A_captured_frame(self):
        self.assertEqual(microphone_frame(['A'],True),bytes.fromhex('41 00 01 01 1A 00 00 06'))
    def test_unsupported_electrical_chord_rejected(self):
        with self.assertRaises(ValueError):validate_keys(['P1','P2'])
        self.assertEqual(validate_keys(['P2','P5','DIAL_PUSH','POWER']),{'P2','P5','DIAL_PUSH','POWER'})
        with self.assertRaises(ValueError):microphone_frame(['UP','DOWN'])
    def test_selected_firmware_vectors_and_hash(self):
        image=bytearray(512);struct.pack_into('<II',image,0,0x200170E0,0x08006021)
        image[0x20:0x22]=b'\xfe\xe7'
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/'test.bin';file.write_bytes(image)
            data,app,meta=inspect_image(file)
            self.assertEqual(data,app);self.assertEqual(meta['reset_entry'],'0x8006021')
            self.assertFalse(meta['source_modified']);self.assertEqual(file.read_bytes(),image)
        struct.pack_into('<I',image,0,0x30000000)
        with self.assertRaises(ValueError):validate_vectors(image,0x08006000)
if __name__=='__main__':unittest.main()
