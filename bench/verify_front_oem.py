"""Separate ABI qualification of real OEM ADC keys and encoder EXTI handler.

This does not claim that the full application has finished booting.
"""
import argparse,json,hashlib
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
from emulate_front_v121 import FrontRunner
from emulate_nand_v121 import CapturedNand
from adc_dma import validate_profile
from audit_ram_v121 import RAM,RAM_SIZE,EXPECTED_SHA
from full_flash import load_full_flash


def qualify(firmware,nand_directory,sram):
    image=Path(firmware).read_bytes()
    fixture=Path(sram).read_bytes()
    assert hashlib.sha256(image).hexdigest()==EXPECTED_SHA and len(fixture)==RAM_SIZE
    profile=validate_profile(json.loads((Path(__file__).parent/'profiles/front_panel.json').read_text()))
    r=FrontRunner(image,CapturedNand(nand_directory),profile=profile)
    load_full_flash(r,Path(firmware).parent/'full_flash_pass1.bin')
    r.cpu.mem_write(RAM,fixture)
    r.cpu.reg_write(UC_ARM_REG_SP,0x20017000)
    r.core[0xD08]=0x08006000
    r.clock.regs.update({0:0x03030083,4:0x0021040A,0x14:0x15,0x18:0x4BFD,0x1C:0x200A003D})
    sentinel=0x08006D40
    active={'returned':False}
    def end(uc,address,size,data):
        if address==sentinel:
            active['returned']=True
            uc.emu_stop()
    r.cpu.hook_add(UC_HOOK_CODE,end)
    def call(address,*values):
        active['returned']=False
        r.cpu.reg_write(UC_ARM_REG_LR,sentinel|1)
        for reg,value in zip((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3),values):
            r.cpu.reg_write(reg,value)
        start=address|1
        limit=r.steps+2000000
        while not active['returned'] and r.steps<limit:
            r.cpu.emu_start(start,0,count=min(10000,limit-r.steps))
            if r.stop:
                r.service_extra_stop()
                assert r.stop is None,r.stop
            start=r.cpu.reg_read(UC_ARM_REG_PC)|1
        assert active['returned'],'OEM function failed to return'
        return r.cpu.reg_read(UC_ARM_REG_R0)
    call(0x0808B7B4)
    call(0x0808CADA,1000)
    observed={}
    for key,expected in [('P1',0x14),('P2',0x15),('P3',0x16),('MENU',0xE),
                         ('P4',0x17),('P5',0x18),('P6',0x19),('EXIT',0xF)]:
        r.input_command({'control':'RELEASE_KEYS'})
        r.input_command({'control':key})
        call(0x0808CADA,1000)
        actual=call(0x0800F08A if key in ('P1','P2','P3','MENU') else 0x0800F048)
        assert actual==expected,(key,actual,expected)
        observed[key]=actual
    r.input_command({'control':'RELEASE_KEYS'})
    assert call(0x0800F11C)==0
    r.input_command({'control':'DIAL_PUSH'})
    assert call(0x0800F11C)==0x1E
    observed['DIAL_PUSH']=0x1E
    r.input_command({'control':'RELEASE_KEYS'})
    call(0x0808C9EC)
    for direction,flag in [('DIAL_UP',0x2000114F),('DIAL_DOWN',0x20001150)]:
        r.input_command({'control':direction})
        call(0x0808CADA,100)
        assert bytes(r.cpu.mem_read(flag,1))==b'\x01'
    assert sum(e['name']=='IRQ23' and e.get('returned',False) for e in r.irq_log)==2
    call(0x08007CAA)
    assert call(0x08007DB6,0x082F5800)==4
    assert bytes(r.cpu.mem_read(0x082F5000,4096))==b'\xFF'*4096
    assert call(0x08008184,0x082F5800,0x1234)==4
    assert bytes(r.cpu.mem_read(0x082F5800,2))==b'\x34\x12'
    assert bytes(r.cpu.mem_read(0x08006000,len(image)))==image
    assert call(0x0808CD6C,0x002F5800)==0x1234
    assert call(0x0808CD6C,0x00000020)==0
    assert call(0x0808CD6C,0x0000003E)==0x0800
    call(0x080733A4)
    call(0x0808A9E4)
    assert call(0x0808ABDC,0x44,1)==0x00FF
    call(0x0808AB18,0x44,0x0732,1)
    assert call(0x0808ABDC,0x44,1)==0x0732
    r.idle_clock_scale=4096
    r.systick.update({0x10:1,0x14:14999999,0x18:14999999})
    delays={}
    for microseconds in (1,100):
        start=r.virtual_units
        call(0x08009EEA,microseconds)
        elapsed=r.virtual_units-start
        assert 120*microseconds<=elapsed<=120*microseconds+512,(microseconds,elapsed)
        delays[str(microseconds)]=elapsed
    call(0x0808D244)
    call(0x0807489C)
    fm_frames=r.fm_i2c.frames
    assert fm_frames[0]['payload']==[0,2],fm_frames
    assert fm_frames[1]['payload']==list(r.cpu.mem_read(0x080C0A24,64)),fm_frames
    assert all(frame['command']==0x20 for frame in fm_frames)
    # Actual weak SVC vector (BX LR), with a thread basic frame on each stack.
    from audit_ram_v121 import APP
    r.systick[0x10]=0
    r.cpu.reg_write(UC_ARM_REG_XPSR,0x01000000)
    r.cpu.reg_write(UC_ARM_REG_CONTROL,0)
    r.cpu.reg_write(UC_ARM_REG_MSP,0x20017000)
    r.cpu.reg_write(UC_ARM_REG_PC,sentinel|1)
    r.deliver_systick(11)
    assert r.stop is None,r.stop
    assert r.cpu.reg_read(UC_ARM_REG_SP)==0x20017000
    r.cpu.reg_write(UC_ARM_REG_PSP,0x20016000)
    r.cpu.reg_write(UC_ARM_REG_CONTROL,2)
    r.cpu.reg_write(UC_ARM_REG_PC,sentinel|1)
    r.deliver_systick(11)
    assert r.stop is None,r.stop
    assert r.cpu.reg_read(UC_ARM_REG_SP)==0x20016000
    assert r.cpu.reg_read(UC_ARM_REG_XPSR)&0x1000000
    r.cpu.reg_write(UC_ARM_REG_PRIMASK,1)
    r.halt('SysTick exception delivery required')
    assert r.stop is None and 15 in r.core_pending
    r.cpu.reg_write(UC_ARM_REG_PRIMASK,0)
    r.deliver_systick()
    assert r.stop is None and 15 not in r.core_pending,r.stop
    r.cpu.reg_write(UC_ARM_REG_CONTROL,0)
    r.cpu.reg_write(UC_ARM_REG_MSP,0x20017000)
    r.systick.update({0x10:1,0x14:14999999,0x18:14999999})
    call(0x08092F06)
    call(0x080A2B66)
    call(0x080A2AA4)
    assert r.sct_hpi.boot_complete and len(r.sct_hpi.boot_received)==2048
    assert bytes(r.sct_hpi.boot_received)==bytes(r.cpu.mem_read(0x080F56CC,2048))
    assert call(0x080A2B7A)==1
    assert r.sct_hpi.read_bytes==8
    r.cpu.mem_write(0x20016F00,b'\x01')  # isolated command-buffer test fixture
    assert call(0x080A8FD2,0x2D,0,0x20016F00,200)==3
    assert r.sct_hpi.controls[0x2D]==b'\x01'
    for register,value in ((0x0C,0),(0x60,0),(0x61,0),(0x65,127),(0x67,0)):
        assert call(0x0808ABDC,register,0)==value
    call(0x080AF930)
    assert r.usbd.read(0x40,4)==0xFF00 and r.usbd.read(0x44,4)==0
    return dict(passed=True,evidence_kind='separate authentic OEM function qualification',
        keys_returned_by_OEM=observed,encoder_IRQ23_returns=2,
        ADC_DMA_transfers=r.adc_dma.total_transfers,firmware_patched=False,
        FMC_OEM_unlock_erase_program_readback=True,flash_cache=r.flash_cache.describe(),
        full_flash_source=r.full_flash_source,boot_alias_reads=r.boot_alias_reads,
        RF_gain_OEM_GPIO_read_write_readback=r.rf_spi.describe(),
        FM_initialisation_OEM_GPIO=r.fm_i2c.describe(),
        native_exception_frames_MSP_PSP_and_masked_pending_tick=True,
        native_SCT_HPI_boot_and_response=r.sct_hpi.describe(),
        OEM_delay_microseconds_to_virtual_units=delays,
        direct_key_or_encoder_event_write_to_RAM=False,
        physical_key_order_confirmed_by_continuity=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('firmware',type=Path)
    p.add_argument('nand_directory',type=Path)
    p.add_argument('sram',type=Path)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    result=qualify(a.firmware,a.nand_directory,a.sram)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
