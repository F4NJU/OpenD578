"""GD32 basic/general timer subset: up-counting, update IRQ and PWM state.

Time units are synthetic processor instruction units, including the explicitly
accelerated OEM delay loops. They are not measurements of wall time or cycles.
"""
from emulate_clock_v121 import StopModel


class Timer:
    def __init__(self, name, clock_enabled=lambda: True):
        self.name = name
        self.clock_enabled = clock_enabled
        self.regs = {off:0 for off in range(0,0x50,4)}
        self.regs[0x2C] = 0xFFFF
        self.prescaler = 0
        self.remainder = 0
        self.time = 0
        self.updates = 0

    def advance(self, now):
        elapsed = now - self.time
        self.time = now
        if not self.clock_enabled() or not self.regs[0] & 1:
            return
        if self.regs[0] & 0x70 or self.regs[8] & 7:
            raise StopModel(self.name+' mode outside up-counting subset')
        increments, self.remainder = divmod(self.remainder+elapsed, self.prescaler+1)
        periods, self.regs[0x24] = divmod(self.regs[0x24]+increments, self.regs[0x2C]+1)
        if periods:
            self.prescaler = self.regs[0x28]
            if not self.regs[0] & 2:
                self.regs[0x10] |= 1
                self.updates += periods
            if self.regs[0] & 8:
                self.regs[0] &= ~1
                self.regs[0x24] = 0

    def access(self, offset, size):
        if size not in (2,4) or offset not in self.regs:
            raise StopModel(self.name+' register/access outside subset')

    def read(self, offset, size):
        self.access(offset,size)
        return self.regs[offset]

    def write(self, offset, size, value):
        self.access(offset,size)
        if value > 0xFFFF:
            raise StopModel(self.name+' upper reserved bits')
        if offset == 0x10:
            self.regs[offset] &= value
        elif offset == 0x14:
            if value & ~1:
                raise StopModel(self.name+' event outside update subset')
            if value & 1:
                self.regs[0x24] = self.remainder = 0
                self.prescaler = self.regs[0x28]
                if not self.regs[0] & 6:
                    self.regs[0x10] |= 1
        else:
            if offset == 0xC and value & ~1:
                raise StopModel(self.name+' IRQ/DMA source outside update subset')
            self.regs[offset] = value

    @property
    def irq(self):
        return bool(self.regs[0xC] & self.regs[0x10] & 1)

    def describe(self):
        return dict(name=self.name, registers={hex(k):hex(v) for k,v in self.regs.items()},
                    updates=self.updates, synthetic_time_units=self.time, cycle_accurate=False)
