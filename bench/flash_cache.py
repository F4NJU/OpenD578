"""GD32 FMC subset for volatile OEM cache writes in high internal flash."""
import hashlib
from emulate_clock_v121 import StopModel


class FlashCache:
    START=0x082F5000
    END=0x08300000

    def __init__(self,read_memory,write_memory):
        self.read_memory=read_memory
        self.write_memory=write_memory
        self.regs={0xC:0,0x10:0x80,0x14:0,0x4C:0,0x50:0x80,0x54:0}
        self.keys={4:0,0x44:0}
        self.busy={0:0,1:0}
        self.erases=[]
        self.program_count=0
        self.program_bytes=0

    def read(self,off,size):
        if off not in self.regs or size!=4:raise StopModel('FMC register/access outside cache subset')
        if off in (0xC,0x4C):
            bank=0 if off==0xC else 1
            if self.busy[bank]:
                self.busy[bank]-=1
                return self.regs[off]|1
        return self.regs[off]

    def write(self,off,size,value):
        if size!=4:raise StopModel('FMC cache requires word register access')
        if off in self.keys:
            ctl=0x10 if off==4 else 0x50
            if self.keys[off]==0 and value==0x45670123:self.keys[off]=1
            elif self.keys[off]==1 and value==0xCDEF89AB:
                self.regs[ctl]&=~0x80
                self.keys[off]=0
            else:raise StopModel('FMC incorrect unlock sequence')
        elif off in (0xC,0x4C):self.regs[off]&=~(value&0x34)
        elif off in (0x14,0x54):self.regs[off]=value
        elif off in (0x10,0x50):
            if self.regs[off]&0x80 and value!=0x80:raise StopModel('FMC control write while locked')
            if value & ~0xC3:raise StopModel('FMC operation outside program/page erase subset')
            self.regs[off]=value&~0x40
            if value&0x40:
                if off!=0x50 or not value&2 or value&0x80:
                    raise StopModel('FMC erase outside high cache bank')
                address=self.regs[0x54]&~0xFFF
                if not self.START<=address<self.END:raise StopModel('FMC erase outside volatile cache range')
                self.write_memory(address,b'\xFF'*4096)
                self.erases.append(address)
                self.regs[0x4C]|=0x20
                self.busy[1]=2
        else:raise StopModel('FMC register outside volatile cache subset')

    def program(self,address,size,value):
        if not self.START<=address<=self.END-size or size not in (2,4) or address%2:
            raise StopModel('FMC program outside aligned volatile high cache')
        if self.regs[0x50]&0x83!=1:raise StopModel('FMC store without unlocked PG mode')
        old=bytes(self.read_memory(address,size))
        new=value.to_bytes(size,'little')
        if any(a&b!=b for a,b in zip(old,new)):
            raise StopModel('FMC zero-to-one programming requires erase')
        self.regs[0x4C]|=0x20
        self.busy[1]=2
        self.program_count+=1
        self.program_bytes+=size

    def describe(self):
        return dict(registers={hex(k):hex(v) for k,v in self.regs.items()},
            erased_4KiB_pages=[hex(x) for x in self.erases],program_count=self.program_count,
            program_bytes=self.program_bytes,storage='volatile emulated internal flash cache',
            range=[hex(self.START),hex(self.END)],
            sha256=hashlib.sha256(bytes(self.read_memory(self.START,self.END-self.START))).hexdigest(),
            firmware_application_modified=False,source_CDD_modified=False)
