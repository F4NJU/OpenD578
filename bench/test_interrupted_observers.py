"""A pre-instruction IRQ must not create an OEM expectation before execution."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from emulate_front_v121 import FrontRunner
from cortex_exceptions import CortexExceptions
from rf_spi import RfSpi
from emulate_clock_v121 import StopModel
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2

class InterruptedObserverTests(unittest.TestCase):
    def test_irq_at_rf_entry_does_not_duplicate_next_transaction(self):
        r=FrontRunner.__new__(FrontRunner)
        r.virtual_units=0;r.last_instruction_units=1;r.steps=1;r.stop=None
        r.rf_spi=RfSpi();r.fwdgt=SimpleNamespace(advance=lambda t:False)
        r.input_poll=10**9;r.peripheral_deadline=10**9;r.exti={0:0,0x14:0}
        regs={UC_ARM_REG_R0:0x44,UC_ARM_REG_R1:0x1234,UC_ARM_REG_R2:0}
        cpu=SimpleNamespace(reg_read=lambda reg:regs[reg])
        def interrupted(*args):r.stop={'kind':'core pending exception delivery required'}
        with patch.object(CortexExceptions,'on_code',interrupted):r.on_code(cpu,0x0808AB18,2,None)
        self.assertEqual(r.rf_spi.expected,[])
        r.stop=None
        with patch.object(CortexExceptions,'on_code',lambda *args:None):r.on_code(cpu,0x0808AB18,2,None)
        self.assertEqual(r.rf_spi.expected,[(0,0x44,0x1234)])
        self.finish_write(r.rf_spi,0x44,0x1234)
        regs[UC_ARM_REG_R0]=0x25;regs[UC_ARM_REG_R1]=2
        with patch.object(CortexExceptions,'on_code',lambda *args:None):r.on_code(cpu,0x0808AB18,2,None)
        self.finish_write(r.rf_spi,0x25,2)
        self.assertEqual(r.rf_spi.crosschecks,2)
        self.assertEqual(r.rf_spi.expected,[])
    @staticmethod
    def finish_write(rf,address,value):
        rf.bank=0;rf.command=address
        rf.bits=[(address>>b)&1 for b in range(7,-1,-1)]+[(value>>b)&1 for b in range(15,-1,-1)]
        rf.finish(1)
    def test_genuine_bus_mismatch_still_stops_with_evidence(self):
        rf=RfSpi();rf.expect(0,0x44,0x1234)
        with self.assertRaisesRegex(StopModel,'expected bank=0 reg=0x44'):
            self.finish_write(rf,0x44,0x1235)
        self.assertEqual(rf.describe()['last_mismatch']['actual']['value'],0x1235)
        self.assertEqual(len(rf.expected),1)

if __name__=='__main__':unittest.main()
