"""CC0: small, original Thumb UART transmitter; no OEM content.
Unroll each UART store/poll pair, with checked encodings documented below.
"""
from pathlib import Path
import struct
r=Path(__file__).resolve().parent
frame=bytes.fromhex('53010100000001010010000000000006')
code=bytearray()
def h(v):code.extend(struct.pack('<H',v))
def mov(rd,value,top=False):
 h((0xF2C0 if top else 0xF240)|((value>>12)&15)|(((value>>11)&1)<<10));h(((value>>8)&7)<<12|rd<<8|(value&255))
def reg(address,value):
 mov(0,address&65535);mov(0,address>>16,True);mov(1,value&65535);mov(1,value>>16,True);h(0x6001) # str r1,[r0]
reg(0x40021018,1<<14);reg(0x40013808,1042);reg(0x4001380c,0x2008)
mov(0,0x3800);mov(0,0x4001,True)
for byte in frame:
 h(0x2100|byte) # movs r1,#byte
 h(0x8081) # strh r1,[r0,#4]
 h(0x8801) # wait: ldrh r1,[r0]
 h(0x0649) # lsls r1,r1,#25 (TC bit 6 -> N)
 h(0xD5FC) # bpl wait
h(0xBF30);h(0xE7FD) # WFI loop
(r/'microphone_tx_demo.bin').write_bytes(struct.pack('<II',0x20018000,0x08006009)+code)
(r/'microphone_tx_demo.c').write_text('''/* CC0 original fixture. Binary emitted by build_microphone_tx_demo.py. */
#include <stdint.h>
#define R(a) (*(volatile uint32_t *)(a))
const uint8_t frame[]={'''+','.join(str(x)for x in frame)+'''};
void Reset_Handler(void){R(0x40021018)=1<<14;R(0x40013808)=1042;R(0x4001380c)=0x2008;
 for(unsigned i=0;i<16;i++){R(0x40013804)=frame[i];while(!(R(0x40013800)&64));}for(;;)__asm volatile("wfi");}
''')
