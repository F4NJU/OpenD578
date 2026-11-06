"""Optional native GPIO dispatcher; the existing LCD controller decodes bytes."""
import ctypes as C
import sys
from pathlib import Path
from unicorn.unicorn_py3.unicorn import uclib
from emulate_clock_v121 import StopModel

READ=C.CFUNCTYPE(C.c_uint64,C.c_void_p,C.c_uint64,C.c_uint32,C.c_void_p)
WRITE=C.CFUNCTYPE(None,C.c_void_p,C.c_uint64,C.c_uint32,C.c_uint64,C.c_void_p)
FLUSH=C.CFUNCTYPE(None,C.c_void_p)
REG_READ=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_int,C.c_void_p)

class Edge(C.Structure):
    _fields_=[('step',C.c_uint64),('value',C.c_uint32),('data',C.c_uint32)]

class State(C.Structure):
    _fields_=[('instructions',C.POINTER(C.c_uint64)),('origin',C.c_uint64),
              ('reads',C.c_uint64),('writes',C.c_uint64),('port_b',C.c_uint32),
              ('port_e',C.c_uint32),('enabled',C.c_uint32),('count',C.c_uint32),
              ('slow_read',READ),('slow_write',WRITE),('flush',FLUSH),('edges',Edge*2048),
              ('reg_read',REG_READ),('reg_r1',C.c_uint32),('reg_pc',C.c_uint32),
              *[(name,C.c_uint32) for name in ('nand_enabled','nand_bits','nand_accumulator',
                'nand_input_count','nand_clk','nand_mosi','nand_miso','nand_io0','cache_size',
                'cache_column','seen_outputs','flushed_outputs')],
              ('cache',C.c_ubyte*2112),('input',C.c_ubyte*2112)]


def library_path():
    suffix='.dll' if sys.platform=='win32' else '.dylib' if sys.platform=='darwin' else '.so'
    return Path(__file__).with_name(('lcd_bridge' if sys.platform=='win32' else 'lcd_bridge_host')+suffix)


