"""GD32 USBD register subset, disconnected host (no enumeration or packets)."""
from emulate_clock_v121 import StopModel


class UsbdIdle:
    def __init__(self):
        self.regs={off:0 for off in (*range(0,0x20,4),0x40,0x44,0x48,0x4C,0x50)}
        self.regs[0x40]=3
        self.pma=bytearray(1024)
        self.writes=[]

    def read(self,off,size):
        if off not in self.regs or size not in (2,4):raise StopModel('USBD register outside disconnected-host subset')
        return self.regs[off]

    def write(self,off,size,value):
        if off not in self.regs or size not in (2,4) or value>65535:raise StopModel('USBD write outside disconnected-host subset')
        old=self.regs[off]
        if off<0x20:
            self.regs[off]=(old&value&0x8080)|((old^value)&0x7070)|(value&0x070F)
        elif off==0x40:
            self.regs[off]=value&0xFFBF
            if value&1:
                for address in range(0,0x20,4):self.regs[address]=0
                self.regs[0x44]=self.regs[0x4C]=0
        elif off==0x44:self.regs[off]&=value&0x7F80
        elif off==0x48:raise StopModel('USBD status register is read-only')
        elif off==0x4C:self.regs[off]=value&0xFF
        elif off==0x50:self.regs[off]=value&0xFFF8
        self.writes.append(dict(offset=hex(off),value=hex(value)))

    def memory_read(self,off,size):
        if size not in (2,4) or off&3 or not 0<=off<1024:raise StopModel('USBD packet memory access outside aligned halfword subset')
        return int.from_bytes(self.pma[off:off+2],'little')

    def memory_write(self,off,size,value):
        self.memory_read(off,size)
        if value>65535:raise StopModel('USBD packet memory upper reserved bits')
        self.pma[off:off+2]=value.to_bytes(2,'little')

    def describe(self):
        return dict(scenario='USB host disconnected',registers={hex(k):hex(v) for k,v in self.regs.items()},
            writes=self.writes,host_packets_injected=0,enumeration_simulated=False)
