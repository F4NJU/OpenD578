"""Isolated host qualification: real OEM AT builder + UART3 IRQ + parser.

This uses an explicitly supplied startup SRAM fixture and calls genuine
OEM routines by ABI. It is separate from the full-reset LCD scenario.
No firmware bytes or return instructions are patched.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_PC,UC_ARM_REG_SP,UC_ARM_REG_LR,
    UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)
from emulate_lcd_v121 import LcdRunner
from emulate_nand_v121 import CapturedNand
from audit_ram_v121 import RAM, RAM_SIZE, EXPECTED_SHA


def qualify(firmware,nand_directory,sram):
    image=Path(firmware).read_bytes()
    assert hashlib.sha256(image).hexdigest()==EXPECTED_SHA
    assert Path(sram).stat().st_size==RAM_SIZE
    runner=LcdRunner(image,CapturedNand(nand_directory),bluetooth='et12')
    runner.cpu.mem_write(RAM,Path(sram).read_bytes())
    runner.clock.regs.update({0:0x03030083,4:0x0021040A,0x14:0x15,0x18:0x4BFD,0x1C:0x200A003D})
    runner.cpu.reg_write(UC_ARM_REG_SP,0x20017000)
    active={'call':False,'returned':False}
    sentinel=0x08006D40

    def end_call(uc,address,size,data):
        if active['call'] and address==sentinel:
            active['returned']=True
            uc.emu_stop()
    runner.cpu.hook_add(UC_HOOK_CODE,end_call)

    def execute(start,budget=200000,until_wire_empty=False):
        target=runner.steps+budget
        while runner.steps<target:
            runner.cpu.emu_start(start|1,0,count=min(20000,target-runner.steps))
            if runner.stop:
                runner.service_extra_stop()
                if runner.stop:
                    raise AssertionError(runner.stop)
            if active['returned']:
                return
            if until_wire_empty and not runner.uart3.rx_wire and runner.uart3.received_data is None:
                return
            start=runner.cpu.reg_read(UC_ARM_REG_PC)
        raise AssertionError('OEM qualification instruction budget exhausted')

    def call(address,args):
        active.update(call=True,returned=False)
        for register,value in zip((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3),args):
            runner.cpu.reg_write(register,value)
        runner.cpu.reg_write(UC_ARM_REG_LR,sentinel|1)
        execute(address)
        assert active['returned']
        active['call']=False

    call(0x080777D0,[115200])
    ver=image.index(b'VER?\0')+0x08006000
    runner.cpu.mem_write(runner.cpu.reg_read(UC_ARM_REG_SP),struct.pack('<I',0))
    call(0x08077E8E,[0,ver,4,0])
    active['returned']=False
    execute(sentinel,until_wire_empty=True)
    observed=bytes(runner.cpu.mem_read(0x2000C0E8,30)).split(b'\0')[0]
    assert observed==b'ET12_AQQX_V10043',repr(observed)
    assert bytes(runner.uart3.tx)==b'AT+VER?\r\n'
    assert runner.uart3.overruns==0
    assert all(x.get('returned') for x in runner.irq_log)
    return dict(passed=True,evidence_kind='isolated OEM routine qualification, not full boot',
        fixture='V4 startup SRAM before UART initialization',
        genuine_AT_request=bytes(runner.uart3.tx).decode(),
        version_stored_by_OEM=observed.decode(),
        IRQ52_returns=len(runner.irq_log), uart3=runner.uart3.describe(),
        firmware_patched=False, direct_version_write_to_RAM=False,
        skipped_firmware_functions=[], instructions=runner.steps)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('firmware',type=Path)
    p.add_argument('nand_directory',type=Path)
    p.add_argument('sram',type=Path)
    p.add_argument('--out',type=Path,default=Path('uart_oem_verification.json'))
    args=p.parse_args()
    result=qualify(args.firmware,args.nand_directory,args.sram)
    args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':
    main()
