"""Original small Thumb fixture generator; contains no vendor instructions.

Emits a limited set of documented Thumb instructions. Inline literal words are
skipped by branches. This is a board-contract probe, not a usable radio firmware.
"""
import struct,argparse
from pathlib import Path

class Thumb:
    def __init__(self,address):self.address=address;self.data=bytearray()
    @property
    def pc(self):return self.address+len(self.data)
    def half(self,value):self.data+=struct.pack('<H',value)
    def constant(self,reg,value):
        if self.pc%4:self.half(0xBF00)
        self.half(0x4800|(reg<<8));self.half(0xE001)
        self.data+=struct.pack('<I',value)
    def write(self,address,value):
        self.constant(0,address);self.constant(1,value);self.half(0x6001)
    def read_to(self,address,target):
        self.constant(0,address);self.half(0x6801)
        self.constant(0,target);self.half(0x6001)
    def bit(self,base,mask,value):self.write(base+0x10,mask if value else mask<<16)

def modes(outputs):
    value=0x44444444
    for pin in outputs:value=(value&~(15<<(pin*4)))|(3<<(pin*4))
    return value

def build(load_address=0x08006000,reset_offset=0x200):
    reset=load_address+reset_offset
    if reset%2:raise ValueError('Thumb entry must be halfword aligned')
    t=Thumb(reset)
    A=0x40010800;B=0x40010C00;C=0x40011000;E=0x40011800
    # Clocks for GPIO A..E. All chip selects are deasserted before driving pins.
    t.write(0x40021018,0x7C)
    t.write(B+0x10,(1<<2)|(1<<5)|(1<<8)|(1<<10)|(1<<13))
    t.write(C+0x10,1<<13);t.write(E+0x10,2)
    t.write(B,modes([2,3,4,5]));t.write(B+4,modes([0,2,3,5,6,7]))
    t.write(C+4,modes([5]));t.write(E,modes([1,7]));t.write(E+4,modes(list(range(7))))
    # Exercise the very top of SRAM and executable SRAM, beyond the OEM scatter.
    t.write(0x20017FFC,0xD578CAFE)
    t.write(0x20017F00,0x4770205A) # movs r0,#90; bx lr
    t.constant(3,0x20017F01);t.half(0x4798) # blx r3
    t.constant(2,0x20017FF8);t.half(0x6010) # str r0,[r2]
    # LCD writes use the actual 8080 GPIO bus, with no function-entry observer.
    def lcd(value,data=False):
        t.bit(B,1<<13,False);t.bit(B,1<<11,data);t.bit(B,1<<10,False)
        data_bits=(value&255)<<7
        t.write(E+0x10,((0x7F80&~data_bits)<<16)|data_bits)
        t.bit(B,1<<10,True);t.bit(B,1<<13,True)
    lcd(0x11);lcd(0x3A);lcd(0x55,True)
    lcd(0x2A)
    for v in (0,0,0,1):lcd(v,True)
    lcd(0x2B)
    for v in (0,0,0,0):lcd(v,True)
    lcd(0x29);lcd(0x2C)
    for v in (0xF8,0,0x07,0xE0):lcd(v,True)
    # RF data is sampled from GPIO ISTAT, regardless of the CPU register usage.
    def rf_header(command):
        t.write(B,modes([2,3,4,5]));t.bit(B,1<<3,False);t.bit(B,1<<5,False)
        for bit in range(7,-1,-1):
            t.bit(B,1<<4,bool(command&(1<<bit)));t.bit(B,1<<3,True);t.bit(B,1<<3,False)
    rf_header(0x44)
    for bit in range(15,-1,-1):
        t.bit(B,1<<4,bool(0x1234&(1<<bit)));t.bit(B,1<<3,True);t.bit(B,1<<3,False)
    t.bit(B,1<<5,True)
    for address,target in ((0x0C,0x20017E00),(0x60,0x20017E40)):
        rf_header(address|0x80)
        t.write(B,(modes([2,3,4,5])&~(15<<16))|(8<<16))
        for bit in range(16):
            t.bit(B,1<<3,True);t.read_to(B+8,target+4*bit);t.bit(B,1<<3,False)
        t.bit(B,1<<5,True)
    t.write(0x20017FF4,0x600DC0DE)
    t.half(0xE7FE) # stable infinite branch; no semihosting result fabrication
    image=bytearray(b'\xFF'*(reset_offset+len(t.data)))
    struct.pack_into('<II',image,0,0x20017DF0,reset|1)
    image[reset_offset:]=t.data
    return bytes(image)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path)
    p.add_argument('--load-address',type=lambda v:int(v,0),default=0x08006000)
    p.add_argument('--reset-offset',type=lambda v:int(v,0),default=0x200)
    a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(build(a.load_address,a.reset_offset))
