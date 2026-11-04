#!/usr/bin/env python3
"""Continue the authentic D578 V1.21 startup with synthetic ADC0/DMA input."""
import argparse
import hashlib
import json
from pathlib import Path

from audit_ram_v121 import EXPECTED_SHA, require, hx
from emulate_clock_v121 import StopModel
from emulate_nand_v121 import CapturedNand, NandRunner
from adc_dma import ADC_BASE, AdcDma, validate_profile
from unicorn.arm_const import UC_ARM_REG_PC


class AdcRunner(NandRunner):
    def __init__(self, image, nand, poison=0xA5, profile=None, conversion_steps=64,
                 calibration_reads=2, **kwargs):
        self.adc_dma = None
        self.peripheral_events = []
        self.adc_reset_asserted = False
        super().__init__(image, nand, poison, **kwargs)
        self.adc_dma = AdcDma(self.cpu.mem_read, self.cpu.mem_write,
                             profile, conversion_steps, calibration_reads,
                             adc_clock_enabled=lambda: bool(self.clock.regs[0x18] & 0x200) and not bool(self.clock.regs[0xC] & 0x200),
                             dma_clock_enabled=lambda: bool(self.clock.regs[0x14] & 1))
        self.dma_regs = self.adc_dma.dma
        # ADC0 shares this MMIO page with adjacent, unsupported devices.
        self.cpu.mem_unmap(0x40012000, 4096)
        self.cpu.mmio_map(0x40012000, 4096, self.extra_read, None, self.extra_write, None)

    def extra_read(self, uc, off, size, data):
        address = 0x40012000 + off
        if ADC_BASE <= address <= ADC_BASE + 0x4C:
            return self.checked_read(lambda: self.adc_dma.read_adc(address - ADC_BASE, size),
                                     address, size, 'ADC0')
        return self.gpio_read_extra(uc, off, size, data)

    def extra_write(self, uc, off, size, value, data):
        address = 0x40012000 + off
        if ADC_BASE <= address <= ADC_BASE + 0x4C:
            self.checked_write(lambda: self.adc_dma.write_adc(address - ADC_BASE, value, size),
                               address, size, value, 'ADC0')
        else:
            self.gpio_write_extra(uc, off, size, value, data)

    def dma_read(self, uc, off, size, data):
        return self.checked_read(lambda: self.adc_dma.read_dma(off, size),
                                 0x40020000 + off, size, 'DMA0')

    def dma_write(self, uc, off, size, value, data):
        self.checked_write(lambda: self.adc_dma.write_dma(off, value, size),
                           0x40020000 + off, size, value, 'DMA0')

    def log(self, op, address, size, value, route):
        if route in ('ADC0', 'DMA0') and len(self.peripheral_events) < 4096:
            self.peripheral_events.append(dict(step=self.steps, op=op, address=hx(address),
                pc=hx(self.cpu.reg_read(UC_ARM_REG_PC)), size=size, value=hx(value), route=route))
        super().log(op, address, size, value, route)

    def on_code(self, uc, address, size, data):
        super().on_code(uc, address, size, data)
        if self.stop is not None or self.adc_dma is None:
            return
        try:
            reset = bool(self.clock.regs[0xC] & 0x200)
            if reset and not self.adc_reset_asserted:
                self.adc_dma.reset_adc()
            self.adc_reset_asserted = reset
            self.adc_dma.advance(self.steps)
            if self.adc_dma.irq_requested:
                # DMA0 ch0 is IRQ11. Preserve the pending state; interrupt
                # delivery for this peripheral remains an explicit boundary.
                self.nvic_pending[0] |= 1 << 11
                if self.nvic_enable[0] & (1 << 11):
                    raise StopModel('DMA0 channel 0 interrupt delivery not yet modelled')
        except StopModel as error:
            self.halt(str(error))

    def run_chunks(self, maximum, **kwargs):
        result, state = super().run_chunks(maximum, **kwargs)
        result.update(simulator_version='V4_ADC_DMA', adc_dma=self.adc_dma.describe(),
                      ADC_DMA_MMIO_events=self.peripheral_events,
                      DMA_transfers_executed=bool(self.adc_dma.total_transfers),
                      configured_DMA=self.adc_dma.descriptors,
                      source_radio_connected=False)
        return result, state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('firmware', type=Path)
    parser.add_argument('nand_directory', type=Path)
    parser.add_argument('--out', type=Path, default=Path('resultats_adc_v121.json'))
    parser.add_argument('--instructions', type=int, default=15_000_000)
    parser.add_argument('--poison', type=lambda x: int(x, 0), choices=(0xA5, 0x5A), default=0xA5)
    parser.add_argument('--adc-profile', type=Path,
                        help='Explicit synthetic 12-bit inputs; without it stop at first conversion')
    parser.add_argument('--conversion-steps', type=int, default=64,
                        help='Executed instructions per synthetic conversion, not hardware cycles')
    parser.add_argument('--calibration-reads', type=int, default=2)
    parser.add_argument('--wake-once', action='store_true')
    parser.add_argument('--idle-clock-scale', type=int, choices=(1, 8, 64), default=64)
    args = parser.parse_args()
    if args.instructions < 1:
        parser.error('--instructions must be positive')
    profile = validate_profile(json.loads(args.adc_profile.read_text(encoding='utf-8-sig'))) if args.adc_profile else None
    image = args.firmware.read_bytes()
    require(hashlib.sha256(image).hexdigest() == EXPECTED_SHA, 'Wrong firmware')
    nand = CapturedNand(args.nand_directory)
    runner = AdcRunner(image, nand, args.poison, profile, args.conversion_steps,
                       args.calibration_reads, wake_once=args.wake_once,
                       idle_clock_scale=args.idle_clock_scale)
    result, state = runner.run_chunks(args.instructions)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    args.out.with_suffix('.sram.bin').write_bytes(state)
    print(json.dumps(dict(stop=result['stop'], steps=result['steps'],
        adc_transfers=result['adc_dma']['total_transfers'],
        adc_sequences=result['adc_dma']['completed_sequences'],
        verified_nand_buffers=len(result['verified_RAM_reads'])), indent=2))


if __name__ == '__main__':
    main()
