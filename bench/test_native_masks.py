"""A pending masked core exception must not cross an unmasking barrier."""
import ctypes as C
import shutil,subprocess,tempfile,unittest
from pathlib import Path
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_MODE_MCLASS
from unicorn.arm_const import UC_ARM_REG_BASEPRI,UC_ARM_REG_PRIMASK,UC_ARM_REG_FAULTMASK
from unicorn.unicorn_py3.unicorn import uclib
from native_gate import Gate,NOTIFY,REG_READ


class NativeMaskTests(unittest.TestCase):
    def test_only_eligible_pending_exception_calls_python_at_mask_barrier(self):
        if not shutil.which('cc'):self.skipTest('C compiler needed')
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'gate.so'
            subprocess.run(['cc','-O2','-shared','-fPIC',str(Path(__file__).with_name('native_gate.c')),'-o',str(path)],check=True)
            dll=C.CDLL(str(path));dll.gate_code.argtypes=[C.c_void_p,C.c_uint64,C.c_uint32,C.c_void_p]
            cpu=Uc(UC_ARCH_ARM,UC_MODE_THUMB|UC_MODE_MCLASS);bitmap=(C.c_ubyte*128)();bitmap[0]=2
            seen=[];callback=NOTIFY(lambda *args:seen.append(True))
            state=Gate(0,1000,0,0,0x1000,0x1100,0x1000,bitmap,callback,0,0)
            state.mask_tracking=1;state.mask_priority=255
            state.reg_read=REG_READ(('uc_reg_read',uclib))
            state.reg_basepri=UC_ARM_REG_BASEPRI;state.reg_primask=UC_ARM_REG_PRIMASK;state.reg_faultmask=UC_ARM_REG_FAULTMASK
            cpu.reg_write(UC_ARM_REG_BASEPRI,32)
            dll.gate_code(cpu._uch,0x1000,2,C.byref(state));self.assertEqual(seen,[])
            cpu.reg_write(UC_ARM_REG_BASEPRI,0)
            dll.gate_code(cpu._uch,0x1000,2,C.byref(state));self.assertEqual(len(seen),1)
            cpu.reg_write(UC_ARM_REG_PRIMASK,1)
            dll.gate_code(cpu._uch,0x1000,2,C.byref(state));self.assertEqual(len(seen),1)
            self.assertEqual(state.instructions,3)
