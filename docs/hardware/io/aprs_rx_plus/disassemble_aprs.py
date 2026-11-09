from pathlib import Path
import capstone as cs,struct,sys,json
from capstone.arm import *
root=Path('aprs_rx_plus_20261109')
images={
'PRO':(0x8006000,Path('oem_v121.cdd').read_bytes()),
'PLUS':(0x8006000,Path('native_v05/firmwares/D578UV2_GD_V2.08_20240619.CDD').read_bytes()),
'H':(0x2000,(root/'BHT_BOARD_H_V2.00_20230417.CDD').read_bytes()),
'M':(0x2000,(root/'BHT_BOARD_V2.00_M_20230923.CDD').read_bytes())}
md=cs.Cs(cs.CS_ARCH_ARM,cs.CS_MODE_THUMB);md.detail=True;md.skipdata=True
def dump(tag,lo,hi):
 base,b=images[tag];lines=[]
 for i in md.disasm(b[lo-base:hi-base],lo):
  ext=''
  if i.id and len(i.operands)>1 and i.operands[1].type==ARM_OP_MEM and i.operands[1].mem.base==ARM_REG_PC:
   ad=((i.address+4)&~3)+i.operands[1].mem.disp
   if base<=ad<base+len(b)-4:ext=f' ; [{ad:08X}]={struct.unpack_from("<I",b,ad-base)[0]:08X}'
  lines.append(f'{i.address:08X} {i.mnemonic:10s} {i.op_str}{ext}')
 return '\n'.join(lines)+'\n'
def calls(tag,target):
 base,b=images[tag];out=[]
 for o in range(0,len(b)-4,2):
  a,z=struct.unpack_from('<HH',b,o)
  if a&0xf800!=0xf000 or z&0xd000!=0xd000:continue
  s=a>>10&1;i1=1-((z>>13&1)^s);i2=1-((z>>11&1)^s)
  imm=(s<<24)|(i1<<23)|(i2<<22)|((a&1023)<<12)|((z&2047)<<1);imm-=s<<25
  if base+o+4+imm==target:out.append(base+o)
 return out
if __name__=='__main__':
 mode=sys.argv[1];tag=sys.argv[2]
 if mode=='dump':print(dump(tag,int(sys.argv[3],16),int(sys.argv[4],16)))
 if mode=='calls':
  for t in sys.argv[3:]:print(t,[hex(a)for a in calls(tag,int(t,16))])
 if mode=='mmio':
  base,b=images[tag]
  for o in range(0,len(b)-3,4):
   v=struct.unpack_from('<I',b,o)[0]
   if 0x40000000<=v<0x40024000 or v in [0x48000000,0x48000400,0x50000000]:print(hex(base+o),hex(v))
