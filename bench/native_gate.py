"""Instruction-clock batching between existing model event boundaries.

The native hook counts every instruction. Python handles all model deadlines,
special PCs and MMIO. Audit mode retains the original per-instruction path.
"""
import ctypes as C,re,sys
from pathlib import Path
from unicorn.unicorn_py3.unicorn import uclib
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE

NOTIFY=C.CFUNCTYPE(None,C.c_void_p,C.c_uint64,C.c_uint32,C.c_void_p)
class Gate(C.Structure):
    _fields_=[('pending',C.c_uint64),('until',C.c_uint64),('address',C.c_uint64),
              ('size',C.c_uint32),('start',C.c_uint32),('end',C.c_uint32),('app',C.c_uint32),
              ('traps',C.POINTER(C.c_ubyte)),('notify',NOTIFY),('calls',C.c_uint64),('instructions',C.c_uint64)]

class NativeGate:
    def __init__(self,r):
        self.r=r;self.busy=False;self.error=None
        suffix='.dll' if sys.platform=='win32' else '.dylib' if sys.platform=='darwin' else '.so'
        library=Path(__file__).with_name(('native_gate' if sys.platform=='win32' else 'native_gate_host')+suffix)
        if not library.is_file():
            raise RuntimeError('Native counter missing: run python build_native.py, or select --engine python')
        self.dll=C.CDLL(str(library))
        self.bitmap=(C.c_ubyte*(0x300000//2))()
        self.callback=NOTIFY(self.notify)
        self.state=Gate(0,1,0,0,0x08000000,0x08006000+len(r.image),0x08006000,self.bitmap,self.callback,0,0)
        traps=set(r.LABELS)
        from firmware_profile import HOOKS
        traps.update(HOOKS)
        for name in ['emulate_nand_v121.py','emulate_front_v121.py','emulate_lcd_v121.py','lab_runner.py','bench_runner.py']:
            text=Path(__file__).with_name(name).read_text(encoding='utf-8')
            traps.update(int(value,16) for value in re.findall(r'0x0?80[0-9A-Fa-f]{5}',text))
        # Sleep opcodes require precise entry handling, including in a new image.
        image=bytes(r.cpu.mem_read(0x08000000,self.state.end-0x08000000))
        traps.update(0x08000000+i for i in range(0,len(image)-1,2) if image[i:i+2] in (b'\x20\xbf',b'\x30\xbf'))
        for pc in traps:self.trap(pc)
        r.cpu.hook_del(r.code_hook)
        self.handle=C.c_uint64()
        result=uclib.uc_hook_add(r.cpu._uch,C.byref(self.handle),UC_HOOK_CODE,
            C.cast(self.dll.gate_code,C.c_void_p),C.cast(C.pointer(self.state),C.c_void_p),1,0)
        if result:raise RuntimeError('Native scheduler hook could not be attached: '+str(result))
        self.original_start=r.cpu.emu_start
        def start(*args,**kwargs):
            try:return self.original_start(*args,**kwargs)
            finally:self.sync()
        r.cpu.emu_start=start
        r.native_gate=self
        self.memory_hook=r.cpu.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,
            lambda *args:self.sync(),begin=0x40000000,end=0xE000EFFF)
        self.refresh()

    def trap(self,pc):
        if 0x08000000<=pc<self.state.end:self.bitmap[(pc-0x08000000)//2]=1

    def quiet(self,count):
        if not count:return
        r=self.r
        # No event may be crossed here. All extras are handled at trapped PCs.
        if r.configuration and r.systick[0x10]&1:
            divider=1 if r.systick[0x10]&4 else 8
            ticks,r.tick_fraction=divmod(r.tick_fraction+count,divider)
            old=r.systick[0x18];reload=r.systick[0x14]
            if reload or old:
                distance=old if old else reload+1
                if ticks>=distance:raise RuntimeError('Native scheduler crossed a SysTick deadline')
                if ticks:r.systick[0x18]=distance-ticks
        r.steps+=count;r.virtual_units+=count;r.last_instruction_units=1
        r.adc_dma.step=r.steps

    def sync(self):
        if self.busy:return
        pending=self.state.pending
        if pending:
            self.state.pending=0;self.quiet(pending)
        self.refresh()
        if self.error:raise self.error

    def refresh(self):
        r=self.r
        deadlines=[64,max(1,r.peripheral_deadline-r.virtual_units),max(1,r.input_poll-r.steps)]
        if r.adc_dma.active and r.adc_dma.next_step is not None:deadlines.append(max(1,r.adc_dma.next_step-r.steps))
        if r.configuration and r.systick[0x10]&1 and (r.systick[0x14] or r.systick[0x18]):
            divider=1 if r.systick[0x10]&4 else 8
            deadlines.append(max(1,(r.systick[0x18] or r.systick[0x14]+1)*divider-r.tick_fraction))
        if hasattr(r,'serial_next'):deadlines.append(max(1,r.serial_next-r.serial_time()))
        if hasattr(r,'lab_next'):deadlines.append(max(1,r.lab_next-r.steps))
        if hasattr(r,'rx_poll'):deadlines.append(max(1,r.rx_poll-r.steps))
        if r.live_directory:deadlines.append(max(1,100000+r.last_publish-r.steps))
        if r.core_pending:deadlines.append(1)
        if r.pending_read_checks:self.trap(r.pending_read_checks[-1]['return_pc'])
        self.state.until=min(deadlines)

    def notify(self,uc,address,size,opaque):
        try:
            pending=self.state.pending;self.state.pending=0
            self.quiet(pending-1)
            self.busy=True
            self.r.on_code(self.r.cpu,address,size,None)
            self.busy=False;self.refresh()
        except BaseException as error:
            self.busy=False;self.error=error;self.r.cpu.emu_stop()

    def describe(self):
        return dict(engine='native instruction counter with Python event deadlines',
                    counted_instructions=self.state.instructions,Python_scheduler_calls=self.state.calls,
                    skipped_firmware_instructions=False,cycle_accurate=False)