class LcdBridge:
    def __init__(self,gate,path=None):
        self.gate=gate;self.r=gate.r;self.error=None
        self.dll=C.CDLL(str(path or library_path()))
        self.state=State()
        self.state.instructions=C.cast(C.addressof(gate.state)+type(gate.state).instructions.offset,C.POINTER(C.c_uint64))
        self.state.origin=self.r.steps
        from unicorn.arm_const import UC_ARM_REG_R1,UC_ARM_REG_PC
        self.state.reg_read=REG_READ(("uc_reg_read",uclib))
        self.state.reg_r1=UC_ARM_REG_R1;self.state.reg_pc=UC_ARM_REG_PC
        self.state.slow_read=READ(self.read)
        self.state.slow_write=WRITE(self.write)
        self.state.flush=FLUSH(lambda opaque:self.safe_flush())
        self.opaque=C.cast(C.pointer(self.state),C.c_void_p)
        self.refresh()
        self.r.cpu.mem_unmap(0x40010000,8192)
        result=uclib.uc_mmio_map(self.r.cpu._uch,0x40010000,8192,
            C.cast(self.dll.lcd_bridge_read,C.c_void_p),self.opaque,
            C.cast(self.dll.lcd_bridge_write,C.c_void_p),self.opaque)
        if result:raise RuntimeError('Native LCD dispatcher could not attach: '+str(result))
        self.total_reads=self.total_writes=self.total_edges=self.total_nand_bytes=0

    def refresh(self,from_slow=False):
        self.state.port_b=self.r.gpio[0x40010C00][12]
        self.state.port_e=self.r.gpio[0x40011800][12]
        self.state.enabled=bool(self.r.lcd.armed and not self.r.trace_enabled
                                and not getattr(self.r,'memory_watch',None))
        nand=getattr(self.r,'nand',None)
        active=bool(self.state.enabled and nand and nand.cs==0 and nand.input_bytes
                    and nand.input_bytes[0]==0x3B and nand.input_bits>=32 and nand.cache is not None
                    and len(nand.cache)<=2112 and len(nand.input_bytes)<=2112)
        if active:
            self.state.nand_bits=nand.input_bits;self.state.nand_accumulator=nand.accumulator
            self.state.nand_clk=nand.clk;self.state.nand_mosi=nand.mosi
            self.state.nand_miso=nand.miso;self.state.nand_io0=nand.io0
            count=len(nand.input_bytes)
            if count!=self.state.nand_input_count:
                previous=min(count,self.state.nand_input_count)
                self.state.input[previous:count]=nand.input_bytes[previous:count]
                self.state.nand_input_count=count
            if from_slow:
                seen=max((key-3 for key in nand.outputs if key>=4),default=0)
                self.state.seen_outputs=self.state.flushed_outputs=seen
            if not self.state.nand_enabled:
                self.state.cache_size=len(nand.cache)
                self.state.cache[:len(nand.cache)]=nand.cache
                self.state.cache_column=int.from_bytes(bytes(nand.input_bytes[1:3]),'big')&0xFFF
                self.state.input[:len(nand.input_bytes)]=nand.input_bytes
                self.state.nand_input_count=len(nand.input_bytes)
                count=max((key-3 for key in nand.outputs if key>=4),default=0)
                self.state.seen_outputs=self.state.flushed_outputs=count
        self.state.nand_enabled=active

    def flush(self):
        s=self.state;r=self.r
        r.gpio[0x40010C00][12]=s.port_b;r.gpio[0x40011800][12]=s.port_e
        if s.nand_enabled:
            nand=r.nand
            nand.input_bits=s.nand_bits;nand.accumulator=s.nand_accumulator
            nand.clk=s.nand_clk;nand.mosi=s.nand_mosi;nand.miso=s.nand_miso;nand.io0=s.nand_io0
            nand.input_bytes.extend(s.input[len(nand.input_bytes):s.nand_input_count])
            for index in range(s.flushed_outputs,s.seen_outputs):
                nand.outputs[4+index]=s.cache[s.cache_column+index]
            added=s.seen_outputs-s.flushed_outputs
            nand.read_bytes+=added;self.total_nand_bytes+=added;s.flushed_outputs=s.seen_outputs
        r.log_counts[('GPIO_AFIO','read')]+=s.reads
        r.log_counts[('GPIO_AFIO','write')]+=s.writes
        self.total_reads+=s.reads;self.total_writes+=s.writes
        s.reads=s.writes=0
        count=s.count;s.count=0;self.total_edges+=count
        for index in range(count):
            edge=s.edges[index]
            r.lcd.step=edge.step;r.lcd.write_edges+=1
            if edge.data:r.lcd.data(edge.value)
            else:r.lcd.new_command(edge.value)

    def safe_flush(self):
        try:self.flush()
        except StopModel as error:self.r.halt(str(error))
        except BaseException as error:
            self.error=error;self.r.cpu.emu_stop()

    def read(self,uc,offset,size,opaque):
        try:
            self.gate.sync()
            value=self.r.gpio_read(self.r.cpu,offset,size,None)
            self.refresh(from_slow=True)
            return value
        except BaseException as error:
            self.error=error;self.r.cpu.emu_stop();return 0

    def write(self,uc,offset,size,value,opaque):
        try:
            self.gate.sync()
            self.r.gpio_write(self.r.cpu,offset,size,value,None)
            self.refresh(from_slow=True)
        except BaseException as error:
            self.error=error;self.r.cpu.emu_stop()

    def describe(self):
        return dict(enabled=True,native_GPIO_reads=self.total_reads,
                    native_GPIO_writes=self.total_writes,LCD_edges=self.total_edges,NAND_cache_bytes=self.total_nand_bytes,
                    ARM_instructions_replaced=False,renderer_replaced=False)
