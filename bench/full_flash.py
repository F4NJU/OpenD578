"""Load the authenticated physical 3 MiB capture, including its boot alias."""
import hashlib
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_PC
from audit_ram_v121 import APP,EXPECTED_SHA,require

FLASH=0x08000000
SIZE=0x300000
FULL_SHA='e2f2483baf60e2bfcab656e25e949670713222591ef4d611d6089054819a750e'
BOOT_SHA='c098c74d2a979e162d6dd901c9d59d7ed3f0a4c9d526a168a1db78fba316fdeb'


def validate_full_flash(data,application):
    require(len(data)==SIZE,'Physical Flash capture must contain exactly 3 MiB')
    require(hashlib.sha256(data).hexdigest()==FULL_SHA,'Unexpected physical Flash capture SHA256')
    require(hashlib.sha256(data[:0x6000]).hexdigest()==BOOT_SHA,'Unexpected boot capture SHA256')
    require(hashlib.sha256(application).hexdigest()==EXPECTED_SHA,'Unexpected CDD')
    require(data[APP-FLASH:APP-FLASH+len(application)]==application,'Physical application differs from CDD')


def load_full_flash(runner,path):
    data=Path(path).read_bytes()
    validate_full_flash(data,runner.image)
    runner.cpu.mem_write(FLASH,data)
    runner.boot_alias_reads=[]
    runner.boot_alias_read_count=0
    # BOOT0=0 scenario. A read-only MMIO window keeps the low-address alias in
    # sync with the actual simulated Flash after any OEM cache programming.
    def alias_read(uc,offset,size,_):
        value=int.from_bytes(uc.mem_read(FLASH+offset,size),'little')
        runner.boot_alias_read_count+=1
        if len(runner.boot_alias_reads)<128:
            runner.boot_alias_reads.append(dict(step=runner.steps,address=hex(offset),size=size,
                value=hex(value),pc=hex(uc.reg_read(UC_ARM_REG_PC))))
        return value
    def alias_write(uc,offset,size,value,_):
        runner.halt('write to read-only boot Flash alias',offset,size=size)
    runner.cpu.mmio_map(0,SIZE,alias_read,None,alias_write,None)
    runner.authenticated_execution_ranges=((FLASH,APP+len(runner.image)),)
    runner.full_flash_source=dict(sha256=FULL_SHA,bytes=SIZE,boot_sha256=BOOT_SHA,
        application_matches_CDD=True,boot_alias_base=0,physical_flash_base=FLASH,
        initial_pc_source='application Reset_Handler; boot bytes loaded but boot Reset_Handler not executed',
        source_file_modified=False)
    return runner.full_flash_source
