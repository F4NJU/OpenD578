"""Restore only the authenticated session bundled with this simulator build.

The recorded state comes from a genuine application-reset execution. The CPU
continues from that state; no firmware function or event is patched into RAM.
Pickle is accepted only after checking the fixed build hash below, never from
arbitrary user-selected files.
"""
from pathlib import Path
import gzip,pickle,hashlib,io,collections
from unicorn.arm_const import *
from audit_ram_v121 import RAM,RAM_SIZE,EXPECTED_SHA

READY_SHA256='0323987aa8f21923f02cb587202d59ad9baf0a851c7eccfd2ed47b859af1ffec'
REGISTERS=[UC_ARM_REG_MSP,UC_ARM_REG_PSP,UC_ARM_REG_CONTROL,
    *range(UC_ARM_REG_R0,UC_ARM_REG_R12+1),UC_ARM_REG_SP,UC_ARM_REG_LR,
    UC_ARM_REG_PC,UC_ARM_REG_XPSR,UC_ARM_REG_PRIMASK,UC_ARM_REG_BASEPRI,
    UC_ARM_REG_FAULTMASK,UC_ARM_REG_FPSCR,*range(UC_ARM_REG_D0,UC_ARM_REG_D31+1)]

def components(r):
    return dict(clock=r.clock,nand=r.nand,lcd=r.lcd,adc_dma=r.adc_dma,
        uart3=r.uart3,usart0=r.usart0,usart1=r.usart1,backup=r.backup,
        lighting=r.lighting,status_led=r.status_led,flash_cache=r.flash_cache,rf_spi=r.rf_spi,
        fm_i2c=r.fm_i2c,sct_hpi=r.sct_hpi,usbd=r.usbd,fwdgt=r.fwdgt,
        **{'timer'+hex(key):value[0] for key,value in r.timers.items()})

def export_ready(r,path):
    excluded=set(components(r))|{'cpu','image','oem_reference','serial_devices','timers','dma_regs','native_gate','code_hook','memory_watch','control_inbox','cdc','cdc_sink'}
    parts={name:{key:value for key,value in vars(obj).items()
        if not callable(value) and key not in ('handles','images')}
        for name,obj in components(r).items()}
    state=dict(schema=1,firmware_sha256=EXPECTED_SHA,
        top={key:value for key,value in vars(r).items() if key not in excluded},parts=parts,
        registers={reg:r.cpu.reg_read(reg) for reg in REGISTERS},
        flash=bytes(r.cpu.mem_read(0x082F5000,0xB000)),ram=bytes(r.cpu.mem_read(RAM,RAM_SIZE)))
    data=gzip.compress(pickle.dumps(state,protocol=5),mtime=0)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()

class SessionUnpickler(pickle.Unpickler):
    """Read the fixed recording on either OS without changing pathlib globally."""
    def find_class(self,module,name):
        if module=='pathlib' and name in ('WindowsPath','PosixPath'):
            return Path
        if module=='collections' and name in ('Counter','deque'):
            return getattr(collections,name)
        if module=='uart_serial' and name in ('BluetoothPeer','IdlePeer'):
            import uart_serial
            return getattr(uart_serial,name)
        raise pickle.UnpicklingError('Unsupported recorded type: '+module+'.'+name)


def load_ready(r):
    path=Path(__file__).parent/'results/ready/session.pkl.gz'
    data=path.read_bytes()
    if not READY_SHA256 or hashlib.sha256(data).hexdigest()!=READY_SHA256:
        raise ValueError('Bundled ready session checksum does not match this build')
    state=SessionUnpickler(io.BytesIO(gzip.decompress(data))).load()
    if state['schema']!=1 or state['firmware_sha256']!=hashlib.sha256(r.image).hexdigest():
        raise ValueError('Bundled ready session does not match firmware')
    directory=r.live_directory
    vars(r).update(state['top'])
    for name,obj in components(r).items():
        if name in state['parts']:vars(obj).update(state['parts'][name])
    r.dma_regs=r.adc_dma.dma
    r.cpu.mem_write(RAM,state['ram'])
    r.cpu.mem_write(0x082F5000,state['flash'])
    for reg in REGISTERS:
        value=state['registers'][reg]
        r.cpu.reg_write(reg,value|1 if reg==UC_ARM_REG_PC else value)
    r.stop=None
    r.live_directory=directory
    r.lcd.dirty=True
    r.last_publish=0
    r.input_poll=r.steps
    r.session_origin=dict(kind='bundled recording from application reset',sha256=READY_SHA256,
        recorded_steps=r.steps,reset_replayed_this_process=False)
    return r.session_origin
