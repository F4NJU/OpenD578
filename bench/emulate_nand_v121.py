#!/usr/bin/env python3
"""D578 GPIO-level SPI NAND emulator backed by the captured device image."""
import argparse
import hashlib
import json
import mmap
import struct
import time
from collections import Counter
from pathlib import Path

from emulate_clock_v121 import Runner, StopModel
from audit_ram_v121 import APP, RAM, RAM_SIZE, EXPECTED_SHA, hx, require, read32
from unicorn import UcError, UC_HOOK_INTR
from unicorn.arm_const import (UC_ARM_REG_PC, UC_ARM_REG_SP, UC_ARM_REG_R0,
    UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_R5,
    UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10,
    UC_ARM_REG_R11, UC_ARM_REG_R12, UC_ARM_REG_LR, UC_ARM_REG_XPSR,
    UC_ARM_REG_MSP, UC_ARM_REG_PSP, UC_ARM_REG_CONTROL, UC_ARM_REG_IPSR,
    UC_ARM_REG_PRIMASK, UC_ARM_REG_BASEPRI, UC_ARM_REG_FAULTMASK)

EXPECTED_FILES = {
    'nand_main_256MiB.bin': (268435456, '329d22165d234bf0df043e62af11397dea96327925b9db18f3c354230ff40945'),
    'nand_oob64_8MiB.bin': (8388608, '9a999b9fd13a02b45ed4d38e68f9e9c7d1095994c751e36e04f4a62b2e4c5106'),
    'nand_ecc_status_128KiB.bin': (131072, 'b40ebd3ebc3923f01d9d98a52a3b019b65785641ba76687127678b788ea793c6'),
}


