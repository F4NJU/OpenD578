#!/usr/bin/env python3
"""Execute authentic D578 startup with a small, explicit clock/device model."""
import argparse
import hashlib
import json
from collections import Counter, deque
from pathlib import Path

from audit_ram_v121 import (APP, RAM, RAM_SIZE, EXPECTED_SHA, hx, require,
                            make_cpu, read32, decode_initialized_data)
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_INVALID, UcError
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_SP, UC_ARM_REG_R1


class StopModel(Exception):
    pass


class ClockModel:
    """RCU subset for GD32F303 XD. Delay unit = CTL reads, not physical time."""
    READY = (1 << 1) | (1 << 17) | (1 << 25)
    ENABLE = {0: 1, 16: 17, 24: 25}
    REGS = {0: 0x83, 4: 0, 8: 0, 0xC: 0, 0x10: 0, 0x14: 0x14,
            0x18: 0, 0x1C: 0, 0x20: 0, 0x24: 0x0C000000, 0x28: 0, 0x2C: 0,
            0xC0:0x80000000}

    def __init__(self, delay_reads=0, unavailable=None):
        self.regs = self.REGS.copy()
        self.delay_reads = delay_reads
        self.unavailable = unavailable
        self.pending = {0: 0, 16: delay_reads, 24: delay_reads}
        self.transitions = []

    def refresh(self, advance=False):
        previous = self.regs[0]
        ctl = previous
        for enable, ready in self.ENABLE.items():
            name = {0: 'IRC8M', 16: 'HXTAL', 24: 'PLL'}[enable]
            upstream = True
            if enable == 24:
                upstream = bool(ctl & (1 << (17 if self.regs[4] & (1 << 16) else 1)))
            available = bool(ctl & (1 << enable)) and name != self.unavailable and upstream
            if not available:
                ctl &= ~(1 << ready)
            elif self.pending[enable] > 0:
                ctl &= ~(1 << ready)
                if advance:
                    self.pending[enable] -= 1
            else:
                ctl |= 1 << ready
        self.regs[0] = ctl
        selected = self.regs[4] & 3
        if selected < 3 and ctl & (1 << (1, 17, 25)[selected]):
            self.regs[4] = (self.regs[4] & ~12) | (selected << 2)
        if previous != ctl:
            self.transitions.append({'control_before': hx(previous), 'control_after': hx(ctl)})

    def read_word(self, offset):
        if offset not in self.regs:
            raise StopModel('RCU register not modelled')
        self.refresh(advance=(offset == 0))
        return self.regs[offset]

    def write_word(self, offset, value):
        if offset not in self.regs:
            raise StopModel('RCU register not modelled')
        old = self.regs[offset]
        if offset == 0:
            # Calibration/stability/reserved bits cannot be written by software.
            writable = 1 | (0x1F << 3) | (1 << 16) | (1 << 18) | (1 << 19) | (1 << 24)
            value = (old & ~writable) | (value & writable)
            source = (self.regs[4] >> 2) & 3
            if source == 0:
                value |= 1
            if source == 2:
                value |= 1 << 24
            if source == 1 or (source == 2 and self.regs[4] & (1 << 16)):
                value |= 1 << 16
            if old & (1 << 16):
                value = (value & ~(1 << 18)) | (old & (1 << 18))
            for enable in self.ENABLE:
                if bool(old & (1 << enable)) != bool(value & (1 << enable)):
                    self.pending[enable] = self.delay_reads
            self.regs[0] = value
        elif offset == 4:
            # SCSS is hardware-owned. PLL source/multiplier are held while enabled.
            value = (value & ~12) | (old & 12)
            if self.regs[0] & (1 << 24):
                mask = (0x3F << 16) | (1 << 27) | (1 << 30)
                value = (value & ~mask) | (old & mask)
            self.regs[4] = value
        elif offset == 8:
            # Only IRQ enables are retained; W1C requests clear their flags.
            self.regs[8] = (old & 0xFF & ~((value >> 16) & 0xFF)) | (value & 0x7F00)
        elif offset==0xC0:
            # GD32F30x manual 5.3.13: calibration is read-only; ideal ready
            # follows IRC48MEN, as for the other ideal oscillators in this model.
            self.regs[offset]=(old&0xFF000000)|(value&0x10001)|(0x20000 if value&0x10000 else 0)
        else:
            self.regs[offset] = value & 0xFFFFFFFF
        self.refresh()


