"""Instruction-clock batching between existing model event boundaries.

The native hook counts every instruction. Python handles all model deadlines,
special PCs and MMIO. Audit mode retains the original per-instruction path.
"""
import ctypes as C,re,sys,ast
from pathlib import Path
from unicorn.unicorn_py3.unicorn import uclib
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE

REG_READ=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_int,C.c_void_p)
NOTIFY=C.CFUNCTYPE(None,C.c_void_p,C.c_uint64,C.c_uint32,C.c_void_p)
class Gate(C.Structure):
    _fields_=[('pending',C.c_uint64),('until',C.c_uint64),('address',C.c_uint64),
              ('size',C.c_uint32),('start',C.c_uint32),('end',C.c_uint32),('app',C.c_uint32),
              ('traps',C.POINTER(C.c_ubyte)),('notify',NOTIFY),('calls',C.c_uint64),('instructions',C.c_uint64),('mask_tracking',C.c_uint32),('reg_read',REG_READ),
              ('reg_basepri',C.c_uint32),('reg_primask',C.c_uint32),
              ('reg_faultmask',C.c_uint32),('mask_priority',C.c_uint32)]

class NativeGate:
    def __init__(self,r,hardware=False):
        self.r=r;self.hardware=hardware;self.busy=False;self.error=None;self.lcd_bridge=None
        suffix='.dll' if sys.platform=='win32' else '.dylib' if sys.platform=='darwin' else '.so'
        library=Path(__file__).with_name(('native_gate' if sys.platform=='win32' else 'native_gate_host')+suffix)
        if not library.is_file():
            raise RuntimeError('Native counter missing: run python build_native.py, or select --engine python')
        self.dll=C.CDLL(str(library))
        self.bitmap=(C.c_ubyte*(0x300000//2))()
        self.callback=NOTIFY(self.notify)
        end=0x08300000 if hardware else 0x08006000+len(r.image)
        self.state=Gate(0,1,0,0,0x08000000,end,0x08006000,self.bitmap,self.callback,0,0)
        from unicorn.arm_const import UC_ARM_REG_BASEPRI,UC_ARM_REG_PRIMASK,UC_ARM_REG_FAULTMASK
        self.state.reg_read=REG_READ(("uc_reg_read",uclib))
        self.state.reg_basepri=UC_ARM_REG_BASEPRI;self.state.reg_primask=UC_ARM_REG_PRIMASK
        self.state.reg_faultmask=UC_ARM_REG_FAULTMASK
        traps=set() if hardware else set(r.LABELS)
        from firmware_profile import HOOKS
        if not hardware:traps.update(HOOKS)
        for name in ([] if hardware else ['emulate_nand_v121.py','emulate_front_v121.py','emulate_lcd_v121.py','lab_runner.py','bench_runner.py']):
            text=Path(__file__).with_name(name).read_text(encoding='utf-8')
            if getattr(r,'interactive_mode',False):
                for node in ast.walk(ast.parse(text)):
                    if isinstance(node,ast.FunctionDef) and node.name=='on_code':
                        traps.update(value.value for value in ast.walk(node)
                            if isinstance(value,ast.Constant) and type(value.value) is int
                            and 0x08000000<=value.value<self.state.end)
            else:traps.update(int(value,16) for value in re.findall(r'0x0?80[0-9A-Fa-f]{5}',text))
        # Sleep opcodes require precise entry handling, including in a new image.
        image=bytes(r.cpu.mem_read(0x08000000,self.state.end-0x08000000))
        sleep_opcodes=(b'\x20\xbf',b'\x30\xbf',b'\x40\xbf') if hardware else (b'\x20\xbf',b'\x30\xbf')
        traps.update(0x08000000+i for i in range(0,len(image)-1,2) if image[i:i+2] in sleep_opcodes)
        mask_traps=set()
        for offset in range(0,len(image)-3,2):
            first=int.from_bytes(image[offset:offset+2],'little')
            second=int.from_bytes(image[offset+2:offset+4],'little')
            # Observe mask-changing instructions and the immediately following
            # instruction. A masked pending tick need not call Python at every
            # instruction inside a critical section.
            if first&0xFFE0==0xB660:
                mask_traps.add(0x08000000+offset+2)
            if first&0xFFF0==0xF380 and second&0xFF00==0x8800:
                mask_traps.add(0x08000000+offset+4)
        for pc in traps:self.trap(pc)
        for pc in mask_traps:
            if 0x08000000<=pc<self.state.end and not self.bitmap[(pc-0x08000000)//2]:self.bitmap[(pc-0x08000000)//2]=2
        r.cpu.hook_del(r.code_hook)
        self.handle=C.c_uint64()
        result=uclib.uc_hook_add(r.cpu._uch,C.byref(self.handle),UC_HOOK_CODE,
            C.cast(self.dll.gate_code,C.c_void_p),C.cast(C.pointer(self.state),C.c_void_p),1,0)
        if result:raise RuntimeError('Native scheduler hook could not be attached: '+str(result))
        self.original_start=r.cpu.emu_start
        def start(*args,**kwargs):
            self.refresh()
            try:return self.original_start(*args,**kwargs)
            finally:self.sync()
        r.cpu.emu_start=start
        r.native_gate=self
        if getattr(r,'interactive_mode',False):
            # GPIO/ADC/timer/UART/RCU callbacks already synchronize through
            # checked_read/write. Keep extra hooks only for bare callbacks.
            self.memory_hooks=[r.cpu.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,
                lambda *args:self.sync(),begin=first,end=last)
                for first,last in ((0x40007000,0x40007FFF),(0x40022000,0x40022FFF),(0x420E0000,0x420E0FFF))]
        else:
            self.memory_hook=r.cpu.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,
                lambda *args:self.sync(),begin=0x40000000,end=0xE000EFFF)
        self.adc_watch = None
        if getattr(r,'interactive_mode',False):
            from interactive_runtime import AdcWatch
            self.adc_watch = AdcWatch(self)
            from lcd_bridge import LcdBridge,library_path
            # The V11.2 NAND fast-input path uses OEM PC/R1 assumptions.
            # Hardware mode keeps its independent GPIO sampling path.
            if not hardware and library_path().is_file() and not getattr(r,'disable_native_lcd',False):self.lcd_bridge=LcdBridge(self)
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
        if self.adc_batching():
            from interactive_runtime import advance_adc_through
            advance_adc_through(r.adc_dma,r.virtual_units if getattr(self,'hardware',False) else r.steps)
        else:r.adc_dma.step=r.virtual_units if getattr(self,'hardware',False) else r.steps

    def sync(self):
        if self.busy:return
        if self.lcd_bridge:self.lcd_bridge.safe_flush()
        pending=self.state.pending
        if pending:
            self.state.pending=0;self.quiet(pending)
        self.refresh()
        if self.lcd_bridge and self.lcd_bridge.error:raise self.lcd_bridge.error
        if self.error:raise self.error

    def adc_batching(self):
        if not getattr(self.r,'interactive_mode',False) or getattr(self.r,'memory_watch',None):return False
        from interactive_runtime import adc_can_batch
        return adc_can_batch(self.r.adc_dma)

    def refresh(self):
        r=self.r
        if self.hardware:
            pending=r.pending_exceptions()
            self.state.until=min(4096,r.next_event_delay(),max(1,r.input_poll-r.steps),max(1,100000+r.last_publish-r.steps) if r.live_directory else 4096)
            self.state.mask_tracking=bool(pending and not r.irq_active)
            self.state.mask_priority=min((r.exception_priority(n) for n in pending),default=255)
            return
        deadlines=[4096 if getattr(r,'interactive_mode',False) else 64,max(1,r.peripheral_deadline-r.virtual_units),max(1,r.input_poll-r.steps)]
        if not self.adc_batching() and r.adc_dma.active and r.adc_dma.next_step is not None:deadlines.append(max(1,r.adc_dma.next_step-r.steps))
        if r.configuration and r.systick[0x10]&1 and (r.systick[0x14] or r.systick[0x18]):
            divider=1 if r.systick[0x10]&4 else 8
            deadlines.append(max(1,(r.systick[0x18] or r.systick[0x14]+1)*divider-r.tick_fraction))
        if hasattr(r,'serial_next'):deadlines.append(max(1,r.serial_next-r.serial_time()))
        if hasattr(r,'lab_next'):deadlines.append(max(1,r.lab_next-r.steps))
        if hasattr(r,'rx_poll'):deadlines.append(max(1,r.rx_poll-r.steps))
        if r.live_directory:deadlines.append(max(1,100000+r.last_publish-r.steps))
        if getattr(r,'fwdgt',None) and r.fwdgt.running:deadlines.append(max(1,r.fwdgt.deadline-r.virtual_units))
        if r.core_pending and any(r.exception_eligible(n) for n in r.core_pending):deadlines.append(1)
        if r.pending_read_checks:self.trap(r.pending_read_checks[-1]['return_pc'])
        self.state.until=min(deadlines)
        self.state.mask_tracking=bool(r.core_pending and not r.irq_active)
        self.state.mask_priority=min((r.exception_priority(n) for n in r.core_pending),default=255)
        if self.lcd_bridge:self.lcd_bridge.refresh()

    def notify(self,uc,address,size,opaque):
        try:
            if self.lcd_bridge:self.lcd_bridge.safe_flush()
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
                    skipped_firmware_instructions=False,cycle_accurate=False,
                    interactive_mode=getattr(self.r,'interactive_mode',False),
                    ADC_conversions_batched_without_dropping_samples=self.adc_batching(),
                    LCD_native_dispatch=self.lcd_bridge.describe() if self.lcd_bridge else None)
