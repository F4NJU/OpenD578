#!/usr/bin/env python3
"""Offline V1.21 startup execution. Does not model a functioning D578 radio."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

import unicorn
from unicorn import (Uc, UcError, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS,
                     UC_PROT_READ, UC_PROT_EXEC, UC_HOOK_CODE, UC_HOOK_MEM_INVALID)
from unicorn.arm_const import (UC_CPU_ARM_CORTEX_M4, UC_ARM_REG_SP,
                              UC_ARM_REG_XPSR, UC_ARM_REG_PC,
                              UC_ARM_REG_R0, UC_ARM_REG_R1,
                              UC_ARM_REG_R2, UC_ARM_REG_R3)

APP = 0x08006000
RAM = 0x20000000
RAM_SIZE = 0x18000
EXPECTED_SHA = '02b2a3b56bd57c7ada581eb52b9b6f41c5d51aaec1b068d37585efd58dff9c9a'


def hx(n):
    return f'0x{n:08X}'


def require(condition, explanation):
    if not condition:
        raise ValueError(explanation)


def read32(image, address):
    return struct.unpack_from('<I', image, address - APP)[0]


def scatter_table(image):
    # ADR at 0x08006138 points to relative bounds at 0x08006164.
    anchor = 0x08006164
    start = anchor + read32(image, anchor)
    end = anchor + read32(image, anchor + 4)
    require((start, end) == (0x080FE678, 0x080FE698), 'Unexpected scatter bounds')
    rows = []
    for address in range(start, end, 16):
        source, target, size, handler = struct.unpack_from('<4I', image, address - APP)
        require(RAM <= target <= target + size <= RAM + RAM_SIZE, 'Scatter outside SRAM')
        rows.append(dict(table_entry=hx(address), source=hx(source), target=hx(target),
                         end_exclusive=hx(target + size), bytes=size, handler=hx(handler)))
    return rows


def decode_initialized_data(image, source, expected_size):
    """Independent translation of the OEM decoder at 0x0800616C."""
    pos = source - APP
    initial_pos = pos
    output = bytearray()
    while len(output) < expected_size:
        control = image[pos]
        pos += 1
        literals = control & 7
        if literals == 0:
            literals = image[pos]
            pos += 1
        run = control >> 4
        if run == 0:
            run = image[pos]
            pos += 1
        require(literals > 0, 'Invalid literal length')
        output.extend(image[pos:pos + literals - 1])
        pos += literals - 1
        if control & 8:
            distance = image[pos]
            pos += 1
            require(0 < distance <= len(output), 'Invalid back reference')
            for _ in range(run + 2):
                output.append(output[-distance])
        else:
            output.extend(bytes(run))
        require(len(output) <= expected_size, 'Decompression exceeds region')
    return bytes(output), pos - initial_pos


def make_cpu(image, poison):
    cpu = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)
    cpu.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_M4)
    cpu.mem_map(0x08000000, 0x300000, UC_PROT_READ | UC_PROT_EXEC)
    cpu.mem_write(APP, image)
    # Only the authenticated CDD range contains loaded executable bytes.
    # No peripheral address space, NVIC, timers or DMA is provided.
    cpu.mem_map(RAM, RAM_SIZE)
    cpu.mem_write(RAM, bytes([poison]) * RAM_SIZE)
    cpu.reg_write(UC_ARM_REG_SP, read32(image, APP))
    cpu.reg_write(UC_ARM_REG_XPSR, 0x01000000)
    return cpu


def execute(image, mode, poison):
    cpu = make_cpu(image, poison)
    steps = 0
    pcs = set()
    lowest_sp = read32(image, APP)
    violations = []
    checkpoints = []
    points = {0x0800620C, 0x08006216, 0x08006654}

    def on_code(uc, address, size, _):
        nonlocal steps, lowest_sp
        steps += 1
        pcs.add(address)
        lowest_sp = min(lowest_sp, uc.reg_read(UC_ARM_REG_SP))
        if address in points:
            checkpoints.append(dict(pc=hx(address), sp=hx(uc.reg_read(UC_ARM_REG_SP))))
        if not APP <= address < APP + len(image):
            violations.append(dict(kind='execution_outside_authenticated_CDD', address=hx(address)))
            uc.emu_stop()

    def on_invalid(uc, access, address, size, value, _):
        violations.append(dict(access=access, address=hx(address), size=size,
                               pc=hx(uc.reg_read(UC_ARM_REG_PC))))
        return False

    # Deliberately no UC_HOOK_MEM_WRITE: on this host Unicorn 2.1.4 with
    # that hook diverged in the OEM Thumb IT/zero-fill decoder. CPU-only
    # hooks plus two poisons and an independent decoder validate this path.
    cpu.hook_add(UC_HOOK_CODE, on_code)
    cpu.hook_add(UC_HOOK_MEM_INVALID, on_invalid)
    start = read32(image, APP + 4) if mode == 'reset_strict' else 0x08006131
    end = 0x0800620C if mode == 'scatter_only' else 0
    status = 'stopped'
    try:
        cpu.emu_start(start, end, count=2_000_000, timeout=10_000_000)
    except UcError as error:
        status = str(error)
    info = dict(mode=mode, poison=hx(poison), status=status,
                end_pc=hx(cpu.reg_read(UC_ARM_REG_PC)), instructions_observed=steps,
                unique_instruction_addresses=len(pcs), minimum_observed_sp=hx(lowest_sp),
                peripheral_or_unmapped_access=violations, checkpoints=checkpoints,
                skip_SystemInit=(mode != 'reset_strict'),
                full_radio_emulated=False)
    return info, bytes(cpu.mem_read(RAM, RAM_SIZE))


def scan_high_literal_loads(image):
    """Conservative halfword candidate scan, NOT control-flow proof."""
    loads = []
    movt = []
    for offset in range(0, len(image) - 3, 2):
        h, h2 = struct.unpack_from('<HH', image, offset)
        address = APP + offset
        pointer = None
        if h & 0xF800 == 0x4800:
            pointer = ((address + 4) & ~3) + (h & 255) * 4
        elif h & 0xFF7F == 0xF85F:
            pointer = ((address + 4) & ~3) + (1 if h & 128 else -1) * (h2 & 4095)
        if pointer is not None and APP <= pointer <= APP + len(image) - 4:
            value = read32(image, pointer)
            if 0x200170E0 <= value <= 0x20018000:
                loads.append(dict(instruction=hx(address), literal=hx(pointer), value=hx(value)))
        if h & 0xFBF0 == 0xF2C0 and not h2 & 0x8000:
            imm = ((h & 15) << 12) | (((h >> 10) & 1) << 11) | (((h2 >> 12) & 7) << 8) | (h2 & 255)
            if imm in (0x2000, 0x2001):
                movt.append(dict(instruction=hx(address), upper_immediate=hx(imm)))
    return dict(candidate_LDR_literal=loads, candidate_MOVT_SRAM_upper=movt,
                limitation='Does not exclude computed pointers, indirect loads, DMA or other images')


def stackheap_registers(image):
    cpu = make_cpu(image, 0xA5)
    cpu.emu_start(0x08006D55, 0x08006D5C, count=10)
    values = [cpu.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)]
    require(values == [0x20016AE0, 0x200170E0, 0x20016CE0, 0x20016CE0], 'Unexpected stackheap ABI')
    return dict(zip(('r0_heap_base', 'r1_initial_stack_top', 'r2_heap_end', 'r3_stack_region_bottom'), map(hx, values)))


def audit(image):
    digest = hashlib.sha256(image).hexdigest()
    require(digest == EXPECTED_SHA, 'Requires the exact unmodified official GD32 V1.21 CDD')
    rows = scatter_table(image)
    require([r['bytes'] for r in rows] == [6872, 87560], 'Unexpected region sizes')
    initialized, consumed = decode_initialized_data(image, int(rows[0]['source'], 16), rows[0]['bytes'])
    expected = initialized + bytes(rows[1]['bytes'])
    result = dict(firmware_sha256=digest, firmware_bytes=len(image), firmware='D578UV PRO GD32 V1.21 official',
                  emulator=dict(name='Unicorn', version=unicorn.__version__, cpu='Cortex-M4',
                                peripherals=False, interrupts=False, DMA=False),
                  sram_capacity_bytes=RAM_SIZE, scatter=rows,
                  initialized_bytes=len(expected), initialized_percent=100 * len(expected) / RAM_SIZE,
                  outside_scatter_bytes=RAM_SIZE - len(expected),
                  outside_scatter_start=hx(RAM + len(expected)), outside_scatter_end_exclusive=hx(RAM + RAM_SIZE),
                  outside_scatter_proven_free=False,
                  independent_decoder=dict(output_bytes=len(initialized), compressed_bytes_consumed=consumed,
                                           output_sha256=hashlib.sha256(initialized).hexdigest()),
                  stackheap_abi=stackheap_registers(image),
                  declared_C_heap_bytes=512, declared_startup_stack_region_bytes=1024,
                  stackheap_note='Included in scatter ZI; not total RTOS heap/stack usage; r3 is not a hardware guard',
                  high_SRAM_scan=scan_high_literal_loads(image), scenarios=[])
    for mode in ('reset_strict', 'scatter_only', 'crt_until_mmio'):
        states = []
        for poison in (0xA5, 0x5A):
            info, state = execute(image, mode, poison)
            result['scenarios'].append(info)
            states.append(state)
            if mode == 'scatter_only':
                require(info['end_pc'] == hx(0x0800620C), 'Scatter emulation did not finish')
                require(state[:len(expected)] == expected, 'Emulator differs from independent decoder/zero-fill')
            if mode != 'reset_strict':
                require(state[len(expected):] == bytes([poison]) * (RAM_SIZE - len(expected)),
                        'High SRAM unexpectedly changed')
            if mode == 'reset_strict':
                require(info['end_pc'] == hx(0x08006344), 'Unexpected reset stopping point')
            elif mode == 'crt_until_mmio':
                require(info['end_pc'] == hx(0x08008A82), 'Unexpected C runtime stopping point')
        if mode != 'reset_strict':
            require(states[0][:len(expected)] == states[1][:len(expected)], 'Startup depends on poison')
    result['correction_of_prior_raw_byte_matches'] = [
        dict(raw_value='0x20017801', example_address='0x08087248', actual_instructions=['ldrb r1, [r0]', 'movs r0, #1']),
        dict(raw_value='0x20017904', example_address='0x080A4A08', actual_instructions=['ldrb r4, [r0, #4]', 'movs r0, #1']),
        dict(raw_value='0x20017F21', example_address='0x080AD978', actual_instructions=['ldrb r1, [r4, #0x1c]', 'movs r0, #1'])]
    result['runtime_RAM_occupation_measured'] = False
    result['conclusion'] = 'Startup allocation confirmed; live RF/UI/APRS/DMR/RTOS maxima and high-SRAM availability are unmeasured.'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('firmware', type=Path, help='Unmodified official GD32 V1.21 CDD')
    parser.add_argument('--out', type=Path, default=Path('resultats_ram_v121.json'))
    args = parser.parse_args()
    result = audit(args.firmware.read_bytes())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({k: result[k] for k in ('initialized_bytes', 'initialized_percent',
                                            'outside_scatter_bytes', 'outside_scatter_proven_free',
                                            'runtime_RAM_occupation_measured')}, indent=2))
    print('Six startup executions and independent decoder comparison passed.')


if __name__ == '__main__':
    main()
