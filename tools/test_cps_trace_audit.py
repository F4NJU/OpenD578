#!/usr/bin/env python3
"""Deterministic, synthetic, offline tests for cps_trace_audit.py."""
import json
from pathlib import Path
import tempfile
import unittest
from cps_trace_audit import audit


def request_write(addr, data):
    head = addr.to_bytes(4, 'big') + bytes([len(data)]) + data
    return b'W' + head + bytes([sum(head) & 255, 6])


def read_response(addr, data):
    head = addr.to_bytes(4, 'big') + bytes([len(data)]) + data
    return b'W' + head + bytes([sum(head) & 255, 6])


class TestCpsAudit(unittest.TestCase):
    def examine(self, packets):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'private.jsonl'
            p.write_text(''.join(json.dumps({'direction': direction, 'hex': data.hex()})+'\n'
                                 for direction, data in packets), encoding='utf-8')
            return audit(p)

    def test_full_split_sequence_without_payload(self):
        addr=0x00800000
        data=b'PRIVATE-CONTENTS'
        packets=[('CPS_to_firmware',b'PRO'),('CPS_to_firmware',b'GRAM'),
                 ('firmware_to_CPS',b'QX\x06'),('CPS_to_firmware',b'\x02'),
                 ('firmware_to_CPS',b'ID578UV\0'+bytes(7)+b'\x06'),
                 ('CPS_to_firmware',b'R'+addr.to_bytes(4,'big')+bytes([len(data)])),
                 ('firmware_to_CPS',read_response(addr,data)[:7]),
                 ('firmware_to_CPS',read_response(addr,data)[7:]),
                 ('CPS_to_firmware',request_write(addr,data)),
                 ('firmware_to_CPS',b'\x06'),
                 ('CPS_to_firmware',b'END'),('firmware_to_CPS',b'\x06')]
        r=self.examine(packets)
        self.assertEqual(r['warnings'],[])
        self.assertEqual(r['counts']['request_WRITE'],1)
        self.assertEqual(r['counts']['response_READ'],1)
        self.assertEqual(r['counts']['response_END'],1)
        self.assertTrue(next(e for e in r['events'] if e['type']=='response_READ')['checksum_ok'])
        self.assertNotIn('PRIVATE',json.dumps(r))
        self.assertFalse(r['contains_payload_bytes'])

    def test_bad_checksum_detected(self):
        addr=0x00800010
        bad=bytearray(read_response(addr,b'0123456789ABCDEF'))
        bad[-2] ^= 1
        r=self.examine([('CPS_to_firmware',b'R'+addr.to_bytes(4,'big')+b'\x10'),
                        ('firmware_to_CPS',bytes(bad))])
        self.assertFalse(r['events'][-1]['checksum_ok'])
        self.assertGreater(r['counts']['warnings'],0)

    def test_truncation_detected(self):
        r=self.examine([('CPS_to_firmware',b'R\x00\x80')])
        self.assertGreater(r['counts']['warnings'],0)

    def test_invalid_json(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad.jsonl';p.write_text('{\n',encoding='utf-8')
            r=audit(p)
            self.assertGreater(r['counts']['warnings'],0)


if __name__=='__main__':unittest.main()
