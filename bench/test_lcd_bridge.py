"""Independent native-edge checks, using no manufacturer firmware or dump."""
import ctypes as C
import collections
import shutil
import os,shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB
from emulate_clock_v121 import Runner as Core
from native_gate import Gate
from lcd_bus import LcdBus
from lcd_bridge import LcdBridge


class LcdFixture:
    @classmethod
    def setUpClass(cls):
        if os.environ.get('OPEND578_LCD_BRIDGE_LIBRARY'):
            cls.path=Path(os.environ['OPEND578_LCD_BRIDGE_LIBRARY']).resolve(strict=True)
            return
        compiler=shlex.split(os.environ.get('CC','cc'))
        if not compiler or not shutil.which(compiler[0]):raise unittest.SkipTest('A C compiler is needed for native dispatcher checks')
        cls.temp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.temp.cleanup)
        cls.path=Path(cls.temp.name)/('lcd.dylib' if sys.platform=='darwin' else 'lcd.so')
        flags=['-dynamiclib','-fPIC'] if sys.platform=='darwin' else ['-shared','-fPIC']
        subprocess.run([*compiler,'-O2',*flags,str(Path(__file__).with_name('lcd_bridge.c')),'-o',str(cls.path)],check=True)

    def runner(self):
        cpu=Uc(UC_ARCH_ARM,UC_MODE_THUMB);cpu.mem_map(0x40010000,8192)
        lcd=LcdBus();lcd.armed=True;lcd.command=0x2C;lcd.pixel_format=0x55
        lcd.columns=(0,31);lcd.rows=(0,31);lcd.width=lcd.height=32
        r=SimpleNamespace(cpu=cpu,lcd=lcd,gpio={0x40010C00:{12:0x800},0x40011800:{12:1}},
                          trace_enabled=False,steps=100,log_counts=collections.Counter(),lane=Core.lane)
        r.gpio_read=lambda uc,off,size,data:Core.gpio_get(r,off,size)
        def write(uc,off,size,value,data):
            previous=r.gpio[0x40010C00][12]
            Core.gpio_set(r,off,size,value)
            lcd.gpio(previous,r.gpio[0x40010C00][12],r.gpio[0x40011800][12])
        r.gpio_write=write
        r.halt=lambda *args:(_ for _ in ()).throw(AssertionError(str(args)))
        gate=SimpleNamespace(r=r,state=Gate())
        def sync():
            gate.bridge.flush();r.steps=100+gate.state.instructions
        gate.sync=sync;bridge=LcdBridge(gate,self.path);gate.bridge=bridge
        bridge.dll.lcd_bridge_write.argtypes=[C.c_void_p,C.c_uint64,C.c_uint32,C.c_uint64,C.c_void_p]
        bridge.dll.lcd_bridge_read.argtypes=[C.c_void_p,C.c_uint64,C.c_uint32,C.c_void_p]
        bridge.dll.lcd_bridge_read.restype=C.c_uint64
        return r,gate,bridge

