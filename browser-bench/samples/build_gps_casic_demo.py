"""CC0 original Thumb transmitter: real USART1 writes and TC polling.
No OEM image, RAM fixture or PC interception is used by this program.
"""
from pathlib import Path
import struct
root=Path(__file__).resolve().parent
commands=b'$PCAS02,1000*2E\r\n$PCAS03,1,0,0,0,1,0,0,0*02\r\n$PCAS04,3*1A\r\n'
code=bytearray()
def h(v):code.extend(struct.pack('<H',v))
def mov(rd,value,top=False):
 h((0xF2C0 if top else 0xF240)|((value>>12)&15)|(((value>>11)&1)<<10));h(((value>>8)&7)<<12|rd<<8|(value&255))
def reg(address,value):
 mov(0,address&65535);mov(0,address>>16,True);mov(1,value&65535);mov(1,value>>16,True);h(0x6001)
reg(0x4002101c,1<<17);reg(0x40004408,6250);reg(0x4000440c,0x2008)
mov(0,0x4400);mov(0,0x4000,True)
for byte in commands:
 h(0x2100|byte);h(0x8081);h(0x8801);h(0x0649);h(0xd5fc)
h(0xbf30);h(0xe7fd)
(root/'gps_casic_demo.bin').write_bytes(struct.pack('<II',0x20018000,0x08006009)+code)
