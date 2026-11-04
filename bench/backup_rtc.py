"""RTC/BKP digital subset, with an explicit retained battery domain.

The OEM decides the epoch and asks the user for a date after a cold start.
No firmware RAM variable or UI state is manufactured here.
"""
from emulate_clock_v121 import StopModel


class BackupRtc:
    def __init__(self, write_enabled=lambda:True, enabled=lambda:True):
        self.write_enabled = write_enabled
        self.enabled = enabled
        self.reset()

    def reset(self):
        self.regs = {0:0,4:0x20,8:0,12:0x8000,16:0,20:0x8000,
                     24:0,28:0,32:0xFFFF,36:0xFFFF}
        self.backup = {off:0 for off in list(range(4,0x2C,4))+[0x2C,0x30,0x34]+list(range(0x40,0xC0,4))}
        self.sync_reads = 0
        self.busy_reads = 0
        self.time = 0
        self.fraction = 0
        self.events = []

    def advance(self, now):
        elapsed = now-self.time
        self.time = now
        if not self.enabled() or self.regs[4] & 16:
            return
        # Ideal 32768 Hz LXTAL, with the programmed 20-bit prescaler.
        # 120 million synthetic core units per second, not host wall time.
        prescaler=(self.regs[8]<<16)|self.regs[12]
        seconds, self.fraction = divmod(self.fraction+elapsed*32768,(prescaler+1)*120_000_000)
        divider=prescaler-self.fraction//120_000_000
        self.regs[16],self.regs[20]=divider>>16,divider&0xFFFF
        if seconds:
            old = self.regs[24]*65536+self.regs[28]
            value = (old+seconds) & 0xFFFFFFFF
            self.regs[24], self.regs[28] = value>>16,value&0xFFFF
            self.regs[4] |= 1 | (4 if old+seconds > 0xFFFFFFFF else 0)
            alarm = self.regs[32]*65536+self.regs[36]
            if old < alarm <= old+seconds:
                self.regs[4] |= 2

    @property
    def irq(self):
        return bool(self.regs[0] & self.regs[4] & 7)

    def read(self, off, size, backup=False):
        registers = self.backup if backup else self.regs
        if off not in registers or size not in (2,4):
            raise StopModel('BKP/RTC register/access outside modelled subset')
        if not backup and off == 4 and self.enabled():
            if self.sync_reads:
                self.sync_reads -= 1
            else:
                self.regs[4] |= 8
            if self.busy_reads:
                self.busy_reads -= 1
            else:
                self.regs[4] |= 32
        return registers[off]

    def write(self, off, size, value, backup=False):
        registers = self.backup if backup else self.regs
        if off not in registers or size not in (2,4):
            raise StopModel('BKP/RTC register/access outside modelled subset')
        if not self.write_enabled():
            return  # Hardware ignores writes with PMU.BKPWEN clear.
        if backup:
            registers[off] = value & 0xFFFF
            return
        value &= 0xFFFF
        if off == 4:
            if not value & 8:
                self.sync_reads = 2
            self.regs[4] = (self.regs[4] & (value | ~15) & ~16) | (value & 16)
            if not value & 16:
                self.regs[4] &= ~32
                self.busy_reads = 2
        else:
            if off in (16,20):
                raise StopModel('write to read-only RTC divider')
            if off >= 8 and not self.regs[4] & 16:
                raise StopModel('RTC data write outside configuration mode')
            self.regs[off] = value
            if off in (8,12,24,28):
                self.fraction=0

    def describe(self):
        return dict(registers={hex(k):hex(v) for k,v in self.regs.items()},
                    backup_registers={hex(k):hex(v) for k,v in self.backup.items()},
                    counter=self.regs[24]*65536+self.regs[28],
                    battery_domain_modelled=True, cycle_accurate=False)