class Runner:
    LABELS = {0x08006D3C: 'SystemInit_returned', 0x0800620C: 'scatter_completed',
              0x08006654: 'application_main', 0x080899F2: 'application_clock_waits_passed',
              0x08006668: 'GPIO_clock_configuration_passed',
              0x0800666C: 'SysTick_configuration_passed',
              0x0808AE62: 'memory_ID_routine_entered'}
    def __init__(self, image, poison, delay_reads=0, unavailable=None, configuration=True):
        self.image = image
        self.poison = poison
        self.cpu = make_cpu(image, poison)
        self.clock = ClockModel(delay_reads, unavailable)
        self.configuration = configuration
        self.events = []
        self.stop = None
        self.steps = 0
        self.trail = deque(maxlen=32)
        self.checkpoints = []
        self.snapshots = {}
        self.pcs = Counter()
        self.gpio = {}
        self.afio = {0: 0, 4: 0, 8: 0, 0xC: 0, 0x10: 0, 0x14: 0, 0x1C: 0}
        self.core = {0xD08: 0, 0xD0C: 0xFA050000, 0xD20: 0}
        self.systick = {0x10: 0, 0x14: 0, 0x18: 0}
        self.tick_fraction = 0
        self.tick_wraps = 0
        self.fmc_ws = 0
        for base in (0x40010800, 0x40010C00, 0x40011000, 0x40011400, 0x40011800):
            self.gpio[base] = {0: 0x44444444, 4: 0x44444444, 0xC: 0, 0x18: 0}
        self.cpu.mmio_map(0x40021000, 4096, self.rcu_read, None, self.rcu_write, None)
        self.cpu.mmio_map(0x42420000, 4096, self.alias_read, None, self.alias_write, None)
        self.cpu.mmio_map(0x40022000, 4096, self.fmc_read, None, self.fmc_write, None)
        self.cpu.mmio_map(0xE000E000, 4096, self.core_read, None, self.core_write, None)
        if configuration:
            self.cpu.mmio_map(0x40010000, 8192, self.gpio_read, None, self.gpio_write, None)
        self.code_hook=self.cpu.hook_add(UC_HOOK_CODE, self.on_code)
        self.cpu.hook_add(UC_HOOK_MEM_INVALID, self.on_invalid)

    def log(self, op, address, size, value, route):
        self.events.append(dict(step=self.steps, pc=hx(self.cpu.reg_read(UC_ARM_REG_PC)),
                                op=op, address=hx(address), size=size, value=hx(value), route=route))

    def halt(self, kind, address=None, **extra):
        if self.stop is None:
            self.stop = dict(kind=kind, pc=hx(self.cpu.reg_read(UC_ARM_REG_PC)), step=self.steps, **extra)
            if address is not None:
                self.stop['address'] = hx(address)
        self.cpu.emu_stop()

    def checked_read(self, function, address, size, route):
        if getattr(self,'native_gate',None):self.native_gate.sync()
        try:
            value = function()
        except StopModel as error:
            self.halt(str(error), address, size=size)
            return 0
        self.log('read', address, size, value, route)
        if getattr(self,'native_gate',None):self.native_gate.refresh()
        return value

    def checked_write(self, function, address, size, value, route):
        if getattr(self,'native_gate',None):self.native_gate.sync()
        try:
            function()
        except StopModel as error:
            self.halt(str(error), address, size=size, attempted_value=hx(value))
            return
        self.log('write', address, size, value, route)
        if getattr(self,'native_gate',None):self.native_gate.refresh()

    @staticmethod
    def lane(offset, size):
        if size not in (1, 2, 4) or offset % size or (offset & 3) + size > 4:
            raise StopModel('unsupported MMIO access alignment')
        return offset & ~3, (offset & 3) * 8, (1 << (8 * size)) - 1

    def clock_get(self, off, size):
        word, shift, mask = self.lane(off, size)
        return (self.clock.read_word(word) >> shift) & mask

    def clock_set(self, off, size, value):
        word, shift, mask = self.lane(off, size)
        old = self.clock.regs.get(word)
        if old is None:
            raise StopModel('RCU register not modelled')
        self.clock.write_word(word, (old & ~(mask << shift)) | ((value & mask) << shift))

    def rcu_read(self, uc, off, size, data):
        return self.checked_read(lambda: self.clock_get(off, size), 0x40021000 + off, size, 'RCU')

    def rcu_write(self, uc, off, size, value, data):
        self.checked_write(lambda: self.clock_set(off, size, value), 0x40021000 + off, size, value, 'RCU')

    @staticmethod
    def alias_decode(off, size):
        if size != 4 or off & 3:
            raise StopModel('unsupported bit-band access')
        byte = off // 32
        return byte & ~3, (byte & 3) * 8 + (off % 32) // 4

    def alias_get(self, off, size):
        word, bit = self.alias_decode(off, size)
        return (self.clock.read_word(word) >> bit) & 1

    def alias_set(self, off, size, value):
        word, bit = self.alias_decode(off, size)
        old = self.clock.regs.get(word)
        if old is None:
            raise StopModel('RCU bit-band register not modelled')
        self.clock.write_word(word, (old & ~(1 << bit)) | ((value & 1) << bit))

    def alias_read(self, uc, off, size, data):
        return self.checked_read(lambda: self.alias_get(off, size), 0x42420000 + off, size, 'RCU_BITBAND')

    def alias_write(self, uc, off, size, value, data):
        self.checked_write(lambda: self.alias_set(off, size, value), 0x42420000 + off, size, value, 'RCU_BITBAND')

    def fmc_read(self, uc, off, size, data):
        if off != 0 or size != 4:
            self.halt('FMC register not modelled', 0x40022000 + off)
            return 0
        self.log('read', 0x40022000, size, self.fmc_ws, 'FMC_WS')
        return self.fmc_ws

    def fmc_write(self, uc, off, size, value, data):
        if off != 0 or size != 4:
            self.halt('FMC register not modelled', 0x40022000 + off)
            return
        self.fmc_ws = value & 7  # Reserved bits read zero. No erase/program model.
        self.log('write', 0x40022000, size, value, 'FMC_WS')

    def core_get(self, off, size):
        word, shift, mask = self.lane(off, size)
        if word == 0xD08:
            value = self.core[word]
        elif self.configuration and word in self.systick:
            value = self.systick[word]
            if word == 0x10:
                self.systick[word] &= ~(1 << 16)
        elif self.configuration and word in self.core:
            value = self.core[word]
        else:
            raise StopModel('CPU register not modelled')
        return (value >> shift) & mask

    def core_set(self, off, size, value):
        word, shift, mask = self.lane(off, size)
        if word == 0xD08:
            self.core[word] = value & 0xFFFFFF80
        elif self.configuration and word in self.systick:
            if size != 4:
                raise StopModel('unsupported SysTick width')
            if word == 0x10:
                self.systick[word] = (self.systick[word] & (1 << 16)) | (value & 7)
            elif word == 0x14:
                self.systick[word] = value & 0xFFFFFF
            else:
                self.systick[0x18] = 0
                self.systick[0x10] &= ~(1 << 16)
                self.tick_fraction = 0
        elif self.configuration and word in self.core:
            old = self.core[word]
            self.core[word] = (old & ~(mask << shift)) | ((value & mask) << shift)
        else:
            raise StopModel('CPU register not modelled')

    def core_read(self, uc, off, size, data):
        return self.checked_read(lambda: self.core_get(off, size), 0xE000E000 + off, size, 'SCB_SYSTICK')

    def core_write(self, uc, off, size, value, data):
        self.checked_write(lambda: self.core_set(off, size, value), 0xE000E000 + off, size, value, 'SCB_SYSTICK')

    def gpio_get(self, off, size):
        address = 0x40010000 + off
        if address < 0x40010400:
            word, shift, mask = self.lane(off, size)
            if word not in self.afio:
                raise StopModel('AFIO register not modelled')
            return (self.afio[word] >> shift) & mask
        base = address & ~0x3FF
        word, shift, mask = self.lane(address - base, size)
        if base not in self.gpio:
            raise StopModel('GPIO port not modelled')
        if word == 8:
            raise StopModel('external GPIO input required')
        if word not in self.gpio[base]:
            raise StopModel('GPIO register not modelled')
        return (self.gpio[base][word] >> shift) & mask

    def gpio_set(self, off, size, value):
        address = 0x40010000 + off
        if address < 0x40010400:
            word, shift, mask = self.lane(off, size)
            if word not in self.afio:
                raise StopModel('AFIO register not modelled')
            self.afio[word] = (self.afio[word] & ~(mask << shift)) | ((value & mask) << shift)
            return
        base = address & ~0x3FF
        word, shift, mask = self.lane(address - base, size)
        if base not in self.gpio:
            raise StopModel('GPIO port not modelled')
        registers = self.gpio[base]
        if word in (0x10, 0x14) and size == 4:
            if word == 0x10:
                registers[0xC] = (registers[0xC] | (value & 0xFFFF)) & ~(value >> 16)
            else:
                registers[0xC] &= ~(value & 0xFFFF)
        elif word in registers:
            registers[word] = (registers[word] & ~(mask << shift)) | ((value & mask) << shift)
        else:
            raise StopModel('GPIO register not modelled')

    def gpio_read(self, uc, off, size, data):
        return self.checked_read(lambda: self.gpio_get(off, size), 0x40010000 + off, size, 'GPIO_AFIO')

    def gpio_write(self, uc, off, size, value, data):
        self.checked_write(lambda: self.gpio_set(off, size, value), 0x40010000 + off, size, value, 'GPIO_AFIO')

    def on_invalid(self, uc, access, address, size, value, data):
        self.halt('unmapped memory', address, access=access, size=size)
        return False

    def on_code(self, uc, address, size, data):
        self.steps += 1
        if not getattr(self, 'fast_mode', False):
            self.pcs[address] += 1
            self.trail.append(hx(address))
        if address in self.LABELS:
            label = self.LABELS[address]
            self.checkpoints.append(dict(label=label, pc=hx(address), step=self.steps))
            if label == 'scatter_completed':
                self.snapshots['scatter'] = bytes(uc.mem_read(RAM, RAM_SIZE))
        inside_application=APP<=address<APP+len(self.image)
        inside_boot=hasattr(self,'full_flash_source') and 0x08000000<=address<APP
        if not inside_application and not inside_boot:
            self.halt('execution outside authenticated CDD', address)
            return
        # Synthetic instruction clock: one executed instruction = one time unit.
        # This is not cycle-accurate. Stop before an unimplemented IRQ delivery.
        if self.configuration and self.systick[0x10] & 1:
            self.tick_fraction += 1
            divider = 1 if self.systick[0x10] & 4 else 8
            if self.tick_fraction >= divider:
                self.tick_fraction = 0
                old = self.systick[0x18]
                self.systick[0x18] = old - 1 if old else self.systick[0x14]
                if old == 1:
                    self.tick_wraps += 1
                    self.systick[0x10] |= 1 << 16
                    if self.systick[0x10] & 2:
                        self.halt('SysTick exception delivery required')

    def run(self, limit=250_000):
        status = 'budget_or_model_stop'
        try:
            self.cpu.emu_start(read32(self.image, APP + 4), 0, count=limit, timeout=10_000_000)
        except UcError as error:
            status = str(error)
        if self.stop is None:
            self.stop = dict(kind='instruction_budget_or_timeout', pc=hx(self.cpu.reg_read(UC_ARM_REG_PC)), step=self.steps)
        ram = bytes(self.cpu.mem_read(RAM, RAM_SIZE))
        high = ram[0x170E0:]
        report = dict(poison=hx(self.poison), ready_delay_CTL_reads=self.clock.delay_reads,
                      forced_unavailable=self.clock.unavailable, configuration_shadow=self.configuration,
                      executed_from_reset=True, skipped_functions=[], patched_firmware=False,
                      status=status, steps=self.steps, checkpoints=self.checkpoints, stop=self.stop,
                      rcu_registers={hx(k): hx(v) for k, v in self.clock.regs.items()},
                      fmc_wait_states=self.fmc_ws,
                      scb_registers={hx(k): hx(v) for k, v in self.core.items()},
                      systick_registers={hx(k): hx(v) for k, v in self.systick.items()},
                      systick_wraps=self.tick_wraps, IRQ_delivery=False,
                      input_bit_mask_at_stop=hx(self.cpu.reg_read(UC_ARM_REG_R1)),
                      high_SRAM_changed_from_poison_bytes=sum(x != self.poison for x in high),
                      high_SRAM_proven_free=False, live_radio_RAM_usage_measured=False,
                      ram_sha256=hashlib.sha256(ram).hexdigest(),
                      most_visited_instructions=[dict(pc=hx(a), count=n) for a, n in self.pcs.most_common(12)],
                      last_instruction_addresses=list(self.trail), mmio_events=self.events)
        return report, ram