class CapturedNand:
    def __init__(self, directory, idle_miso=1, busy_polls=1, verify=True):
        self.sources = {}
        self.handles = []
        self.images = {}
        for name, (size, expected) in EXPECTED_FILES.items():
            path = Path(directory) / name
            require(path.stat().st_size == size, f'Wrong size: {name}')
            handle = path.open('rb')
            digest = hashlib.file_digest(handle, 'sha256').hexdigest() if verify else expected
            require(digest == expected, f'Wrong SHA256: {name}')
            handle.seek(0)
            self.handles.append(handle)
            self.images[name] = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ)
            self.sources[name] = dict(bytes=size, sha256=digest)
        self.idle = idle_miso & 1
        self.busy_polls = busy_polls
        self.features = {0xA0: 0x38, 0xB0: 0x16}
        self.status = 0
        self.pending_busy = 0
        self.cached_page = None
        self.cache = None
        self.cs, self.clk, self.mosi, self.miso = 1, 0, 0, self.idle
        self.io0 = self.idle
        self.input_bits = 0
        self.accumulator = 0
        self.input_bytes = []
        self.outputs = {}
        self.transactions = []
        self.opcodes = Counter()
        self.pages = Counter()
        self.feature_reads = Counter()
        self.read_bytes = 0
        self.array_writes = []

    def feature(self, address):
        self.feature_reads[address] += 1
        if address == 0xC0:
            value = self.status
            if self.pending_busy:
                value |= 1
                self.pending_busy -= 1
            return value
        if address not in self.features:
            raise StopModel(f'uncaptured NAND feature {address:02X}')
        return self.features[address]

    def begin(self):
        self.input_bits = 0
        self.accumulator = 0
        self.input_bytes = []
        self.outputs = {}
        self.miso = self.idle

    def end(self):
        data = self.input_bytes
        if not data:
            return
        command = data[0]
        self.opcodes[command] += 1
        entry = dict(command=f'{command:02X}', input_prefix=bytes(data[:16]).hex(' '),
                     bytes_clocked=len(data), response_prefix=bytes(self.outputs[k] for k in sorted(self.outputs)[:16]).hex(' '))
        if command == 0x13:
            if len(data) != 4:
                raise StopModel('malformed NAND page read')
            row = int.from_bytes(bytes(data[1:4]), 'big')
            if row >= 131072:
                raise StopModel('NAND row outside captured device')
            if not self.features[0xB0] & 0x10 or self.features[0xB0] & 0x40:
                raise StopModel('requested raw ECC-off or special NAND page not captured')
            self.cached_page = row
            main = self.images['nand_main_256MiB.bin']
            oob = self.images['nand_oob64_8MiB.bin']
            self.cache = main[row * 2048:(row + 1) * 2048] + oob[row * 64:(row + 1) * 64]
            self.status = self.images['nand_ecc_status_128KiB.bin'][row] | (self.status & 2)
            self.pending_busy = self.busy_polls
            self.pages[row] += 1
            entry.update(page=row, main_offset=hx(row * 2048), captured_ECC=f'{self.status & 0x30:02X}')
        elif command == 0x1F:
            if len(data) != 3:
                raise StopModel('malformed NAND Set Feature')
            address, value = data[1:]
            if address == 0xA0:
                self.features[address] = value & 0xB8
            elif address == 0xB0:
                self.features[address] = (value & 0xD2) | 4
            else:
                raise StopModel(f'NAND feature write not modelled: {address:02X}')
            entry.update(feature=f'{address:02X}', value=f'{self.features[address]:02X}')
        elif command == 0x06:
            self.status |= 2
        elif command == 0x04:
            self.status &= ~2
        elif command in (0xFF, 0xFE):
            self.status = 0
            self.pending_busy = self.busy_polls
            self.cached_page = None
            self.cache = None
        elif command in (0x02, 0x84, 0x10, 0xD8, 0x2A):
            self.array_writes.append(entry)
            raise StopModel('NAND array modification requested; model not implemented')
        elif command not in (0x9F, 0x0F, 0x03, 0x0B, 0x3B):
            raise StopModel(f'unsupported NAND opcode {command:02X}')
        if command in (0x03, 0x0B, 0x3B):
            entry.update(page=self.cached_page, column=int.from_bytes(bytes(data[1:3]), 'big') & 0xFFF,
                         returned_data_bytes=max(0, self.input_bits - 32) // (4 if command == 0x3B else 8),
                         data_prefix=bytes(self.outputs[k] for k in sorted(self.outputs) if k >= 4)[:16].hex(' '))
        self.transactions.append(entry)

    def byte_out(self, byte_index):
        if byte_index in self.outputs:
            return self.outputs[byte_index]
        value = 0xFF if self.idle else 0
        data = self.input_bytes
        if not data:
            return value
        command = data[0]
        if command == 0x9F and byte_index >= 2:
            position = byte_index - 2
            if position >= 2:
                raise StopModel('uncaptured reserved Read ID output')
            value = (0x98, 0xCB)[position]
        elif command == 0x0F and byte_index >= 2:
            value = self.feature(data[1])
        elif command in (0x03, 0x0B, 0x3B) and byte_index >= 4:
            if self.cache is None:
                raise StopModel('NAND cache read without captured page')
            column = int.from_bytes(bytes(data[1:3]), 'big') & 0xFFF
            offset = column + byte_index - 4
            if offset >= len(self.cache):
                raise StopModel('NAND cache offset outside captured 2048+64 bytes')
            value = self.cache[offset]
            self.read_bytes += 1
        self.outputs[byte_index] = value
        return value

    def drive(self, levels, write_mask):
        cs = 1 if levels & (1 << 8) else 0
        clk = 1 if levels & (1 << 15) else 0
        mosi = 1 if levels & (1 << 14) else 0
        if write_mask & (1 << 8) and cs != self.cs:
            if cs:
                self.end()
            else:
                self.begin()
            self.cs = cs
        if write_mask & (1 << 14):
            self.mosi = mosi
        if write_mask & (1 << 15) and clk != self.clk:
            if not self.cs:
                if not clk:
                    if self.input_bytes and self.input_bytes[0] == 0x3B and self.input_bits >= 32:
                        bit_offset = (self.input_bits - 32) * 2
                        byte_index, bit_index = divmod(bit_offset, 8)
                        output = self.byte_out(4 + byte_index)
                        self.miso = (output >> (7 - bit_index)) & 1
                        self.io0 = (output >> (6 - bit_index)) & 1
                    else:
                        byte_index, bit_index = divmod(self.input_bits, 8)
                        self.miso = (self.byte_out(byte_index) >> (7 - bit_index)) & 1
                else:
                    self.accumulator = (self.accumulator << 1) | self.mosi
                    self.input_bits += 1
                    if self.input_bits % 8 == 0:
                        self.input_bytes.append(self.accumulator & 255)
                        self.accumulator = 0
                        if len(self.input_bytes) == 1 and self.input_bytes[0] not in (0x9F, 0x0F, 0x13, 0x03, 0x0B, 0x3B, 0x1F, 0x06, 0x04, 0xFF, 0xFE, 0x02, 0x84, 0x10, 0xD8, 0x2A):
                            raise StopModel(f'unsupported NAND opcode {self.input_bytes[0]:02X}')
            self.clk = clk

    def describe(self):
        return dict(sources=self.sources, jedec='98 CB',
                    wiring=dict(CS='PB8', SCLK='PB15', MOSI='PB14', MISO='PA15'),
                    idle_MISO=self.idle, busy_status_reads=self.busy_polls,
                    feature_registers={f'{k:02X}': f'{v:02X}' for k, v in self.features.items()},
                    opcodes={f'{k:02X}': v for k, v in self.opcodes.items()},
                    page_reads=dict(self.pages), feature_reads={f'{k:02X}': v for k, v in self.feature_reads.items()},
                    returned_cache_bytes=self.read_bytes, transactions=self.transactions,
                    incomplete_transaction=dict(input_bytes=self.input_bytes[:16], input_bits=self.input_bits),
                    NAND_array_write_requests=self.array_writes, capture_files_modified=False)


