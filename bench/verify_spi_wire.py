#!/usr/bin/env python3
"""Exercise command bytes and single/dual response bits against real captures."""
import argparse
import json
from pathlib import Path
from emulate_nand_v121 import CapturedNand


class HostWire:
    def __init__(self, nand):
        self.nand = nand
        self.levels = 0x8100
        self.nand.drive(self.levels, 0xC100)

    def set(self, mask, value):
        self.levels = (self.levels & ~mask) | (value & mask)
        self.nand.drive(self.levels, mask)

    def begin(self):
        self.set(0x100, 0)

    def end(self):
        self.set(0x100, 0x100)

    def send(self, data):
        for byte in data:
            for bit in range(7, -1, -1):
                self.set(0xC000, ((byte >> bit) & 1) << 14)
                self.set(0x8000, 0x8000)

    def receive(self, count, dual=False):
        data = bytearray()
        for _ in range(count):
            byte = 0
            for _ in range(4 if dual else 8):
                self.set(0x8000, 0)
                if dual:
                    byte = (byte << 2) | (self.nand.miso << 1) | self.nand.io0
                else:
                    byte = (byte << 1) | self.nand.miso
                self.set(0x8000, 0x8000)
            data.append(byte)
        return bytes(data)

    def transaction(self, command, receive=0, dual=False):
        self.begin()
        self.send(command)
        result = self.receive(receive, dual)
        self.end()
        return result


def verify(directory):
    checks = []
    for idle in (0, 1):
        nand = CapturedNand(directory, idle_miso=idle)
        wire = HostWire(nand)
        assert wire.transaction(bytes([0x9F, 0]), 2) == bytes.fromhex('98 cb')
        checks.append(f'JEDEC_98CB_idle_{idle}')
        assert wire.transaction(bytes([0x0F, 0xB0]), 1) == bytes([0x16])
        checks.append(f'captured_feature_B0_idle_{idle}')
        for row in (0, 63, 192, 19008, 24512):
            wire.transaction(bytes([0x13]) + row.to_bytes(3, 'big'))
            busy = wire.transaction(bytes([0x0F, 0xC0]), 1)[0]
            ready = wire.transaction(bytes([0x0F, 0xC0]), 1)[0]
            assert busy & 1 and not ready & 1
            assert ready & 0x30 == nand.images['nand_ecc_status_128KiB.bin'][row] & 0x30
            column = 1792 if row == 63 else 0
            expected = nand.images['nand_main_256MiB.bin'][row * 2048 + column:row * 2048 + column + 128]
            prefix = column.to_bytes(2, 'big') + bytes(1)
            assert wire.transaction(bytes([0x03]) + prefix, 128) == expected
            assert wire.transaction(bytes([0x3B]) + prefix, 128, dual=True) == expected
            checks.append(f'page_{row}_busy_ECC_single_dual_idle_{idle}')
        # Read the captured 64 auxiliary bytes as well as the end of main data.
        wire.transaction(bytes([0x13, 0, 0, 0]))
        for _ in range(2):
            wire.transaction(bytes([0x0F, 0xC0]), 1)
        expected = nand.images['nand_main_256MiB.bin'][2040:2048] + nand.images['nand_oob64_8MiB.bin'][:64]
        assert wire.transaction(bytes.fromhex('3b 07 f8 00'), 72, dual=True) == expected
        checks.append(f'main_to_OOB_boundary_idle_{idle}')
    return dict(passed=True, checks=checks, count=len(checks))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('nand_directory', type=Path)
    p.add_argument('--out', type=Path, default=Path('verification_spi_wire.json'))
    a = p.parse_args()
    result = verify(a.nand_directory)
    a.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