class LcdNativeTests(LcdFixture,unittest.TestCase):
    def test_cached_frame_preserves_RGB565_colors_and_reset_clears_it(self):
        lcd=LcdBus();lcd.width=2;lcd.height=1;lcd.pixel_format=0x55
        lcd.columns=(0,1);lcd.rows=(0,0);lcd.new_command(0x2C)
        for byte in (0xF8,0,0x07,0xE0):lcd.data(byte)
        self.assertEqual(list(lcd.frame(False).get_flattened_data()),[(255,0,0),(0,255,0)])
        lcd.new_command(1)
        self.assertEqual(list(lcd.frame(False).get_flattened_data()),[(0,0,0),(0,0,0)])

    def test_all_data_bytes_match_reference_gpio_decode(self):
        r,g,b=self.runner();reference=LcdBus();reference.armed=True;reference.command=0x2C
        reference.pixel_format=0x55;reference.columns=(0,31);reference.rows=(0,31);reference.width=reference.height=32
        for value in range(256):
            for off,v in ((0x180C,(value<<7)|1),(0xC14,0x400),(0xC10,0x400)):
                g.state.instructions+=1;b.dll.lcd_bridge_write(None,off,4,v,b.opaque)
            reference.data(value);reference.write_edges+=1
        b.flush()
        self.assertEqual(r.lcd.pixels,reference.pixels)
        self.assertEqual(r.lcd.write_edges,reference.write_edges)
        self.assertEqual(r.gpio[0x40011800][12],(255<<7)|1)
        self.assertIsNone(b.error)

    def test_full_edge_queue_flushes_without_dropping_bytes(self):
        r,g,b=self.runner()
        for index in range(5000):
            for off,v in ((0x180C,((index&255)<<7)|1),(0xC14,0x400),(0xC10,0x400)):
                g.state.instructions+=1;b.dll.lcd_bridge_write(None,off,4,v,b.opaque)
        b.flush()
        self.assertEqual(r.lcd.write_edges,5000)
        self.assertEqual(r.lcd.total_pixels,2500)
        self.assertEqual(b.total_edges,5000)

    def test_other_gpio_pins_use_existing_model_and_refresh_native_readback(self):
        r,g,b=self.runner()
        g.state.instructions+=1;b.dll.lcd_bridge_write(None,0xC10,4,0x10,b.opaque)
        self.assertEqual(r.gpio[0x40010C00][12]&0x10,0x10)
        self.assertEqual(b.state.port_b,r.gpio[0x40010C00][12])
        self.assertEqual(b.dll.lcd_bridge_read(None,0x180C,4,b.opaque),1)

    def test_trace_mode_disables_native_shortcut(self):
        r,g,b=self.runner();r.trace_enabled=True;b.refresh()
        self.assertFalse(b.state.enabled)
        b.dll.lcd_bridge_write(None,0x180C,4,0x1001,b.opaque)
        self.assertEqual(r.gpio[0x40011800][12],0x1001)
        self.assertEqual(b.state.writes,0)


if __name__=='__main__':unittest.main()

class NandNativeTests(LcdFixture,unittest.TestCase):
    def test_cached_dual_spi_bytes_and_protocol_state_match_original_model(self):
        from emulate_nand_v121 import CapturedNand
        from unicorn.arm_const import UC_ARM_REG_PC,UC_ARM_REG_R1
        import copy
        r,g,b=self.runner()
        nand=CapturedNand.__new__(CapturedNand)
        nand.idle=1;nand.cs=0;nand.clk=1;nand.mosi=1;nand.miso=1;nand.io0=1
        nand.input_bits=32;nand.accumulator=0;nand.input_bytes=[0x3B,0,7,0]
        nand.outputs={0:255,1:255,2:255,3:255};nand.cache=bytes(range(256))*8+bytes(64);nand.read_bytes=0
        reference=copy.deepcopy(nand);r.nand=nand;r.gpio[0x40010C00][12]=0xC800
        original_write=r.gpio_write
        def write(uc,off,size,value,data):
            original_write(uc,off,size,value,data)
            if off in (0xC10,0xC14):nand.drive(r.gpio[0x40010C00][12],(value|(value>>16))&65535 if off==0xC10 else value)
        r.gpio_write=write
        b.refresh();r.cpu.reg_write(UC_ARM_REG_PC,0x0800879A)
        actual=[];expected=[];levels=0xC800
        for index in range(127):
            a=e=0
            for _ in range(4):
                g.state.instructions+=1;b.dll.lcd_bridge_write(r.cpu._uch,0xC14,4,0x8000,b.opaque)
                levels&=~0x8000;reference.drive(levels,0x8000)
                r.cpu.reg_write(UC_ARM_REG_R1,0x8000)
                hi=b.dll.lcd_bridge_read(r.cpu._uch,0x808,4,b.opaque)>>15
                r.cpu.reg_write(UC_ARM_REG_R1,0x4000)
                lo=b.dll.lcd_bridge_read(r.cpu._uch,0xC08,4,b.opaque)>>14
                a=(a<<2)|(hi<<1)|lo;e=(e<<2)|(reference.miso<<1)|reference.io0
                g.state.instructions+=1;b.dll.lcd_bridge_write(r.cpu._uch,0xC10,4,0x8000,b.opaque)
                levels|=0x8000;reference.drive(levels,0x8000)
            actual.append(a);expected.append(e)
        b.flush()
        self.assertEqual(actual,list(nand.cache[7:134]));self.assertEqual(actual,expected)
        for field in ('input_bits','accumulator','input_bytes','outputs','clk','mosi','miso','io0','read_bytes'):
            self.assertEqual(getattr(nand,field),getattr(reference,field),field)
        self.assertIsNone(b.error)
