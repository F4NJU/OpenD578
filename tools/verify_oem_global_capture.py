"""Independently verify a private global USB capture against the published V1.21 map.

No device access. Outputs aggregate evidence only, never names or frequencies.
The XML reference remains external and its exact SHA256 is enforced.
"""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

XML_SHA256 = '4b3e4efb52d43d5ae5e79b318e33bb689d8115d23ccc3c3feb3e448592ff4b7a'


def verify(capture, reference, qualification):
    xml = Path(reference).read_bytes()
    if hashlib.sha256(xml).hexdigest() != XML_SHA256:
        raise ValueError('Unexpected XML reference version')
    root = ET.fromstring(xml)
    enum = next(e for e in root.find('repeat/repeat/element').iter('enum')
                if e.findtext('meta/name') == 'TX Tone CTCSS')
    tones = {int(item.attrib['value']): round(float(item.findtext('name').split()[0]) * 10)
             for item in enum.findall('item') if item.findtext('name') != 'Custom'}
    exported = json.loads(Path(capture).read_text())
    if exported['received_base'] != 0:
        raise ValueError('USB capture overflowed: complete session required')
    wire = bytes.fromhex(exported['received_hex'])
    if wire[:3] != b'QX\x06' or wire[3:11] != b'ID578UV\0' or wire[18] != 6:
        raise ValueError('Invalid PROGRAM/identity replies')
    cursor, frames = 19, 0

    def read(address):
        nonlocal cursor, frames
        packet = wire[cursor:cursor + 24]
        cursor += 24
        if (len(packet) != 24 or packet[0] != 87 or int.from_bytes(packet[1:5], 'big') != address
                or packet[5] != 16 or packet[23] != 6 or sum(packet[1:22]) % 256 != packet[22]):
            raise ValueError('Invalid observed read reply')
        frames += 1
        return packet[6:22]

    bitmap = b''.join(read(0x024c1500 + offset) for offset in range(0, 512, 16))
    active = [i for i in range(4000) if bitmap[i // 8] & (1 << (i % 8))]

    def tone(record, rx):
        mode = (record[9] >> (0 if rx else 2)) & 3
        index = record[11 if rx else 10]
        if mode == 0:
            return {'kind': 'none'}
        if mode == 1:
            value = int.from_bytes(record[16:18], 'little') if index == 51 else tones.get(index)
            if value is not None and 600 <= value <= 2600:
                return {'kind': 'ctcss', 'deciHz': value}
        offset = 14 if rx else 12
        word = int.from_bytes(record[offset:offset + 2], 'little')
        if mode == 2 and word < 1024:
            return {'kind': 'dcs', 'code': format(word % 512, '03o'), 'inverted': word >= 512}
        return {'kind': 'unknown', 'rawMode': mode, 'rawValue': index if mode == 1 else word}

    def bcd(value):
        digits = value.hex()
        return int(digits) * 10 if digits.isdecimal() and int(digits) else None

    slots = []
    counts = {'rx': {}, 'tx': {}}
    for index in active:
        base = 0x00800000 + index // 128 * 0x40000 + index % 128 * 64
        record = b''.join(read(base + offset) for offset in range(0, 64, 16))
        name = record[35:51].split(b'\0')[0]
        rx = bcd(record[:4])
        offset = 0 if record[4:8] == b'\0' * 4 else bcd(record[4:8])
        shift = record[8] >> 6
        tx = None if rx is None or offset is None or shift == 3 else rx + (0 if shift == 0 else offset if shift == 1 else -offset)
        item = dict(slot=index + 1, name=name.decode('ascii') if name and all(32 <= b <= 126 for b in name) else None,
                    rxHz=rx, txHz=tx if tx is not None and tx > 0 else None,
                    mode=['FM', 'DMR', 'FM + DMR RX', 'DMR + FM RX'][record[8] & 3],
                    power=['Low', 'Mid', 'High', 'Turbo'][(record[8] >> 2) & 3],
                    rxTone=tone(record, True), txTone=tone(record, False))
        for direction in ('rx', 'tx'):
            kind = item[direction + 'Tone']['kind']
            counts[direction][kind] = counts[direction].get(kind, 0) + 1
        slots.append(item)
    if wire[cursor:] != b'\x06':
        raise ValueError('Final END ACK missing or unexpected trailing replies')
    digest = hashlib.sha256(json.dumps(slots, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
    expected = json.loads(Path(qualification).read_text())
    if digest != expected['slotSnapshotSha256'] or counts != expected['tones']:
        raise ValueError('Independent decoding differs from TypeScript result')
    return dict(passed=True, activeChannels=len(slots), maxSlot=max(active, default=-1) + 1,
                banksRead=sorted({index // 128 for index in active}), verifiedReadReplies=frames,
                tones=counts, slotSnapshotSha256=digest, referenceSha256=XML_SHA256)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('capture', 'reference', 'qualification', 'report'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.capture, args.reference, args.qualification)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result))
