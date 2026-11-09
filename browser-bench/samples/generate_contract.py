#!/usr/bin/env python3
"""Rebuild GPL-3.0-or-later synthetic test binaries; contains no OEM instructions."""
from pathlib import Path
from struct import pack

HERE = Path(__file__).resolve().parent


def image(sp: int, pc: int, halfwords: list[int], constants: list[int]) -> bytes:
    return pack('<II', sp, pc) + b''.join(pack('<H', h) for h in halfwords) + b''.join(pack('<I', c) for c in constants)


# Application at 0x08006000:
#   MOVS R0,#42; LDR R1,[PC,#4]; STR R0,[R1]; BKPT #0
#   .word 0x20000000
app = image(0x20018000, 0x08006009, [0x202A, 0x4901, 0x6008, 0xBE00], [0x20000000])
assert len(app) == 20
(HERE / 'contract_thumb16.bin').write_bytes(app)

# Bootloader at 0x08000000:
#   LDR R0,[PC,#4]; BX R0; NOP; NOP
#   .word 0x08006009  # application reset vector
boot = image(0x20018000, 0x08000009, [0x4801, 0x4700, 0xBF00, 0xBF00], [0x08006009])
assert len(boot) == 20
(HERE / 'boot_jump_demo.bin').write_bytes(boot)
print('Synthetic images generated; app and bootloader: 20 bytes each')
