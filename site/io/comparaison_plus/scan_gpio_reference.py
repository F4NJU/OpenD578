from pathlib import Path
import capstone as cs, struct,json,hashlib
from capstone.arm import *
B=0x08000000
image=Path('inputs/Firmware D578/full_flash_pass1(1).bin').read_bytes()
md=cs.Cs(cs.CS_ARCH_ARM,cs.CS_MODE_THUMB);md.detail=True;md.skipdata=True
api={0x8008796:'read',0x80087ca:'set',0x80087ce:'clear',0x80087d2:'write',0x80087dc:'port-write',0x8008670:'init',0x800191e:'read',0x8001952:'set',0x8001956:'clear',0x800195a:'write',0x8001964:'port-write',0x80017f8:'init'}
ports={0x40010800:'PA',0x40010c00:'PB',0x40011000:'PC',0x40011400:'PD',0x40011800:'PE'}
calls=[]
for off in range(0,0x100000-4,2):
 a,z=struct.unpack_from('<HH',image,off)
 if a&0xf800!=0xf000 or z&0xd000!=0xd000:continue
 s=a>>10&1;i1=1-((z>>13&1)^s);i2=1-((z>>11&1)^s)
 imm=(s<<24)|(i1<<23)|(i2<<22)|((a&1023)<<12)|((z&2047)<<1);imm-=s<<25
 calls.append((B+off,B+off+4+imm))
def val(op,regs):
 if op.type==ARM_OP_IMM:return op.imm & 0xffffffff
 if op.type==ARM_OP_REG:
  v=regs.get(op.reg)
  if v is not None and op.shift.type==ARM_SFT_LSL:v=(v<<op.shift.value)&0xffffffff
  if v is not None and op.shift.type==ARM_SFT_LSR:v>>=op.shift.value
  return v
 return None
def interpret(ins,regs):
 if not ins.id:return
 ops=ins.operands;m=ins.mnemonic.split('.')[0].rstrip('s')
 dst=ops[0].reg if ops and ops[0].type==ARM_OP_REG else None
 result=None
 if m in ('mov','movw') and len(ops)==2:result=val(ops[1],regs)
 elif m=='movt' and dst in regs:result=(regs[dst]&65535)|(ops[1].imm<<16)
 elif m in ('ldr','ldrh','ldrb') and len(ops)>1 and ops[1].type==ARM_OP_MEM:
  mem=ops[1].mem
  base=((ins.address+4)&~3) if mem.base==ARM_REG_PC else regs.get(mem.base)
  if base is not None and not mem.index:
   ad=base+mem.disp;n={'ldr':4,'ldrh':2,'ldrb':1}[m]
   if B<=ad<=B+len(image)-n:result=int.from_bytes(image[ad-B:ad-B+n],'little')
 elif m in ('add','sub','orr','and','bic','lsl','lsr') and len(ops)>=2:
  aa=val(ops[1],regs) if len(ops)==3 else regs.get(dst);bb=val(ops[-1],regs)
  if aa is not None and bb is not None:
   if m=='add':result=aa+bb
   elif m=='sub':result=aa-bb
   elif m=='orr':result=aa|bb
   elif m=='and':result=aa&bb
   elif m=='bic':result=aa&~bb
   elif m=='lsl':result=aa<<bb
   elif m=='lsr':result=aa>>bb
 elif m in ('uxtb','uxth') and len(ops)==2:
  v=val(ops[1],regs)
  if v is not None:result=v&(255 if m=='uxtb' else 65535)
 try:_,writes=ins.regs_access()
 except: writes=[]
 for reg in writes:regs.pop(reg,None)
 if result is not None and dst is not None:regs[dst]=result&0xffffffff
 if ins.mnemonic in ('bl','blx'):
  for reg in (ARM_REG_R0,ARM_REG_R1,ARM_REG_R2,ARM_REG_R3,ARM_REG_R12):regs.pop(reg,None)
records=[]
for addr,target in calls:
 if target not in api:continue
 regs={};seq=list(md.disasm(image[addr-B-128:addr-B+4],addr-128))
 for ins in seq:
  if ins.address==addr:break
  if ins.mnemonic=='push':regs={}
  interpret(ins,regs)
 port=regs.get(ARM_REG_R0);mask=regs.get(ARM_REG_R1)
 pins=[ports[port]+str(i)for i in range(16)if mask&(1<<i)] if port in ports and mask is not None and 0<mask<65536 else []
 records.append(dict(call=hex(addr),api=api[target],port=hex(port)if port else None,mask=hex(mask)if mask is not None else None,pins=pins,r2=regs.get(ARM_REG_R2)))
Path('io_resolution_20261109/gpio_refs_candidates.json').write_text(json.dumps(records,indent=2))
unknown=['PE0','PE2','PE5','PE6','PE15','PC3','PC4','PC6','PC7','PC12','PC14','PC15','PD0','PD1','PD6','PD7','PA8','PB9','PC0']
with open('io_resolution_20261109/unknown_refs.disasm','w')as f:
 for p in unknown:
  rr=[r for r in records if p in r['pins']]
  print(p,len(rr),[(r['call'],r['api'])for r in rr]);f.write('\n### '+p+'\n')
  for r in rr:
   addr=int(r['call'],16);f.write('\n'+str(r)+'\n')
   for ins in md.disasm(image[addr-B-48:addr-B+20],addr-48):
    if not ins.id:continue
    s=''
    if len(ins.operands)>1 and ins.operands[1].type==ARM_OP_MEM and ins.operands[1].mem.base==ARM_REG_PC:
     ad=((ins.address+4)&~3)+ins.operands[1].mem.disp
     if B<=ad<B+len(image)-4:s=' ; '+hex(struct.unpack_from('<I',image,ad-B)[0])
    f.write(f'{ins.address:08x} {ins.mnemonic:9s} {ins.op_str}{s}\n')
print('Resolved candidate args',sum(bool(r['pins'])for r in records),'/',len(records))
Path('io_resolution_20261109/all_calls.json').write_text(json.dumps(calls))
print('full flash SHA256',hashlib.sha256(image).hexdigest())
