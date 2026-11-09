"""Derive the original CC0 UART demo's USART0 variant by checked Thumb relocations.
No OEM image is used. The source UART1 binary and its C source are shipped.
"""
from pathlib import Path
import struct
root=Path(__file__).resolve().parent
b=bytearray((root/'uart_rx_demo.bin').read_bytes())
def mov(rd,value,top=False):
    return struct.pack('<HH',(0xF2C0 if top else 0xF240)|((value>>12)&15)|(((value>>11)&1)<<10),((value>>8)&7)<<12|rd<<8|(value&255))
def patch(offset,old,new):
    old=bytes.fromhex(old);assert b[offset:offset+len(old)]==old,(offset,b[offset:offset+len(old)].hex());b[offset:offset+len(old)]=new
handler=struct.unpack_from('<I',b,54*4)[0];struct.pack_into('<I',b,53*4,handler);struct.pack_into('<I',b,54*4,0)
for off,old,rd,val,top in [(0xdc,'44f20040',0,0x3800,False),(0xe0,'c4f20000',0,0x4001,True),(0x12e,'41f21c01',1,0x1018,False),(0x138,'42f40032',2,0x4000,False),(0x13e,'44f20841',1,0x3808,False),(0x142,'c4f20001',1,0x4001,True),(0x146,'41f66a02',2,1042,False)]:patch(off,old,mov(rd,val,top))
for off,old,new in [(0x100,'0428','0828'),(0x10e,'4021','2021'),(0x15a,'4022','2022'),(0x160,'0329','0729'),(0x168,'0429','0829')]:patch(off,old,bytes.fromhex(new))
(root/'microphone_rx_demo.bin').write_bytes(b)
s=(root/'uart_rx_demo.c').read_text()
s=s.replace('USART1_Handler','USART0_Handler').replace('0x400044','0x400138').replace('vectors[55]','vectors[54]').replace('[54]=','[53]=').replace('COUNT==4','COUNT==8').replace('COUNT<4','COUNT<8').replace('1<<6','1<<5').replace('R(0x4002101c)|=1<<17','R(0x40021018)=1<<14').replace('=6250','=1042')
(root/'microphone_rx_demo.c').write_text('/* CC0 original test; binary derived with build_microphone_demo.py. */\n'+s)
print('USART0 IRQ37 8-byte ARM test built from original UART demo')
# Full duplex variant: every group of eight RX bytes produces a real TX AA.
duplex=bytearray(b)
duplex[0x100:0x102]=struct.pack('<H',29<<6) # lsls r0,r0,#29 tests COUNT modulo 8
for off,rd,val,top in [(0x106,0,0x3804,False),(0x10a,0,0x4001,True),(0x14c,2,0x202c,False)]:duplex[off:off+4]=mov(rd,val,top)
duplex[0x10e:0x110]=struct.pack('<H',0x21aa)
(root/'microphone_duplex_demo.bin').write_bytes(duplex)
(root/'microphone_duplex_demo.c').write_text(s.replace('if(COUNT==8)R(0xe000e184)=1<<5;','if((COUNT&7)==0)R(0x40013804)=170;').replace('=0x2024','=0x202c'))