class NandRunner(Runner):
    def __init__(self, image, nand, poison=0xA5, delay=0, wake_once=False, idle_clock_scale=1):
        self.nand = nand
        self.log_counts = Counter()
        self.lowest_sp = 0x200170E0
        self.lowest_sp_after_main = 0x200170E0
        self.entered_main = False
        self.irq_active = False
        self.irq_returned = False
        self.irq_log = []
        self.pending_read_checks = []
        self.verified_RAM_reads = []
        self.exti = {off: 0 for off in (0, 4, 8, 0xC, 0x10, 0x14)}
        self.nvic_enable = [0] * 8
        self.nvic_pending = [0] * 8
        self.nvic_priorities = {}
        self.pmu_ctl = 0
        self.dac_ctl = 0
        self.dac_regs = {off: 0 for off in range(0x400, 0x434, 4)}
        self.wake_once = wake_once
        self.wake_events = []
        self.PA0 = None
        self.idle_clock_scale = idle_clock_scale
        self.wake_tick = None
        self.dma_regs = {}
        self.dma_descriptors = []
        for controller, channels in ((0, 7), (0x400, 5)):
            self.dma_regs.update({controller: 0, controller + 4: 0})
            for channel in range(channels):
                for offset in (0, 4, 8, 12):
                    self.dma_regs[controller + 8 + channel * 20 + offset] = 0
        super().__init__(image, poison, delay, configuration=True)
        self.gpio[0x40011C00] = {0: 0x44444444, 4: 0x44444444, 0xC: 0, 0x18: 0}
        self.gpio[0x40012000] = {0: 0x44444444, 4: 0x44444444, 0xC: 0, 0x18: 0}
        self.core[0xD10] = 0
        self.cpu.mmio_map(0x40012000, 4096, self.gpio_read_extra, None, self.gpio_write_extra, None)
        self.cpu.mmio_map(0x40007000, 4096, self.pmu_read, None, self.pmu_write, None)
        self.cpu.mmio_map(0x40020000, 4096, self.dma_read, None, self.dma_write, None)
        self.cpu.hook_add(UC_HOOK_INTR, self.on_intr)

    def gpio_read_extra(self, uc, off, size, data):
        return self.checked_read(lambda: self.gpio_get(0x2000 + off, size), 0x40012000 + off, size, 'GPIO_AFIO')

    def gpio_write_extra(self, uc, off, size, value, data):
        self.checked_write(lambda: self.gpio_set(0x2000 + off, size, value), 0x40012000 + off, size, value, 'GPIO_AFIO')

    def pmu_read(self, uc, off, size, data):
        if off in self.dac_regs and size == 4:
            value = self.dac_regs[off]
            self.log('read', 0x40007000 + off, size, value, 'DAC_DIGITAL')
            return value
        if off != 0 or size != 4:
            self.halt('peripheral register not modelled', 0x40007000 + off)
            return 0
        self.log('read', 0x40007000, size, self.pmu_ctl, 'PMU_CTL')
        return self.pmu_ctl

    def pmu_write(self, uc, off, size, value, data):
        if off in self.dac_regs and size == 4:
            self.dac_regs[off] = value
            if off == 0x400:
                self.dac_ctl = value
            for channel, offsets in ((0, (0x408, 0x40C, 0x410)), (1, (0x414, 0x418, 0x41C))):
                if off in offsets:
                    mode = offsets.index(off)
                    sample = (value & 0xFFF) if mode == 0 else ((value >> 4) & 0xFFF) if mode == 1 else ((value & 255) << 4)
                    self.dac_regs[offsets[0]] = sample
                    if not self.dac_ctl & (1 << (channel * 16 + 2)):
                        self.dac_regs[0x42C + channel * 4] = sample
            if off == 0x404:
                for channel in (0, 1):
                    if value & (1 << channel):
                        self.dac_regs[0x42C + channel * 4] = self.dac_regs[0x408 + channel * 0xC]
                self.dac_regs[0x404] = 0
            self.log('write', 0x40007000 + off, size, value, 'DAC_DIGITAL')
            return
        if off != 0 or size != 4:
            self.halt('peripheral register not modelled', 0x40007000 + off)
            return
        self.pmu_ctl = value
        self.log('write', 0x40007000, size, value, 'PMU_CTL')

    def dma_read(self, uc, off, size, data):
        if off not in self.dma_regs or size != 4:
            self.halt('DMA register not modelled', 0x40020000 + off)
            return 0
        value = self.dma_regs[off]
        self.log('read', 0x40020000 + off, size, value, 'DMA_CONFIG')
        return value

    def dma_write(self, uc, off, size, value, data):
        if off not in self.dma_regs or size != 4:
            self.halt('DMA register not modelled', 0x40020000 + off)
            return
        controller, local = (0x400, off - 0x400) if off >= 0x400 else (0, off)
        if local == 4:
            self.dma_regs[controller] &= ~value
        else:
            self.dma_regs[off] = value
        self.log('write', 0x40020000 + off, size, value, 'DMA_CONFIG')
        if local >= 8 and (local - 8) % 20 == 0 and value & 1:
            base = off
            count = self.dma_regs[base + 4] & 0xFFFF
            memory = self.dma_regs[base + 12]
            width = 1 << ((value >> 10) & 3)
            span = count * width if value & 0x80 else width
            descriptor = dict(controller=controller // 0x400, channel=(local - 8) // 20,
                control=hx(value), count=count, memory_address=hx(memory),
                peripheral_address=hx(self.dma_regs[base + 8]), memory_width_bytes=width,
                configured_memory_span_bytes=span, direction='memory_to_peripheral' if value & 0x10 else 'peripheral_to_memory',
                step=self.steps)
            self.dma_descriptors.append(descriptor)
            self.halt('DMA transfer engine required', 0x40020000 + off, descriptor=descriptor)

    def core_get(self, off, size):
        word, shift, mask = self.lane(off, size)
        for start, registers in ((0x100, self.nvic_enable), (0x180, self.nvic_enable),
                                 (0x200, self.nvic_pending), (0x280, self.nvic_pending)):
            if start <= word < start + 32:
                return (registers[(word - start) // 4] >> shift) & mask
        if 0x300 <= word < 0x320:
            return 0  # No external exception delivered by this model.
        if 0x400 <= word < 0x500:
            return (self.nvic_priorities.get(word, 0) >> shift) & mask
        return super().core_get(off, size)

    def core_set(self, off, size, value):
        word, shift, mask = self.lane(off, size)
        for start, registers, setting in ((0x100, self.nvic_enable, True), (0x180, self.nvic_enable, False),
                                          (0x200, self.nvic_pending, True), (0x280, self.nvic_pending, False)):
            if start <= word < start + 32:
                if size != 4:
                    raise StopModel('unsupported NVIC bitmap width')
                index = (word - start) // 4
                if setting:
                    registers[index] |= value
                else:
                    registers[index] &= ~value
                if start == 0x200 and value:
                    raise StopModel('external software-pended interrupt not modelled')
                return
        if 0x400 <= word < 0x500:
            self.nvic_priorities[word] = (self.nvic_priorities.get(word, 0) & ~(mask << shift)) | ((value & mask) << shift)
            return
        return super().core_set(off, size, value)

    def log(self, op, address, size, value, route):
        self.log_counts[(route, op)] += 1
        if len(self.events) < 4096:
            super().log(op, address, size, value, route)

    def gpio_get(self, off, size):
        address = 0x40010000 + off
        if 0x40010400 <= address < 0x40010800:
            word, shift, mask = self.lane(address - 0x40010400, size)
            if word not in self.exti:
                raise StopModel('EXTI register not modelled')
            return (self.exti[word] >> shift) & mask
        if address == 0x40010808 and size == 4:
            if self.cpu.reg_read(UC_ARM_REG_PC) == 0x0800879A and self.cpu.reg_read(UC_ARM_REG_R1) == 1 and self.PA0 is not None:
                return self.PA0
            if self.cpu.reg_read(UC_ARM_REG_PC) != 0x0800879A or self.cpu.reg_read(UC_ARM_REG_R1) != 0x8000:
                raise StopModel('GPIOA input other than NAND PA15 is not modelled')
            return self.nand.miso << 15
        if address == 0x40010C08 and size == 4:
            if self.cpu.reg_read(UC_ARM_REG_PC) != 0x0800879A or self.cpu.reg_read(UC_ARM_REG_R1) != 0x4000:
                raise StopModel('GPIOB input other than NAND IO0 is not modelled')
            return self.nand.io0 << 14
        return super().gpio_get(off, size)

    def gpio_set(self, off, size, value):
        address = 0x40010000 + off
        if 0x40010400 <= address < 0x40010800:
            word, shift, mask = self.lane(address - 0x40010400, size)
            if word not in self.exti:
                raise StopModel('EXTI register not modelled')
            if word == 0x14:
                self.exti[word] &= ~(value << shift)
            else:
                self.exti[word] = (self.exti[word] & ~(mask << shift)) | ((value & mask) << shift)
                if word == 0x10 and value:
                    raise StopModel('EXTI software interrupt delivery not modelled')
            return
        super().gpio_set(off, size, value)
        address = 0x40010000 + off
        if 0x40010C00 <= address < 0x40011000:
            word, shift, mask = self.lane(address - 0x40010C00, size)
            if word == 0x10:
                drive_mask = (value & 0xFFFF) | ((value >> 16) & 0xFFFF)
            elif word == 0x14:
                drive_mask = value & 0xFFFF
            elif word == 0xC:
                drive_mask = mask << shift
            else:
                return
            self.nand.drive(self.gpio[0x40010C00][0xC], drive_mask)

    def on_code(self, uc, address, size, data):
        self.last_instruction_units = 1
        super().on_code(uc, address, size, data)
        # Optional untimed idle-loop acceleration. No branch or return patched:
        # the OEM keeps polling a counter which advances faster in this scenario.
        delay_poll=address==0x08009F0C
        date_idle=(address in (0x08074736,0x0809319E) and getattr(self,'fast_mode',False)
                   and bytes(uc.mem_read(0x2000129D,1))!=b'\x00')
        rtos_idle=(address==0x080AD2D8 and getattr(self,'fast_mode',False)
                   and bytes(uc.mem_read(0x20001542,1))==b'\x01'
                   and bytes(uc.mem_read(0x20001537,1))==b'\x3F')
        uart_wait=getattr(self,'uart_wait_extra',0)
        if (delay_poll or date_idle or rtos_idle or uart_wait) and self.idle_clock_scale > 1 and self.systick[0x10] & 1 and self.stop is None:
            divider = 1 if self.systick[0x10] & 4 else 8
            remaining=max(0,uc.reg_read(UC_ARM_REG_R4)-uc.reg_read(UC_ARM_REG_R2)) if delay_poll else None
            # Advance only at the OEM timer-poll read and cap the acceleration
            # to the delay still requested. This avoids turning a 1 us I2C
            # wait into thousands of virtual units at every instruction.
            extra=min(self.idle_clock_scale-1,remaining*divider) if delay_poll else min(self.idle_clock_scale-1,uart_wait) if uart_wait else self.idle_clock_scale-1
            # End the bulk advance at the first SysTick boundary, preserving
            # all elapsed units when an interrupt becomes pending.
            until_wrap=(self.systick[0x18] or self.systick[0x14]+1)*divider-self.tick_fraction
            extra=min(extra,until_wrap)
            self.last_instruction_units += extra
            ticks, self.tick_fraction = divmod(self.tick_fraction + extra, divider)
            # Same decrement/reload sequence, computed in bulk. Stop at the
            # first interrupt boundary, as the instruction loop did in V5.
            while ticks:
                old = self.systick[0x18]
                distance = old if old else self.systick[0x14] + 1
                if not old and not self.systick[0x14]:
                    break  # RELOAD=0 never produces a 1 -> 0 transition.
                if ticks < distance:
                    self.systick[0x18] = (old if old else self.systick[0x14] + 1) - ticks
                    break
                ticks -= distance
                self.systick[0x18] = 0
                self.tick_wraps += 1
                self.systick[0x10] |= 1 << 16
                if self.systick[0x10] & 2:
                    self.halt('SysTick exception delivery required')
                    break
        if self.PA0 == 0 and self.wake_tick is not None and self.tick_wraps - self.wake_tick >= 20 and 'POWER' not in getattr(self,'held_keys',()):
            self.PA0 = 1
            self.wake_events[-1].update(released_at_step=self.steps, released_at_systick=self.tick_wraps,
                                         release_rule='20 SysTick periods after virtual Power press')
            self.wake_tick = None
        opcode=self.image[address-APP:address-APP+2] if APP<=address<APP+len(self.image) else bytes(uc.mem_read(address,2))
        if opcode in (b'\x30\xbf', b'\x20\xbf'):
            self.halt('CPU sleep instruction requires wake event')
        if self.pending_read_checks and address == self.pending_read_checks[-1]['return_pc']:
            check = self.pending_read_checks.pop()
            expected = check.pop('expected')
            actual = bytes(uc.mem_read(check['target'], len(expected)))
            check.update(actual_sha256=hashlib.sha256(actual).hexdigest(),
                         matches_captured_dump=(actual == expected) if check.get('source','captured')=='captured' else None,
                         matches_model_output=(actual == expected),checked_step=self.steps)
            self.verified_RAM_reads.append(check)
            if actual != expected:
                self.halt('SPI output did not reproduce captured bytes in MCU RAM')
        if address == 0x0808ADBE and self.nand.cache is not None:
            dest, count = uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1)
            tx = self.nand.input_bytes
            if tx and tx[0] == 0x3B and len(tx) >= 4:
                column = int.from_bytes(bytes(tx[1:3]), 'big') & 0xFFF
                if not RAM <= dest <= dest + count <= RAM + RAM_SIZE or column + count > len(self.nand.cache):
                    self.halt('invalid NAND receive buffer or uncaptured range')
                else:
                    expected = self.nand.cache[column:column + count]
                    self.pending_read_checks.append(dict(target=dest, bytes=count, page=self.nand.cached_page,
                        source='volatile_overlay' if self.nand.cached_page in getattr(self.nand,'overlay',{}) else 'captured',
                        column=column, return_pc=uc.reg_read(UC_ARM_REG_LR) & ~1, expected=expected,
                        expected_sha256=hashlib.sha256(expected).hexdigest()))
        sp = None if getattr(self, 'fast_mode', False) else uc.reg_read(UC_ARM_REG_SP)
        if sp is not None:
            self.lowest_sp = min(self.lowest_sp, sp)
        if address == 0x08006654:
            self.entered_main = True
        if self.entered_main and sp is not None:
            self.lowest_sp_after_main = min(self.lowest_sp_after_main, sp)

    def on_intr(self, uc, number, data):
        if number == 8 and self.irq_active:
            self.irq_returned = True
            uc.emu_stop()
        else:
            self.halt('unhandled CPU exception', exception_number=number)

    def deliver_systick(self, exception=15):
        cpu = self.cpu
        name = 'SysTick' if exception == 15 else f'IRQ{exception - 16}'
        if self.irq_active or cpu.reg_read(UC_ARM_REG_IPSR):
            self.halt('nested interrupt not modelled')
            return
        if cpu.reg_read(UC_ARM_REG_PRIMASK) or cpu.reg_read(UC_ARM_REG_FAULTMASK):
            self.halt('SysTick pending while interrupts masked')
            return
        irq = exception - 16
        priority = (self.core[0xD20] >> 24) & 255 if exception == 15 else (self.nvic_priorities.get(0x400 + (irq & ~3), 0) >> (8 * (irq & 3))) & 255
        basepri = cpu.reg_read(UC_ARM_REG_BASEPRI)
        if basepri and priority >= basepri:
            self.halt('SysTick pending below BASEPRI mask')
            return
        resume = cpu.reg_read(UC_ARM_REG_PC)
        original_sp = cpu.reg_read(UC_ARM_REG_SP)
        psp_active = bool(cpu.reg_read(UC_ARM_REG_CONTROL) & 2)
        pad = original_sp & 7
        if pad not in (0, 4):
            self.halt('unaligned exception stack')
            return
        frame_address = original_sp - 32 - pad
        if not RAM <= frame_address <= RAM + RAM_SIZE - 32:
            self.halt('exception stack outside SRAM')
            return
        registers = (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
                     UC_ARM_REG_R12, UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_XPSR)
        frame_values = [cpu.reg_read(reg) for reg in registers]
        frame_values[-1] = (frame_values[-1] & ~(1 << 9)) | (bool(pad) << 9)
        frame = struct.pack('<8I', *frame_values)
        callee_regs = (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
                       UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11)
        callee_values = [cpu.reg_read(reg) for reg in callee_regs]
        context = cpu.context_save()
        cpu.mem_write(frame_address, frame)
        if psp_active:
            cpu.reg_write(UC_ARM_REG_PSP, frame_address)
            handler_sp = cpu.reg_read(UC_ARM_REG_MSP)
        else:
            handler_sp = frame_address
            cpu.reg_write(UC_ARM_REG_MSP, handler_sp)
        cpu.reg_write(UC_ARM_REG_XPSR, (frame_values[-1] & 0xF8000000) | 0x01000000 | exception)
        cpu.reg_write(UC_ARM_REG_SP, handler_sp)
        cpu.reg_write(UC_ARM_REG_LR, 0xFFFFFFFD if psp_active else 0xFFFFFFF9)
        handler = read32(self.image, APP + exception * 4)
        if not APP <= (handler & ~1) < APP + len(self.image):
            self.halt('invalid SysTick vector')
            return
        self.irq_active = True
        self.irq_returned = False
        if exception >= 16:
            self.nvic_pending[irq // 32] &= ~(1 << (irq % 32))
        self.irq_log.append(dict(step=self.steps, vector=hx(handler), exception=exception, name=name, interrupted_pc=hx(resume),
                                 frame_address=hx(frame_address), stack='PSP' if psp_active else 'MSP'))
        try:
            cpu.emu_start(handler, 0, count=50_000)
        except UcError as error:
            if not self.irq_returned:
                self.halt('SysTick CPU exception', error=str(error))
        if self.irq_returned and self.stop is None:
            if bytes(cpu.mem_read(frame_address, 32)) != frame:
                self.halt('exception frame modified; task switch model required')
            elif [cpu.reg_read(reg) for reg in callee_regs] != callee_values:
                self.halt('SysTick did not preserve callee-saved registers')
            elif cpu.reg_read(UC_ARM_REG_SP) != handler_sp:
                self.halt('SysTick exception stack did not balance')
            else:
                cpu.context_restore(context)
                self.irq_log[-1].update(returned=True, returned_step=self.steps)
        elif self.stop is None:
            self.halt('SysTick handler budget exhausted')
        self.irq_active = False

    def wake_from_sleep(self):
        # The firmware explicitly selects EXTI0/PA0 falling edge and enables IRQ6.
        if self.afio[8] & 15 or not self.exti[0] & 1 or not self.exti[0xC] & 1 or not self.nvic_enable[0] & (1 << 6):
            self.halt('no supported wake input configured')
            return
        pc = self.cpu.reg_read(UC_ARM_REG_PC)
        self.PA0 = 0
        self.wake_tick = self.tick_wraps
        self.exti[0x14] |= 1
        self.nvic_pending[0] |= 1 << 6
        self.wake_events.append(dict(step=self.steps, source='synthetic PA0 falling edge', sleep_pc=hx(pc),
                                     input_level_after_edge=0, physical_pin_identity_not_asserted=True))
        # Complete WFI; hardware resumes at its following instruction after IRQ.
        self.cpu.reg_write(UC_ARM_REG_PC, (pc + 2)|1)
        if self.core[0xD10] & 4:
            self.clock.regs[0] &= ~((1 << 16) | (1 << 17) | (1 << 24) | (1 << 25))
            self.clock.regs[0] |= 3
            self.clock.regs[4] &= ~15
        self.deliver_systick(exception=22)

    def service_extra_stop(self):
        """Extension point for additional explicitly modelled IRQ sources."""
        return

    def run_chunks(self, maximum, chunk=250_000):
        started = time.monotonic()
        start = (self.cpu.reg_read(UC_ARM_REG_PC) | 1) if self.steps else getattr(self,'reset_entry',read32(self.image, APP + 4))
        status = 'running'
        next_progress=self.steps
        while self.steps < maximum and self.stop is None:
            try:
                self.cpu.emu_start(start, 0, count=min(chunk, maximum - self.steps))
            except UcError as error:
                status = str(error)
                if self.stop is None:
                    self.halt('CPU exception', error=status)
            if self.stop and self.stop['kind'] == 'SysTick exception delivery required':
                self.stop = None
                self.deliver_systick()
            if self.stop and self.stop['kind'] == 'CPU sleep instruction requires wake event' and self.wake_once and not self.wake_events:
                self.stop = None
                self.wake_from_sleep()
            self.service_extra_stop()
            if self.stop or not getattr(self,'fast_mode',False) or self.steps>=next_progress:
                print(json.dumps(dict(steps=self.steps, pc=hx(self.cpu.reg_read(UC_ARM_REG_PC)),
                                  transactions=len(self.nand.transactions), cache_bytes=self.nand.read_bytes,
                                  pages=len(self.nand.pages), stop=self.stop)), flush=True)
                next_progress=self.steps+chunk
            start = self.cpu.reg_read(UC_ARM_REG_PC) | 1
        state = bytes(self.cpu.mem_read(RAM, RAM_SIZE))
        if self.stop is None:
            self.stop = dict(kind='instruction_budget', pc=hx(self.cpu.reg_read(UC_ARM_REG_PC)), step=self.steps)
        return dict(firmware_sha256=hashlib.sha256(self.image).hexdigest(), steps=self.steps,
                    host_elapsed_seconds=round(time.monotonic() - started, 3), stop=self.stop,
                    checkpoints=self.checkpoints,
                    lowest_observed_sp=None if getattr(self, 'fast_mode', False) else hx(self.lowest_sp),
                    lowest_observed_sp_after_main=None if getattr(self, 'fast_mode', False) else hx(self.lowest_sp_after_main),
                    full_instruction_audit=not getattr(self, 'fast_mode', False),
                    high_SRAM_changed_from_poison_bytes=sum(x != self.poison for x in state[0x170E0:]),
                    high_SRAM_proven_free=False, live_radio_RAM_usage_measured=False,
                    poison=hx(self.poison), ram_sha256=hashlib.sha256(state).hexdigest(),
                    IRQ_delivery='SysTick actual vector with emulated basic frame',
                    delivered_exceptions=self.irq_log, systick_wraps=self.tick_wraps, wake_events=self.wake_events,
                    idle_clock_scale=self.idle_clock_scale,
                    timing_cycle_accurate=False,
                    DMA_transfers_executed=False, configured_DMA=self.dma_descriptors,
                    hardware_configuration=dict(afio={hx(k):hx(v) for k,v in self.afio.items()},
                        exti={hx(k):hx(v) for k,v in self.exti.items()}, nvic_enable=[hx(x) for x in self.nvic_enable],
                        nvic_pending=[hx(x) for x in self.nvic_pending], core={hx(k):hx(v) for k,v in self.core.items()},
                        interrupt_masks=dict(PRIMASK=self.cpu.reg_read(UC_ARM_REG_PRIMASK),
                            BASEPRI=self.cpu.reg_read(UC_ARM_REG_BASEPRI), FAULTMASK=self.cpu.reg_read(UC_ARM_REG_FAULTMASK))),
                    systick={hx(k): hx(v) for k, v in self.systick.items()},
                    skipped_firmware_functions=[], firmware_patched=False,
                    nand=self.nand.describe(), mmio_counts={str(k): v for k, v in self.log_counts.items()},
                    verified_RAM_reads=self.verified_RAM_reads,
                    first_4096_MMIO_events=self.events,
                    most_visited_instructions=[dict(pc=hx(a), count=n) for a, n in self.pcs.most_common(20)],
                    last_instructions=list(self.trail)), state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('firmware', type=Path)
    parser.add_argument('nand_directory', type=Path)
    parser.add_argument('--out', type=Path, default=Path('resultats_nand_v121.json'))
    parser.add_argument('--instructions', type=int, default=3_000_000)
    parser.add_argument('--poison', type=lambda x:int(x,0), default=0xA5)
    parser.add_argument('--idle-miso', type=int, choices=(0,1), default=1)
    parser.add_argument('--busy-polls', type=int, choices=(0,1,2), default=1)
    parser.add_argument('--wake-once', action='store_true', help='One synthetic falling edge on the configured PA0 wake input')
    parser.add_argument('--idle-clock-scale', type=int, choices=(1,8,64), default=1,
                        help='Virtual timer acceleration only inside the OEM polling delay loop; not cycle accurate')
    args = parser.parse_args()
    image = args.firmware.read_bytes()
    require(hashlib.sha256(image).hexdigest() == EXPECTED_SHA, 'Wrong firmware')
    nand = CapturedNand(args.nand_directory, idle_miso=args.idle_miso, busy_polls=args.busy_polls)
    runner = NandRunner(image, nand, args.poison, wake_once=args.wake_once, idle_clock_scale=args.idle_clock_scale)
    result, state = runner.run_chunks(args.instructions)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    args.out.with_suffix('.sram.bin').write_bytes(state)
    print(json.dumps({k:v for k,v in result.items() if k not in ('nand','first_4096_MMIO_events','most_visited_instructions')},indent=2))


if __name__ == '__main__':
    main()