def run_audit(image):
    require(hashlib.sha256(image).hexdigest() == EXPECTED_SHA, 'Wrong firmware; exact GD32 V1.21 CDD required')
    data, _ = decode_initialized_data(image, 0x080FE7A8, 6872)
    expected = data + bytes(87560)
    runs = []
    for configuration in (False, True):
        for delay in (0, 7):
            states = []
            for poison in (0xA5, 0x5A):
                runner = Runner(image, poison, delay, configuration=configuration)
                result, state = runner.run()
                labels = {c['label'] for c in result['checkpoints']}
                require({'SystemInit_returned', 'scatter_completed', 'application_main',
                         'application_clock_waits_passed'} <= labels, 'Clock path did not finish')
                require(runner.snapshots['scatter'][:len(expected)] == expected, 'Startup memory differs from independent decoder')
                require(result['high_SRAM_changed_from_poison_bytes'] == 0, 'Unexpected high SRAM change')
                if configuration:
                    require(result['stop']['kind'] == 'external GPIO input required', 'Unexpected external input boundary')
                    require(result['stop']['address'] == hx(0x40010808), 'Unexpected GPIO port')
                    require(result['stop']['pc'] == hx(0x0800879A), 'Unexpected input routine')
                    require(result['input_bit_mask_at_stop'] == hx(0x8000), 'Unexpected input pin')
                else:
                    require(result['stop']['address'] == hx(0x40011000), 'Clock-only path did not reach GPIO')
                states.append(state[:len(expected)])
                runs.append(result)
            require(states[0] == states[1], 'Low SRAM depends on initial poison')
    # Delay changes a software timeout counter before scatter overwrites it.
    # Later RAM may include changed virtual timing, so only the initialized
    # scatter snapshot, not all eventual SRAM, is required delay-independent.
    for unavailable in ('HXTAL', 'PLL'):
        runner = Runner(image, 0xA5, 0, unavailable, configuration=False)
        result, _ = runner.run(limit=100_000)
        labels = {c['label'] for c in result['checkpoints']}
        require('application_main' not in labels, 'Unavailable oscillator was incorrectly bypassed')
        require(result['stop']['kind'] == 'instruction_budget_or_timeout', 'Negative scenario escaped expected wait loop')
        runs.append(result)
    return dict(firmware_sha256=EXPECTED_SHA, image_bytes=len(image),
                conclusion='Clock waits passed from authentic reset. Strict physical input boundary on PA15 remains.',
                positive_runs=8, oscillator_failure_runs=2,
                synthetic_timing='RCU settling measured in CTL reads; SysTick uses one instruction per virtual time unit',
                scope='RCU, RCU bit-band, FMC wait-state register, VTOR; optional GPIO/AFIO/SysTick configuration',
                IRQ_delivery=False, RF_LCD_NAND_devices_emulated=False,
                high_SRAM_proven_free=False, live_radio_RAM_usage_measured=False, runs=runs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('firmware', type=Path)
    parser.add_argument('--out', type=Path, default=Path('resultats_clock_v121.json'))
    args = parser.parse_args()
    result = run_audit(args.firmware.read_bytes())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    for run in result['runs']:
        print(json.dumps({k: run[k] for k in ('configuration_shadow', 'ready_delay_CTL_reads',
                                             'poison', 'forced_unavailable', 'steps', 'stop',
                                             'high_SRAM_changed_from_poison_bytes')}))
    print('8 successful clock runs; 2 negative oscillator runs; independent scatter comparisons passed.')


if __name__ == '__main__':
    main()
