#!/usr/bin/env python3
"""D578 V5: capture authentic LCD bus pixels during the emulated startup."""
import argparse
import hashlib
import json
import time
from pathlib import Path
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_PRIMASK,
                               UC_ARM_REG_FAULTMASK, UC_ARM_REG_BASEPRI)
from adc_dma import validate_profile
from audit_ram_v121 import EXPECTED_SHA, require
from emulate_adc_v121 import AdcRunner
from emulate_nand_v121 import CapturedNand
from lcd_bus import LcdBus
from uart_serial import Uart3, BluetoothPeer, IdlePeer


class LcdRunner(AdcRunner):
    def __init__(self, *args, live_directory=None, bluetooth='absent', fast_mode=True, **kwargs):
        self.fast_mode = fast_mode
        self.lcd = LcdBus()
        self.live_directory = Path(live_directory) if live_directory else None
        self.last_publish = 0
        self.uart3 = None
        self.uart_reset_asserted = False
        super().__init__(*args, **kwargs)
        self.uart3 = Uart3(BluetoothPeer(bluetooth),
                          clock_enabled=lambda: bool(self.clock.regs[0x1C] & (1 << 19)) and not bool(self.clock.regs[0x10] & (1 << 19)))
        self.cpu.mmio_map(0x40004000, 4096, self.serial_read, None, self.serial_write, None)
        self.usart0 = Uart3(IdlePeer(), name='USART0',
            clock_enabled=lambda: bool(self.clock.regs[0x18] & (1 << 14)) and not bool(self.clock.regs[0xC] & (1 << 14)))
        self.usart1 = Uart3(IdlePeer(), name='USART1',
            clock_enabled=lambda: bool(self.clock.regs[0x1C] & (1 << 17)) and not bool(self.clock.regs[0x10] & (1 << 17)))
        self.serial_devices = {0x40013800:(self.usart0,37,0xC,14),
                               0x40004400:(self.usart1,38,0x10,17),
                               0x40004C00:(self.uart3,52,0x10,19)}
        self.serial_resets = dict.fromkeys(self.serial_devices, False)
        self.serial_next = 10**30
        self.cpu.mmio_map(0x40013000, 4096,
            lambda uc,off,size,data:self.serial_read_at(0x40013000+off,size), None,
            lambda uc,off,size,value,data:self.serial_write_at(0x40013000+off,size,value), None)

    def serial_device(self, address):
        for base, spec in self.serial_devices.items():
            if base <= address < base + 0x18:
                return base, spec[0]
        return None, None

    def serial_read_at(self, address, size):
        base, device = self.serial_device(address)
        if device is None:
            self.halt('serial peripheral outside qualified subset', address)
            return 0
        device.advance(self.serial_time())
        value = self.checked_read(lambda: device.read(address-base, size), address, size, device.name)
        self.serial_deadline()
        return value

    def serial_write_at(self, address, size, value):
        base, device = self.serial_device(address)
        if device is None:
            self.halt('serial peripheral outside qualified subset', address)
            return
        device.advance(self.serial_time())
        self.checked_write(lambda: device.write(address-base, size, value), address, size, value, device.name)
        if getattr(self,'serial_virtual_time',False) and device.regs[8]:
            device.byte_steps=device.regs[8]*10*(1 if base==0x40013800 else 2)
        self.serial_deadline()

    def serial_time(self):
        return self.virtual_units if getattr(self,'serial_virtual_time',False) else self.steps

    def serial_deadline(self):
        deadlines=[]
        for device,_,_,_ in self.serial_devices.values():
            if device.tx_shift:
                deadlines.append(device.tx_shift[1])
            if device.rx_wire:
                deadlines.append(device.rx_wire[0][0])
            if device.irq:
                deadlines.append(self.serial_time()+1)
        self.serial_next=min(deadlines,default=10**30)

    def clock_set(self,off,size,value):
        super().clock_set(off,size,value)
        self.serial_reset_update()

    def alias_set(self,off,size,value):
        super().alias_set(off,size,value)
        self.serial_reset_update()

    def serial_reset_update(self):
        if not hasattr(self,'serial_devices'):
            return
        for base,(device,irq,reg,bit) in self.serial_devices.items():
            reset=bool(self.clock.regs[reg] & (1<<bit))
            if reset and not self.serial_resets[base]:
                device.reset()
            self.serial_resets[base]=reset
        self.serial_deadline()

    def serial_read(self, uc, off, size, data):
        return self.serial_read_at(0x40004000 + off, size)

    def serial_write(self, uc, off, size, value, data):
        self.serial_write_at(0x40004000 + off, size, value)

    def gpio_set(self, off, size, value):
        address = 0x40010000 + off
        before = self.gpio[0x40010C00][0xC] if 0x40010C00<=address<0x40011000 else None
        super().gpio_set(off, size, value)
        if before is not None and not before&0x400 and self.gpio[0x40010C00][0xC]&0x400:
            self.lcd.step = self.steps
            self.lcd.gpio(before, self.gpio[0x40010C00][0xC], self.gpio[0x40011800][0xC])

    def on_code(self, uc, address, size, data):
        super().on_code(uc, address, size, data)
        if address == 0x0808B672:
            # Ignore output changes made while configuring GPIO/reset lines;
            # start sampling at the first proven OEM command call.
            self.lcd.armed = True
            self.lcd.expected_commands.append(uc.reg_read(UC_ARM_REG_R0) & 255)
        if hasattr(self, 'serial_next') and self.serial_time()>=self.serial_next and self.stop is None:
            from emulate_clock_v121 import StopModel
            try:
                for base, (device,irq,reset_reg,reset_bit) in self.serial_devices.items():
                    if device.tx_shift or device.rx_wire:
                        device.advance(self.serial_time())
                    if device.irq:
                        self.nvic_pending[irq//32] |= 1 << (irq%32)
                        priority = (self.nvic_priorities.get(0x400+(irq & ~3),0) >> (8*(irq%4))) & 255
                        basepri = uc.reg_read(UC_ARM_REG_BASEPRI)
                        eligible = not (uc.reg_read(UC_ARM_REG_PRIMASK) or uc.reg_read(UC_ARM_REG_FAULTMASK)) and (not basepri or priority < basepri)
                        if not self.irq_active and self.nvic_enable[irq//32] & (1 << (irq%32)) and eligible:
                            self.halt('serial interrupt delivery required', irq=irq)
                self.serial_deadline()
            except StopModel as error:
                self.halt(str(error))
        if self.live_directory and self.steps - self.last_publish >= 100000:
            self.publish()

    def publish(self, final=False):
        if self.live_directory is None:
            return
        target = self.live_directory
        target.mkdir(parents=True, exist_ok=True)
        if self.lcd.dirty or final:
            self.lcd.save(target/'lcd.png')
            self.lcd.save(target/'lcd_gram.png', honor_display=False)
        status = dict(steps=self.steps, running=not final, stop=self.stop,
                      pixels=self.lcd.total_pixels, width=self.lcd.width, height=self.lcd.height,
                      display_on=self.lcd.display_on, sleeping=self.lcd.sleeping,
                      NAND_buffers=len(self.verified_RAM_reads),
                      ADC_transfers=self.adc_dma.total_transfers)
        status['application_running']=bytes(self.cpu.mem_read(0x20001542,1))==b'\x01'
        status['quick_resume']=hasattr(self,'session_origin')
        status['model_seconds']=round(getattr(self,'tick_wraps',0)*.005,3)
        status['execution_engine']='native' if getattr(self,'native_gate',None) else 'python'
        if hasattr(self,'hardware_state'):status['hardware']=self.hardware_state()
        if hasattr(self,'lighting'):
            status['lighting']={k:v for k,v in self.lighting.describe().items() if k!='frames'}
        from live_io import publish_status
        publish_status(target/'status.json',status,final)
        self.last_publish = self.steps
        if not final and (target/'stop.request').exists():
            self.halt('stopped by simulator user')

    def run_chunks(self, *args, **kwargs):
        result, state = super().run_chunks(*args, **kwargs)
        result.update(simulator_version='V8', lcd=self.lcd.describe(), uart3=self.uart3.describe(),
                      usart0=self.usart0.describe(), usart1=self.usart1.describe())
        self.publish(final=True)
        return result, state

    def service_extra_stop(self):
        if self.stop and self.stop['kind'] == 'serial interrupt delivery required':
            irq = self.stop['irq']
            self.stop = None
            self.deliver_systick(exception=irq+16)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('firmware', type=Path)
    parser.add_argument('nand_directory', type=Path)
    parser.add_argument('--out', type=Path, default=Path('results/lcd.json'))
    parser.add_argument('--instructions', type=int, default=15_000_000)
    parser.add_argument('--adc-profile', type=Path, default=Path(__file__).parent/'profiles/diagnostic.json')
    parser.add_argument('--poison', type=lambda x:int(x,0), default=0xA5)
    parser.add_argument('--wake-once', action='store_true')
    args = parser.parse_args()
    image = args.firmware.read_bytes()
    require(hashlib.sha256(image).hexdigest() == EXPECTED_SHA, 'Wrong firmware')
    profile = validate_profile(json.loads(args.adc_profile.read_text(encoding='utf-8')))
    nand = CapturedNand(args.nand_directory)
    runner = LcdRunner(image, nand, args.poison, profile=profile,
                       wake_once=args.wake_once, idle_clock_scale=64,
                       live_directory=args.out.parent)
    result, state = runner.run_chunks(args.instructions)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    args.out.with_suffix('.sram.bin').write_bytes(state)
    print(json.dumps(dict(stop=result['stop'], lcd={k:v for k,v in result['lcd'].items() if k!='commands'}), indent=2))


if __name__ == '__main__':
    main()
