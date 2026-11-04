"""Select a virtual application/full Flash while retaining baseline provenance."""
from pathlib import Path
import hashlib,struct
from audit_ram_v121 import APP,RAM,RAM_SIZE,EXPECTED_SHA
from full_flash import FLASH,SIZE,load_full_flash,FULL_SHA
from unicorn.arm_const import UC_ARM_REG_SP,UC_ARM_REG_PC,UC_ARM_REG_XPSR

def validate_vectors(data,base):
    if len(data)<256:raise ValueError('Image trop courte : table des vecteurs absente')
    sp,entry=struct.unpack_from('<II',data)
    if not RAM<sp<=RAM+RAM_SIZE or sp%8:raise ValueError('Pile initiale hors SRAM GD32 ou non alignée')
    if not entry&1 or not base<=entry&~1<base+len(data):raise ValueError('Reset_Handler Thumb hors image')
    return sp,entry

def inspect_image(path):
    path=Path(path);data=path.read_bytes()
    full=len(data)==SIZE
    if not full and (path.suffix.lower() not in ('.cdd','.bin') or len(data)>SIZE-(APP-FLASH)):
        raise ValueError('Choisir une application brute .CDD/.bin ou une Flash complète de 3 Mio')
    app=data[APP-FLASH:] if full else data
    sp,entry=validate_vectors(app,APP)
    return data,app,dict(path=str(path.resolve()),sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),
        format='full_flash_3MiB' if full else 'raw_application_at_08006000',
        application_sha256=hashlib.sha256(app).hexdigest(),initial_SP=hex(sp),reset_entry=hex(entry),
        model='D578 GD32 V1.21; compatibility of experimental code is not certified',source_modified=False)

def load_selected(runner,base_flash,selected=None,entry='application'):
    # The original board image is always authenticated first, including its
    # baseline application. Selection changes only this process's memory.
    baseline=runner.image
    load_full_flash(runner,base_flash)
    metadata=dict(path=str(Path(base_flash).resolve()),sha256=FULL_SHA,format='baseline',
        application_sha256=hashlib.sha256(baseline).hexdigest(),experimental=False,source_modified=False)
    if selected:
        data,app,metadata=inspect_image(selected)
        full=metadata['format']=='full_flash_3MiB'
        runner.cpu.mem_write(FLASH if full else APP,data)
        runner.image=app
        metadata['experimental']=data!=Path(base_flash).read_bytes() if full else app!=baseline
        runner.full_flash_source['application_matches_CDD']=app[:len(baseline)]==baseline
        runner.full_flash_source['selection_overlaid_in_virtual_memory']=True
    flash=bytes(runner.cpu.mem_read(FLASH,SIZE))
    vectors=flash if entry=='bootloader' else flash[APP-FLASH:APP-FLASH+len(runner.image)]
    sp,pc=validate_vectors(vectors,FLASH if entry=='bootloader' else APP)
    runner.reset_entry=pc
    runner.cpu.reg_write(UC_ARM_REG_SP,sp);runner.cpu.reg_write(UC_ARM_REG_PC,pc|1)
    runner.cpu.reg_write(UC_ARM_REG_XPSR,0x01000000)
    runner.firmware_selection=metadata
    runner.firmware_selection['reset_kind']=entry
    runner.full_flash_source['initial_pc_source']=entry+' Reset_Handler in this process'
    # Selection may have a different application length. Do not keep the old
    # execution bound from load_full_flash(). Peripheral coverage remains finite.
    runner.authenticated_execution_ranges=((FLASH,APP+len(runner.image)),)
    from firmware_profile import inspect_profile
    runner.observation_profile=inspect_profile(baseline,runner.image)
    return metadata
